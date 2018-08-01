import asyncio
import time
import datetime
import pyodbc
import discord
import sqlite3
import sys
import traceback
import logging
from os import path
from discord import Game
from discord.ext.commands import Bot

def setup_logging_to_file(filename):
    logging.basicConfig(filename=filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')


def extract_function_name():
    tb = sys.exc_info()[-1]
    stk = traceback.extract_tb(tb, 1)
    fname = stk[0][3]
    return fname


def log_exception(e):
    logging.error(
        "Function {function_name} raised {exception_class} ({exception_docstring}): {exception_message}".format(
            function_name=extract_function_name(),  # this is optional
            exception_class=e.__class__,
            exception_docstring=e.__doc__,
            exception_message=e))

setup_logging_to_file('StormBot_log.txt')
#CONFIG
text_file = open("StormBot.config", "r")
BOT_CONFIG = text_file.readlines()
text_file.close()

server_addr = str(BOT_CONFIG[0]).strip()
database = str(BOT_CONFIG[1]).strip()
username = str(BOT_CONFIG[2]).strip()
password = str(BOT_CONFIG[3]).strip()
TOKEN = str(BOT_CONFIG[4])

retry_flag = True
retry_count = 0
while retry_flag:
  try:
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server_addr + ';DATABASE=' + database + ';UID=' + username + ';PWD='
            + password)
        cursor = conn.cursor()
        server_env = 'Linux'
    except:
        conn = pyodbc.connect('DRIVER={SQL SERVER};SERVER=' + server_addr + ';DATABASE=' + database + ';UID=' + username + ';PWD='
                               + password)
        cursor = conn.cursor()
        server_env = 'Windows'
    retry_flag = False
    print('Connection to SQL server - Succeeded')
    print('Bot running in ' + str(server_env) + ' environment')
  except Exception as e:
    log_exception(str(e))
    retry_count = retry_count + 1
    time.sleep(2)
    if retry_count == 5:
        print('Connection to SQL server - Failed')
        sys.exit(2)
#conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server_addr + ';DATABASE=' + database + ';UID=' + username + ';PWD='
#                      + password)
#cursor = conn.cursor()

SQL = path.exists("pythonsqlite.db") #Resumes or creates Database file
if SQL is True:
    print("SQL INTERNAL SERVER -- DATABASE RESUMING TO SAVED STATE")
    connect = sqlite3.connect('pythonsqlite.db')
    cursor2 = connect.cursor()
else:
    print("WARNING -- INTERNAL DATABASE FAILED TO RESUME TO SAVED STATE")
    print("        -- SYSTEM CREATING DATABASE WITH NEW TABLE")
    connect = sqlite3.connect('pythonsqlite.db')
    cursor2 = connect.cursor()
    cursor2.execute("""CREATE TABLE Presets
                          (NoVoice integer , NoMessages integer, GuestRole text, ActiveRole text, InactiveRole text, BeginDate text, StombotChannel text)
                       """)
    connect.commit()
    cursor2.execute("""INSERT INTO Presets VALUES (?,?,?,?,?,?,?)""", (120, 10, "381911719901134850", "SB_Test_A", "SB_Test_X", '2018-07-22 00:00:00', '466401774094516245'))
    connect.commit()

server_id = '162706186272112640'#StormBot
#server_id = '451097751975886858'#TestBot

BOT_PREFIX = "?"
client = Bot(command_prefix=BOT_PREFIX)


