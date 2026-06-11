
import logging
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode
from datetime import datetime, timedelta

# ========================
# SOZLAMALAR
# ========================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8886980857:AAGQhpYs9s2_2RgzMhrUT8HfWuC7F7e8iaY")  # Set this or export BOT_TOKEN in your environment

# Kanal va guruh linklaringiz (ixtiyoriy)
CHANNEL_LINK = "https://t.me/CodX1kjwhshdjdi"
GROUP_LINK   = "https://t.me/+scu8_xImlZoxNThi"
SUPPORT_LINK = "https://t.me/IN1SIMON"

# Ogohlantirishlar soni — bu qadamdan keyin ban
WARN_LIMIT = 3

# ========================
# LOGGING
# ========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ========================
# IN-MEMORY STORAGE
# (Katta loyiha uchun SQLite/PostgreSQL ishlating)
# ========================
# { chat_id: { user_id: warn_count } }
warns: dict[int, dict[int, int]] = {}

# { chat_id: language }   ("uz" | "ru" | "en")
chat_lang: dict[int, str] = {}


# ========================
# TARJIMA / TEXTS
# ========================
TEXTS = {
    "uz": {
        "start": (
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "🤖 <b>jarvis help bot</b> — guruhingizni oson va xavfsiz boshqarish uchun "
            "eng mukammal bot!\n\n"
            "➕ Botni guruhingizga qo'shing va ishga tushishi uchun "
            "<b>Admin</b> huquqini bering!\n\n"
            "❓ <b>QANDAY BUYRUQLAR BOR?</b>\n"
            "Barcha buyruqlarni ko'rish uchun /help buyrug'ini yuboring!"
        ),
        "help": (
            "📋 <b>BUYRUQLAR RO'YXATI</b>\n\n"
            "👮 <b>Admin buyruqlari:</b>\n"
            "/ban — Foydalanuvchini ban qilish\n"
            "/unban — Foydalanuvchidan ban olib tashlash\n"
            "/kick — Foydalanuvchini guruhdan chiqarish\n"
            "/mute — Foydalanuvchini jim qilish\n"
            "/unmute — Jim qilishni bekor qilish\n"
            "/warn — Foydalanuvchiga ogohlantirish berish\n"
            "/unwarn — Ogohlantirishni olib tashlash\n"
            "/warns — Ogohlantirishlarni ko'rish\n"
            "/pin — Xabarni pin qilish\n"
            "/unpin — Xabarni pin'dan olib tashlash\n\n"
            "👥 <b>Guruh buyruqlari:</b>\n"
            "/rules — Guruh qoidalari\n"
            "/info — Guruh ma'lumotlari\n"
            "/members — A'zolar soni\n\n"
            "🔤 <b>Umumiy buyruqlar:</b>\n"
            "/start — Botni ishga tushirish\n"
            "/help — Yordam menyusi\n"
            "/language — Tilni o'zgartirish\n"
            "/id — Foydalanuvchi ID'sini ko'rish\n"
        ),
        "rules": (
            "📜 <b>GURUH QOIDALARI</b>\n\n"
            "1️⃣ Hurmat bilan muloqot qiling\n"
            "2️⃣ Spam va reklama taqiqlangan\n"
            "3️⃣ Yomon so'zlar ishlatmang\n"
            "4️⃣ Faqat mavzuga oid gaplashing\n"
            "5️⃣ Boshqalarning shaxsiy ma'lumotlarini tarqatmang\n\n"
            "⚠️ Qoidalarni buzganlar ogohlantirish oladi, "
            f"so'ng ban qilinadi ({WARN_LIMIT} ta ogohlantirish)."
        ),
        "welcome": "👋 Xush kelibsiz, {name}! Guruhimizga qo'shilganingiz bilan tabriklaymiz! /rules buyrug'i bilan qoidalarni o'qing.",
        "banned": "🚫 {name} ban qilindi.",
        "unbanned": "✅ {name} ban'dan ozod qilindi.",
        "kicked": "👢 {name} guruhdan chiqarildi.",
        "muted": "🔇 {name} jim qilindi.",
        "unmuted": "🔊 {name} gapirishga ruxsat berildi.",
        "warned": "⚠️ {name} ogohlantirish oldi! ({count}/{limit})\nSabab: {reason}",
        "warned_banned": "🚫 {name} {limit} ta ogohlantirish olganligi sababli ban qilindi!",
        "unwarn": "✅ {name} ogohlantirishlari tozalandi.",
        "no_warns": "✅ {name} ogohlantirishlari yo'q.",
        "current_warns": "⚠️ {name}: {count}/{limit} ogohlantirish.",
        "not_admin": "❌ Siz admin emassiz!",
        "no_reply": "❌ Foydalanuvchini belgilang (reply qiling).",
        "pinned": "📌 Xabar pin qilindi.",
        "unpinned": "📌 Xabar pin'dan olib tashlandi.",
        "lang_changed": "✅ Til o'zgartirildi: O'zbekcha 🇺🇿",
    },
    "ru": {
        "start": (
            "👋 <b>Привет!</b>\n\n"
            "🤖 <b>jarvis help bot</b> — лучший бот для управления группой!\n\n"
            "➕ Добавьте бота в группу и дайте права <b>Admin</b>!\n\n"
            "❓ <b>ДОСТУПНЫЕ КОМАНДЫ?</b>\n"
            "Отправьте /help для списка команд!"
        ),
        "help": (
            "📋 <b>СПИСОК КОМАНД</b>\n\n"
            "👮 <b>Команды администратора:</b>\n"
            "/ban — Забанить пользователя\n"
            "/unban — Разбанить пользователя\n"
            "/kick — Выгнать из группы\n"
            "/mute — Заглушить пользователя\n"
            "/unmute — Снять заглушку\n"
            "/warn — Предупреждение\n"
            "/unwarn — Снять предупреждение\n"
            "/warns — Просмотр предупреждений\n"
            "/pin — Закрепить сообщение\n"
            "/unpin — Открепить сообщение\n\n"
            "👥 <b>Команды группы:</b>\n"
            "/rules — Правила группы\n"
            "/info — Информация о группе\n"
            "/members — Количество участников\n\n"
            "🔤 <b>Общие команды:</b>\n"
            "/start — Запустить бота\n"
            "/help — Помощь\n"
            "/language — Сменить язык\n"
            "/id — Узнать ID\n"
        ),
        "rules": (
            "📜 <b>ПРАВИЛА ГРУППЫ</b>\n\n"
            "1️⃣ Общайтесь уважительно\n"
            "2️⃣ Спам и реклама запрещены\n"
            "3️⃣ Не используйте нецензурную лексику\n"
            "4️⃣ Говорите только по теме\n"
            "5️⃣ Не распространяйте личные данные других\n\n"
            "⚠️ Нарушители получают предупреждения, "
            f"затем бан ({WARN_LIMIT} предупреждения)."
        ),
        "welcome": "👋 Добро пожаловать, {name}! Прочитайте правила: /rules",
        "banned": "🚫 {name} забанен.",
        "unbanned": "✅ {name} разбанен.",
        "kicked": "👢 {name} выгнан из группы.",
        "muted": "🔇 {name} заглушен.",
        "unmuted": "🔊 {name} может снова говорить.",
        "warned": "⚠️ {name} получил предупреждение! ({count}/{limit})\nПричина: {reason}",
        "warned_banned": "🚫 {name} забанен за {limit} предупреждения!",
        "unwarn": "✅ Предупреждения {name} сброшены.",
        "no_warns": "✅ У {name} нет предупреждений.",
        "current_warns": "⚠️ {name}: {count}/{limit} предупреждений.",
        "not_admin": "❌ Вы не администратор!",
        "no_reply": "❌ Ответьте на сообщение пользователя.",
        "pinned": "📌 Сообщение закреплено.",
        "unpinned": "📌 Сообщение откреплено.",
        "lang_changed": "✅ Язык изменён: Русский 🇷🇺",
    },
    "en": {
        "start": (
            "👋 <b>Hello!</b>\n\n"
            "🤖 <b>jarvis help bot</b> — the best bot for managing your group!\n\n"
            "➕ Add the bot to your group and give it <b>Admin</b> rights!\n\n"
            "❓ <b>AVAILABLE COMMANDS?</b>\n"
            "Send /help for a list of commands!"
        ),
        "help": (
            "📋 <b>COMMAND LIST</b>\n\n"
            "👮 <b>Admin commands:</b>\n"
            "/ban — Ban a user\n"
            "/unban — Unban a user\n"
            "/kick — Kick from group\n"
            "/mute — Mute a user\n"
            "/unmute — Unmute a user\n"
            "/warn — Warn a user\n"
            "/unwarn — Clear warnings\n"
            "/warns — View warnings\n"
            "/pin — Pin a message\n"
            "/unpin — Unpin a message\n\n"
            "👥 <b>Group commands:</b>\n"
            "/rules — Group rules\n"
            "/info — Group info\n"
            "/members — Member count\n\n"
            "🔤 <b>General commands:</b>\n"
            "/start — Start the bot\n"
            "/help — Help menu\n"
            "/language — Change language\n"
            "/id — Get user ID\n"
        ),
        "rules": (
            "📜 <b>GROUP RULES</b>\n\n"
            "1️⃣ Be respectful\n"
            "2️⃣ No spam or advertising\n"
            "3️⃣ No offensive language\n"
            "4️⃣ Stay on topic\n"
            "5️⃣ Don't share others' private info\n\n"
            "⚠️ Rule-breakers receive warnings, "
            f"then a ban ({WARN_LIMIT} warnings)."
        ),
        "welcome": "👋 Welcome, {name}! Please read the rules: /rules",
        "banned": "🚫 {name} has been banned.",
        "unbanned": "✅ {name} has been unbanned.",
        "kicked": "👢 {name} has been kicked.",
        "muted": "🔇 {name} has been muted.",
        "unmuted": "🔊 {name} can speak again.",
        "warned": "⚠️ {name} has been warned! ({count}/{limit})\nReason: {reason}",
        "warned_banned": "🚫 {name} has been banned after {limit} warnings!",
        "unwarn": "✅ Warnings for {name} have been cleared.",
        "no_warns": "✅ {name} has no warnings.",
        "current_warns": "⚠️ {name}: {count}/{limit} warnings.",
        "not_admin": "❌ You are not an admin!",
        "no_reply": "❌ Reply to a user's message.",
        "pinned": "📌 Message pinned.",
        "unpinned": "📌 Message unpinned.",
        "lang_changed": "✅ Language changed: English 🇬🇧",
    },
    "tr": {
        "start": (
            "👋 <b>Merhaba!</b>\n\n"
            "🤖 <b>jarvis help bot</b> — grubunuzu yönetmek için en iyi bot!\n\n"
            "➕ Botu grubunuza ekleyin va ona <b>Admin</b> yetkisi verin!\n\n"
            "❓ <b>KULLANILABİLİR KOMUTLAR?</b>\n"
            "Komut listesi için /help yazın!"
        ),
        "help": (
            "📋 <b>KOMUT LİSTESİ</b>\n\n"
            "👮 <b>Yönetici komutları:</b>\n"
            "/ban — Kullanıcıyı yasakla\n"
            "/unban — Kullanıcının yasağını kaldır\n"
            "/kick — Grubtan at\n"
            "/mute — Kullanıcıyı sustur\n"
            "/unmute — Susturmayı kaldır\n"
            "/warn — Uyarı ver\n"
            "/unwarn — Uyarıyı kaldır\n"
            "/warns — Uyarıları göster\n"
            "/pin — Mesajı sabitle\n"
            "/unpin — Sabitlemeyi kaldır\n\n"
            "👥 <b>Grup komutları:</b>\n"
            "/rules — Grup kuralları\n"
            "/info — Grup bilgisi\n"
            "/members — Üye sayısı\n\n"
            "🔤 <b>Genel komutlar:</b>\n"
            "/start — Botu başlat\n"
            "/help — Yardım\n"
            "/language — Dil değiştir\n"
            "/id — Kullanıcı ID'si\n"
        ),
        "rules": (
            "📜 <b>GRUP KURALLARI</b>\n\n"
            "1️⃣ Saygılı olun\n"
            "2️⃣ Spam ve reklam yasaktır\n"
            "3️⃣ Küfürlü dil kullanmayın\n"
            "4️⃣ Konuya uygun konuşun\n"
            "5️⃣ Başkalarının özel bilgilerini paylaşmayın\n\n"
            "⚠️ Kuralları çiğneyenler uyarı alır, sonra yasaklanır "
            f"({WARN_LIMIT} uyarı)."
        ),
        "welcome": "👋 Hoş geldin, {name}! /rules ile kuralları oku.",
        "banned": "🚫 {name} yasaklandı.",
        "unbanned": "✅ {name} yasağı kaldırıldı.",
        "kicked": "👢 {name} gruptan atıldı.",
        "muted": "🔇 {name} susturuldu.",
        "unmuted": "🔊 {name} artık konuşabilir.",
        "warned": "⚠️ {name} uyarıldı! ({count}/{limit})\nSebep: {reason}",
        "warned_banned": "🚫 {name} {limit} uyarı sonrası yasaklandı!",
        "unwarn": "✅ {name} uyarıları temizlendi.",
        "no_warns": "✅ {name} için uyarı yok.",
        "current_warns": "⚠️ {name}: {count}/{limit} uyarı.",
        "not_admin": "❌ Sen admin değilsin!",
        "no_reply": "❌ Bir kullanıcıya yanıt ver.",
        "pinned": "📌 Mesaj sabitlendi.",
        "unpinned": "📌 Mesaj sabitleme kaldırıldı.",
        "lang_changed": "✅ Dil değiştirildi: Türkçe 🇹🇷",
    },
    "es": {
        "start": (
            "👋 <b>¡Hola!</b>\n\n"
            "🤖 <b>jarvis help bot</b> — el mejor bot para gestionar tu grupo!\n\n"
            "➕ Agrégalo a tu grupo y dale permisos de <b>Admin</b>!\n\n"
            "❓ <b>¿COMANDOS DISPONIBLES?</b>\n"
            "Envía /help para ver la lista de comandos!"
        ),
        "help": (
            "📋 <b>LISTA DE COMANDOS</b>\n\n"
            "👮 <b>Comandos de administrador:</b>\n"
            "/ban — Banear usuario\n"
            "/unban — Desbanear usuario\n"
            "/kick — Expulsar del grupo\n"
            "/mute — Silenciar usuario\n"
            "/unmute — Quitar silencio\n"
            "/warn — Advertir usuario\n"
            "/unwarn — Quitar advertencia\n"
            "/warns — Ver advertencias\n"
            "/pin — Fijar mensaje\n"
            "/unpin — Desfijar mensaje\n\n"
            "👥 <b>Comandos de grupo:</b>\n"
            "/rules — Reglas del grupo\n"
            "/info — Información del grupo\n"
            "/members — Número de miembros\n\n"
            "🔤 <b>Comandos generales:</b>\n"
            "/start — Iniciar el bot\n"
            "/help — Ayuda\n"
            "/language — Cambiar idioma\n"
            "/id — Obtener ID\n"
        ),
        "rules": (
            "📜 <b>REGLAS DEL GRUPO</b>\n\n"
            "1️⃣ Sé respetuoso\n"
            "2️⃣ No spam ni publicidad\n"
            "3️⃣ No uses lenguaje ofensivo\n"
            "4️⃣ Mantente en el tema\n"
            "5️⃣ No compartas datos privados\n\n"
            "⚠️ Los infractores reciben advertencias, luego ban "
            f"({WARN_LIMIT} advertencias)."
        ),
        "welcome": "👋 ¡Bienvenido, {name}! Lee las reglas: /rules",
        "banned": "🚫 {name} ha sido baneado.",
        "unbanned": "✅ {name} ha sido desbaneado.",
        "kicked": "👢 {name} ha sido expulsado.",
        "muted": "🔇 {name} ha sido silenciado.",
        "unmuted": "🔊 {name} puede hablar de nuevo.",
        "warned": "⚠️ {name} ha sido advertido! ({count}/{limit})\nRazón: {reason}",
        "warned_banned": "🚫 {name} ha sido baneado después de {limit} advertencias!",
        "unwarn": "✅ Las advertencias de {name} han sido borradas.",
        "no_warns": "✅ {name} no tiene advertencias.",
        "current_warns": "⚠️ {name}: {count}/{limit} advertencias.",
        "not_admin": "❌ No eres administrador!",
        "no_reply": "❌ Responde al mensaje del usuario.",
        "pinned": "📌 Mensaje fijado.",
        "unpinned": "📌 Mensaje desafijado.",
        "lang_changed": "✅ Idioma cambiado: Español 🇪🇸",
    },
    "fr": {
        "start": (
            "👋 <b>Bonjour!</b>\n\n"
            "🤖 <b>jarvis help bot</b> — le meilleur bot pour gérer votre groupe!\n\n"
            "➕ Ajoutez-le à votre groupe et donnez-lui les droits <b>Admin</b>!\n\n"
            "❓ <b>COMMANDES DISPONIBLES?</b>\n"
            "Envoyez /help pour voir la liste des commandes!"
        ),
        "help": (
            "📋 <b>LISTE DES COMMANDES</b>\n\n"
            "👮 <b>Commandes admin:</b>\n"
            "/ban — Bannir un utilisateur\n"
            "/unban — Débannir un utilisateur\n"
            "/kick — Expulser du groupe\n"
            "/mute — Mettre en sourdine un utilisateur\n"
            "/unmute — Réactiver le micro\n"
            "/warn — Avertir un utilisateur\n"
            "/unwarn — Retirer l'avertissement\n"
            "/warns — Voir les avertissements\n"
            "/pin — Épingler un message\n"
            "/unpin — Détacher un message\n\n"
            "👥 <b>Commandes de groupe:</b>\n"
            "/rules — Règles du groupe\n"
            "/info — Infos du groupe\n"
            "/members — Nombre de membres\n\n"
            "🔤 <b>Commandes générales:</b>\n"
            "/start — Démarrer le bot\n"
            "/help — Aide\n"
            "/language — Changer de langue\n"
            "/id — Obtenir l'ID\n"
        ),
        "rules": (
            "📜 <b>RÈGLES DU GROUPE</b>\n\n"
            "1️⃣ Soyez respectueux\n"
            "2️⃣ Pas de spam ni de publicité\n"
            "3️⃣ Pas de langage offensant\n"
            "4️⃣ Restez dans le sujet\n"
            "5️⃣ Ne partagez pas d'infos privées\n\n"
            "⚠️ Les contrevenants reçoivent des avertissements, puis un ban "
            f"({WARN_LIMIT} avertissements)."
        ),
        "welcome": "👋 Bienvenue, {name}! Lisez les règles : /rules",
        "banned": "🚫 {name} a été banni.",
        "unbanned": "✅ {name} a été débanni.",
        "kicked": "👢 {name} a été expulsé.",
        "muted": "🔇 {name} a été rendu muet.",
        "unmuted": "🔊 {name} peut reparler.",
        "warned": "⚠️ {name} a été averti! ({count}/{limit})\nRaison : {reason}",
        "warned_banned": "🚫 {name} a été banni après {limit} avertissements!",
        "unwarn": "✅ Les avertissements de {name} ont été effacés.",
        "no_warns": "✅ {name} n'a pas d'avertissements.",
        "current_warns": "⚠️ {name} : {count}/{limit} avertissements.",
        "not_admin": "❌ Vous n'êtes pas admin!",
        "no_reply": "❌ Répondez au message de l'utilisateur.",
        "pinned": "📌 Message épinglé.",
        "unpinned": "📌 Message désépinglé.",
        "lang_changed": "✅ Langue changée : Français 🇫🇷",
    },
    "de": {
        "start": (
            "👋 <b>Hallo!</b>\n\n"
            "🤖 <b>jarvis help bot</b> — der beste Bot zur Verwaltung deiner Gruppe!\n\n"
            "➕ Füge ihn deiner Gruppe hinzu und gib ihm <b>Admin</b>-Rechte!\n\n"
            "❓ <b>VERFÜGBARE BEFEHLE?</b>\n"
            "Sende /help für die Liste der Befehle!"
        ),
        "help": (
            "📋 <b>BEFEHLSLISTE</b>\n\n"
            "👮 <b>Admin-Befehle:</b>\n"
            "/ban — Benutzer sperren\n"
            "/unban — Entsperren\n"
            "/kick — Aus der Gruppe entfernen\n"
            "/mute — Benutzer stummschalten\n"
            "/unmute — Stummschaltung aufheben\n"
            "/warn — Verwarnen\n"
            "/unwarn — Verwarnung entfernen\n"
            "/warns — Verwarnungen anzeigen\n"
            "/pin — Nachricht anheften\n"
            "/unpin — Nachricht lösen\n\n"
            "👥 <b>Gruppenbefehle:</b>\n"
            "/rules — Gruppenregeln\n"
            "/info — Gruppeninfo\n"
            "/members — Mitgliederzahl\n\n"
            "🔤 <b>Allgemeine Befehle:</b>\n"
            "/start — Bot starten\n"
            "/help — Hilfe\n"
            "/language — Sprache ändern\n"
            "/id — ID abrufen\n"
        ),
        "rules": (
            "📜 <b>GRUPPENREGELN</b>\n\n"
            "1️⃣ Sei respektvoll\n"
            "2️⃣ Kein Spam oder Werbung\n"
            "3️⃣ Keine beleidigende Sprache\n"
            "4️⃣ Bleibe beim Thema\n"
            "5️⃣ Teile keine privaten Infos\n\n"
            "⚠️ Regelbrecher erhalten Verwarnungen, dann Bann "
            f"({WARN_LIMIT} Verwarnungen)."
        ),
        "welcome": "👋 Willkommen, {name}! Bitte lese die Regeln: /rules",
        "banned": "🚫 {name} wurde gebannt.",
        "unbanned": "✅ {name} wurde entbannt.",
        "kicked": "👢 {name} wurde aus der Gruppe geworfen.",
        "muted": "🔇 {name} wurde stummgeschaltet.",
        "unmuted": "🔊 {name} kann wieder sprechen.",
        "warned": "⚠️ {name} wurde verwarnt! ({count}/{limit})\nGrund: {reason}",
        "warned_banned": "🚫 {name} wurde nach {limit} Verwarnungen gebannt!",
        "unwarn": "✅ Verwarnungen von {name} wurden gelöscht.",
        "no_warns": "✅ {name} hat keine Verwarnungen.",
        "current_warns": "⚠️ {name}: {count}/{limit} Verwarnungen.",
        "not_admin": "❌ Du bist kein Admin!",
        "no_reply": "❌ Antworte auf die Nachricht des Benutzers.",
        "pinned": "📌 Nachricht angepinnt.",
        "unpinned": "📌 Nachricht gelöst.",
        "lang_changed": "✅ Sprache geändert: Deutsch 🇩🇪",
    },
    "pt": {
        "start": (
            "👋 <b>Olá!</b>\n\n"
            "🤖 <b>jarvis help bot</b> — o melhor bot para gerenciar seu grupo!\n\n"
            "➕ Adicione-o ao seu grupo e dê permissões de <b>Admin</b>!\n\n"
            "❓ <b>COMANDOS DISPONÍVEIS?</b>\n"
            "Envie /help para ver a lista de comandos!"
        ),
        "help": (
            "📋 <b>LISTA DE COMANDOS</b>\n\n"
            "👮 <b>Comandos de administrador:</b>\n"
            "/ban — Banir usuário\n"
            "/unban — Desbanir usuário\n"
            "/kick — Expulsar do grupo\n"
            "/mute — Silenciar usuário\n"
            "/unmute — Desmutar usuário\n"
            "/warn — Avisar usuário\n"
            "/unwarn — Remover aviso\n"
            "/warns — Ver avisos\n"
            "/pin — Fixar mensagem\n"
            "/unpin — Desfixar mensagem\n\n"
            "👥 <b>Comandos de grupo:</b>\n"
            "/rules — Regras do grupo\n"
            "/info — Informações do grupo\n"
            "/members — Contagem de membros\n\n"
            "🔤 <b>Comandos gerais:</b>\n"
            "/start — Iniciar o bot\n"
            "/help — Ajuda\n"
            "/language — Mudar idioma\n"
            "/id — Obter ID\n"
        ),
        "rules": (
            "📜 <b>REGRAS DO GRUPO</b>\n\n"
            "1️⃣ Seja respeitoso\n"
            "2️⃣ Sem spam ou propaganda\n"
            "3️⃣ Sem linguagem ofensiva\n"
            "4️⃣ Fique no assunto\n"
            "5️⃣ Não compartilhe informações privadas\n\n"
            "⚠️ Infratores recebem avisos, depois ban "
            f"({WARN_LIMIT} avisos)."
        ),
        "welcome": "👋 Bem-vindo, {name}! Leia as regras: /rules",
        "banned": "🚫 {name} foi banido.",
        "unbanned": "✅ {name} foi desbanido.",
        "kicked": "👢 {name} foi expulso.",
        "muted": "🔇 {name} foi silenciado.",
        "unmuted": "🔊 {name} pode falar novamente.",
        "warned": "⚠️ {name} recebeu um aviso! ({count}/{limit})\nMotivo: {reason}",
        "warned_banned": "🚫 {name} foi banido após {limit} avisos!",
        "unwarn": "✅ Avisos de {name} foram limpos.",
        "no_warns": "✅ {name} não tem avisos.",
        "current_warns": "⚠️ {name}: {count}/{limit} avisos.",
        "not_admin": "❌ Você não é admin!",
        "no_reply": "❌ Responda à mensagem do usuário.",
        "pinned": "📌 Mensagem fixada.",
        "unpinned": "📌 Mensagem desafixada.",
        "lang_changed": "✅ Idioma alterado: Português 🇵🇹",
    },
    "ar": {
        "start": (
            "👋 <b>مرحباً!</b>\n\n"
            "🤖 <b>jarvis help bot</b> — أفضل بوت لإدارة مجموعتك!\n\n"
            "➕ أضفه إلى مجموعتك ومنحه صلاحيات <b>Admin</b>!\n\n"
            "❓ <b>الأوامر المتاحة؟</b>\n"
            "أرسل /help لرؤية قائمة الأوامر!"
        ),
        "help": (
            "📋 <b>قائمة الأوامر</b>\n\n"
            "👮 <b>أوامر المدير:</b>\n"
            "/ban — حظر مستخدم\n"
            "/unban — فك الحظر عن مستخدم\n"
            "/kick — طرد من المجموعة\n"
            "/mute — كتم مستخدم\n"
            "/unmute — إلغاء الكتم\n"
            "/warn — تحذير مستخدم\n"
            "/unwarn — إزالة التحذير\n"
            "/warns — عرض التحذيرات\n"
            "/pin — تثبيت رسالة\n"
            "/unpin — إلغاء تثبيت رسالة\n\n"
            "👥 <b>أوامر المجموعة:</b>\n"
            "/rules — قواعد المجموعة\n"
            "/info — معلومات المجموعة\n"
            "/members — عدد الأعضاء\n\n"
            "🔤 <b>الأوامر العامة:</b>\n"
            "/start — تشغيل البوت\n"
            "/help — المساعدة\n"
            "/language — تغيير اللغة\n"
            "/id — الحصول على المعرف\n"
        ),
        "rules": (
            "📜 <b>قواعد المجموعة</b>\n\n"
            "1️⃣ كن محترماً\n"
            "2️⃣ لا سبام ولا إعلانات\n"
            "3️⃣ لا تستخدم لغة مسيئة\n"
            "4️⃣ ابق في الموضوع\n"
            "5️⃣ لا تشارك معلومات خاصة عن الآخرين\n\n"
            "⚠️ المخالفون يتلقون تحذيرات ثم حظر "
            f"({WARN_LIMIT} تحذيرات)."
        ),
        "welcome": "👋 مرحبًا، {name}! اقرأ القواعد: /rules",
        "banned": "🚫 تم حظر {name}.",
        "unbanned": "✅ تم رفع الحظر عن {name}.",
        "kicked": "👢 تم طرد {name} من المجموعة.",
        "muted": "🔇 تم كتم {name}.",
        "unmuted": "🔊 يمكن لـ {name} التحدث مرة أخرى.",
        "warned": "⚠️ تم تحذير {name}! ({count}/{limit})\nالسبب: {reason}",
        "warned_banned": "🚫 تم حظر {name} بعد {limit} تحذيرات!",
        "unwarn": "✅ تم مسح تحذيرات {name}.",
        "no_warns": "✅ لا توجد تحذيرات لـ {name}.",
        "current_warns": "⚠️ {name}: {count}/{limit} تحذيرات.",
        "not_admin": "❌ أنت لست مشرفاً!",
        "no_reply": "❌ الرد على رسالة المستخدم.",
        "pinned": "📌 تم تثبيت الرسالة.",
        "unpinned": "📌 تم إلغاء تثبيت الرسالة.",
        "lang_changed": "✅ تم تغيير اللغة: العربية 🇸🇦",
    },
}


