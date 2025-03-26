import os
import requests
from dotenv import load_dotenv
from pymongo import MongoClient
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from flask import Flask

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
API_URL = "https://tuongtaccheo.com/logintoken.php"

client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
collection = db["tokens"]

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Telegram đang chạy!"

def add_token(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)
    if len(context.args) == 0:
        update.message.reply_text("Vui lòng nhập token sau lệnh /addtoken")
        return
    token = context.args[0]
    
    if collection.find_one({"user_id": user_id, "token": token}):
        update.message.reply_text("Token này đã tồn tại trong danh sách!")
        return

    collection.insert_one({"user_id": user_id, "token": token})
    count = collection.count_documents({"user_id": user_id})
    update.message.reply_text(f"Đã thêm token! Hiện có {count} token.")

def list_tokens(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)
    tokens = list(collection.find({"user_id": user_id}))
    
    if not tokens:
        update.message.reply_text("Bạn chưa có token nào!")
        return

    response = "Danh sách token của bạn:\n"
    response += "\n".join([f"{i+1}. {t['token']}" for i, t in enumerate(tokens)])
    update.message.reply_text(response)

def remove_token(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)
    if len(context.args) == 0:
        update.message.reply_text("Vui lòng nhập số thứ tự của token cần xóa!")
        return
    
    try:
        index = int(context.args[0]) - 1
        tokens = list(collection.find({"user_id": user_id}))

        if index < 0 or index >= len(tokens):
            update.message.reply_text("Số thứ tự không hợp lệ!")
            return

        removed_token = tokens[index]["token"]
        collection.delete_one({"_id": tokens[index]["_id"]})
        count = collection.count_documents({"user_id": user_id})
        update.message.reply_text(f"Đã xóa token: {removed_token}\nCòn lại {count} token.")
    except ValueError:
        update.message.reply_text("Số thứ tự không hợp lệ!")

def check_balance(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)
    tokens = list(collection.find({"user_id": user_id}))

    if not tokens:
        update.message.reply_text("Bạn chưa có token nào!")
        return
    
    update.message.reply_text("Đang kiểm tra số dư, vui lòng chờ...")
    results = []
    
    for token in tokens:
        result = get_balance(token["token"])
        results.append(result)
    
    update.message.reply_text("Kết quả kiểm tra số dư:\n\n" + "\n".join(results))

def get_balance(token):
    try:
        response = requests.post(API_URL, data={"access_token": token})
        data = response.json()
        if data.get("status") == "success":
            return f"User: {data['data']['user']}\nSố dư: {data['data']['sodu']} VNĐ\n"
        else:
            return "Token lỗi hoặc hết hạn!"
    except Exception:
        return "Lỗi kết nối API!"

def start_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("addtoken", add_token))
    dp.add_handler(CommandHandler("listtoken", list_tokens))
    dp.add_handler(CommandHandler("removetoken", remove_token))
    dp.add_handler(CommandHandler("check", check_balance))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    import threading
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