async def update_activity_weekly(): #0001
    try:
        await client.wait_until_ready()
        while not client.is_closed:
            current_weekday = datetime.datetime.now().weekday()
            await asyncio.sleep(2)
            if current_weekday == 6:
                logging.info('Processing Weekly Activity')
                print("-Processing Weekly Activity")
                act_tmp = 0
                inact_temp = 0
                cursor.execute("""SELECT * FROM DiscordActivity""")
                user_dat = cursor.fetchall()
                cursor2.execute("""SELECT * FROM Presets""")
                conf_dat = cursor2.fetchall()
                def_voice = conf_dat[0][0]
                def_msg = conf_dat[0][1]
                if len(user_dat) == 0:
                    break
                temp = 0
                while temp < len(user_dat):
                    userid = str(user_dat[temp][2])
                    voice_val = int(str(user_dat[temp][4]))
                    msg_val = int(user_dat[temp][5])

                    if voice_val >= def_voice and msg_val >= def_msg:
                        sql = """
                                                               UPDATE DiscordActivity
                                                               SET Weekly_Activity = ? 
                                                               WHERE User_ID = ?
                                                            """
                        data = ("Active", userid)
                        cursor.execute(sql, data)
                        conn.commit()
                        act_tmp = act_tmp + 1
                    else:
                        sql = """
                                                                       UPDATE DiscordActivity
                                                                       SET Weekly_Activity = ?
                                                                       WHERE User_ID = ?
                                                                    """
                        data = ("Inactive", userid)
                        cursor.execute(sql, data)
                        conn.commit()
                        inact_temp = inact_temp + 1
                    temp = temp + 1

                    begindate = conf_dat[0][5]

                    cursor.execute("""INSERT INTO DiscordActivityArchive VALUES (?,?,?,?)""", userid, voice_val, msg_val
                                   , begindate)
                    conn.commit()

                    sql = """
                                                                                                           UPDATE DiscordActivity
                                                                                                           SET Minutes_Voice = ?, Messages_Sent = ?
                                                                                                           WHERE User_ID = ?
                                                                                                        """
                    data = (0, 0, userid)
                    cursor.execute(sql, data)
                    conn.commit()

                ts = time.time()
                enddate = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                sql = """
                                                                                                                          UPDATE Presets
                                                                                                                          SET BeginDate = ?
                                                                                                                    """
                data = (enddate,)
                cursor2.execute(sql, data)
                connect.commit()
                print("Active:" + str(act_tmp) + "   Inactive:" + str(inact_temp))
                logging.info("Weekly Activity Finished  -   Active:" + str(act_tmp) + "   Inactive:" + str(inact_temp))
                await asyncio.sleep(60 * 60 * 24)
    except Exception as e:
        log_exception(str(e))


@asyncio.coroutine
async def update_roles(): #0001
    try:
        await client.wait_until_ready()
        while not client.is_closed:
            current_weekday = datetime.datetime.now().weekday()
            await asyncio.sleep(2)
            if current_weekday == 5:
                logging.info('Processing Role Update')
                print("-Processing Role Update --- " + str(current_weekday))
                cursor.execute("""SELECT * FROM DiscordActivity""")
                user_dat = cursor.fetchall()
                cursor2.execute("""SELECT * FROM Presets""")
                conf_dat = cursor2.fetchall()
                role_active = conf_dat[0][3]
                role_inactive = conf_dat[0][4]
                def_voice = conf_dat[0][0]
                def_msg = conf_dat[0][1]
                server = client.get_server(server_id)
                role_ac = discord.utils.get(server.roles, name=role_active)
                role_in = discord.utils.get(server.roles, name=role_inactive)
                if len(user_dat) == 0:
                    break
                else:
                    temp = 0
                    act_tmp = 0
                    inact_temp = 0
                    while temp < len(user_dat):
                        userid = str(user_dat[temp][2])
                        voice_val = int(str(user_dat[temp][4]))
                        msg_val = int(user_dat[temp][5])
                        member = server.get_member(userid)

                        if voice_val >= def_voice and msg_val >= def_msg:
                            try:
                                await client.add_roles(member, role_ac)
                                await client.remove_roles(member, role_in)
                                act_tmp = act_tmp + 1
                            except Exception as e:
                                print(repr(e))
                        else:
                            try:
                                await client.add_roles(member, role_in)
                                await client.remove_roles(member, role_ac)
                                inact_temp = inact_temp + 1
                            except Exception as e:
                                print(repr(e))
                        temp = temp + 1

                    print("Active:" + str(act_tmp) + "   Inactive:" + str(inact_temp))
                    logging.info("Role Update Finished    -    Active:" + str(act_tmp) + "   Inactive:" + str(inact_temp))
                    await asyncio.sleep(80)
    except Exception as e:
        log_exception(str(e))


@asyncio.coroutine
async def check_not_in_clan():
    try:
        await client.wait_until_ready()
        while not client.is_closed:
            await asyncio.sleep(2)
            current_time = datetime.datetime.now()
            today1am = current_time.replace(hour=1, minute=0)
            if current_time == today1am:
                print("-Processing Guest Update --- " + str(current_time))
                cursor.execute("""select * from DiscordActivity d
                                    where User_ID not in (
                                    select User_ID from ClanMembers m
                                    join DiscordActivity d on d.User_ID=m.DiscordID
                                    where m.IsActive=1)
                                    and Discord_Roles not like '%Clan%'
                                    and Discord_Roles not like '%Bots%'
                                    and Discord_Roles not like '%Guest%'
                                    """)
                user_dat = cursor.fetchall()
                cursor2.execute("""SELECT * FROM Presets""")
                conf_dat = cursor2.fetchall()
                role_guest = conf_dat[0][2]
                server = client.get_server(server_id)
                role_guest = discord.utils.get(server.roles, id=role_guest)
                if len(user_dat) == 0:
                    break
                else:
                    temp = 0
                    while temp < len(user_dat):
                        userid = str(user_dat[temp][2])
                        member = server.get_member(userid)
                        try:
                            await client.add_roles(member, role_guest)
                        except Exception as e:
                            print(repr(e))
                        temp = temp + 1
                print("Guest Update - FINISHED")
    except Exception as e:
        log_exception(str(e))


