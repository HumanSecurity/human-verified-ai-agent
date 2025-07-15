#!/usr/bin/env python3

import sys
import os
import requests
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Add parent directory to path to access request signing modules
sys.path.append('..')
sys.path.append('../..')
from request_signer import sign_request, print_signer
from request_orchestrator import send_request
from agent_key_manager import get_agent_key_id_ed25519

class RequestGateway:
    """
    Security gateway that ensures all outgoing HTTP requests from agents are cryptographically signed.
    Acts as a central point for request authentication and security.
    """
    
    def __init__(self, agent_name: str, agent_domain: Optional[str] = None, ans_name: Optional[str] = None):
        """
        Initialize the request gateway for a specific agent.
        
        Args:
            agent_name: Name of the agent (e.g., "WeatherAgent", "TripAgent", "LLMAgent")
            agent_domain: Domain name for the agent (defaults to environment variable)
            ans_name: ANS (Agent Name Service) name for secure agent identification
        """
        load_dotenv()
        
        self.agent_name = agent_name
        self.ans_name = ans_name  # Store ANS name for X-Agent-Name header
        self.agent_domain = agent_domain or os.getenv("AGENT_HOSTED_DOMAIN", "localhost")
        self.signature_agent = f"{agent_name.lower().replace(' ', '-')}.{self.agent_domain}"
        
        # Map agent names to their key file names
        self.agent_key_mapping = {
            "Weather Agent": "weather_agent",
            "Trip Agent": "trip_agent", 
            "Trip Planner Agent": "trip_agent",
            "LLM Agent": "llm_agent"
        }
        
        # Get the key name for this agent
        self.agent_key_name = self.agent_key_mapping.get(agent_name, "weather_agent")  # Default fallback
        self.agent_key_path = f"keys/private_ed25519_pem_{self.agent_key_name}"
        
        # Check if request signing is enabled
        self.signing_enabled = os.getenv("ENABLE_REQUEST_SIGNING", "true").lower() == "true"
        
        if self.signing_enabled:
            try:
                # Get the key_id for this agent
                self.key_id = get_agent_key_id_ed25519(self.agent_key_name)
                print_signer("")
                print_signer(f"🔐 Request Gateway initialized for {self.agent_name}")
                print_signer(f"🏷️  Signature Agent: {self.signature_agent}")
                print_signer(f"🔑 Using Key ID: {self.key_id}")
                print_signer(f"📁 Key Path: {self.agent_key_path}")
                print_signer("")
            except Exception as e:
                logging.error(f"Failed to load key for {self.agent_name}: {e}")
                self.signing_enabled = False
        else:
            logging.info(f"Request Gateway initialized for {self.agent_name} (signing disabled)")
    
    def get(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, 
            timeout: int = 30, **kwargs) -> requests.Response:
        """
        Make a signed GET request through the gateway.
        
        Args:
            url: Target URL
            params: Query parameters
            headers: Request headers
            timeout: Request timeout
            **kwargs: Additional arguments for requests
            
        Returns:
            requests.Response object
        """
        return self._make_signed_request("GET", url, params=params, headers=headers, 
                                       timeout=timeout, **kwargs)
    
    def post(self, url: str, data: Optional[Dict] = None, json: Optional[Dict] = None,
             headers: Optional[Dict] = None, timeout: int = 30, **kwargs) -> requests.Response:
        """
        Make a signed POST request through the gateway.
        
        Args:
            url: Target URL
            data: Form data
            json: JSON data
            headers: Request headers  
            timeout: Request timeout
            **kwargs: Additional arguments for requests
            
        Returns:
            requests.Response object
        """
        return self._make_signed_request("POST", url, data=data, json=json, headers=headers,
                                       timeout=timeout, **kwargs)
    
    def put(self, url: str, data: Optional[Dict] = None, json: Optional[Dict] = None,
            headers: Optional[Dict] = None, timeout: int = 30, **kwargs) -> requests.Response:
        """Make a signed PUT request through the gateway."""
        return self._make_signed_request("PUT", url, data=data, json=json, headers=headers,
                                       timeout=timeout, **kwargs)
    
    def delete(self, url: str, headers: Optional[Dict] = None, timeout: int = 30, 
               **kwargs) -> requests.Response:
        """Make a signed DELETE request through the gateway."""
        return self._make_signed_request("DELETE", url, headers=headers, timeout=timeout, **kwargs)
    
    def _make_signed_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Internal method to make a signed HTTP request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            **kwargs: Request arguments (including timeout)
            
        Returns:
            requests.Response object
        """
        if not self.signing_enabled:
            # If signing is disabled, make regular requests
            return requests.request(method, url, **kwargs)
        
        try:
            # Extract timeout from kwargs for session.send()
            timeout = kwargs.pop('timeout', 30)  # Default 30 seconds
            
            # Create request object without timeout (Request doesn't accept timeout)
            request = requests.Request(method, url, **kwargs)
            
            # Prepare the request
            session = requests.Session()
            prepared_req = session.prepare_request(request)
            
            print_signer("")
            print_signer(f"🚪 Gateway: {self.agent_name} making signed {method} request to {url}")
            
            # Sign the request using existing infrastructure with agent-specific key
            sign_request(
                prepared_req,
                signature_agent=self.signature_agent,
                key_path_for_signature=self.agent_key_path,  # Uses agent-specific key
                agent_name=self.ans_name or self.agent_name  # Use ANS name if available, fallback to agent name
            )
            
            # Send the signed request with timeout
            response = session.send(prepared_req, timeout=timeout)
            
            print_signer(f"✅ Gateway: Signed request completed - Status: {response.status_code}")
            print_signer("")
            
            return response
            
        except Exception as e:
            logging.error(f"Request Gateway error for {self.agent_name}: {str(e)}")
            # Fallback to unsigned request if signing fails
            logging.warning(f"Falling back to unsigned request for {url}")
            # Re-add timeout to kwargs for fallback
            kwargs['timeout'] = timeout
            return requests.request(method, url, **kwargs)
    
    def make_a2a_request(self, agent_url: str, query: str, headers: Optional[Dict] = None) -> requests.Response:
        """
        Make a signed Agent-to-Agent (A2A) request.
        
        Args:
            agent_url: URL of the target agent
            query: Query to send to the agent
            headers: Additional headers
            
        Returns:
            requests.Response object
        """
        a2a_headers = {
            "Content-Type": "application/json",
            "User-Agent": f"{self.agent_name}/1.0",
            "X-Agent-Source": self.signature_agent
        }
        
        if headers:
            a2a_headers.update(headers)
        
        a2a_data = {
            "message": {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": query
                }
            }
        }
        
        print_signer(f"🤖 Gateway: {self.agent_name} making A2A request to {agent_url}")
        
        return self.post(agent_url + "/tasks", json=a2a_data, headers=a2a_headers)


# Convenience functions for backwards compatibility
def create_gateway(agent_name: str) -> RequestGateway:
    """Create a request gateway for an agent."""
    return RequestGateway(agent_name)


class SignedSession:
    """
    Drop-in replacement for requests.Session that automatically signs all requests.
    Useful for agents that need a session-like interface.
    """
    
    def __init__(self, agent_name: str, agent_domain: Optional[str] = None):
        self.gateway = RequestGateway(agent_name, agent_domain)
    
    def get(self, url: str, **kwargs) -> requests.Response:
        return self.gateway.get(url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        return self.gateway.post(url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        return self.gateway.put(url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        return self.gateway.delete(url, **kwargs)
    
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        return self.gateway._make_signed_request(method, url, **kwargs)


if __name__ == "__main__":
    # Test the gateway
    gateway = RequestGateway("TestAgent")
    print("Request Gateway test initialized") 