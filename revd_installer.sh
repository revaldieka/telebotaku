#!/bin/sh

# OpenWRT Telegram Bot Service Installer
# Created by REVD.CLOUD
# Improved version with GitHub repository integration

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
ROOT_DIR="/root/REVDBOT"
PLUGINS_DIR="$ROOT_DIR/plugins"
GITHUB_REPO="https://github.com/revaldieka/telebotaku.git"

# Create root directory if it doesn't exist
if [ ! -d "$ROOT_DIR" ]; then
    echo "📁 Membuat direktori $ROOT_DIR..."
    mkdir -p "$ROOT_DIR"
fi

# Install dependencies
echo "📦 Memeriksa dan menginstal dependensi yang diperlukan..."

# Update package list
echo "Memperbarui daftar paket..."
opkg update

# Install required packages
echo "Menginstal paket pendukung..."
opkg install git python3 python3-pip openssh-sftp-server vnstat

# Install git if not already installed
if ! command -v git >/dev/null 2>&1; then
    echo "Menginstal git..."
    opkg install git
fi

# Install python3 if not already installed
if ! command -v python3 >/dev/null 2>&1; then
    echo "Menginstal Python3..."
    opkg install python3 python3-pip
fi

# Clone the repository
echo "📥 Mengkloning repository dari GitHub..."
if [ -d "$ROOT_DIR/.git" ]; then
    echo "Repository sudah ada, melakukan pull untuk pembaruan..."
    cd "$ROOT_DIR" && git pull
    if [ $? -ne 0 ]; then
        echo "❌ Gagal memperbarui repository. Mencoba clone ulang..."
        rm -rf "$ROOT_DIR"/*
        git clone "$GITHUB_REPO" "$ROOT_DIR"
    fi
else
    git clone "$GITHUB_REPO" "$ROOT_DIR"
    if [ $? -ne 0 ]; then
        echo "❌ Gagal mengkloning repository GitHub."
        echo "Periksa koneksi internet atau ketersediaan repository."
        exit 1
    fi
fi

# Install Python dependencies
echo "📦 Menginstal dependensi Python..."
pip3 install telethon configparser asyncio

# Make sure the plugins directory exists
if [ ! -d "$PLUGINS_DIR" ]; then
    echo "📁 Membuat direktori plugins..."
    mkdir -p "$PLUGINS_DIR"
fi

# Make all scripts in plugins directory executable
if [ -d "$PLUGINS_DIR" ]; then
    echo "🔧 Membuat semua script di direktori plugins dapat dieksekusi..."
    chmod +x "$PLUGINS_DIR"/*.sh 2>/dev/null
    echo "✅ Script plugins siap digunakan"
fi

# Make the main bot script executable
if [ -f "$ROOT_DIR/bot_openwrt.py" ]; then
    chmod +x "$ROOT_DIR/bot_openwrt.py"
    echo "✅ Script bot utama siap digunakan"
else
    echo "⚠️ Script bot utama tidak ditemukan!"
    echo "Pastikan repository GitHub berisi file bot_openwrt.py"
    exit 1
fi

# Download the init script to /etc/init.d
echo "📄 Membuat script init 'revd'..."
cat > "$INIT_SCRIPT" << EOF
#!/bin/sh /etc/rc.common

START=99
USE_PROCD=1
PROG=/usr/bin/python3
SCRIPT_PATH=$ROOT_DIR/bot_openwrt.py

start_service() {
    # Check if script exists
    if [ ! -f "\$SCRIPT_PATH" ]; then
        echo "Skrip bot tidak ditemukan di \$SCRIPT_PATH"
        return 1
    fi
    
    # Check if Python3 is installed
    if [ ! -x "\$PROG" ]; then
        echo "Python3 tidak ditemukan di \$PROG"
        return 1
    fi
    
    # Log starting message
    logger -t revd "Memulai layanan Telegram Bot"
    
    # Configure the service
    procd_open_instance
    procd_set_param command \$PROG \$SCRIPT_PATH
    procd_set_param stderr 1
    procd_set_param stdout 1
    procd_set_param respawn \${respawn_threshold:-3600} \${respawn_timeout:-5} \${respawn_retry:-5}
    procd_close_instance
}

stop_service() {
    # Log stopping message
    logger -t revd "Menghentikan layanan Telegram Bot"
    
    # Find and kill all Python processes running the bot script
    kill -9 \$(ps | grep "\$SCRIPT_PATH" | grep -v grep | awk '{print \$1}') 2>/dev/null
}

reload_service() {
    stop
    start
}
EOF

# Make init script executable
chmod +x "$INIT_SCRIPT"

# Get API credentials from user
echo "📝 Masukkan kredensial API Telegram dan informasi admin:"

# Ask for API ID with validation
while true; do
    read -p "API ID: " api_id
    if [ -n "$api_id" ]; then
        # Validate API ID (should be numeric)
        if echo "$api_id" | grep -q "^[0-9]\+$"; then
            break
        else
            echo "⚠️ API ID harus berupa angka. Silakan coba lagi."
        fi
    else
        echo "⚠️ API ID tidak boleh kosong! Dapatkan dari https://my.telegram.org"
    fi
done

# Ask for API Hash with validation
while true; do
    read -p "API Hash: " api_hash
    if [ -n "$api_hash" ]; then
        # Validate API Hash (should be hexadecimal, 32 chars)
        if echo "$api_hash" | grep -q "^[0-9a-fA-F]\{32\}$"; then
            break
        else
            echo "⚠️ API Hash harus berupa kode hex 32 karakter. Silakan coba lagi."
        fi
    else
        echo "⚠️ API Hash tidak boleh kosong! Dapatkan dari https://my.telegram.org"
    fi
done

# Ask for Bot Token with validation
while true; do
    read -p "Bot Token: " bot_token
    if [ -n "$bot_token" ]; then
        # Validate Bot Token (should contain a colon)
        if echo "$bot_token" | grep -q ":"; then
            break
        else
            echo "⚠️ Bot Token tidak valid. Seharusnya berformat seperti 123456789:ABCDEF1234567890abcdef"
        fi
    else
        echo "⚠️ Bot Token tidak boleh kosong! Dapatkan dari @BotFather"
    fi
done

# Ask for Admin ID with validation
while true; do
    read -p "Admin ID: " admin_id
    if [ -n "$admin_id" ]; then
        # Validate Admin ID (should be numeric)
        if echo "$admin_id" | grep -q "^[0-9]\+$"; then
            break
        else
            echo "⚠️ Admin ID harus berupa angka. Silakan coba lagi."
        fi
    else
        echo "⚠️ Admin ID tidak boleh kosong! Ini adalah ID Telegram Anda."
    fi
done

# Ask for Device Name
read -p "Device Name [default: OpenWRT | REVD.CLOUD]: " device_name
device_name=${device_name:-"OpenWRT | REVD.CLOUD"}

# Create or update config.ini
echo "📝 Membuat config.ini dengan kredensial yang dimasukkan..."
cat > "$ROOT_DIR/config.ini" << EOF
[Telegram]
api_id = $api_id
api_hash = $api_hash
bot_token = $bot_token
admin_id = $admin_id

[OpenWRT]
device_name = $device_name
EOF

echo "✅ File config.ini berhasil dibuat."

# Enable and start service
echo "🔄 Mengaktifkan dan memulai layanan bot..."
/etc/init.d/revd enable
/etc/init.d/revd start

# Check if service started successfully
sleep 2
if pgrep -f "python3.*bot_openwrt.py" > /dev/null; then
    echo "✅ Bot berhasil dijalankan!"
    echo "Bot Telegram sudah aktif dengan nama: $device_name"
    echo "Anda sekarang dapat mengakses bot melalui Telegram."
else
    echo "⚠️ Bot belum berjalan. Coba jalankan manual dengan perintah:"
    echo "   /etc/init.d/revd start"
    echo "   Atau lihat error dengan: python3 $ROOT_DIR/bot_openwrt.py"
fi

# Show final instructions
echo ""
echo "📱 Cara menggunakan bot:"
echo "1. Buka Telegram dan cari bot Anda"
echo "2. Kirim perintah /start untuk memulai"
echo "3. Gunakan menu dan tombol yang tersedia"
echo ""
echo "✅ Instalasi selesai!"