@client.event#0004
async def on_ready():
    try:
        #await client.change_presence(game=Game(name="TESTING - IN DEVELOPMENT"))#?help
        print("********************************************Login*Details***********************************************")
        print("     Logged in as " + client.user.name)
        print("     Client User ID: " + client.user.id)
        print("     Invite at: https://discordapp.com/oauth2/authorize?client_id=" + client.user.id + "&scope=bot")
        print("********************************************************************************************************")
    except Exception as e:
        log_exception(str(e))


async def list_servers():
    try:
        await client.wait_until_ready()
        while not client.is_closed:
            print("********************************************Current*Servers*********************************************")
            for server in client.servers:
                print("     " + str(server.name) + " (Members: " + str(len(server.members)) + ") [" + str(server.id) + "]")
            print("********************************************************************************************************")
            await asyncio.sleep(60*60)
    except Exception as e:
        log_exception(str(e))


@client.event#0009
async def display():
    try:
        await client.wait_until_ready()
        while not client.is_closed:
            await client.change_presence(game=Game(name="?help | BETA"))  #?help
            await asyncio.sleep(25)
            await client.change_presence(game=Game(name="ENV: " + str(server_env)))
            await asyncio.sleep(2)
            await client.change_presence(game=Game(name="DEV: ZombieEar#0493"))
            await asyncio.sleep(2)
    except Exception as e:
        log_exception(str(e))


@client.event#0006
async def on_voice_state_update(before, after):
    try:
        server = client.get_server(server_id)
        channel = discord.utils.get(server.channels, name='AFK', type='Voice')
        if in_voice_channel(before, server, 'AFK') == False:
            if before.voice.voice_channel is None and after.voice.voice_channel is not None:
                if before.voice.voice_channel is None and after.voice.voice_channel is not None:
                    start = int(time.time())
                while before.voice.voice_channel is None and after.voice.voice_channel is not None:
                    await asyncio.sleep(0.5)
                finish = int(time.time())
                duration = ((finish - start) / 60)
                print(str(duration))
                print(str(int(duration)))
                cursor.execute("""SELECT * FROM DiscordActivity WHERE User_ID = ?""", (after.id,))
                retn = cursor.fetchall()
                if len(retn) == 0:
                    print("Warning 0008 -- MEMBER *" + str(after) + "* NOT FOUND - Adding user to DataBase")
                    roles = fetch_roles(after)
                    user = str(after)
                    cursor.execute("""INSERT INTO DiscordActivity VALUES (?, ?, ?, ?, 0, 0, 'NA', 'NA', ?)""",
                                   (user, str(after.id), str(after.nick), int(duration), str(roles)))
                    conn.commit()
                else:
                    sql = """
                       UPDATE DiscordActivity
                       SET Minutes_Voice = Minutes_Voice + ?
                       WHERE User_ID = ?
                    """
                    data = (duration, after.id)
                    cursor.execute(sql, data)
                    conn.commit()
    except Exception as e:
        log_exception(str(e))


