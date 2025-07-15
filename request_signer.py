"""
Handles the creation of HTTP Message Signatures for requests.

This module provides the necessary classes and functions to sign a request object
(specifically a requests.PreparedRequest) according to the HTTP Message Signatures
specification, using Ed25519 algorithm and a key resolver pattern.
"""
import base64
import collections
import datetime
import os
from typing import Any, Dict, List, Optional, Sequence, Type

import requests
import http_sfv
from cryptography.hazmat.primitives.asymmetric import ed25519

# ANSI color codes for console output
class Colors:
    SIGNER = '\033[94m'  # Blue
    LLM = '\033[92m'     # Green
    RESET = '\033[0m'    # Reset to default color

def print_signer(message: str):
    """Print a signer message in blue color."""
    print(f"{Colors.SIGNER}{message}{Colors.RESET}")

def print_llm(message: str):
    """Print an LLM message in green color."""
    print(f"{Colors.LLM}{message}{Colors.RESET}")

from agent_key_manager import get_key_id_ed25519, get_private_key_ed25519
from http_message_signatures import (
    algorithms,
    HTTPSignatureAlgorithm,
    HTTPSignatureKeyResolver,
    HTTPSignatureComponentResolver,
    HTTPMessageSignaturesException
)

# Standard HTTP signature components for different security levels
MINIMAL_COMPONENTS = ["@authority"]
BOT_AUTH_COMPONENTS = ["@authority", "signature-agent"]  # Recommended for bot authentication
ENHANCED_COMPONENTS = ["@authority", "signature-agent", "@method", "@path"]

default_expiry_days_interval = 1

class HTTPSignatureHandler:
    """Base handler for HTTP message signature operations."""
    signature_metadata_parameters = {"alg", "created", "expires", "keyid", "nonce", "tag"}

    def __init__(
        self,
        *,
        signature_algorithm: Type[HTTPSignatureAlgorithm],
        key_resolver: HTTPSignatureKeyResolver,
        component_resolver_class: type = HTTPSignatureComponentResolver
    ):
        self.signature_algorithm = signature_algorithm
        self.key_resolver = key_resolver
        self.component_resolver_class = component_resolver_class

    def _build_signature_base(
        self, message, *, covered_component_ids: list, signature_params: Dict[str, str]
    ) -> tuple:
        """Constructs the signature base string according to RFC 9421."""
        if "@signature-params" in covered_component_ids:
            raise AssertionError("@signature-params should not be in covered_component_ids")
        if "@authority" not in [str(cid.value if hasattr(cid, 'value') else cid) for cid in covered_component_ids]:
            raise AssertionError("@authority must be in covered_component_ids")
        
        sig_elements = collections.OrderedDict()
        component_resolver = self.component_resolver_class(message)
        
        for component_id_node in covered_component_ids:
            component_key = str(http_sfv.List([component_id_node]))
            component_value = component_resolver.resolve(component_id_node)
            
            if isinstance(component_id_node.value, str) and component_id_node.value.lower() != component_id_node.value:
                raise HTTPMessageSignaturesException(f'Component ID "{component_id_node.value}" is not all lowercase.'
                      ' While the spec allows mixed case, lowercase is recommended for consistency.')

            if "\n" in component_key:
                raise HTTPMessageSignaturesException(f'Component ID "{component_key}" contains newline character.')
            if component_key in sig_elements:
                raise HTTPMessageSignaturesException(
                    f'Component ID "{component_key}" appeared multiple times in signature input.'
                )
            sig_elements[component_key] = component_value
            
        sig_params_node = http_sfv.InnerList(covered_component_ids)
        sig_params_node.params.update(signature_params)
        sig_elements['"@signature-params"'] = str(sig_params_node)
        
        sig_base = "\n".join(f"{k}: {v}" for k, v in sig_elements.items())
        return sig_base, sig_params_node, sig_elements


