import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Настройки
TOKEN = '8309970362:AAEuRpJnhtAqOJcdmjr36GMqQfZR92bJ58Q'  # Замените на ваш токен
ADMIN_CHAT_ID = 5135791667 # Ваш chat_id

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранилище сообщений
message_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Отправь мне сообщение, и я перешлю его админу."
    )

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пересылает сообщение пользователя админу"""
    try:
        user = update.effective_user
        chat_id = update.message.chat_id
        message_id = update.message.message_id
        
        # Формируем подпись
        caption = (
            f"Сообщение от {user.full_name} "
            f"(@{user.username or 'нет'}, ID: {user.id})"
        )
        
        # Пересылаем сообщение админу
        if update.message.text:
            forwarded_msg = await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"{caption}\n\n{update.message.text}"
            )
        else:
            # Для медиа-сообщений
            forwarded_msg = await update.message.forward(ADMIN_CHAT_ID)
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=caption,
                reply_to_message_id=forwarded_msg.message_id
            )
        
        # Сохраняем соответствие
        message_store[forwarded_msg.message_id] = (chat_id, message_id)
        
        # Подтверждение пользователю
        await update.message.reply_text("✅ Ваше сообщение отправлено админу. Ожидайте ответа.")
    
    except Exception as e:
        logger.error(f"Ошибка при пересылке: {e}")
        await update.message.reply_text("⚠️ Не удалось отправить сообщение админу.")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает ответ админа"""
    try:
        if update.effective_chat.id != ADMIN_CHAT_ID:
            return
            
        if not update.message.reply_to_message:
            return
            
        replied_to_id = update.message.reply_to_message.message_id
        
        if replied_to_id not in message_store:
            await update.message.reply_text("❌ Это не ответ на сообщение пользователя.")
            return
            
        user_chat_id, original_message_id = message_store[replied_to_id]
        
        await context.bot.send_message(
            chat_id=user_chat_id,
            text=f"📨 Ответ от поддержки:\n\n{update.message.text}"
        )
        await update.message.reply_text("✅ Ответ отправлен пользователю.")
        
    except Exception as e:
        logger.error(f"Ошибка при ответе админа: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")

def main() -> None:
    """Запуск бота"""
    try:
        application = Application.builder().token(TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(
            filters.ALL & ~filters.COMMAND & ~filters.Chat(ADMIN_CHAT_ID),
            forward_to_admin
        ))
        application.add_handler(MessageHandler(
            filters.TEXT & filters.Chat(ADMIN_CHAT_ID) & filters.REPLY,
            handle_admin_reply
        ))

        logger.info("Бот запущен")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")

if __name__ == '__main__':
    main()