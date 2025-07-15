#!/usr/bin/env python3

import os
import time

import google.generativeai as genai
from dotenv import load_dotenv
from python_a2a import A2AServer, AgentCard, AgentSkill, run_server, TaskStatus, TaskState, A2AClient

from showcases.utils.agent_colors import llm_printer, print_task_start, print_task_complete
from showcases.utils.request_gateway import RequestGateway
from showcases.utils.system_instructions import system_instruction

# Load environment variables
load_dotenv()

class LLMAgent(A2AServer):
    """
    AI Agent Orchestrator powered by Google Gemini.
    Handles all AI queries and coordinates with specialized agents using tool calling.
    All outgoing requests are cryptographically signed through the Request Gateway.
    Uses ANS (Agent Name Service) naming for secure agent identification.
    """
    
    def __init__(self, port=8003):
        """Initialize LLM Agent with Request Gateway and agent clients."""
        # Create agent card with ANS name as the name field
        agent_card = AgentCard(
            name="orchestrator.llm.v1.human-security.com",
            description="AI Agent Orchestrator with Google Gemini - handles all AI queries and coordinates with specialized agents",
            url=f"http://localhost:{port}",
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Smart AI Assistant",
                    description="Intelligent AI assistant that can handle queries and coordinate with specialized agents",
                    tags=["ai", "orchestrator", "weather", "travel", "assistant"],
                    examples=["What's the weather like in Paris?", "Plan a trip to Tokyo", "What should I do in New York?"]
                )
            ]
        )
        
        # Store agent card for use in requests
        self.agent_card = agent_card
        
        # Initialize with agent card
        super().__init__(agent_card=agent_card)
        
        # Initialize the security gateway for signed requests
        self.gateway = RequestGateway("LLM Agent", ans_name=self.agent_card.name)
        llm_printer.print_success(f"LLM Agent initialized with Request Gateway and ANS name: {self.agent_card.name}")
        
        # Initialize clients for other agents
        self.weather_client = A2AClient("http://localhost:8001")
        self.trip_client = A2AClient("http://localhost:8002")
        llm_printer.print_info("Agent clients initialized for Weather and Trip agents")
        
        self.configure_llm()
    
    def configure_llm(self):
        """Configure Google Gemini API."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
    
    def smart_assistant(self, query: str) -> str:
        """
        Process a query using Google Gemini with tool calling capabilities.
        Can coordinate with Weather and Trip agents when needed.
        
        Args:
            query: The user's question or request
            
        Returns:
            AI response from Gemini, potentially enhanced with agent data
        """
        try:
            llm_printer.print_info(f"Processing smart query: {query[:100]}...")
            llm_printer.print_info("Analyzing request and determining if specialized agents needed")
            
            # Define tools for Weather and Trip agents
            tools = [
                genai.types.Tool(
                    function_declarations=[
                        genai.types.FunctionDeclaration(
                            name="get_weather",
                            description="Get current weather information for a city",
                            parameters={
                                "type": "object",
                                "properties": {
                                    "city": {
                                        "type": "string",
                                        "description": "The city to get weather for"
                                    }
                                },
                                "required": ["city"]
                            }
                        ),
                        genai.types.FunctionDeclaration(
                            name="plan_trip",
                            description="Get trip planning data for a city",
                            parameters={
                                "type": "object", 
                                "properties": {
                                    "city": {
                                        "type": "string",
                                        "description": "The city to plan a trip for"
                                    }
                                },
                                "required": ["city"]
                            }
                        )
                    ]
                )
            ]
            
            # Create model with tools and system instruction
            model = genai.GenerativeModel(
                "gemini-2.0-flash-exp",
                tools=tools,
                system_instruction=system_instruction
            )
            
            chat = model.start_chat()
            response = chat.send_message(query)
            
            # Check if any tools were called
            for part in response.parts:
                if part.function_call:
                    function_name = part.function_call.name
                    args = part.function_call.args
                    
                    llm_printer.print_info(f"Tool call detected: {function_name}")
                    
                    if function_name == "get_weather":
                        city = args["city"] if "city" in args else ""
                        llm_printer.print_info(f"Calling Weather Agent for city: {city}")
                        
                        # Call Weather Agent with just the city name
                        weather_data = self.weather_client.ask(city)
                        
                        # Send tool result back to model
                        llm_printer.print_info("Integrating weather data into response")
                        response = chat.send_message(
                            f"Weather data for {city}:\n{weather_data}\n\n"
                            f"Please provide a comprehensive response to the original query: {query}"
                        )
                        
                    elif function_name == "plan_trip":
                        city = args["city"] if "city" in args else ""
                        llm_printer.print_info(f"Calling Trip Agent for city: {city}")
                        
                        # Call Trip Agent with just the city name
                        trip_data = self.trip_client.ask(city)
                        
                        # Send tool result back to model
                        llm_printer.print_info("Integrating trip data into response")
                        response = chat.send_message(
                            f"Trip data for {city}:\n{trip_data}\n\n"
                            f"Please provide a comprehensive response with travel recommendations for: {query}"
                        )
            
            llm_printer.print_success("Smart AI processing completed")
            
            try:
                return response.text
            except Exception as text_error:
                # If we can't get text, try to extract from parts
                text_parts = []
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                
                if text_parts:
                    return ''.join(text_parts)
                else:
                    llm_printer.print_warning("No text found in response, returning default message")
                    return "I processed your request but encountered an issue generating the final response. Please try asking again."
            
        except Exception as e:
            error_msg = f"Error in smart assistant: {str(e)}"
            llm_printer.print_error(error_msg)
            return error_msg
    
    def handle_task(self, task):
        """Handle incoming A2A tasks for LLM queries"""
        start_time = time.time()
        try:
            # Extract query from message
            message_data = task.message or {}
            content = message_data.get("content", {})
            
            if isinstance(content, dict):
                text = content.get("text", "")
            else:
                text = str(content)
            
            print_task_start("LLM Agent", f"Smart AI Processing: {text[:50]}...")
            llm_printer.print_task(f"Processing smart AI task: {text[:100]}...")
            
            if not text.strip():
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={
                        "role": "agent",
                        "content": {
                            "type": "text", 
                            "text": "Please provide a question or request for the AI assistant."
                        }
                    }
                )
                return task
            
            # Process with Smart Assistant (includes tool calling)  
            response_text = self.smart_assistant(text.strip())
            
            task.artifacts = [{
                "parts": [{"type": "text", "text": response_text}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
            duration = time.time() - start_time
            print_task_complete("LLM Agent", duration)
            llm_printer.print_success("Smart AI task completed successfully")
            
        except Exception as e:
            llm_printer.print_error(f"Task failed: {str(e)}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent",
                    "content": {
                        "type": "text",
                        "text": f"Sorry, I encountered an error processing your request: {str(e)}"
                    }
                }
            )
            
            duration = time.time() - start_time
            print_task_complete("LLM Agent", duration)
        
        return task


# Run the server
if __name__ == "__main__":
    llm_printer.print_info("Starting LLM Agent server...")
    agent = LLMAgent(port=8003)
    llm_printer.print_success("LLM Agent ready on http://localhost:8003")
    run_server(agent, port=8003, debug=True)
