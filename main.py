from telethon import TelegramClient, events, Button
from telethon import functions, types
from secrets import token_urlsafe
from dotenv import load_dotenv
import pdfminer
from pdfminer.high_level import extract_text
from gtts import gTTS
from argostranslate import package, translate
import os


# VAR ENV
load_dotenv()
global specs, tr

# Telegram
bot = TelegramClient(
    os.getenv('SESSION_FILE_NAME'),
    api_id=os.getenv('API_ID'),
    api_hash=os.getenv('API_HASH')
)

bot.start(bot_token=os.getenv('TOKEN'))
tr = None
specs = []

# Some Functions
async def info():
    me = await bot.get_me()
    print(f'''Logged in as @{me.username}, {me.first_name}.
    [INFO] Verified: {str(me.verified)}
    [INFO] Restricted: {str(me.restricted)}
    [INFO] Scam: {str(me.scam)}
    [INFO] Fake: {str(me.fake)}

STARTED @{me.username} ...
''')
async def specs_init(specs):
    return specs

async def convert(FILE, FILE_NAME, specs):
    # Argos
    global tr
    if specs[0] == 'en':
        package.install_from_path('en_ru.argosmodel')
        installed_languages = translate.get_installed_languages()
        from_lang = list(filter(
            lambda x: x.code == 'en',
            installed_languages))[0]
        to_lang = list(filter(
            lambda x: x.code == 'ru',
            installed_languages))[0]
    else:
        package.install_from_path('ru_en.argosmodel')
        installed_languages = translate.get_installed_languages()
        from_lang = list(filter(
            lambda x: x.code == 'ru',
            installed_languages))[0]
        to_lang = list(filter(
            lambda x: x.code == 'en',
            installed_languages))[0]

    tr = from_lang.get_translation(to_lang)

    try:
        text = await pdf2Text(FILE)
        tar = await text2Ar(text)
        print(tar)
        await ar2Audio(tar, FILE_NAME, specs)
        return True
    except Exception as e:
        print(str(e))
        return False

async def pdf2Text(FILEPATH):
    return extract_text(FILEPATH)

async def text2Ar(TEXT):
    print(tr.translate(TEXT))
    return tr.translate(TEXT)

async def ar2Audio(text, filename, specs):
    audio = gTTS(text=text, lang=str(specs[1]))
    audio.save(f'{filename}.mp3')

@bot.on(events.CallbackQuery(data=b'ru to en'))
async def handler(event):
    await event.respond('Send pdf [ru]')
    global specs
    specs = ['ru', 'en']
    await event.delete()

# Handle only callback queries with data being b'no'
@bot.on(events.CallbackQuery(data=b'en to ru'))
async def handler(event):
    # Pop-up message with alert
    await event.respond('Send pdf [en]')
    global specs
    specs = ['en', 'ru']
    await event.delete()

@bot.on(events.NewMessage(pattern='^/start'))
async def start(event):
    await event.reply('Send a pdf file to convert it into AR speech!')
    await bot.send_message(await event.get_chat(), 'Choose specs:', buttons=[
        Button.inline('ru to en', b'ru to en'),
        Button.inline('en to ru', b'en to ru')
    ])

@bot.on(events.NewMessage)
async def on_pdf(event):
    if (event.message.media is not None
            and event.message.media.document.mime_type == 'application/pdf'
            and event.message.media.document.size <= 6500000 # bytes
    ):
        FILE_NAME = token_urlsafe(16)
        SAVED_PATH = '{}\{}.pdf'.format(f'{os.getcwd()}\\files', FILE_NAME)

        await bot.download_media(
            message=event.message.media,
            file=SAVED_PATH
        )

        conv = await convert(SAVED_PATH, FILE_NAME, specs)
        if conv:
            await bot.send_file(
                await event.get_chat(),
                f'{FILE_NAME}.mp3',
                voice_note=True
            )



if __name__ == '__main__':
    bot.loop.run_until_complete(info())
    bot.run_until_disconnected()