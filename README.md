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
- **👥 User List** - Daftar perangkat yang terhubung dengan detail lengkap
- **🔐 Admin Control** - Kontrol akses untuk perintah sensitif
- **🛡️ Security Monitoring** - Monitoring keamanan sistem real-time

### 🚀 **Fitur Lanjutan**
- **⬆️ Update Bot** - Update otomatis dari GitHub repository
- **🗑️ Uninstall** - Penghapusan bersih dengan opsi backup konfigurasi
- **📝 Interactive Buttons** - Interface button yang mudah digunakan
- **🔄 Auto-restart** - Service otomatis restart jika terjadi error

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

## 🎮 Cara Penggunaan

### Interface Button

Bot menyediakan keyboard interaktif dengan tombol:

**Baris 1:**
- 📊 **System Info** - Informasi sistem lengkap
- 🔄 **Reboot** - Restart perangkat

**Baris 2:**
- 🧹 **Clear RAM** - Bersihkan cache memori
- 🌐 **Network Stats** - Statistik jaringan

**Baris 3:**
- 🚀 **Speed Test** - Test kecepatan internet
- 📡 **Ping Test** - Test konektivitas

**Baris 4:** *(FITUR BARU)*
- 📶 **WiFi Info** - Informasi WiFi lengkap
- 🔥 **Firewall** - Status firewall dan keamanan

**Baris 5:** *(FITUR BARU)*
- 👥 **User List** - Daftar perangkat terhubung
- 💾 **Backup** - Backup sistem

**Baris 6:**
- ⬆️ **Update Bot** - Update dari GitHub *(Admin only)*
- 🗑️ **Uninstall Bot** - Hapus bot *(Admin only)*

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
| `/wifi` | **BARU** - Informasi WiFi dan client | Semua user |
| `/firewall` | **BARU** - Status firewall dan rules | Semua user |
| `/userlist` | Daftar perangkat yang terhubung | Semua user |
| `/backup` | **BARU** - Backup konfigurasi sistem | Semua user |
| `/update` | Update bot dari GitHub | **Admin only** |
| `/uninstall` | Hapus bot dari sistem | **Admin only** |

## ⚙️ Konfigurasi

### File Konfigurasi (`config.ini`)

```ini
[Telegram]
api_id = YOUR_API_ID
api_hash = YOUR_API_HASH
bot_token = YOUR_BOT_TOKEN
admin_id = YOUR_ADMIN_ID

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

## 🔧 Plugin System

Bot menggunakan sistem plugin modular dengan script shell di direktori `plugins/`:

### Plugin Tersedia

| Plugin | File | Deskripsi |
|--------|------|-----------|
| **System Monitor** | `system.sh` | Monitoring sistem real-time |
| **Memory Cleaner** | `clear_ram.sh` | Pembersihan cache RAM |
| **Network Stats** | `vnstat.sh` | Statistik penggunaan jaringan |
| **Speed Test** | `speedtest.sh` | Test kecepatan internet |
| **Ping Test** | `ping.sh` | Test konektivitas jaringan |
| **WiFi Info** | `wifi.sh` | **BARU** - Informasi WiFi lengkap |
| **Firewall Status** | `firewall.sh` | **BARU** - Status firewall |
| **User List** | `userlist.sh` | Daftar perangkat terhubung |
| **System Backup** | `backup.sh` | **BARU** - Backup sistem |
| **System Reboot** | `reboot.sh` | Restart perangkat |
| **Bot Update** | `update.sh` | Update bot dari GitHub |
| **Bot Uninstall** | `uninstall.sh` | Penghapusan bot |

### Menambah Plugin Baru

1. Buat script shell baru di `/root/REVDBOT/plugins/`
2. Berikan permission executable: `chmod +x plugin_name.sh`
3. Tambahkan ke `required_scripts` di `bot_openwrt.py`
4. Tambahkan handler dan button di bot

## 🔧 Manajemen Service

### Kontrol Service

```bash
# Start bot
/etc/init.d/revd start

# Stop bot
/etc/init.d/revd stop

# Restart bot
/etc/init.d/revd restart

# Check status
/etc/init.d/revd status

# Enable auto-start
/etc/init.d/revd enable

# Disable auto-start
/etc/init.d/revd disable
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

### Database Locked Error

Jika terjadi error "database is locked":

```bash
# Stop service
/etc/init.d/revd stop

# Remove session files
rm -f /root/REVDBOT/bot_session.session*

# Restart service
/etc/init.d/revd start
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
/etc/init.d/revd restart
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

3. **Monitor logs** secara berkala

4. **Update bot** secara rutin

### Security Features

- ✅ **Admin-only commands** untuk operasi sensitif
- ✅ **Command confirmation** untuk operasi berbahaya
- ✅ **Session management** yang aman
- ✅ **Input validation** untuk semua perintah
- ✅ **Timeout protection** untuk operasi long-running

## 📊 Fitur Monitoring

### System Information
- CPU usage dan temperature
- Memory usage (RAM/Storage)
- System uptime dan load average
- Kernel dan firmware version

### Network Monitoring
- Bandwidth usage statistics
- Connected devices list
- WiFi information dan client count
- Internet speed testing
- Network connectivity testing

### Security Monitoring
- Firewall status dan rules
- Port forwarding configuration
- Connection tracking
- Blocked connections count

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

### v2.1 (Latest - Enhanced Edition)
- ✅ **NEW**: WiFi Information plugin dengan detail lengkap
- ✅ **NEW**: Firewall Status monitoring
- ✅ **NEW**: System Backup functionality
- ✅ **IMPROVED**: Button interface dengan 6 baris menu
- ✅ **IMPROVED**: Plugin system yang lebih modular
- ✅ **IMPROVED**: Error handling dan logging
- ✅ **IMPROVED**: Database lock prevention
- ✅ **FIXED**: Button responsiveness issues
- ✅ **FIXED**: Access denied problems
- ✅ **FIXED**: Service startup reliability

### v2.0 (Enhanced Edition)
- ✅ Enhanced security features
- ✅ Improved error handling
- ✅ Better logging system
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

**🔥 Fitur Terbaru v2.1:**
- 📶 WiFi Info dengan monitoring client real-time
- 🔥 Firewall Status dengan detail rules
- 💾 System Backup dengan kompresi otomatis
- 🎯 Interface button yang lebih lengkap dan responsif