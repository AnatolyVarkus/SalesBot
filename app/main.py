from app.bot import bot_handler
import asyncio

async def main():
    await bot_handler.client.start()
    asyncio.create_task(bot_handler.monitor_exits())
    await bot_handler.process_unanswered_messages()
    print("Bot started...")
    await bot_handler.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())