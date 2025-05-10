#!/bin/sh

# OpenWRT Telegram Bot Service Installer
# Created by REVD.CLOUD
# Improved version with complete dependency installation

echo "
╔═══════════════════════════════════╗
║  OpenWRT Telegram Bot Installer   ║
║           REVD.CLOUD              ║
╚═══════════════════════════════════╝
"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "⚠️  Skrip ini memerlukan hak akses root."
    echo "Silakan jalankan dengan 'sudo' atau sebagai root."
    exit 1
fi

# Define paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INIT_SCRIPT="/etc/init.d/revd"
ROOT_DIR="/root/revd"
BOT_SCRIPT="$SCRIPT_DIR/bot_openwrt.py"
PLUGINS_DIR="$SCRIPT_DIR/plugins"
REVD_SCRIPT="$SCRIPT_DIR/revd"

# Check if bot script exists
if [ ! -f "$BOT_SCRIPT" ]; then
    echo "❌ Skrip bot tidak ditemukan di: $BOT_SCRIPT"
    exit 1
fi

# Create root directory if it doesn't exist
if [ ! -d "$ROOT_DIR" ]; then
    echo "📁 Membuat direktori $ROOT_DIR..."
    mkdir -p "$ROOT_DIR"
fi

# Make sure the plugins directory exists
if [ ! -d "$PLUGINS_DIR" ]; then
    echo "📁 Membuat direktori plugins..."
    mkdir -p "$PLUGINS_DIR"
fi

# Make sure the plugins directory exists in ROOT_DIR
if [ ! -d "$ROOT_DIR/plugins" ]; then
    echo "📁 Membuat direktori plugins di $ROOT_DIR..."
    mkdir -p "$ROOT_DIR/plugins"
fi

# Copy all required scripts to plugins directory
for script in speedtest.sh reboot.sh ping.sh clear_ram.sh vnstat.sh system.sh; do
    if [ -f "$SCRIPT_DIR/$script" ]; then
        echo "📄 Menginstal $script ke direktori plugins..."
        cp "$SCRIPT_DIR/$script" "$PLUGINS_DIR/"
        chmod +x "$PLUGINS_DIR/$script"
        
        # Also copy to ROOT_DIR/plugins
        cp "$SCRIPT_DIR/$script" "$ROOT_DIR/plugins/"
        chmod +x "$ROOT_DIR/plugins/$script"
    else
        echo "⚠️  Script tidak ditemukan: $script"
    fi
done

# Install system dependencies
echo "📦 Memeriksa dan menginstal dependensi sistem..."
echo "Memperbarui repositori paket..."
opkg update

echo "Menginstal Python3 dan paket pendukung..."
opkg install python3 python3-pip

echo "Menginstal utilitas jaringan dan monitoring..."
opkg install speedtest-cli curl

# Install Python dependencies using pip
echo "📦 Menginstal paket Python dengan pip..."
pip3 install telethon configparser speedtest-cli
# Removed paramiko since it's no longer needed

# Test speedtest-cli
echo "🚀 Menjalankan speedtest-cli untuk verifikasi instalasi..."
speedtest-cli --simple >/dev/null 2>&1 &

# Check if revd script exists in source directory and copy it
if [ -f "$REVD_SCRIPT" ]; then
    echo "📄 Menyalin skrip init 'revd' dari folder sumber ke /etc/init.d/..."
    cp "$REVD_SCRIPT" "$INIT_SCRIPT"
    chmod +x "$INIT_SCRIPT"
    echo "✅ Skrip init berhasil disalin dan dibuat executable"
else
    echo "⚠️  Skrip init 'revd' tidak ditemukan di direktori sumber."
    echo "📝 Membuat skrip init baru..."
    
    # Create init script
    cat > "$INIT_SCRIPT" << 'EOF'
#!/bin/sh /etc/rc.common

START=99
USE_PROCD=1
PROG=/usr/bin/python3
SCRIPT_PATH=/root/revd/bot_openwrt.py

