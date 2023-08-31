# freegooglebard
Free self-hosted telegram bot for google bard

Free Google Bard is a Telegram bot that allows users to chat with Google Bard, a large language model from Google AI. Bard can generate text, translate languages, write different creative content, and answer your questions in an informative way.

To start chatting with Free Google Bard, you first need to get a token. A token is a unique identifier that allows you to authenticate with Google Bard.

After setting the token, you will be able to start chatting with Free Google Bard.


# How to get token?

* Install Cookie-Editor extension.

* Go to https://bard.google.com and login, you may need to use a VPN to access Bard in countries where it is not available.

* Click on the extension icon and copy a cookie starting with __Secure-{account_number}PSID.

* For example, **__Secure-1PSID**
      Ensure you are copying the correct cookie corresponding to the account number, which can be found in the URL as bard.google.com/u/{account_number}.
      If your account number is /u/2, search for the cookie named __Secure-2PSID.
      If your account number is /u/3, search for the cookie named __Secure-3PSID.

Once you have a token, you can set it in Free Google Bard using the **/token** command. To do this, send a message to the bot with the text **/token your_token**.

# How to use Free Google Bard?

To start chatting with Free Google Bard, send a message to the bot

In a group you can send a message to the bot using **.bard** command and with reply to bards messages.

**.bard what is the weather today in London**

Special command **/token copy** may be used in chat to copy your private key.

# Description of commands:

**/start** - This command greets you and briefly describes the features of Free Google Bard.

**/token** - This command allows you to set your personal Google Bard token. The token is necessary to access Google Bard.

**/clear** - This command clears the current dialog and starts a new one. This is useful if you want to start with a clean 
slate or if you want to forget about what was said before.

**/lang** - This command allows you to change the language that Free Google Bard uses. This is useful if you do not speak English or if you want Free Google Bard to use a different language to communicate with you.

# Install on self-hosted server
Python 3.8+

sudo apt-get update
sudo apt install translate-shell python3-venv


git clone https://github.com/theurs/freegooglebard.git

python -m venv .tb-tr
source ~/.tb/bin/activate

pip install -r requirements.txt

config file

cfg.py
```
# Bot description, up to 512 symbols. Fewer characters for automatic translation to work properly.
bot_description = """Free Telegram bot for chatting with Google Bard

You only need to get your own Google Bard token and then you can talk to bard in telegram.

https://github.com/theurs/freegooglebard

@theurs"""


# a short description of the bot that is displayed on the bot's profile page and submitted
# along with a link when users share the bot. Up to 120 characters.
# Fewer characters for automatic translation to work properly.
bot_short_description = """Free telegram bot for chatting with Google Bard"""


# Bot name (pseudonym), this is not a unique name, you can call it whatever you like,
# is not the name of the bot it responds to. Up to 64 characters.
bot_name = "Free Google Bard"

# bot call word, use it in chats for ask bot
# Example - .bard how are you
BOT_CALL_WORD = '.bard'

# list of admins who can use admin commands (/restart etc)
admins = [xxx,]


# telegram bot token
# @free_google_bard_bot
token   = "xxx"
```

start ./tb.py


**Commands for admins**

**/restart** - This command restarts Free Google Bard. This is useful if Free Google Bard is stuck or not working properly.

**/init** - This command initializes Free Google Bard. This is necessary to do if you are using Free Google Bard for the first time or if you have changed the settings of the bot.
