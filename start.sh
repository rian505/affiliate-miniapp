#!/bin/bash
# Start the affiliate mini app server with env loaded from hermes .env
cd /home/ubuntu/affiliate-miniapp
set -a
# Load only the telegram vars we need (skip comments)
export TELEGRAM_BOT_TOKEN=$(grep -E "^TELEGRAM_BOT_TOKEN=" /home/ubuntu/.hermes/.env | head -1 | cut -d= -f2-)
export TELEGRAM_ALLOWED_USERS=$(grep -E "^TELEGRAM_ALLOWED_USERS=" /home/ubuntu/.hermes/.env | head -1 | cut -d= -f2-)
set +a
exec python3 -m uvicorn app:app --host 127.0.0.1 --port 8088
