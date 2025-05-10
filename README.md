## Instruksi Instalasi

### Metode 1: Menggunakan Skrip Installer (Direkomendasikan)

1. Unggah `revd_installer.sh` ke perangkat OpenWRT Anda (dalam direktori yang sama dengan bot Anda)
2. Jadikan executable:
   ```
   chmod +x revd_installer.sh
   ```
3. Jalankan installer:
   ```
   ./revd_installer.sh
   ```

Installer akan:
- Menginstal dependensi yang diperlukan
- Menyalin bot Anda ke `/root/revd/`
- Menyiapkan skrip init
- Mengaktifkan layanan untuk mulai saat boot
- Memulai layanan bot

### Metode 2: Instalasi Manual

Jika Anda lebih suka menyiapkan secara manual:

1. Buat skrip init:
   ```
   cat > /etc/init.d/revd << 'EOF'
#!/bin/sh /etc/rc.common

START=99
USE_PROCD=1
PROG=/usr/bin/python3
SCRIPT_PATH=/root/revd/bot_openwrt.py
LOG_FILE=/var/log/revd_bot.log

start_service() {
    # Check if script exists
    if [ ! -f "$SCRIPT_PATH" ]; then
        echo "Skrip bot tidak ditemukan di $SCRIPT_PATH"
        logger -t revd "Skrip bot tidak ditemukan di $SCRIPT_PATH"
        return 1
    fi
    
    # Check if Python3 is installed
    if [ ! -x "$PROG" ]; then
        echo "Python3 tidak ditemukan di $PROG"
        logger -t revd "Python3 tidak ditemukan di $PROG"
        return 1
    fi

    # Make sure plugins directory exists and has correct permissions
    if [ ! -d "/root/revd/plugins" ]; then
        mkdir -p /root/revd/plugins
        chmod 755 /root/revd/plugins
        logger -t revd "Membuat direktori plugins"
    fi

    # Check for plugin scripts and copy from backup if missing
    for script in speedtest.sh reboot.sh ping.sh clear_ram.sh vnstat.sh system.sh; do
        if [ ! -f "/root/revd/plugins/$script" ] && [ -f "/etc/revd_backup/$script" ]; then
            cp "/etc/revd_backup/$script" "/root/revd/plugins/$script"
            chmod +x "/root/revd/plugins/$script"
            logger -t revd "Memulihkan skrip $script dari backup"
        fi
    done
    
    # Log starting message
    logger -t revd "Memulai layanan Telegram Bot"
    
    # Configure the service with logging
    procd_open_instance
    procd_set_param command $PROG $SCRIPT_PATH
    procd_set_param stderr 1
    procd_set_param stdout 1
    procd_set_param respawn ${respawn_threshold:-3600} ${respawn_timeout:-5} ${respawn_retry:-5}
    procd_close_instance
    
    # Create a log entry for successful start
    echo "$(date): Service started" >> $LOG_FILE
}

stop_service() {
    # Log stopping message
    logger -t revd "Menghentikan layanan Telegram Bot"
    
    # Find and kill all Python processes running the bot script
    PIDS=$(ps | grep "$SCRIPT_PATH" | grep -v grep | awk '{print $1}')
    if [ -n "$PIDS" ]; then
        kill -9 $PIDS 2>/dev/null
        logger -t revd "Bot dihentikan, PID: $PIDS"
    else
        logger -t revd "Tidak ada proses bot yang berjalan"
    fi
    
    # Create a log entry for stop
    echo "$(date): Service stopped" >> $LOG_FILE
}

reload_service() {
    logger -t revd "Memuat ulang layanan Telegram Bot"
    stop
    sleep 2
    start
}

restart() {
    logger -t revd "Memulai ulang layanan Telegram Bot"
    stop
    sleep 3
    start
}
   ```

2. Jadikan skrip init executable:
   ```
   chmod +x /etc/init.d/revd
   ```

3. Salin skrip bot Anda ke /root/revd/ (jika belum ada):
   ```
   mkdir -p /root/revd
   cp bot_openwrt.py /root/revd/
   ```

4. Pastikan Anda memiliki semua plugin yang diperlukan di /root/revd/plugins/:
   ```
   mkdir -p /root/revd/plugins
   cp plugins/*.sh /root/revd/plugins/
   chmod +x /root/revd/plugins/*.sh
   ```

5. Aktifkan dan mulai layanan:
   ```
   /etc/init.d/revd enable
   /etc/init.d/revd start
   ```

## Manajemen Layanan

Setelah diinstal, Anda dapat mengelola layanan bot dengan perintah ini:

- **Mulai bot**: `/etc/init.d/revd start`
- **Hentikan bot**: `/etc/init.d/revd stop`
- **Mulai ulang bot**: `/etc/init.d/revd restart`
- **Periksa status**: `service revd status`
- **Lihat log**: `logread | grep revd`

## Pemecahan Masalah

Jika bot tidak mulai secara otomatis setelah reboot:

1. Periksa apakah layanan diaktifkan:
   ```
   ls -la /etc/rc.d/ | grep revd
   ```
   Anda seharusnya melihat symbolic link seperti `S99revd`.

2. Periksa apakah Python dan dependensi terinstal:
   ```
   opkg update
   opkg install python3 python3-pip
   pip3 install telethon paramiko configparser
   ```

3. Periksa log:
   ```
   logread | grep revd
   ```

4. Periksa kesalahan skrip secara manual:
   ```
   cd /root/revd
   python3 bot_openwrt.py
   ```

## Catatan Keamanan

Ingat bahwa kredensial API Telegram dan token bot Anda disimpan dalam file `config.ini`. Pastikan untuk melindungi file ini dengan izin yang sesuai:

```
chmod 600 /root/revd/config.ini
```

## Kredit

Dibuat oleh REVD.CLOUD