# ========================
# HELPER FUNCTIONS
# ========================

def t(chat_id: int, key: str) -> str:
    """Joriy chat tilida matnni qaytaradi."""
    lang = chat_lang.get(chat_id, "uz")
    return TEXTS[lang].get(key, TEXTS["uz"][key])


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Foydalanuvchi admin yoki yo'qligini tekshiradi."""
    user = update.effective_user
    chat = update.effective_chat
    if chat.type == "private":
        return True
    member = await context.bot.get_chat_member(chat.id, user.id)
    return member.status in ("administrator", "creator")


def start_keyboard() -> InlineKeyboardMarkup:
    """Rasmda ko'rsatilgan inline tugmalar."""
    keyboard = [
        [
            InlineKeyboardButton("🌐 Guruh", url=GROUP_LINK),
            InlineKeyboardButton("📢 Kanal", url=CHANNEL_LINK),
        ],
     
        [
            InlineKeyboardButton("🆘 Yordam", url=SUPPORT_LINK),
            InlineKeyboardButton("ℹ️ Batafsil", callback_data="batafsil"),
        ],
        [
            InlineKeyboardButton("🌍 Tilni o'zgartirish", callback_data="language"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_start_keyboard(bot_username: str | None = None) -> InlineKeyboardMarkup:
    """Build start keyboard; include Add-bot-to-group deep link when username available."""
    keyboard = [
        [
            InlineKeyboardButton("🌐 Guruh", url=GROUP_LINK),
            InlineKeyboardButton("📢 Kanal", url=CHANNEL_LINK),
        ],
        [
            InlineKeyboardButton("🆘 Yordam", url=SUPPORT_LINK),
            InlineKeyboardButton("ℹ️ Batafsil", callback_data="batafsil"),
        ],
        [
            InlineKeyboardButton("🌍 Tilni o'zgartirish", callback_data="language"),
        ],
    ]

    if bot_username:
        # deep-link to add bot to group
        bot_add_url = f"https://t.me/{bot_username}?startgroup=true"
        keyboard.insert(0, [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=bot_add_url)])

    return InlineKeyboardMarkup(keyboard)


def language_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский",   callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English",   callback_data="lang_en"),
        ],
        [
            InlineKeyboardButton("🇹🇷 Türkçe",         callback_data="lang_tr"),
            InlineKeyboardButton("🇪🇸 Español",        callback_data="lang_es"),
            InlineKeyboardButton("🇫🇷 Français",       callback_data="lang_fr"),
        ],
        [
            InlineKeyboardButton("🇩🇪 Deutsch",        callback_data="lang_de"),
            InlineKeyboardButton("🇵🇹 Português",      callback_data="lang_pt"),
            InlineKeyboardButton("🇸🇦 العربية",      callback_data="lang_ar"),
        ],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_start")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ========================
