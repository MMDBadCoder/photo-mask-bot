from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Updater, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction, PhotoSize
from PIL import Image 
from io import BytesIO
from functools import wraps

# This function will be used as a decorator for calback functions
def send_action(action):
    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context,  *args, **kwargs)
        return command_func
    
    return decorator

# sending photo >>> action in bot
send_uploading_photo = send_action(ChatAction.UPLOAD_PHOTO)
# typing... action in bot
send_typing = send_action(ChatAction.TYPING)

# mask image load into memory here
mask = Image.open("mask.png")
mask_width, mask_height = mask.size

# mask size in a Touple for PIL.Image.resize() methode
mask_size = (mask_width,mask_height)

# gets upadate and context from calback and photo_file (`cls`:telegram.File)
# ceate PIL.Image from photo_file and add mask to it and send it back to user
def process_image(update, context, photo_file):
    photo_byte = photo_file.download_as_bytearray()
    image = image_from_bytearray(photo_byte)
    masked_image = add_mask_to_background(image)
    send_image_to_user(context.bot,update.effective_chat.id,masked_image)

# function for MessageHandler (image_handler) in main()
def from_profile(update, context):
    profile_photos = context.bot.get_user_profile_photos(update.message.from_user.id)
    if profile_photos.total_count == 0: # if user doesn't have profile photo
        no_profile_error(update, context)
    else:
        send_from_profile(update,context,profile_photos)

# send result from profile photo
@send_uploading_photo
def send_from_profile(update, context, profile_photos):
    # photo_file will be last profile of user
    photo_file = profile_photos.photos[0][-1].get_file()
    process_image(update,context,photo_file)

# send message that user doesn't have a profile poto
@send_typing
def no_profile_error(update, context):
    reply_text = "شما تصویر پروفایلی ندارید"
    context.bot.send_message(chat_id=update.effective_chat.id, text = reply_text)

# send result from received photo
@send_uploading_photo
def from_send(update, context):
    photo_file = update.message.photo[-1].get_file()
    process_image(update,context,photo_file)
    
# create PIL.Image from byte array
def image_from_bytearray(byte_array):
    image = Image.open(BytesIO(byte_array))
    return image

# crop the image if it's not square and resize it to mask size
# retures croped and resized image
def crop_if_needed_and_resize(image):
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

# pasetes mask to the background and returns the result
def add_mask_to_background(background):
    background = crop_if_needed_and_resize(background)
    background.paste(mask,(0,0),mask)
    return background

# send PIL.Image to the user
def send_image_to_user(bot, chat_id, image):
    bio = BytesIO()
    bio.name = 'masked.jpeg'
    image.save(bio, 'JPEG')
    bio.seek(0)
    bot.send_photo(chat_id, photo=bio)

# function responsible for /start command
@send_typing
def start(update, context):
    keyboard = [["استفاده از عکس پروفایل"]]
    reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True)
    reply_text = "سلام\n" + "یک عکس برام بفرست یا با دکمه پایین عکس پروفایلت رو تغییر بده" + "\n" + "اگر به اطلاهات بیشتری نیاز داری  از /help استفاده کن"
    context.bot.send_message(chat_id=update.effective_chat.id, text = reply_text, reply_markup=reply_markup)

# function responsible for unknown commands and messages
@send_typing
def unknown_format(update, context):
    update.message.reply_text("چنین دستوری برای من تعریف نشده است.")

# function responsible for /help command
@send_typing
def help(update, context):
    reply_text = "شما میتونی یک عکس برای من بفرستی یا حتی از عکس فعلی پروفایلت استفاده کنی" + "\n" +  "برای استفاده از عکس پروفایل از دکمه \"استفاده از عکس پروفایل\" استفاده کن ." + "\n"
    reply_text2 = "\n" + "اگر میخوای از عکس های درون گالریت استفاده کنی اون رو برای من بفرست" + "\n"
    reply_text3 = "بهتره هر قسمت از عکس رو میخوای قبل از فرستادن به صورت مربع برش بزنی. اگر عکس ارسالی مربع نباشه به صورت خودکار بزرگترین مربع وسطش برش میخوره."
    context.bot.send_message(chat_id=update.effective_chat.id, text = reply_text + reply_text2 + reply_text3)

# main function
def main():
    # Replace "your_token" with <Your Token>
    token = "your_token"
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