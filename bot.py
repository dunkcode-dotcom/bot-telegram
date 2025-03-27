from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Token do seu bot (substitua pelo token gerado pelo BotFather)
TOKEN = "7613908238:AAFaavgcKhxOzxUOQ337P-yxDbqi7XVDchI"

# Função para responder ao comando /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Olá! Eu sou um bot do Telegram. Como posso ajudar?")

# Função para responder a mensagens de texto
def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f"Você disse: {update.message.text}")

# Configuração do bot
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Adicionando comandos
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Iniciando o bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
