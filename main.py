import os, locale
from dotenv import load_dotenv
from datetime import datetime, time, timedelta

import discord
from discord.ext import tasks, commands
import requests
from bs4 import BeautifulSoup

from utils import get_mensa_status

### configs
locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
local_tz = datetime.now().astimezone().tzinfo
print(f'local timezone: {local_tz}')

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
URL = os.getenv("URL")

intents = discord.Intents.all()
bot = commands.Bot(intents=intents, command_prefix='/')
awake = True

checking_times = [
    time(hour=8, minute=0, tzinfo=local_tz),
    time(hour=11, minute=30, tzinfo=local_tz),
    time(hour=14, minute=0, tzinfo=local_tz),
    time(hour=15, minute=0, tzinfo=local_tz)
]

STATUS_CLOSED = 'Closed. Reopening at 11:30.'
STATUS_SERVING = '🍝 Eating'
STATUS_CAFE = '☕️ @ Café71'


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    
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
    menu = get_menu_from_url()
    if menu:
        await channel.send(menu)


@tasks.loop(minutes=10, count=None)
async def log():
    channel = bot.get_channel(int(os.getenv("DEBUG_CHANNEL_ID")))
    now = datetime.now().time()
    if now.minute == 0:
        menu = get_menu_from_url()
        if menu:
            await channel.send(menu)
        else:
            await channel.send('Kein Menü verfügbar.')
    else:
        await channel.send(f'`{now.strftime("%H:%M:%S")}: client UP`')


@bot.command(name='menu')
@commands.is_owner()
async def menu(ctx):
    menu = get_menu_from_url()
    if menu:
        await ctx.send(menu)
    else:
        await ctx.send('Die Mensa hat heute geschlossen.')


@bot.command(name='sleep')
@commands.is_owner()
async def sleep(ctx):
    if awake:
        send_menu.stop()
        awake = False
        await ctx.send('Bot is now sleeping.')


@bot.command(name='wake')
@commands.is_owner()
async def wake(ctx):
    if not awake:
        send_menu.start()
        awake = True
        await ctx.send('Bot is now awake.')


@bot.command(name='status')
@commands.is_owner()
async def status(ctx):
    await ctx.send(f'Bot is {"awake" if awake else "sleeping"}.')


def get_menu_from_url():
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    # find menu element
    speiseplan = soup.find('div', class_='speiseplan')
    
    heute = datetime.now()
    wochentag = heute.strftime('%A')
    
    # extract day menu
    if heute.weekday() in [5, 6]:
        # no menu on weekends
        return
    
    tag = speiseplan.find('div', class_='tab_' + wochentag)
    tagesmenu_raw = tag.find('ul').find_all('li')
    
    # format menu
    tagesmenu = ''
    for item in tagesmenu_raw:
        title_raw = item.find('h5').text.split('(')
        title = []
        for title_item in title_raw:
            title.append(title_item.strip())

        title = ' ('.join(title)
        description = item.find('p', class_='essen').find('strong').text.strip()
        prices = item.find('p', class_='preise').text.strip().replace('\n', ' ').replace('\t', '')
        tagesmenu += f'> **{title}**\n> {description}\n> {prices}\n\n'
    
    return f'**Speiseplan für den {heute.strftime("%d.%m.%Y")}:**\n{tagesmenu}'


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)