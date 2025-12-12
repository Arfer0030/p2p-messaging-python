import uuid
import socket
from datetime import datetime
from crypto import CryptoManager
from network import P2PNode


class P2PChatCLI:
    # Versi CLI untuk di tes di hp (kepo aja si ini hehe)
    def __init__(self):
        self.crypto = CryptoManager()
        self.network = None
        self.running = False
        self.current_peer = None
        self.current_group = None
        self.username = ""
    
    def log(self, msg, icon="📌"):
        print(f"[{datetime.now().strftime('%H:%M')}] {icon} {msg}")
    
    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def setup_callbacks(self):
        self.network.on_peer_connected = lambda pid, user: (
            self.network.send_public_key(pid, self.crypto.get_public_key()),
            self.log(f"{user} terhubung")
        )
        self.network.on_peer_disconnected = lambda pid, user: self.log(f"{user} terputus")
        self.network.on_public_key_received = lambda pid, key: (
            self.crypto.import_peer_public_key(pid, key),
            self.log(f"Kunci dari {self.network.get_peer_username(pid)}", "🔐")
        )
        self.network.on_message_received = lambda pid, data: self.log(
            f"{self.network.get_peer_username(pid)}: {self.crypto.decrypt_message(data, pid)}", "📩"
        )
        self.network.on_group_invite_received = self.handle_group_invite
        self.network.on_group_message_received = self.handle_group_msg
    
    def handle_group_invite(self, gid, name, key, from_id):
        self.crypto.set_group_key(gid, key.encode('utf-8'))
        self.log(f"Diundang ke group '{name}'", "👥")
    
    def handle_group_msg(self, from_id, payload):
        try:
            gid = payload['group_id']
            sender = payload['sender']
            msg = self.crypto.decrypt_group_message(payload['encrypted'], gid)
            gname = self.network.groups.get(gid)
            gname = gname.name if gname else gid[:8]
            self.log(f"[{gname}] {sender}: {msg}", "👥")
        except Exception as e:
            self.log(f"Error: {e}")
    
    def send_msg(self, msg):
        if not self.current_peer:
            return self.log("Pilih peer dulu!")
        enc = self.crypto.encrypt_message(msg, self.current_peer)
        self.network.send_chat(self.current_peer, enc)
        self.log(f"You: {msg}", "📤")
    
    def send_group_msg(self, gid, msg):
        if not self.crypto.has_group_key(gid):
            return self.log("Tidak punya key group ini!")
        enc = self.crypto.encrypt_group_message(msg, gid)
        self.network.send_group_message(gid, enc, self.username)
        gname = self.network.groups.get(gid)
        gname = gname.name if gname else gid[:8]
        self.log(f"[{gname}] You: {msg}", "📤")
    
    def create_group(self):
        peers = self.network.get_connected_peers()
        if not peers:
            return self.log("Tidak ada peer!")
        
        name = input("Nama group: ").strip()
        if not name:
            return
        
        print("Pilih member (pisah koma, misal: 1,2):")
        for i, (pid, user) in enumerate(peers.items(), 1):
            print(f"  {i}. {user}")
        
        nums = input("Member: ").strip().split(",")
        pids = list(peers.keys())
        members = []
        for n in nums:
            try:
                idx = int(n.strip()) - 1
                if 0 <= idx < len(pids):
                    members.append(pids[idx])
            except:
                pass
        
        if not members:
            return self.log("Pilih minimal 1 member!")
        
        gid = f"group_{uuid.uuid4().hex[:8]}"
        key = self.crypto.create_group_key(gid)
        self.network.create_group(gid, name, members, key)
        self.log(f"Group '{name}' dibuat!")
    
    def show_menu(self):
        print("\n" + "=" * 35)
        peer_name = self.network.get_peer_username(self.current_peer) if self.current_peer else "-"
        print(f"  Chat: {peer_name}")
        print("=" * 35)
        print("  1. Connect    5. Kirim pesan")
        print("  2. Peers      6. Buat group")
        print("  3. Pilih peer 7. Groups")
        print("  4. Pilih group 8. Kirim ke group")
        print("  0. Keluar")
        print("=" * 35)
    
    def run(self):
        print("\n" + "=" * 35)
        print("  🔒 P2P CHAT CLI + GROUP")
        print("=" * 35)
        
        self.username = input("Username: ").strip() or "User"
        port = int(input("Port (5000): ").strip() or "5000")
        
        ip = self.get_ip()
        self.network = P2PNode(ip, port, self.username)
        self.network.debug = False
        self.setup_callbacks()
        
        self.network.start()
        self.log(f"Server: {ip}:{port}")
        self.running = True
        
        while self.running:
            try:
                self.show_menu()
                opsi = input("Pilih: ").strip()
                
                if opsi == "0":
                    break
                
                elif opsi == "1":
                    ip = input("IP: ").strip()
                    p = int(input("Port: ").strip())
                    self.network.connect_to_peer(ip, p)
                
                elif opsi == "2":
                    peers = self.network.get_connected_peers()
                    if not peers:
                        print("  Tidak ada peer.")
                    for i, (pid, user) in enumerate(peers.items(), 1):
                        mark = " *" if pid == self.current_peer else ""
                        print(f"  {i}. {user}{mark}")
                
                elif opsi == "3":
                    peers = list(self.network.get_connected_peers().keys())
                    if not peers:
                        self.log("Tidak ada peer!")
                    else:
                        for i, pid in enumerate(peers, 1):
                            print(f"  {i}. {self.network.get_peer_username(pid)}")
                        num = int(input("Nomor: ").strip())
                        if 0 < num <= len(peers):
                            self.current_peer = peers[num-1]
                            self.current_group = None
                            self.log(f"Chat: {self.network.get_peer_username(self.current_peer)}", "💬")
                
                elif opsi == "4":
                    groups = self.network.groups
                    if not groups:
                        self.log("Tidak ada group!")
                    else:
                        for i, (gid, g) in enumerate(groups.items(), 1):
                            print(f"  {i}. {g.name}")
                        num = int(input("Nomor: ").strip())
                        gids = list(groups.keys())
                        if 0 < num <= len(gids):
                            self.current_group = gids[num-1]
                            self.current_peer = None
                            self.log(f"Group: {groups[self.current_group].name}", "👥")
                
                elif opsi == "5":
                    if self.current_group:
                        self.log("Mode group, gunakan menu 8")
                    else:
                        msg = input("Pesan: ").strip()
                        if msg:
                            self.send_msg(msg)
                
                elif opsi == "6":
                    self.create_group()
                
                elif opsi == "7":
                    groups = self.network.groups
                    if not groups:
                        print("  Tidak ada group.")
                    for i, (gid, g) in enumerate(groups.items(), 1):
                        mark = " *" if gid == self.current_group else ""
                        print(f"  {i}. {g.name}{mark}")
                
                elif opsi == "8":
                    if not self.current_group:
                        self.log("Pilih group dulu (menu 4)!")
                    else:
                        msg = input("Pesan: ").strip()
                        if msg:
                            self.send_group_msg(self.current_group, msg)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(str(e))
        
        self.network.stop()
        print("Selesai!")


if __name__ == "__main__":
    P2PChatCLI().run()
