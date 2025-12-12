import os
import base64
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import serialization

class KriptoManager:
    # Mengelola enkripsi dan dekripsi dengan X25519 + ChaCha20-Poly1305
    
    def __init__(self):
        # Generate X25519 key pair
        self.private_key = X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.peer_public_key = {}
        self.shared_key = {}
        self.group_key = {} 

    def get_public_key_raw(self) -> bytes:
        # Mendapatkan public key dalam format raw bytes untuk dikirim ke peer
        return self.public_key.public_bytes(
            encoding = serialization.Encoding.Raw,
            format = serialization.PublicFormat.Raw
        )
    
    def get_public_key(self) -> bytes:
        # ubah ke base64 encoded public key
        return base64.b64encode(self.get_public_key_raw())
    
    def get_shared_key(self, peer_id: str, key_bytes: bytes):
        # Import public key dari peer dan buat shared key
        try:
            if len(key_bytes) != 32:
                key_bytes = base64.b64decode(key_bytes)
        except:
            pass

        peer_public = X25519PublicKey.from_public_bytes(key_bytes)
        self.peer_public_key[peer_id] = peer_public

        shared_key = self.private_key.exchange(peer_public)
        self.shared_key[peer_id] = shared_key

    def encrypt_message(self, message: str, peer_id: str) -> dict:
        # Enkripsi pesan dari peer dengan ChaCha20-Poly1305 dan shared key
        if peer_id not in self.shared_key:
            raise ValueError(f"Shared key untuk peer {peer_id} tidak ditemukan")
        
        nonce = os.urandom(12)
        chacha = ChaCha20Poly1305(self.shared_key[peer_id])
        cipher = chacha.encrypt(nonce, message.encode('utf-8'), None)

        return {
            'encrypted_message' : base64.b64encode(cipher).decode('utf-8'),
            'nonce' : base64.b64encode(nonce).decode('utf-8')
        }
    
    def decrypt_message(self, encrypted_data: dict, peer_id: str) -> str:
        # Dekripsi pesan dari peer
        if peer_id not in self.shared_key:
            raise ValueError(f"Shared key untuk peer {peer_id} tidak ditemukan")

        cipher = base64.b64decode(encrypted_data['encrypted_message'])
        nonce = base64.b64decode(encrypted_data['nonce'])
        chacha = ChaCha20Poly1305(self.shared_key[peer_id])
        plaintext = chacha.decrypt(nonce, cipher, None)

        return plaintext.decode('utf-8')
    
    def encrypt_file(self, file_data: bytes, peer_id: str) -> dict:
        # Enkripsi file yang dikirim dengan ChaCha20-Poly1305 dan shared key
        if peer_id not in self.shared_key:
            raise ValueError(f"Shared key untuk peer {peer_id} tidak ditemukan")
        
        nonce = os.urandom(12)
        chacha = ChaCha20Poly1305(self.shared_key[peer_id])
        cipher = chacha.encrypt(nonce, file_data, None)

        return {
            'encrypted_file' : base64.b64encode(cipher).decode('utf-8'),
            'nonce' : base64.b64encode(nonce).decode('utf-8')
        }
    
    def decrypt_file(self, encrypted_data: dict, peer_id: str) -> bytes:
        # dekripsi file yang diterima
        cipher = base64.b64decode(encrypted_data["encrypted_file"])
        nonce = base64.b64decode(encrypted_data['nonce'])

        if peer_id and peer_id in self.shared_key:
            chacha = ChaCha20Poly1305(self.shared_key[peer_id])
            return chacha.decrypt(nonce, cipher, None)
        
        for shared_key in self.shared_key.values():
            try:
                chacha = ChaCha20Poly1305(shared_key)
                return chacha.decrypt(nonce, cipher, None)
            except:
                continue
            
        raise ValueError("Gagal mendekripsi file!")
    
    def get_group_key(self, group_id: str) -> bytes:
        # Mendapatkan group key, jika tidak ada buat baru
        key = os.urandom(32)
        self.group_key[group_id] = key
        return key
    
    def set_group_key(self, group_id: str, key_bytes: bytes):
        # Set group key dari bytes
        try:
            if len(key_bytes) != 32:
                key_bytes = base64.b64decode(key_bytes)
        except:
            pass

        self.group_key[group_id] = key_bytes

    def has_group_key(self, group_id: str) -> bool:
        # Cek apakah group key ada
        return group_id in self.group_key
    
    def encrypt_message_group(self, message: str, group_id: str) -> dict:
        # Enkripsi pesan group menggunakan ChaCha20-Poly1305 dengan shared group key
        if group_id not in self.group_key:
            raise ValueError(f"Group key untuk group {group_id} tidak ditemukan")
        
        nonce = os.urandom(12)
        chacha = ChaCha20Poly1305(self.group_key[group_id])
        cipher = chacha.encrypt(nonce, message.encode('utf-8'), None)

        return{
            'encrypted_message_group' : base64.b64encode(cipher).decode('utf-8'),
            "nonce" : base64.b64encode(nonce).decode('utf-8'),
            "group_id" : group_id
        }
    
    def decrypt_message_group(self, encypted_data: dict, group_id: str) -> str:
        # Dekripsi pesan group 
        if group_id  not in self.group_key:
            raise ValueError(f"Group key untuk group {group_id} tidak ditemukan")
        
        cipher = base64.b64decode(encypted_data['encrypted_message_group'])
        nonce = base64.b64decode(encypted_data['nonce'])
        chacha = ChaCha20Poly1305(self.group_key[group_id])
        plaintext = chacha.decrypt(nonce, cipher, None)

        return plaintext.decode('utf-8')