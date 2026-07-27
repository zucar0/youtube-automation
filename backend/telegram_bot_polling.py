from telegram.ext import Application, CommandHandler, MessageHandler, filters
from app.config import settings
from app.services.telegram_bot_logic import start, manejar_mensaje

app = Application.builder().token(settings.telegram_bot_token_dev).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

if __name__ == "__main__":
    app.run_polling()