#!/usr/bin/env python3


import io
import html
import os
import re
import time
import threading
import tempfile

import telebot

import cfg
import my_bard
import my_dic
import my_log
import my_trans
import my_tts
import my_stt
import utils


# set the working folder = the folder where the script is located
os.chdir(os.path.abspath(os.path.dirname(__file__)))


bot = telebot.TeleBot(cfg.token, skip_pending=True)
BOT_ID = bot.get_me().id


# folder for permanent dictionaries, bot memory
if not os.path.exists('db'):
    os.mkdir('db')


# saved pairs of {user:(lang, token)}
DB = my_dic.PersistentDict('db/db.pkl')


supported_langs_trans = [
        "af","am","ar","az","be","bg","bn","bs","ca","ceb","co","cs","cy","da","de",
        "el","en","eo","es","et","eu","fa","fi","fr","fy","ga","gd","gl","gu","ha",
        "haw","he","hi","hmn","hr","ht","hu","hy","id","ig","is","it","iw","ja","jw",
        "ka","kk","km","kn","ko","ku","ky","la","lb","lo","lt","lv","mg","mi","mk",
        "ml","mn","mr","ms","mt","my","ne","nl","no","ny","or","pa","pl","ps","pt",
        "ro","ru","rw","sd","si","sk","sl","sm","sn","so","sq","sr","st","su","sv",
        "sw","ta","te","tg","th","tl","tr","uk","ur","uz","vi","xh","yi","yo","zh",
        "zh-TW","zu"]


HELP = r'''You need to get a google bard token to talk with Bard.

1. Install Cookie-Editor extension.

2. Go to https://bard.google.com and login, you may need to use a VPN to access Bard in countries where it is not available.

3. Click on the extension icon and copy a token starting with __Secure-{account_number}PSID.

For example, __Secure-1PSID
Ensure you are copying the correct token corresponding to the account number, which can be found in the URL as bard.google.com/u/{account_number}.
If your account number is /u/2, search for the token named __Secure-2PSID.
If your account number is /u/3, search for the token named __Secure-3PSID.

4. Paste the token in the bot as [/token xxx...xxx]. 

You can set a token for group by coping the personal token, use [/token copy] command in chat.
'''


class ShowAction(threading.Thread):
    """A thread that can be stopped. Continuously sends an activity notification to the chat.
    Telegram automatically extinguishes the notification after 5 seconds, so it must be repeated.

    It should be used in code like this
    with ShowAction(message, 'typing'):
        we do something and while we do the notification burning"""

    def __init__(self, message, action):
        """_summary_

        Args:
            chat_id (_type_): ID of the chat in which the notification will be displayed
            action (_type_):  "typing", "upload_photo", "record_video", "upload_video", "record_audio", 
                              "upload_audio", "upload_document", "find_location", "record_video_note", "upload_video_note"
        """
        super().__init__()
        self.actions = [  "typing", "upload_photo", "record_video", "upload_video", "record_audio",
                         "upload_audio", "upload_document", "find_location", "record_video_note", "upload_video_note"]
        assert action in self.actions, f'Допустимые actions = {self.actions}'
        self.chat_id = message.chat.id
        self.thread_id = message.message_thread_id
        self.is_topic = message.is_topic_message
        self.action = action
        self.is_running = True
        self.timerseconds = 1

    def run(self):
        while self.is_running:
            try:
                if self.is_topic:
                    bot.send_chat_action(self.chat_id, self.action, message_thread_id = self.thread_id)
                else:
                    bot.send_chat_action(self.chat_id, self.action)
            except Exception as error:
                my_log.log2(f'tb:show_action:run: {error}')
            n = 50
            while n > 0:
                time.sleep(0.1)
                n = n - self.timerseconds

    def stop(self):
        self.timerseconds = 50
        self.is_running = False
        try:
            bot.send_chat_action(self.chat_id, 'cancel', message_thread_id = self.thread_id)
        except Exception as error:
            my_log.log2(f'tb:show_action: {error}')

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