# COMMAND HANDLERS
# ========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    me = await context.bot.get_me()
    await update.message.reply_text(
        t(chat_id, "start"),
        parse_mode=ParseMode.HTML,
        reply_markup=build_start_keyboard(me.username),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        t(chat_id, "help"),
        parse_mode=ParseMode.HTML,
    )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        t(chat_id, "rules"),
        parse_mode=ParseMode.HTML,
    )


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        await update.message.reply_text(
            f"👤 <b>{target.full_name}</b>\n"
            f"🆔 User ID: <code>{target.id}</code>\n"
            f"💬 Chat ID: <code>{chat.id}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            f"👤 <b>{user.full_name}</b>\n"
            f"🆔 User ID: <code>{user.id}</code>\n"
            f"💬 Chat ID: <code>{chat.id}</code>",
            parse_mode=ParseMode.HTML,
        )


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    count = await context.bot.get_chat_member_count(chat.id)
    text = (
        f"ℹ️ <b>Guruh ma'lumotlari</b>\n\n"
        f"📛 Nomi: {chat.title}\n"
        f"🆔 ID: <code>{chat.id}</code>\n"
        f"👥 A'zolar: {count}\n"
        f"🔗 Username: @{chat.username}" if chat.username else ""
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    count = await context.bot.get_chat_member_count(chat.id)
    await update.message.reply_text(
        f"👥 Guruhda <b>{count}</b> a'zo bor.", parse_mode=ParseMode.HTML
    )


async def language_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🌍 <b>Tilni tanlang / Выберите язык / Choose language:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=language_keyboard(),
    )


