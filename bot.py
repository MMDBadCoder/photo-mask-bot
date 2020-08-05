from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Updater, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction, PhotoSize
from PIL import Image 
from io import BytesIO
from functools import wraps

def send_action(action):
    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context,  *args, **kwargs)
        return command_func
    
    return decorator

send_uploading_photo = send_action(ChatAction.UPLOAD_PHOTO)
send_typing = send_action(ChatAction.TYPING)

mask = Image.open("mask.png")
mask_width, mask_height = mask.size
mask_size = (mask_width,mask_height)

def process_image(update, context, photo_file):
    photo_byte = photo_file.download_as_bytearray()
    image = image_from_bytearray(photo_byte)
    masked_image = add_mask_to_background(image)
    send_image_to_user(context.bot,update.effective_chat.id,masked_image)

def from_profile(update, context):
    profile_photos = context.bot.get_user_profile_photos(update.message.from_user.id)
    if profile_photos.total_count == 0:
        no_profile_error(update, context)
    else:
        send_from_profile(update,context,profile_photos)

@send_uploading_photo
def send_from_profile(update, context, profile_photos):
    photo_file = profile_photos.photos[0][-1].get_file()
    process_image(update,context,photo_file)

@send_typing
def no_profile_error(update, context):
    reply_text = "شما تصویر پروفایلی ندارید"
    context.bot.send_message(chat_id=update.effective_chat.id, text = reply_text)

@send_uploading_photo
def from_send(update, context):
    photo_file = update.message.photo[-1].get_file()
    process_image(update,context,photo_file)
    
def image_from_bytearray(byte_array):
    image = Image.open(BytesIO(byte_array))
    return image

def crop_if_needed(image):
    width, height = image.size
    if width == height:
        pass
    elif width > height:
        trash = (width - height)/2
        image = image.crop((trash,0,width-trash,height))
    else:
        trash = (height - width)/2
        image = image.crop((0,trash,width,height - trash))
    
    return image.resize(mask_size)

def add_mask_to_background(background):
    background = crop_if_needed(background)
    background.paste(mask,(0,0),mask)
    return background

def send_image_to_user(bot, chat_id, image):
    bio = BytesIO()
    bio.name = 'masked.jpeg'
    image.save(bio, 'JPEG')
    bio.seek(0)
    bot.send_photo(chat_id, photo=bio)

@send_typing
def start(update, context):
    keyboard = [["استفاده از عکس پروفایل"]]
    reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True)
    reply_text = "سلام\n" + "یک عکس برام بفرست یا با دکمه پایین عکس پروفایلت رو تغییر بده" + "\n" + "اگر به اطلاهات بیشتری نیاز داری  از /help استفاده کن"
    context.bot.send_message(chat_id=update.effective_chat.id, text = reply_text, reply_markup=reply_markup)

@send_typing
def unknown_format(update, context):
    update.message.reply_text("چنین دستوری برای من تعریف نشده است.")

@send_typing
def help(update, context):
    reply_text = "شما میتونی یک عکس برای من بفرستی یا حتی از عکس فعلی پروفایلت استفاده کنی" + "\n" +  "برای استفاده از عکس پروفایل از دکمه \"استفاده از عکس پروفایل\" استفاده کن ." + "\n"
    reply_text2 = "\n" + "اگر میخوای از عکس های درون گالریت استفاده کنی اون رو برای من بفرست" + "\n"
    reply_text3 = "بهتره هر قسمت از عکس رو میخوای قبل از فرستادن به صورت مربع برش بزنی. اگر عکس ارسالی مربع نباشه به صورت خودکار بزرگترین مربع وسطش برش میخوره."
    context.bot.send_message(chat_id=update.effective_chat.id, text = reply_text + reply_text2 + reply_text3)

def main():
    token = "1199859151:AAG7JtLndlfvCDO_BJgHNsrYsMzWTLYkrzM"
    updater = Updater(token= token,use_context= True)
    dispacher = updater.dispatcher

    start_handler = CommandHandler('start',start)
    dispacher.add_handler(start_handler)

    profile_handler = MessageHandler(Filters.regex('^استفاده از عکس پروفایل$'), from_profile)
    dispacher.add_handler(profile_handler)

    image_handler = MessageHandler(Filters.photo,from_send)
    dispacher.add_handler(image_handler)

    help_handler = CommandHandler('help', help)
    dispacher.add_handler(help_handler)

    unknown_handler = MessageHandler(Filters.all,unknown_format)
    dispacher.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()