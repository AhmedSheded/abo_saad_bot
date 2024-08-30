api_token = '7263508017:AAH1r3HXqeeIoROsDVJ_xUITNYZU_uau-5Q'
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from processing import process_data


# aaa = """
# اذا لم يكن الأستاذ عبدالله من يستخدم البوت يرجى ارسال هذه الرسالة له
#
# السلام عليكم أستاذ عبدالله تقدر تتواصل معايا عبر واتساب او تليجرام على الرقم دا لسرعة التواصل
# متأسف لكن مش مسموح ابعت اي تواصل خارجي في مستقل
# +201015415017
# """
CHOOSING_TEMPLATE, ASKING_QUESTION, ASKING_TEXT1, ASKING_PHOTOS = range(4)

# Ensure the downloads directory exis
downloades_path = os.path.join(os.getcwd(), 'downloads')
if not os.path.exists(downloades_path):
    os.makedirs(downloades_path)


async def start(update: Update, context: CallbackContext) -> int:
    # Reset user data to ensure a clean state
    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton("VIP", callback_data='VIP')],
        [InlineKeyboardButton("مميز", callback_data='مميز')],
        [InlineKeyboardButton("مجاني", callback_data='مجاني')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('قم بإختيار قالب:', reply_markup=reply_markup)
    return CHOOSING_TEMPLATE


async def choose_template(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    context.user_data['template'] = query.data
    await query.answer()
    await query.edit_message_text(text=f"قمت باختيار: {query.data}. الان ماهي لغة الوصف الموجود.")

    keyboard = [
        [InlineKeyboardButton("English", callback_data='English')],
        [InlineKeyboardButton("Arabic", callback_data='Arabic')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('اختيار لغة الوصف:', reply_markup=reply_markup)
    return ASKING_QUESTION


async def handle_choice(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    context.user_data['choice'] = query.data
    await query.answer()
    await query.message.reply_text('ماهو الوصف :')
    return ASKING_TEXT1


async def handle_text1(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    context.user_data['text1'] = text
    await update.message.reply_text('شكرا لك الان قم بارسال الصور (من 1 إلى 2 صور):')
    return ASKING_PHOTOS


async def handle_photos(update: Update, context: CallbackContext) -> int:
    photos = update.message.photo
    if 'photos' not in context.user_data:
        context.user_data['photos'] = {}

    # Save the file ID of the highest resolution photo
    highest_resolution_photo = max(photos, key=lambda p: p.width * p.height)
    file_id = highest_resolution_photo.file_id
    if file_id not in context.user_data['photos']:
        context.user_data['photos'][file_id] = None

    # If we have received 3 photos, move to processing
    if len(context.user_data['photos']) >= 2:
        await update.message.reply_text("تم استلام الصورتين. جاري معالجة الصور.")
        return await done(update, context)

    # Inform the user about the received photos
    await update.message.reply_text(
        "تم استلام صورة. إذا كنت ترغب في إرسال المزيد (إجمالي حتى 2)، يرجى إرسالها. أو أرسل /done إذا انتهيت.")
    return ASKING_PHOTOS


async def save_photos(context: CallbackContext, update: Update):
    if not os.path.exists(downloades_path):
        os.makedirs(downloades_path)

    downloaded_file_ids = set()
    for file_id in context.user_data['photos']:
        if file_id not in downloaded_file_ids:
            file_path = os.path.join(downloades_path, f"{file_id}.jpg")
            if context.user_data['photos'][file_id] is None:
                new_file = await context.bot.get_file(file_id)
                await new_file.download_to_drive(file_path)
                context.user_data['photos'][file_id] = file_path
            downloaded_file_ids.add(file_id)


async def process_and_send_photo(context: CallbackContext, update: Update):
    template = context.user_data.get('template')
    choice = context.user_data.get('choice')
    text1 = context.user_data.get('text1')
    photos = [path for path in context.user_data['photos'].values() if path]

    # Process data and get the photo path
    photo_path, post = process_data(template, choice, text1, photos)

    # Send the processed photo to the user
    with open(photo_path, 'rb') as photo:
        await update.message.reply_photo(photo, caption="Here is your processed photo.")
    await update.message.reply_text(post)
    # await update.message.reply_text(aaa)

    # Remove the downloads folder after sending the photo
    # if os.path.exists(downloades_path):
    #     for file in os.listdir(downloades_path):
    #         os.remove(os.path.join(downloades_path, file))
    #     os.rmdir(downloades_path)


async def done(update: Update, context: CallbackContext) -> int:
    if 'photos' not in context.user_data or not context.user_data['photos']:
        await update.message.reply_text("لم يتم استلام أي صور.")
        return ConversationHandler.END

    await save_photos(context, update)
    await process_and_send_photo(context, update)

    # Inform the user that the process is complete
    await update.message.reply_text('تم الانتهاء. يمكنك البدء مرة أخرى بإرسال /start')

    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token(api_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_TEMPLATE: [CallbackQueryHandler(choose_template)],
            ASKING_QUESTION: [CallbackQueryHandler(handle_choice)],
            ASKING_TEXT1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text1)],
            ASKING_PHOTOS: [
                MessageHandler(filters.PHOTO, handle_photos),
                CommandHandler('done', done)
            ],
        },
        fallbacks=[CommandHandler('start', start), CommandHandler('done', done), CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == '__main__':
    main()