@bot.message_handler(commands=['restart']) 
def restart(message: telebot.types.Message):
    """bot stop. after stopping it will have to restart the systemd script"""
    if message.from_user.id in cfg.admins:
        bot.stop_polling()
    else:
        bot.reply_to(message, 'For admins only.')


@bot.message_handler(commands=['start'])
def send_welcome_start(message: telebot.types.Message):
    # Send hello

    my_log.log_echo(message)

    user_id = message.from_user.id
    if user_id in DB:
        lang = DB[user_id][0]
    else:
        lang = message.from_user.language_code or 'en'
    
    default_lang = message.from_user.language_code or 'en'
    token = ''
    if user_id not in DB:
        DB[user_id] = (default_lang, token)

    if lang != 'en':
        translated = my_trans.translate(HELP, lang)
    else:
        translated = HELP

    bot.reply_to(message, html.escape(translated), parse_mode='HTML', disable_web_page_preview=True)
    my_log.log_echo(message, HELP)


@bot.message_handler(commands=['language', 'lang'])
def language(message: telebot.types.Message):
    """Change language"""
    user_id = message.from_user.id
    if user_id not in DB:
        token = ''
        lang = message.from_user.language_code or 'en'
        DB[user_id] = (lang, token)
    else:
        lang = DB[user_id][0]

    help = f'''/language language code

Example:

<code>/language es</code>
<code>/language en</code>
<code>/language ru</code>
<code>/language fr</code>

https://en.wikipedia.org/wiki/Template:Google_translation
'''

    # if lang != 'en':
    #     help = my_trans.translate(help, lang)

    try:
        new_lang = message.text.split(' ')[1].strip().lower()
    except IndexError:
        bot.reply_to(message, help, parse_mode='HTML', disable_web_page_preview=True)
        return

    token = DB[user_id][1]
    DB[user_id] = (new_lang, token)
    bot.reply_to(message, 'Language changed.')


@bot.message_handler(commands=['init'])
def set_default_commands(message: telebot.types.Message) -> None:
    """
    Reads a file containing a list of commands and their descriptions,
    and sets the default commands and descriptions for the bot.
    """
    if message.from_user.id not in cfg.admins:
        bot.reply_to(message, 'For admins only.')
        return

    commands = []
    with open('commands.txt', encoding='utf-8') as file:
        for line in file:
            try:
                command, description = line[1:].strip().split(' - ', 1)
                if command and description:
                    commands.append(telebot.types.BotCommand(command, description))
            except Exception as error:
                print(error)
    bot.set_my_commands(commands)

    bot_name = bot.get_my_name().name.strip()
    description = bot.get_my_description().description.strip()
    short_description = str(bot.get_my_short_description().short_description).strip()

    new_description = cfg.bot_description.strip()
    new_short_description = cfg.bot_short_description.strip()

    # most used languages
    languages = ['ar', 'bn', 'da', 'de', 'el', 'es', 'fa', 'fi', 'fr', 'hi', 'hu', 'id', 'in', 'it',
                 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'ro', 'ru', 'sv', 'sw', 'th', 'tr', 'uk', 'ur',
                 'vi', 'zh']

    try:
        if not bot.set_my_name(bot_name):
            my_log.log2(f'Failed to set bot name: {bot_name}')
    except Exception as error_set_bot_name:
        my_log.log2(f'Failed to set bot name: {error_set_bot_name}')

    try:
        if not bot.set_my_description(cfg.bot_description):
            my_log.log2(f'Failed to set bot description: {cfg.bot_description}')
    except Exception as error_set_description:
        my_log.log2(f'Failed to set bot description: {error_set_description}')

    for i in languages:
        translated = my_trans.translate(new_description, i)
        try:
            if not bot.set_my_description(translated, language_code=i):
                my_log.log2(f'Failed to set bot description: {translated}')
        except Exception as error:
            my_log.log2(f'Failed to set bot description: [{i}] {translated}')

    try:
        if not bot.set_my_short_description(cfg.bot_short_description):
            my_log.log2(f'Failed to set bot short description: {new_description}')
    except Exception as error_set_short_description:
        my_log.log2(f'Failed to set bot short description: {error_set_short_description}')

    for i in languages:
        translated = my_trans.translate(new_short_description, i)
        try:
            if not bot.set_my_short_description(translated, language_code=i):
                my_log.log2(f'Failed to set bot short description: {translated}')
        except Exception as error:
            my_log.log2(f'Failed to set bot short description: [{i}] {translated}')


