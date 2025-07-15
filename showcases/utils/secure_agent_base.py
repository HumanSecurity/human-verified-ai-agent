#!/usr/bin/env python3

"""
Secure Agent Base Class

Provides a robust foundation for agents that need cryptographic request signing.
Any agent can inherit from SecureAgentBase to automatically get:
- Request Gateway integration
- Signed HTTP requests
- Configurable signing via environment variables
- Fallback to unsigned requests if needed
"""

import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from python_a2a import A2AServer
from .request_gateway import RequestGateway
from .agent_colors import gateway_printer

class SecureAgentBase(A2AServer):
    """
    Base class for A2A agents with built-in request signing capabilities.
    
    All HTTP requests made through this agent will be cryptographically signed
    if ENABLE_REQUEST_SIGNING is set to 'true' in environment variables.
    
    Environment Variables:
        ENABLE_REQUEST_SIGNING (default: "true"): Enable/disable request signing
        AGENT_HOSTED_DOMAIN (default: "your-agent-domain.com"): Domain for signature
        
    Usage:
        class MyAgent(SecureAgentBase):
            def __init__(self):
                super().__init__(agent_name="My Custom Agent")
                
            def make_api_call(self, url):
                # This will be automatically signed
                return self.gateway.get(url)
    """
    
    def __init__(self, agent_name: str, agent_domain: Optional[str] = None, *args, **kwargs):
        """
        Initialize secure agent with request signing capabilities.
        
        Args:
            agent_name: Name of the agent (used for logging and signatures)
            agent_domain: Domain for signatures (defaults to environment variable)
            *args, **kwargs: Arguments passed to A2AServer parent class
        """
        super().__init__(*args, **kwargs)
        
        # Load environment variables
        load_dotenv()
        
        # Store agent information
        self.agent_name = agent_name
        self.agent_domain = agent_domain or os.getenv("AGENT_HOSTED_DOMAIN", "your-agent-domain.com")
        
        # Initialize request gateway for secure HTTP requests
        self.gateway = RequestGateway(self.agent_name, self.agent_domain)
        
        # Check signing configuration
        self.signing_enabled = os.getenv("ENABLE_REQUEST_SIGNING", "true").lower() == "true"
        
        if self.signing_enabled:
            gateway_printer.print_success(f"🔐 {self.agent_name} initialized with cryptographic request signing")
            gateway_printer.print_info(f"🏷️  Signature Domain: {self.agent_domain}")
        else:
            gateway_printer.print_warning(f"⚠️  {self.agent_name} initialized with signing DISABLED")
            gateway_printer.print_info("Set ENABLE_REQUEST_SIGNING=true to enable security")
    
    def make_signed_get(self, url: str, params: Optional[Dict] = None, 
                       headers: Optional[Dict] = None, **kwargs) -> Any:
        """
        Make a signed GET request (convenience method).
        
        Args:
            url: Target URL
            params: Query parameters
            headers: Request headers
            **kwargs: Additional arguments
            
        Returns:
            requests.Response object
        """
        return self.gateway.get(url, params=params, headers=headers, **kwargs)
    
    def make_signed_post(self, url: str, data: Optional[Dict] = None, 
                        json: Optional[Dict] = None, headers: Optional[Dict] = None, **kwargs) -> Any:
        """
        Make a signed POST request (convenience method).
        
        Args:
            url: Target URL
            data: Form data
            json: JSON data
            headers: Request headers
            **kwargs: Additional arguments
            
        Returns:
            requests.Response object
        """
        return self.gateway.post(url, data=data, json=json, headers=headers, **kwargs)
    
    def make_a2a_call(self, agent_url: str, query: str, headers: Optional[Dict] = None) -> Any:
        """
        Make a signed Agent-to-Agent call.
        
        Args:
            agent_url: URL of the target agent
            query: Query to send
            headers: Additional headers
            
        Returns:
            requests.Response object
        """
        return self.gateway.make_a2a_request(agent_url, query, headers)
    
    def log_security_status(self):
        """Log the current security configuration for debugging."""
        if self.signing_enabled:
            gateway_printer.print_info(f"🔐 Security Status: ENABLED for {self.agent_name}")
            gateway_printer.print_info(f"🏷️  Signature Agent: {self.gateway.signature_agent}")
        else:
            gateway_printer.print_warning(f"⚠️  Security Status: DISABLED for {self.agent_name}")
            gateway_printer.print_info("All requests will be unsigned (not recommended for production)")
    
    @classmethod
    def create_secure_agent(cls, agent_name: str, **kwargs):
        """
        Factory method to create a secure agent instance.
        
        Args:
            agent_name: Name of the agent
            **kwargs: Additional arguments for initialization
            
        Returns:
            Configured secure agent instance
        """
        return cls(agent_name=agent_name, **kwargs)


# Utility functions for easy integration
def enable_signing_for_agent(agent_instance, agent_name: str, agent_domain: Optional[str] = None):
    """
    Add signing capabilities to an existing agent instance.
    
    Args:
        agent_instance: Existing agent instance
        agent_name: Name for signing purposes
        agent_domain: Domain for signatures
    """
    if not hasattr(agent_instance, 'gateway'):
        agent_instance.gateway = RequestGateway(agent_name, agent_domain)
        gateway_printer.print_success(f"🔐 Request signing enabled for {agent_name}")
    else:
        gateway_printer.print_info(f"🔐 Request signing already enabled for {agent_name}")


def check_signing_environment():
    """
    Check and display the current signing environment configuration.
    Useful for debugging and setup verification.
    """
    load_dotenv()
    
    print("\n🔐 REQUEST SIGNING CONFIGURATION")
    print("=" * 50)
    
    # Check signing enablement
    signing_enabled = os.getenv("ENABLE_REQUEST_SIGNING", "true").lower() == "true"
    if signing_enabled:
        gateway_printer.print_success("✅ Request signing: ENABLED")
    else:
        gateway_printer.print_warning("⚠️  Request signing: DISABLED")
    
    # Check domain configuration
    domain = os.getenv("AGENT_HOSTED_DOMAIN", "your-agent-domain.com")
    if domain == "your-agent-domain.com":
        gateway_printer.print_warning(f"⚠️  Using default domain: {domain}")
        gateway_printer.print_info("Set AGENT_HOSTED_DOMAIN for production use")
    else:
        gateway_printer.print_success(f"✅ Agent domain: {domain}")
    
    # Check for signing keys
    key_path = os.getenv("PRIVATE_KEY_PATH", "../keys/private_ed25519_pem")
    if os.path.exists(key_path):
        gateway_printer.print_success(f"✅ Private key found: {key_path}")
    else:
        gateway_printer.print_error(f"❌ Private key missing: {key_path}")
        gateway_printer.print_info("Run key generator to create signing keys")
    
    print("=" * 50)


if __name__ == "__main__":
    # Demonstrate the secure agent base
    check_signing_environment()
    
    # Example usage
    class ExampleAgent(SecureAgentBase):
        def __init__(self):
            super().__init__(agent_name="Example Secure Agent")
        
        def test_request(self):
            # This request will be automatically signed
            try:
                response = self.make_signed_get("https://httpbin.org/get")
                return f"Request successful: {response.status_code}"
            except Exception as e:
                return f"Request failed: {e}"
    
    # Test the example
    example = ExampleAgent()
    example.log_security_status() 