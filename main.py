import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = "https://tuongtaccheo.com/logintoken.php"
TOKEN_FOLDER = "tokens"

if not os.path.exists(TOKEN_FOLDER):
    os.makedirs(TOKEN_FOLDER)

def get_token_file(user_id):
    return os.path.join(TOKEN_FOLDER, f"{user_id}.txt")

def read_tokens(user_id):
    file_path = get_token_file(user_id)
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def write_tokens(user_id, tokens):
    file_path = get_token_file(user_id)
    with open(file_path, "w") as f:
        f.write("\n".join(tokens))

def add_token(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if len(context.args) == 0:
        update.message.reply_text("⚠️ Vui lòng nhập token sau lệnh /addtoken")
        return
    token = context.args[0]
    tokens = read_tokens(user_id)
    if token in tokens:
        update.message.reply_text("⚠️ Token này đã tồn tại trong danh sách!")
        return
    tokens.append(token)
    write_tokens(user_id, tokens)
    update.message.reply_text(f"✅ Đã thêm token! Hiện có {len(tokens)} token.")

def list_tokens(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    tokens = read_tokens(user_id)
    if not tokens:
        update.message.reply_text("⚠️ Bạn chưa có token nào!")
        return
    response = "📜 Danh sách token của bạn:\n"
    response += "\n".join([f"{i+1}. {token}" for i, token in enumerate(tokens)])
    update.message.reply_text(response)

def remove_token(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if len(context.args) == 0:
        update.message.reply_text("⚠️ Vui lòng nhập số thứ tự của token cần xóa!")
        return
    try:
        index = int(context.args[0]) - 1
        tokens = read_tokens(user_id)
        if index < 0 or index >= len(tokens):
            update.message.reply_text("⚠️ Số thứ tự không hợp lệ!")
            return
        removed_token = tokens.pop(index)
        write_tokens(user_id, tokens)
        update.message.reply_text(f"🗑️ Đã xóa token: {removed_token}\n📌 Còn lại {len(tokens)} token.")
    except ValueError:
        update.message.reply_text("⚠️ Số thứ tự không hợp lệ!")

def check_balance(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    tokens = read_tokens(user_id)
    if not tokens:
        update.message.reply_text("⚠️ Bạn chưa có token nào!")
        return
    update.message.reply_text("🔄 Đang kiểm tra số dư, vui lòng chờ...")
    results = []
    for token in tokens:
        result = get_balance(token)
        results.append(result)
    update.message.reply_text(f"📊 Kết quả kiểm tra số dư:\n\n" + "\n".join(results))

def get_balance(token):
    try:
        response = requests.post(API_URL, data={"access_token": token})
        data = response.json()
        if data.get("status") == "success":
            return f"🔹 User: {data['data']['user']}\n💰 Số dư: {data['data']['sodu']} VNĐ\n"
        else:
            return "❌ Token lỗi hoặc hết hạn!"
    except Exception:
        return "⚠️ Lỗi kết nối API!"

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("addtoken", add_token))
    dp.add_handler(CommandHandler("listtoken", list_tokens))
    dp.add_handler(CommandHandler("removetoken", remove_token))
    dp.add_handler(CommandHandler("check", check_balance))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