@bot.message_handler(commands=['token'])
def token(message: telebot.types.Message) -> None:
    """Token command handler"""
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id in DB:
        lang = DB[user_id][0]
    else:
        lang = message.from_user.language_code or 'en'
    try:
        token = message.text.split(' ')[1].strip()
        if token.lower() == 'copy':
            DB[chat_id] = DB[user_id]
            my_log.log_echo(message)
            bot.reply_to(message, 'OK.')
            return

        DB[user_id] = (lang, token)
        my_log.log_echo(message)
        bot.reply_to(message, 'OK.')
        return
    except IndexError:
        pass

    if lang != 'en':
        translated = my_trans.translate(HELP, lang)
    else:
        translated = HELP

    bot.reply_to(message, html.escape(translated), parse_mode='HTML', disable_web_page_preview=True)
    return


@bot.message_handler(commands=['removeme'])
def removeme(message: telebot.types.Message):
    """Remove user from DB"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_private = message.chat.type == 'private'
    if not is_private:
        user_id = chat_id
    if user_id in DB:
        del DB[user_id]
        my_log.log_echo(message)
        bot.reply_to(message, 'OK')
        my_log.log_echo(message, 'OK')
        return
    else:
        lang = message.from_user.language_code or 'en'
        msg = 'User not found.'
        if lang != 'en':
            msg = my_trans.translate(msg, lang)
        bot.reply_to(message, msg)
        my_log.log_echo(message, msg)


@bot.message_handler(content_types = ['voice', 'audio'])
def handle_voice(message: telebot.types.Message): 
    """voice handler"""
    thread = threading.Thread(target=handle_voice_thread, args=(message,))
    thread.start()
def handle_voice_thread(message: telebot.types.Message):
    """voice handler"""

    my_log.log_media(message)
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_private = message.chat.type == 'private'
    if not is_private:
        user_id = chat_id

    if user_id not in DB:
        return
    lang = DB[user_id][0]

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name
    try:
        file_info = bot.get_file(message.voice.file_id)
    except AttributeError:
        file_info = bot.get_file(message.audio.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    with ShowAction(message, 'typing'):
        text = my_stt.stt(file_path, lang)
        os.remove(file_path)
        text = text.strip()
        if text:
            reply_to_long_message(message, text)
            my_log.log_echo(message, f'[ASR] {text}')
        else:
            msg = 'Did not recognize any text.'
            if lang != 'en':
                msg = my_trans.translate(msg, lang)
            bot.reply_to(message, msg)
            my_log.log_echo(message, '[ASR] no results')

        if text:
            message.text = text
            echo_all(message)


@bot.message_handler(commands=['tts']) 
def tts(message: telebot.types.Message):
    """Text to speech"""
    thread = threading.Thread(target=tts_thread, args=(message,))
    thread.start()
def tts_thread(message: telebot.types.Message):
    """Text to speech"""

    my_log.log_echo(message)

    user_id = message.from_user.id
    chat_id = message.chat.id
    is_private = message.chat.type == 'private'
    if not is_private:
        user_id = chat_id
    if user_id in DB:
        lang = DB[user_id][0]
    else:
        return

    text = ''
    try:
        text = message.text.split(' ', 1)[1].strip()
    except IndexError:
        pass

    if not text:
        msg = '@tts text to say with google voice'
        if lang != 'en':
            msg = my_trans.translate(msg, lang) or msg
        msg = msg.replace('@', '/')
        bot.reply_to(message, msg)
        return

    with ShowAction(message, 'record_audio'):
        audio = my_tts.tts(text, lang)
        if audio:
            bot.send_voice(message.chat.id, audio, reply_to_message_id = message.message_id)
            my_log.log_echo(message, '[Send voice message]')
        else:
            msg = 'TTS failed.'
            if lang != 'en':
                msg = my_trans.translate(msg, lang)
            bot.reply_to(message, msg)
            my_log.log_echo(message, msg)


@bot.message_handler(commands=['trans'])
def trans(message: telebot.types.Message):
    thread = threading.Thread(target=trans_thread, args=(message,))
    thread.start()
def trans_thread(message: telebot.types.Message):

    my_log.log_echo(message)
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_private = message.chat.type == 'private'
    if not is_private:
        user_id = chat_id
    if user_id in DB:
        user_lang = DB[user_id][0]
    else:
        user_lang = message.from_user.language_code or 'en'

    help = f"""@trans [en|ru|uk|..] text to be translated into the specified language

