import os
import dotenv

import discord

import asyncio

from openai import OpenAI
# AUTO_CHECK_ASSISTANT_ID=asst_cdNhh39ldmeLphGz20Zsj4zW
# MESSAGE_CHECK_ASSISTANT_ID=asst_uwE8bACTTq15kj2TT8aHdz43
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
dotenv.load_dotenv()

MODEL = 'qwen2.5:0.5b'
HOST = os.getenv('OLLAMA_HOST', "http://localhost:11434")
TOKEN = os.getenv('DISCORD_TOKEN', "")
AUTO_CHECK_ASSISTANT_ID = os.getenv("AUTO_CHECK_ASSISTANT_ID", "")
MESSAGE_CHECK_ASSISTANT_ID = os.getenv("MESSAGE_CHECK_ASSISTANT_ID", "")

auto_on = False
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
def gpt(content: str, assistant_id: str):
    client = OpenAI()
    assistant_id = assistant_id
    assistant = client.beta.assistants.retrieve(
        assistant_id=assistant_id
    )
    thread = client.beta.threads.create(
        messages=[{"role": "user", "content": content}]
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )
    if run.status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        ai_response = messages.data[0].content[0].text.value
        return ai_response
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
async def check_message_thread(message, client, statement):
    await message.add_reaction("👀")

    content = gpt(statement, MESSAGE_CHECK_ASSISTANT_ID)

    await message.remove_reaction("👀", client.user)
    await message.reply(content)


def check_message(message, client, statement):
    asyncio.create_task(check_message_thread(message, client, statement))
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
async def auto_check_message_thread(message, client):
    await message.add_reaction("👀")

    content = gpt(str(message), AUTO_CHECK_ASSISTANT_ID)

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
        await message.add_reaction(emoji)
    else:
        await message.add_reaction("❓")

    await message.remove_reaction("👀", client.user)


def auto_check_message(message, client):
    asyncio.create_task(auto_check_message_thread(message, client))
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
async def reply(message, content):
    await message.reply(content, allowed_mentions=discord.AllowedMentions.none())

async def send_mode(message):
    global auto_on
    if auto_on:
        mode_str = f"Auto checking is enabled (1 = True, 6 = False)."
    else:
        mode_str = "Auto checking is disabled."
    await reply(message, mode_str)

async def help_message(message):
    help_str = """`!help`: Display this message.
`!check` # reply to a message to check the truth of the statement
`!check <statement>` # check the truth of the statement
`!auto on` # enable auto checking
`!auto off` # disable auto checking"""
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
    global auto_on
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
            auto_on = True
            await send_mode(message)
        case ["!auto", "off"]:
            auto_on = False
            await send_mode(message)
        case _ if message.content.startswith("!"):
            await reply(message, "Invalid command. Use !help for a list of commands.")
        case _ if auto_on:
            auto_check_message(message, client)
        case _:
            pass


client.run(TOKEN)
#------------------------------------------------------------------------------#
