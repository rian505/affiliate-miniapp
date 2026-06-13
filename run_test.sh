#!/bin/bash
cd /home/ubuntu/affiliate-miniapp
set -a
export TELEGRAM_BOT_TOKEN="$(grep '^TELEGRAM_BOT_TOKEN=' /home/ubuntu/.hermes/.env | head -1 | cut -d= -f2-)"
export TELEGRAM_ALLOWED_USERS="$(grep '^TELEGRAM_ALLOWED_USERS=' /home/ubuntu/.hermes/.env | head -1 | cut -d= -f2-)"
set +a
python3 test_write.py
