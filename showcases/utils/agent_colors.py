#!/usr/bin/env python3

"""
Color utility system for A2A multi-agent outputs.
Provides colored printing functions for different agents and task highlighting.
"""

from typing import Optional

# ANSI color codes
class Colors:
    # Reset
    RESET = '\033[0m'
    
    # Agent-specific colors
    WEATHER = '\033[96m'      # Bright Cyan - Weather theme
    TRIP = '\033[92m'         # Bright Green - Travel theme  
    LLM = '\033[95m'          # Bright Magenta - AI theme
    ORCHESTRATOR = '\033[93m' # Bright Yellow - Coordination theme
    GATEWAY = '\033[91m'      # Bright Red - Security theme
    
    # Additional colors
    SIGNER = '\033[94m'       # Blue - Signature system
    SUCCESS = '\033[92m'      # Green - Success messages
    ERROR = '\033[91m'        # Red - Error messages
    WARNING = '\033[93m'      # Yellow - Warning messages
    INFO = '\033[97m'         # White - Info messages
    
    # Style modifiers
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    
    # Task highlighting
    TASK_HIGHLIGHT = '\033[1;97;46m'  # Bold White on Cyan background
    TASK_BORDER = '\033[1;46m'        # Bold Cyan background


class AgentPrinter:
    """Colored printing utility for agents."""
    
    def __init__(self, agent_name: str, color: str, icon: str = "🤖"):
        self.agent_name = agent_name
        self.color = color
        self.icon = icon
        self.prefix = f"{color}{icon} {agent_name}:{Colors.RESET}"
    
    def __call__(self, message: str, style: Optional[str] = None):
        """Make the printer callable like a function."""
        self.print(message, style)
    
    def print(self, message: str, style: Optional[str] = None):
        """Print a colored message from this agent."""
        if style:
            styled_message = f"{style}{message}{Colors.RESET}"
        else:
            styled_message = message
        print(f"{self.prefix} {styled_message}")
    
    def print_task(self, message: str):
        """Print a highlighted task message."""
        task_prefix = f"{Colors.TASK_HIGHLIGHT} 📋 TASK {Colors.RESET}"
        print(f"{task_prefix} {self.prefix} {Colors.BOLD}{message}{Colors.RESET}")
    
    def print_success(self, message: str):
        """Print a success message."""
        self.print(f"✅ {message}", Colors.SUCCESS)
    
    def print_error(self, message: str):
        """Print an error message."""
        self.print(f"❌ {message}", Colors.ERROR)
    
    def print_warning(self, message: str):
        """Print a warning message."""
        self.print(f"⚠️ {message}", Colors.WARNING)
    
    def print_info(self, message: str):
        """Print an info message."""
        self.print(f"ℹ️ {message}", Colors.INFO)


# Pre-configured agent printers
weather_printer = AgentPrinter("Weather Agent", Colors.WEATHER, "🌤️")
trip_printer = AgentPrinter("Trip Agent", Colors.TRIP, "✈️")
llm_printer = AgentPrinter("LLM Agent", Colors.LLM, "🧠")
orchestrator_printer = AgentPrinter("Orchestrator", Colors.ORCHESTRATOR, "🎯")
gateway_printer = AgentPrinter("Gateway", Colors.GATEWAY, "🔐")

# Simple print function wrappers for each agent
# Usage: 
#   from utils.agent_colors import weather_print as print
#   print.print_success("Success message")
#   print.print_error("Error message")
#   print.print_info("Info message")
#   print.print_task("Task message")
#   print.print("Regular message")

class WeatherPrint:
    @staticmethod
    def print(message: str):
        weather_printer.print(message)
    
    @staticmethod
    def print_success(message: str):
        weather_printer.print_success(message)
    
    @staticmethod
    def print_error(message: str):
        weather_printer.print_error(message)
    
    @staticmethod
    def print_info(message: str):
        weather_printer.print_info(message)
    
    @staticmethod
    def print_task(message: str):
        weather_printer.print_task(message)

class TripPrint:
    @staticmethod
    def print(message: str):
        trip_printer.print(message)
    
    @staticmethod
    def print_success(message: str):
        trip_printer.print_success(message)
    
    @staticmethod
    def print_error(message: str):
        trip_printer.print_error(message)
    
    @staticmethod
    def print_info(message: str):
        trip_printer.print_info(message)
    
    @staticmethod
    def print_task(message: str):
        trip_printer.print_task(message)

# Create instances to be imported
weather_print = WeatherPrint()
trip_print = TripPrint()

# Legacy compatibility functions
def print_signer(message: str):
    """Print a signer message in blue color (legacy compatibility)."""
    print(f"{Colors.SIGNER}🔐 Signer: {message}{Colors.RESET}")

def print_llm(message: str):
    """Print an LLM message in green color (legacy compatibility)."""
    llm_printer.print(message)


def print_task_start(agent_name: str, task_description: str):
    """Print a highlighted task start message."""
    border = f"{Colors.TASK_BORDER}{'=' * 60}{Colors.RESET}"
    task_msg = f"{Colors.TASK_HIGHLIGHT} 📋 TASK STARTED {Colors.RESET}"
    agent_msg = f"{Colors.BOLD}Agent: {agent_name}{Colors.RESET}"
    desc_msg = f"{Colors.BOLD}Task: {task_description}{Colors.RESET}"
    
    print()
    print(border)
    print(f"{task_msg} {agent_msg}")
    print(f"       {desc_msg}")
    print(border)


