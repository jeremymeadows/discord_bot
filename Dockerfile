FROM python:3.11-alpine

WORKDIR /app

RUN pip install discord.py python-dotenv pytz

COPY ./bot.py .
ADD modules/*.py modules/

CMD ["python", "./bot.py"]
