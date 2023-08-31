# freegooglebard
Free self-hosted telegram bot for google bard

Free Google Bard is a Telegram bot that allows users to chat with Google Bard, a large language model from Google AI. Bard can generate text, translate languages, write different creative content, and answer your questions in an informative way.

To start chatting with Free Google Bard, you first need to get a token. A token is a unique identifier that allows you to authenticate with Google Bard.

After setting the token, you will be able to start chatting with Free Google Bard.


# How to get token?

* Install Cookie-Editor extension.

* Go to https://bard.google.com and login, you may need to use a VPN to access Bard in countries where it is not available.

* Click on the extension icon and copy a cookie starting with __Secure-{account_number}PSID.

* For example, ***__Secure-1PSID***
      Ensure you are copying the correct cookie corresponding to the account number, which can be found in the URL as bard.google.com/u/{account_number}.
      If your account number is /u/2, search for the cookie named __Secure-2PSID.
      If your account number is /u/3, search for the cookie named __Secure-3PSID.

Once you have a token, you can set it in Free Google Bard using the ***/token*** command. To do this, send a message to the bot with the text ***/token your_token***.

# How to use Free Google Bard?

To start chatting with Free Google Bard, send a message to the bot

In a group you can send a message to the bot using ***.bard*** command and with reply to bards messages.

***.bard what is the weather today in London***

Special command ***/token copy*** may be used in chat to copy your private key.

# Description of commands:

*/start* - This command greets you and briefly describes the features of Free Google Bard.

**/token** - This command allows you to set your personal Google Bard token. The token is necessary to access Google Bard.

/clear - This command clears the current dialog and starts a new one. This is useful if you want to start with a clean 
slate or if you want to forget about what was said before.

/lang - This command allows you to change the language that Free Google Bard uses. This is useful if you do not speak English or if you want Free Google Bard to use a different language to communicate with you.

/restart - This command restarts Free Google Bard. This is useful if Free Google Bard is stuck or not working properly.

/init - This command is an admin command that initializes Free Google Bard. This is necessary to do if you are using Free Google Bard for the first time or if you have changed the settings of the bot.