def _parse_covered_component_ids(covered_component_ids_str: Sequence[str]) -> List[http_sfv.Item]:
    """Parses string component IDs into http_sfv.Item objects."""
    covered_component_nodes = []
    for component_id_str in covered_component_ids_str:
        component_name_node = http_sfv.Item()
        # HTTP SFV Items that are tokens (like @authority) don't start with ", derived names do.
        if component_id_str.startswith('"'):
            component_name_node.parse(component_id_str.encode())
        else:
            component_name_node.value = component_id_str
        covered_component_nodes.append(component_name_node)
    return covered_component_nodes


class HTTPMessageSigner(HTTPSignatureHandler):
    """Signs HTTP messages using a specified algorithm and key resolver."""
    DEFAULT_SIGNATURE_LABEL = "sig1"
    MANDATORY_TAG = "web-bot-auth"

    def sign(
        self,
        message: Any, # Should have a .headers attribute (dict-like)
        *,
        key_id: str,
        created: datetime.datetime,
        expires: datetime.datetime,
        nonce: Optional[str] = '',
        tag: str = MANDATORY_TAG,
        label: Optional[str] = DEFAULT_SIGNATURE_LABEL,
        include_alg: bool = True,
        covered_component_ids: Sequence[str] = ("@authority",),
        signature_agent_value: Optional[str] = None,
        agent_name: Optional[str] = None,
    ):
        """Signs the given message and adds Signature, Signature-Input headers and optionally Signature-Agent."""
        
        print_signer("Signer: Initializing signature process...")
        
        key = self.key_resolver.resolve_private_key(key_id)
        if created is None:
            created = datetime.datetime.now(datetime.timezone.utc)

        # Add custom headers before processing covered components
        headers_added = []

        if agent_name:
            message.headers["X-Agent-Name"] = agent_name
            headers_added.append(f"X-Agent-Name: {agent_name}")

        if signature_agent_value:
            message.headers["Signature-Agent"] = signature_agent_value
            headers_added.append(f"Signature-Agent: {signature_agent_value}")

        processed_covered_component_ids_str = list(covered_component_ids)

        # Auto-add signature-agent to covered components if present in headers
        if "Signature-Agent" in message.headers and "signature-agent" not in processed_covered_component_ids_str:
            if not any(item.strip('"') == "signature-agent" for item in processed_covered_component_ids_str):
                 processed_covered_component_ids_str.append("signature-agent")

        print_signer(f"Signer: Final covered components: {processed_covered_component_ids_str}")

        print_signer("Signer: Building signature parameters...")
        
        signature_params_dict: Dict[str, Any] = collections.OrderedDict()
        signature_params_dict["created"] = int(created.timestamp())
        if expires:
            signature_params_dict["expires"] = int(expires.timestamp())
        signature_params_dict["keyid"] = key_id
        if nonce:
            signature_params_dict["nonce"] = nonce
        signature_params_dict["tag"] = tag
        if include_alg:
            signature_params_dict["alg"] = self.signature_algorithm.algorithm_id

        print_signer(f"Signer: Signature parameters: {dict(signature_params_dict)}")

        print_signer("Signer: Constructing signature base string...")
        
        parsed_covered_component_nodes = _parse_covered_component_ids(processed_covered_component_ids_str)
        
        sig_base, sig_params_sfv_node, _ = self._build_signature_base(
            message, 
            covered_component_ids=parsed_covered_component_nodes, 
            signature_params=signature_params_dict
        )
        
        print_signer("Signer: Generating cryptographic signature...")
        
        signer = self.signature_algorithm(private_key=key)
        signature_bytes = signer.sign(sig_base.encode("utf-8"))

        print_signer("Signer: Applying signature headers to request...")

        sig_input_sfv_dict = http_sfv.Dictionary({label: sig_params_sfv_node})
        message.headers["Signature-Input"] = str(sig_input_sfv_dict)
        
        sig_sfv_dict = http_sfv.Dictionary({label: signature_bytes})
        message.headers["Signature"] = str(sig_sfv_dict)
        
        print_signer("Signer: HTTP Message Signature successfully created and applied")