@client.event#0007
@asyncio.coroutine
async def on_message(message):
    try:
        server = client.get_server(server_id)
        if message.author == client.user:#do not want the bot to reply to itself
            return

        author = str(message.author)
        cursor.execute("""SELECT * FROM DiscordActivity WHERE User_ID = ?""", message.author.id,)
        retn = cursor.fetchone()
        if retn is None:
            member2 = server.get_member(message.author.id)
            usr_roles2 = fetch_roles(member2)
            print("Warning 0007 -- MEMBER *" + str(author) + "* NOT FOUND - Adding user to DataBase")
            cursor.execute("""INSERT INTO DiscordActivity VALUES (?, ?, ?, 0, 1, 0, 'NA', 'NA', ?)""", author, message.author.id
                                                                                              , message.author.display_name, usr_roles2)
            conn.commit()
        else:
            sql = """
                       UPDATE DiscordActivity
                       SET Messages_Sent = Messages_Sent + ?
                       WHERE User_ID = ? 
                    """
            data = (1, message.author.id)
            cursor.execute(sql, data)
            conn.commit()

        if message.content.startswith(BOT_PREFIX + 'hello'):
            msg = 'Sup {0.author.mention}'.format(message)
            await client.send_message(message.channel, msg)

        if message.content.startswith(BOT_PREFIX + 'help'):
            emb = (discord.Embed(title="Help Commands:", color=0xe1960b))
            emb.add_field(name='?roles', value='Gets the current roles that a member belongs to. Use \'?roles\' to '
                                                 'get your current roles or \'?roles @Member\' to get another members '
                                                 'current roles.', inline=True)
            emb.add_field(name='?change_nick', value='Changes the nickname of the current member. Ex. \'?change_nick StormBot#1234\'', inline=True)
            emb.add_field(name='?activity', value='Gets the current activity of a member. Use \'?activity\' to '
                                               'get your current activity or \'?roles @Member\' to get another members '
                                               'activity.\n'
                                                '*AVAILABLE TO MODERATORS AND ADMINISTRATORS ONLY*', inline=True)
            emb.add_field(name='?set help', value='Shows a list of commands to set the Bot Presets\n'
                                                  '*AVAILABLE TO ADMINISTRATORS ONLY*', inline=True)
            await client.send_message(message.channel, embed=emb)

        if message.content.startswith(BOT_PREFIX + 'roles'):
            if "<@" in message.content:
                member = server.get_member(str(message.content[9:-1]))
            else:
                member = server.get_member(message.author.id)
            usr_roles = fetch_roles(member)
            await client.send_message(message.channel, str(usr_roles))

        if message.content.startswith(BOT_PREFIX + 'activity'):
            member = server.get_member(message.author.id)
            mod_ck = moderator_check(message.author.id, server_id)
            if (mod_ck is True) or member.server_permissions.administrator:
                if "<@" in message.content:
                    member_id = str(message.content[12:-1])
                    temp_con = str(message.content[12:-1])
                    if "!" in member_id:
                        member_id = temp_con[1:]
                else:
                    member_id = str(message.author.id)
                cursor.execute("""SELECT * FROM DiscordActivity WHERE User_ID = ?""", member_id, )
                user_dat = cursor.fetchall()
                if str(user_dat) != '[]':
                    emb = (discord.Embed(title="Activity Request:", color=0x49ad3f))
                    emb.add_field(name='User', value=user_dat[0][1], inline=True)
                    emb.add_field(name='User ID', value=user_dat[0][2], inline=True)
                    emb.add_field(name='Nickname/BattleTag', value=user_dat[0][3], inline=True)
                    emb.add_field(name='Current Voice Activity', value=user_dat[0][4], inline=True)
                    emb.add_field(name='Current Message Activity', value=user_dat[0][5], inline=True)
                    emb.add_field(name='Previous 7-Day Activity', value=user_dat[0][8], inline=True)
                    await client.send_message(message.channel, embed=emb)
                else:
                    emb = (discord.Embed(title="Activity Request:", color=0x49ad3f))
                    emb.set_author(name="Stormbot")
                    emb.add_field(name='ERROR - BAD REQUEST', value='That Member don\'t exist. Either the Member is not in the database,'
                                                      ' you fucked up, '
                                                      'or the programmer fucked up.', inline=True)
                    emb.set_footer(text="If the member exists and the error is repeated please notify ZombieEar#0493 ")
                    await client.send_message(message.channel, embed=emb)
            else:
                await client.send_message(message.channel, 'Access Denied - You are not a Moderator or Administrator'.format(message))

        if message.content.startswith(BOT_PREFIX + 'set'):
            member = server.get_member(message.author.id)
            if member.server_permissions.administrator:
                if message.content.startswith(BOT_PREFIX + 'set def_voice'):
                    if message.content == (BOT_PREFIX + 'set def_voice'):
                        await client.send_message(message.channel, 'No value specified. To Update '
                                                                   'Default Voice No enter'
                                                                   ' \'?set def_voice Value\''.format(message))
                    else:
                        value = message.content[15:]
                        sql = """
                                UPDATE Presets
                                SET NoVoice = ?
                            """
                        cursor2.execute(sql, (value,))
                        connect.commit()
                        await client.send_message(message.channel, ('The Default number of requred voice minutes has been updated to (' + value + ')').format(message))
                if message.content.startswith(BOT_PREFIX + 'set def_message'):
                    if message.content == (BOT_PREFIX + 'set def_message'):
                        await client.send_message(message.channel, 'No value specified. To Update '
                                                                   'Default Messages No enter'
                                                                   ' \'?set def_message Value\''.format(message))
                    else:
                        value = message.content[17:]
                        sql = """
                                UPDATE Presets
                                SET NoMessages = ?
                            """
                        cursor2.execute(sql, (value,))
                        connect.commit()
                        await client.send_message(message.channel, ('The Default number of requred messages has been updated to (' + value + ')').format(message))
                if message.content.startswith(BOT_PREFIX + 'set active_role'):
                    if message.content == (BOT_PREFIX + 'set active_role'):
                        await client.send_message(message.channel, 'No value specified. To Update '
                                                                   'Default Active Role enter'
                                                                   ' \'?set active_role RoleName\''.format(message))
                    else:
                        value = message.content[17:]
                        sql = """
                                UPDATE Presets
                                SET ActiveRole = ?
                            """
                        cursor2.execute(sql, (value,))
                        connect.commit()
                        await client.send_message(message.channel, ('The Default Active Role has been updated to (' + value + ')').format(message))
                        print("Active Role Updated to *" + str(value) + '*')
                if message.content.startswith(BOT_PREFIX + 'set guest_role'):
                    if message.content == (BOT_PREFIX + 'set guest_role'):
                        await client.send_message(message.channel, 'No value specified. To Update '
                                                                   'Default Guest Role enter'
                                                                   ' \'?set guest_role RoleID\''.format(message))
                    else:
                        value = message.content[16:]
                        sql = """
                                UPDATE Presets
                                SET GuestRole = ?
                            """
                        cursor2.execute(sql, (value,))
                        connect.commit()
                        await client.send_message(message.channel, ('The Default Guest Role has been updated to (' + value + ')').format(message))
                        print("Active Role Updated to *" + str(value) + '*')
                if message.content.startswith(BOT_PREFIX + 'set inactive_role'):
                    if message.content == (BOT_PREFIX + 'set inactive_role'):
                        await client.send_message(message.channel, 'No value specified. To Update '
                                                                   'Default Inactive Role enter'
                                                                   ' \'?set inactive_role RoleName\''.format(message))
                    else:
                        value = message.content[19:]
                        sql = """
                                UPDATE Presets
                                SET InactiveRole = ?
                            """
                        cursor2.execute(sql, (value,))
                        connect.commit()
                        await client.send_message(message.channel, ('The Default Inactive Role has been updated to (' + value + ')').format(message))
                        print("Inactive Role Updated to *" + str(value) + '*')
                if message.content.startswith(BOT_PREFIX + 'set channel_cleft'):
                    if message.content == (BOT_PREFIX + 'set channel_cleft'):
                        await client.send_message(message.channel, 'No value specified. To update '
                                                                   'the Clan Member Left Channel enter'
                                                                   ' \'?set channel_cleft Channel_ID\''.format(message))
                    else:
                        value = message.content[21:-1]
                        sql = """
                                UPDATE Presets
                                SET StombotChannel = ?
                            """
                        cursor2.execute(sql, (value,))
                        connect.commit()
                        await client.send_message(message.channel, ('The Clan Member Left Channel has been updated to (' + value + ')').format(message))
                        print("Inactive Role Updated to *" + str(value) + '*')
                if message.content.startswith(BOT_PREFIX + 'set display'):
                    cursor2.execute("""SELECT * FROM Presets""")
                    conf_dat = cursor2.fetchall()

                    emb3 = (discord.Embed(title="Storm Bot Presets:", color=0xee1b15))
                    emb3.add_field(name='Voice Minutes', value=conf_dat[0][0], inline=True)
                    emb3.add_field(name='Messages', value=conf_dat[0][1], inline=True)
                    emb3.add_field(name='GuestRole', value=conf_dat[0][2], inline=True)
                    emb3.add_field(name='Active Role', value=conf_dat[0][3], inline=True)
                    emb3.add_field(name='Inactive Role', value=conf_dat[0][4], inline=True)
                    emb3.add_field(name='Clan Member Left Channel', value=conf_dat[0][6], inline=True)
                    await client.send_message(message.channel, embed=emb3)
                if message.content.startswith(BOT_PREFIX + 'set help'):
                    emb = (discord.Embed(title="Set Help Commands:", color=0xee1b15))
                    emb.add_field(name='?set def_voice', value='Use \'?set def_voice Value\' to update the Default Voice preset value. Example (?set def_voice 60)', inline=True)
                    emb.add_field(name='?set def_message', value='Use \'?set def_message Value\' to update the Default Messages preset value. Example (?set def_message 5)', inline=True)
                    emb.add_field(name='?set guest_role', value='Use \'?set guest_role Value\' to update the Default Active Role preset value. Example (?set active_role @Guest)', inline=True)
                    emb.add_field(name='?set active_role', value='Use \'?set active_role Value\' to update the Default Active Role preset value. Example (?set active_rolee ACTIVE)', inline=True)
                    emb.add_field(name='?set inactive_role', value='Use \'?set inactive_role Value\' to update the Default Inactive Role preset value. Example (?set inactive_role INACTIVE)', inline=True)
                    emb.add_field(name='?set ?set channel_cleft Channel_ID', value='Use this update the Clan Member Left Channel preset. Example (set channel_cleft #bot-logs)', inline=True)
                    emb.add_field(name='?set display', value='Use this command to display all the current presets', inline=True)
                    await client.send_message(message.channel, embed=emb)
            else:
                emb5 = (discord.Embed(color=0xee1b15))
                emb5.add_field(name='ACCESS DENIED', value='Only Administrators may set Bot presets', inline=True)
                emb5.set_footer(text="For further assistance please contact an Administrator")
                await client.send_message(message.channel, embed=emb5)

        if message.content.startswith(BOT_PREFIX + 'system'):
            member = server.get_member(message.author.id)
            if member.server_permissions.administrator == True:
                print("Access Granted")
                if message.content == (BOT_PREFIX + 'system refresh_roles'):
                    msg = 'Access Granted - Force Update Roles (Started) - Please Wait...'
                    await client.send_message(message.channel, msg.format(message))
                    server = client.get_server(server_id)
                    cursor.execute("""SELECT * FROM DiscordActivity""")
                    user_dat = cursor.fetchall()
                    if len(user_dat) == 0:
                        print("Refresh - Error")
                    temp8 = 0
                    while temp8 < len(user_dat):
                        member = server.get_member(str(user_dat[temp8][2]))
                        if str(member) == 'None':
                            usr_roles = 'ERROR GETTING ROLES'
                        else:
                            usr_roles = fetch_roles(member)

                        sql = """
                                                                                       UPDATE DiscordActivity
                                                                                       SET Discord_Roles = ?
                                                                                       WHERE User_ID = ?
                                                                                    """
                        data = (usr_roles, user_dat[temp8][2])
                        cursor.execute(sql, data)
                        temp8 = temp8 + 1
                    msg2 = ('Force Update Roles (Finished) - Updated:' + str(len(user_dat)) + ' Members')
                    await client.send_message(message.channel, msg2.format(message))
            else:
                print("Access Denied - U no admin")

        if message.content.startswith(BOT_PREFIX + 'change_nick'):
            member = server.get_member(message.author.id)
            if message.content == (BOT_PREFIX + 'change_nick'):
                await client.send_message(message.channel, 'No value specified. To Update '
                                                           'your Nickname/BattleTag enter'
                                                           ' \'?set change_nick Value\''.format(message))
            else:
                value = message.content[13:]
                await client.change_nickname(member, value)
                msg = ('<@' + message.author.id + '> Your Nickname has been updated to \'' + value + '\'')
                await client.send_message(message.channel, msg.format(message))

        if message.content.startswith(BOT_PREFIX + 'stop'):
            if str(message.author.id) == '162705828883726336':
                await client.send_message(message.channel, 'Halting StormBot Operations with exit code 0'.format(message))
                sys.exit()
            else:
                await client.send_message(message.channel, 'You do not have the required permissions to execute '
                                                           'this command'.format(message))

        if message.content.startswith(BOT_PREFIX + 'top25'):
            member = server.get_member(message.author.id)
            mod_ck = moderator_check(message.author.id, server_id)
            if (mod_ck is True) or member.server_permissions.administrator:
                msg_cont = message.content[7:]
                if msg_cont == 'message' or msg_cont == 'Message':
                    cursor.execute("""SELECT Top 25 * FROM DiscordActivity
                                      ORDER BY Messages_Sent DESC""")
                elif msg_cont == 'message active' or msg_cont == 'Message Active' or msg_cont == 'Message active' or msg_cont == 'message Active':
                    cursor.execute("""SELECT Top 25 * FROM DiscordActivity
                                      WHERE Weekly_Activity = 'Active'
                                      ORDER BY Messages_Sent DESC""")
                elif msg_cont == 'message inactive' or msg_cont == 'Message Inactive' or msg_cont == 'Message inactive' or msg_cont == 'message Inactive':
                    cursor.execute("""SELECT Top 25 * FROM DiscordActivity
                                      WHERE Weekly_Activity = 'Inactive'
                                      ORDER BY Messages_Sent DESC""")
                elif msg_cont == 'voice active' or msg_cont == 'Voice Active' or msg_cont == 'Voice active' or msg_cont == 'voice Active':
                    cursor.execute("""SELECT Top 25 * FROM DiscordActivity
                                      WHERE Weekly_Activity = 'Active'
                                      ORDER BY Minutes_Voice DESC""")
                elif msg_cont == 'voice inactive' or msg_cont == 'Voice Inactive' or msg_cont == 'Voice inactive' or msg_cont == 'voice Inactive':
                    cursor.execute("""SELECT Top 25 * FROM DiscordActivity
                                      WHERE Weekly_Activity = 'Inactive'
                                      ORDER BY Minutes_Voice DESC""")
                else:
                    cursor.execute("""SELECT Top 25 * FROM DiscordActivity
                                      ORDER BY Minutes_Voice DESC""")
                user_dat = cursor.fetchall()
                temp = 0
                emb = (discord.Embed(title="Active Top 25", color=0xe1960b))
                while temp < len(user_dat):
                    emb.add_field(name=(str(temp + 1) + '. ' + str(user_dat[temp][2]) + ''), value=('```Voice (Minutes): ' + str(user_dat[temp][4]) + '     Message(s): ' +
                                                                                               str(user_dat[temp][5]) + '\nWeekly Activity: ' + str(user_dat[temp][8])) + '```', inline=True)
                    temp = temp + 1
                emb.set_footer(text='Requested By: (' + str(message.author.id) + ') ' + str(message.author))
                await client.send_message(message.channel, embed=emb)
            else:
                await client.send_message(message.channel, 'Access Denied - You are not a Moderator or Administrator'.format(message))
    except Exception as e:
        log_exception(str(e))


