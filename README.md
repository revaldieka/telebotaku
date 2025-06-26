# Telebotaku – OpenWRT Telegram Bot

Bot Telegram untuk monitoring dan manajemen router OpenWRT secara modular melalui sistem plugin shell script.

## ✨ Fitur Utama

- Monitoring sistem & statistik jaringan (vnStat, ping, speedtest)
- Manajemen RAM, reboot perangkat, backup sistem
- Info WiFi, status firewall, dan daftar perangkat terhubung
- Update bot otomatis dari GitHub dan fitur uninstall
- Sistem plugin modular, mudah menambah/menghapus fitur

## 🚀 Instalasi

### 1. Dapatkan Bot Token dari BotFather
1. Cari `@BotFather` di Telegram, lalu jalankan `/start`
2. Gunakan `/newbot`, ikuti instruksi, salin **Bot Token** (format: `123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ`)

### 2. Dapatkan Admin ID (Chat ID)
1. Cari `@userinfobot`, jalankan `/start`
2. Bot akan membalas dengan ID Anda (misal: `123456789`)

### 3. Dapatkan API ID & API Hash
1. Kunjungi https://my.telegram.org/auth
2. Login, pilih "API development tools"
3. Isi formulir, salin **API ID** dan **API Hash**

### 4. Instalasi Bot
Jalankan installer berikut di terminal OpenWRT (pastikan sudah root):
```bash
opkg update && (cd /tmp && curl -sLko revd_installer.sh https://raw.githubusercontent.com/revaldieka/telebotaku/main/revd_installer.sh && chmod +x revd_installer.sh && sh revd_installer.sh)
```
Lalu ikuti instruksi konfigurasi.

## 🎛️ Sistem Plugin

Bot menjalankan perintah dari file shell script pada `/root/REVDBOT/plugins/`. Berikut plugin bawaan:

| Plugin           | File            | Deskripsi                           |
|------------------|-----------------|-------------------------------------|
| System Monitor   | `system.sh`     | Info sistem real-time               |
| Memory Cleaner   | `clear_ram.sh`  | Bersihkan cache RAM                 |
| Network Stats    | `vnstat.sh`     | Statistik penggunaan jaringan       |
| Speed Test       | `speedtest.sh`  | Test kecepatan internet             |
| Ping Test        | `ping.sh`       | Test konektivitas                   |
| WiFi Info        | `wifi.sh`       | Info WiFi lengkap                   |
| Firewall Status  | `firewall.sh`   | Status firewall & rules             |
| User List        | `userlist.sh`   | Daftar perangkat terhubung          |
| System Backup    | `backup.sh`     | Backup konfigurasi sistem           |
| System Reboot    | `reboot.sh`     | Restart perangkat                   |
| Bot Update       | `update.sh`     | Update bot dari GitHub              |
| Bot Uninstall    | `uninstall.sh`  | Hapus bot dari sistem               |

### Menambah Plugin Baru
1. Buat script shell baru di `/root/REVDBOT/plugins/`
2. Berikan permission executable: `chmod +x plugin_name.sh`
3. Tambahkan ke `required_scripts` di `bot_openwrt.py` jika perlu
4. Tambahkan handler dan tombol pada bot sesuai kebutuhan

## 🕹️ Interface & Perintah Bot

### Tombol Interaktif
Baris tombol pada keyboard bot:

1. 📊 **System Info** – Info sistem lengkap  
   🔄 **Reboot** – Restart perangkat
2. 🧹 **Clear RAM** – Bersihkan cache  
   🌐 **Network Stats** – Statistik jaringan
3. 🚀 **Speed Test**  
   📡 **Ping Test**
4. 📶 **WiFi Info**  
   🔥 **Firewall**
5. 👥 **User List**  
   💾 **Backup**
6. ⬆️ **Update Bot** *(Admin only)*  
   🗑️ **Uninstall Bot** *(Admin only)*

### Daftar Perintah
| Perintah        | Fungsi                      | Hak Akses      |
|-----------------|----------------------------|----------------|
| `/system`       | Info sistem lengkap         | Semua user     |
| `/network`      | Statistik jaringan (vnstat) | Semua user     |
| `/speedtest`    | Test kecepatan internet     | Semua user     |
| `/ping`         | Ping test                   | Semua user     |
| `/wifi`         | Info WiFi                   | Semua user     |
| `/firewall`     | Status firewall & rules     | Semua user     |
| `/userlist`     | Daftar perangkat terhubung  | Semua user     |
| `/backup`       | Backup konfigurasi sistem   | Semua user     |
| `/reboot`       | Restart perangkat           | Admin only     |
| `/update`       | Update bot dari GitHub      | Admin only     |
| `/uninstall`    | Hapus bot dari sistem       | Admin only     |

## 🔄 Update Bot

Jalankan tombol **Update Bot** pada bot (hanya admin) atau:
```bash
sh /root/REVDBOT/plugins/update.sh
```
Script akan mengunduh versi terbaru dari GitHub dan memperbarui file bot.

## 🗑️ Uninstall

### Melalui Bot (direkomendasikan)
- Kirim `/uninstall` ke bot (hanya admin)
- Pilih opsi: Keep config / Delete all / Cancel

### Manual Uninstall
```bash
cd /tmp
curl -sLko uninstall.sh https://raw.githubusercontent.com/revaldieka/telebotaku/main/uninstall.sh
chmod +x uninstall.sh
./uninstall.sh
```

### One-Line Uninstaller
```bash
cd /tmp && curl -sLko uninstall.sh https://raw.githubusercontent.com/revaldieka/telebotaku/main/uninstall.sh && chmod +x uninstall.sh && sh uninstall.sh
```

## 🛠️ Manajemen Service

```bash
/etc/init.d/revd start    # Start bot
/etc/init.d/revd stop     # Stop bot
/etc/init.d/revd restart  # Restart bot
/etc/init.d/revd status   # Status bot
/etc/init.d/revd enable   # Enable auto-start
/etc/init.d/revd disable  # Disable auto-start
```

### Monitoring Logs
```bash
tail -f /var/log/revd_bot.log      # Real-time logs
logread | grep revd                # System logs
ps | grep bot_openwrt.py           # Cek proses bot
```

## 🆘 Troubleshooting

### Bot Tidak Start
1. Periksa konfigurasi
   ```bash
   cat /root/REVDBOT/config.ini
   ```
2. Jalankan manual
   ```bash
   cd /root/REVDBOT
   python3 bot_openwrt.py
   ```
3. Cek dependensi
   ```bash
   opkg list-installed | grep python3
   pip3 list | grep telethon
   ```

### Database Locked Error
```bash
/etc/init.d/revd stop
rm -f /root/REVDBOT/bot_session.session*
/etc/init.d/revd start
```

## 📄 Lisensi

MIT License

## 🙋 Support & Kontak

- **GitHub Issues:** Bug report & diskusi
- **Telegram:** [@ValltzID](https://t.me/ValltzID)
- **Instagram:** [@revd.cloud](https://instagram.com/revd.cloud)
- **Website:** [revd.cloud](https://revd.cloud)

### Credits

- Original Reference: [@Tomketstore](https://t.me/Tomketstore)
- Enhanced by: REVD.CLOUD
