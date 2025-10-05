import pandas as pd
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import matplotlib.pyplot as plt
import os

FOODS_FILE = "foods.csv"

if not os.path.exists(FOODS_FILE):
    pd.DataFrame(columns=["name", "protein", "fat", "carb", "calories"]).to_csv(FOODS_FILE, index=False)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to CalorieTrackerBot! Use /setfood and /log to begin.")


async def setfood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) != 5:
            await update.message.reply_text("Usage: /setfood name protein fat carb calories")
            return

        name, protein, fat, carb, calories = args
        df = pd.read_csv(FOODS_FILE)

        df = df[df['name'] != name]  # overwrite existing
        df = pd.concat([
            df,
            pd.DataFrame([{
                "name": name.lower(),
                "protein": float(protein),
                "fat": float(fat),
                "carb": float(carb),
                "calories": float(calories)
            }])
        ])
        df.to_csv(FOODS_FILE, index=False)
        await update.message.reply_text(f"{name} saved to database ✅")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    lines = update.message.text.strip().split("\n")[1:]
    if not lines:
        await update.message.reply_text("Please provide food and amount lines after /log.")
        return

    df_foods = pd.read_csv(FOODS_FILE)
    results = []

    for line in lines:
        parts = line.strip().split()
        if len(parts) != 2:
            continue
        name, amount = parts[0].lower(), float(parts[1])
        food_row = df_foods[df_foods["name"] == name]

        if food_row.empty:
            results.append({"Food": name, "Error": "Not found"})
            continue

        r = food_row.iloc[0]
        factor = amount / 100
        results.append({
            "Food": name,
            "Protein": r["protein"] * factor,
            "Fat": r["fat"] * factor,
            "Carb": r["carb"] * factor,
            "Calories": r["calories"] * factor
        })

    df_result = pd.DataFrame(results)

    if "Error" in df_result.columns:
        msg = "Some foods not found. Please check with /setfood."
    else:
        totals = df_result[["Protein", "Fat", "Carb", "Calories"]].sum()
        df_result.loc[len(df_result)] = ["Total", *totals]
        msg = "```\n" + df_result.to_string(index=False, formatters={"Calories": "{:.0f}".format}) + "\n```"

    await update.message.reply_text(msg, parse_mode="Markdown")


if __name__ == "__main__":
    import threading
    from flask import Flask

    TOKEN = os.getenv("TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setfood", setfood))
    app.add_handler(CommandHandler("log", log))

    # Run Flask + Bot together for Render
    from telegram.ext import Application
    from flask import Flask
    flask_app = Flask(__name__)

    @flask_app.route('/')
    def home():
        return "Bot running!"

    def run_bot():
        app.run_polling()

    t = threading.Thread(target=run_bot)
    t.start()
    flask_app.run(host="0.0.0.0", port=10000)
