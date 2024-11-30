import json

import os
import dotenv

import discord

import ollama
import asyncio
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
NORMAL_PROMPT = 'You are a misinformation detector who takes a fact and returns a short response justifying if the fact is true, partially true, partially false, or false.'
async def check_message_thread(message, client, statement):
    await message.add_reaction("👀")

    ollama_client = ollama.Client(host=HOST)
    messages = [
        { "role": "system", "content": NORMAL_PROMPT },
        { "role": "user",   "content": statement     }
    ]
    response = ollama_client.chat(model=MODEL, messages=messages)
    content = response["message"]["content"]
    print(f"'{content}'")

    await message.remove_reaction("👀", client.user)
    await message.reply(content)

def check_message(message, client, statement):
    asyncio.create_task(check_message_thread(message, client, statement))
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
AUTO_PROMPT = "You are a misinformation detector who takes a fact and returns a number, 1 through 6, where 1 is a completely true statement and 6 is a completely false statement. Only return this number. Check accurately and do not return any other information."
async def auto_check_message_thread(message, client):
    await message.add_reaction("👀")

    ollama_client = ollama.Client(host=HOST)
    messages = [
        { "role": "system", "content": AUTO_PROMPT     },
        { "role": "user",   "content": message.content }
    ]
    response = ollama_client.chat(model=MODEL, messages=messages)
    content = response["message"]["content"]
    print(f"'{content}'")

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

    await message.remove_reaction("👀", client.user)

def auto_check_message(message, client):
    asyncio.create_task(auto_check_message_thread(message, client))
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
    help_str = """`!help`: Display this message.
`!check` # reply to a message to check the truth of the statement
`!check <statement>` # check the truth of the statement
`!auto on` # enable auto checking
`!auto off` # disable auto checking
`!auto level <level>` # only flag statements with a level greater than or equal to the given level (1-6)"""
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
            check_message(message, client, statement)
        case ["!check", *statement]:
            statement = " ".join(statement)
            check_message(message, client, statement)
        case ["!auto", "on"]:
            settings["auto"] = True
            save_mode()
            await send_mode(message)
        case ["!auto", "off"]:
            settings["auto"] = False
            save_mode()
            await send_mode(message)
        case ["!auto", "level", level] if level.isdigit() and 1 <= int(level) <= 6:
            settings["auto_level"] = int(level)
            save_mode()
            await send_mode(message.channel)
        case _ if message.content.startswith("!"):
            await reply(message, "Invalid command. Use !help for a list of commands.")
        case _ if settings["auto"]: 
            auto_check_message(message, client)
        case _: pass

client.run(TOKEN)
#------------------------------------------------------------------------------#