start_service() {
    # Check if script exists
    if [ ! -f "$SCRIPT_PATH" ]; then
        echo "Skrip bot tidak ditemukan di $SCRIPT_PATH"
        return 1
    fi
    
    # Check if Python3 is installed
    if [ ! -x "$PROG" ]; then
        echo "Python3 tidak ditemukan di $PROG"
        return 1
    fi
    
    # Log starting message
    logger -t revd "Memulai layanan Telegram Bot"
    
    # Configure the service
    procd_open_instance
    procd_set_param command $PROG $SCRIPT_PATH
    procd_set_param stderr 1
    procd_set_param stdout 1
    procd_set_param respawn ${respawn_threshold:-3600} ${respawn_timeout:-5} ${respawn_retry:-5}
    procd_close_instance
}

stop_service() {
    # Log stopping message
    logger -t revd "Menghentikan layanan Telegram Bot"
    
    # Find and kill all Python processes running the bot script
    kill -9 $(ps | grep "$SCRIPT_PATH" | grep -v grep | awk '{print $1}') 2>/dev/null
}

reload_service() {
    stop
    start
}
EOF

    # Make init script executable
    chmod +x "$INIT_SCRIPT"
fi

# Copy bot script to ROOT_DIR
echo "📄 Menyalin skrip bot ke $ROOT_DIR/..."
cp "$BOT_SCRIPT" "$ROOT_DIR/"
chmod +x "$ROOT_DIR/bot_openwrt.py"

# Copy config.ini if it exists
if [ -f "$SCRIPT_DIR/config.ini" ]; then
    echo "📄 Menyalin config.ini ke $ROOT_DIR/..."
    cp "$SCRIPT_DIR/config.ini" "$ROOT_DIR/"
    chmod 600 "$ROOT_DIR/config.ini"
else
    # Create a default config.ini if it doesn't exist
    echo "📝 Membuat config.ini default..."
    cat > "$ROOT_DIR/config.ini" << 'EOF'
[Telegram]
api_id = 25188016
api_hash = 31d1351ef7b53bc85fd6ec96a9db397a
bot_token = 6533113920:AAGbuDyx9OPzfF0qSL-GTsGiHc4et6QyArs
admin_id = 866930833

[OpenWRT]
host = 192.168.1.1
username = root
password = 990701xx
device_name = OpenWRT | REVD.CLOUD
EOF
    chmod 600 "$ROOT_DIR/config.ini"
fi

# Run speedtest once to initialize
echo "🚀 Menjalankan speedtest-cli untuk inisialisasi..."
speedtest-cli --simple >/dev/null 2>&1 &

# Initialize vnstat database if possible
if command -v vnstat >/dev/null 2>&1; then
    echo "📊 Menginisialisasi database vnstat..."
    MAIN_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n 1)
    if [ -n "$MAIN_INTERFACE" ]; then
        vnstat -i "$MAIN_INTERFACE" --create >/dev/null 2>&1
    fi
fi

# Enable and start the service
echo "🚀 Mengaktifkan dan memulai layanan bot..."
"$INIT_SCRIPT" enable
"$INIT_SCRIPT" start

echo "
✅ Instalasi Selesai!

Bot Telegram Anda telah diinstal sebagai layanan sistem
dan akan otomatis dimulai saat boot.

Nama layanan: revd
Lokasi bot: $ROOT_DIR/bot_openwrt.py
Skrip init: $INIT_SCRIPT

Perintah:
 - Mulai:   /etc/init.d/revd start
 - Berhenti: /etc/init.d/revd stop
 - Restart:  /etc/init.d/revd restart
 - Status:   service revd status
"

# Check if service is running
if pgrep -f "python3 $ROOT_DIR/bot_openwrt.py" > /dev/null; then
    echo "✅ Bot sedang berjalan!"
else
    echo "⚠️  Bot tidak berjalan. Periksa log dengan: logread | grep revd"
    echo "Mencoba memulai ulang layanan..."
    "$INIT_SCRIPT" restart
    sleep 3
    
    # Check again
    if pgrep -f "python3 $ROOT_DIR/bot_openwrt.py" > /dev/null; then
        echo "✅ Bot berhasil dimulai setelah percobaan ulang!"
    else
        echo "❌ Bot masih tidak berjalan. Periksa log untuk detail lebih lanjut."
    fi
fi

echo "
By REVD.CLOUD
"