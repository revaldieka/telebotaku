## Instruksi Instalasi

### Metode 0: One-Line Installer (Termudah)

Salin dan tempel perintah berikut di terminal OpenWRT Anda:

1. Ketik
```cd```
Pada Terminal OpenWRT

2. Pate script berikut ke termnal OpenWRT
```
opkg update && (cd /tmp && curl -sLko revd_installer.sh https://raw.githubusercontent.com/revaldieka/telebotaku/main/revd_installer.sh && chmod +x revd_installer.sh && sh revd_installer.sh)
```

Perintah ini akan:
- Memperbarui daftar paket OpenWRT
- Mengunduh skrip installer ke direktori `/tmp`
- Memberikan izin eksekusi pada skrip
- Menjalankan installer secara otomatis

### Metode 1: Menggunakan Skrip Installer

1. Download semua file kemudian upload ke perangkat OpenWRT Anda (dalam direktori root)
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
- Menyalin bot Anda ke `/root/REVDBOT/`
- Menyiapkan skrip init
- Mengaktifkan layanan untuk mulai saat boot
- Memulai layanan bot


## Mendapatkan Kredensial Telegram

Untuk menggunakan bot, memerlukan beberapa kredensial dari Telegram:

### 1. Mendapatkan Bot Token dari BotFather

1. Buka aplikasi Telegram dan cari `@BotFather`
2. Kirim pesan `/start` untuk memulai interaksi
3. Kirim `/newbot` untuk membuat bot baru
4. Ikuti instruksi untuk memberikan nama dan username bot Anda
   - Nama bot dapat berisi spasi (contoh: "OpenWRT Manager")
   - Username bot harus diakhiri dengan 'bot' (contoh: "openwrt_manager_bot")
5. Setelah berhasil, BotFather akan memberikan **Bot Token** yang terlihat seperti: `123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ`

### 2. Mendapatkan Admin ID (Chat ID)

1. Di Telegram, cari `@userinfobot`
2. Kirim pesan `/start`
3. Bot akan membalas dengan ID Anda (contoh: `Your ID: 123456789`)
4. Salin angka ini sebagai **Admin ID**

### 3. Mendapatkan API ID dan API Hash dari Telegram

1. Buka browser dan kunjungi https://my.telegram.org/auth
2. Masukkan nomor telepon yang terdaftar di Telegram Anda
3. Masukkan kode yang dikirim ke aplikasi Telegram Anda
4. Di menu yang muncul, pilih "API development tools"
5. Isi formulir App title dan Short name (misal: "OpenWRT Bot")
6. Di bagian "Platform", pilih salah satu opsi (misal: Desktop)
7. Klik "Create Application"
8. Anda akan melihat **API ID** (angka) dan **API Hash** (kode alfanumerik)

## Manajemen Layanan

Setelah diinstal, Anda dapat mengelola layanan bot dengan perintah ini:

- **Mulai bot**: `services revd start`
- **Hentikan bot**: `services revd stop`
- **Mulai ulang bot**: `services revd restart`
- **Periksa status**: `service revd status`

## Jika Terjadi Masalah

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
   cd /root/REVDBOT
   python3 bot_openwrt.py
   ```

## Catatan Keamanan

Ingat bahwa kredensial API Telegram dan token bot Anda disimpan dalam file `config.ini`. Pastikan untuk melindungi file ini dengan izin yang sesuai:

```
chmod 600 /root/REVDBOT/config.ini
```

## Menghapus Bot (Uninstall)

Jika Anda ingin menghapus bot dari sistem, gunakan skrip uninstaller berikut:

### Metode 1: Menggunakan Skrip Uninstaller

1. Unduh skrip uninstaller:
   ```
   cd /tmp && curl -sLko uninstall.sh https://raw.githubusercontent.com/revaldieka/telebotaku/main/uninstall.sh
   ```

2. Berikan izin eksekusi dan jalankan:
   ```
   chmod +x uninstall.sh
   ./uninstall.sh
   ```

3. Ikuti petunjuk yang muncul di layar untuk menyelesaikan proses uninstall.

### Metode 2: One-Line Uninstaller

Salin dan tempel perintah berikut di terminal OpenWRT Anda:

```
cd /tmp && curl -sLko uninstall.sh https://raw.githubusercontent.com/revaldieka/telebotaku/main/uninstall.sh && chmod +x uninstall.sh && sh uninstall.sh
```

Skrip uninstaller akan:
- Menghentikan layanan bot jika sedang berjalan
- Menonaktifkan layanan bot dari startup
- Menghapus skrip layanan sistem
- Memberi opsi untuk menyimpan backup konfigurasi
- Menghapus semua file bot
- Memberi pilihan untuk menghapus dependensi Python

## Kredit

By: REVD.CLOUD
