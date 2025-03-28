import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# Token do seu bot (substitua pelo token gerado pelo BotFather)
TOKEN = "7613908238:AAFaavgcKhxOzxUOQ337P-yxDbqi7XVDchI"

# URL do endpoint onde o formulário será enviado
form_endpoint = "https://exemplo.com/endpoint"  # Substitua pela URL do seu endpoint de formulário

# Lista de IDs de usuários autorizados (substitua pelos IDs corretos)
authorized_user_ids = [6462985710, 987654321]  # Exemplo de IDs de usuários autorizados

# Emails predefinidos
PREDEFINED_EMAILS = [
    "gabrielgehren16@gmail.com",
    "tatipimenta13@gmail.com"
]

# Apartamentos predefinidos
PREDEFINED_APARTMENTS = [
    "402 B"
]

# Nomes predefinidos
PREDEFINED_NAMES = [
    "Gabriel Gehren",
    "Thatiana Pimenta"
]

# Função para verificar se o usuário é autorizado pelo ID
async def check_authorized(update: Update) -> bool:
    user_id = update.message.from_user.id if update.message.from_user else None
    return user_id in authorized_user_ids

# Função para validar o formato do e-mail
def is_valid_email(email: str) -> bool:
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

# Função para responder ao comando /start
async def start(update: Update, context: CallbackContext) -> None:
    if not await check_authorized(update):
        await update.message.reply_text("Você não pode estar aqui, mete o pé. Só falo com os mídias.")
        return

    user_id = update.message.from_user.id
    print(f"ID do usuário: {user_id}")

    await update.message.reply_text("Olá! Eu sou teu pai. Esse bot foi criado pra te ajudar a enviar o comprovante da imobiliária no dia certo, JÁ QUE TU ESQUECE.")
    await update.message.reply_text("Envie o comprovante do pagamento do teu condominio para eu continuar te enchendo.")

# Função para responder a imagens
async def handle_image(update: Update, context: CallbackContext) -> None:
    if not await check_authorized(update):
        await update.message.reply_text("Você não pode estar aqui, mete o pé. Só falo com os mídias.")
        return

    if update.message.photo:
        await show_name_options(update, context)
        context.user_data['photo'] = update.message.photo[-1].file_id
        context.user_data['step'] = 1
    else:
        await update.message.reply_text("Você é burro cara? Anexe primeiro o comprovante, não quero falar com você.")

