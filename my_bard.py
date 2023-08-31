#!/usr/bin/env python3


import threading
import requests

from bardapi import Bard

import my_log


# storage for sessions {chat_id(int):session(bardapi.Bard),...}
DIALOGS = {}
# lock storage so that users cannot make new requests until a response to the old one is received
# {chat_id(str):threading.Lock(),...}
CHAT_LOCKS = {}

# the maximum request size that the bard accepts is obtained by selection
MAX_REQUEST = 3100


def get_new_session(token: str, lang: str, user_name: str) -> Bard:
    """
    Creates a new session for interacting with the Bard API.

    Args:
        token (str): The authentication token for the session.
        lang (str): The language of the user.
        user_name (str): The name of the user.

    Returns:
        Bard: An instance of the Bard class representing the session.
    """
    session = requests.Session()

    session.cookies.set("__Secure-1PSID", token)

    session.headers = {
        "Host": "bard.google.com",
        "X-Same-Domain": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Origin": "https://bard.google.com",
        "Referer": "https://bard.google.com/",
        }

    bard = Bard(token=token, session=session, timeout=30)

    rules = f"You are talking to user with name [{user_name}] and user's locale is [{lang}]. Take care about the name, gender and locale of the user. Say OK if got."

    r = bard.get_answer(rules)

    return bard


def reset_bard_chat(dialog: str):
    """
    Deletes a specific dialog from the DIALOGS dictionary.

    Args:
        dialog (str): The key of the dialog to be deleted.

    Returns:
        None
    """
    try:
        del DIALOGS[dialog]
    except KeyError:
        print(f'no such key in DIALOGS: {dialog}')
        my_log.log2(f'my_bard.py:reset_bard_chat:no such key in DIALOGS: {dialog}')
    return


def chat_request(query: str, dialog: str, token: str, lang: str, user_name: str, reset: bool = False) -> str:
    """
    Executes a chat request to the dialog system.

    Args:
        query (str): The query string for the chat request.
        dialog (str): The identifier for the current dialog session.
        token (str): The authentication token for accessing the dialog system.
        lang (str): The language code for the chat request.
        user_name (str): The name of the user making the chat request.
        reset (bool, optional): Whether to reset the dialog session. Defaults to False.

    Returns:
        str: The response from the dialog system, limited to 4096 characters.

    Raises:
        KeyError: If the specified dialog session does not exist in the DIALOGS dictionary.
    """
    if reset:
        reset_bard_chat(dialog)
        return

    if dialog in DIALOGS:
        session = DIALOGS[dialog]
    else:
        session = get_new_session(token, lang, user_name)
        DIALOGS[dialog] = session

    try:
        response = session.get_answer(query)
    except Exception as error:
        print(error)
        my_log.log2(str(error))

        try:
            del DIALOGS[dialog]
            session = get_new_session(token, lang, user_name)
            DIALOGS[dialog] = session
        except KeyError:
            print(f'no such key in DIALOGS: {dialog}')
            my_log.log2(f'my_bard.py:chat_request:no such key in DIALOGS: {dialog}')

        try:
            response = session.get_answer(query)
        except Exception as error2:
            print(error2)
            my_log.log2(str(error2))
            return ''

    result = response['content']

    try:
        links = list(set([x for x in response['links'] if 'http://' not in x]))
    except Exception as links_error:
        reset_bard_chat(dialog)
        return 'key error'

    return result[:4096]


def chat(query: str, dialog: str, token: str, lang: str, user_name: str, reset: bool = False) -> str:
    """
    This function is used to chat with a dialog bot.

    Args:
        query (str): The query message to send to the bot.
        dialog (str): The ID of the dialog to chat with.
        token (str): The authentication token for the bot.
        lang (str): The language code for the dialog.
        user_name (str): The name of the user chatting with the bot.
        reset (bool, optional): Whether to reset the dialog. Defaults to False.

    Returns:
        str: The response message from the bot.
    """
    if dialog in CHAT_LOCKS:
        lock = CHAT_LOCKS[dialog]
    else:
        lock = threading.Lock()
        CHAT_LOCKS[dialog] = lock
    result = ''
    with lock:
        try:
            result = chat_request(query, dialog, token, lang, user_name, reset)
        except Exception as error:
            print(f'my_bard:chat: {error}')
            my_log.log2(f'my_bard:chat: {error}')
            try:
                result = chat_request(query, dialog, token, lang, user_name, reset)
            except Exception as error2:
                print(f'my_bard:chat:2: {error2}')
                my_log.log2(f'my_bard:chat:2: {error2}')
    return result


if __name__ == "__main__":

    token = 'xxx.'

    n = 'test chat'

    queries = [ 'hi',
                'who are you',
                'where are you from',
                'what was before you']
    for q in queries:
        print('user:', q)
        b = chat_request(q, n, token, 'ru', 'Егор')
        print('bard:', b, '\n')
