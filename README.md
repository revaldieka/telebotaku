# 🤖 OpenWRT Telegram Bot - Enhanced Edition

**Kelola perangkat OpenWRT Anda melalui Telegram dengan mudah dan aman!**

Bot Telegram canggih untuk monitoring dan manajemen perangkat OpenWRT dengan fitur lengkap, keamanan berlapis, dan antarmuka yang user-friendly.

## ✨ Fitur Utama

### 🔧 **Manajemen Sistem**
- **📊 System Info** - Monitoring sistem real-time (CPU, RAM, Temperature, Uptime)
- **🔄 Reboot** - Restart perangkat dengan konfirmasi keamanan
- **🧹 Clear RAM** - Pembersihan cache memori untuk performa optimal
- **💾 Backup** - Backup konfigurasi sistem lengkap dengan kompresi

### 🌐 **Monitoring Jaringan**
- **📡 Network Stats** - Statistik penggunaan data dengan vnstat
- **🚀 Speed Test** - Test kecepatan internet real-time
- **📡 Ping Test** - Test konektivitas ke target tertentu
- **📶 WiFi Info** - Informasi lengkap WiFi dan client yang terhubung

### 🛡️ **Keamanan & Firewall**
- **🔥 Firewall Status** - Status firewall, rules, dan port forwarding
- **👥 User List** - Daftar perangkat yang terhubung
- **🔐 Multi-user Access** - Kontrol akses untuk multiple user
- **🛡️ Admin Privileges** - Perintah sensitif hanya untuk admin

### 🚀 **Fitur Lanjutan**
- **⬆️ Update Bot** - Update otomatis dari GitHub repository
- **📈 Bot Statistics** - Statistik penggunaan dan performa bot
- **🗑️ Uninstall** - Penghapusan bersih dengan opsi backup
- **📝 Command History** - Riwayat perintah yang dieksekusi (admin only)

## 🚀 Instalasi

### Auto Installer (Recommended)

Salin dan tempel perintah berikut di terminal OpenWRT Anda:

1. **Masuk ke direktori root:**
```bash
cd
```

2. **Jalankan auto installer:**
```bash
opkg update && (cd /tmp && curl -sLko revd_installer.sh https://raw.githubusercontent.com/revaldieka/telebotaku/main/revd_installer.sh && chmod +x revd_installer.sh && sh revd_installer.sh)
```

Installer akan secara otomatis:
- ✅ Memperbarui daftar paket OpenWRT
- ✅ Menginstal dependensi yang diperlukan
- ✅ Mengunduh bot dari GitHub repository
- ✅ Menyiapkan konfigurasi dan service
- ✅ Mengaktifkan auto-start saat boot
- ✅ Memulai bot service

### Manual Installation

1. **Download semua file dan upload ke OpenWRT**
2. **Masuk ke direktori root:**
   ```bash
   cd
   ```
3. **Berikan permission executable:**
   ```bash
   chmod +x revd_installer.sh
   ```
4. **Jalankan installer:**
   ```bash
   ./revd_installer.sh
   ```

## 🔑 Mendapatkan Kredensial Telegram

### 1. Bot Token dari BotFather

1. Buka Telegram dan cari `@BotFather`
2. Kirim `/start` untuk memulai
3. Kirim `/newbot` untuk membuat bot baru
4. Ikuti instruksi:
   - **Nama bot**: Boleh pakai spasi (contoh: "OpenWRT Manager")
   - **Username bot**: Harus diakhiri 'bot' (contoh: "openwrt_manager_bot")
5. Salin **Bot Token** yang diberikan (format: `123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ`)

### 2. Admin ID (Chat ID)

1. Di Telegram, cari `@userinfobot`
2. Kirim `/start`
3. Bot akan membalas dengan ID Anda (contoh: `Your ID: 123456789`)
4. Salin angka tersebut sebagai **Admin ID**

### 3. API ID dan API Hash

1. Kunjungi https://my.telegram.org/auth
2. Masukkan nomor telepon Telegram Anda
3. Masukkan kode verifikasi dari aplikasi Telegram
4. Pilih "API development tools"
5. Isi formulir:
   - **App title**: "OpenWRT Bot"
   - **Short name**: "openwrt_bot"
   - **Platform**: Desktop
