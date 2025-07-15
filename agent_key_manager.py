import json
import hashlib
import base64
import os
from typing import Dict, Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from jwcrypto import jwk

"""
DEMO SECURITY NOTE:
==================
This implementation uses hardcoded cryptographic keys stored in the 'keys/' directory
for demonstration purposes only. In a production environment, keys should be:

1. Generated dynamically and stored securely
2. Never committed to version control
3. Rotated regularly
4. Protected with proper access controls and encryption at rest

The current approach is acceptable for showcasing the HTTP Message Signatures 
authentication flow, but should NOT be used in production systems.
"""


def get_private_key_ed25519(key_path="private_ed25519_pem") -> ed25519.Ed25519PrivateKey:
    """
    Load a private key from either PEM or JWK format.
    
    Args:
        key_path: Path to the private key file
        
    Returns:
        Ed25519PrivateKey object
    """
    # Construct path relative to the keys directory, if not absolute.
    if not os.path.isabs(key_path):
        # Get the project root directory (same as current file location)
        project_root = os.path.dirname(os.path.realpath(__file__))
        keys_dir = os.path.join(project_root, "keys")
        
        # Prevent path duplication if key_path already contains 'keys/'
        if 'keys' in key_path:
            key_path = os.path.join(project_root, key_path)
        else:
            key_path = os.path.join(keys_dir, key_path)

    # Try to load as JWK first, then fall back to PEM
    try:
        with open(key_path, "r") as f:
            jwk_data = json.load(f)
            jwk_key = jwk.JWK.from_json(json.dumps(jwk_data))
            return jwk_key.get_op_key('sign')
    except (json.JSONDecodeError, KeyError):
        # Fall back to PEM format
        with open(key_path, "rb") as pem_file:
            pem_bytes_data = pem_file.read()
        
        private_key_ed25519: ed25519.Ed25519PrivateKey = serialization.load_pem_private_key(
            pem_bytes_data,
            password=None
        )
        return private_key_ed25519


def get_key_id_ed25519(private_key_path: Optional[str] = None) -> str:
    """
    Generate key_id from a private key file using JWK thumbprint.
    
    Args:
        private_key_path: Path to the private key file. If None, uses default.
    
    Returns:
        Base64url-encoded SHA256 hash of the JWK public key (key_id)
    """
    if private_key_path:
        public_key: ed25519.Ed25519PublicKey = get_private_key_ed25519(private_key_path).public_key()
    else:
        public_key: ed25519.Ed25519PublicKey = get_private_key_ed25519().public_key()
    
    public_jwk_ed25519_obj: jwk.JWK = jwk.JWK.from_pyca(public_key)
    public_jwk_dict: Dict[str, str] = public_jwk_ed25519_obj.export_public(as_dict=True)

    jwk_thumbprint_input = {k: v for k, v in public_jwk_dict.items() if k != 'kid'}
    encoded_jwk = json.dumps(jwk_thumbprint_input, sort_keys=True, separators=(',', ':')).encode("utf-8")
    thumbprint = hashlib.sha256(encoded_jwk).digest()
    return base64.urlsafe_b64encode(thumbprint).rstrip(b"=").decode("utf-8")


def get_agent_private_key_ed25519(agent_name: str) -> ed25519.Ed25519PrivateKey:
    """
    Get the private key for a specific agent.
    
    Args:
        agent_name: Name of the agent (e.g., 'weather_agent', 'trip_agent', 'llm_agent')
    
    Returns:
        Ed25519PrivateKey object for the agent
    """
    key_path = f"private_ed25519_pem_{agent_name}"
    return get_private_key_ed25519(key_path)


def get_agent_key_id_ed25519(agent_name: str) -> str:
    """
    Get the key_id for a specific agent.
    
    Args:
        agent_name: Name of the agent (e.g., 'weather_agent', 'trip_agent', 'llm_agent')
    
    Returns:
        Base64url-encoded key_id for the agent
    """
    key_path = f"private_ed25519_pem_{agent_name}"
    return get_key_id_ed25519(key_path)


