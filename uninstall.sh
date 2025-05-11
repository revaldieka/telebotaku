#!/bin/sh

# OpenWRT Telegram Bot Uninstaller
# Created for REVD.CLOUD

echo "
╔═══════════════════════════════════╗
║  OpenWRT Telegram Bot Uninstaller ║
║            REVD.CLOUD             ║
╚═══════════════════════════════════╝
"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "⚠️  Skrip ini memerlukan hak akses root."
    echo "Silakan jalankan dengan 'sudo' atau sebagai root."
    exit 1
fi

# Define paths
INIT_SCRIPT="/etc/init.d/revd"
ROOT_DIR="/root/REVDBOT"
SERVICE_NAME="revd"
BACKUP_DIR="/etc/revd_backup"
LOG_FILE="/var/log/revd_bot.log"

echo "🔍 Memeriksa instalasi Bot Telegram..."

# Check if service exists
if [ ! -f "$INIT_SCRIPT" ]; then
    echo "❌ Layanan bot tidak ditemukan di sistem."
    echo "Sepertinya bot tidak pernah diinstal atau sudah dihapus."
    
    # Still check for remnant directories just in case
    if [ -d "$ROOT_DIR" ]; then
        echo "📁 Namun direktori bot ditemukan. Lanjutkan penghapusan..."
    else
        echo "📁 Mencari sisa-sisa instalasi..."
    fi
else
    echo "✅ Layanan bot ditemukan di sistem."
fi

# Get the keep_config parameter
keep_config=$1

echo "🛑 Menghentikan layanan bot..."
if [ -f "$INIT_SCRIPT" ]; then
    # Stop the service
    $INIT_SCRIPT stop
    
    # Disable the service
    $INIT_SCRIPT disable
    
    echo "🗑️  Menghapus skrip init..."
    # Remove the init script
    rm -f "$INIT_SCRIPT"
else
    echo "ℹ️  Layanan tidak ditemukan, lanjut ke langkah berikutnya."
fi

# Kill any remaining bot processes
echo "🔍 Mencari dan menghentikan proses bot yang masih berjalan..."
BOT_PIDS=$(ps | grep "bot_openwrt.py" | grep -v grep | awk '{print $1}')
if [ -n "$BOT_PIDS" ]; then
    echo "🛑 Menghentikan proses bot dengan PID: $BOT_PIDS"
    kill -9 $BOT_PIDS 2>/dev/null
else
    echo "ℹ️  Tidak ada proses bot yang berjalan."
fi

# Handle configuration based on parameter
if [ "$keep_config" = "y" ]; then
    # Create backup directory if it doesn't exist
    if [ ! -d "/etc/revd_backup" ]; then
        mkdir -p "/etc/revd_backup"
    fi
    
    # Backup configuration
    if [ -f "$ROOT_DIR/config.ini" ]; then
        echo "💾 Menyimpan backup konfigurasi ke /etc/revd_backup/config.ini"
        cp "$ROOT_DIR/config.ini" "/etc/revd_backup/config.ini"
        chmod 600 "/etc/revd_backup/config.ini"
    fi
    
    # Backup plugins
    if [ -d "$ROOT_DIR/plugins" ]; then
        echo "💾 Menyimpan backup plugin ke /etc/revd_backup/plugins/"
        mkdir -p "/etc/revd_backup/plugins"
        cp -r "$ROOT_DIR/plugins/"* "/etc/revd_backup/plugins/" 2>/dev/null
        chmod +x "/etc/revd_backup/plugins/"*.sh 2>/dev/null
    fi
    
    echo "✅ Backup selesai."
else
    # Remove backup directory if it exists
    if [ -d "$BACKUP_DIR" ]; then
        echo "🗑️  Menghapus direktori backup..."
        rm -rf "$BACKUP_DIR"
    fi
fi

# Remove bot directory
echo "🗑️  Menghapus direktori bot di $ROOT_DIR..."
if [ -d "$ROOT_DIR" ]; then
    rm -rf "$ROOT_DIR"
    echo "✅ Direktori bot berhasil dihapus."
else
    echo "ℹ️  Direktori bot tidak ditemukan."
fi

# Remove log file
if [ -f "$LOG_FILE" ]; then
    echo "🗑️  Menghapus file log..."
    rm -f "$LOG_FILE"
fi

# Remove startup symlink if exists
STARTUP_LINK="/etc/rc.d/S99$SERVICE_NAME"
if [ -L "$STARTUP_LINK" ]; then
    echo "🗑️  Menghapus symlink startup..."
    rm -f "$STARTUP_LINK"
fi

# Clean up any remaining rc.d entries
for RCLINK in /etc/rc.d/*$SERVICE_NAME; do
    if [ -L "$RCLINK" ]; then
        echo "🗑️  Menghapus symlink $RCLINK..."
        rm -f "$RCLINK"
    fi
done

# Skip Python dependencies removal
echo "ℹ️ Dependensi Python (telethon, configparser, paramiko) tidak dihapus."

echo ""
echo "✅ Uninstall selesai!"
echo ""
echo "🚀 Terima kasih telah menggunakan layanan REVD.CLOUD"
echo "    Jika Anda ingin menginstal kembali di masa mendatang, gunakan:"
echo "    opkg update && (cd /tmp && curl -sLko revd_installer.sh https://raw.githubusercontent.com/revaldieka/telebotaku/main/revd_installer.sh && chmod +x revd_installer.sh && sh revd_installer.sh)"