async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a chat invite link (requires bot to be admin in the chat)."""
    chat = update.effective_chat
    chat_id = chat.id
    if chat.type == "private":
        await update.message.reply_text("❌ Bu buyruq guruh ichida ishlaydi. Guruhda yuboring.")
        return
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "not_admin"))
        return
    try:
        invite_link = await context.bot.create_chat_invite_link(chat_id)
        await update.message.reply_text(
            f"🔗 Taklif linki: {invite_link.invite_link}", parse_mode=ParseMode.HTML
        )
    except Exception as exc:
        logger.exception("Invite link yaratishda xato:")
        await update.message.reply_text("❌ Taklif linkini yaratib bo'lmadi. Botga admin huquqlarini tekshiring.")


async def bot_chat_member_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Bot guruhga qo'shilganda xabar yuboradi."""
    chat = update.effective_chat
    old_status = update.my_chat_member.old_chat_member.status
    new_status = update.my_chat_member.new_chat_member.status

    if old_status in ("left", "kicked") and new_status in ("member", "administrator"):
        me = await context.bot.get_me()
        await context.bot.send_message(
            chat.id,
            t(chat.id, "start"),
            parse_mode=ParseMode.HTML,
            reply_markup=build_start_keyboard(me.username),
        )


# ========================
# ADMIN COMMANDS
# ========================

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "not_admin"))
        return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "no_reply"))
        return
    target = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(chat_id, target.id)
    await update.message.reply_text(
        t(chat_id, "banned").format(name=target.full_name),
        parse_mode=ParseMode.HTML,
    )


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "not_admin"))
        return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "no_reply"))
        return
    target = update.message.reply_to_message.from_user
    await context.bot.unban_chat_member(chat_id, target.id)
    await update.message.reply_text(
        t(chat_id, "unbanned").format(name=target.full_name),
        parse_mode=ParseMode.HTML,
    )


