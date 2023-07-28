import os
from dotenv import load_dotenv
import schedule
import telebot
from threading import Thread
from time import sleep

load_dotenv()

API_KEY = os.getenv('API_KEY')

bot = telebot.TeleBot(API_KEY)

# Dictionary to keep track of users who activated the newsletter
subscribed_users = {}

def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(60)

def send_daily_report():
    for user_id in subscribed_users:
        bot.send_message(user_id, "The report")

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    subscribed_users[user_id] = True
    bot.send_message(user_id, "You have subscribed to the daily report! Send /stop to unsubscibe.")

@bot.message_handler(commands=['stop'])
def stop(message):
    user_id = message.from_user.id
    if user_id in subscribed_users:
        subscribed_users.pop(user_id)
        bot.send_message(user_id, "You have unsubscribed from the daily report.")
    else:
        bot.send_message(user_id, "You are not subscribed to the daily report.")

if __name__ == "__main__":
    # Create the job in schedule.
    schedule.every().day.at("09:00").do(send_daily_report)

    # Spin up a thread to run the schedule check so it doesn't block your bot.
    # This will take the function schedule_checker which will check every minute
    # to see if the scheduled job needs to be ran.
    Thread(target=schedule_checker).start() 

    bot.polling()