If not specified, then your language will be used.

@trans de hi, how are you?
@trans was ist das

Supported languages: {', '.join(supported_langs_trans)}

"""
    if user_lang != 'en':
        help = my_trans.translate(help, user_lang)
    help = help.replace('@', '/')

    pattern = r'^\/trans\s+((?:' + '|'.join(supported_langs_trans) + r')\s+)?\s*(.*)$'

    match = re.match(pattern, message.text, re.DOTALL)

    if match:
        lang = match.group(1) or user_lang
        text = match.group(2) or ''
    else:
        my_log.log_echo(message, help)
        bot.reply_to(message, help)
        return
    lang = lang.strip()

    with ShowAction(message, 'typing'):
        translated = my_trans.translate(text, lang)
        if translated:
            bot.reply_to(message, translated)
            my_log.log_echo(message, translated)
        else:
            msg = 'Ошибка перевода'
            if lang != 'en':
                msg = my_trans.translate(msg, lang)
            bot.reply_to(message, msg)
            my_log.log_echo(message, msg)


def send_long_message(message: telebot.types.Message, resp: str, parse_mode:str = None, disable_web_page_preview: bool = None,
                      reply_markup: telebot.types.InlineKeyboardMarkup = None):
    """send the message; if it is too long, it splits it into 2 parts or sends it as a text file"""
    reply_to_long_message(message=message, resp=resp, parse_mode=parse_mode,
                          disable_web_page_preview=disable_web_page_preview,
                          reply_markup=reply_markup, send_message = True)


def reply_to_long_message(message: telebot.types.Message, resp: str, parse_mode: str = None,
                          disable_web_page_preview: bool = None,
                          reply_markup: telebot.types.InlineKeyboardMarkup = None, send_message: bool = False):
    """send the message; if it is too long, it splits it into 2 parts or sends it as a text file"""

    if len(resp) < 20000:
        if parse_mode == 'HTML':
            chunks = utils.split_html(resp, 4000)
        else:
            chunks = utils.split_text(resp, 4000)
        counter = len(chunks)
        for chunk in chunks:
            try:
                if send_message:
                    bot.send_message(message.chat.id, chunk, message_thread_id=message.message_thread_id, parse_mode=parse_mode,
                                        disable_web_page_preview=disable_web_page_preview, reply_markup=reply_markup)
                else:
                    bot.reply_to(message, chunk, parse_mode=parse_mode,
                            disable_web_page_preview=disable_web_page_preview, reply_markup=reply_markup)
            except Exception as error:
                print(error)
                my_log.log2(f'tb:reply_to_long_message: {error}')
                if send_message:
                    bot.send_message(message.chat.id, chunk, message_thread_id=message.message_thread_id, parse_mode='',
                                        disable_web_page_preview=disable_web_page_preview, reply_markup=reply_markup)
                else:
                    bot.reply_to(message, chunk, parse_mode='', disable_web_page_preview=disable_web_page_preview, reply_markup=reply_markup)

            counter -= 1
            if counter < 0:
                break
            time.sleep(2)
    else:
        buf = io.BytesIO()
        buf.write(resp.encode())
        buf.seek(0)
        bot.send_document(message.chat.id, document=buf, caption='resp.txt', visible_file_name = 'resp.txt')


@bot.message_handler(commands=['clear'])
def clear(message: telebot.types.Message) -> None:
    """start new dialog"""
    thread = threading.Thread(target=clear_thread, args=(message,))
    thread.start()
def clear_thread(message):
    """start new dialog"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_private = message.chat.type == 'private'
    if not is_private:
        user_id = chat_id
    my_log.log_echo(message)
    if user_id in DB:
        lang = DB[user_id][0]
        my_bard.reset_bard_chat(user_id)
        translated = 'New dialog started.'
        if lang != 'en':
            translated = my_trans.translate(translated, lang)
        bot.reply_to(message, translated)
        my_log.log_echo(message, translated)
    else:
        translated = 'You have to provide a token. Use <code>/token</code> command.'
        lang = message.from_user.language_code or 'en'
        if lang != 'en':
            translated = my_trans.translate(translated, lang)
        bot.reply_to(message, translated)
        my_log.log_echo(message, translated)


