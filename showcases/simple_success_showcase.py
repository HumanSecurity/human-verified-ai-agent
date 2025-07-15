import os
import requests
from dotenv import load_dotenv

from request_orchestrator import *

def simple_request_flow() -> str:
    """
    Demonstrates a simple successful signed request flow.
    
    Returns:
        Response from the verification server
    """
    agent_verifier_base_url = os.getenv("AGENT_VERIFIER_ADDRESS")
    if not agent_verifier_base_url:
        raise ValueError("AGENT_VERIFIER_ADDRESS environment variable not set.")

    verify_url = f"{agent_verifier_base_url}/verify"
    print(f"Signer: Preparing and Sending Signed Request to: {verify_url}")

    signature_agent = os.environ.get('AGENT_HOSTED_DOMAIN', None)

    req = requests.Request(
        method="POST",
        url=verify_url
    )
    return send_request(request=req, signature_agent=signature_agent)


if __name__ == "__main__":
    load_dotenv()
    try:
        result = simple_request_flow()
        print(f"Request completed successfully")
    except Exception as e:
        print(f"Request failed due to an error: {e}")