6. Klik "Create Application"
7. Salin **API ID** (angka) dan **API Hash** (kode alfanumerik)

### 4. Multi-User Access (Opsional)

Untuk memberikan akses ke user lain, tambahkan User ID mereka di `allowed_users` (pisahkan dengan koma):
```
allowed_users = 123456789,987654321,555666777
```

## 🎮 Cara Penggunaan

### Perintah Tersedia

| Perintah | Deskripsi | Akses |
|----------|-----------|-------|
| `/start` | Memulai bot dan menampilkan menu utama | Semua user |
| `/help` | Menampilkan bantuan dan daftar perintah | Semua user |
| `/system` | Informasi sistem lengkap | Semua user |
| `/reboot` | Restart perangkat (dengan konfirmasi) | Semua user |
| `/clearram` | Bersihkan cache RAM | Semua user |
| `/network` | Statistik jaringan dan penggunaan data | Semua user |
| `/speedtest` | Test kecepatan internet | Semua user |
| `/ping [target]` | Ping test ke target (default: google.com) | Semua user |
| `/userlist` | Daftar perangkat yang terhubung | Semua user |
| `/wifi` | Informasi WiFi dan client | Semua user |
| `/firewall` | Status firewall dan rules | Semua user |
| `/backup` | Backup konfigurasi sistem | Semua user |
| `/stats` | Statistik bot dan performa | Semua user |
| `/update` | Update bot dari GitHub | **Admin only** |
| `/uninstall` | Hapus bot dari sistem | **Admin only** |
| `/history` | Riwayat perintah yang dieksekusi | **Admin only** |

### Interface Button

Bot menyediakan keyboard interaktif dengan tombol:

**Baris 1:**
- 📊 System Info
- 🔄 Reboot

**Baris 2:**
- 🧹 Clear RAM
- 🌐 Network Stats

**Baris 3:**
- 🚀 Speed Test
- 📡 Ping Test

**Baris 4:**
- 📶 WiFi Info
- 🔥 Firewall

**Baris 5:**
- 👥 User List
- 💾 Backup

**Baris 6:**
- 📈 Bot Stats
- ⬆️ Update Bot

**Baris 7:**
- 🗑️ Uninstall Bot
- ℹ️ Help

## ⚙️ Konfigurasi Lanjutan

### File Konfigurasi (`config.ini`)

```ini
[Telegram]
api_id = YOUR_API_ID
api_hash = YOUR_API_HASH
bot_token = YOUR_BOT_TOKEN
admin_id = YOUR_ADMIN_ID
allowed_users = USER_ID_1,USER_ID_2,USER_ID_3

[OpenWRT]
device_name = OpenWRT | REVD.CLOUD
auto_backup = true
notification_enabled = true
```

### Opsi Konfigurasi

| Parameter | Deskripsi | Default |
|-----------|-----------|---------|
| `device_name` | Nama perangkat yang ditampilkan di bot | OpenWRT \| REVD.CLOUD |
| `auto_backup` | Backup otomatis saat update | true |
| `notification_enabled` | Notifikasi startup ke admin | true |
| `allowed_users` | Daftar user ID yang diizinkan akses | (kosong = hanya admin) |

## 🔧 Manajemen Service

### Kontrol Service

```bash
# Start bot
service revd start

# Stop bot
service revd stop

# Restart bot
service revd restart

# Check status
service revd status

# Enable auto-start
service revd enable

# Disable auto-start
service revd disable
```

### Monitoring Logs

```bash
# View real-time logs
tail -f /var/log/revd_bot.log

# View system logs
logread | grep revd

# Check bot process
ps | grep bot_openwrt.py
```

## 🛠️ Troubleshooting

### Bot Tidak Start

1. **Periksa konfigurasi:**
   ```bash
   cat /root/REVDBOT/config.ini
   ```

2. **Test manual:**
   ```bash
   cd /root/REVDBOT
   python3 bot_openwrt.py
   ```

3. **Periksa dependensi:**
   ```bash
   opkg list-installed | grep python3
   pip3 list | grep telethon
   ```

### Service Tidak Auto-Start

1. **Periksa service enable:**
   ```bash
   ls -la /etc/rc.d/ | grep revd
   ```

2. **Re-enable service:**
   ```bash
   /etc/init.d/revd enable
   ```