def generate_agent_keypair(agent_name: str) -> Dict[str, str]:
    """
    Generate a new Ed25519 keypair for an agent in JWK format.
    
    Args:
        agent_name: Name of the agent (e.g., 'weather_agent', 'trip_agent', 'llm_agent')
    
    Returns:
        Dictionary with 'private_key_path', 'public_key_path', and 'key_id'
    """
    # Generate new Ed25519 private key
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Convert to JWK format
    private_jwk = jwk.JWK.from_pyca(private_key)
    public_jwk = jwk.JWK.from_pyca(public_key)
    
    # Export as JWK dictionaries
    private_jwk_dict = private_jwk.export(as_dict=True)
    public_jwk_dict = public_jwk.export_public(as_dict=True)
    
    # Define file paths - point to the keys directory in project root
    project_root = os.path.dirname(os.path.realpath(__file__))
    keys_dir = os.path.join(project_root, "keys")
    private_key_path = os.path.join(keys_dir, f"private_ed25519_pem_{agent_name}")
    
    # Write private key to file as JWK
    with open(private_key_path, "w") as f:
        json.dump(private_jwk_dict, f, indent=2)
    
    # Generate key_id using the written private key
    key_id = get_agent_key_id_ed25519(agent_name)
    
    # Use key_id as the public key filename
    public_key_path = os.path.join(keys_dir, key_id)
    
    # Write public key to file as JWK with key_id as filename
    with open(public_key_path, "w") as f:
        json.dump(public_jwk_dict, f, indent=2)
    
    print(f"Generated JWK keypair for {agent_name}:")
    print(f"  Private key: {private_key_path}")
    print(f"  Public key: {public_key_path}")
    print(f"  Key ID: {key_id}")
    
    return {
        'private_key_path': private_key_path,
        'public_key_path': public_key_path,
        'key_id': key_id,
        'agent_name': agent_name
    }


def generate_all_agent_keypairs() -> Dict[str, Dict[str, str]]:
    """
    Generate JWK keypairs for all agents in the system.
    
    Returns:
        Dictionary mapping agent names to their key information
    """
    agents = ['weather_agent', 'trip_agent', 'llm_agent']
    all_keys = {}
    
    print("Generating Ed25519 JWK keypairs for all agents...")
    print("=" * 60)
    
    for agent in agents:
        all_keys[agent] = generate_agent_keypair(agent)
        print()
    
    print("=" * 60)
    print("All agent JWK keypairs generated successfully!")
    
    return all_keys


def list_agent_keys() -> Dict[str, Dict[str, str]]:
    """
    List all existing agent keys and their key_ids.
    
    Returns:
        Dictionary mapping agent names to their key information
    """
    agents = ['weather_agent', 'trip_agent', 'llm_agent']
    keys_info = {}
    
    print("Agent JWK Key Information:")
    print("=" * 60)
    
    for agent in agents:
        try:
            key_id = get_agent_key_id_ed25519(agent)
            # Point to the keys directory in project root
            project_root = os.path.dirname(os.path.realpath(__file__))
            keys_dir = os.path.join(project_root, "keys")
            private_key_path = os.path.join(keys_dir, f"private_ed25519_pem_{agent}")
            public_key_path = os.path.join(keys_dir, key_id)  # Use key_id as filename
            
            keys_info[agent] = {
                'private_key_path': private_key_path,
                'public_key_path': public_key_path,
                'key_id': key_id,
                'agent_name': agent
            }
            
            print(f"🔐 {agent.replace('_', ' ').title()}:")
            print(f"  Key ID: {key_id}")
            print(f"  Private: {private_key_path}")
            print(f"  Public:  {public_key_path}")
            print()
            
        except FileNotFoundError:
            print(f"❌ {agent.replace('_', ' ').title()}: Keys not found")
            print()
    
    return keys_info


def convert_pem_to_jwk(pem_file_path: str, jwk_file_path: str, is_private: bool = True) -> str:
    """
    Convert a PEM key file to JWK format.
    
    Args:
        pem_file_path: Path to the PEM key file
        jwk_file_path: Path where the JWK file should be saved
        is_private: Whether this is a private key (True) or public key (False)
    
    Returns:
        The key_id of the converted key
    """
    # Read PEM file
    with open(pem_file_path, "rb") as f:
        pem_data = f.read()
    
    if is_private:
        # Load private key
        private_key = serialization.load_pem_private_key(pem_data, password=None)
        jwk_key = jwk.JWK.from_pyca(private_key)
        jwk_dict = jwk_key.export(as_dict=True)
    else:
        # Load public key
        public_key = serialization.load_pem_public_key(pem_data)
        jwk_key = jwk.JWK.from_pyca(public_key)
        jwk_dict = jwk_key.export_public(as_dict=True)
    
    # Save as JWK
    with open(jwk_file_path, "w") as f:
        json.dump(jwk_dict, f, indent=2)
    
    # Return key_id
    if is_private:
        public_jwk = jwk.JWK.from_pyca(private_key.public_key())
    else:
        public_jwk = jwk_key
    
    public_jwk_dict = public_jwk.export_public(as_dict=True)
    jwk_thumbprint_input = {k: v for k, v in public_jwk_dict.items() if k != 'kid'}
    encoded_jwk = json.dumps(jwk_thumbprint_input, sort_keys=True, separators=(',', ':')).encode("utf-8")
    thumbprint = hashlib.sha256(encoded_jwk).digest()
    return base64.urlsafe_b64encode(thumbprint).rstrip(b"=").decode("utf-8")


