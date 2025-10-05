import pandas as pd
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import matplotlib.pyplot as plt
import os

TOKEN = os.getenv("TOKEN")
DATA_FILE = "meals.csv"


def load_data():
    try:
        return pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["date", "food", "calories"])


def save_data(df):
    df.to_csv(DATA_FILE, index=False)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I’m your calorie tracker bot.\n"
        "Send messages like:\n\n🍎 `apple 95`\n🍗 `chicken breast 200`\n\n"
        "Use /summary to see today’s total, or /chart for a weekly view!!"
    )


async def add_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()

    if len(parts) < 2 or not parts[-1].isdigit():
        await update.message.reply_text("Please send in format: `foodname calories` (e.g. banana 105)")
        return

    calories = int(parts[-1])
    food = " ".join(parts[:-1])
    df = load_data()
    df.loc[len(df)] = [datetime.now().strftime("%Y-%m-%d"), food, calories]
    save_data(df)

    await update.message.reply_text(f"✅ Added {food} ({calories} kcal).")


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    total = df[df["date"] == today]["calories"].sum()
    await update.message.reply_text(f"📅 Today’s total: {total} kcal")


async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = load_data()
    if df.empty:
        await update.message.reply_text("No data yet!")
        return

    df["date"] = pd.to_datetime(df["date"])
    weekly = df.groupby("date")["calories"].sum().tail(7)

    plt.figure()
    weekly.plot(kind="bar", title="Last 7 Days Calorie Intake")
    plt.ylabel("Calories")
    plt.tight_layout()
    plt.savefig("chart.png")
    plt.close()

    await update.message.reply_photo(photo=open("chart.png", "rb"))


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("summary", summary))
app.add_handler(CommandHandler("chart", chart))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_food))

if __name__ == "__main__":
    app.run_polling()



import threading
from flask import Flask

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is running!"

def run_bot():
    app.run_polling()

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.start()
    app_flask.run(host="0.0.0.0", port=10000)

