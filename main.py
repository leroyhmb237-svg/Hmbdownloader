#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════╗
║     Media Downloader Bot Pro      ║
║          Créé par 🇭 🇲 🇧            ║
╚════════════════════════════════════╝
"""

import os
import sys
import asyncio
import threading
import logging
import re
import time

from datetime import datetime
from flask import Flask, jsonify

from telethon import TelegramClient, events
from telethon.sessions import StringSession


# =========================================================
# CONFIGURATION LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

start_time = time.time()

download_count = 0

user_client = None
bot_client = None


# =========================================================
# WEB ROUTES
# =========================================================

@app.route('/')
def home():

    uptime = int(time.time() - start_time)

    hours = uptime // 3600
    minutes = (uptime % 3600) // 60

    return jsonify({
        "bot": "Media Downloader Pro",
        "creator": "🇭 🇲 🇧",
        "status": "online",
        "downloads": download_count,
        "uptime": f"{hours}h {minutes}m",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/health')
def health():
    return jsonify({
        "status": "healthy"
    }), 200


@app.route('/ping')
def ping():
    return "Pong!", 200


# =========================================================
# RUN WEB SERVER
# =========================================================

def run_web():

    port = int(os.getenv("PORT", "10000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


# =========================================================
# FORMAT FILE SIZE
# =========================================================

def format_size(size):

    if not size:
        return "Inconnue"

    power = 1024
    n = 0
    units = ['B', 'KB', 'MB', 'GB']

    while size > power and n < len(units) - 1:
        size /= power
        n += 1

    return f"{round(size, 2)} {units[n]}"


# =========================================================
# MAIN
# =========================================================

async def main():

    global user_client
    global bot_client
    global download_count

    print("╔════════════════════════════════════╗")
    print("║  🤖 Media Downloader Pro           ║")
    print("║  👑 Créé par 🇭 🇲 🇧                 ║")
    print("╚════════════════════════════════════╝")

    # =====================================================
    # START WEB SERVER
    # =====================================================

    web_thread = threading.Thread(
        target=run_web,
        daemon=True
    )

    web_thread.start()

    logger.info("🌐 Serveur web démarré")

    # =====================================================
    # ENV VARIABLES
    # =====================================================

    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    SESSION_STRING = os.getenv("SESSION_STRING", "")

    if not all([API_ID, API_HASH, BOT_TOKEN, SESSION_STRING]):

        logger.error("❌ Variables Render manquantes")
        return

    # =====================================================
    # USER CLIENT
    # =====================================================

    try:

        logger.info("📱 Connexion utilisateur...")

        user_client = TelegramClient(
            StringSession(SESSION_STRING),
            API_ID,
            API_HASH
        )

        await user_client.start()

        me = await user_client.get_me()

        logger.info(f"✅ Connecté : {me.first_name}")

    except Exception as e:

        logger.error(f"❌ Erreur connexion utilisateur : {e}")
        return

    # =====================================================
    # BOT CLIENT
    # =====================================================

    try:

        logger.info("🤖 Démarrage du bot...")

        bot_client = TelegramClient(
            "bot",
            API_ID,
            API_HASH
        )

        await bot_client.start(
            bot_token=BOT_TOKEN
        )

        bot_me = await bot_client.get_me()

        logger.info(f"✅ Bot démarré : @{bot_me.username}")

        logger.info("🚀 Bot lancé avec succès")

        # =================================================
        # /START
        # =================================================

        @bot_client.on(events.NewMessage(pattern="/start"))
        async def start_handler(event):

            await event.respond(
                "╔══════════════════╗\n"
                "🤖 Media Downloader Pro\n"
                "👑 By 🇭 🇲 🇧\n"
                "╚══════════════════╝\n\n"

                "📥 Envoie un lien Telegram :\n"
                "`https://t.me/c/1234567890/142`\n\n"

                "✅ Support :\n"
                "• 📸 Photos\n"
                "• 🎬 Vidéos\n"
                "• 🎵 Audio\n"
                "• 🎤 Vocaux\n"
                "• 📄 Documents\n"
                "• 📱 APK\n"
                "• 🔒 Canaux privés"
            )

        # =================================================
        # /PING
        # =================================================

        @bot_client.on(events.NewMessage(pattern="/ping"))
        async def ping_handler(event):

            await event.respond(
                "🏓 Pong!\n"
                "✅ Bot online"
            )

        # =================================================
        # /UPTIME
        # =================================================

        @bot_client.on(events.NewMessage(pattern="/uptime"))
        async def uptime_handler(event):

            uptime = int(time.time() - start_time)

            hours = uptime // 3600
            minutes = (uptime % 3600) // 60

            await event.respond(
                f"⏳ Uptime : {hours}h {minutes}m"
            )

        # =================================================
        # /STATUS
        # =================================================

        @bot_client.on(events.NewMessage(pattern="/status"))
        async def status_handler(event):

            uptime = int(time.time() - start_time)

            hours = uptime // 3600
            minutes = (uptime % 3600) // 60

            await event.respond(
                "📊 Status du bot\n\n"
                f"✅ Online\n"
                f"📥 Téléchargements : {download_count}\n"
                f"⏳ Uptime : {hours}h {minutes}m"
            )

        # =================================================
        # /ABOUT
        # =================================================

        @bot_client.on(events.NewMessage(pattern="/about"))
        async def about_handler(event):

            await event.respond(
                "🤖 Media Downloader Pro\n"
                "👑 Créé par 🇭 🇲 🇧\n"
                "⚡ Powered by Telethon + Render"
            )

        # =================================================
        # /HELP
        # =================================================

        @bot_client.on(events.NewMessage(pattern="/help"))
        async def help_handler(event):

            await event.respond(
                "📖 Aide du bot\n\n"

                "📥 Envoie simplement un lien Telegram.\n\n"

                "✅ Formats supportés :\n"
                "• Photos\n"
                "• Vidéos\n"
                "• Vocaux\n"
                "• Audio\n"
                "• APK\n"
                "• Documents\n\n"

                "📌 Exemple :\n"
                "`https://t.me/c/1234567890/142`"
            )

        # =================================================
        # TELEGRAM LINKS
        # =================================================

        @bot_client.on(events.NewMessage(pattern=r'https?://'))
        async def link_handler(event):

            global download_count

            url = event.text.strip()

            chat_id = event.chat_id

            # =============================================
            # CHECK TELEGRAM URL
            # =============================================

            if "t.me/" not in url:

                await event.respond(
                    "❌ Seuls les liens Telegram sont acceptés"
                )

                return

            msg = await event.respond(
                "╔══════════════╗\n"
                "📥 Téléchargement\n"
                "⏳ Veuillez patienter...\n"
                "╚══════════════╝"
            )

            try:

                channel_id = None
                message_id = None

                # =========================================
                # PRIVATE LINKS
                # =========================================

                private_match = re.search(
                    r't\.me/c/(\d+)/(\d+)',
                    url
                )

                # =========================================
                # PUBLIC LINKS
                # =========================================

                public_match = re.search(
                    r't\.me/([a-zA-Z0-9_]+)/(\d+)',
                    url
                )

                if private_match:

                    channel_id = int(
                        f"-100{private_match.group(1)}"
                    )

                    message_id = int(
                        private_match.group(2)
                    )

                elif public_match:

                    channel_id = public_match.group(1)

                    message_id = int(
                        public_match.group(2)
                    )

                # =========================================
                # INVALID LINK
                # =========================================

                if not channel_id:

                    await msg.edit(
                        "❌ Lien Telegram invalide"
                    )

                    return

                # =========================================
                # GET MESSAGE
                # =========================================

                entity = await user_client.get_entity(
                    channel_id
                )

                message = await user_client.get_messages(
                    entity,
                    ids=message_id
                )

                if not message:

                    await msg.edit(
                        "❌ Message introuvable"
                    )

                    return

                # =========================================
                # TEXT MESSAGE
                # =========================================

                if not message.media:

                    text = (
                        message.text
                        or message.message
                        or "Message vide"
                    )

                    await msg.edit(
                        f"📝 Message :\n\n{text[:4000]}"
                    )

                    return

                # =========================================
                # MEDIA TYPE
                # =========================================

                media_type = "📄 Document"

                if message.photo:
                    media_type = "📸 Photo"

                elif message.video:
                    media_type = "🎬 Vidéo"

                elif message.voice:
                    media_type = "🎤 Vocal"

                elif message.audio:
                    media_type = "🎵 Audio"

                # =========================================
                # FILE SIZE
                # =========================================

                file_size = "Inconnue"

                if message.file:
                    file_size = format_size(
                        message.file.size
                    )

                # =========================================
                # DOWNLOAD
                # =========================================

                await msg.edit(
                    f"{media_type} détecté\n"
                    f"📦 Taille : {file_size}\n\n"
                    "📥 Téléchargement..."
                )

                start_download = time.time()

                os.makedirs(
                    "downloads",
                    exist_ok=True
                )

                file_path = await message.download_media(
                    file="downloads/"
                )

                if not file_path:

                    await msg.edit(
                        "❌ Impossible de télécharger ce média"
                    )

                    return

                # =========================================
                # CAPTION
                # =========================================

                caption_text = (
                    message.text
                    or message.message
                    or ""
                )

                caption = (
                    f"✅ by 🇭 🇲 🇧\n\n"
                    f"{caption_text}"
                )[:1024]

                # =========================================
                # SEND FILE
                # =========================================

                await bot_client.send_file(
                    entity=chat_id,
                    file=file_path,
                    caption=caption
                )

                # =========================================
                # CLEANUP
                # =========================================

                try:

                    if os.path.exists(file_path):
                        os.remove(file_path)

                except Exception as cleanup_error:

                    logger.warning(
                        f"⚠️ Erreur suppression : {cleanup_error}"
                    )

                # =========================================
                # DOWNLOAD STATS
                # =========================================

                download_count += 1

                elapsed = round(
                    time.time() - start_download,
                    2
                )

                await msg.edit(
                    "✅ Téléchargement terminé !\n\n"
                    f"{media_type}\n"
                    f"📦 Taille : {file_size}\n"
                    f"⏱ Temps : {elapsed}s"
                )

            except Exception as e:

                logger.error(
                    f"❌ Erreur téléchargement : {e}"
                )

                await msg.edit(
                    "❌ Impossible de télécharger ce média"
                )

        # =================================================
        # READY
        # =================================================

        logger.info(
            "🎯 Bot prêt ! En attente de liens..."
        )

        await bot_client.run_until_disconnected()

    except Exception as e:

        logger.error(f"❌ Erreur bot : {e}")

    finally:

        try:

            if user_client:
                await user_client.disconnect()

            if bot_client:
                await bot_client.disconnect()

        except Exception:
            pass


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
