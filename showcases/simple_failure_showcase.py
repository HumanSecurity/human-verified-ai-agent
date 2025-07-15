import os
import requests
from dotenv import load_dotenv

# Assuming send_request is in request_orchestrator and will be modified
# to accept a key_path argument.
from request_orchestrator import send_request

def simple_failure_request_flow() -> str:
    """
    Demonstrates a request flow that will fail verification.
    Does not include agent domain to show failure handling.
    
    Returns:
        Response from the verification server (expected to be an error)
    """
    agent_verifier_base_url = os.getenv("AGENT_VERIFIER_ADDRESS")
    if not agent_verifier_base_url:
        raise ValueError("AGENT_VERIFIER_ADDRESS environment variable not set.")

    verify_url = f"{agent_verifier_base_url}/verify"
    print(f"Signer: Preparing and Sending Signed Request to: {verify_url}")

    req = requests.Request(
        method="POST",
        url=verify_url
    )
    return send_request(request=req, signature_agent=None)

if __name__ == "__main__":
    load_dotenv()
    try:
        result = simple_failure_request_flow()
        print(f"Request completed. Result: {result}")
        print("Note: This flow was expected to fail at the server due to incorrect key usage.")
    except Exception as e:
        print(f"Request failed due to an error: {e}") 