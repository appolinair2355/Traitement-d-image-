from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from PIL import Image
from io import BytesIO
import pytesseract
import json
import config
import os
import asyncio
import threading

# Flask app
app = Flask(__name__)

# Fichier JSON pour stocker les textes par utilisateur
DATA_FILE = "data.json"

# Charger ou créer le fichier JSON
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Application Telegram (globale)
application = Application.builder().token(config.BOT_TOKEN).build()

# --- COMMANDES --- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bienvenue ! Envoyez-moi une image et je vous renverrai le texte qu'elle contient.\n"
        "Tapez /help pour voir toutes les commandes."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commandes disponibles :\n"
        "/start - Démarrer le bot\n"
        "/help - Voir ce message\n"
        "/stats - Voir combien d'images ont été traitées\n"
        "/clear - [ADMIN] Supprimer toutes les données"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_users = len(data)
    total_texts = sum(len(texts) for texts in data.values())
    await update.message.reply_text(f"Total utilisateurs : {total_users}\nTotal images traitées : {total_texts}")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != config.ADMIN:
        await update.message.reply_text("Vous n'êtes pas autorisé à utiliser cette commande.")
        return
    global data
    data = {}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    await update.message.reply_text("Toutes les données ont été supprimées !")

# --- GESTION DES IMAGES --- #

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = BytesIO()
    await photo_file.download_to_memory(photo_bytes)
    photo_bytes.seek(0)
    
    image = Image.open(photo_bytes)
    text = pytesseract.image_to_string(image, lang="fra")
    
    if text.strip():
        await update.message.reply_text(f"Texte reconnu :\n{text}")
    else:
        await update.message.reply_text("Impossible de lire le texte.")
    
    # Stocker le texte dans JSON
    user_id = str(update.message.from_user.id)
    if user_id not in data:
        data[user_id] = []
    data[user_id].append(text)
    
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- FLASK ROUTES --- #

@app.route('/')
def home():
    return "Bot is running!"

@app.route(f'/{config.BOT_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(process_update(update))
    return "OK", 200

async def process_update(update):
    await application.process_update(update)

# --- MAIN --- #

def setup_handlers():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

def set_webhook():
    webhook_url = f"{config.WEBHOOK_URL}/{config.BOT_TOKEN}"
    application.bot.set_webhook(url=webhook_url)
    print(f"Webhook set to: {webhook_url}")

if __name__ == "__main__":
    # Setup
    setup_handlers()
    
    # Initialize application
    application.initialize()
    
    # Set webhook
    set_webhook()
    
    # Run Flask
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)
