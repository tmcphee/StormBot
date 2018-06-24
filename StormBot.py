import random
import asyncio
import time
import sqlite3
from discord import Game
from discord.ext.commands import Bot

conn = sqlite3.connect('pythonsqlite.db')
cursor = conn.cursor()

#cursor.execute("""CREATE TABLE Activity
                  #(User text PRIMARY KEY, ID integer, Minutes_Voice integer,
                  # Messages_Sent integer, Overall_Activity boolean)
               #""")

#conn.commit()

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
async def on_voice_state_update(before, after):
    if before.voice.voice_channel is None and after.voice.voice_channel is not None:
        if before.voice.voice_channel is None and after.voice.voice_channel is not None:
            start = int(time.time())
        while before.voice.voice_channel is None and after.voice.voice_channel is not None:
            await asyncio.sleep(0.5)
        finish = int(time.time())
        duration = finish - start
        cursor.execute("""SELECT * FROM Activity WHERE User = ?""", (after.name,))
        retn = cursor.fetchall()
        if len(retn) == 0:
            cursor.execute("""INSERT INTO  Activity VALUES (?, NULL, ?, 0, 0)""", (after.name, duration))
            conn.commit()
        else:
            sql = """
               UPDATE Activity
               SET Minutes_Voice = Minutes_Voice + ?
               WHERE User = ?
            """
            data = (duration, after.name)
            cursor.execute(sql, data)
            conn.commit()



@client.event
async def on_message(message):
    author = str(message.author)
    author = author[:-5]
    cursor.execute("""SELECT * FROM Activity WHERE User = ?""", (author,))
    retn = cursor.fetchall()
    if len(retn) == 0:
        cursor.execute("""INSERT INTO  Activity VALUES (?, ?, ?, 0, 0)""", (author, message.author.id, 1))
        conn.commit()
    else:
        sql = """
                   UPDATE Activity
                   SET Messages_Sent = Messages_Sent + ?
                   WHERE User = ? 
                """
        data = (1, author)
        cursor.execute(sql, data)
        conn.commit()



client.loop.create_task(list_servers())
client.run(TOKEN)