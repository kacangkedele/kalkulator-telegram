# Kalkulator Telegram Interaktif

Bot kalkulator Telegram dengan keyboard inline, dibuat menggunakan Python dan `python-telegram-bot` versi 20+. Bot ini sudah disesuaikan agar ringan dan mudah dijalankan di Termux.

## Fitur

- Tombol angka dan operator matematika
- `C` untuk reset
- `DEL` untuk menghapus karakter terakhir
- `=` untuk menghitung hasil
- Dukungan ekspresi seperti `(12+3)*4`, `8/2`, `10-2.5`
- Aman dari eksekusi kode Python dengan parser AST terbatas
- Token bot diambil dari environment variable atau file `.env`

## Persiapan di Termux

```bash
pkg update && pkg upgrade -y
pkg install python -y

mkdir tg-kalkulator && cd tg-kalkulator
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Konfigurasi token bot

Buat file `.env` dari contoh:

```bash
cp .env.example .env
nano .env
```

Isi token dari @BotFather:

```bash
BOT_TOKEN=TOKEN_BOT_TELEGRAM_KAMU
```

## Menjalankan bot

### Mode langsung

```bash
source .venv/bin/activate
python bot.py
```

### Mode background (Termux)

```bash
source .venv/bin/activate
nohup python bot.py > output.log 2>&1 &
```

Cek log:

```bash
tail -f output.log
```

## Perintah bot

- `/start` — memulai kalkulator
- `/kalkulator` — membuka kalkulator
- `/help` — menampilkan panduan

## Catatan keamanan

- Jangan pernah mengunggah token bot ke GitHub.
- Simpan token di `.env` dan pastikan file `.env` masuk ke `.gitignore`.
