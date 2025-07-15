#!/usr/bin/env python3

"""
Smart Travel Assistant - A2A Agent Coordination Demo

This demonstrates the AI-powered agent coordination system with:
- 🧠 LLM Agent: AI orchestrator with tool calling
- 🌦️ Weather Agent: WeatherAPI.com integration 
- ✈️ Trip Agent: External trip API integration
- 🔐 Request Gateway: Cryptographic security for all requests

Single comprehensive mode: Ask for a city, get AI-coordinated results.
"""

import sys
import os
import asyncio
import threading
import time
from dotenv import load_dotenv
from python_a2a import AgentNetwork, A2AClient, run_server
from showcases.agents.llm_agent import LLMAgent
from showcases.agents.trip_agent import TripPlannerAgent  
from showcases.agents.weather_agent import WeatherAgent
from showcases.utils.agent_colors import (
    orchestrator_printer, weather_print, trip_print, llm_printer,
    print_startup_banner, print_agent_status, print_agent_route, 
    print_separator, format_response
)


class A2AAgentOrchestrator:
    """
    Orchestrates multiple A2A agents for travel planning and assistance.
    Manages LLM, Trip Planning, and Weather agents in a coordinated network.
    """
    
    def __init__(self):
        self.network = None
        self.agents = {}
        self.agent_threads = []
        
    def start_agent_servers(self):
        """Start all agent servers in background threads"""
        orchestrator_printer.print_info("Starting A2A Agent Servers...")
        print()
        
        # Start Weather Agent on port 8001
        try:
            weather_agent = WeatherAgent(port=8001)
            weather_thread = threading.Thread(
                target=lambda: run_server(weather_agent, port=8001, debug=False),
                daemon=True
            )
            weather_thread.start()
            self.agent_threads.append(weather_thread)
            print_agent_status("Weather Agent", 8001, "STARTED")
        except Exception as e:
            print_agent_status("Weather Agent", 8001, "FAILED")
            orchestrator_printer.print_error(f"Failed to start Weather Agent: {e}")
        
        # Start Trip Planner Agent on port 8002  
        try:
            trip_agent = TripPlannerAgent(port=8002)
            trip_thread = threading.Thread(
                target=lambda: run_server(trip_agent, port=8002, debug=False),
                daemon=True
            )
            trip_thread.start()
            self.agent_threads.append(trip_thread)
            print_agent_status("Trip Planner Agent", 8002, "STARTED")
        except Exception as e:
            print_agent_status("Trip Planner Agent", 8002, "FAILED")
            orchestrator_printer.print_error(f"Failed to start Trip Agent: {e}")
        
        # Start LLM Agent on port 8003
        try:
            llm_agent = LLMAgent(port=8003)
            llm_thread = threading.Thread(
                target=lambda: run_server(llm_agent, port=8003, debug=False),
                daemon=True
            )
            llm_thread.start()
            self.agent_threads.append(llm_thread)
            print_agent_status("LLM Agent", 8003, "STARTED")
        except Exception as e:
            print_agent_status("LLM Agent", 8003, "FAILED")
            orchestrator_printer.print_error(f"Failed to start LLM Agent: {e}")
        
        # Give agents time to start
        orchestrator_printer.print_info("Waiting for agents to initialize...")
        time.sleep(3)
        print()
        
    def setup_agent_network(self):
        """Set up the A2A agent network"""
        orchestrator_printer.print_info("Setting up Agent Network...")
        
        # Create agent network
        self.network = AgentNetwork(name="Travel Assistant Network")
        
        # Add agents to network
        self.network.add("weather", "http://localhost:8001")
        self.network.add("trip", "http://localhost:8002") 
        self.network.add("llm", "http://localhost:8003")
        
        # Create client connections
        self.agents = {
            "weather": A2AClient("http://localhost:8001"),
            "trip": A2AClient("http://localhost:8002"),
            "llm": A2AClient("http://localhost:8003")
        }
        
        orchestrator_printer.print_success("Agent network configured")
        orchestrator_printer.print_info("Available Agents:")
        for agent_info in self.network.list_agents():
            orchestrator_printer.print(f"   - {agent_info['name']}: {agent_info['description']}")
        print()
            

    def run_smart_travel_assistant(self):
        """Run the smart travel assistant powered by AI agent coordination"""
        print_separator("=", 70)
        orchestrator_printer.print_info("🧠 SMART TRAVEL ASSISTANT - AI Agent Coordination")
        print_separator("=", 70)
        
        destination = input("🗺️  Enter a destination city: ").strip()
        if not destination:
            destination = "Paris"
            
        orchestrator_printer.print_info(f"🤖 Analyzing travel requirements for {destination}...")
        
        # Use LLM Agent to coordinate all services intelligently
        travel_query = f"I want to visit {destination}. Please provide comprehensive travel information including weather conditions and trip planning recommendations."
        
        print_agent_route("User", "Smart LLM Agent", f"Comprehensive travel query for {destination}")
        orchestrator_printer.print_info("🧠 AI Agent coordinating with Weather and Trip services...")
        print()
        
        # The LLM Agent will automatically:
        # 1. Call Weather Agent for weather data
        # 2. Call Trip Agent for trip recommendations  
        # 3. Combine everything into a comprehensive response
        smart_response = self.agents["llm"].ask(travel_query)
        
        print()
        print_separator("-", 70)
        print(format_response("Smart AI Assistant", smart_response))
        print_separator("=", 70)
        orchestrator_printer.print_success(f"✨ Smart travel assistance for {destination} completed!")
        print_separator("=", 70)

def main():
    """Main entry point for A2A agent demonstration"""
    # Print the demo banner
    print("🚀 Starting Smart Travel Assistant...")
    print("=" * 60)
    print("🧠 AI-Powered Agent Coordination System")  
    print("🌟 Single Comprehensive Mode")
    print("🔐 Enterprise-Grade Security")
    print("=" * 60)
    print()
    
    print_startup_banner()
    
    # Load environment variables
    load_dotenv()
    
    # Verify required environment variables
    required_vars = ["GOOGLE_API_KEY"]
    optional_vars = ["WEATHERAPI_KEY", "AGENT_VERIFIER_ADDRESS", "AGENT_HOSTED_DOMAIN", "ENABLE_REQUEST_SIGNING"]
    
    missing_required = [var for var in required_vars if not os.getenv(var)]
    if missing_required:
        orchestrator_printer.print_error(f"Missing required environment variables: {', '.join(missing_required)}")
        orchestrator_printer.print_error("Please set these in your .env file or environment.")
        return
        
    missing_optional = [var for var in optional_vars if not os.getenv(var)]
    if missing_optional:
        orchestrator_printer.print_warning(f"Optional environment variables not set: {', '.join(missing_optional)}")
        orchestrator_printer.print_warning("Some features may be limited.")
    
    try:
        # Initialize orchestrator
        orchestrator = A2AAgentOrchestrator()
        
        # Start agent servers
        orchestrator.start_agent_servers()
        
        # Setup network
        orchestrator.setup_agent_network()
        
        # Run the single comprehensive mode
        orchestrator.run_smart_travel_assistant()
            
    except KeyboardInterrupt:
        orchestrator_printer.print_info("Goodbye!")
    except Exception as e:
        orchestrator_printer.print_error(f"Error: {str(e)}")
    finally:
        orchestrator_printer.print_warning("Shutting down agents...")


if __name__ == "__main__":
    main()
