FROM python:3-alpine3.10
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD python -u bot.py
