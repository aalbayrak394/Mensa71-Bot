FROM python:3.12-slim

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot

COPY . .

RUN apt-get update
RUN apt-get install -y locales
RUN sed -i -e 's/# de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen \
 && locale-gen

RUN pip install -r requirements.txt
ENV TZ=Europe/Berlin

CMD [ "python3", "-u", "main.py" ]