async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "not_admin"))
        return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "no_reply"))
        return
    target = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(chat_id, target.id)
    await context.bot.unban_chat_member(chat_id, target.id)  # kick = ban + unban
    await update.message.reply_text(
        t(chat_id, "kicked").format(name=target.full_name),
        parse_mode=ParseMode.HTML,
    )


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "not_admin"))
        return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "no_reply"))
        return
    target = update.message.reply_to_message.from_user

    # Args: /mute 10m  /mute 1h  /mute 1d  (yoki abadiy)
    until = None
    if context.args:
        arg = context.args[0]
        try:
            if arg.endswith("m"):
                until = datetime.now() + timedelta(minutes=int(arg[:-1]))
            elif arg.endswith("h"):
                until = datetime.now() + timedelta(hours=int(arg[:-1]))
            elif arg.endswith("d"):
                until = datetime.now() + timedelta(days=int(arg[:-1]))
        except ValueError:
            pass

    await context.bot.restrict_chat_member(
        chat_id,
        target.id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until,
    )
    duration = f" ({context.args[0]})" if until else ""
    await update.message.reply_text(
        t(chat_id, "muted").format(name=target.full_name) + duration,
        parse_mode=ParseMode.HTML,
    )


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "not_admin"))
        return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "no_reply"))
        return
    target = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(
        chat_id,
        target.id,
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        ),
    )
    await update.message.reply_text(
        t(chat_id, "unmuted").format(name=target.full_name),
        parse_mode=ParseMode.HTML,
    )