### Plugin Script Error

1. **Periksa permission:**
   ```bash
   ls -la /root/REVDBOT/plugins/
   ```

2. **Fix permission:**
   ```bash
   chmod +x /root/REVDBOT/plugins/*.sh
   ```

### Memory Issues

1. **Clear RAM:**
   ```bash
   sync && echo 3 > /proc/sys/vm/drop_caches
   ```

2. **Check memory:**
   ```bash
   free -m
   ```

## 🔄 Update & Maintenance

### Auto Update

Bot dapat update otomatis melalui Telegram:
1. Kirim `/update` (admin only)
2. Konfirmasi update
3. Bot akan download versi terbaru dari GitHub
4. Restart otomatis setelah update

### Manual Update

```bash
cd /root/REVDBOT
git pull origin main
service revd restart
```

### Backup Manual

```bash
# Backup konfigurasi
cp -r /root/REVDBOT /tmp/revdbot_backup

# Backup sistem
sysupgrade -b /tmp/system_backup.tar.gz
```

## 🗑️ Uninstall

### Melalui Bot (Recommended)

1. Kirim `/uninstall` ke bot (admin only)
2. Pilih opsi:
   - **Keep config**: Simpan konfigurasi untuk reinstall
   - **Delete all**: Hapus semua data
   - **Cancel**: Batalkan uninstall

### Manual Uninstall

```bash
# Download uninstaller
cd /tmp
curl -sLko uninstall.sh https://raw.githubusercontent.com/revaldieka/telebotaku/main/uninstall.sh
chmod +x uninstall.sh

# Run uninstaller
./uninstall.sh
```

### One-Line Uninstaller

```bash
cd /tmp && curl -sLko uninstall.sh https://raw.githubusercontent.com/revaldieka/telebotaku/main/uninstall.sh && chmod +x uninstall.sh && sh uninstall.sh
```

## 🔒 Keamanan

### Best Practices

1. **Lindungi file konfigurasi:**
   ```bash
   chmod 600 /root/REVDBOT/config.ini
   ```

2. **Gunakan strong bot token** dari BotFather

3. **Batasi akses user** dengan `allowed_users`

4. **Monitor logs** secara berkala

5. **Update bot** secara rutin

### Security Features

- ✅ **Multi-layer authorization** (admin + allowed users)
- ✅ **Command logging** dengan timestamp
- ✅ **Session management** yang aman
- ✅ **Input validation** untuk semua perintah
- ✅ **Timeout protection** untuk operasi long-running

## 📊 Monitoring & Statistics

### Bot Statistics

Bot menyediakan statistik lengkap:
- Total perintah yang dieksekusi
- Uptime bot
- Memory usage
- Command frequency
- Error rate

### System Monitoring

- CPU usage dan temperature
- Memory usage (RAM/Storage)
- Network statistics
- Connected devices
- Firewall status

## 🆘 Support & Contact

### Dokumentasi
- **GitHub**: https://github.com/revaldieka/telebotaku
- **Issues**: Report bugs di GitHub Issues

### Contact
- **Telegram**: [@ValltzID](https://t.me/ValltzID)
- **Instagram**: [@revd.cloud](https://instagram.com/revd.cloud)
- **Website**: [revd.cloud](https://revd.cloud)

### Credits
- **Original Reference**: [@Tomketstore](https://t.me/Tomketstore)
- **Enhanced by**: REVD.CLOUD
- **License**: MIT License

## 📝 Changelog

### v2.0 (Enhanced Edition)
- ✅ Multi-user access control
- ✅ Enhanced security features
- ✅ New plugins (WiFi, Firewall, Backup)
- ✅ Bot statistics and monitoring
- ✅ Improved error handling
- ✅ Better logging system
- ✅ Command history tracking
- ✅ Auto-backup functionality

### v1.0 (Original)
- ✅ Basic system monitoring
- ✅ Network statistics
- ✅ Speed test functionality
- ✅ User management
- ✅ Auto-update feature

## 📄 License

MIT License - Lihat file [LICENSE](LICENSE) untuk detail lengkap.

---

**🚀 Developed with ❤️ by REVD.CLOUD**

*Terima kasih telah menggunakan OpenWRT Telegram Bot Enhanced Edition!*