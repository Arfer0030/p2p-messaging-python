"""
Modul Network untuk P2P Chat
Menggunakan python-p2p-network library untuk koneksi P2P
"""

import json
import os
from typing import Callable, Optional
from dataclasses import dataclass, field
from enum import Enum

from p2pnetwork.node import Node


class MessageType(Enum):
    """Jenis pesan dalam protokol P2P"""
    HANDSHAKE = "handshake"
    PUBLIC_KEY = "public_key"
    CHAT = "chat"
    FILE_START = "file_start"
    FILE_CHUNK = "file_chunk"
    FILE_END = "file_end"
    DISCONNECT = "disconnect"
    # Group chat
    GROUP_INVITE = "group_invite"
    GROUP_MESSAGE = "group_message"
    GROUP_JOIN = "group_join"


@dataclass
class Group:
    """Representasi group chat"""
    group_id: str
    name: str
    creator_id: str
    members: list = field(default_factory=list)  # list of node ids


class P2PNode(Node):
    """P2P Node menggunakan python-p2p-network library"""
    
    CHUNK_SIZE = 32768  # 32KB chunk untuk file
    
    def __init__(self, host: str, port: int, username: str, id=None, max_connections=0):
        super(P2PNode, self).__init__(host, port, id, None, max_connections)
        self.debug = False  # Set True untuk troubleshooting
        self.username = username
        self.peer_usernames = {}  # node_id -> username
        self.groups = {}  # group_id -> Group
        
        # Callbacks
        self.on_message_received: Optional[Callable] = None
        self.on_file_received: Optional[Callable] = None
        self.on_peer_connected: Optional[Callable] = None
        self.on_peer_disconnected: Optional[Callable] = None
        self.on_public_key_received: Optional[Callable] = None
        self.on_file_progress: Optional[Callable] = None
        self.on_group_invite_received: Optional[Callable] = None
        self.on_group_message_received: Optional[Callable] = None
        
        # File transfer state
        self.receiving_files = {}
        
    def outbound_node_connected(self, node):
        """Called when connected to another node"""
        # Send handshake
        self.send_to_node(node, {
            'type': MessageType.HANDSHAKE.value,
            'payload': {'username': self.username}
        })
    
    def inbound_node_connected(self, node):
        """Called when another node connects to us"""
        # Send handshake
        self.send_to_node(node, {
            'type': MessageType.HANDSHAKE.value,
            'payload': {'username': self.username}
        })
    
    def inbound_node_disconnected(self, node):
        """Called when an inbound node disconnects"""
        self._handle_disconnect(node)
    
    def outbound_node_disconnected(self, node):
        """Called when an outbound node disconnects"""
        self._handle_disconnect(node)
    
    def _handle_disconnect(self, node):
        """Handle peer disconnect"""
        username = self.peer_usernames.get(node.id, "Unknown")
        if node.id in self.peer_usernames:
            del self.peer_usernames[node.id]
        if self.on_peer_disconnected:
            self.on_peer_disconnected(node.id, username)
    
    def node_message(self, node, data):
        """Called when a message is received from a node"""
        try:
            if isinstance(data, str):
                data = json.loads(data)
            
            msg_type = MessageType(data.get('type'))
            payload = data.get('payload', {})
            
            if msg_type == MessageType.HANDSHAKE:
                self._handle_handshake(node, payload)
            elif msg_type == MessageType.PUBLIC_KEY:
                if self.on_public_key_received:
                    self.on_public_key_received(node.id, payload['public_key'].encode('utf-8'))
            elif msg_type == MessageType.CHAT:
                if self.on_message_received:
                    self.on_message_received(node.id, payload)
            elif msg_type == MessageType.FILE_START:
                self._handle_file_start(node.id, payload)
            elif msg_type == MessageType.FILE_CHUNK:
                self._handle_file_chunk(node.id, payload)
            elif msg_type == MessageType.FILE_END:
                self._handle_file_end(node.id, payload)
            elif msg_type == MessageType.GROUP_INVITE:
                self._handle_group_invite(node.id, payload)
            elif msg_type == MessageType.GROUP_MESSAGE:
                self._handle_group_message(node.id, payload)
            elif msg_type == MessageType.GROUP_JOIN:
                self._handle_group_join(node.id, payload)
                
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def _handle_handshake(self, node, payload):
        """Handle handshake message"""
        username = payload.get('username', 'Unknown')
        self.peer_usernames[node.id] = username
        if self.on_peer_connected:
            self.on_peer_connected(node.id, username)
    
    def _handle_file_start(self, peer_id, payload):
        """Handle awal transfer file"""
        self.receiving_files[peer_id] = {
            'filename': payload['filename'],
            'filesize': payload['filesize'],
            'chunks': [],
            'received': 0,
            'nonce': payload['nonce']
        }
    
    def _handle_file_chunk(self, peer_id, payload):
        """Handle chunk file"""
        if peer_id in self.receiving_files:
            file_info = self.receiving_files[peer_id]
            file_info['chunks'].append(payload['data'])
            file_info['received'] += len(payload['data'])
            
            if self.on_file_progress:
                progress = (file_info['received'] / file_info['filesize']) * 100
                self.on_file_progress(peer_id, file_info['filename'], progress)
    
    def _handle_file_end(self, peer_id, payload):
        """Handle akhir transfer file"""
        if peer_id in self.receiving_files:
            file_info = self.receiving_files[peer_id]
            encrypted_data = {
                'encrypted_file': ''.join(file_info['chunks']),
                'nonce': file_info['nonce']
            }
            
            if self.on_file_received:
                self.on_file_received(peer_id, file_info['filename'], encrypted_data)
            
            del self.receiving_files[peer_id]
    
    def _handle_group_invite(self, from_id, payload):
        """Handle group invitation"""
        group_id = payload['group_id']
        group_name = payload['group_name']
        creator_id = payload['creator_id']
        group_key = payload['group_key']
        members = payload.get('members', [])
        
        # Create group locally
        self.groups[group_id] = Group(
            group_id=group_id,
            name=group_name,
            creator_id=creator_id,
            members=members
        )
        
        if self.on_group_invite_received:
            self.on_group_invite_received(group_id, group_name, group_key, from_id)
    
    def _handle_group_message(self, from_id, payload):
        """Handle group message"""
        if self.on_group_message_received:
            self.on_group_message_received(from_id, payload)
    
    def _handle_group_join(self, from_id, payload):
        """Handle group join notification"""
        group_id = payload['group_id']
        if group_id in self.groups:
            if from_id not in self.groups[group_id].members:
                self.groups[group_id].members.append(from_id)
    
    # ==================== SEND METHODS ====================
    
    def send_public_key(self, node_id: str, public_key: bytes):
        """Kirim public key ke peer"""
        node = self._get_node_by_id(node_id)
        if node:
            self.send_to_node(node, {
                'type': MessageType.PUBLIC_KEY.value,
                'payload': {'public_key': public_key.decode('utf-8')}
            })
    
    def send_chat(self, node_id: str, encrypted_data: dict) -> bool:
        """Kirim pesan chat terenkripsi"""
        node = self._get_node_by_id(node_id)
        if node:
            self.send_to_node(node, {
                'type': MessageType.CHAT.value,
                'payload': encrypted_data
            })
            return True
        return False
    
    def send_file(self, node_id: str, filename: str, encrypted_data: dict):
        """Kirim file terenkripsi dalam chunks"""
        node = self._get_node_by_id(node_id)
        if not node:
            return
        
        file_data = encrypted_data['encrypted_file']
        filesize = len(file_data)
        
        # Send file start
        self.send_to_node(node, {
            'type': MessageType.FILE_START.value,
            'payload': {
                'filename': os.path.basename(filename),
                'filesize': filesize,
                'nonce': encrypted_data['nonce']
            }
        })
        
        # Send chunks
        for i in range(0, filesize, self.CHUNK_SIZE):
            chunk = file_data[i:i + self.CHUNK_SIZE]
            self.send_to_node(node, {
                'type': MessageType.FILE_CHUNK.value,
                'payload': {'data': chunk}
            })
            
            if self.on_file_progress:
                progress = min(100, ((i + len(chunk)) / filesize) * 100)
                self.on_file_progress(node_id, filename, progress)
        
        # Send file end
        self.send_to_node(node, {
            'type': MessageType.FILE_END.value,
            'payload': {}
        })
    
    # ==================== GROUP METHODS ====================
    
    def create_group(self, group_id: str, group_name: str, member_ids: list, group_key: bytes):
        """Create a new group and invite members"""
        # Create group locally
        self.groups[group_id] = Group(
            group_id=group_id,
            name=group_name,
            creator_id=self.id,
            members=[self.id] + member_ids
        )
        
        # Send invite to all members
        for member_id in member_ids:
            node = self._get_node_by_id(member_id)
            if node:
                self.send_to_node(node, {
                    'type': MessageType.GROUP_INVITE.value,
                    'payload': {
                        'group_id': group_id,
                        'group_name': group_name,
                        'creator_id': self.id,
                        'group_key': group_key.decode('utf-8'),
                        'members': [self.id] + member_ids
                    }
                })
    
    def send_group_message(self, group_id: str, encrypted_data: dict, sender_username: str):
        """Send message to all group members"""
        if group_id not in self.groups:
            return False
        
        group = self.groups[group_id]
        payload = {
            'group_id': group_id,
            'sender': sender_username,
            'encrypted': encrypted_data
        }
        
        # Send to all members except self
        for member_id in group.members:
            if member_id != self.id:
                node = self._get_node_by_id(member_id)
                if node:
                    self.send_to_node(node, {
                        'type': MessageType.GROUP_MESSAGE.value,
                        'payload': payload
                    })
        
        return True
    
    # ==================== UTILITY METHODS ====================
    
    def _get_node_by_id(self, node_id: str):
        """Get node object by id"""
        for node in self.all_nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_peer_username(self, node_id: str) -> str:
        """Get username of a peer"""
        return self.peer_usernames.get(node_id, "Unknown")
    
    def get_connected_peers(self) -> dict:
        """Get all connected peers as {node_id: username}"""
        return self.peer_usernames.copy()
    
    def connect_to_peer(self, host: str, port: int) -> bool:
        """Connect to another peer"""
        try:
            print(f"[INFO] Menghubungi {host}:{port}...")
            result = self.connect_with_node(host, port)
            if result:
                print(f"[INFO] Berhasil terhubung ke {host}:{port}")
                return True
            else:
                print(f"[ERROR] Gagal terhubung ke {host}:{port}")
                return False
        except Exception as e:
            print(f"[ERROR] Error connecting to peer: {e}")
            return False
