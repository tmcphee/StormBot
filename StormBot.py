import asyncio
import time
import datetime
import pyodbc
import discord
import sqlite3
from os import path
from discord import Game
from discord.ext.commands import Bot

#CONFIG
text_file = open("StormBot.config", "r")
BOT_CONFIG = text_file.readlines()
text_file.close()

server_addr = str(BOT_CONFIG[0]).strip()
database = str(BOT_CONFIG[1]).strip()
username = str(BOT_CONFIG[2]).strip()
password = str(BOT_CONFIG[3]).strip()
TOKEN = str(BOT_CONFIG[4])

#ODBC Driver 17 for SQL Server
#SQL SERVER
conn = pyodbc.connect('DRIVER={SQL SERVER};SERVER=' + server_addr + ';DATABASE=' + database + ';UID=' + username + ';PWD='
                      + password)
cursor = conn.cursor()

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
                          (NoVoice integer , NoMessages integer, ActiveDays integer, ActiveRole text, InactiveRole text, BeginDate text, ActiveDaysRoles integer)
                       """)
    connect.commit()
    cursor2.execute("""INSERT INTO Presets VALUES (?,?,?,?,?,?,?)""", (60, 5, 4, "ACTIVE_SB", "INACTIVE_SB", '2018-07-22 00:00:00', 2))
    connect.commit()

#server_id = '162706186272112640'#StormBot
server_id = '451097751975886858'#TestBot

BOT_PREFIX = "?"
client = Bot(command_prefix=BOT_PREFIX)


async def update_activity_weekly(): #0001
    await client.wait_until_ready()
    while not client.is_closed:
        current_weekday = datetime.datetime.now().weekday()
        await asyncio.sleep(2)
        if current_weekday == 6:
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
            await asyncio.sleep(60 * 60 * 24)


@asyncio.coroutine
async def update_roles(): #0001
    await client.wait_until_ready()
    while not client.is_closed:
        current_weekday = datetime.datetime.now().weekday()
        await asyncio.sleep(2)
        if current_weekday == 5:
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
                await asyncio.sleep(80)


@client.event#0004
async def on_ready():
    #await client.change_presence(game=Game(name="TESTING - IN DEVELOPMENT"))#?help
    print("********************************************Login*Details***********************************************")
    print("     Logged in as " + client.user.name)
    print("     Client User ID: " + client.user.id)
    print("     Invite at: https://discordapp.com/oauth2/authorize?client_id=" + client.user.id + "&scope=bot")
    print("********************************************************************************************************")


async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("********************************************Current*Servers*********************************************")
        for server in client.servers:
            print("     " + str(server.name) + " (Members: " + str(len(server.members)) + ") [" + str(server.id) + "]")
        print("********************************************************************************************************")
        await asyncio.sleep(60*60)


@client.event#0009
async def display():
    await client.wait_until_ready()
    while not client.is_closed:
        await client.change_presence(game=Game(name="?help"))  #?help
        await asyncio.sleep(20)
        await client.change_presence(game=Game(name="WATCHDOG (ACTIVE)"))
        await asyncio.sleep(5)
        await client.change_presence(game=Game(name="DEV: ZombieEar#0493"))
        await asyncio.sleep(2)


@client.event#0006
async def on_voice_state_update(before, after):
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


@client.event#0007
@asyncio.coroutine
async def on_message(message):
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
                emb.add_field(name='Previous Week Activity(7 days)', value=user_dat[0][8], inline=True)
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
                                                               ' \'?set def_message Value\''.format(message))
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
            if message.content.startswith(BOT_PREFIX + 'set inactive_role'):
                if message.content == (BOT_PREFIX + 'set inactive_role'):
                    await client.send_message(message.channel, 'No value specified. To Update '
                                                               'Default Inactive Role enter'
                                                               ' \'?set def_message Value\''.format(message))
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
            if message.content.startswith(BOT_PREFIX + 'set display'):
                cursor2.execute("""SELECT * FROM Presets""")
                conf_dat = cursor2.fetchall()

                emb3 = (discord.Embed(title="Storm Bot Presets:", color=0xee1b15))
                emb3.add_field(name='Voice Minutes', value=conf_dat[0][0], inline=True)
                emb3.add_field(name='Messages', value=conf_dat[0][1], inline=True)
                emb3.add_field(name='Active Days', value=conf_dat[0][2], inline=True)
                emb3.add_field(name='Active Role', value=conf_dat[0][3], inline=True)
                emb3.add_field(name='Inactive Role', value=conf_dat[0][4], inline=True)
                emb3.add_field(name='Active Days For Roles Update', value=conf_dat[0][6], inline=True)
                await client.send_message(message.channel, embed=emb3)
            if message.content.startswith(BOT_PREFIX + 'set help'):
                emb = (discord.Embed(title="Set Help Commands:", color=0xee1b15))
                emb.add_field(name='?set def_voice', value='Use \'?set def_voice Value\' to update the Default Voice preset value. Example (?set def_voice 60)', inline=True)
                emb.add_field(name='?set def_message', value='Use \'?set def_message Value\' to update the Default Messages preset value. Example (?set def_message 5)', inline=True)
                emb.add_field(name='?set active_role', value='Use \'?set active_role Value\' to update the Default Active Role preset value. Example (?set active_rolee ACTIVE)', inline=True)
                emb.add_field(name='?set inactive_role', value='Use \'?set inactive_role Value\' to update the Default Inactive Role preset value. Example (?set inactive_role INACTIVE)', inline=True)
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


@client.event#0008
async def on_member_join(member):
    roles = fetch_roles(member)
    user = str(member)
    cursor.execute("""INSERT INTO DiscordActivity VALUES (?, ?, ?, 0, 0, 0, 'NA', 'NA', ?)""", (user, str(member.id)
                                                                                      , str(member.nick), str(roles)))
    conn.commit()
    embed = discord.Embed(title='Welcome to Collective Conscious!', color=0x05dd00)
    embed.add_field(name='/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/', value='>', inline=False)
    embed.add_field(name='We are excited that you are here, please apply to join the clan in #clan-application', value='>', inline=False)
    embed.add_field(name='For server rules see #rules', value='>', inline=False)
    embed.add_field(name='For any questions regarding you application status or discord roles consult a @Moderator', value='>', inline=False)
    embed.add_field(name='All CoCo Clan members are required to change their nickname to their Battle Tag. This can be done by typing \'?change_nick BattleTag\'', value='(EX. \'?change_nick StormBot#1234\')', inline=False)
    embed.set_footer(text='This is an automated message')
    await client.send_message(member, embed=embed)
    print("-on_member_join      User Joined      User:" + user)
    #embed=embed

@client.event#0009
async def on_member_remove(member):
    userid = str(member.id)
    user = str(member)
    cursor.execute("""DELETE FROM DiscordActivity WHERE User_ID = ?""", (userid, ))
    conn.commit()
    cursor.execute("""DELETE FROM DiscordActivityArchive WHERE User_ID = ?""", (userid,))
    conn.commit()
    print("-on_member_remove   User Left     User:" + user)


@client.event
async def on_member_update(before, after):
    cursor.execute("""SELECT * FROM DiscordActivity WHERE User_ID = ?""", (after.id,))
    retn = cursor.fetchall()
    if before.nick != after.nick:
        if len(retn) == 0:
            print("Warning 0009 -- MEMBER *" + str(after) + "* NOT FOUND - Adding user to DataBase")
            roles = fetch_roles(after)
            user = str(after)
            cursor.execute("""INSERT INTO DiscordActivity VALUES (?, ?, ?, ?, 0, 0, 'NA', 'NA', ?)""",
                           (user, str(after.id), str(after.nick), 0, str(roles)))
            conn.commit()
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
            print("Warning 0010 -- MEMBER *" + str(after) + "* NOT FOUND - Adding user to DataBase")
            roles = fetch_roles(after)
            user = str(after)
            cursor.execute("""INSERT INTO DiscordActivity VALUES (?, ?, ?, ?, 0, 0, 'NA', 'NA', ?)""",
                           (user, str(after.id), str(after.nick), 0, str(roles)))
            conn.commit()
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
            print("Warning 0011 -- MEMBER *" + str(after) + "* NOT FOUND - Adding user to DataBase")
            roles = fetch_roles(after)
            user = str(after)
            cursor.execute("""INSERT INTO DiscordActivity VALUES (?, ?, ?, ?, 0, 0, 'NA', 'NA', ?)""",
                           (user, str(after.id), str(after.nick), 0, str(roles)))
            conn.commit()
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


@asyncio.coroutine
async def update_role(userid, role, serverid):
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


def fetch_roles(member):
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


def moderator_check(userid, serverid):#check if user is in a Moderator
    server = client.get_server(serverid)
    member = server.get_member(userid)
    result = False
    mod = 'Moderator'

    roles = fetch_roles(member)

    if mod in roles:
        result = True
    return result


def in_voice_channel(member, server, channel_name):#check if member is in a specific voice channel
    voicechannel = discord.utils.get(server.channels, name=channel_name, type=discord.ChannelType.voice)
    members = voicechannel.voice_members
    memids = []
    for member in members:
        memids.append(member.id)

    if member.id in memids:
        return True
    else:
        return False


client.loop.create_task(display())
client.loop.create_task(update_roles())
client.loop.create_task(list_servers())
client.loop.create_task(update_activity_weekly())
client.run(TOKEN)