@client.event#0008
async def on_member_join(member):
    try:
        server = client.get_server(server_id)
        add_member_database(member, server)
        embed = discord.Embed(title="Welcome to Collective Conscious.", description="CoCo is a PC-only Destiny 2 clan covering both NA and EU.", color=0x008000)
        embed.add_field(name='1. Server nickname', value='Your nickname must match your BattleTag regardless of clan member status.\n'
                                                         'Example: PeachTree#11671\n Set your nickname using the command \'?change_nick BattleTag\'.', inline=False)
        embed.add_field(name='2. Clan Applications', value='Head to the #clan-application channel and apply to one of '
                                                           'the clans showing as "recruiting." Once you\'ve requested '
                                                           'membership, post in #request-a-rank stating the clan you '
                                                           'applied to and clan staff will process your request.', inline=False)
        embed.add_field(name='3. Clan & Discord Information', value='Please take a moment to read over server rules '
                                                                    'in #rules as well as Frequently Asked Questions '
                                                                    'in #faq before asking questions, as you may find '
                                                                    'them answered!', inline=False)
        embed.set_footer(text='I\'m a bot. If you have questions, please contact a Clan Leader, Admin, or Moderator!')
        await client.send_message(member, embed=embed)
        print("-on_member_join      User Joined      User:" + str(member))
        #embed=embed
    except Exception as e:
        log_exception(str(e))


