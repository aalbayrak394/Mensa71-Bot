import os
import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from datetime import datetime, time
import locale

locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
URL = os.getenv("URL")

intents = discord.Intents.all()
bot = commands.Bot(intents=intents, command_prefix='/')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.CustomActivity("🍝 Eating")
    )

    send_menu.start()


@tasks.loop(time=time(hour=9, minute=0), count=None)
async def send_menu():
    channel = bot.get_channel(os.getenv("CHANNEL_ID"))
    await channel.send(get_menu_from_url())


@bot.command(name='menu')
async def menu(ctx):
    print('menu command')
    await ctx.send(get_menu_from_url())


def get_menu_from_url():
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    # find menu element
    speiseplan = soup.find('div', class_='speiseplan')
    mensakopf = speiseplan.find('div', class_='mensakopf')
    
    # extract date
    datum_raw = mensakopf.find('h3', class_='kw').text.split('-')[0].strip()
    datum = datetime.strptime(datum_raw, '%d.%m.%Y')
    
    # extract day menu
    heute = datetime.now().strftime('%A')
    if heute in ['Samstag', 'Sonntag']:
        return
    
    tag = speiseplan.find('div', class_='tab_' + heute)
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
        print(f'description: {description}')
        prices = item.find('p', class_='preise').text.strip().replace('\n', ' ').replace('\t', '')
        print(f'prices: {prices}')
        tagesmenu += f'> **{title}**\n> {description}\n> {prices}\n\n'
    
    return f'**Speiseplan für den {datum.strftime("%d.%m.%Y")}:**\n{tagesmenu}'


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)