class StaticKeyResolver(HTTPSignatureKeyResolver):
    """A simple key resolver that can use a specified key path or a default static private key."""
    def __init__(self, key_path: Optional[str] = None):
        self.key_path = key_path

    def resolve_private_key(self, key_id: str) -> ed25519.Ed25519PrivateKey:
        if self.key_path:
            return get_private_key_ed25519(key_path=self.key_path)
        return get_private_key_ed25519()


def sign_request(
    req_to_sign: requests.PreparedRequest,
    signature_agent: Optional[str] = None,
    key_path_for_signature: Optional[str] = None,
    covered_components: Optional[Sequence[str]] = None,
    agent_name: Optional[str] = None
) -> None:
    """
    Signs an HTTP request using Ed25519 signature according to HTTP Message Signatures specification.
    
    Args:
        req_to_sign: The prepared request to sign
        signature_agent: Domain name of the signing agent
        key_path_for_signature: Path to private key file (optional)
        covered_components: Custom list of HTTP components to include in signature
        :param req_to_sign:
        :param signature_agent:
        :param key_path_for_signature:
        :param covered_components:
        :param agent_name:
    """
    print("\n" + "="*60)
    print_signer("🔐 SIGNER: Starting HTTP Message Signature signing process")
    print("="*60)
    
    print_signer("Signer: Loading cryptographic keys and configuration...")
    
    # Use the key_id from the specific key file if a key path is provided
    if key_path_for_signature:
        key_id_for_signature = get_key_id_ed25519(key_path_for_signature)
    else:
        key_id_for_signature = get_key_id_ed25519()
    
    print_signer(f"Signer: Using key ID: {key_id_for_signature}")

    print_signer("Signer: Generating secure nonce for replay protection...")
    
    nonce_bytes = os.urandom(32)
    generated_nonce_value = base64.b64encode(nonce_bytes).decode('ascii')

    print_signer("Signer: Initializing signature algorithm and key resolver...")

    signer_instance = HTTPMessageSigner(
        signature_algorithm=algorithms.ED25519,
        key_resolver=StaticKeyResolver(key_path=key_path_for_signature)
    )

    # Determine which HTTP components to include in the signature
    if covered_components is None:
        if signature_agent:
            components_to_use = BOT_AUTH_COMPONENTS
            print_signer(f"Signer: Using BOT_AUTH_COMPONENTS (auto-selected): {components_to_use}")
        else:
            components_to_use = MINIMAL_COMPONENTS
            print_signer(f"Signer: Using MINIMAL_COMPONENTS (auto-selected): {components_to_use}")
    else:
        components_to_use = covered_components
        print_signer(f"Signer: Using custom covered components: {list(components_to_use)}")

    print_signer("Signer: Setting up signature timestamps and validity period...")

    current_time = datetime.datetime.now(datetime.timezone.utc)
    expiration_time = current_time + datetime.timedelta(days=default_expiry_days_interval)

    print_signer("Signer: Proceeding to cryptographic signature generation...")

    signer_instance.sign(
        req_to_sign,
        key_id=key_id_for_signature,
        created=current_time,
        expires=expiration_time,
        covered_component_ids=list(components_to_use),
        nonce=generated_nonce_value,
        signature_agent_value=signature_agent,
        agent_name=agent_name
    )
    print_signer("Signer: Request signing process completed successfully")
    
    # Display complete request headers for verification
    print_signer("\n📋 COMPLETE REQUEST HEADERS:")
    print("-" * 60)
    for header_name, header_value in req_to_sign.headers.items():
        print_signer(f"  {header_name}: {header_value}")
    print("-" * 60)
    
    print("="*60)
    print_signer("🔐 SIGNER: HTTP Message Signature process COMPLETED")
    print("="*60 + "\n")










