import os
from dotenv import load_dotenv
import schedule
import telebot
from threading import Thread
from time import sleep
import requests
from pymongo import MongoClient

load_dotenv()

API_KEY = os.getenv('API_KEY')
URL = os.getenv('URL')

bot = telebot.TeleBot(API_KEY)

# Set up the connection to MongoDB
MONGO_URI = os.getenv('MONGO_URI')
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.get_database("WSI")
subscribed_users_collection = db.get_collection("subscribers")


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
    print('sending daily report initialized')
    print('error value: ',error)
    subscribed_users = subscribed_users_collection.find({"subscribed": True})
    counter = 0
    for user_id in subscribed_users:
        if not error:
            bot.send_message(user_id, report)
        else:
            bot.send_message(
                user_id, "Sorry, an error occurred when calling the server. We can't show the daily report today :(")
        counter = counter + 1
        if counter % 5 == 0:
            sleep(5)
    print('done sending report')

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = 'unknown'
    if message.from_user.username:
        username = message.from_user.username
    print(f'/start message received from user_id: {user_id} username: {username}')
    subscribed_users_collection.update_one(
        {"user_id": user_id, "username": username}, {"$set": {"subscribed": True}}, upsert=True)
    bot.send_message(
        user_id, "You have subscribed to the daily report! Send /stop to unsubscribe.")
    print(f'/start successfully handled user_id: {user_id} username: {username}')

@bot.message_handler(commands=['send'])
def send(message):
    user_id = message.from_user.id
    username = 'unknown'
    if message.from_user.username:
        username = message.from_user.username
    print(f'/send message received from user_id: {user_id} username: {username}')
    bot.send_message(
        user_id, "Loading the report. This can take a few minutes...")
    report, error = get_report()
    if error:
        bot.send_message(
            user_id, "Sorry, an error occurred when loading the report")
    else:
        bot.send_message(user_id, report)
    print(f'/send message handled for user_id: {user_id} username: {username}')

@bot.message_handler(commands=['stop'])
def stop(message):
    user_id = message.from_user.id
    username = 'unknown'
    if message.from_user.username:
        username = message.from_user.username
    print(f'/stop message received from user_id: {user_id} username: {username}')
    subscribed_users_collection.delete_one({"user_id": user_id})
    bot.send_message(user_id, "You have unsubscribed from the daily report. Send /start to subscribe again.")
    print(f'/stop message handled for user_id: {user_id} username: {username}')

if __name__ == "__main__":
    # Create the job in schedule.
    schedule.every().day.at("00:00").do(send_daily_report)  # 09:00 for MSK

    # Spin up a thread to run the schedule check so it doesn't block your bot.
    # This will take the function schedule_checker which will check every minute
    # to see if the scheduled job needs to be ran.
    Thread(target=schedule_checker).start()

    bot.infinity_polling()
