# Mensa71 Bot
This discord bot sends the daily menu from Mensa71 of the University of Kassel into a specified channel.

## Usage
If you want to host this bot, you have to create a secret `.env` file with the following variables:

- `DISCORD_TOKEN`: Your own discord application token
- `URL`: The url to the menu site of the Studierendenwerk
- `CHANNEL_ID`: The channel ID where the daily menu should be sent
- `DEBUG_CHANNEL_ID`: The channel ID where debug messages should be sent.
  
Now you can simply start the bot via

```bash
python main.py
````

However, if you want to host it permanently you should build a docker image with the provided Dockerfile:

```bash
docker build -t mensa-bot:0.1 .
docker run mensa-bot:0.1
```

## Have fun!
Feature requests and bug reports are welcome! Just create an issue :)