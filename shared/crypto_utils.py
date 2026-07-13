import os
import hashlib
import cryptography.exceptions
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

def compute_fingerprint(public_key_pem: bytes) -> str:
    """
    Calcule l'empreinte SHA-256 de la clé publique selon le format du contrat.
    Retourne les 16 premiers caractères hex, groupés par 4.
    Exemple : "A1B2-C3D4-E5F6-A7B8"
    """
    # 1. Hasher la clé publique (PEM bytes) en SHA-256
    sha256_hex = hashlib.sha256(public_key_pem).hexdigest().upper()
    
    # 2. Prendre les 16 premiers caractères
    hex_16 = sha256_hex[:16]
    
    # 3. Grouper par 4
    formatted = "-".join([hex_16[i:i+4] for i in range(0, 16, 4)])
    
    return formatted

def encrypt_file(file_bytes: bytes):
    """
    Chiffre des données avec AES-256-CBC et padding PKCS7.
    Génère une nouvelle clé AES et un nouveau vecteur d'initialisation (IV) aléatoirement.
    Retourne (aes_key, iv, ciphertext).
    """
    aes_key = os.urandom(32) # Clé AES-256 = 32 octets
    iv = os.urandom(16)      # Bloc AES = 16 octets
    
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(file_bytes) + padder.finalize()
    
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    return aes_key, iv, ciphertext

def decrypt_file(aes_key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    """
    Déchiffre un ciphertext avec AES-256-CBC en supprimant le padding PKCS7.
    Retourne les données en clair (bytes).
    """
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    file_bytes = unpadder.update(padded_data) + unpadder.finalize()
    
    return file_bytes

# ================================
# Etape 3 : Intégrité (Hachage et Signature)
# ================================

def hash_file(file_bytes: bytes) -> str:
    """Retourne le hash SHA-256 du fichier en hexadécimal."""
    return hashlib.sha256(file_bytes).hexdigest()

def sign_hash(sha256_hex: str, private_key) -> bytes:
    """Signe le hash du fichier avec RSA-PSS."""
    signature = private_key.sign(
        sha256_hex.encode('utf-8'),
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

def verify_signature(sha256_hex: str, signature: bytes, public_key) -> bool:
    """Vérifie la signature RSA-PSS du hash."""
    try:
        public_key.verify(
            signature,
            sha256_hex.encode('utf-8'),
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except cryptography.exceptions.InvalidSignature:
        return False

# ================================
# Etape 4 : Échange de Clé AES (Chiffrement Asymétrique)
# ================================

def encrypt_aes_key(aes_key: bytes, recipient_public_key) -> bytes:
    """Chiffre la clé AES avec la clé publique du destinataire (RSA-OAEP)."""
    encrypted_key = recipient_public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_key

def decrypt_aes_key(encrypted_aes_key: bytes, private_key) -> bytes:
    """Déchiffre la clé AES avec la clé privée (RSA-OAEP)."""
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return aes_key

# Petit test pour J2
if __name__ == "__main__":
    dummy_pem = b"-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhki...\n-----END PUBLIC KEY-----"
    print(f"Test empreinte: {compute_fingerprint(dummy_pem)}")
    
    # Test chiffr/dechiffr
    msg = b"Fichier ultra secret"
    k, i, c = encrypt_file(msg)
    print(f"Chiffre: {c}")
    print(f"Dechiffre: {decrypt_file(k, i, c).decode()}")
