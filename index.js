require("dotenv").config();
const { Telegraf } = require("telegraf");
const mongoose = require("mongoose");
const axios = require("axios");
const express = require("express");

const bot = new Telegraf(process.env.BOT_TOKEN);
const API_URL = "https://tuongtaccheo.com/logintoken.php";

// Kết nối MongoDB
mongoose.connect(process.env.MONGO_URI, { useNewUrlParser: true, useUnifiedTopology: true });

const tokenSchema = new mongoose.Schema({
  userId: String,
  token: String,
});

const Token = mongoose.model("Token", tokenSchema);

// Route web để giữ bot chạy trên Render
const app = express();
app.get("/", (req, res) => res.send("Bot đang chạy!"));
app.listen(process.env.PORT || 8080, () => console.log("Server đang chạy..."));

// Thêm token
bot.command("addtoken", async (ctx) => {
  const userId = ctx.chat.id.toString();
  const token = ctx.message.text.split(" ")[1];

  if (!token) return ctx.reply("⚠️ Vui lòng nhập token sau lệnh /addtoken");

  const exists = await Token.findOne({ userId, token });
  if (exists) return ctx.reply("⚠️ Token này đã tồn tại!");

  await Token.create({ userId, token });
  const count = await Token.countDocuments({ userId });
  ctx.reply(`✅ Đã thêm token! Hiện có ${count} token.`);
});

// Xem danh sách token
bot.command("listtoken", async (ctx) => {
  const userId = ctx.chat.id.toString();
  const tokens = await Token.find({ userId });

  if (!tokens.length) return ctx.reply("⚠️ Bạn chưa có token nào!");

  let response = "📜 Danh sách token của bạn:\n";
  response += tokens.map((t, i) => `${i + 1}. ${t.token}`).join("\n");
  ctx.reply(response);
});

// Xóa token theo số thứ tự
bot.command("removetoken", async (ctx) => {
  const userId = ctx.chat.id.toString();
  const index = parseInt(ctx.message.text.split(" ")[1]) - 1;

  if (isNaN(index)) return ctx.reply("⚠️ Vui lòng nhập số thứ tự hợp lệ!");

  const tokens = await Token.find({ userId });
  if (index < 0 || index >= tokens.length) return ctx.reply("⚠️ Số thứ tự không hợp lệ!");

  await Token.deleteOne({ _id: tokens[index]._id });
  const count = await Token.countDocuments({ userId });
  ctx.reply(`🗑️ Đã xóa token! Còn lại ${count} token.`);
});

// Kiểm tra số dư
bot.command("check", async (ctx) => {
  const userId = ctx.chat.id.toString();
  const tokens = await Token.find({ userId });

  if (!tokens.length) return ctx.reply("⚠️ Bạn chưa có token nào!");

  ctx.reply("🔄 Đang kiểm tra số dư, vui lòng chờ...");
  
  let results = [];
  for (let t of tokens) {
    const res = await axios.post(API_URL, new URLSearchParams({ access_token: t.token }));
    const data = res.data;
    if (data.status === "success") {
      results.push(`🔹 User: ${data.data.user}\n💰 Số dư: ${data.data.sodu} coin\n`);
    } else {
      results.push("❌ Token lỗi hoặc hết hạn!");
    }
  }

  ctx.reply("📊 Kết quả kiểm tra số dư:\n\n" + results.join("\n"));
});

// Khởi chạy bot
bot.launch();
