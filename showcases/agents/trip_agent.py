#!/usr/bin/env python3

import os
import logging
import time
from python_a2a import A2AServer, AgentCard, AgentSkill, run_server, TaskStatus, TaskState
from showcases.utils.request_gateway import RequestGateway
from showcases.utils.agent_colors import trip_print as print, print_task_start, print_task_complete
# Add parent directory to path for imports
import sys
sys.path.append('..')
from dotenv import load_dotenv


class TripPlannerAgent(A2AServer):
    """
    Trip planning agent with secure external API integration.
    Uses ANS (Agent Name Service) naming for secure agent identification.
    """
    
    def __init__(self, port=8002):
        """Initialize Trip Planner Agent with Request Gateway."""
        # Create agent card with ANS name as the name field
        agent_card = AgentCard(
            name="planner.trip.v1.human-security.com",
            description="Secure trip planning service with external API integration and cryptographic authentication",
            url=f"http://localhost:{port}",
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Plan Trip",
                    description="Get trip planning data from secure external API with cryptographic authentication",
                    tags=["travel", "trip", "planning", "external-api", "secure"],
                    examples=["Plan a trip to Paris", "Help me plan a trip to Tokyo", "What should I do in New York?"]
                )
            ]
        )
        
        # Store agent card for use in requests
        self.agent_card = agent_card
        
        # Initialize with agent card
        super().__init__(agent_card=agent_card)
        
        # Initialize the security gateway for signed requests
        self.gateway = RequestGateway("Trip Planner Agent", ans_name=self.agent_card.name)
        print.print_success(f"Trip Planner Agent initialized with Request Gateway and ANS name: {self.agent_card.name}")
        print.print_info("Trip Agent focused on secure external API integration")

    def get_attractions(self, city: str) -> str:
        """
        Makes a secure authenticated request to the external attractions service.
        This method focuses purely on API integration without AI processing.
        
        Args:
            city: The city to get attractions for
            
        Returns:
            JSON response from attractions service
        """
        try:
            print.print_info(f"Getting attractions for city: {city}")
            print.print_info("Preparing to make secure request to attractions service")
            print.print_info("Validating city parameter and preparing query parameters")
            
            agent_verifier_base_url = os.getenv("AGENT_VERIFIER_ADDRESS")
            if not agent_verifier_base_url:
                print.print_error("AGENT_VERIFIER_ADDRESS environment variable not set")
                return "Error: AGENT_VERIFIER_ADDRESS environment variable not set."

            verify_url = f"{agent_verifier_base_url}/attractions"

            # Use Request Gateway for secure signed requests with query parameters
            trip_query_params = {"city": city}
            
            print.print_info("Making secure signed request through gateway with query parameters")
            response = self.gateway.get(verify_url, params=trip_query_params, timeout=30)
            response.raise_for_status()
            
            print.print_success("Successfully retrieved attractions data from external service")
            return response.text
            
        except Exception as e:
            error_msg = f"Error getting attractions for {city}: {str(e)}"
            print.print_error(error_msg)
            return error_msg


    
    def handle_task(self, task):
        """
        Handle incoming A2A tasks for getting attractions.
        This agent expects the city to be provided directly by the LLM Agent.
        """
        start_time = time.time()
        try:
            # Extract message content
            message_data = task.message or {}
            content = message_data.get("content", {})
            
            if isinstance(content, dict):
                city = content.get("text", "").strip()
            else:
                city = str(content).strip()
            
            # The LLM Agent should pass the city directly
            if not city:
                task.status = TaskStatus(
                    state=TaskState.FAILED,
                    message={
                        "role": "agent",
                        "content": {
                            "type": "text",
                            "text": "Error: No city provided by LLM Agent"
                        }
                    }
                )
                return task
            
            print_task_start("Trip Planner Agent", f"API call for: {city}")
            print.print_task(f"Fetching attractions for: {city}")
            
            # Get attractions data from external API
            attractions_data = self.get_attractions(city)
            
            task.artifacts = [{
                "parts": [{"type": "text", "text": attractions_data}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
            duration = time.time() - start_time
            print_task_complete("Trip Planner Agent", duration)
            print.print_success(f"Attractions data fetched for {city}")
            print.print("")
            
        except Exception as e:
            print.print_error(f"Task failed: {str(e)}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent",
                    "content": {
                        "type": "text",
                        "text": f"Attractions service error: {str(e)}"
                    }
                }
            )
            
            duration = time.time() - start_time
            print_task_complete("Trip Planner Agent", duration)
        
        return task


# Run the server
if __name__ == "__main__":
    load_dotenv()
    agent = TripPlannerAgent(port=8002)
    run_server(agent, port=8002, debug=True)