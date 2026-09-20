# Kalkulator Telegram

Bot kalkulator Telegram dengan inline keyboard, dibuat menggunakan Python dan `python-telegram-bot`. Kode ini aman untuk dijalankan di Termux dan tidak menyimpan token bot di dalam source code.

## Instalasi di Termux

```bash
pkg update && pkg upgrade -y
pkg install python -y
pip install -r requirements.txt
```

Atur token dari [@BotFather](https://t.me/BotFather) sebagai environment variable:

```bash
export BOT_TOKEN="TOKEN_BOT_TELEGRAM_KAMU"
python bot.py
```

Kirim `/start` atau `/kalkulator` kepada bot.

## Menjalankan di background

```bash
export BOT_TOKEN="TOKEN_BOT_TELEGRAM_KAMU"
nohup python bot.py > output.log 2>&1 &
tail -f output.log
```

Untuk menghentikannya:

```bash
pkill -f "python bot.py"
```

## Fitur

- Tombol angka, operasi `+`, `−`, `×`, `÷`, kurung, desimal, dan hasil.
- Tombol `C` untuk menghapus semua dan `DEL` untuk menghapus satu karakter.
- Evaluasi matematika menggunakan parser AST terbatas, bukan `eval()` bebas.
- Token dibaca dari `BOT_TOKEN`, sehingga tidak perlu ditulis di repository.
