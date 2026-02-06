from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from PIL import Image
from io import BytesIO
import pytesseract
import json
import config
import os

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

# --- COMMANDES --- #

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Bienvenue ! Envoyez-moi une image et je vous renverrai le texte qu'elle contient.\n"
        "Tapez /help pour voir toutes les commandes."
    )

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Commandes disponibles :\n"
        "/start - Démarrer le bot\n"
        "/help - Voir ce message\n"
        "/stats - Voir combien d'images ont été traitées\n"
        "/clear - [ADMIN] Supprimer toutes les données"
    )

def stats(update: Update, context: CallbackContext):
    total_users = len(data)
    total_texts = sum(len(texts) for texts in data.values())
    update.message.reply_text(f"Total utilisateurs : {total_users}\nTotal images traitées : {total_texts}")

def clear(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id != config.ADMIN:
        update.message.reply_text("Vous n'êtes pas autorisé à utiliser cette commande.")
        return
    global data
    data = {}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    update.message.reply_text("Toutes les données ont été supprimées !")

# --- GESTION DES IMAGES --- #

def handle_photo(update: Update, context: CallbackContext):
    photo_file = update.message.photo[-1].get_file()
    photo_bytes = BytesIO()
    photo_file.download(out=photo_bytes)
    photo_bytes.seek(0)
    
    image = Image.open(photo_bytes)
    text = pytesseract.image_to_string(image, lang="fra")
    
    if text.strip():
        update.message.reply_text(f"Texte reconnu :\n{text}")
    else:
        update.message.reply_text("Impossible de lire le texte.")
    
    # Stocker le texte dans JSON
    user_id = str(update.message.from_user.id)
    if user_id not in data:
        data[user_id] = []
    data[user_id].append(text)
    
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- MAIN --- #

def main():
    updater = Updater(config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Commandes
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CommandHandler("clear", clear))
    
    # Gestion des photos
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    
    # Webhook sur le port 10000
    PORT = 10000
    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=config.BOT_TOKEN)
    updater.bot.set_webhook(config.WEBHOOK_URL)
    
    print(f"Bot démarré sur le port {PORT}...")
    updater.idle()

if __name__ == "__main__":
    main()
