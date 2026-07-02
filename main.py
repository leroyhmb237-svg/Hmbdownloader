#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Media Downloader Bot Pro
Créé par 🇭 🇲 🇧
"""

import os
import sys
import asyncio
import threading
import logging
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeFilename
from flask import Flask, jsonify
from datetime import datetime
import time

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Flask app pour UptimeRobot
app = Flask(__name__)
start_time = time.time()

# Variables globales
user_client = None
bot_client = None

@app.route('/')
def home():
    uptime = int(time.time() - start_time)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    return jsonify({
        "bot": "Media Downloader Pro",
        "creator": "🇭 🇲 🇧",
        "status": "online",
        "uptime": f"{hours}h {minutes}m",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/ping')
def ping():
    return "Pong!", 200

def run_web():
    port = int(os.getenv("PORT", "10000"))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

async def main():
    print("╔════════════════════════════════════╗")
    print("║  🤖 Media Downloader Pro           ║")
    print("║  👑 Créé par 🇭 🇲 🇧                 ║")
    print("╚════════════════════════════════════╝")
    
    # Démarrer serveur web
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    logger.info("🌐 Serveur web démarré")
    
    # Récupérer les variables
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    
    if not all([API_ID, API_HASH, PHONE_NUMBER, BOT_TOKEN]):
        logger.error("❌ Variables manquantes! Vérifie Render Environment Variables")
        return
    
    # Connexion compte utilisateur
    logger.info("📱 Connexion au compte utilisateur...")
    
    try:
        if SESSION_STRING:
            logger.info("✅ Utilisation de la session existante")
            user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        else:
            logger.info("🆕 Création d'une nouvelle session...")
            user_client = TelegramClient(StringSession(), API_ID, API_HASH)
        
        await user_client.start(phone=PHONE_NUMBER)
        
        if not SESSION_STRING:
            new_session = user_client.session.save()
            logger.info("=" * 60)
            logger.info("🆕 NOUVELLE SESSION CRÉÉE!")
            logger.info("Copie cette ligne dans SESSION_STRING sur Render:")
            logger.info(new_session)
            logger.info("=" * 60)
        
        me = await user_client.get_me()
        logger.info(f"✅ Connecté: {me.first_name}")
        
    except Exception as e:
        logger.error(f"❌ Erreur connexion: {e}")
        return
    
    # Démarrer le bot
    logger.info("🤖 Démarrage du bot...")
    bot_client = TelegramClient('bot', API_ID, API_HASH)
    
    try:
        await bot_client.start(bot_token=BOT_TOKEN)
        bot_me = await bot_client.get_me()
        logger.info(f"✅ Bot démarré: @{bot_me.username}")
        
        # Handler /start
        @bot_client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            await event.respond(
                "👋 **Salut!**\n\n"
                "Je suis **Media Downloader Pro** by 🇭 🇲 🇧\n\n"
                "📥 Envoie-moi un lien Telegram:\n"
                "`https://t.me/c/1234567890/142`\n\n"
                "Je télécharge:\n"
                "• 📸 Photos\n"
                "• 🎬 Vidéos\n"
                "• 🎵 Audio\n"
                "• 📱 APK\n"
                "• 🔒 Canaux privés"
            )
        
        # Handler liens
        @bot_client.on(events.NewMessage(pattern=r'https?://t\.me/.*'))
        async def link_handler(event):
            url = event.text
            chat_id = event.chat_id
            
            msg = await event.respond("⏳ Analyse du lien...")
            
            try:
                # Parser le lien
                channel_id, message_id = None, None
                
                # Canal privé: t.me/c/ID/MSG
                match = re.search(r't\.me/c/(\d+)/(\d+)', url)
                if match:
                    channel_id = int(f"-100{match.group(1)}")
                    message_id = int(match.group(2))
                else:
                    # Canal public: t.me/nom/MSG
                    match = re.search(r't\.me/([a-zA-Z0-9_]+)/(\d+)', url)
                    if match:
                        channel_id = match.group(1)
                        message_id = int(match.group(2))
                
                if not channel_id:
                    await msg.edit("❌ Lien invalide. Format: https://t.me/c/ID/MSG")
                    return
                
                # Récupérer message
                entity = await user_client.get_entity(channel_id)
                message = await user_client.get_messages(entity, ids=message_id)
                
                if not message:
                    await msg.edit("❌ Message introuvable ou pas d'accès")
                    return
                
                if not message.media:
                    text = message.text or message.caption or "Message vide"
                    await msg.edit(f"📝 Message:\n\n{text[:4000]}")
                    return
                
                # Télécharger
                await msg.edit("📥 Téléchargement...")
                
                os.makedirs("downloads", exist_ok=True)
                file_path = await user_client.download_media(message, file="downloads/")
                
                if not file_path:
                    await msg.edit("❌ Échec du téléchargement")
                    return
                
                # Envoyer
                caption = f"✅ by 🇭 🇲 🇧\n\n{message.text or message.caption or ''}"[:1024]
                
                await bot_client.send_file(
                    chat_id, 
                    file_path, 
                    caption=caption,
                    force_document=True
                )
                
                # Nettoyer
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                await msg.delete()
                
            except Exception as e:
                await msg.edit(f"❌ Erreur: {str(e)}")
        
        logger.info("🎯 Bot prêt! En attente de liens...")
        await bot_client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ Erreur bot: {e}")
    finally:
        if user_client:
            await user_client.disconnect()
        if bot_client:
            await bot_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
