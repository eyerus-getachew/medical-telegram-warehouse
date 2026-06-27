import asyncio

from src.extractors.telegram_client import create_client


async def main():
    client = create_client()

    await client.start(phone=lambda: input("Enter your phone number: "))

    me = await client.get_me()

    print("\nSuccessfully connected!")
    print(f"Logged in as: {me.first_name}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())