# Função para exibir as opções de nome
async def show_name_options(update: Update, context: CallbackContext) -> None:
    keyboard = []
    for name in PREDEFINED_NAMES:
        keyboard.append([InlineKeyboardButton(name, callback_data=f"name_{name}")])
    keyboard.append([InlineKeyboardButton("Outro", callback_data="name_outro")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.reply_text("Por favor, escolha seu nome:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Por favor, escolha seu nome:", reply_markup=reply_markup)

# Função para coletar dados adicionais
async def collect_data(update: Update, context: CallbackContext) -> None:
    if not await check_authorized(update):
        await update.message.reply_text("Você não pode estar aqui, mete o pé. Só falo com os mídias.")
        return

    if 'photo' not in context.user_data:
        await update.message.reply_text("Você é burro cara? Anexe primeiro o comprovante, não quero falar com você.")
        return

    step = context.user_data.get('step', 0)

    if step == 1:
        # Coletando o nome do locatário
        context.user_data['nome'] = update.message.text.strip()
        await show_email_options(update, context)
        context.user_data['step'] = 2

    elif step == 1.5:  # Novo step para coleta de nome personalizado
        context.user_data['nome'] = update.message.text.strip()
        await show_email_options(update, context)
        context.user_data['step'] = 2

    elif step == 2:
        # Coletando o e-mail e validando
        email = update.message.text.strip().lower()  # Formatar para minúsculas
        if not is_valid_email(email):
            await update.message.reply_text("E-mail inválido! Por favor, envie um e-mail válido:")
            return
        context.user_data['email'] = email
        await show_building_options(update, context)

    elif step == 2.5:  # Novo step para coleta de email personalizado
        email = update.message.text.strip().lower()
        if not is_valid_email(email):
            await update.message.reply_text("E-mail inválido! Por favor, envie um e-mail válido:")
            return
        context.user_data['email'] = email
        await show_building_options(update, context)

    elif step == 3:
        # Coletando o número do edifício
        building_number = update.message.text.strip()
        try:
            building_number = int(building_number)
            if 1 <= building_number <= len(buildings_list):
                context.user_data['edificio'] = buildings_list[building_number - 1]
                await update.message.reply_text(f"Edifício selecionado: {context.user_data['edificio']}. Agora, me passe o número do apartamento:")
                context.user_data['step'] = 4
            else:
                await update.message.reply_text(f"Por favor, escolha um número válido entre 1 e {len(buildings_list)}.")
        except ValueError:
            await update.message.reply_text("Por favor, digite um número válido para o edifício:")

    elif step == 4:
        # Coletando o número do apartamento
        context.user_data['apartamento'] = update.message.text.strip()
        await update.message.reply_text("Comprovante recebido! Agora, vamos confirmar os dados:")
        await show_summary(update, context)

    elif step == 4.5:  # Novo step para coleta de apartamento personalizado
        context.user_data['apartamento'] = update.message.text.strip()
        await update.message.reply_text("Comprovante recebido! Agora, vamos confirmar os dados:")
        await show_summary(update, context)

    elif step == 5:
        # Caso o usuário responda com sim, enviaremos os dados para o endpoint
        if update.message.text.lower() == "sim":
            await send_to_endpoint(update, context)
        else:
            try:
                correction_number = int(update.message.text.strip())
                if 1 <= correction_number <= 5:
                    if correction_number == 1:
                        await show_name_options(update, context)
                        context.user_data['step'] = 1
                    elif correction_number == 2:
                        await show_email_options(update, context)
                        context.user_data['step'] = 2
                    elif correction_number == 3:
                        await show_building_options(update, context)
                        context.user_data['step'] = 3
                    elif correction_number == 4:
                        await show_apartment_options(update, context)
                        context.user_data['step'] = 4
                    elif correction_number == 5:
                        await update.message.reply_text("Por favor, envie o novo comprovante:")
                        context.user_data['step'] = 0.5
                else:
                    await update.message.reply_text("Por favor, digite um número válido entre 1 e 5.")
            except ValueError:
                await update.message.reply_text("Por favor, digite um número válido entre 1 e 5.")

    elif step == 0.5:  # Novo step para alteração do comprovante
        if update.message.photo:
            context.user_data['photo'] = update.message.photo[-1].file_id
            await update.message.reply_text("Comprovante atualizado! Vamos confirmar os dados novamente:")
            await show_summary(update, context)
        else:
            await update.message.reply_text("Você é burro cara? Anexe o comprovante, não quero falar com você.")

    elif step == 6:
        # Editando apenas o nome
        context.user_data['nome'] = update.message.text.strip()
        await update.message.reply_text("Nome atualizado! Vamos confirmar os dados novamente:")
        await show_summary(update, context)

# Função para exibir as opções de edifícios
async def show_building_options(update: Update, context: CallbackContext) -> None:
    global buildings_list
    buildings_list = ["Residencial Reserva do Arvoredo"]  # Adicione mais edifícios se necessário

    keyboard = [
        [InlineKeyboardButton(building, callback_data=str(i))] for i, building in enumerate(buildings_list)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Verifica se é uma callback query ou mensagem normal
    if update.callback_query:
        await update.callback_query.message.reply_text("Por favor, escolha o edifício:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Por favor, escolha o edifício:", reply_markup=reply_markup)

# Função para exibir as opções de apartamento
async def show_apartment_options(update: Update, context: CallbackContext) -> None:
    keyboard = []
    for apartment in PREDEFINED_APARTMENTS:
        keyboard.append([InlineKeyboardButton(apartment, callback_data=f"apartment_{apartment}")])
    keyboard.append([InlineKeyboardButton("Outro", callback_data="apartment_outro")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.reply_text("Por favor, escolha o número do apartamento:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Por favor, escolha o número do apartamento:", reply_markup=reply_markup)

# Função para exibir o resumo para confirmação
async def show_summary(update: Update, context: CallbackContext) -> None:
    nome = context.user_data.get('nome')
    email = context.user_data.get('email')
    edificio = context.user_data.get('edificio')
    apartamento = context.user_data.get('apartamento')
    photo_file_id = context.user_data.get('photo')

    # Obtém o username do usuário
    if update.callback_query:
        username = update.callback_query.from_user.username
    else:
        username = update.message.from_user.username

    summary = f"Resumo dos dados:\n"
    summary += f"1. Nome do locatário: {nome}\n"
    summary += f"2. E-mail: {email}\n"
    summary += f"3. Edifício: {edificio}\n"
    summary += f"4. Número do apartamento: {apartamento}\n"
    summary += "Se algum dado estiver errado, digite o número do dado para corrigir (1, 2, 3, 4, 5). Para enviar, digite 'sim'."

    if update.callback_query:
        # Envia o comprovante
        await update.callback_query.message.reply_photo(photo=photo_file_id, caption="Comprovante anexado:")
        # Envia o resumo
        await update.callback_query.message.reply_text(summary, parse_mode="Markdown")
    else:
        # Envia o comprovante
        await update.message.reply_photo(photo=photo_file_id, caption="Comprovante anexado:")
        # Envia o resumo
        await update.message.reply_text(summary, parse_mode="Markdown")
    
    context.user_data['step'] = 5

# Função para enviar dados para o endpoint
async def send_to_endpoint(update: Update, context: CallbackContext) -> None:
    nome = context.user_data.get('nome')
    email = context.user_data.get('email')
    edificio = context.user_data.get('edificio')
    apartamento = context.user_data.get('apartamento')
    photo_file_id = context.user_data.get('photo')

    file = await update.message.bot.get_file(photo_file_id)
    photo_url = file.file_url

    data = {
        'nome': nome,
        'email': email,
        'edificio': edificio,
        'apartamento': apartamento,
        'comprovante': photo_url
    }

    try:
        response = requests.post(form_endpoint, data=data)
        if response.status_code == 200:
            await update.message.reply_text("Comprovante enviado com sucesso!")
        else:
            await update.message.reply_text("Houve um erro ao enviar o comprovante, tente novamente mais tarde.")
    except requests.RequestException as e:
        await update.message.reply_text(f"Erro ao tentar enviar os dados: {e}")

    context.user_data.clear()

# Função para exibir as opções de email
async def show_email_options(update: Update, context: CallbackContext) -> None:
    keyboard = []
    for email in PREDEFINED_EMAILS:
        keyboard.append([InlineKeyboardButton(email, callback_data=f"email_{email}")])
    keyboard.append([InlineKeyboardButton("Outro", callback_data="email_outro")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.reply_text("Por favor, escolha seu e-mail:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Por favor, escolha seu e-mail:", reply_markup=reply_markup)

# Função para responder a interações com os botões
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data.startswith("name_"):
        name = query.data.replace("name_", "")
        if name == "outro":
            await query.edit_message_text(text="Por favor, digite seu nome:")
            context.user_data['step'] = 1.5
        else:
            context.user_data['nome'] = name
            await query.edit_message_text(text=f"Nome selecionado: {name}")
            await show_email_options(update, context)
            context.user_data['step'] = 2
    elif query.data.startswith("email_"):
        email = query.data.replace("email_", "")
        if email == "outro":
            await query.edit_message_text(text="Por favor, digite seu e-mail:")
            context.user_data['step'] = 2.5
        else:
            context.user_data['email'] = email
            await query.edit_message_text(text=f"E-mail selecionado: {email}")
            await show_building_options(update, context)
    elif query.data.startswith("apartment_"):
        apartment = query.data.replace("apartment_", "")
        if apartment == "outro":
            await query.edit_message_text(text="Por favor, digite o número do apartamento:")
            context.user_data['step'] = 4.5
        else:
            context.user_data['apartamento'] = apartment
            await query.edit_message_text(text=f"Apartamento selecionado: {apartment}")
            await query.message.reply_text("Comprovante recebido! Agora, vamos confirmar os dados:")
            await show_summary(update, context)
    else:
        # Lógica existente para seleção de edifício
        building_index = int(query.data)
        context.user_data['edificio'] = buildings_list[building_index]
        
        await query.edit_message_text(text=f"Edifício selecionado: {context.user_data['edificio']}")
        await show_apartment_options(update, context)
        context.user_data['step'] = 4

# Função para responder a mensagens de texto (quando não for imagem)
async def echo(update: Update, context: CallbackContext) -> None:
    if not await check_authorized(update):
        await update.message.reply_text("Você não pode estar aqui, mete o pé. Só falo com os mídias.")
        return

    if 'photo' not in context.user_data:
        await update.message.reply_text("Você é burro cara? Anexe primeiro o comprovante, não quero falar com você.")
    elif not update.message.photo:
        await update.message.reply_text("Você é burro cara? Anexe primeiro o comprovante, não quero falar com você.")

# Configuração do bot
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))  # Captura apenas imagens
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data))  # Coleta dados adicionais
    app.add_handler(CallbackQueryHandler(button))  # Adiciona o handler para os botões

    app.run_polling()

if __name__ == "__main__":
    main()
