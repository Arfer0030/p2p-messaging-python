"""
P2P Secure Chat Application
Main entry point - integrasi semua module dengan group chat support
"""

import os
import threading
import uuid
import tkinter as tk
import socket
from tkinter import simpledialog, messagebox
from datetime import datetime
from crypto import CryptoManager
from network import P2PNode, get_local_ip
from gui import ChatGUI


class P2PChatApp:
    # Aplikasi utama P2P Chat dengan Group Chat support
    
    DOWNLOAD_DIR = "downloads"
    
    def __init__(self):
        # Buat folder downloads jika belum ada
        if not os.path.exists(self.DOWNLOAD_DIR):
            os.makedirs(self.DOWNLOAD_DIR)
        
        # Initialize components
        self.crypto = CryptoManager()
        self.network: P2PNode = None
        self.gui = ChatGUI()
        self.username = ""
        
        # Pending downloads
        self.pending_downloads = {}
        self.file_counter = 0
        
        # Setup callbacks
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        # Setup semua callbacks
        # GUI callbacks
        self.gui.on_connect = self._on_connect
        self.gui.on_send_message = self._on_send_message
        self.gui.on_send_file = self._on_send_file
        self.gui.on_download_file = self._on_download_file
        self.gui.on_create_group = self._on_create_group
        self.gui.on_send_group_message = self._on_send_group_message
    
    def _setup_network_callbacks(self):
        # Setup network callbacks
        self.network.on_peer_connected = self._on_peer_connected
        self.network.on_peer_disconnected = self._on_peer_disconnected
        self.network.on_public_key_received = self._on_public_key_received
        self.network.on_message_received = self._on_message_received
        self.network.on_file_received = self._on_file_received
        self.network.on_file_progress = self._on_file_progress
        self.network.on_group_invite_received = self._on_group_invite_received
        self.network.on_group_message_received = self._on_group_message_received
    
    def _on_connect(self, ip: str, port: int):
        # Handle koneksi ke peer
        if self.network:
            success = self.network.connect_to_peer(ip, port)
            if success:
                self.gui.add_system_message(f"Terhubung ke - {ip}:{port}!")
            else:
                self.gui.show_error(f"Gagal terhubung ke - {ip}:{port}. Pastikan peer sudah berjalan.")
    
    def _on_peer_connected(self, peer_id: str, username: str):
        # Handle peer baru terkoneksi
        print(f"[INFO] Peer connected: {username}")
        # Kirim public key
        self.network.send_public_key(peer_id, self.crypto.get_public_key())
        
        # Update GUI (thread-safe)
        self.gui.root.after(0, lambda: self.gui.add_peer(peer_id, username))
    
    def _on_peer_disconnected(self, peer_id: str, username: str):
        # Handle peer disconnect
        self.gui.root.after(0, lambda: self.gui.remove_peer(peer_id))
    
    def _on_public_key_received(self, peer_id: str, public_key: bytes):
        # Handle penerimaan public key dari peer
        self.crypto.import_peer_public_key(peer_id, public_key)
        self.gui.root.after(0, lambda: self.gui.add_system_message(
            f"🔐 Kunci enkripsi diterima dari {self.network.get_peer_username(peer_id)}"
        ))
    
    def _on_send_message(self, peer_id: str, message: str):
        # Handle pengiriman pesan
        try:
            # Enkripsi pesan
            encrypted = self.crypto.encrypt_message(message, peer_id)
            
            # Kirim pesan
            success = self.network.send_chat(peer_id, encrypted)
            
            if success:
                # Tampilkan di GUI
                username = self.network.get_peer_username(peer_id)
                self.gui.add_message(username, message, is_sent=True, peer_id=peer_id)
            else:
                self.gui.show_error("Gagal mengirim pesan!")
                
        except ValueError as e:
            self.gui.show_error(str(e))
        except Exception as e:
            self.gui.show_error(f"Error: {str(e)}")
    
    def _on_message_received(self, peer_id: str, encrypted_data: dict):
        # Handle penerimaan pesan
        try:
            # Dekripsi pesan
            message = self.crypto.decrypt_message(encrypted_data)
            username = self.network.get_peer_username(peer_id)
            
            # Tampilkan di GUI (thread-safe)
            self.gui.root.after(0, lambda: self.gui.add_message(
                username, message, is_sent=False, peer_id=peer_id
            ))
            
        except Exception as e:
            print(f"Error decrypting message: {e}")
    
    def _on_send_file(self, peer_id: str, filepath: str):
        # Handle pengiriman file
        def send_file_thread():
            try:
                # Baca file
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                
                filename = os.path.basename(filepath)
                
                # Enkripsi file
                encrypted = self.crypto.encrypt_file(file_data, peer_id)
                
                # Kirim file
                self.network.send_file(peer_id, filename, encrypted)
                
                # Update GUI
                self.gui.root.after(0, lambda: self.gui.add_file_message(
                    self.network.get_peer_username(peer_id),
                    filename,
                    is_sent=True,
                    peer_id=peer_id
                ))
                
            except ValueError as e:
                self.gui.root.after(0, lambda: self.gui.show_error(str(e)))
            except Exception as e:
                self.gui.root.after(0, lambda: self.gui.show_error(f"Error: {str(e)}"))
        
        # Jalankan di thread terpisah
        threading.Thread(target=send_file_thread, daemon=True).start()
    
    def _on_file_received(self, peer_id: str, filename: str, encrypted_data: dict):
        # Handle penerimaan file
        try:
            # Generate file_id unik
            self.file_counter += 1
            file_id = f"file_{self.file_counter}_{datetime.now().strftime('%H%M%S')}"
            
            # Hitung ukuran file
            encrypted_file_data = encrypted_data.get('encrypted_file', '')
            filesize = len(encrypted_file_data) if isinstance(encrypted_file_data, bytes) else len(encrypted_file_data)
            
            # Simpan data file sementara
            self.pending_downloads[file_id] = {
                'peer_id': peer_id,
                'filename': filename,
                'encrypted_data': encrypted_data,
                'filesize': filesize
            }
            
            username = self.network.get_peer_username(peer_id)
            
            # Update GUI
            self.gui.root.after(0, lambda: self.gui.add_file_message_with_download(
                username, filename, file_id, filesize, peer_id
            ))
            
        except Exception as e:
            print(f"Error receiving file: {e}")
            self.gui.root.after(0, lambda: self.gui.show_error(f"Gagal menerima file: {str(e)}"))
    
    def _on_download_file(self, file_id: str):
        # Handle download file
        if file_id not in self.pending_downloads:
            self.gui.show_error("File tidak ditemukan!")
            return
        
        file_info = self.pending_downloads[file_id]
        
        def download_thread():
            try:
                # Dekripsi file
                file_data = self.crypto.decrypt_file(
                    file_info['encrypted_data'],
                    file_info['peer_id']
                )
                
                filename = file_info['filename']
                
                # Simpan file
                save_path = os.path.join(self.DOWNLOAD_DIR, filename)
                
                # Jika file sudah ada
                if os.path.exists(save_path):
                    name, ext = os.path.splitext(filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = os.path.join(self.DOWNLOAD_DIR, f"{name}_{timestamp}{ext}")
                
                with open(save_path, 'wb') as f:
                    f.write(file_data)
                
                # Hapus dari pending
                del self.pending_downloads[file_id]
                
                # Update GUI
                self.gui.root.after(0, lambda: self.gui.mark_file_downloaded(file_id, save_path))
                
            except Exception as e:
                print(f"Error downloading file: {e}")
                self.gui.root.after(0, lambda: self.gui.show_error(f"Gagal menyimpan: {str(e)}"))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def _on_file_progress(self, peer_id: str, filename: str, progress: float):
        # Handle progress transfer file
        self.gui.root.after(0, lambda: self.gui.show_progress(filename, progress))
    
    # ==================== GROUP CHAT METHODS ====================
    
    def _on_create_group(self, group_name: str, member_ids: list):
        # Handle create group
        try:
            # Generate unique group id
            group_id = f"group_{uuid.uuid4().hex[:8]}"
            
            # Create group key
            group_key = self.crypto.create_group_key(group_id)
            
            # Create group in network and send invites
            self.network.create_group(group_id, group_name, member_ids, group_key)
            
            # Add group to GUI
            self.gui.root.after(0, lambda: self.gui.add_group(group_id, group_name))
            self.gui.root.after(0, lambda: self.gui.add_system_message(
                f"Group '{group_name}' berhasil dibuat!"
            ))
            
        except Exception as e:
            self.gui.root.after(0, lambda: self.gui.show_error(f"Gagal membuat group: {str(e)}"))
    
    def _on_group_invite_received(self, group_id: str, group_name: str, group_key: str, from_id: str):
        # Handle group invite received
        try:
            # Import group key
            self.crypto.set_group_key(group_id, group_key.encode('utf-8'))
            
            # Add group to GUI
            self.gui.root.after(0, lambda: self.gui.add_group(group_id, group_name))
            self.gui.root.after(0, lambda: self.gui.add_system_message(
                f"Diundang ke group '{group_name}'!"
            ))
            
        except Exception as e:
            print(f"Error handling group invite: {e}")
    
    def _on_send_group_message(self, group_id: str, message: str):
        # Handle send group message
        try:
            # Encrypt with group key
            encrypted = self.crypto.encrypt_group_message(message, group_id)
            
            # Send to all group members
            success = self.network.send_group_message(group_id, encrypted, self.username)
            
            if success:
                # Show in GUI
                self.gui.add_group_message(group_id, self.username, message, is_sent=True)
            else:
                self.gui.show_error("Gagal mengirim pesan ke group!")
                
        except ValueError as e:
            self.gui.show_error(str(e))
        except Exception as e:
            self.gui.show_error(f"Error: {str(e)}")
    
    def _on_group_message_received(self, from_id: str, payload: dict):
        # Handle group message received
        try:
            group_id = payload['group_id']
            sender = payload['sender']
            encrypted_data = payload['encrypted']
            
            # Decrypt message
            message = self.crypto.decrypt_group_message(encrypted_data, group_id)
            
            # Show in GUI
            self.gui.root.after(0, lambda: self.gui.add_group_message(
                group_id, sender, message, is_sent=False
            ))
            
        except Exception as e:
            print(f"Error decrypting group message: {e}")
    
    # ==================== START/STOP ====================
    
    def start(self):
        # Mulai aplikasi
        # Minta username
        root = tk.Tk()
        root.withdraw()
        
        username = simpledialog.askstring(
            "P2P Chat App",
            "Masukkan username anda:",
            parent=root,
            initialvalue="user"
        )
        root.destroy()
        
        if not username:
            username = "User"
        self.username = username
        
        # Minta port
        root = tk.Tk()
        root.withdraw()
        
        port_str = simpledialog.askstring(
            "P2P Chat App",
            "Masukkan port untuk server peer anda:",
            parent=root,
            initialvalue="5000"
        )
        root.destroy()
        
        try:
            port = int(port_str) if port_str else 5050
        except ValueError:
            port = 5050
        
        # Initialize network
        ip = get_local_ip()
        self.network = P2PNode(ip, port, username)
        self._setup_network_callbacks()
        
        # Start node
        try:
            self.network.start()
            self.gui.set_server_info(ip, port)
            self.gui.set_username(username)  # Display username in header
            self.gui.add_system_message(f"Server dimulai di {ip}:{port}")
            self.gui.add_system_message(f"Username: {username}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memulai server: {str(e)}")
            return
        
        # Handle window close
        def on_closing():
            if self.network:
                self.network.stop()
            self.gui.close()
        
        self.gui.root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Run GUI
        self.gui.run()


def main():
    # Entry point
    app = P2PChatApp()
    app.start()


if __name__ == "__main__":
    main()
