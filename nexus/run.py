# /sd/nexus/run.py
import argparse
import threading
import asyncio
from web.app import app
from bot.main import run_bot

def start_flask():
    app.run(host="0.0.0.0", port=8000)

def start_bot():
    asyncio.run(run_bot())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Запуск компонентов Nexus")
    parser.add_argument("--flask", action="store_true", help="Запустить только Flask")
    parser.add_argument("--bot", action="store_true", help="Запустить только бота")
    args = parser.parse_args()

    # Запуск всех модулей без флагов
    if not args.flask and not args.bot:
        print("Запуск Flask и Telegram-бота...")
        flask_thread = threading.Thread(target=start_flask, daemon=True)
        flask_thread.start()
        asyncio.run(run_bot())

    # Запуск отдельных модулей
    elif args.flask:
        print("Запуск Flask...")
        start_flask()
    elif args.bot:
        print("Запуск Telegram-бота...")
        start_bot()