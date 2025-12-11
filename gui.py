"""
GUI Module untuk P2P Chat
Interface berbasis Tkinter dengan tema modern
Support untuk chat history per peer dan group chat
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import os
from datetime import datetime
from typing import Callable, Optional


class ChatGUI:
    """GUI utama untuk aplikasi P2P Chat"""
    
    # Warna tema
    COLORS = {
        'bg_dark': '#0d0221',           # Deep purple-black
        'bg_medium': '#1b0638',         # Dark galaxy purple
        'bg_light': '#3b1c5a',          # Medium purple
        'accent': '#b537f2',            # Bright purple
        'accent_hover': '#d35cff',      # Light purple glow
        'text': '#f4f0ff',              # Soft white
        'text_muted': '#a89cc8',        # Muted lavender
        'success': '#00ffcc',           # Cyan-green
        'warning': '#ff6ec7',           # Pink
        'message_sent': '#3b1c5a',      # Medium purple
        'message_received': '#1b0638',  # Dark purple
        'border': '#5e2b8f',            # Purple border
        'group': '#ff9500'              # Orange for groups
    }
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("P2P Messaging Service")
        self.root.geometry("700x750")
        self.root.minsize(600, 700)
        self.root.configure(bg=self.COLORS['bg_dark'])
        
        # Callbacks
        self.on_connect: Optional[Callable] = None
        self.on_send_message: Optional[Callable] = None
        self.on_send_file: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_download_file: Optional[Callable] = None
        self.on_create_group: Optional[Callable] = None
        self.on_send_group_message: Optional[Callable] = None
        
        # State
        self.current_peer: Optional[str] = None  # peer_id or group_id
        self.current_is_group: bool = False
        self.peers: dict = {}  # peer_id -> username
        self.groups: dict = {}  # group_id -> group_name
        self.pending_files: dict = {}
        self.my_username: str = "Me"  # Our username
        
        # Chat history storage
        self.chat_histories: dict = {}  # peer_id/group_id -> list of tuples (timestamp, sender, message, is_sent, msg_type)
        
        self._setup_styles()
        self._create_widgets()
        
    def _setup_styles(self):
        """Setup custom styles untuk ttk widgets"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure button style
        style.configure('Accent.TButton',
                       background=self.COLORS['accent'],
                       foreground='white',
                       padding=(15, 8),
                       font=('Segoe UI', 10, 'bold'))
        style.map('Accent.TButton',
                 background=[('active', self.COLORS['accent_hover'])])
        
        # Configure entry style
        style.configure('Dark.TEntry',
                       fieldbackground=self.COLORS['bg_medium'],
                       foreground=self.COLORS['text'],
                       padding=8)
        
        # Configure frame style
        style.configure('Dark.TFrame',
                       background=self.COLORS['bg_dark'])
        
        style.configure('Card.TFrame',
                       background=self.COLORS['bg_medium'])
        
        # Configure label style
        style.configure('Dark.TLabel',
                       background=self.COLORS['bg_dark'],
                       foreground=self.COLORS['text'],
                       font=('Segoe UI', 10))
        
        style.configure('Title.TLabel',
                       background=self.COLORS['bg_dark'],
                       foreground=self.COLORS['text'],
                       font=('Segoe UI', 14, 'bold'))
        
        style.configure('Muted.TLabel',
                       background=self.COLORS['bg_dark'],
                       foreground=self.COLORS['text_muted'],
                       font=('Segoe UI', 9))
    
    def _create_widgets(self):
        """Buat semua widgets"""
        # Main container
        main_container = ttk.Frame(self.root, style='Dark.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left sidebar
        self._create_sidebar(main_container)
        
        # Right chat area
        self._create_chat_area(main_container)
    
    def _create_sidebar(self, parent):
        """Buat sidebar untuk koneksi dan peers"""
        sidebar = tk.Frame(parent, bg=self.COLORS['bg_medium'], width=280)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sidebar.pack_propagate(False)
        
        # Header
        header = tk.Frame(sidebar, bg=self.COLORS['bg_medium'])
        header.pack(fill=tk.X, padx=15, pady=15)
        
        title = tk.Label(header, text="🔒 P2P Chat",
                        bg=self.COLORS['bg_medium'],
                        fg=self.COLORS['text'],
                        font=('Segoe UI', 16, 'bold'))
        title.pack(anchor='w')
        
        subtitle = tk.Label(header, text="End-to-End Encrypted",
                           bg=self.COLORS['bg_medium'],
                           fg=self.COLORS['success'],
                           font=('Segoe UI', 9))
        subtitle.pack(anchor='w')
        
        # Separator
        sep = tk.Frame(sidebar, bg=self.COLORS['border'], height=1)
        sep.pack(fill=tk.X, padx=15)
        
        # Connection section
        conn_frame = tk.Frame(sidebar, bg=self.COLORS['bg_medium'])
        conn_frame.pack(fill=tk.X, padx=15, pady=15)
        
        conn_label = tk.Label(conn_frame, text="Koneksi",
                             bg=self.COLORS['bg_medium'],
                             fg=self.COLORS['text'],
                             font=('Segoe UI', 11, 'bold'))
        conn_label.pack(anchor='w', pady=(0, 10))
        
        # IP Input
        ip_label = tk.Label(conn_frame, text="IP Address",
                           bg=self.COLORS['bg_medium'],
                           fg=self.COLORS['text_muted'],
                           font=('Segoe UI', 9))
        ip_label.pack(anchor='w')
        
        self.ip_entry = tk.Entry(conn_frame,
                                bg=self.COLORS['bg_light'],
                                fg=self.COLORS['text'],
                                insertbackground=self.COLORS['text'],
                                relief='flat',
                                font=('Segoe UI', 10))
        self.ip_entry.pack(fill=tk.X, pady=(2, 8), ipady=6)
        self.ip_entry.insert(0, "127.0.0.1")
        
        # Port Input
        port_label = tk.Label(conn_frame, text="Port",
                             bg=self.COLORS['bg_medium'],
                             fg=self.COLORS['text_muted'],
                             font=('Segoe UI', 9))
        port_label.pack(anchor='w')
        
        self.port_entry = tk.Entry(conn_frame,
                                  bg=self.COLORS['bg_light'],
                                  fg=self.COLORS['text'],
                                  insertbackground=self.COLORS['text'],
                                  relief='flat',
                                  font=('Segoe UI', 10))
        self.port_entry.pack(fill=tk.X, pady=(2, 10), ipady=6)
        self.port_entry.insert(0, "5000")
        
        # Connect button
        self.connect_btn = tk.Button(conn_frame, text="🔗 Connect",
                                    bg=self.COLORS['accent'],
                                    fg='white',
                                    activebackground=self.COLORS['accent_hover'],
                                    activeforeground='white',
                                    relief='flat',
                                    font=('Segoe UI', 10, 'bold'),
                                    cursor='hand2',
                                    command=self._on_connect_click)
        self.connect_btn.pack(fill=tk.X, ipady=8)
        
        # Separator
        sep2 = tk.Frame(sidebar, bg=self.COLORS['border'], height=1)
        sep2.pack(fill=tk.X, padx=15, pady=10)
        
        # Server info
        self.server_info = tk.Label(sidebar, text="Server: Not started",
                                   bg=self.COLORS['bg_medium'],
                                   fg=self.COLORS['text_muted'],
                                   font=('Segoe UI', 9))
        self.server_info.pack(padx=15, anchor='w')
        
        # Separator
        sep3 = tk.Frame(sidebar, bg=self.COLORS['border'], height=1)
        sep3.pack(fill=tk.X, padx=15, pady=10)
        
        # Peers section
        peers_frame = tk.Frame(sidebar, bg=self.COLORS['bg_medium'])
        peers_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        peers_label = tk.Label(peers_frame, text="Peers Connected",
                              bg=self.COLORS['bg_medium'],
                              fg=self.COLORS['text'],
                              font=('Segoe UI', 11, 'bold'))
        peers_label.pack(anchor='w', pady=(0, 5))
        
        # Peers listbox
        self.peers_listbox = tk.Listbox(peers_frame,
                                       bg=self.COLORS['bg_light'],
                                       fg=self.COLORS['text'],
                                       selectbackground=self.COLORS['accent'],
                                       selectforeground='white',
                                       relief='flat',
                                       font=('Segoe UI', 10),
                                       activestyle='none',
                                       height=6)
        self.peers_listbox.pack(fill=tk.X, pady=(0, 10))
        self.peers_listbox.bind('<<ListboxSelect>>', self._on_peer_select)
        
        # Groups section
        groups_label = tk.Label(peers_frame, text="Groups",
                               bg=self.COLORS['bg_medium'],
                               fg=self.COLORS['group'],
                               font=('Segoe UI', 11, 'bold'))
        groups_label.pack(anchor='w', pady=(5, 5))
        
        # Create group button
        self.create_group_btn = tk.Button(peers_frame, text="➕ Create Group",
                                         bg=self.COLORS['group'],
                                         fg='white',
                                         activebackground=self.COLORS['accent_hover'],
                                         activeforeground='white',
                                         relief='flat',
                                         font=('Segoe UI', 9, 'bold'),
                                         cursor='hand2',
                                         command=self._on_create_group_click)
        self.create_group_btn.pack(fill=tk.X, ipady=4, pady=(0, 5))
        
        # Groups listbox
        self.groups_listbox = tk.Listbox(peers_frame,
                                        bg=self.COLORS['bg_light'],
                                        fg=self.COLORS['group'],
                                        selectbackground=self.COLORS['group'],
                                        selectforeground='white',
                                        relief='flat',
                                        font=('Segoe UI', 10),
                                        activestyle='none',
                                        height=5)
        self.groups_listbox.pack(fill=tk.BOTH, expand=True)
        self.groups_listbox.bind('<<ListboxSelect>>', self._on_group_select)
    
    def _create_chat_area(self, parent):
        """Buat area chat utama"""
        chat_container = tk.Frame(parent, bg=self.COLORS['bg_dark'])
        chat_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Chat header
        header = tk.Frame(chat_container, bg=self.COLORS['bg_medium'], height=70)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg=self.COLORS['bg_medium'])
        header_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Left side - chat title
        left_header = tk.Frame(header_content, bg=self.COLORS['bg_medium'])
        left_header.pack(side=tk.LEFT, fill=tk.Y)
        
        self.chat_title = tk.Label(left_header, text="Pilih peer atau group untuk chat",
                                  bg=self.COLORS['bg_medium'],
                                  fg=self.COLORS['text'],
                                  font=('Segoe UI', 12, 'bold'))
        self.chat_title.pack(anchor='w')
        
        self.chat_status = tk.Label(left_header, text="",
                                   bg=self.COLORS['bg_medium'],
                                   fg=self.COLORS['success'],
                                   font=('Segoe UI', 9))
        self.chat_status.pack(anchor='w')
        
        # Right side - my username
        right_header = tk.Frame(header_content, bg=self.COLORS['bg_medium'])
        right_header.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.my_username_label = tk.Label(right_header, text="👤 Me",
                                         bg=self.COLORS['bg_medium'],
                                         fg=self.COLORS['accent'],
                                         font=('Segoe UI', 10, 'bold'))
        self.my_username_label.pack(anchor='e')
        
        # Chat messages area
        chat_frame = tk.Frame(chat_container, bg=self.COLORS['bg_dark'])
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_text = scrolledtext.ScrolledText(chat_frame,
                                                   bg=self.COLORS['bg_dark'],
                                                   fg=self.COLORS['text'],
                                                   font=('Segoe UI', 10),
                                                   relief='flat',
                                                   wrap=tk.WORD,
                                                   state='disabled',
                                                   cursor='arrow')
        self.chat_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Configure tags for messages - sent aligned right, received aligned left
        self.chat_text.tag_configure('sent', 
                                    background=self.COLORS['message_sent'],
                                    foreground=self.COLORS['text'],
                                    justify='right',
                                    lmargin1=100, lmargin2=100, rmargin=10,
                                    spacing1=5, spacing3=5)
        self.chat_text.tag_configure('sent_time', 
                                    foreground=self.COLORS['text_muted'],
                                    font=('Segoe UI', 8),
                                    justify='right')
        self.chat_text.tag_configure('received',
                                    background=self.COLORS['message_received'],
                                    foreground=self.COLORS['text'],
                                    justify='left',
                                    lmargin1=10, lmargin2=10, rmargin=100,
                                    spacing1=5, spacing3=5)
        self.chat_text.tag_configure('received_time', 
                                    foreground=self.COLORS['text_muted'],
                                    font=('Segoe UI', 8),
                                    justify='left')
        self.chat_text.tag_configure('system',
                                    foreground=self.COLORS['text_muted'],
                                    justify='center',
                                    spacing1=5, spacing3=5)
        self.chat_text.tag_configure('time',
                                    foreground=self.COLORS['text_muted'],
                                    font=('Segoe UI', 8))
        self.chat_text.tag_configure('file',
                                    foreground=self.COLORS['warning'],
                                    font=('Segoe UI', 10, 'italic'))
        self.chat_text.tag_configure('group',
                                    foreground=self.COLORS['group'],
                                    font=('Segoe UI', 10, 'italic'))
        
        # Input area
        input_frame = tk.Frame(chat_container, bg=self.COLORS['bg_medium'])
        input_frame.pack(fill=tk.X)
        
        input_inner = tk.Frame(input_frame, bg=self.COLORS['bg_medium'])
        input_inner.pack(fill=tk.X, padx=10, pady=10)
        
        # File button
        self.file_btn = tk.Button(input_inner, text="📁",
                                 bg=self.COLORS['bg_light'],
                                 fg=self.COLORS['text'],
                                 activebackground=self.COLORS['accent'],
                                 activeforeground='white',
                                 relief='flat',
                                 font=('Segoe UI', 14),
                                 cursor='hand2',
                                 command=self._on_file_click)
        self.file_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=8, ipady=4)
        
        # Message entry
        self.message_entry = tk.Entry(input_inner,
                                     bg=self.COLORS['bg_light'],
                                     fg=self.COLORS['text'],
                                     insertbackground=self.COLORS['text'],
                                     relief='flat',
                                     font=('Segoe UI', 11))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(0, 10))
        self.message_entry.bind('<Return>', self._on_send_click)
        
        # Send button
        self.send_btn = tk.Button(input_inner, text="➤ Send",
                                 bg=self.COLORS['accent'],
                                 fg='white',
                                 activebackground=self.COLORS['accent_hover'],
                                 activeforeground='white',
                                 relief='flat',
                                 font=('Segoe UI', 10, 'bold'),
                                 cursor='hand2',
                                 command=self._on_send_click)
        self.send_btn.pack(side=tk.RIGHT, ipadx=15, ipady=8)
        
        # Progress bar (hidden by default)
        self.progress_frame = tk.Frame(chat_container, bg=self.COLORS['bg_dark'])
        self.progress_label = tk.Label(self.progress_frame, text="",
                                      bg=self.COLORS['bg_dark'],
                                      fg=self.COLORS['text_muted'],
                                      font=('Segoe UI', 9))
        self.progress_label.pack(anchor='w', padx=10)
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)
    
    def _on_connect_click(self):
        """Handle klik tombol connect"""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        
        if not ip or not port:
            messagebox.showerror("Error", "Masukkan IP dan Port!")
            return
        
        try:
            port = int(port)
        except ValueError:
            messagebox.showerror("Error", "Port harus berupa angka!")
            return
        
        if self.on_connect:
            self.on_connect(ip, port)
    
    def _on_send_click(self, event=None):
        """Handle klik tombol send"""
        message = self.message_entry.get().strip()
        if not message:
            return
        
        if not self.current_peer:
            messagebox.showwarning("Warning", "Pilih peer atau group terlebih dahulu!")
            return
        
        if self.current_is_group:
            if self.on_send_group_message:
                self.on_send_group_message(self.current_peer, message)
        else:
            if self.on_send_message:
                self.on_send_message(self.current_peer, message)
        
        self.message_entry.delete(0, tk.END)
    
    def _on_file_click(self):
        """Handle klik tombol file"""
        if not self.current_peer or self.current_is_group:
            messagebox.showwarning("Warning", "Kirim file hanya bisa ke peer langsung!")
            return
        
        filepath = filedialog.askopenfilename(title="Pilih file untuk dikirim")
        if filepath and self.on_send_file:
            self.on_send_file(self.current_peer, filepath)
    
    def _on_peer_select(self, event):
        """Handle pemilihan peer dari list"""
        # Deselect groups
        self.groups_listbox.selection_clear(0, tk.END)
        
        selection = self.peers_listbox.curselection()
        if selection:
            index = selection[0]
            peer_id = list(self.peers.keys())[index]
            self._switch_chat(peer_id, is_group=False)
    
    def _on_group_select(self, event):
        """Handle pemilihan group dari list"""
        # Deselect peers
        self.peers_listbox.selection_clear(0, tk.END)
        
        selection = self.groups_listbox.curselection()
        if selection:
            index = selection[0]
            group_id = list(self.groups.keys())[index]
            self._switch_chat(group_id, is_group=True)
    
    def _on_create_group_click(self):
        """Handle create group button"""
        if not self.peers:
            messagebox.showwarning("Warning", "Tidak ada peer yang terhubung!")
            return
        
        # Ask for group name
        group_name = simpledialog.askstring("Create Group", "Masukkan nama group:",
                                           parent=self.root)
        if not group_name:
            return
        
        # Create member selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Pilih Members")
        dialog.geometry("300x400")
        dialog.configure(bg=self.COLORS['bg_dark'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Pilih peers untuk diundang:",
                bg=self.COLORS['bg_dark'], fg=self.COLORS['text'],
                font=('Segoe UI', 11)).pack(pady=10)
        
        # Checkboxes for each peer
        selected_peers = {}
        for peer_id, username in self.peers.items():
            var = tk.BooleanVar()
            cb = tk.Checkbutton(dialog, text=username,
                               variable=var,
                               bg=self.COLORS['bg_dark'],
                               fg=self.COLORS['text'],
                               selectcolor=self.COLORS['bg_medium'],
                               activebackground=self.COLORS['bg_dark'],
                               activeforeground=self.COLORS['text'],
                               font=('Segoe UI', 10))
            cb.pack(anchor='w', padx=20)
            selected_peers[peer_id] = var
        
        def on_confirm():
            members = [pid for pid, var in selected_peers.items() if var.get()]
            if not members:
                messagebox.showwarning("Warning", "Pilih minimal 1 member!")
                return
            dialog.destroy()
            if self.on_create_group:
                self.on_create_group(group_name, members)
        
        tk.Button(dialog, text="Create Group",
                 bg=self.COLORS['group'], fg='white',
                 font=('Segoe UI', 10, 'bold'),
                 command=on_confirm).pack(pady=20, ipadx=20, ipady=5)
    
    def _switch_chat(self, chat_id: str, is_group: bool = False):
        """Switch to a different chat and load history"""
        self.current_peer = chat_id
        self.current_is_group = is_group
        
        if is_group:
            name = self.groups.get(chat_id, "Unknown Group")
            self.chat_title.config(text=f"👥 {name}")
            self.chat_status.config(text="🔐 Group Encrypted", fg=self.COLORS['group'])
        else:
            name = self.peers.get(chat_id, "Unknown")
            self.chat_title.config(text=f"💬 Chat dengan {name}")
            self.chat_status.config(text="🔒 End-to-End Encrypted", fg=self.COLORS['success'])
        
        # Load chat history
        self._load_chat_history(chat_id)
    
    def _load_chat_history(self, chat_id: str):
        """Load and display chat history for a peer/group"""
        self.chat_text.config(state='normal')
        self.chat_text.delete(1.0, tk.END)
        
        if chat_id in self.chat_histories:
            for item in self.chat_histories[chat_id]:
                timestamp, sender, message, is_sent, msg_type = item
                if msg_type == 'message':
                    tag = 'sent' if is_sent else 'received'
                    prefix = "You" if is_sent else sender
                    self.chat_text.insert(tk.END, f"\n[{timestamp}] {prefix}:\n", 'time')
                    self.chat_text.insert(tk.END, f"{message}\n", tag)
                elif msg_type == 'system':
                    self.chat_text.insert(tk.END, f"\n--- {message} ---\n", 'system')
                elif msg_type == 'file':
                    self.chat_text.insert(tk.END, f"\n[{timestamp}] ", 'time')
                    self.chat_text.insert(tk.END, f"📁 {message}\n", 'file')
        
        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)
    
    def _store_message(self, chat_id: str, sender: str, message: str, is_sent: bool, msg_type: str = 'message'):
        """Store message in chat history"""
        if chat_id not in self.chat_histories:
            self.chat_histories[chat_id] = []
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_histories[chat_id].append((timestamp, sender, message, is_sent, msg_type))
    
    def set_server_info(self, ip: str, port: int):
        """Set informasi server"""
        self.server_info.config(text=f"📡 Server: {ip}:{port}")
    
    def set_username(self, username: str):
        """Set username kita yang akan ditampilkan"""
        self.my_username = username
        self.my_username_label.config(text=f"👤 {username}")
    
    def add_peer(self, peer_id: str, username: str):
        """Tambah peer ke list"""
        self.peers[peer_id] = username
        self._update_peers_list()
        self.add_system_message(f"{username} terhubung")
    
    def remove_peer(self, peer_id: str):
        """Hapus peer dari list"""
        if peer_id in self.peers:
            username = self.peers[peer_id]
            del self.peers[peer_id]
            self._update_peers_list()
            self.add_system_message(f"{username} terputus")
            
            if self.current_peer == peer_id:
                self.current_peer = None
                self.current_is_group = False
                self.chat_title.config(text="Pilih peer atau group untuk chat")
                self.chat_status.config(text="")
    
    def _update_peers_list(self):
        """Update tampilan list peers"""
        self.peers_listbox.delete(0, tk.END)
        for peer_id, username in self.peers.items():
            self.peers_listbox.insert(tk.END, f"👤 {username}")
    
    def add_group(self, group_id: str, group_name: str):
        """Add group to list"""
        self.groups[group_id] = group_name
        self._update_groups_list()
    
    def _update_groups_list(self):
        """Update tampilan list groups"""
        self.groups_listbox.delete(0, tk.END)
        for group_id, group_name in self.groups.items():
            self.groups_listbox.insert(tk.END, f"👥 {group_name}")
    
    def add_message(self, sender: str, message: str, is_sent: bool = False, peer_id: str = None):
        """Tambah pesan ke chat"""
        # Determine chat_id
        chat_id = peer_id if peer_id else self.current_peer
        if not chat_id:
            return
        
        # Store in history
        self._store_message(chat_id, sender, message, is_sent, 'message')
        
        # Only display if this is the current chat
        if chat_id == self.current_peer:
            self.chat_text.config(state='normal')
            
            timestamp = datetime.now().strftime("%H:%M")
            
            if is_sent:
                # Sent message - aligned right
                time_tag = 'sent_time'
                msg_tag = 'sent'
                prefix = "You"
            else:
                # Received message - aligned left
                time_tag = 'received_time'
                msg_tag = 'received'
                prefix = sender
            
            self.chat_text.insert(tk.END, f"\n[{timestamp}] {prefix}:\n", time_tag)
            self.chat_text.insert(tk.END, f"{message}\n", msg_tag)
            
            self.chat_text.config(state='disabled')
            self.chat_text.see(tk.END)
    
    def add_group_message(self, group_id: str, sender: str, message: str, is_sent: bool = False):
        """Tambah pesan group ke chat"""
        # Store in history
        self._store_message(group_id, sender, message, is_sent, 'message')
        
        # Only display if this is the current chat
        if group_id == self.current_peer and self.current_is_group:
            self.chat_text.config(state='normal')
            
            timestamp = datetime.now().strftime("%H:%M")
            
            if is_sent:
                time_tag = 'sent_time'
                msg_tag = 'sent'
                prefix = "You"
            else:
                time_tag = 'received_time'
                msg_tag = 'received'
                prefix = sender
            
            self.chat_text.insert(tk.END, f"\n[{timestamp}] {prefix}:\n", time_tag)
            self.chat_text.insert(tk.END, f"{message}\n", msg_tag)
            
            self.chat_text.config(state='disabled')
            self.chat_text.see(tk.END)
    
    def add_file_message(self, sender: str, filename: str, is_sent: bool = False, peer_id: str = None):
        """Tambah notifikasi file ke chat"""
        chat_id = peer_id if peer_id else self.current_peer
        if not chat_id:
            return
        
        action = "mengirim" if is_sent else "mengirim"
        prefix = "You" if is_sent else sender
        msg = f"{prefix} {action} file: {filename}"
        
        # Store in history
        self._store_message(chat_id, sender, msg, is_sent, 'file')
        
        if chat_id == self.current_peer:
            self.chat_text.config(state='normal')
            
            timestamp = datetime.now().strftime("%H:%M")
            self.chat_text.insert(tk.END, f"\n[{timestamp}] ", 'time')
            self.chat_text.insert(tk.END, f"📁 {msg}\n", 'file')
            
            self.chat_text.config(state='disabled')
            self.chat_text.see(tk.END)
    
    def add_file_message_with_download(self, sender: str, filename: str, file_id: str, filesize: int = 0, peer_id: str = None):
        """Tambah notifikasi file dengan tombol download ke chat"""
        chat_id = peer_id if peer_id else self.current_peer
        
        self.chat_text.config(state='normal')
        
        timestamp = datetime.now().strftime("%H:%M")
        
        # Format ukuran file
        if filesize > 0:
            if filesize < 1024:
                size_str = f"{filesize} B"
            elif filesize < 1024 * 1024:
                size_str = f"{filesize / 1024:.1f} KB"
            else:
                size_str = f"{filesize / (1024 * 1024):.1f} MB"
            size_info = f" ({size_str})"
        else:
            size_info = ""
        
        msg = f"{sender} mengirim file: {filename}{size_info}"
        self._store_message(chat_id, sender, msg, False, 'file')
        
        self.chat_text.insert(tk.END, f"\n[{timestamp}] ", 'time')
        self.chat_text.insert(tk.END, f"📁 {msg}\n", 'file')
        
        # Buat frame untuk tombol download
        btn_frame = tk.Frame(self.chat_text, bg=self.COLORS['bg_dark'])
        
        download_btn = tk.Button(btn_frame, text="📥 Download",
                                bg=self.COLORS['success'],
                                fg=self.COLORS['bg_dark'],
                                activebackground=self.COLORS['accent'],
                                activeforeground='white',
                                relief='flat',
                                font=('Segoe UI', 9, 'bold'),
                                cursor='hand2',
                                command=lambda fid=file_id: self._on_download_click(fid))
        download_btn.pack(side=tk.LEFT, padx=5, pady=2, ipadx=8, ipady=2)
        
        # Simpan referensi tombol
        self.pending_files[file_id] = {
            'filename': filename,
            'button': download_btn,
            'frame': btn_frame
        }
        
        self.chat_text.window_create(tk.END, window=btn_frame)
        self.chat_text.insert(tk.END, "\n")
        
        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)
    
    def _on_download_click(self, file_id: str):
        """Handle klik tombol download"""
        if file_id in self.pending_files:
            file_info = self.pending_files[file_id]
            file_info['button'].config(text="⏳ Menyimpan...", state='disabled')
            
            if self.on_download_file:
                self.on_download_file(file_id)
    
    def mark_file_downloaded(self, file_id: str, save_path: str):
        """Tandai file sudah didownload"""
        if file_id in self.pending_files:
            file_info = self.pending_files[file_id]
            
            file_info['button'].config(
                text=f"✅ Tersimpan",
                bg=self.COLORS['text_muted'],
                state='disabled'
            )
            
            self.chat_text.config(state='normal')
            self.chat_text.insert(tk.END, f"   📂 Lokasi: {save_path}\n", 'time')
            self.chat_text.config(state='disabled')
            self.chat_text.see(tk.END)
            
            del self.pending_files[file_id]
    
    def add_system_message(self, message: str, chat_id: str = None):
        """Tambah pesan sistem ke chat"""
        # Store for current chat or global
        if chat_id:
            self._store_message(chat_id, "", message, False, 'system')
        
        # Always show system messages in current view
        self.chat_text.config(state='normal')
        self.chat_text.insert(tk.END, f"\n--- {message} ---\n", 'system')
        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)
    
    def show_progress(self, filename: str, progress: float):
        """Tampilkan progress transfer file"""
        if progress <= 0:
            self.progress_frame.pack_forget()
        else:
            self.progress_frame.pack(fill=tk.X, pady=(0, 5))
            self.progress_label.config(text=f"Transferring: {os.path.basename(filename)}")
            self.progress_bar['value'] = progress
            
            if progress >= 100:
                self.root.after(1000, lambda: self.progress_frame.pack_forget())
    
    def show_error(self, message: str):
        """Tampilkan pesan error"""
        messagebox.showerror("Error", message)
    
    def show_info(self, message: str):
        """Tampilkan pesan info"""
        messagebox.showinfo("Info", message)
    
    def run(self):
        """Jalankan GUI"""
        self.root.mainloop()
    
    def close(self):
        """Tutup GUI"""
        self.root.quit()
        self.root.destroy()
