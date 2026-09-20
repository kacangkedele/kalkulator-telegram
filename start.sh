#!/usr/bin/env bash
set -e

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "$BOT_TOKEN" ]; then
  echo "Token bot belum diatur. Buat file .env dan isi BOT_TOKEN=..."
  exit 1
fi

python bot.py
