#!/bin/bash
cd /opt/data/telegram-digital-store
nohup /opt/data/telegram-digital-store/.venv/bin/python bot.py > bot.log 2>&1 &
echo "Digital Jahan Bot started with PID $!"
