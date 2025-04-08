from datetime import datetime
import discord
from bs4 import BeautifulSoup
import requests


def get_mensa_status(datetime: datetime) -> int:
    if datetime.weekday() in [5, 6]:
        # Weekend
        return -1
    
    if datetime.hour >= 11 and datetime.minute >= 30:
        # Mensa is open
        return 1
    
    if 8 <= datetime.hour < 15:
        # Café71 is open
        return 0
    
    # Café71 and Mensa71 are closed
    return -1


def get_menu_from_url(url):
    page = requests.get(url)
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
    day_string = tag.find('a').text.strip()

    # no menu on holidays
    if "geschlossen" in tagesmenu_raw[0].text.strip():
        return
    
    # format menu
    embed = discord.Embed(
        title=f'Speiseplan für {day_string}',
        url=url,
        color=0xfec30a
    )

    for idx, item in enumerate(tagesmenu_raw):
        title_raw = item.find('h5').text.split('(')
        title = []
        for title_item in title_raw:
            title.append(title_item.strip())

        title = ' ('.join(title)
        description = item.find('p', class_='essen').find('strong').text.strip()
        prices = item.find('p', class_='preise').text.strip().replace('\n', ' ').replace('\t', '')

        embed.add_field(
            name=f':salad: {title}' if idx == 3 else title,
            value=f'{description}\n{prices}',
            inline=False
        )
        embed.add_field(
            name='\u200b',
            value='',
            inline=False
        )

    embed.set_footer(text='Essensausgabe: 11:30 - 14:00 Uhr')
    return embed