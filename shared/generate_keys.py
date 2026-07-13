import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

KEYS_DIR = os.path.join(os.path.dirname(__file__), 'keys')
os.makedirs(KEYS_DIR, exist_ok=True)

def generate_key_pair(username):
    """Génère une paire de clés RSA 2048 pour l'utilisateur et l'enregistre en PEM."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    with open(os.path.join(KEYS_DIR, f'{username}_private.pem'), 'wb') as f:
        f.write(priv_pem)
        
    with open(os.path.join(KEYS_DIR, f'{username}_public.pem'), 'wb') as f:
        f.write(pub_pem)
        
    print(f"Clés générées pour {username} dans {KEYS_DIR}")

if __name__ == '__main__':
    print("Génération des clés RSA...")
    generate_key_pair('alice')
    generate_key_pair('bob')
    generate_key_pair('eve')
