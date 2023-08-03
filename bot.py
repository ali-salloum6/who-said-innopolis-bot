import os
from dotenv import load_dotenv
import schedule
import telebot
from threading import Thread
from time import sleep
import requests

load_dotenv()

API_KEY = os.getenv('API_KEY')
URL = os.getenv('URL')

bot = telebot.TeleBot(API_KEY)

# Dictionary to keep track of users who activated the newsletter
subscribed_users = {}

def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(60)

def get_report():
    report = ""
    error = False
    try:
        response = requests.get(URL)

        # Check if the request was successful (status code 200 indicates success)
        if response.status_code == 200:
            # You can access the response content as text
            report = response.text
        else:
            error = True
            print(f"Request failed with status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        error = False
        print(f"An error occurred: {e}")

    return report, error

def send_daily_report():
    report, error = get_report()

    for user_id in subscribed_users:
        if not error:
            bot.send_message(user_id, report)
        else:
            bot.send_message(user_id, "Sorry, an error occurred when calling the server. We can't show the daily report today :(")

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    subscribed_users[user_id] = True
    bot.send_message(user_id, "You have subscribed to the daily report! Send /stop to unsubscibe.")

@bot.message_handler(commands=['send'])
def send(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "Loading the report...")
    report, error = get_report()
    if error:
        bot.send_message(user_id, "Sorry, an error occurred when loading the report")
    else:
        bot.send_message(user_id, report)

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

    bot.infinity_polling()