async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "not_admin"))
        return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "no_reply"))
        return
    target = update.message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "Sabab ko'rsatilmagan"

    warns.setdefault(chat_id, {})
    warns[chat_id][target.id] = warns[chat_id].get(target.id, 0) + 1
    count = warns[chat_id][target.id]

    if count >= WARN_LIMIT:
        await context.bot.ban_chat_member(chat_id, target.id)
        warns[chat_id][target.id] = 0
        await update.message.reply_text(
            t(chat_id, "warned_banned").format(name=target.full_name, limit=WARN_LIMIT),
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            t(chat_id, "warned").format(
                name=target.full_name, count=count, limit=WARN_LIMIT, reason=reason
            ),
            parse_mode=ParseMode.HTML,
        )


async def unwarn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "not_admin"))
        return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "no_reply"))
        return
    target = update.message.reply_to_message.from_user
    warns.setdefault(chat_id, {})
    warns[chat_id][target.id] = 0
    await update.message.reply_text(
        t(chat_id, "unwarn").format(name=target.full_name),
        parse_mode=ParseMode.HTML,
    )


async def show_warns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "no_reply"))
        return
    target = update.message.reply_to_message.from_user
    count = warns.get(chat_id, {}).get(target.id, 0)
    if count == 0:
        await update.message.reply_text(
            t(chat_id, "no_warns").format(name=target.full_name),
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            t(chat_id, "current_warns").format(
                name=target.full_name, count=count, limit=WARN_LIMIT
            ),
            parse_mode=ParseMode.HTML,
        )


