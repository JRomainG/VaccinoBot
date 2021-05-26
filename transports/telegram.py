from telegram import Bot
from .generic import Transport


class Telegram(Transport):
    def __init__(self, config):
        super().__init__(config)

        # Read the token for the Telegram Bot
        with open("secret.token", "r") as file:
            token = file.readline()
            token = token.strip()

        self.tg_bot = Bot(token=token)
        self.chat_id = config["chat_id"]

    def send_message(self, text):
        self.tg_bot.send_message(chat_id=self.chat_id, text=text)