@client.event#0009
async def on_member_remove(member):
    try:
        cursor.execute("""SELECT * FROM DiscordActivity WHERE User_ID = ? and Discord_Roles LIKE '%Clan%'""", member.id)
        user_dat = cursor.fetchall()
        if len(user_dat) != 0:
            cursor2.execute("""SELECT * FROM Presets""")
            conf_dat = cursor2.fetchall()
            stormbot_channel = conf_dat[0][6]
            roles = str(user_dat[0][9])
            indx = roles.index('Clan')
            clan = ''
            temp = indx
            while str(roles[temp]) != ',':
                clan = (clan + roles[temp])
                temp = temp + 1
            embed = discord.Embed(title="Clan Member Left Discord",
                                  description="User has now been purged from the DataBase", color=0x008000)
            embed.add_field(name='User:',
                            value=str(member),
                            inline=False)
            embed.add_field(name='User ID:',
                            value=str(member.id),
                            inline=False)
            embed.add_field(name='BattleTag/Nickname:',
                            value=str(member.nick),
                            inline=False)
            embed.add_field(name='Clan Role:',
                            value=str(clan),
                            inline=False)
            embed.set_footer(text='This is an automated message     <@&382117075558203392> <@&382118099341541379>')
            await client.send_message(client.get_channel(stormbot_channel), embed=embed)
            print(str(clan) + ' Member Left ' + str(member))
        userid = str(member.id)
        user = str(member)
        cursor.execute("""DELETE FROM DiscordActivity WHERE User_ID = ?""", (userid, ))
        conn.commit()
        cursor.execute("""DELETE FROM DiscordActivityArchive WHERE User_ID = ?""", (userid,))
        conn.commit()
        print("-on_member_remove   User Left     User:" + user)
    except Exception as e:
        log_exception(str(e))


