#!/usr/bin/env python3


import os
import datetime
import telebot
import threading


lock = threading.Lock()


if not os.path.exists('logs'):
    os.mkdir('logs')


def log2(text: str) -> None:
    """для дебага"""
    time_now = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    log_file_path = 'logs/debug.log'
    open(log_file_path, 'a', encoding="utf-8").write(f'{time_now}\n\n{text}\n{"=" * 80}\n')


def log_echo(message: telebot.types.Message, reply_from_bot: str = '', debug: bool = False) -> None:
    """writes to the log a message received by the regular message handler or a bot response"""
    global lock
    time_now = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    private_or_chat = 'private' if message.chat.type == 'private' else 'chat'
    chat_name = message.chat.username or message.chat.first_name or message.chat.title or ''
    user_name = message.from_user.first_name or message.from_user.username or ''
    chat_name = chat_name.replace('/', '⁄')
    user_name = user_name.replace('/', '⁄')

    logname = f'logs/[{chat_name}] [{private_or_chat}] [{message.chat.type}] [{message.chat.id}].log'.replace('[private] [private]', '[private]').replace('[chat] [supergroup]', '[chat]')

    topic_id = 0

    if message.reply_to_message and message.reply_to_message.is_topic_message:
        topic_id = message.reply_to_message.message_thread_id
    elif message.is_topic_message:
        topic_id = message.message_thread_id

    log_file_path = logname
    
    if debug:
        log_file_path = log_file_path + '.debug.log'

    if topic_id:
        log_file_path = log_file_path[:-4] + f' [{topic_id}].log'

    with lock:
        with open(log_file_path, 'a', encoding="utf-8") as log_file:
            if reply_from_bot:
                log_file.write(f"[{time_now}] [BOT]: {reply_from_bot}\n")
            else:
                log_file.write(f"[{time_now}] [{user_name}]: {message.text or message.caption or ''}\n")


if __name__ == '__main__':
    pass