@bot.message_handler(func=lambda message: True)
def echo_all(message: telebot.types.Message) -> None:
    """Text message handler"""
    thread = threading.Thread(target=do_task, args=(message,))
    thread.start()
def do_task(message):
    """Text message handler threaded"""
    user_id = message.from_user.id
    chat_id = message.chat.id

    is_private = message.chat.type == 'private'
    is_reply = message.reply_to_message and message.reply_to_message.from_user.id == BOT_ID
    
    if not is_private:
        user_id = chat_id

    if user_id not in DB or DB[user_id][1] == '':
        if is_private:
            msg = 'You have to provide a token. Use <code>/token</code> command.'
        else:
            msg = 'You have to provide a token. Use <code>/token copy</code> command to copy your private token.'
        lang = message.from_user.language_code or 'en'
        if lang != 'en':
            translated = my_trans.translate(msg, lang)
        else:
            translated = msg
        bot.reply_to(message, translated, parse_mode='HTML')
        my_log.log_echo(message)
        my_log.log_echo(message, translated)
        return

    # bot can answer it chats if it is reply to his answer or code word was used
    if not (is_private or is_reply or message.text.lower().startswith(cfg.BOT_CALL_WORD)):
        return

    lang = DB[user_id][0]
    token = DB[user_id][1]

    my_log.log_echo(message)
    msg = message.text
    if len(msg) > my_bard.MAX_REQUEST:
        msg = f'Message too long for bard: {len(msg)} of {my_bard.MAX_REQUEST}'
        if lang != 'en':
            translated = my_trans.translate(msg, lang)
        else:
            translated = msg
        bot.reply_to(message, translated)
        my_log.log_echo(message, translated)
        return
    with ShowAction(message, 'typing'):
        try:
            if is_private:
                user_name = (message.from_user.first_name or '') + ' ' + (message.from_user.last_name or '')
            else:
                user_name = '(public chat, it is not person) ' + (message.chat.username or message.chat.first_name or message.chat.title or 'noname')
            answer = my_bard.chat(message.text, user_id, token, lang, user_name)
            if not answer:
                # 1 more try
                answer = my_bard.chat(message.text, user_id, token, lang, user_name)
            answer = utils.bot_markdown_to_html(answer)
            my_log.log_echo(message, answer)
            if answer:
                try:
                    reply_to_long_message(message, answer, parse_mode='HTML', disable_web_page_preview = True)
                except Exception as error:
                    print(f'tb:do_task: {error}')
                    my_log.log2(f'tb:do_task: {error}')
                    reply_to_long_message(message, answer, parse_mode='', disable_web_page_preview = True)
            else:
                translated = 'Bard did not answer. May be you need to renew your token.'
                if lang != 'en':
                    translated = my_trans.translate(translated, lang)
                bot.reply_to(message, translated)
        except Exception as error3:
            print(error3)
            my_log.log2(str(error3))
        return


def main():
    """
    Runs the main function, which sets default commands and starts polling the bot.
    """
    # set_default_commands()
    bot.polling(timeout=90, long_polling_timeout=90)


if __name__ == '__main__':
    main()
