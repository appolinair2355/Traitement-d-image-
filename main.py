from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import asyncio
import config

app = Flask(__name__)

# Initialiser bot et application
bot = Bot(token=config.BOT_TOKEN)
application = Application.builder().token(config.BOT_TOKEN).build()

# --- HANDLERS --- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenue !")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Aide")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))

# --- FLASK ROUTES --- #
@app.route('/')
def home():
    return "Bot is running!"

@app.route(f'/{config.BOT_TOKEN}', methods=['POST'])
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, bot)
    
    # Créer un nouveau event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Initialiser si besoin
    if not application._initialized:
        loop.run_until_complete(application.initialize())
    
    # Traiter la mise à jour
    loop.run_until_complete(application.process_update(update))
    
    return "OK", 200

# --- MAIN --- #
if __name__ == "__main__":
    # Setup webhook
    webhook_url = f"{config.WEBHOOK_URL}/{config.BOT_TOKEN}"
    asyncio.run(bot.set_webhook(url=webhook_url))
    print(f"Webhook set: {webhook_url}")
    
    # Run Flask sur le port Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
