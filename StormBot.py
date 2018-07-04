import random
import asyncio
import time
import sqlite3
import os
from os import path
from discord import Game
from discord.ext.commands import Bot

#User Acitve Req
def_voice = 60
def_msg = 5
def_active_days = 4

SQL = path.exists("pythonsqlite.db") #Resumes or creates Database file
if SQL is True:
    print("SQL SERVER -- DATABASE RESUMING TO SAVED STATE")
    conn = sqlite3.connect('pythonsqlite.db')
    cursor = conn.cursor()
else:
    print("WARNING -- DATABASE FAILED TO RESUME TO SAVED STATE")
    print("        -- SYSTEM CREATING DATABASE WITH NEW TABLE")
    conn = sqlite3.connect('pythonsqlite.db')
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE Activity
                      (User text PRIMARY KEY, User_ID text, User_Nickname text, Minutes_Voice double,
                       Messages_Sent integer, Active_Days_Weekly integer, Daily_Activity text,
                        Weekly_Activity text)
                   """)
    conn.commit()


BOT_PREFIX = "?"

#I always forget to switch them when moving to Heroku
token_key = path.exists("token.auth") #Resumes or creates Database file
if token_key is True:
    #Get Token from file
    f = open("token.auth", "r")
    TOKEN = str(f.readline())
    f.close()
else:
    TOKEN = os.environ['BOT_TOKEN']

client = Bot(command_prefix=BOT_PREFIX)


async def update_activity_daily(): #0001
    await client.wait_until_ready()
    while not client.is_closed:
        await asyncio.sleep(60 * 60 * 24)  # task runs every day
        print("-Processing Daily Activity")
        act_tmp = 0
        inact_temp = 0
        cursor.execute("""SELECT COUNT(*) FROM Activity""")
        rows = int(cursor.fetchone()[0])
        if rows == 0:
            break
        temp = 0
        while temp < rows:
            cursor.execute("""SELECT User FROM Activity""")
            user = str(cursor.fetchall()[temp][0])
            cursor.execute("""SELECT Minutes_Voice FROM Activity WHERE User LIKE (?)""", (('%' + user + '%'),))
            voice_val = int(cursor.fetchone()[0])
            cursor.execute("""SELECT Messages_Sent FROM Activity WHERE User LIKE (?)""", (('%' + user + '%'),))
            msg_val = int(cursor.fetchone()[0])

            if voice_val >= def_voice and msg_val >= def_msg:
                sql = """
                                       UPDATE Activity
                                       SET Daily_Activity = ?
                                       AND Active_Days_Weekly = Active_Days_Weekly + ?
                                       WHERE User = ?
                                    """
                data = ('Active', 1, user)
                cursor.execute(sql, data)
                act_tmp = act_tmp + 1
            else:
                sql = """
                                               UPDATE Activity
                                               SET Daily_Activity = ?
                                               WHERE User = ?
                                            """
                data = ("Inactive", user)
                cursor.execute(sql, data)
                inact_temp = inact_temp + 1
            temp = temp + 1
        print("Active:" + str(act_tmp) + "   Inactive:" + str(inact_temp))


async def update_activity_weekly(): #0001
    await client.wait_until_ready()
    while not client.is_closed:
        print("-Processing Weekly Activity")
        await asyncio.sleep(60 * 60 * 24 * 7)  # task runs every week
        act_tmp = 0
        inact_temp = 0
        cursor.execute("""SELECT COUNT(*) FROM Activity""")
        rows = int(cursor.fetchone()[0])
        if rows == 0:
            break
        temp2 = 0
        while temp2 < rows:
            cursor.execute("""SELECT User FROM Activity""")
            user = str(cursor.fetchall()[temp2][0])
            cursor.execute("""SELECT Active_Days_Weekly FROM Activity WHERE User LIKE (?)""", (('%' + user + '%'),))
            active_days = int(cursor.fetchone()[0])

            if active_days >= def_active_days:
                sql = """
                                                       UPDATE Activity
                                                       SET Weekly_Activity = ?
                                                       WHERE User = ?
                                                    """
                data = ("Active", user)
                cursor.execute(sql, data)
                act_tmp = act_tmp + 1
            else:
                sql = """
                                                               UPDATE Activity
                                                               SET Weekly_Activity = ?
                                                               WHERE User = ?
                                                            """
                data = ("Inactive", user)
                cursor.execute(sql, data)
                inact_temp = inact_temp + 1
            temp2 = temp2 + 1
        print("Active:" + str(act_tmp) + "   Inactive:" + str(inact_temp))


@client.event#0004
async def on_ready():
    #await client.change_presence(game=Game(name="TESTING - IN DEVELOPMENT"))#?help
    print("********************************************Login*Details***********************************************")
    print("     Logged in as " + client.user.name)
    print("     Client User ID: " + client.user.id)
    print("     Invite at: https://discordapp.com/oauth2/authorize?client_id=" + client.user.id + "&scope=bot")
    print("********************************************************************************************************")


@client.event#0005
async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("********************************************Current*Servers*********************************************")
        for server in client.servers:
            print("     " + server.name + " (Members: " + str(len(server.members)) + ")")
        print("********************************************************************************************************")
        await asyncio.sleep(60*60)


@client.event#0009
async def display():
    await client.wait_until_ready()
    while not client.is_closed:
        await client.change_presence(game=Game(name="TESTING - IN DEVELOPMENT"))  #?help
        await asyncio.sleep(20)
        await client.change_presence(game=Game(name="WATCHDOG (ACTIVE)"))
        await asyncio.sleep(5)
        await client.change_presence(game=Game(name="DEV: ZombieEar#0493"))
        await asyncio.sleep(2)


@client.event#0006
async def on_voice_state_update(before, after):
    if before.voice.voice_channel is None and after.voice.voice_channel is not None:
        if before.voice.voice_channel is None and after.voice.voice_channel is not None:
            start = int(time.time())
        while before.voice.voice_channel is None and after.voice.voice_channel is not None:
            await asyncio.sleep(0.5)
        finish = int(time.time())
        duration = ((finish - start) / 60)
        cursor.execute("""SELECT * FROM Activity WHERE User LIKE (?)""", (('%' + after.name + '%'),))
        retn = cursor.fetchall()
        if len(retn) == 0:
            print("ERROR 0006 -- THE MEMBER *" + after.name + "* CANNOT BE LOCATED IN THE DATABASE")
        else:
            sql = """
               UPDATE Activity
               SET Minutes_Voice = Minutes_Voice + ?
               WHERE User LIKE (?)
            """
            data = (duration, ('%' + after.name + '%'))
            cursor.execute(sql, data)
            conn.commit()


@client.event#0007
async def on_message(message):
    if message.author == client.user:#do not want the bot to reply to itself
        return

    author = str(message.author)
    cursor.execute("""SELECT * FROM Activity WHERE User = ?""", (author,))
    retn = cursor.fetchall()
    if len(retn) == 0:
        print("Warning 0007 -- MEMBER *" + author + "* NOT FOUND - Adding user to DataBase")
        cursor.execute("""INSERT INTO Activity VALUES (?, ?, ?, 0, 1, 0, 'NA', 'NA')""", (author, message.author.id
                                                                                          , message.author.display_name))
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

    if message.content.startswith(BOT_PREFIX + 'hello'):
        msg = 'Sup {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)

    if message.content.startswith(BOT_PREFIX + 'report'):
        import datetime
        date = str(datetime.datetime.now().strftime("%y-%m-%d-%H-%M"))

        cursor.execute("""SELECT COUNT(*) FROM Activity""")
        rows = int(cursor.fetchone()[0])
        temp3 = 0
        filename = 'member_activity_report.html'
        file = open(filename, 'w')
        file.write("<html><head><title>output</title></head><body bgcolor='#949494'>")
        file.write("Member Activity Report - %s" % (date,))
        file.write("            Members in Database - %s" % (str(rows),))
        file.write("<table border = 1>")
        file.write("<tr><th>" + "User" + "</th><th>" + "Minutes in Voice" + "</th><th>" + "Messages Sent" + "</th>")
        file.write("<th>" + "Total Days Active" + "</th><th>" + "Daily Activity" + "</th>")
        file.write("<th>" + "Weekly Activity" + "</th></tr>")
        while temp3 < rows:
            cursor.execute("""SELECT User FROM Activity""")
            user = str(cursor.fetchall()[temp3][0])
            print(str(temp3) + "    " + user)
            cursor.execute("""SELECT Minutes_Voice FROM Activity WHERE User = ?""", (user,))
            min_voice = int(cursor.fetchone()[0])
            cursor.execute("""SELECT Messages_Sent FROM Activity WHERE User = ?""", (user,))
            msg_sent = int(cursor.fetchone()[0])
            cursor.execute("""SELECT Active_Days_Weekly FROM Activity WHERE User = ?""", (user,))
            active_days = str(cursor.fetchone()[0])
            cursor.execute("""SELECT Daily_Activity FROM Activity WHERE User = ?""", (user,))
            daily_act = str(cursor.fetchone()[0])
            cursor.execute("""SELECT Weekly_Activity FROM Activity WHERE User = ?""", (user,))
            weekly_act = str(cursor.fetchone()[0])

            file.write("<tr>")
            print("tr")
            try:
                file.write("<th>%s</th>" % (user,))
            except:
                user1 = user.encode(('utf-8'))
                file.write("<th>%s</th>" % ((user1),))
            print("us")
            file.write("<th>%s</th>" % (min_voice,))
            file.write("<th>%s</th>" % (msg_sent,))
            file.write("<th>%s</th><th>%s</th><th>%s</th></tr>" % (active_days, daily_act, weekly_act))
            temp3 = temp3 + 1
        file.write("</table>")
        file.write("*Note: For text the website don't understand is converted to utf-8")
        file.write("</body></html>")
        file.close()
        await client.send_file(message.channel, 'member_activity_report.html')

    if message.content.startswith(BOT_PREFIX + 'database'):
        await client.send_file(message.channel, 'pythonsqlite.db')

    if message.content.startswith(BOT_PREFIX + 'help'):
        msg = '```css\n' \
              'List of Help Commands:\n' \
              'Report: - Sends a html file containing user activity\n' \
              '```'.format(message)
        await client.send_message(message.channel, msg)

    if message.content.startswith(BOT_PREFIX + 'test'):
        cursor.execute("""SELECT COUNT(*) FROM Activity""")
        rows = cursor.fetchone()
        print(rows)
        cursor.execute("SELECT * FROM Activity")
        print(cursor.fetchall()[1])

    if message.content.startswith(BOT_PREFIX + 'db'):
        cursor.execute("""SELECT COUNT(*) FROM Activity""")
        rows = int(cursor.fetchone()[0])
        members = 0
        for server in client.servers:
            members = members + len(server.members)
        msg = ('I have ' + str(rows) + " of " + str(members - 3) + " Members in the Database")
        await client.send_message(message.channel, msg.format(message))
        msg2 = ('I have ' + str((members - 3) - rows) + ' left to put in the Database')
        await client.send_message(message.channel, msg2.format(message))


@client.event#0008
async def on_member_join(member):
    user = str(member)
    cursor.execute("""INSERT INTO Activity VALUES (?, ?, ?, 0, 0, 0, 'NA', 'NA')""", (user, str(member.id)
                                                                                      , str(member.nick)))
    conn.commit()
    print("-on_member_join   User Joined      User:" + user)


@client.event#0009
async def on_member_remove(member):
    user = str(member)
    cursor.execute("""DELETE FROM Activity WHERE User = ?""", (user, ))
    conn.commit()
    print("-on_member_remove   User Left     User:" + user)


@client.event
async def on_member_update(before, after):
    cursor.execute("""SELECT * FROM Activity WHERE User LIKE (?)""", (('%' + after.name + '%'),))
    retn = cursor.fetchall()
    if before.nick != after.nick:
        if len(retn) == 0:
            print("ERROR 0006 -- THE MEMBER *" + after.name + "* CANNOT BE LOCATED IN THE DATABASE")
        else:
            sql = """
                       UPDATE Activity
                       SET User_Nickname = ?
                       WHERE User LIKE (?)
                    """
            data = (str(after.nick), ('%' + after.name + '%'))
            cursor.execute(sql, data)
            conn.commit()
            print("-Updated the user: " + after.name + " changed Nickname from *" + str(before.nick) + "* to *"
                  + str(after.nick) + "*")


def set_role(user, role):
    print("")


client.loop.create_task(display())
client.loop.create_task(list_servers())
client.loop.create_task(update_activity_daily())
client.loop.create_task(update_activity_weekly())
client.run(TOKEN)
