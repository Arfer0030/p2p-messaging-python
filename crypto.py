import os
import base64
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305


class CryptoManager:
    # Mengelola enkripsi dan dekripsi dengan X25519 + ChaCha20-Poly1305
    def __init__(self):
        # Generate X25519 key pair
        self.private_key = X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.peer_public_keys = {}  # peer_id -> X25519PublicKey
        self.shared_keys = {}  # peer_id -> shared key (ChaCha20 key)
        self.group_keys = {}  # group_id -> shared key (32 bytes for ChaCha20)
        
    def get_public_key_bytes(self) -> bytes:
        # Mendapatkan public key dalam format raw bytes untuk dikirim ke peer
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
    def get_public_key(self) -> bytes:
        # Mengubah bentuk bytes ke base64
        return base64.b64encode(self.get_public_key_bytes())
        
    def import_peer_public_key(self, peer_id: str, key_bytes: bytes):
        # Import public key dari peer dan buat shared key
        try:
            if len(key_bytes) != 32:
                key_bytes = base64.b64decode(key_bytes)
        except:
            pass
            
        peer_public = X25519PublicKey.from_public_bytes(key_bytes)
        self.peer_public_keys[peer_id] = peer_public

        shared_key = self.private_key.exchange(peer_public)
        self.shared_keys[peer_id] = shared_key  
        
    def encrypt_message(self, message: str, peer_id: str) -> dict:
        # Enkripsi pesan menggunakan ChaCha20-Poly1305 dengan shared key dari X25519 key exchange
        if peer_id not in self.shared_keys:
            raise ValueError(f"Shared key untuk peer {peer_id} tidak ditemukan")

        nonce = os.urandom(12)
        chacha = ChaCha20Poly1305(self.shared_keys[peer_id])
        ciphertext = chacha.encrypt(nonce, message.encode('utf-8'), None)
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'nonce': base64.b64encode(nonce).decode('utf-8')
        }
    
    def decrypt_message(self, encrypted_data: dict, peer_id: str) -> str:
        # Dekripsi pesan dari peer tertentu menggunakan ChaCha20-Poly1305
        if peer_id not in self.shared_keys:
            raise ValueError(f"Shared key untuk peer {peer_id} tidak ditemukan")
        
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        nonce = base64.b64decode(encrypted_data['nonce'])
        chacha = ChaCha20Poly1305(self.shared_keys[peer_id])
        plaintext = chacha.decrypt(nonce, ciphertext, None)
        
        return plaintext.decode('utf-8')
    
    def encrypt_file(self, file_data: bytes, peer_id: str) -> dict:
        # Enkripsi file menggunakan ChaCha20-Poly1305
        if peer_id not in self.shared_keys:
            raise ValueError(f"Shared key untuk peer {peer_id} tidak ditemukan")

        nonce = os.urandom(12)
        chacha = ChaCha20Poly1305(self.shared_keys[peer_id])
        ciphertext = chacha.encrypt(nonce, file_data, None)
        
        return {
            'encrypted_file': base64.b64encode(ciphertext).decode('utf-8'),
            'nonce': base64.b64encode(nonce).decode('utf-8')
        }
    
    def decrypt_file(self, encrypted_data: dict, peer_id: str = None) -> bytes:
        # Dekripsi file
        ciphertext = base64.b64decode(encrypted_data['encrypted_file'])
        nonce = base64.b64decode(encrypted_data['nonce'])

        if peer_id and peer_id in self.shared_keys:
            chacha = ChaCha20Poly1305(self.shared_keys[peer_id])
            return chacha.decrypt(nonce, ciphertext, None)
        
        for shared_key in self.shared_keys.values():
            try:
                chacha = ChaCha20Poly1305(shared_key)
                return chacha.decrypt(nonce, ciphertext, None)
            except:
                continue
        
        raise ValueError("Gagal mendekripsi file")
    
    def create_group_key(self, group_id: str) -> bytes:
        # Generate random 32-byte key untuk group chat dan diubah ke base64
        key = os.urandom(32) 
        self.group_keys[group_id] = key
        return base64.b64encode(key)
    
    def set_group_key(self, group_id: str, key_bytes: bytes):
        # Import group key dari creator grup
        try:
            if len(key_bytes) != 32:
                key_bytes = base64.b64decode(key_bytes)
        except:
            pass
        self.group_keys[group_id] = key_bytes
    
    def get_group_key(self, group_id: str) -> bytes:
        # Get group key 
        if group_id not in self.group_keys:
            raise ValueError(f"Group key untuk {group_id} tidak ditemukan")
        return base64.b64encode(self.group_keys[group_id])
    
    def has_group_key(self, group_id: str) -> bool:
        # Check apakah group key ada
        return group_id in self.group_keys
    
    def encrypt_group_message(self, message: str, group_id: str) -> dict:
        # Enkripsi pesan group menggunakan ChaCha20-Poly1305 dengan shared group key
        if group_id not in self.group_keys:
            raise ValueError(f"Group key untuk {group_id} tidak ditemukan")
        
        nonce = os.urandom(12)
        chacha = ChaCha20Poly1305(self.group_keys[group_id])
        ciphertext = chacha.encrypt(nonce, message.encode('utf-8'), None)
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'nonce': base64.b64encode(nonce).decode('utf-8'),
            'group_id': group_id
        }
    
    def decrypt_group_message(self, encrypted_data: dict, group_id: str) -> str:
        # Dekripsi pesan group menggunakan ChaCha20-Poly1305
        if group_id not in self.group_keys:
            raise ValueError(f"Group key untuk {group_id} tidak ditemukan")
        
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        nonce = base64.b64decode(encrypted_data['nonce'])
        chacha = ChaCha20Poly1305(self.group_keys[group_id])
        plaintext = chacha.decrypt(nonce, ciphertext, None)
        
        return plaintext.decode('utf-8')

