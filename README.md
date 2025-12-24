# 🔒 P2P Secure Chat Application

Aplikasi chat peer-to-peer (P2P) terenkripsi end-to-end dengan dukungan group chat, transfer file, dan antarmuka GUI.

## ✨ Fitur

- **Enkripsi End-to-End**: Menggunakan X25519 (ECDH) untuk key exchange dan ChaCha20-Poly1305 untuk enkripsi pesan
- **Chat P2P**: Komunikasi langsung antar peer tanpa server pusat
- **Group Chat**: Membuat dan bergabung dalam group chat terenkripsi
- **Transfer File**: Mengirim dan menerima file terenkripsi
- **GUI**: Interface berbasis Tkinter dengan tema dark purple yang elegan
- **CLI Version**: Versi command-line untuk environment tanpa GUI
- **Auto-Download Management**: Sistem download file dengan progress tracking

## 🔐 Keamanan

- **X25519**: Elliptic Curve Diffie-Hellman untuk pertukaran kunci aman
- **ChaCha20-Poly1305**: Authenticated encryption dengan AEAD (Authenticated Encryption with Associated Data)
- **Per-Peer Encryption**: Setiap peer memiliki shared key unik
- **Group Key Distribution**: Kunci group didistribusikan secara aman melalui encrypted channel

## 📋 Requirements

- Python 3.7+
- Lihat `requirements.txt` untuk dependencies lengkap

## 🚀 Instalasi

1. Clone repository:
```bash
git clone <repository-url>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 💻 Cara Penggunaan

### GUI Version (Recommended)

Jalankan aplikasi dengan antarmuka grafis:

```bash
python main.py
```

**Langkah-langkah:**
1. Masukkan username Anda saat diminta
2. Masukkan port untuk server lokal (default: 5000)
3. Aplikasi akan menampilkan IP dan port server Anda
4. Untuk terhubung ke peer lain:
   - Masukkan IP address peer lain
   - Masukkan port peer lain
   - Klik tombol "Connect"
5. Pilih peer dari daftar untuk mulai chat
6. Untuk membuat group: klik "Create Group" dan pilih members

### CLI Version

Jalankan versi command-line:

```bash
python main_cli.py
```

**Menu CLI:**
- `1` - Connect ke peer lain
- `2` - Lihat daftar peer terhubung
- `3` - Pilih peer untuk chat
- `4` - Pilih group untuk chat
- `5` - Kirim pesan ke peer
- `6` - Buat group baru
- `7` - Lihat daftar group
- `8` - Kirim pesan ke group
- `0` - Keluar

## 📁 Struktur Proyek

```
p2p-secure-chat/
│
├── main.py           # Entry point aplikasi GUI
├── main_cli.py       # Entry point aplikasi CLI
├── crypto.py         # Modul enkripsi dan key management
├── network.py        # Modul networking P2P
├── gui.py            # Modul GUI dengan Tkinter
├── requirements.txt  # Dependencies Python
├── README.md         # Dokumentasi ini
└── downloads/        # Folder untuk file yang diunduh (auto-created)
```

## 🔧 Konfigurasi

### Port Default
- Default port: `5000`
- Pastikan port tidak digunakan oleh aplikasi lain
- Gunakan port berbeda jika menjalankan multiple instances di satu mesin

### Network
- Aplikasi otomatis mendeteksi IP lokal
- Untuk koneksi LAN: gunakan IP lokal (192.168.x.x)
- Untuk testing lokal: gunakan 127.0.0.1

### File Transfer
- File terenkripsi sebelum dikirim
- Chunk size: 32KB
- File disimpan di folder `downloads/`
- Nama file duplikat otomatis diberi timestamp

## 🛡️ Arsitektur Keamanan

### 1. Key Exchange (X25519)
- Setiap peer menggenerate private/public key pair
- Public key ditukar saat koneksi
- Shared secret derived menggunakan ECDH

### 2. Message Encryption (ChaCha20-Poly1305)
- Setiap pesan menggunakan nonce random 12-byte
- AEAD memastikan integritas dan autentikasi
- Tidak ada pesan plaintext yang dikirim melalui network

### 3. Group Chat Encryption
- Creator group menggenerate symmetric key 32-byte
- Key didistribusikan terenkripsi ke setiap member
- Semua pesan group menggunakan shared group key

### 4. File Encryption
- File dienkripsi sebelum transfer
- Menggunakan shared key yang sama dengan chat
- Transfer dalam chunks untuk efisiensi

## 🐛 Troubleshooting

### Peer tidak bisa terhubung
- Pastikan kedua peer sudah menjalankan aplikasi
- Check firewall settings
- Pastikan IP dan port sudah benar
- Verifikasi kedua peer berada di network yang sama (untuk LAN)

### Error "Port already in use"
- Ganti port ke nomor lain (misal: 5001, 5002, dst)
- Check apakah ada instance lain yang berjalan

### Gagal dekripsi pesan
- Pastikan key exchange sudah selesai (tunggu notifikasi "🔐 Kunci enkripsi diterima")
- Reconnect jika masih gagal

## 📝 Development Notes

### Menambah Fitur
- `crypto.py`: Tambah metode enkripsi baru
- `network.py`: Tambah message type dan handler
- `gui.py`: Tambah UI component
- `main.py`: Integrasikan callback dan logic

### Testing
- Jalankan multiple instances dengan port berbeda
- Test di environment LAN untuk real P2P testing
- Test dengan file berbagai ukuran untuk file transfer

## 📄 License

Project ini dibuat untuk tujuan pembelajaran tentang:
- Peer-to-peer networking
- Cryptography implementation
- End-to-end encryption
- GUI development dengan Python

**Mohon Maaf Lahir dan Batin! 🔒💬**
