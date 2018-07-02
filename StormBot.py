import random
import asyncio
import time
from discord import Game
from discord.ext.commands import Bot

BOT_PREFIX = ("?", "!")
#Get Token from file
f = open("token.auth", "r")
TOKEN = str(f.readline())
f.close()

client = Bot (command_prefix=BOT_PREFIX)

@client.command(name='8Ball',
                description='Answer a yes/no question',
                brief="Answers from the beyond",
                aliases=['eight_ball', 'eightball', '8-ball'],
                pass_context=True)
async def eight_ball(context):
    possible_responces = [
        'Thats a no',
        'Not likely',
        'Probs',
    ]
    await client.say(random.choice(possible_responces) + " , " + context.message.author.mention)


@client.command(pass_context=True, name='report')
async def report(ctx):
    print("report")
    channel = ctx.message.author.voice.voice_channel
    await client.send_file(ctx.message.channel, 'member_activity_report.html')
    print("done")


@client.event
async def on_ready():
    await client.change_presence(game=Game(name="?help"))
    print("Logged in as " + client.user.name)
    print("Client User ID: " + client.user.id)
    file = open("member_activity_report.html", "w+")
    file.close()


@client.event
async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("*****Current*Servers******")
        for server in client.servers:
            print(server.name + " (Members: " + str(len(server.members)) + ")")
        print("**************************")
        await asyncio.sleep(600)


@client.event
async def on_voice_state_update(before, after, context):
    if before.voice.voice_channel is None and after.voice.voice_channel is not None:
        if before.voice.voice_channel is None and after.voice.voice_channel is not None:
            start = int(time.time())
            print("joined-" + str(start))
        while before.voice.voice_channel is None and after.voice.voice_channel is not None:
            print("looping...")
            await asyncio.sleep(0.5)
        finish = int(time.time())
        print("left-" + str(finish))
        print(str(finish - start))


#@client.event
#async def on_message(message):
   # author = message.author
   # authorid = message.author.id


client.loop.create_task(list_servers())
client.run(TOKEN)