@client.event
async def on_member_update(before, after):
    try:
        server = client.get_server(server_id)
        cursor.execute("""SELECT * FROM DiscordActivity WHERE User_ID = ?""", (after.id,))
        retn = cursor.fetchall()
        if before.nick != after.nick:
            if len(retn) == 0:
                add_member_database(after, server)
            else:
                sql = """
                           UPDATE DiscordActivity
                           SET User_Nickname = ?
                           WHERE User_ID = ?
                        """
                data = (str(after.nick), after.id)
                cursor.execute(sql, data)
                conn.commit()
                print("-Updated the user: " + after.name + " changed Nickname from *" + str(before.nick) + "* to *"
                      + str(after.nick) + "*")
        if before.roles != after.roles:
            if len(retn) == 0:
                add_member_database(after, server)
            else:
                usr_roles2 = fetch_roles(after)
                usr_roles3 = fetch_roles(before)
                sql = """
                           UPDATE DiscordActivity
                           SET Discord_Roles = ?
                           WHERE User_ID = ?
                        """
                data = (str(usr_roles2), after.id)
                cursor.execute(sql, data)
                conn.commit()
                print("-Updated the user: " + after.name + " changed Member Roles from *" + str(usr_roles3) + "* to *"
                      + str(usr_roles2) + "*")
        if str(before) != str(after):
            if len(retn) == 0:
                add_member_database(after, server)
            else:

                sql = """
                           UPDATE DiscordActivity
                           SET [User] = ?
                           WHERE User_ID = ?
                        """
                data = (str(after), after.id)
                cursor.execute(sql, data)
                conn.commit()
                print("-Updated the user: " + after.id + " changed Username from  *" + str(before) + "* to *"
                      + str(after) + "*")
    except Exception as e:
        log_exception(str(e))


