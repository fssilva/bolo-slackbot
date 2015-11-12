import os
import sys
from dotenv import load_dotenv
from bolobot import BoloBot

DOTENV_PATH = os.path.join(os.path.dirname(__file__), '.env')


load_dotenv(DOTENV_PATH)
bot = BoloBot(os.environ.get('BOT_TOKEN'))
bot.run()
