from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from PIL import Image
from io import BytesIO
import requests
import json
import config
import os
import base64

DATA_FILE = "data.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {}

# API OCR.space (gratuit)
OCR_API_KEY = "K86527928888957"  # Clé API gratuite par défaut

async def ocr_space_api(image_bytes):
    url = "https://api.ocr.space/parse/image"
    payload = {
        'apikey': OCR_API_KEY,
        'language': 'fre',
        'isOverlayRequired': False
    }
    files = {'image': ('image.jpg', image_bytes)}
    response = requests.post(url, data=payload, files=files)
    result = response.json()
    if result.get("ParsedResults"):
        return result["ParsedResults"][0].get("ParsedText", "")
    return ""

# --- COMMANDES --- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenue ! Envoyez-moi une image et je vous renverrai le texte.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - Démarrer\n/help - Aide\n/stats - Statistiques")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(len(v) for v in data.values())
    await update.message.reply_text(f"Images traitées : {total}")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != config.ADMIN:
        return await update.message.reply_text("Non autorisé")
    global data
    data = {}
    await update.message.reply_text("Données supprimées")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = BytesIO()
    await photo_file.download_to_memory(photo_bytes)
    photo_bytes.seek(0)
    
    # Utiliser API OCR au lieu de Tesseract
    text = await ocr_space_api(photo_bytes)
    
    if text.strip():
        await update.message.reply_text(f"Texte reconnu :\n{text}")
    else:
        await update.message.reply_text("Impossible de lire le texte.")
    
    user_id = str(update.message.from_user.id)
    data[user_id] = data.get(user_id, []) + [text]

def main():
    application = Application.builder().token(config.BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.run_polling()

if __name__ == "__main__":
    main()
    
