import json

import os
import dotenv

import discord

import ollama
import threading
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
dotenv.load_dotenv()

SETTINGS_FILE = "settings.json"
MODEL = 'qwen2.5:0.5b'
HOST = os.getenv('OLLAMA_HOST', "http://localhost:11434")
TOKEN = os.getenv('DISCORD_TOKEN', "")

settings = json.load(open(SETTINGS_FILE)) # { "auto": False, "auto_level": 0 }
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
NORMAL_PROMPT = ''
async def check_message_thread(message, statement):
    await message.add_reaction("👀")

    ollama_client = ollama.Client(host=HOST)
    messages = [
        { "role": "system", "content": NORMAL_PROMPT },
        { "role": "user",   "content": statement     }
    ]
    response = ollama_client.chat(model=MODEL, messages=messages)
    content = response["messages"]["content"]

    message.reply(content)

def check_message(message, statement):
    t = threading.Thread(target=check_message_thread, args=(message, statement))
    t.start()
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
AUTO_PROMPT = ''
async def auto_check_message_thread(message):
    await message.add_reaction("👀")

    ollama_client = ollama.Client(host=HOST)
    messages = [
        { "role": "system", "content": AUTO_PROMPT     },
        { "role": "user",   "content": message.content }
    ]
    response = ollama_client.chat(model=MODEL, messages=messages)
    content = response["messages"]["content"]

    emoji_map = {
        "0": "0️⃣",
        "1": "1️⃣",
        "2": "2️⃣",
        "3": "3️⃣",
        "4": "4️⃣",
        "5": "5️⃣",
        "6": "6️⃣"
    }
    emoji = emoji_map.get(content, None)
    if emoji:
        if int(content) >= settings["auto_level"]:
            await message.add_reaction(emoji)
        else:
            await message.add_reaction("✅")
    else:
        await message.add_reaction("❓")

    await message.remove_reaction("👀")

def auto_check_message(message):
    t = threading.Thread(target=auto_check_message_thread, args=(message,))
    t.start()
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
def save_mode():
    json.dump(settings, open(SETTINGS_FILE, "w"))

async def reply(message, content):
    await message.reply(content, allowed_mentions=discord.AllowedMentions.none())

async def send_mode(message):
    if settings["auto"]:
        mode_str = f"Auto checking is enabled with a level of {settings['auto_level']}."
    else:
        mode_str = "Auto checking is disabled."
    await reply(message, mode_str)

async def help_message(message):
    help_str = """
    ```
    !help: Display this message.
    !check [statement]: Check the given statement for plagiarism.
    !auto on: Enable auto checking.
    !auto off: Disable auto checking.
    !auto level [level]: Set the auto checking level.
    ```
    """
    await reply(message, help_str)
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    match message.content.split():
        case ["!help"]:
            await help_message(message)
        case ["!check"] if message.reference:
            statement = message.reference.resolved.content
            check_message(message, statement)
        case ["!check", *statement]:
            statement = " ".join(statement)
            check_message(message, statement)
        case ["!auto", "on"]:
            settings["auto"] = True
            save_mode()
            await send_mode(message)
        case ["!auto", "off"]:
            settings["auto"] = False
            save_mode()
            await send_mode(message)
        case ["!auto", "level", level] if level.isdigit() and 0 <= int(level) <= 6:
            settings["auto_level"] = int(level)
            save_mode()
            await send_mode(message.channel)
        case _ if settings["auto"]: 
            auto_check_message(message)
        case _:
            await reply(message, "Invalid command. Use !help for a list of commands.")

client.run(TOKEN)
#------------------------------------------------------------------------------#
