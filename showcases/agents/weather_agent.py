#!/usr/bin/env python3

import sys
import os
import logging
import time
from dotenv import load_dotenv
from python_a2a import A2AServer, AgentCard, AgentSkill, run_server, TaskStatus, TaskState
from showcases.utils.request_gateway import RequestGateway
from showcases.utils.agent_colors import weather_print as print, print_task_start, print_task_complete

# Load environment variables
load_dotenv()

class WeatherAgent(A2AServer):
    """
    Weather information agent with secure external API integration.
    Uses ANS (Agent Name Service) naming for secure agent identification.
    """
    
    def __init__(self, port=8001):
        """Initialize Weather Agent with Request Gateway."""
        # Create agent card with ANS name as the name field
        agent_card = AgentCard(
            name="forecast.weather.v1.human-security.com",
            description="Provides current weather information with air quality data for any location worldwide through secure external API",
            url=f"http://localhost:{port}",
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Get Weather",
                    description="Get current weather forecast with air quality data for any location through secure external API",
                    tags=["weather", "forecast", "temperature", "air quality", "external-api", "secure"],
                    examples=["What's the weather like in Paris?", "Get weather for New York", "How's the weather in Tokyo?"]
                )
            ]
        )
        
        # Store agent card for use in requests
        self.agent_card = agent_card
        
        # Initialize with agent card
        super().__init__(agent_card=agent_card)
        
        # Initialize the security gateway for signed requests
        self.gateway = RequestGateway("Weather Agent", ans_name=self.agent_card.name)
        print.print_success(f"Weather Agent initialized with Request Gateway and ANS name: {self.agent_card.name}")
    
    def get_weather(self, location: str):
        """
        Get weather data from secure external API with cryptographic authentication.
        This method focuses on API integration through the verifier service.
        
        Args:
            location: The city or location name
            
        Returns:
            JSON response from weather service
        """
        try:
            print.print_info(f"Getting weather for location: {location}")
            print.print_info("Preparing to make secure request to weather service")
            print.print_info("Validating location parameter and preparing query parameters")
            
            agent_verifier_base_url = os.getenv("AGENT_VERIFIER_ADDRESS")
            if not agent_verifier_base_url:
                print.print_error("AGENT_VERIFIER_ADDRESS environment variable not set")
                return "Error: AGENT_VERIFIER_ADDRESS environment variable not set."

            verify_url = f"{agent_verifier_base_url}/weather"

            # Use Request Gateway for secure signed requests with query parameters
            weather_query_params = {"location": location}
            
            print.print_info("Making secure signed request through gateway with query parameters")
            response = self.gateway.get(verify_url, params=weather_query_params, timeout=30)
            response.raise_for_status()
            
            print.print_success("Successfully retrieved weather data from external service")
            return response.text
            
        except Exception as e:
            error_msg = f"Error getting weather for {location}: {str(e)}"
            print.print_error(error_msg)
            return error_msg
    
    def handle_task(self, task):
        """
        Handle incoming A2A tasks for weather queries.
        This agent expects the location to be provided directly by the LLM Agent.
        """
        start_time = time.time()
        try:
            # Extract location from message
            message_data = task.message or {}
            content = message_data.get("content", {})
            
            if isinstance(content, dict):
                location = content.get("text", "").strip()
            else:
                location = str(content).strip()
            
            # The LLM Agent should pass the location directly
            if not location:
                task.status = TaskStatus(
                    state=TaskState.FAILED,
                    message={
                        "role": "agent",
                        "content": {
                            "type": "text",
                            "text": "Error: No location provided by LLM Agent"
                        }
                    }
                )
                return task
            
            print_task_start("Weather Agent", f"API call for: {location}")
            print.print_task(f"Fetching weather for: {location}")
            
            # Get weather data from API
            weather_text = self.get_weather(location)
            
            task.artifacts = [{
                "parts": [{"type": "text", "text": weather_text}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
            duration = time.time() - start_time
            print_task_complete("Weather Agent", duration)
            print.print_success(f"Weather data fetched for {location}")
            print.print("")
            
        except Exception as e:
            print.print_error(f"Task failed: {str(e)}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent",
                    "content": {
                        "type": "text", 
                        "text": f"Weather service error: {str(e)}"
                    }
                }
            )
            
            duration = time.time() - start_time
            print_task_complete("Weather Agent", duration)
        
        return task


# Run the server
if __name__ == "__main__":
    print.print_info("Starting Weather Agent server...")
    agent = WeatherAgent(port=8001)
    print.print_success("Weather Agent ready on http://localhost:8001")
    run_server(agent, port=8001, debug=True)