def print_task_complete(agent_name: str, duration: Optional[float] = None):
    """Print a task completion message."""
    duration_str = f" ({duration:.2f}s)" if duration else ""
    print(f"{Colors.SUCCESS}✅ TASK COMPLETED{Colors.RESET} - {Colors.BOLD}{agent_name}{Colors.RESET}{duration_str}")
    print()


def print_agent_route(source_agent: str, target_agent: str, query: str):
    """Print agent routing information."""
    print(f"{Colors.ORCHESTRATOR}🎯 Orchestrator:{Colors.RESET} Routing request from {Colors.BOLD}{source_agent}{Colors.RESET} → {Colors.BOLD}{target_agent}{Colors.RESET}")
    print(f"{Colors.ORCHESTRATOR}   Query:{Colors.RESET} {Colors.DIM}{query[:80]}{'...' if len(query) > 80 else ''}{Colors.RESET}")


def print_startup_banner():
    """Print the colored startup banner."""
    banner = f"""
{Colors.BOLD}{Colors.ORCHESTRATOR}╔══════════════════════════════════════════════════════════════╗{Colors.RESET}
{Colors.BOLD}{Colors.ORCHESTRATOR}║                                                              ║{Colors.RESET}
{Colors.BOLD}{Colors.ORCHESTRATOR}║    🤖 HUMAN VERIFIED AI AGENT - A2A PROTOCOL 🤖              ║{Colors.RESET}
{Colors.BOLD}{Colors.ORCHESTRATOR}║                                                              ║{Colors.RESET}
{Colors.BOLD}{Colors.ORCHESTRATOR}║    {Colors.WEATHER}🌐 Agent Network Communication{Colors.ORCHESTRATOR}                            ║{Colors.RESET}
{Colors.BOLD}{Colors.ORCHESTRATOR}║    {Colors.GATEWAY}🔐 Cryptographic Request Signing{Colors.ORCHESTRATOR}                          ║{Colors.RESET}
{Colors.BOLD}{Colors.ORCHESTRATOR}║    {Colors.LLM}🧠 Google Gemini LLM{Colors.ORCHESTRATOR}                                      ║{Colors.RESET}
{Colors.BOLD}{Colors.ORCHESTRATOR}║    {Colors.TRIP}✈️ Secure Trip Planning{Colors.ORCHESTRATOR}                                   ║{Colors.RESET}
{Colors.BOLD}{Colors.ORCHESTRATOR}║    {Colors.WEATHER}🌤️ Weather Information{Colors.ORCHESTRATOR}                                    ║{Colors.RESET}
{Colors.BOLD}{Colors.ORCHESTRATOR}║                                                              ║{Colors.RESET}
{Colors.BOLD}{Colors.ORCHESTRATOR}╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(banner)


def print_agent_status(agent_name: str, port: int, status: str = "STARTED"):
    """Print agent startup status."""
    if "weather" in agent_name.lower():
        printer = weather_printer
    elif "trip" in agent_name.lower():
        printer = trip_printer
    elif "llm" in agent_name.lower():
        printer = llm_printer
    else:
        printer = orchestrator_printer
    
    if status == "STARTED":
        printer.print_success(f"Agent started on http://localhost:{port}")
    elif status == "FAILED":
        printer.print_error(f"Failed to start agent on port {port}")
    else:
        printer.print_info(f"Agent status: {status} on port {port}")


# Utility functions for consistent formatting
def format_response(agent_name: str, response: str) -> str:
    """Format agent response with consistent styling."""
    if "weather" in agent_name.lower():
        color = Colors.WEATHER
        icon = "🌤️"
    elif "trip" in agent_name.lower():
        color = Colors.TRIP
        icon = "✈️"
    elif "llm" in agent_name.lower():
        color = Colors.LLM
        icon = "🧠"
    else:
        color = Colors.INFO
        icon = "🤖"
    
    return f"{color}{icon} {agent_name} Response:{Colors.RESET}\n{response}"


def print_separator(char: str = "─", length: int = 70, color: str = Colors.DIM):
    """Print a colored separator line."""
    print(f"{color}{char * length}{Colors.RESET}")


if __name__ == "__main__":
    # Test the color system
    print_startup_banner()
    print()
    
    # Test agent printers (old style)
    weather_printer.print_task("Getting weather for Paris")
    weather_printer.print_success("Weather data retrieved successfully")
    
    trip_printer.print_task("Planning trip to Tokyo")
    trip_printer.print_info("Contacting external travel API")
    trip_printer.print_success("Trip plan generated")
    
    llm_printer.print_task("Processing user query")
    llm_printer.print_warning("High token usage detected")
    llm_printer.print_success("AI response generated")
    
    print()
    print("Testing new simplified print pattern:")
    print()
    
    # Test new simplified print pattern
    weather_print.print_success("Weather agent using new print pattern")
    weather_print.print_info("This is much simpler!")
    weather_print.print_task("Processing weather request")
    
    trip_print.print_success("Trip agent using new print pattern")
    trip_print.print_info("Easy to use!")
    trip_print.print_task("Planning trip")
    
    gateway_printer.print_info("Signing outgoing request")
    gateway_printer.print_success("Request signed and sent")
    
    print_separator()
    print_task_start("Weather Agent", "Get weather for multiple cities")
    print_task_complete("Weather Agent", 2.34) 