@asyncio.coroutine
async def update_role(userid, role, serverid):
    try:
        cursor2.execute("""SELECT * FROM Presets""")
        conf_dat = cursor2.fetchall()
        role_active = conf_dat[0][3]
        role_inactive = conf_dat[0][4]

        server = client.get_server(serverid)
        member = server.get_member(userid)
        if str(role) == str(role_active):
            role = discord.utils.get(server.roles, name=role_active)
            await client.add_roles(member, role)
            client.remove_roles(member, role)
        else:
            if str(role) == str(role_inactive):
                role = discord.utils.get(server.roles, name=role_inactive)
                await client.add_roles(member, role)
                client.remove_roles(member, role)
            else:
                print('ERROR - NO ROLE')
        #role2 = discord.utils.get(server.roles, name=role_active)
    except Exception as e:
        log_exception(str(e))


def fetch_roles(member):
    try:
        roles_list_ob = member.roles
        roles_len = len(roles_list_ob)
        if roles_len != 0:
            temp4 = 1
            roles_st = ''
            while temp4 < roles_len:
                roles_st = roles_st + roles_list_ob[temp4].name
                if temp4 >= 1:
                    roles_st = roles_st + ','
                temp4 = temp4 + 1
            return roles_st[:-1]
        else:
            return 'NONE'
    except Exception as e:
        log_exception(str(e))


def moderator_check(userid, serverid):#check if user is in a Moderator
    try:
        server = client.get_server(serverid)
        member = server.get_member(userid)
        result = False
        mod = 'Moderator'

        roles = fetch_roles(member)

        if mod in roles:
            result = True
        return result
    except Exception as e:
        log_exception(str(e))


def in_voice_channel(member, server, channel_name):#check if member is in a specific voice channel
    try:
        voicechannel = discord.utils.get(server.channels, name=channel_name, type=discord.ChannelType.voice)
        members = voicechannel.voice_members
        memids = []
        for member in members:
            memids.append(member.id)

        if member.id in memids:
            return True
        else:
            return False
    except Exception as e:
        log_exception(str(e))


def add_member_database(member, server):
    try:
        print("Warning 0012 -- MEMBER *" + str(member) + "* NOT FOUND - Adding user to DataBase")
        roles = fetch_roles(member)
        user = str(member)
        cursor.execute("""INSERT INTO DiscordActivity VALUES (?, ?, ?, ?, 0, 0, 'NA', 'NA', ?)""",
                       (user, str(member.id), str(member.nick), 0, str(roles)))
        conn.commit()
    except Exception as e:
        log_exception(str(e))


client.loop.create_task(display())
client.loop.create_task(update_roles())
client.loop.create_task(list_servers())
client.loop.create_task(update_activity_weekly())
#client.loop.create_task(check_not_in_clan)
client.run(TOKEN)
