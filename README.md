# HUMAN Verified AI Agent

> A multi-agent AI system showcasing cryptographically secure agent-to-service communication using HTTP Message Signatures and Google A2A protocol.

This repository is an open-source showcase of a multi-agent AI system that implements HTTP Message Signatures for authenticating agent requests to external services. It demonstrates a **Google A2A (Agent-to-Agent) architecture** with three specialized agents working together to provide comprehensive trip planning services.

## What are HTTP Message Signatures?

HTTP Message Signatures ([RFC 9421](https://www.rfc-editor.org/rfc/rfc9421#section-2.2.1)) provide a cryptographic method for verifying the authenticity and integrity of HTTP requests. Unlike traditional authentication methods that rely on API keys or tokens, HTTP Message Signatures use public-key cryptography to prove that a request came from a specific agent without revealing sensitive credentials.

The system is built on this RFC standard, with additional architectural considerations from the [Web Bot Authentication Architecture draft](https://datatracker.ietf.org/doc/draft-meunier-web-bot-auth-architecture/).

The overall goal is to provide a robust and verifiable way for AI agents to identify themselves to external web services, moving beyond IP-based or User-Agent-based identification methods.

## What You'll Learn

By exploring this project, you'll understand:

- How to implement HTTP Message Signatures for AI agent authentication
- Multi-agent architecture patterns using Google A2A protocol
- Cryptographic key management for individual agents
- Secure agent-to-external-service communication patterns
- Real-world application of RFC 9421 standards

## What This Demo Shows

**A Multi-Agent Architecture with Individual Agent Keys**

This showcase demonstrates a **Google A2A (Agent-to-Agent) protocol** implementation with three specialized agents:

1. **LLM Agent** (Orchestrator): Coordinates the trip planning process using AI
2. **Weather Agent**: Provides current weather information for cities
3. **Attractions Agent**: Retrieves points of interest and attractions for cities

**Key Features:**
- **Individual Agent Keys**: Each agent has its own unique Ed25519 key pair in JWK format
- **Cryptographic Authentication**: Agents use HTTP Message Signatures when communicating with external services
- **Secure Request Gateway**: A gateway service validates signatures and routes requests to external APIs
- **Agent Orchestration**: The LLM agent combines weather and attractions data to create comprehensive itineraries
- **ANS (Agent Name Service)**: Each agent implements secure naming following the [OWASP ANS v1.0 standard](https://genai.owasp.org/resource/agent-name-service-ans-for-secure-al-agent-discovery-v1-0/) for structured agent identification. The agents use hierarchical names like `forecast.weather.v1.human-security.com` and `planner.trip.v1.human-security.com` to enable secure agent discovery and authentication. This naming system provides a DNS-inspired framework for AI agent identity management that scales across distributed systems.

**Demo Key Management:**
This showcase is designed to work out-of-the-box using demonstration key-pairs. Each agent has its own private key in the `keys/` directory, with corresponding public keys pre-configured on HUMAN's registry. This approach allows you to immediately experience the multi-agent HTTP Message Signatures protocol in action without needing to set up your own certificate authority or key management infrastructure.

**Why this approach is necessary for the demo:**
- No agent registry or certificate authority currently exists in production for this protocol
- The verifier service needs to trust and validate signatures using known public keys
- This demo setup lets you focus on understanding the multi-agent signature protocol rather than key management complexity

In a production environment, each agent would have its own unique key-pair issued through a proper certificate authority, but for learning and demonstration purposes, these demo key-pairs provide the simplest path to understanding the architecture.

**⚠️ Important Note:** This is a demonstration project designed for learning and evaluation purposes. While the cryptographic implementations are production-ready, the key management and agent registry components are simplified for educational use.

### For Commercial AI Agent Companies

If you are a commercial AI agent company and would like your AI agents' messages to be verified cryptographically by HUMAN, please submit a verification request via this form: https://forms.gle/1MLRFqjzDpaooaK79

## Quick Start

### Prerequisites

*   Python 3.8 or higher
*   Google API key (required for the LLM Agent orchestrator functionality)

### Setup

1.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    pip3 install -r requirements.txt
    ```

3.  **Configure environment variables:**
    Create a `.env` file in the root of the project. You can use the `.env.example` file as a template.
    ```bash
    cp .env.example .env
    ```
    You will need to populate the `.env` file with the following:
    *   `GOOGLE_API_KEY`: A valid Google API key for using the underlying language model (needed for LLM Agent orchestrator).
    *   `AGENT_VERIFIER_ADDRESS`: The network address (URL) of the verifier component. This value is populated for you, using HUMAN's existing service.
    *   `AGENT_HOSTED_DOMAIN`: The domain from which the verifier will pull the public keys. This is used in the `Signature-Agent` header to indicate where verifiers can find your agents' public keys for signature validation.

## Usage Examples

### 1. Multi-Agent Trip Planner Showcase (Full AI Experience)

The main showcase demonstrates a complete multi-agent system with three specialized agents working together:

```bash
python -m showcases.a2a_showcase
```

**What it does:**
1. Prompts you for a destination city
2. **LLM Agent** (Orchestrator) coordinates the trip planning process
3. **Weather Agent** fetches current weather conditions for the city from external APIs using signed requests
4. **Attractions Agent** retrieves points of interest and attractions from external APIs using signed requests
5. **LLM Agent** combines both data sources to create a comprehensive, weather-aware itinerary
6. External service communications are secured using HTTP Message Signatures with individual agent keys
7. Presents a complete trip plan considering both attractions and weather conditions

**Requirements:** Google API key needed for AI functionality.

### 2. Simple Verification Success (Minimal Example)

Test the signature verification flow with proper agent identification:

```bash
python -m showcases.simple_success_showcase
```

**What it does:** Sends a signed POST request to the verifier's `/verify` endpoint **with** proper agent domain identification, demonstrating successful signature verification.

**Requirements:** No Google API key needed.

### 3. Simple Verification Failure (Error Demonstration)

Test what happens when agent identification is missing:

```bash
python -m showcases.simple_failure_showcase
```

**What it does:** Sends a signed POST request **without** agent domain identification, demonstrating how verification fails when the verifier cannot locate the public key.

**Requirements:** No Google API key needed.

## Architecture & Technical Details

### Multi-Agent Architecture

This implementation demonstrates a **Google A2A (Agent-to-Agent) protocol** with three specialized agents:

1. **LLM Agent** (`showcases/agents/llm_agent.py`): The orchestrator that coordinates trip planning by calling other agents
2. **Weather Agent** (`showcases/agents/weather_agent.py`): Provides weather information by fetching data from external APIs
3. **Attractions Agent** (`showcases/agents/trip_agent.py`): Provides attractions data by fetching data from external APIs

**Communication Architecture:**
- **Agent-to-Agent**: LLM Agent communicates with Weather and Attractions Agents using standard Google A2A protocol (HTTP/JSON)
- **Agent-to-External-Service**: Weather and Attractions Agents communicate with external APIs through a verifier service using HTTP Message Signatures for authentication

**Communication Flow:**
1. **LLM Agent** → **Weather Agent** (A2A Protocol, no signatures)
2. **Weather Agent** → **Verifier Service** → **External Weather API** (HTTP Message Signatures)
3. **LLM Agent** → **Attractions Agent** (A2A Protocol, no signatures)  
4. **Attractions Agent** → **Verifier Service** → **External Attractions API** (HTTP Message Signatures)

### Project Structure

```
human-verified-ai-agent/
├── agent_key_manager.py         # Core key management infrastructure
├── request_signer.py            # Core HTTP Message Signatures infrastructure
├── request_orchestrator.py      # Core request orchestration infrastructure
├── keys/                        # Individual agent JWK key pairs
│   ├── private_ed25519_pem_llm_agent
│   ├── private_ed25519_pem_weather_agent
│   ├── private_ed25519_pem_trip_agent
│   └── [public keys with key_id filenames]
└── showcases/                   # Multi-agent showcase implementation
    ├── a2a_showcase.py          # Main A2A demo entry point
    ├── agents/                  # Agent implementations
    │   ├── llm_agent.py         # LLM orchestrator agent
    │   ├── weather_agent.py     # Weather information agent
    │   └── trip_agent.py        # Attractions/trip planning agent
    └── utils/                   # Showcase utilities
        ├── agent_colors.py      # Agent output formatting
        ├── request_gateway.py   # Request routing and validation
        ├── secure_agent_base.py # Base agent functionality
        └── system_instructions.py # Agent system prompts
```

**Core Infrastructure Components:**
1. **Agent Key Manager** (`agent_key_manager.py`): Generates and manages individual Ed25519 key pairs in JWK format
2. **Request Signer** (`request_signer.py`): Handles HTTP Message Signatures for all agent communications
3. **Request Orchestrator** (`request_orchestrator.py`): Coordinates signed request sending and verification
4. **A2A Showcase** (`showcases/a2a_showcase.py`): Main entry point demonstrating the complete multi-agent system

**Showcase Components:**
1. **Individual Agents** (`showcases/agents/`): Three specialized agents with their own keys and responsibilities
2. **Request Gateway** (`showcases/utils/request_gateway.py`): Routes and validates signed requests between agents
3. **Agent Utilities** (`showcases/utils/`): Supporting utilities for agent operation and display

**Key Features:**
- Each agent has its own unique Ed25519 key pair stored in JWK format
- External service communication uses HTTP Message Signatures for authentication
- Request gateway validates signatures and routes requests to external APIs
- Google A2A protocol compatibility for agent-to-agent communication
- Clean separation between core infrastructure and showcase implementation

### Agent Keys

The system generates individual keys for each agent using the core `agent_key_manager.py` infrastructure:

- **LLM Agent**: `keys/9i2hRtJ6sUUO2fK1ZJyXdUGJK1kwI1wVRoe9VDhX4yY` (JWK format)
- **Weather Agent**: `keys/aAVQ596pKliWDfyo89RNTromrwqQMyD45YI36ldcCeo` (JWK format)  
- **Attractions Agent**: `keys/DTNGykza-ch_trY8qfZwXRojdNa4R06CtC_ixX0VwuE` (JWK format)

Each key file contains the private key in JWK format, with the filename being the key_id (JWK thumbprint). The corresponding public keys are registered with HUMAN's verification service using the same key_id for identification.

**Key Management Features:**
- Individual Ed25519 key pairs for each agent
- JWK format for web-compatible key handling
- Key_id-based public key filenames for efficient lookup
- Centralized key management through `agent_key_manager.py`
- Automatic key generation and conversion utilities

**Note on Current Implementation:** The current implementation is simplified and does not include an agent registry, certificate management, or domain validation features. A complete registry system would typically handle the entire agent lifecycle, including registration, certificate renewal, and revocation processes. These enhanced security features are planned for future integration.

### HTTP Message Signatures Configuration

This multi-agent implementation uses [RFC 9421: HTTP Message Signatures](https://www.rfc-editor.org/rfc/rfc9421#section-2.2.1) to cryptographically sign requests to external services. Each agent has its own unique Ed25519 key pair in JWK format, and communications with external APIs are signed and verified through the verifier service. The signature covers specific HTTP components, and you can configure which components are included based on your security requirements.

#### Covered Components

The library provides three predefined component sets:

- **`MINIMAL_COMPONENTS`**: `["@authority"]` - The absolute minimum required by the specification
- **`BOT_AUTH_COMPONENTS`**: `["@authority", "signature-agent"]` - **Recommended for bot authentication** (follows [Cloudflare's guidance](https://blog.cloudflare.com/web-bot-auth/))
- **`ENHANCED_COMPONENTS`**: `["@authority", "signature-agent", "@method", "@path"]` - For enhanced security when needed

#### Smart Defaults

The signing process automatically selects appropriate components:

- **When using `signature_agent`** (bot authentication): Uses `BOT_AUTH_COMPONENTS`
- **When not using `signature_agent`**: Falls back to `MINIMAL_COMPONENTS`
- **Custom configuration**: You can specify exact components as needed

#### Customizing Covered Components

To customize which HTTP components are included in the signature, you can modify the `sign_request` calls in the showcase files or use the predefined constants:

```python
from request_signer import MINIMAL_COMPONENTS, BOT_AUTH_COMPONENTS, ENHANCED_COMPONENTS

# Use predefined sets
sign_request(req, covered_components=ENHANCED_COMPONENTS)

# Or specify custom components
sign_request(req, covered_components=["@authority", "signature-agent", "@method", "content-type"])
```

The `@authority` component (target domain) is always required as per the HTTP Message Signatures specification. Including `signature-agent` is strongly recommended for bot authentication as it helps verifiers locate your public key.

### Enhanced Architecture & Organization

This implementation features a **professional, scalable architecture** with clear separation of concerns:

#### Core Infrastructure (Root Level)
- **`agent_key_manager.py`**: Complete key management system for generating, loading, and managing individual agent keys
- **`request_signer.py`**: HTTP Message Signatures implementation following RFC 9421 standards
- **`request_orchestrator.py`**: High-level request coordination and verification handling

#### Showcase Implementation (showcases/)
- **`a2a_showcase.py`**: Main demo orchestrating all three agents working together
- **`agents/`**: Individual agent implementations with specialized responsibilities
- **`utils/`**: Supporting utilities for agent operation, formatting, and request handling

#### Benefits of This Organization
- **Modularity**: Clear separation between core infrastructure and showcase implementation
- **Reusability**: Core components can be easily extracted and used in other projects
- **Maintainability**: Related functionality grouped together with logical dependencies
- **Scalability**: Easy to add new agents or modify existing ones without affecting core infrastructure
- **Professional Structure**: Follows industry best practices for Python project organization

## Troubleshooting

### Common Issues

**Import Errors:**
- Ensure you've activated your virtual environment: `source .venv/bin/activate`
- Install all dependencies: `pip3 install -r requirements.txt`

**Google API Key Issues:**
- Verify your API key is valid and has the necessary permissions
- Check that the `.env` file is properly configured with `GOOGLE_API_KEY`

**Agent Communication Errors:**
- Verify that all agent keys are present in the `keys/` directory
- Check that the verifier service is accessible via the configured `AGENT_VERIFIER_ADDRESS`

## Contributing

This is an open-source project, and contributions are welcome! Here's how you can help:

- **Report bugs**: Open an issue with details about the problem
- **Suggest features**: Share ideas for new functionality or improvements
- **Submit pull requests**: Fix bugs or add features (please include tests)
- **Improve documentation**: Help make the README and code comments clearer

Please feel free to open issues or submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT
