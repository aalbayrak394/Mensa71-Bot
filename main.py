import os, locale
from dotenv import load_dotenv
from datetime import datetime, time, timedelta

import discord
from discord.ext import tasks
from discord import app_commands

from utils import get_mensa_status, get_menu_from_url


### Configs & Constants
locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
local_tz = datetime.now().astimezone().tzinfo
print(f'local timezone: {local_tz}')

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
URL = os.getenv("URL")

bot = discord.Client(command_prefix='!', intents=discord.Intents.all())
tree = app_commands.CommandTree(bot)

checking_times = [
    time(hour=8, minute=0, tzinfo=local_tz),
    time(hour=11, minute=30, tzinfo=local_tz),
    time(hour=14, minute=0, tzinfo=local_tz),
    time(hour=15, minute=0, tzinfo=local_tz)
]

STATUS_CLOSED = 'Closed'
STATUS_SERVING = '🍝 Eating'
STATUS_CAFE = '☕️ @ Café71'


### Bot events
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

    try:
        synced = await tree.sync()
        print(f'Synced {len(synced)} commands.')
    except Exception as e:
        print(f'Error syncing commands: {e}')
    
    if not send_menu.is_running():
        send_menu.start()

    if not check_mensa_status.is_running():
        check_mensa_status.start()

    if not log.is_running():
        log.start()

    if not clear_log_history.is_running():
        clear_log_history.start()


@tasks.loop(hours=6, count=None)
async def clear_log_history():
    channel = bot.get_channel(int(os.getenv("DEBUG_CHANNEL_ID")))
    log_messages = [
        message async for message in channel.history(before=datetime.now() - timedelta(hours=24))
    ]
    await channel.delete_messages(log_messages)
    print('Cleared log history.')


@tasks.loop(time=checking_times, count=None)
async def check_mensa_status():
    status = get_mensa_status(datetime.now())
    if status == -1:
       await bot.change_presence(
            status=discord.Status.do_not_disturb,
            activity=discord.CustomActivity(STATUS_CLOSED)
        )
    elif status == 0:
        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.CustomActivity(STATUS_CAFE)
        )
    elif status == 1:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.CustomActivity(STATUS_SERVING)
        )


@tasks.loop(time=time(hour=9, minute=0, tzinfo=local_tz), count=None)
async def send_menu():
    print('Sending menu...')
    channel = bot.get_channel(int(os.getenv("CHANNEL_ID")))

    # send menu for today
    menu = get_menu_from_url(URL)
    if menu:
        msg = await channel.send(embed=menu)
        await msg.publish()


@tasks.loop(minutes=10, count=None)
async def log():
    channel = bot.get_channel(int(os.getenv("DEBUG_CHANNEL_ID")))
    now = datetime.now().time()
    if now.minute == 0:
        menu = get_menu_from_url(URL)
        if menu:
            await channel.send(embed=menu)
        else:
            await channel.send('Kein Menü verfügbar.')
    else:
        await channel.send(f'`{now.strftime("%H:%M:%S")}: client UP`')


@tree.command(name='hello', description='Say hello')
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message('Hello, World!')


@tree.command(name='menu', description='Get the menu for today')
async def menu(interaction: discord.Interaction):
    menu = get_menu_from_url(URL)
    if menu:
        await interaction.response.send_message(embed=menu)
    else:
        await interaction.response.send_message('Die Mensa hat heute geschlossen.')


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
