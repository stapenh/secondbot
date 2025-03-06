FROM python:3.9-slim

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
COPY . /app
WORKDIR /app/bot


CMD ["python", "-m", "bot.app"]