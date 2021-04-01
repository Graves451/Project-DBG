import database
import character
import game

import discord
from discord.ext.commands import Bot
from discord.ext import tasks, commands
import datetime
import random
import hashlib

#make the entrance text a little more complex


#add a battle weapon, maybe armour? for the character

#givev the character in a proper weapon id in the start
#finish the graphic table properly

#add a function to check the profile of others

#finish the combat things


token = "NjEzMTc4MDQwMDMzNDc2NjE5.XVtIjQ.mQQMnAT4Gd6GYu5PqJLoMiacZjY"

entrance_id = 816195177113714708

id = {
    "guild":811159707757707304,
    "entrance":816195177113714708,
    "outskirts":811783861851389953,
    "server":811159707757707304,
    "role":{
        "red":811782727895613451,
        "black":811782734522351636,
        "white":811782735323856917
    }
}

command_prefix = "."

db = database.Database()
db.delete_table()
#db.clear_game_data()
db.setup()
db.load_game_data()

def hash_string(string_input):
    return int(hashlib.sha256(string_input.encode('utf-8')).hexdigest(), 16) % 10**8

class RpgBot:
    def __init__(self, token):
        self.client = Bot(command_prefix=command_prefix)
        self.token = token
        self.prepare_client()

    def run(self):
        self.client.run(self.token)

    def get_discord_emoji(self,emoji_id):
        return self.client.get_emoji(int(emoji_id))

    async def create_enemy_embed(self,enemy_data):
        enemyembed = discord.Embed(colour=discord.Colour.red(),description=f"`CLASS` {enemy_data[2]}")
        enemyembed.set_author(name=f"LVL.{str(enemy_data[3])} {enemy_data[0].upper()}")
        enemyembed.set_thumbnail(url=db.get_graphic(enemy_data[2])[1])
        enemyembed.add_field(name=f"{enemy_data[5]}/{enemy_data[6]} ❤️",value=f"`STR` {enemy_data[7]}\n`MAG` {enemy_data[8]}\n`SPD` {enemy_data[9]}\n`DEF` {enemy_data[10]}\n`LOG` {enemy_data[11]}")
        item_data = db.get_weapon(enemy_data[1])
        enemyembed.add_field(name=f"{self.get_discord_emoji(db.get_graphic(item_data[1])[1])} {db.get_item(enemy_data[1])[1]}",value=f"`PWR` {item_data[2]}\n`CRT` {item_data[3]}")
        return enemyembed

    async def setup_messages(self):
        entrance_channel = self.client.get_channel(id["entrance"])
        deleted = await entrance_channel.purge(limit=100)
        entrance_msg = await entrance_channel.send("welcome who do you want to be?")
        self.entrance_msg_id = entrance_msg.id
        await entrance_msg.add_reaction("🚩")
        await entrance_msg.add_reaction("🏴")
        await entrance_msg.add_reaction("🏳️")

    def prepare_client(self):
        @self.client.event
        async def on_ready():
            self.entrance_msg_id = 0
            await self.setup_messages()
            self.guild = await self.client.fetch_guild(id["server"])
            print("ready for an adventure")
            spawn_bosses.start()

        @tasks.loop(seconds=45.0)
        async def spawn_bosses():
            outskirt_channel = self.client.get_channel(id["outskirts"])
            boss_data = character.generate_boss(25)
            enemy_embed = await self.create_enemy_embed(boss_data)
            msg = await outskirt_channel.send(embed=enemy_embed,delete_after=300.0)
            db.add_boss(msg.id,boss_data)
            await msg.add_reaction("⚔️")
            print("spawning boss")

        @self.client.event
        async def on_message_delete(message):
            print("msg dleterd")

        @self.client.event
        async def on_reaction_add(reaction,user):
            if user != self.client.user:
                if reaction.message.id == self.entrance_msg_id:
                    if not db.get_user(user.id) and reaction.emoji in ["🚩","🏳️","🏴"]:
                        member = discord.utils.get(reaction.message.guild.members, id=user.id)
                        if str(reaction) == "🚩":
                            db.add_user(user.id,"red")
                            db.add_character(user.id,"mercenary","archer",hash_string("stone sword"))
                            db.add_bank(user.id,100)
                            await member.add_roles(reaction.message.guild.get_role(id["role"]["red"]))
                        if str(reaction) == "🏳️":
                            db.add_user(user.id,"white")
                            db.add_character(user.id,"mercenary","archer",hash_string("stone sword"))
                            db.add_bank(user.id,100)
                            await member.add_roles(reaction.message.guild.get_role(id["role"]["white"]))
                        if str(reaction) == "🏴":
                            db.add_user(user.id,"black")
                            db.add_character(user.id,"mercenary","archer",hash_string("stone sword"))
                            db.add_bank(user.id,100)
                            await member.add_roles(reaction.message.guild.get_role(id["role"]["black"]))
                elif db.get_boss(reaction.message.id) is not None and reaction.emoji == "⚔️":
                    player_data = list(db.get_character(user.id))
                    if player_data[6] == 0:
                        await reaction.message.channel.send(f"{user.mention} your health is too low, go take a rest")
                        return
                    boss_data = list(db.get_boss(reaction.message.id))
                    player_data, boss_data, damage1, damage2 = character.combat(player_data,boss_data)
                    db.update_character(player_data)
                    enemyembed = await self.create_enemy_embed(boss_data[1:])
                    await reaction.message.edit(embed=enemyembed)
                    db.update_boss(boss_data)
                    await reaction.message.channel.send(f"{user.mention} - {damage1}\n {boss_data[1]} - {damage2}")

        @self.client.event
        async def on_message(message):
            user = message.author
            if message.author == self.client.user:
                return
            if message.content.startswith(command_prefix+"ping"):
                await message.channel.send(f"pong! {round(self.client.latency*1000)}ms")

            if message.content.startswith(command_prefix+"stat"):
                await message.channel.send(db.get_user(user.id))

            if message.content.startswith(command_prefix+"char"):
                char_data = db.get_character(user.id)
                StatEmbed = discord.Embed(colour=discord.Colour.red(),description=f"`LVL` {str(char_data[4])}\n`EXP` {str(int(char_data[5]*100/character.next_level(char_data[5])))}%")
                StatEmbed.set_author(name=char_data[3].upper())
                #make sure to change this
                StatEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/816863665194139689/817207665432330240/Gangrel2.gif")
                stat_name = f"{str(char_data[6])}/{str(char_data[7])} ❤️"
                stat_stats = f"`STR` {char_data[8]}\n`MAG` {char_data[9]}\n`SPD` {char_data[10]}\n`DEF` {char_data[11]}\n`LOG` {char_data[12]}"
                StatEmbed.add_field(name=stat_name,value=stat_stats)
                item_data = db.get_weapon(char_data[2])
                StatEmbed.add_field(name=db.get_item(char_data[2])[1],value=f"`PWR` {item_data[2]}\n`CRT` {item_data[3]}")
                await message.channel.send(embed=StatEmbed)

            if message.content.startswith(command_prefix+"inv"):
                await message.channel.send(db.get_inventory(user.id))

            if message.content.startswith(command_prefix+"bank"):
                await message.channel.send(db.get_bank(user.id))

            if message.content.startswith(command_prefix+"shop"):
                game.update_shop(game.generate_shop())
                print(game.get_shop())

            if message.content.startswith(command_prefix+"use "):
                target_item = message.content[5:]
                print(target_item)
                if db.get_user_item(user.id,hash_string(message_contents)) is not None:
                    if db.get_usable(hash_string(target_item)) is not None:
                        character_data = list(db.get_character(user.id))
                await message.channel.send(f"you don't have a {target_item}")

            if message.content.startswith(command_prefix+"equip "):
                message_contents = message.content[7:]
                print(message_contents)
                if db.get_user_item(user.id,hash_string(message_contents)) is not None:
                    if db.get_weapon(hash_string(message_contents)) is not None:
                        character_data = list(db.get_character(user.id))
                        db.add_item(user.id,character_data[2],1)
                        character_data[2] = hash_string(message_contents)
                        db.add_item(user.id,hash_string(message_contents),-1)
                        db.update_character(character_data)
                        await message.channel.send(f"{message_contents} has been equiped")
                        return
                    await message.channel.send(f"{message_contents} is not a valid weapon")
                    return
                await message.channel.send(f"you don't have a {message_contents}")

            if message.content.startswith(command_prefix+"daily"):
                user_data = list(db.get_user(user.id))
                dif = datetime.datetime.now()-user_data[2]
                if dif.days >= 1:
                    user_data[2] = datetime.datetime.now()
                    db.update_user(user_data)
                    update_money(user.id,50)
                    await message.channel.send(f"{user.mention} has claimed his daily 50 bucks")
                    return
                await message.channel.send(f"{str(datetime.timedelta(seconds=86400-int(dif.total_seconds())))} left")

            if message.content.startswith(command_prefix+"weekly"):
                user_data = list(db.get_user(user.id))
                dif = datetime.datetime.now()-user_data[3]
                if dif.days >= 7:
                    user_data[3] = datetime.datetime.now()
                    db.update_user(user_data)
                    update_money(user.id,1000)
                    await message.channel.send(f"{user.mention} has claimed his weekly 1000 bucks")
                    return
                await message.channel.send(f"{str(datetime.timedelta(seconds=604800-int(dif.total_seconds())))} left")

            if message.content.startswith(command_prefix+"buy "):
                message_contents = message.content.split(" ")
                amount = 1
                if message_contents[-1].isdigit():
                    item_name = " ".join(message_contents[1:-1])
                    amount = int(message_contents[-1])
                else:
                    item_name = " ".join(message_contents[1:])
                if db.get_item(hash_string(item_name)) is None:
                    await message.channel.send(f"{item_name} is not a valid item")
                    return
                if update_money(user.id,-db.get_item(hash_string(item_name))[2]*amount):
                    db.add_item(user.id,hash_string(item_name),amount)
                    await message.channel.send(f"{user.mention} bought {str(amount)} X {item_name}")
                    return
                await message.channel.send("you don't have enough money, my friend")

            if message.content.startswith(command_prefix+"sell "):
                user_inv = db.get_inventory(user.id)
                message_contents = message.content.split(" ")
                amount = 1
                if message_contents[-1].isdigit():
                    item_name = " ".join(message_contents[1:-1])
                    amount = int(message_contents[-1])
                else:
                    item_name = " ".join(message_contents[1:])
                if item_name not in user_inv.keys():
                    await message.channel.send(f"{item_name} is not in your inventory")
                    return
                if user_inv[item_name] >= amount:
                    update_money(user.id,db.get_item(hash_string(item_name))[2]*amount)
                    await message.channel.send(f"{user.mention} sold {str(amount)} X {item_name}")
                    db.add_item(user.id,hash_string(item_name),-user_inv[item_name])
                    print(f"{str(user.id)} has removed {str(amount)} X {item_name}")
                    return
                await message.channel.send(f"you don't have enough {item_name}, my friend")

            if message.content.startswith(command_prefix+"level"):
                user_data = list(db.get_character(user.id))
                user_data[5] = 500
                user_data = character.level_check(user_data)
                db.update_character(user_data)
                await message.channel.send(f"{user.mention} leveled up!")

#user: user_id,faction,daily,weekly,first
#character: user_id, name, class, level, exp, health, max_health, strength, magic, speed, defense, logic
def update_money(user_id,amount):
    print(user_id)
    user_money = list(db.get_bank(user_id))
    if amount < 0:
        if user_money[1] < -amount:
            return False
    user_money[1]+=amount
    print(user_money)
    db.update_bank(user_money)
    print(f"{user_id} has gained "+str(amount))
    return True

obj = RpgBot(token)
obj.run()
