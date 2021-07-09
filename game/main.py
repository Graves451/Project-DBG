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

#add a function to check the profile of others

#finish the combat things

#wfurther troubleshoot the change class function

'''
commands tested:
.char
.daily
.weekly
.bank
.equip
.combat now works but still needs to balanced
'''

#still needs to work on shop and balancing and adding new items

token = "NjEzMTc4MDQwMDMzNDc2NjE5.XVtIjQ.aqegtZrJa9SMkoXt3ld7lr7AetU"

entrance_id = 816195177113714708

id = {
    "guild":811159707757707304,
    "entrance":816195177113714708,
    "outskirts":811783861851389953,
    "server":811159707757707304,
    "role":{
        "The-Far-East":811782727895613451,
        "The-Lost-Peninsula":811782734522351636,
        "The-Caspian-Confederation":811782735323856917,
        "Main-Island":861494656831717396
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

    async def setup_messages(self):
        entrance_channel = self.client.get_channel(id["entrance"])
        deleted = await entrance_channel.purge(limit=100)
        entrance_msg = await entrance_channel.send("welcome who do you want to be?")
        self.entrance_msg_id = entrance_msg.id
        await entrance_msg.add_reaction("🚩")

    def prepare_client(self):
        @self.client.event
        async def on_ready():
            self.entrance_msg_id = 0
            await self.setup_messages()
            self.guild = await self.client.fetch_guild(id["server"])
            print("ready for an adventure")
            spawn_bosses.start()

        @tasks.loop(seconds=30.0)
        async def spawn_bosses():
            print("spawning enemies")
            channel = self.client.get_channel(id["outskirts"])
            enemy_data = character.generate_enemy("enemy",10,"archer",hash_string("iron sword"))
            enemy_embed = character.create_character_embed(enemy_data)
            msg = await channel.send(embed=enemy_embed)
            enemy_data[0] = msg.id
            db.add_enemy(enemy_data)
            await msg.add_reaction("⚔️")

        @self.client.event
        async def on_message_delete(message):
            print("msg deleted")

        @self.client.event
        async def on_reaction_add(reaction,user):
            if user != self.client.user:
                msg = reaction.message
                if msg.id == self.entrance_msg_id:
                    if not db.get_user(user.id) and reaction.emoji in ["🚩"]:
                        member = discord.utils.get(msg.guild.members, id=user.id)
                        await member.add_roles(msg.guild.get_role(id["role"]["Main-Island"]))
                        db.add_user(user.id)
                        db.add_character(character.generate_character(user.id,"mercenary","archer",hash_string("fist")))
                        db.add_bank(user.id,100)
                elif db.get_enemy(msg.id) is not None and reaction.emoji == "⚔️":
                    fight = game.battle(list(db.get_character(user.id)),list(db.get_enemy(msg.id)))
                    player_character, enemy_character = fight.get_characters()
                    db.update_character(player_character)
                    await reaction.message.channel.send(embed=fight.combat_result_embed())
                    if enemy_character[6] == 0:
                        db.delete_enemy(msg.id)
                        await msg.delete()
                        return
                    db.update_enemy(enemy_character)
                    await msg.edit(embed=character.create_character_embed(enemy_character))

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
                StatEmbed = character.create_character_embed(char_data)
                print(StatEmbed)
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
                weapon_id = hash_string(message_contents)
                if db.get_user_item(user.id,weapon_id) is not None:
                    if db.get_weapon(weapon_id) is not None:
                        character_data = list(db.get_character(user.id))
                        if db.get_weapon(weapon_id)[1] in character.get_class_weapons(character_data[3]):
                            if character_data[2] != hash_string("fist"):
                                db.add_item(user.id,character_data[2],1)
                            character_data[2] = weapon_id
                            db.add_item(user.id,weapon_id,-1)
                            db.update_character(character_data)
                            await message.channel.send(f"{message_contents} has been equiped")
                            return
                        await message.channel.send(f"{character_data[3]} cannot equip {db.get_weapon(weapon_id)[1]}")
                        return
                    await message.channel.send(f"{message_contents} is not a valid weapon")
                    return
                await message.channel.send(f"you don't have a {message_contents}")

            if message.content.startswith(command_prefix+"daily"):
                user_data = list(db.get_user(user.id))
                dif = datetime.datetime.now()-user_data[1]
                if dif.days >= 1:
                    user_data[1] = datetime.datetime.now()
                    db.update_user(user_data)
                    update_money(user.id,50)
                    await message.channel.send(f"{user.mention} has claimed his daily 50 bucks")
                    return
                await message.channel.send(f"{str(datetime.timedelta(seconds=86400-int(dif.total_seconds())))} left")

            if message.content.startswith(command_prefix+"weekly"):
                user_data = list(db.get_user(user.id))
                dif = datetime.datetime.now()-user_data[2]
                if dif.days >= 7:
                    user_data[2] = datetime.datetime.now()
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

            if message.content.startswith(command_prefix+"change "):
                target_class = message.content[8:]
                print(db.get_class("mage"))
                print(target_class)
                print(db.get_class(target_class))
                if db.get_class(target_class) is None:
                    await message.channel.send(f"{target_class} is not a valid class")
                    return
                character_data = list(db.get_character(user.id))
                if character.change_class(character_data,target_class):
                    character_data[3] = target_class
                    db.update_character(character_data)
                    await message.channel.send(f"{character_data[1]}'s class has been changed to {target_class}")
                else:
                    await message.channel.send(f"{character_data[1]} doesn't meet the requirement for {target_class}")

            if message.content.startswith(command_prefix+"level"):
                user_data = list(db.get_character(user.id))
                user_data[5] = 500
                user_data = character.level_check(user_data)
                db.update_character(user_data)
                await message.channel.send(f"{user.mention} leveled up!")

#user: user_id,faction,daily,weekly,first
#character: user_id, name, class, level, exp, health, max_health, strength, magic, speed, defense, logic
def update_money(user_id,amount):
    user_money = list(db.get_bank(user_id))
    if amount < 0:
        if user_money[1] < -amount:
            return False
    db.update_bank(user_id,user_money[1]+amount)
    return True

obj = RpgBot(token)
obj.run()
