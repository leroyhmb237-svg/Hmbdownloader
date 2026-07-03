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
import shutil
import platform

from datetime import datetime
from flask import Flask, jsonify

from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged


# =========================================================
# CONFIGURATION
# =========================================================

DOWNLOAD_DIR = "/tmp/downloads"
MAX_FILE_SIZE = 500 * 1024 * 1024
FORCE_CHANNEL = "FichierHatunnelPlus"
LOG_FILE = "bot.log"

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE)
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

users = set()
banned_users = set()

private_mode = False


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
        "users": len(users),
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
# FORMAT SIZE
# =========================================================

def format_size(size):

    if not size:
        return "Inconnue"

    power = 1024
    n = 0

    units = ['B', 'KB', 'MB', 'GB', 'TB']

    while size >= power and n < len(units) - 1:

        size /= power
        n += 1

    return f"{round(size, 2)} {units[n]}"


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(user_id):

    return user_id == ADMIN_ID


# =========================================================
# FORCE JOIN CHECK
# =========================================================

async def check_force_join(user_id):

    try:

        participant = await bot_client.get_permissions(
            FORCE_CHANNEL,
            user_id
        )

        return bool(participant)

    except Exception:
        return False


# =========================================================
# MAIN
# =========================================================

async def main():

    global user_client
    global bot_client
    global download_count
    global private_mode

    print("╔════════════════════════════════════╗")
    print("║  🤖 Media Downloader Pro           ║")
    print("║  👑 Créé par 🇭 🇲 🇧                 ║")
    print("╚════════════════════════════════════╝")

    # WEB SERVER
    web_thread = threading.Thread(
        target=run_web,
        daemon=True
    )

    web_thread.start()

    logger.info("🌐 Serveur web démarré")

    # ENV VARIABLES
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    SESSION_STRING = os.getenv("SESSION_STRING", "")

    if not all([
        API_ID,
        API_HASH,
        BOT_TOKEN,
        SESSION_STRING
    ]):

        logger.error("❌ Variables Render manquantes")
        return

    # USER CLIENT
    try:

        logger.info("📱 Connexion utilisateur...")

        user_client = TelegramClient(
            StringSession(SESSION_STRING),
            API_ID,
            API_HASH,
            connection=ConnectionTcpAbridged,
            connection_retries=10,
            retry_delay=2,
            auto_reconnect=True,
            sequential_updates=False,
            flood_sleep_threshold=60
        )

        await user_client.start()

        me = await user_client.get_me()

        logger.info(f"✅ Connecté : {me.first_name}")

    except Exception as e:

        logger.error(f"❌ Erreur connexion utilisateur : {e}")
        return

    # BOT CLIENT
    try:

        logger.info("🤖 Démarrage du bot...")

        bot_client = TelegramClient(
            "bot",
            API_ID,
            API_HASH,
            connection=ConnectionTcpAbridged,
            connection_retries=10,
            retry_delay=2,
            auto_reconnect=True,
            sequential_updates=False
        )

        await bot_client.start(bot_token=BOT_TOKEN)

        bot_me = await bot_client.get_me()

        logger.info(f"✅ Bot démarré : @{bot_me.username}")

        # /START
        @bot_client.on(events.NewMessage(pattern=r"^/start$"))
        async def start_handler(event):

            users.add(event.sender_id)

            if not await check_force_join(event.sender_id):

                await event.respond(
                    "🚫 Vous devez rejoindre notre canal pour utiliser ce bot.",
                    buttons=[
                        [
                            Button.url(
                                "📢 Rejoindre le canal",
                                f"https://t.me/{FORCE_CHANNEL}"
                            )
                        ]
                    ]
                )

                return

            await event.respond(
                "🤖 Media Downloader Pro\n\n"
                "📥 Envoie un lien Telegram\n\n"
                "📚 /commandes"
            )

        # /COMMANDES
        @bot_client.on(events.NewMessage(pattern=r"^/commandes$"))
        async def commandes_handler(event):

            await event.respond(
                "📚 Commandes disponibles\n\n"
                "/start\n"
                "/help\n"
                "/about\n"
                "/ping\n"
                "/uptime\n"
                "/status\n"
                "/stats\n"
                "/commandes\n\n"
                "👑 Admin :\n"
                "/users\n"
                "/broadcast MESSAGE\n"
                "/restart\n"
                "/logs\n"
                "/clear\n"
                "/private\n"
                "/ban ID\n"
                "/unban ID"
            )

        # /HELP
        @bot_client.on(events.NewMessage(pattern=r"^/help$"))
        async def help_handler(event):

            await event.respond(
                "📥 Envoie simplement un lien Telegram.\n\n"
                "📚 Voir les commandes : /commandes"
            )

        # /ABOUT
        @bot_client.on(events.NewMessage(pattern=r"^/about$"))
        async def about_handler(event):

            await event.respond(
                "🤖 Media Downloader Bot Pro\n"
                "👑 Créé par 🇭 🇲 🇧\n"
                "⚡ Powered by Telethon + Render"
            )

        # /PING
        @bot_client.on(events.NewMessage(pattern=r"^/ping$"))
        async def ping_handler(event):

            await event.respond("🏓 Pong !")

        # /UPTIME
        @bot_client.on(events.NewMessage(pattern=r"^/uptime$"))
        async def uptime_handler(event):

            uptime = int(time.time() - start_time)

            hours = uptime // 3600
            minutes = (uptime % 3600) // 60

            await event.respond(
                f"⏳ Uptime : {hours}h {minutes}m"
            )

        # /STATUS
        @bot_client.on(events.NewMessage(pattern=r"^/status$"))
        async def status_handler(event):

            await event.respond(
                "📊 Status du bot\n\n"
                f"📥 Téléchargements : {download_count}\n"
                f"👥 Utilisateurs : {len(users)}"
            )

        # /USERS
        @bot_client.on(events.NewMessage(pattern=r"^/users$"))
        async def users_handler(event):

            if not is_admin(event.sender_id):
                return

            await event.respond(
                f"👥 Nombre utilisateurs : {len(users)}"
            )

        # /PRIVATE
        @bot_client.on(events.NewMessage(pattern=r"^/private$"))
        async def private_handler(event):

            global private_mode

            if not is_admin(event.sender_id):
                return

            private_mode = not private_mode

            status = "Activé" if private_mode else "Désactivé"

            await event.respond(
                f"🔒 Mode privé : {status}"
            )

        # /CLEAR
        @bot_client.on(events.NewMessage(pattern=r"^/clear$"))
        async def clear_handler(event):

            if not is_admin(event.sender_id):
                return

            try:

                if os.path.exists(DOWNLOAD_DIR):
                    shutil.rmtree(DOWNLOAD_DIR)

                os.makedirs(DOWNLOAD_DIR, exist_ok=True)

                await event.respond("🗑 Cache supprimé")

            except Exception as e:

                await event.respond(f"❌ {e}")

        # /RESTART
        @bot_client.on(events.NewMessage(pattern=r"^/restart$"))
        async def restart_handler(event):

            if not is_admin(event.sender_id):
                return

            await event.respond("♻️ Redémarrage du bot...")

            os.execl(
                sys.executable,
                sys.executable,
                *sys.argv
            )

        # /LOGS
        @bot_client.on(events.NewMessage(pattern=r"^/logs$"))
        async def logs_handler(event):

            if not is_admin(event.sender_id):
                return

            try:

                if os.path.exists(LOG_FILE):

                    with open(
                        LOG_FILE,
                        "r",
                        encoding="utf-8",
                        errors="ignore"
                    ) as f:

                        data = f.read()[-4000:]

                    await event.respond(
                        f"📄 Logs :\n\n{data}"
                    )

                else:

                    await event.respond("⚠️ Aucun log disponible")

            except Exception as e:

                await event.respond(f"❌ {e}")

        # /STATS
        @bot_client.on(events.NewMessage(pattern=r"^/stats$"))
        async def stats_handler(event):

            total, used, free = shutil.disk_usage("/")

            await event.respond(
                "📊 Statistiques\n\n"
                f"💾 Total : {format_size(total)}\n"
                f"📦 Utilisé : {format_size(used)}\n"
                f"🆓 Libre : {format_size(free)}\n"
                f"📥 Téléchargements : {download_count}\n"
                f"🖥 OS : {platform.system()}"
            )

        # /BAN
        @bot_client.on(events.NewMessage(pattern=r"^/ban (.+)$"))
        async def ban_handler(event):

            if not is_admin(event.sender_id):
                return

            try:

                user_id = int(
                    event.pattern_match.group(1)
                )

                banned_users.add(user_id)

                await event.respond(
                    f"🚫 Utilisateur banni : {user_id}"
                )

            except:

                await event.respond(
                    "❌ Utilisation : /ban ID"
                )

        # /UNBAN
        @bot_client.on(events.NewMessage(pattern=r"^/unban (.+)$"))
        async def unban_handler(event):

            if not is_admin(event.sender_id):
                return

            try:

                user_id = int(
                    event.pattern_match.group(1)
                )

                banned_users.discard(user_id)

                await event.respond(
                    f"✅ Utilisateur débanni : {user_id}"
                )

            except:

                await event.respond(
                    "❌ Utilisation : /unban ID"
                )

        # /BROADCAST
        @bot_client.on(events.NewMessage(pattern=r"^/broadcast (.+)$"))
        async def broadcast_handler(event):

            if not is_admin(event.sender_id):
                return

            text = event.pattern_match.group(1)

            success = 0

            for user in users:

                try:

                    await bot_client.send_message(
                        user,
                        f"📢 {text}"
                    )

                    success += 1

                except:
                    pass

            await event.respond(
                f"✅ Message envoyé à {success} utilisateurs"
            )

        # TELEGRAM LINKS
        @bot_client.on(events.NewMessage(pattern=r'https?://'))
        async def link_handler(event):

            global download_count

            user_id = event.sender_id

            users.add(user_id)

            if user_id in banned_users:

                await event.respond("🚫 Vous êtes bloqué")
                return

            if private_mode and not is_admin(user_id):

                await event.respond("🔒 Bot actuellement privé")
                return

            if not await check_force_join(user_id):

                await event.respond(
                    "🚫 Vous devez rejoindre le canal pour utiliser ce bot.",
                    buttons=[
                        [
                            Button.url(
                                "📢 Rejoindre le canal",
                                f"https://t.me/{FORCE_CHANNEL}"
                            )
                        ]
                    ]
                )

                return

            url = event.text.strip()

            if "t.me/" not in url:

                await event.respond("❌ Liens Telegram uniquement")
                return

            msg = await event.respond("📥 Téléchargement...")

            try:

                channel_id = None
                message_id = None

                private_match = re.search(
                    r't\.me/c/(\d+)/(\d+)',
                    url
                )

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

                if not channel_id:

                    await msg.edit("❌ Lien invalide")
                    return

                entity = await user_client.get_entity(channel_id)

                message = await user_client.get_messages(
                    entity,
                    ids=message_id
                )

                if not message:

                    await msg.edit("❌ Message introuvable")
                    return

                if not message.media:

                    text = (
                        message.text
                        or message.message
                        or "Message vide"
                    )

                    await msg.edit(f"📝 {text[:4000]}")
                    return

                if (
                    message.file
                    and message.file.size > MAX_FILE_SIZE
                ):

                    await msg.edit("❌ Fichier trop volumineux")
                    return

                media_type = "📄 Document"

                if message.photo:
                    media_type = "📸 Photo"

                elif message.video:
                    media_type = "🎬 Vidéo"

                elif message.voice:
                    media_type = "🎤 Vocal"

                elif message.audio:
                    media_type = "🎵 Audio"

                file_size = "Inconnue"

                if message.file:

                    file_size = format_size(
                        message.file.size
                    )

                await msg.edit(
                    f"{media_type}\n"
                    f"📦 Taille : {file_size}\n\n"
                    "⚡ Téléchargement rapide..."
                )

                start_download = time.time()

                os.makedirs(
                    DOWNLOAD_DIR,
                    exist_ok=True
                )

                file_path = await user_client.download_media(
                    message,
                    file=DOWNLOAD_DIR,
                    thumb=None
                )

                if not file_path:

                    await msg.edit("❌ Téléchargement impossible")
                    return

                caption_text = (
                    message.text
                    or message.message
                    or ""
                )

                caption = (
                    f"✅ by 🇭 🇲 🇧\n\n"
                    f"{caption_text}"
                )[:1024]

                supports_streaming = bool(message.video)

                await bot_client.send_file(
                    entity=event.chat_id,
                    file=file_path,
                    caption=caption,
                    supports_streaming=supports_streaming,
                    allow_cache=True
                )

                try:

                    if os.path.exists(file_path):
                        os.remove(file_path)

                except Exception as cleanup_error:

                    logger.warning(
                        f"⚠️ Erreur suppression : {cleanup_error}"
                    )

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
                    f"❌ Impossible de télécharger\n\n{e}"
                )

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