async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "not_admin"))
        return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "no_reply"))
        return
    await update.message.reply_to_message.pin()
    await update.message.reply_text(t(chat_id, "pinned"))


async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "not_admin"))
        return
    await context.bot.unpin_all_chat_messages(chat_id)
    await update.message.reply_text(t(chat_id, "unpinned"))


# ========================
# NEW MEMBER WELCOME
# ========================

async def welcome_new_member(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    chat_id = update.effective_chat.id
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        name = member.full_name
        await update.message.reply_text(
            t(chat_id, "welcome").format(name=name),
            parse_mode=ParseMode.HTML,
        )


# ========================
# CALLBACK QUERY (INLINE BUTTONS)
# ========================

async def callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    chat_id = query.message.chat_id
    await query.answer()

    if query.data == "language":
        await query.edit_message_text(
            "🌍 <b>Tilni tanlang / Выберите язык / Choose language / اختر اللغة / Sprache auswählen</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=language_keyboard(),
        )

    elif query.data.startswith("lang_"):
        lang_code = query.data.split("_", 1)[1]
        if lang_code in TEXTS:
            chat_lang[chat_id] = lang_code
            await query.edit_message_text(
                t(chat_id, "lang_changed"),
                parse_mode=ParseMode.HTML,
            )
        else:
            await query.edit_message_text(
                "❌ Bu til hozircha qo'llab-quvvatlanmaydi.",
                parse_mode=ParseMode.HTML,
            )

    elif query.data == "batafsil":
        await query.edit_message_text(
            "ℹ️ <b>Batafsil ma'lumot</b>\n\n"
            "GroupHelpBot — guruhlaringizni professional darajada boshqarish uchun yaratilgan.\n\n"
            "✅ Ban/kick/mute\n"
            "✅ Ogohlantirish tizimi\n"
            "✅ Xush kelibsiz xabarlar\n"
            "✅ Ko'p tilli qo'llab-quvvatlash\n"
            "✅ Admin huquqlarini tekshirish\n\n"
            "Savollar uchun: /help",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_start")]]
            ),
        )

    elif query.data == "back_start":
        me = await context.bot.get_me()
        await query.edit_message_text(
            t(chat_id, "start"),
            parse_mode=ParseMode.HTML,
            reply_markup=build_start_keyboard(me.username),
        )