def convert_all_pem_to_jwk() -> None:
    """
    Convert all existing PEM keys to JWK format.
    """
    keys_dir = os.path.dirname(os.path.realpath(__file__))
    agents = ['weather_agent', 'trip_agent', 'llm_agent']
    
    print("Converting PEM keys to JWK format...")
    print("=" * 60)
    
    for agent in agents:
        private_pem_path = os.path.join(keys_dir, f"private_ed25519_pem_{agent}")
        
        if os.path.exists(private_pem_path):
            try:
                # Convert private key
                private_jwk_path = private_pem_path  # Same filename
                key_id = convert_pem_to_jwk(private_pem_path, private_jwk_path + ".jwk", is_private=True)
                os.rename(private_jwk_path + ".jwk", private_jwk_path)
                
                # Find and convert public key
                # Look for existing public key file with old naming or key_id naming
                old_public_files = [
                    os.path.join(keys_dir, f"ed25519_pem_pub_{agent}"),
                    os.path.join(keys_dir, key_id)
                ]
                
                public_pem_found = False
                for old_public_path in old_public_files:
                    if os.path.exists(old_public_path):
                        # Check if it's PEM or already JWK
                        try:
                            with open(old_public_path, "r") as f:
                                content = f.read()
                                if content.strip().startswith("{"):
                                    # Already JWK format
                                    print(f"✅ {agent}: Public key already in JWK format")
                                    public_pem_found = True
                                    break
                        except:
                            pass
                        
                        # Convert PEM to JWK
                        try:
                            new_public_path = os.path.join(keys_dir, key_id)
                            convert_pem_to_jwk(old_public_path, new_public_path, is_private=False)
                            if old_public_path != new_public_path:
                                os.remove(old_public_path)
                            print(f"✅ {agent}: Converted public key to JWK")
                            public_pem_found = True
                            break
                        except Exception as e:
                            print(f"❌ {agent}: Failed to convert public key: {e}")
                
                if not public_pem_found:
                    print(f"⚠️ {agent}: Public key not found, generating from private key")
                    # Generate public key from private key
                    private_key = get_agent_private_key_ed25519(agent)
                    public_jwk = jwk.JWK.from_pyca(private_key.public_key())
                    public_jwk_dict = public_jwk.export_public(as_dict=True)
                    
                    public_key_path = os.path.join(keys_dir, key_id)
                    with open(public_key_path, "w") as f:
                        json.dump(public_jwk_dict, f, indent=2)
                
                print(f"✅ {agent}: Converted to JWK format (Key ID: {key_id})")
                
            except Exception as e:
                print(f"❌ {agent}: Failed to convert - {e}")
        else:
            print(f"❌ {agent}: Private key not found")
        
        print()
    
    print("=" * 60)
    print("PEM to JWK conversion completed!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "generate":
            generate_all_agent_keypairs()
        elif command == "list":
            list_agent_keys()
        elif command == "generate-agent" and len(sys.argv) > 2:
            agent_name = sys.argv[2]
            generate_agent_keypair(agent_name)
        elif command == "convert-to-jwk":
            convert_all_pem_to_jwk()
        else:
            print("Usage:")
            print("  python key_generator.py generate              # Generate all agent JWK keys")
            print("  python key_generator.py list                  # List existing agent keys")
            print("  python key_generator.py generate-agent NAME   # Generate JWK key for specific agent")
            print("  python key_generator.py convert-to-jwk        # Convert existing PEM keys to JWK")
    else:
        print("Usage:")
        print("  python key_generator.py generate              # Generate all agent JWK keys")
        print("  python key_generator.py list                  # List existing agent keys")
        print("  python key_generator.py generate-agent NAME   # Generate JWK key for specific agent")
        print("  python key_generator.py convert-to-jwk        # Convert existing PEM keys to JWK")

