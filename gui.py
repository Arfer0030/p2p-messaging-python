import customtkinter as ctr
from tkinter import filedialog, messagebox, simpledialog
import os
from datetime import datetime
from typing import Callable, Optional
from network import get_local_ip


# Set appearance mode and default color theme
ctr.set_appearance_mode("dark")
ctr.set_default_color_theme("dark-blue")


class ChatGUI:
    # GUI dengan customTKinter
    COLORS = {
        'bg_dark': '#0b141a',           # Bg utama
        'bg_medium': '#111b21',         # Sidebar
        'bg_light': '#202c33',          # Input field
        'accent': '#00a884',            # Primary action 
        'accent_hover': '#06cf9c',      # Hover 
        'text': '#e9edef',              # Text utama
        'text_muted': '#8696a0',        # Text secondary
        'success': '#25d366',           # Success 
        'warning': '#ea4335',           # Error
        'border': '#2a3942',            # Border
        'group': '#334155',             # Group chat 
        'message_sent': '#005c4b',      # Bubble sent 
        'message_received': '#202c33',  # Bubble received 
    }
    
    def __init__(self):
        self.root = ctr.CTk()
        self.root.title("P2P Messaging Service")
        self.root.geometry("700x700")
        self.root.minsize(600, 600)
        
        # Callbacks
        self.on_connect: Optional[Callable] = None
        self.on_send_message: Optional[Callable] = None
        self.on_send_file: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_download_file: Optional[Callable] = None
        self.on_create_group: Optional[Callable] = None
        self.on_send_group_message: Optional[Callable] = None
        
        # State
        self.current_peer: Optional[str] = None
        self.current_is_group: bool = False
        self.peers: dict = {}
        self.groups: dict = {}
        self.pending_files: dict = {}
        self.my_username: str = "Me"
        
        # Chat history storage
        self.chat_histories: dict = {}
        
        # Peer/Group button references
        self.peer_buttons: dict = {}
        self.group_buttons: dict = {}
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Buat semua widgets
        # Main container, sidebar kiri, dan chat area kanan
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self._create_sidebar()
        self._create_chat_area()
    
    def _create_sidebar(self):
        # Buat sidebar untuk koneksi dan peers
        sidebar = ctr.CTkFrame(self.root, width=260, corner_radius=0,
                              fg_color=self.COLORS['bg_medium'])
        sidebar.grid(row=0, column=0, sticky="nswe")
        sidebar.grid_propagate(False)
        
        # Header
        header_frame = ctr.CTkFrame(sidebar, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(12, 6))
        
        title = ctr.CTkLabel(header_frame, text="🔒 P2P Chat",
                            font=ctr.CTkFont(size=18, weight="bold"),
                            text_color=self.COLORS['text'])
        title.pack(anchor="w")
        
        subtitle = ctr.CTkLabel(header_frame, text="End-to-End Encrypted",
                               font=ctr.CTkFont(size=10),
                               text_color=self.COLORS['success'])
        subtitle.pack(anchor="w")
        
        # Separator
        sep = ctr.CTkFrame(sidebar, height=1, fg_color=self.COLORS['border'])
        sep.pack(fill="x", padx=15, pady=6)
        
        # Scrollable konten area
        scroll_content = ctr.CTkScrollableFrame(sidebar, fg_color="transparent",
                                                corner_radius=0)
        scroll_content.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Connection section
        conn_frame = ctr.CTkFrame(scroll_content, fg_color="transparent")
        conn_frame.pack(fill="x", padx=15, pady=4)
        
        conn_label = ctr.CTkLabel(conn_frame, text="Koneksi",
                                 font=ctr.CTkFont(size=12, weight="bold"),
                                 text_color=self.COLORS['text'])
        conn_label.pack(anchor="w", pady=(0, 4))
        
        # IP Input
        ip_label = ctr.CTkLabel(conn_frame, text="IP Address",
                               font=ctr.CTkFont(size=10),
                               text_color=self.COLORS['text_muted'])
        ip_label.pack(anchor="w")
        
        self.ip_entry = ctr.CTkEntry(conn_frame, height=32,
                                    placeholder_text="IP peer yang terkoneksi",
                                    fg_color=self.COLORS['bg_light'],
                                    border_color=self.COLORS['border'],
                                    text_color=self.COLORS['text'])
        self.ip_entry.pack(fill="x", pady=(2, 4))
        ip = get_local_ip()
        self.ip_entry.insert(0, ip)
        
        # Port Input
        port_label = ctr.CTkLabel(conn_frame, text="Port",
                                 font=ctr.CTkFont(size=10),
                                 text_color=self.COLORS['text_muted'])
        port_label.pack(anchor="w")
        
        self.port_entry = ctr.CTkEntry(conn_frame, height=32,
                                      placeholder_text="5000",
                                      fg_color=self.COLORS['bg_light'],
                                      border_color=self.COLORS['border'],
                                      text_color=self.COLORS['text'])
        self.port_entry.pack(fill="x", pady=(2, 6))
        self.port_entry.insert(0, "5000")
        
        # Connect button
        self.connect_btn = ctr.CTkButton(conn_frame, text="🔗 Connect",
                                        height=35,
                                        fg_color=self.COLORS['accent'],
                                        hover_color=self.COLORS['accent_hover'],
                                        font=ctr.CTkFont(size=12, weight="bold"),
                                        command=self._on_connect_click)
        self.connect_btn.pack(fill="x")
        
        # Separator
        sep2 = ctr.CTkFrame(scroll_content, height=1, fg_color=self.COLORS['border'])
        sep2.pack(fill="x", padx=15, pady=6)
        
        # Server info
        self.server_info = ctr.CTkLabel(scroll_content, text="Server: Not started",
                                       font=ctr.CTkFont(size=10),
                                       text_color=self.COLORS['text_muted'])
        self.server_info.pack(padx=15, anchor="w")
        
        # Separator
        sep3 = ctr.CTkFrame(scroll_content, height=1, fg_color=self.COLORS['border'])
        sep3.pack(fill="x", padx=15, pady=6)
        
        # Peers section
        peers_header = ctr.CTkLabel(scroll_content, text="Peers Connected",
                                   font=ctr.CTkFont(size=12, weight="bold"),
                                   text_color=self.COLORS['text'])
        peers_header.pack(padx=15, anchor="w", pady=(0, 3))
        
        # Peers frame 
        self.peers_frame = ctr.CTkFrame(scroll_content, fg_color=self.COLORS['bg_light'],
                                        corner_radius=6)
        self.peers_frame.pack(fill="x", padx=15, pady=(0, 6))
        
        # Groups section
        groups_header = ctr.CTkLabel(scroll_content, text="Groups",
                                    font=ctr.CTkFont(size=12, weight="bold"),
                                    text_color=self.COLORS['text'])
        groups_header.pack(padx=15, anchor="w", pady=(6, 3))
        
        # Create group button
        self.create_group_btn = ctr.CTkButton(scroll_content, text="➕ Create Group",
                                             height=30,
                                             fg_color=self.COLORS['group'],
                                             hover_color="#475569",
                                             font=ctr.CTkFont(size=11, weight="bold"),
                                             command=self._on_create_group_click)
        self.create_group_btn.pack(fill="x", padx=15, pady=(0, 4))
        
        # Groups frame 
        self.groups_frame = ctr.CTkFrame(scroll_content, fg_color=self.COLORS['bg_light'],
                                         corner_radius=6)
        self.groups_frame.pack(fill="x", padx=15, pady=(0, 12))
    
    def _create_chat_area(self):
        # Chat section 
        chat_container = ctr.CTkFrame(self.root, corner_radius=0,
                                     fg_color=self.COLORS['bg_dark'])
        chat_container.grid(row=0, column=1, sticky="nswe")
        chat_container.grid_columnconfigure(0, weight=1)
        chat_container.grid_rowconfigure(1, weight=1)
        
        # Chat header
        header = ctr.CTkFrame(chat_container, height=70, corner_radius=0,
                             fg_color=self.COLORS['bg_medium'])
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        # Bagian kiri - chat title
        left_header = ctr.CTkFrame(header, fg_color="transparent")
        left_header.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        self.chat_title = ctr.CTkLabel(left_header, text="Pilih peer atau group untuk chat",
                                       font=ctr.CTkFont(size=16, weight="bold"),
                                       text_color=self.COLORS['text'])
        self.chat_title.pack(anchor="w")
        
        self.chat_status = ctr.CTkLabel(left_header, text="",
                                        font=ctr.CTkFont(size=11),
                                        text_color=self.COLORS['success'])
        self.chat_status.pack(anchor="w")
        
        # Bagian kanan - username kita
        right_header = ctr.CTkFrame(header, fg_color="transparent")
        right_header.grid(row=0, column=0, sticky="e", padx=20, pady=15)
        
        self.my_username_label = ctr.CTkLabel(right_header, text="👤 Me",
                                              font=ctr.CTkFont(size=16, weight="bold"),
                                              text_color=self.COLORS['text'])
        self.my_username_label.pack(anchor="e")
        
        # Chat messages area
        self.chat_frame = ctr.CTkScrollableFrame(
            chat_container,
            fg_color=self.COLORS['bg_dark'],
            corner_radius=0
        )
        self.chat_frame.grid(row=1, column=0, sticky="nswe", padx=10, pady=(10, 0))

        # Progress bar
        self.progress_frame = ctr.CTkFrame(chat_container, fg_color="transparent")
        self.progress_label = ctr.CTkLabel(self.progress_frame, text="",
                                          font=ctr.CTkFont(size=11),
                                          text_color=self.COLORS['text_muted'])
        self.progress_label.pack(anchor="w", padx=10)
        self.progress_bar = ctr.CTkProgressBar(self.progress_frame, 
                                               progress_color=self.COLORS['accent'])
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        # Input area
        input_frame = ctr.CTkFrame(chat_container, height=70, corner_radius=0,
                                  fg_color=self.COLORS['bg_medium'])
        input_frame.grid(row=3, column=0, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)
        
        # File button
        self.file_btn = ctr.CTkButton(input_frame, text="📁", width=50, height=45,
                                     fg_color=self.COLORS['bg_light'],
                                     hover_color=self.COLORS['accent'],
                                     text_color=self.COLORS['text'],
                                     font=ctr.CTkFont(size=18),
                                     command=self._on_file_click)
        self.file_btn.grid(row=0, column=0, padx=(15, 10), pady=12)
        
        # Message entry
        self.message_entry = ctr.CTkEntry(input_frame, height=45,
                                         placeholder_text="Ketik pesan...",
                                         fg_color=self.COLORS['bg_light'],
                                         border_color=self.COLORS['border'],
                                         text_color=self.COLORS['text'],
                                         font=ctr.CTkFont(size=14))
        self.message_entry.grid(row=0, column=1, sticky="ew", pady=12)
        self.message_entry.bind('<Return>', self._on_send_click)
        
        # Send button
        self.send_btn = ctr.CTkButton(input_frame, text="➤ Send", width=100, height=45,
                                     fg_color=self.COLORS['accent'],
                                     hover_color=self.COLORS['accent_hover'],
                                     font=ctr.CTkFont(size=14, weight="bold"),
                                     command=self._on_send_click)
        self.send_btn.grid(row=0, column=2, padx=(10, 15), pady=12)
    
    def _on_connect_click(self):
        # Handle klik tombol connect
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
        # Handle klik tombol send
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
        
        self.message_entry.delete(0, "end")
    
    def _on_file_click(self):
        # Handle klik tombol file
        if not self.current_peer or self.current_is_group:
            messagebox.showwarning("Warning", "Kirim file hanya bisa ke peer langsung!")
            return
        
        filepath = filedialog.askopenfilename(title="Pilih file untuk dikirim")
        if filepath and self.on_send_file:
            self.on_send_file(self.current_peer, filepath)
    
    def _on_peer_click(self, peer_id: str):
        # Handle pemilihan peer
        self._switch_chat(peer_id, is_group=False)
        self._update_selected_states(peer_id, is_group=False)
    
    def _on_group_click(self, group_id: str):
        # Handle pemilihan group
        self._switch_chat(group_id, is_group=True)
        self._update_selected_states(group_id, is_group=True)
    
    def _update_selected_states(self, selected_id: str, is_group: bool):
        # Update visual state peer/group button
        for pid, btn in self.peer_buttons.items():
            if pid == selected_id and not is_group:
                btn.configure(fg_color=self.COLORS['accent'])
            else:
                btn.configure(fg_color="transparent")

        for gid, btn in self.group_buttons.items():
            if gid == selected_id and is_group:
                btn.configure(fg_color=self.COLORS['group'])
            else:
                btn.configure(fg_color="transparent")
    
    def _on_create_group_click(self):
        # Handle create group button
        if not self.peers:
            messagebox.showwarning("Warning", "Tidak ada peer yang terhubung!")
            return

        group_name = simpledialog.askstring("Create Group", "Masukkan nama group:",
                                           parent=self.root)
        if not group_name:
            return
        
        # Dialog member selection buat group
        dialog = ctr.CTkToplevel(self.root)
        dialog.title("Pilih Members")
        dialog.geometry("350x450")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.after(100, lambda: dialog.focus())
        
        ctr.CTkLabel(dialog, text="Pilih peers untuk diundang:",
                    font=ctr.CTkFont(size=14, weight="bold")).pack(pady=15)
        
        checkbox_frame = ctr.CTkScrollableFrame(dialog, height=250)
        checkbox_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        selected_peers = {}
        for peer_id, username in self.peers.items():
            var = ctr.BooleanVar()
            cb = ctr.CTkCheckBox(checkbox_frame, text=username,
                                variable=var,
                                font=ctr.CTkFont(size=13),
                                fg_color=self.COLORS['accent'],
                                hover_color=self.COLORS['accent_hover'])
            cb.pack(anchor="w", pady=5, padx=10)
            selected_peers[peer_id] = var
        
        def on_confirm():
            members = [pid for pid, var in selected_peers.items() if var.get()]
            if not members:
                messagebox.showwarning("Warning", "Pilih minimal 1 member!")
                return
            dialog.destroy()
            if self.on_create_group:
                self.on_create_group(group_name, members)
        
        ctr.CTkButton(dialog, text="Create Group",
                     fg_color=self.COLORS['group'],
                     hover_color="#475569",
                     font=ctr.CTkFont(size=14, weight="bold"),
                     height=42,
                     command=on_confirm).pack(pady=20)
    
    def _switch_chat(self, chat_id: str, is_group: bool = False):
        # Switch different chat dan load history
        self.current_peer = chat_id
        self.current_is_group = is_group
        
        if is_group:
            name = self.groups.get(chat_id, "Unknown Group")
            self.chat_title.configure(text=f"👥 {name}")
            self.chat_status.configure(text="🔐 Group Encrypted", text_color=self.COLORS['success'])
        else:
            name = self.peers.get(chat_id, "Unknown")
            self.chat_title.configure(text=f"💬 Chat dengan {name}")
            self.chat_status.configure(text="🔒 End-to-End Encrypted", text_color=self.COLORS['success'])
        
        self._load_chat_history(chat_id)
    
    def _load_chat_history(self, chat_id: str):
        # Load dan display chat history
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        
        if chat_id in self.chat_histories:
            for item in self.chat_histories[chat_id]:
                timestamp, sender, message, is_sent, msg_type = item
                
                if msg_type == 'message':
                    if is_sent:
                        self._add_sent_bubble(sender, message, timestamp)
                    else:
                        self._add_received_bubble(sender, message, timestamp)
                
                elif msg_type == 'system':
                    sys_frame = ctr.CTkFrame(self.chat_frame, fg_color="transparent")
                    sys_frame.pack(fill="x", pady=8)
                    
                    ctr.CTkLabel(
                        sys_frame,
                        text=f"--- {message} ---",
                        font=ctr.CTkFont(size=10, slant="italic"),
                        text_color=self.COLORS['text_muted']
                    ).pack()
                
                elif msg_type == 'file':
                    pass 

    def _store_message(self, chat_id: str, sender: str, message: str, is_sent: bool, msg_type: str = 'message'):
        # Store message ke chat history
        if chat_id not in self.chat_histories:
            self.chat_histories[chat_id] = []
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_histories[chat_id].append((timestamp, sender, message, is_sent, msg_type))
    
    def set_server_info(self, ip: str, port: int):
        # Set informasi server
        self.server_info.configure(text=f"📡 Server: {ip}:{port}")
    
    def set_username(self, username: str):
        # Set username kita 
        self.my_username = username
        self.my_username_label.configure(text=f"👤 {username}")
    
    def add_peer(self, peer_id: str, username: str):
        # Tambah peer ke list
        self.peers[peer_id] = username
        self._update_peers_list()
        self.add_system_message(f"{username} terhubung")
    
    def remove_peer(self, peer_id: str):
        # Hapus peer dari list
        if peer_id in self.peers:
            username = self.peers[peer_id]
            del self.peers[peer_id]
            self._update_peers_list()
            self.add_system_message(f"{username} terputus")
            
            if self.current_peer == peer_id:
                self.current_peer = None
                self.current_is_group = False
                self.chat_title.configure(text="Pilih peer atau group untuk chat")
                self.chat_status.configure(text="")
    
    def _update_peers_list(self):
        # Update tampilan list peers
        for widget in self.peers_frame.winfo_children():
            widget.destroy()
        self.peer_buttons.clear()
        
        for peer_id, username in self.peers.items():
            btn = ctr.CTkButton(self.peers_frame, 
                               text=f"👤 {username}",
                               fg_color="transparent",
                               hover_color=self.COLORS['accent'],
                               text_color=self.COLORS['text'],
                               anchor="w",
                               height=35,
                               font=ctr.CTkFont(size=13),
                               command=lambda pid=peer_id: self._on_peer_click(pid))
            btn.pack(fill="x", pady=2)
            self.peer_buttons[peer_id] = btn
    
    def add_group(self, group_id: str, group_name: str):
        # Add group ke list
        self.groups[group_id] = group_name
        self._update_groups_list()
    
    def _update_groups_list(self):
        # Update tampilan list groups
        for widget in self.groups_frame.winfo_children():
            widget.destroy()
        self.group_buttons.clear()
        
        for group_id, group_name in self.groups.items():
            btn = ctr.CTkButton(self.groups_frame,
                               text=f"👥 {group_name}",
                               fg_color="transparent",
                               hover_color=self.COLORS['group'],
                               text_color=self.COLORS['text'],
                               anchor="w",
                               height=35,
                               font=ctr.CTkFont(size=13),
                               command=lambda gid=group_id: self._on_group_click(gid))
            btn.pack(fill="x", pady=2)
            self.group_buttons[group_id] = btn
    
    def add_message(self, sender: str, message: str, is_sent: bool = False, peer_id: str = None):
        # Tambah pesan ke area chat dengan bubble
        chat_id = peer_id if peer_id else self.current_peer
        if not chat_id:
            return

        self._store_message(chat_id, sender, message, is_sent, 'message')

        if chat_id == self.current_peer:
            timestamp = datetime.now().strftime("%H:%M")
            
            if is_sent:
                self._add_sent_bubble(sender, message, timestamp)
            else:
                self._add_received_bubble(sender, message, timestamp)

            self.chat_frame._parent_canvas.yview_moveto(1.0)


    def _add_sent_bubble(self, sender: str, message: str, timestamp: str):
       # Buat bubble untuk pesan yang terkirim
        container = ctr.CTkFrame(self.chat_frame, fg_color="transparent")
        container.pack(fill="x", pady=5)
        inner = ctr.CTkFrame(container, fg_color="transparent")
        inner.pack(side="right", anchor="e", padx=10)

        bubble = ctr.CTkFrame(inner, fg_color=self.COLORS['message_sent'], corner_radius=12)
        bubble.pack(anchor="e")
        
        msg_label = ctr.CTkLabel(
            bubble,
            text=message,
            font=ctr.CTkFont(size=13),
            text_color=self.COLORS['text'],
            wraplength=350,
            justify="left",
            anchor="w"
        )
        msg_label.pack(padx=12, pady=8)
        
        info_label = ctr.CTkLabel(
            inner,
            text=f"You  •  {timestamp}",
            font=ctr.CTkFont(size=10),
            text_color=self.COLORS['text_muted']
        )
        info_label.pack(anchor="e", pady=(2, 0))


    def _add_received_bubble(self, sender: str, message: str, timestamp: str):
        # Buat bubble untuk pesan yang terkirim
        container = ctr.CTkFrame(self.chat_frame, fg_color="transparent")
        container.pack(fill="x", pady=5)
        inner = ctr.CTkFrame(container, fg_color="transparent")
        inner.pack(side="left", anchor="w", padx=10)
        
        bubble = ctr.CTkFrame(inner, fg_color=self.COLORS['message_received'], corner_radius=12)
        bubble.pack(anchor="w")
        
        msg_label = ctr.CTkLabel(
            bubble,
            text=message,
            font=ctr.CTkFont(size=13),
            text_color=self.COLORS['text'],
            wraplength=350,
            justify="left",
            anchor="w"
        )
        msg_label.pack(padx=12, pady=8)
        
        info_label = ctr.CTkLabel(
            inner,
            text=f"{sender}  •  {timestamp}",
            font=ctr.CTkFont(size=10),
            text_color=self.COLORS['text_muted']
        )
        info_label.pack(anchor="w", pady=(2, 0))


    
    def add_group_message(self, group_id: str, sender: str, message: str, is_sent: bool = False):
        # Tambah pesan group ke chat
        self._store_message(group_id, sender, message, is_sent, 'message')
        
        if group_id == self.current_peer and self.current_is_group:
            timestamp = datetime.now().strftime("%H:%M")
            
            if is_sent:
                self._add_group_sent_bubble(sender, message, timestamp)
            else:
                self._add_group_received_bubble(sender, message, timestamp)
            
            self.chat_frame._parent_canvas.yview_moveto(1.0)

    def _add_group_sent_bubble(self, sender: str, message: str, timestamp: str):
        # Bubble pesan group yg terkirim
        container = ctr.CTkFrame(self.chat_frame, fg_color="transparent")
        container.pack(fill="x", pady=5)
        inner = ctr.CTkFrame(container, fg_color="transparent")
        inner.pack(side="right", anchor="e", padx=10)
        
        bubble = ctr.CTkFrame(inner, fg_color=self.COLORS['message_sent'], corner_radius=12)
        bubble.pack(anchor="e")
        
        msg_label = ctr.CTkLabel(
            bubble,
            text=message,
            font=ctr.CTkFont(size=13),
            text_color=self.COLORS['text'],
            wraplength=350,
            justify="left",
            anchor="w"
        )
        msg_label.pack(padx=12, pady=8)

        info_label = ctr.CTkLabel(
            inner,
            text=f"You  •  {timestamp}",
            font=ctr.CTkFont(size=10),
            text_color=self.COLORS['text_muted']
        )
        info_label.pack(anchor="e", pady=(2, 0))


    def _add_group_received_bubble(self, sender: str, message: str, timestamp: str):
        # Bubble pesan group yg diterima
        container = ctr.CTkFrame(self.chat_frame, fg_color="transparent")
        container.pack(fill="x", pady=5)
        inner = ctr.CTkFrame(container, fg_color="transparent")
        inner.pack(side="left", anchor="w", padx=10)
        
        bubble = ctr.CTkFrame(inner, fg_color=self.COLORS['message_received'], corner_radius=12)
        bubble.pack(anchor="w")
        
        msg_label = ctr.CTkLabel(
            bubble,
            text=message,
            font=ctr.CTkFont(size=13),
            text_color=self.COLORS['text'],
            wraplength=350,
            justify="left",
            anchor="w"
        )
        msg_label.pack(padx=12, pady=8)
        
        info_label = ctr.CTkLabel(
            inner,
            text=f"{sender}  •  {timestamp}",
            font=ctr.CTkFont(size=10),
            text_color=self.COLORS['text_muted']
        )
        info_label.pack(anchor="w", pady=(2, 0))

    
    def add_file_message(self, sender: str, filename: str, is_sent: bool = False, peer_id: str = None):
        # Tambah notifikasi file ke chat
        chat_id = peer_id if peer_id else self.current_peer
        if not chat_id:
            return
        
        action = "mengirim" if is_sent else "mengirim"
        prefix = "You" if is_sent else sender
        msg = f"{prefix} {action} file: {filename}"
        
        self._store_message(chat_id, sender, msg, is_sent, 'file')
        
        if chat_id == self.current_peer:
            timestamp = datetime.now().strftime("%H:%M")
            self._add_file_bubble(sender, filename, timestamp, is_sent)
            self.chat_frame._parent_canvas.yview_moveto(1.0)
    
    def _add_file_bubble(self, sender: str, filename: str, timestamp: str, is_sent: bool):
        # Bubble untuk file message
        container = ctr.CTkFrame(self.chat_frame, fg_color="transparent")
        container.pack(fill="x", pady=5)
        
        if is_sent:
            inner = ctr.CTkFrame(container, fg_color="transparent")
            inner.pack(side="right", anchor="e", padx=10)
            bubble_color = self.COLORS['message_sent']
            anchor = "e"
            info_text = f"You  •  {timestamp}"
        else:
            inner = ctr.CTkFrame(container, fg_color="transparent")
            inner.pack(side="left", anchor="w", padx=10)
            bubble_color = self.COLORS['message_received']
            anchor = "w"
            info_text = f"{sender}  •  {timestamp}"
        
        bubble = ctr.CTkFrame(inner, fg_color=bubble_color, corner_radius=12)
        bubble.pack(anchor=anchor)
        
        msg_label = ctr.CTkLabel(
            bubble,
            text=f"📁 {filename}",
            font=ctr.CTkFont(size=13),
            text_color=self.COLORS['text'],
            wraplength=350,
            justify="left",
            anchor="w"
        )
        msg_label.pack(padx=12, pady=8)
        
        info_label = ctr.CTkLabel(
            inner,
            text=info_text,
            font=ctr.CTkFont(size=10),
            text_color=self.COLORS['text_muted']
        )
        info_label.pack(anchor=anchor, pady=(2, 0))
    
    def add_file_message_with_download(self, sender: str, filename: str, file_id: str, filesize: int = 0, peer_id: str = None):
        # Tambah notifikasi file dan tombol download ke chat
        chat_id = peer_id if peer_id else self.current_peer
        timestamp = datetime.now().strftime("%H:%M")

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
        
        container = ctr.CTkFrame(self.chat_frame, fg_color="transparent")
        container.pack(fill="x", pady=5)
        
        inner = ctr.CTkFrame(container, fg_color="transparent")
        inner.pack(side="left", anchor="w", padx=10)

        bubble = ctr.CTkFrame(inner, fg_color=self.COLORS['message_received'], corner_radius=12)
        bubble.pack(anchor="w")
        
        msg_label = ctr.CTkLabel(
            bubble,
            text=f"📁 {filename}{size_info}",
            font=ctr.CTkFont(size=13),
            text_color=self.COLORS['text'],
            wraplength=350,
            justify="left",
            anchor="w"
        )
        msg_label.pack(padx=12, pady=(8, 4))

        download_btn = ctr.CTkButton(bubble, text="📥 Download",
                                    fg_color=self.COLORS['success'],
                                    hover_color="#22c55e",
                                    text_color=self.COLORS['bg_dark'],
                                    font=ctr.CTkFont(size=12, weight="bold"),
                                    height=32, width=120,
                                    command=lambda fid=file_id: self._on_download_click(fid))
        download_btn.pack(padx=12, pady=(0, 8))
        
        info_label = ctr.CTkLabel(
            inner,
            text=f"{sender}  •  {timestamp}",
            font=ctr.CTkFont(size=10),
            text_color=self.COLORS['text_muted']
        )
        info_label.pack(anchor="w", pady=(2, 0))
        
        self.pending_files[file_id] = {
            'filename': filename,
            'button': download_btn,
            'bubble': bubble
        }
        
        self.chat_frame._parent_canvas.yview_moveto(1.0)
    
    def _on_download_click(self, file_id: str):
        # Handle klik tombol download
        if file_id in self.pending_files:
            file_info = self.pending_files[file_id]
            file_info['button'].configure(text="⏳ Menyimpan...", state="disabled")
            
            if self.on_download_file:
                self.on_download_file(file_id)
    
    def mark_file_downloaded(self, file_id: str, save_path: str):
        # Tandai file sudah didownload
        if file_id in self.pending_files:
            file_info = self.pending_files[file_id]
            
            file_info['button'].configure(
                text="✅ Tersimpan",
                fg_color=self.COLORS['text_muted'],
                state="disabled"
            )
            
            # Add saved location label
            if 'bubble' in file_info:
                loc_label = ctr.CTkLabel(
                    file_info['bubble'],
                    text=f"📂 {save_path}",
                    font=ctr.CTkFont(size=10),
                    text_color=self.COLORS['text_muted'],
                    wraplength=300
                )
                loc_label.pack(padx=12, pady=(0, 8))
            
            del self.pending_files[file_id]
    
    def add_system_message(self, message: str, chat_id: str = None):
        # Tambah pesan sistem ke chat
        if chat_id:
            self._store_message(chat_id, "", message, False, 'system')

        sys_frame = ctr.CTkFrame(self.chat_frame, fg_color="transparent")
        sys_frame.pack(fill="x", pady=8)
        
        sys_label = ctr.CTkLabel(
            sys_frame,
            text=f"--- {message} ---",
            font=ctr.CTkFont(size=10, slant="italic"),
            text_color=self.COLORS['text_muted']
        )
        sys_label.pack()

    
    def show_progress(self, filename: str, progress: float):
        # Tampilkan progress transfer file
        if progress <= 0:
            self.progress_frame.grid_forget()
        else:
            self.progress_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
            self.progress_label.configure(text=f"Transferring: {os.path.basename(filename)}")
            self.progress_bar.set(progress / 100)
            
            if progress >= 100:
                self.root.after(1000, lambda: self.progress_frame.grid_forget())
    
    def show_error(self, message: str):
        # Tampilkan pesan error
        messagebox.showerror("Error", message)
    
    def show_info(self, message: str):
        # Tampilkan pesan info
        messagebox.showinfo("Info", message)
    
    def run(self):
        # Jalankan GUI
        self.root.mainloop()
    
    def close(self):
        # Tutup GUI
        self.root.quit()
        self.root.destroy()