# ========================
# MAIN
# ========================

def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN":
        logger.error(
            "BOT_TOKEN noto'g'ri konfiguratsiya qilingan. "
            "Iltimos, script ichidagi BOT_TOKEN yoki BOT_TOKEN muhit o'zgaruvchisini sozlang."
        )
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # General
    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     help_command))
    app.add_handler(CommandHandler("rules",    rules))
    app.add_handler(CommandHandler("id",       get_id))
    app.add_handler(CommandHandler("info",     info))
    app.add_handler(CommandHandler("members",  members))
    app.add_handler(CommandHandler("language", language_cmd))
    app.add_handler(CommandHandler("invite", invite))
    app.add_handler(
        ChatMemberHandler(bot_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER)
    )

    # Admin
    app.add_handler(CommandHandler("ban",      ban))
    app.add_handler(CommandHandler("unban",    unban))
    app.add_handler(CommandHandler("kick",     kick))
    app.add_handler(CommandHandler("mute",     mute))
    app.add_handler(CommandHandler("unmute",   unmute))
    app.add_handler(CommandHandler("warn",     warn))
    app.add_handler(CommandHandler("unwarn",   unwarn))
    app.add_handler(CommandHandler("warns",    show_warns))
    app.add_handler(CommandHandler("pin",      pin))
    app.add_handler(CommandHandler("unpin",    unpin))

    # New members
    app.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member)
    )

    # Inline buttons
    app.add_handler(CallbackQueryHandler(callback_handler))

    logger.info("Bot ishga tushdi...")
    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as exc:
        logger.exception("Bot ishlamayapti:")


if __name__ == "__main__":
    main()
