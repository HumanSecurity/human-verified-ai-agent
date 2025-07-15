import os
import requests
from request_signer import sign_request, print_signer
from typing import Optional

def send_request(request: requests.Request, key_path: Optional[str] = None, signature_agent: Optional[str] = None, agent_name: Optional[str] = None) -> str:
    """
    Sends a signed HTTP request to the verification endpoint.
    
    Args:
        request: The HTTP request to send
        key_path: Optional path to private key file
        signature_agent: Domain name of the signing agent
        
    Returns:
        Response text from the server or error message
    """
    verify_url = request.url
    try:
        session = requests.Session()
        prepared_req = session.prepare_request(request)
        
        print_signer("System: Request prepared, transitioning to signature phase...")
        
        sign_request(prepared_req, key_path_for_signature=key_path, signature_agent=signature_agent, agent_name=agent_name)

        print_signer("Signer: Signed request ready, sending to verification endpoint...")

        response_signed_req = session.send(prepared_req)
        response_signed_req.raise_for_status()
        print("System: Message verified successfully")
        return response_signed_req.text

    except requests.exceptions.HTTPError as http_err:
        error_content = "<Could not decode error response content>"
        if hasattr(http_err, 'response') and http_err.response is not None and http_err.response.content:
            try:
                error_content = http_err.response.content.decode('utf-8')
            except UnicodeDecodeError:
                error_content = f"<Binary content or undecodable text: {len(http_err.response.content)} bytes>"
        print(f"Error during sending signed request to {verify_url}: {error_content}")
        return f"Response content: {error_content}"
    except requests.exceptions.ConnectionError as conn_err:
        return f"Could not connect to {verify_url}. Error: {conn_err}"
    except requests.exceptions.Timeout as timeout_err:
        return f"Request to {verify_url} timed out. Error: {timeout_err}"
    except requests.exceptions.RequestException as req_err:
        return f"An unexpected error occurred during the signed request to {verify_url}. Error: {req_err}"
    except Exception as e:
        return f"An unexpected non-request error occurred while preparing/sending request: {e}"
