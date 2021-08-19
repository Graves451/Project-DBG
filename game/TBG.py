import database
import character
import game

import discord
from discord.ext.commands import Bot
from discord.ext import tasks, commands
import datetime
import random
import asyncio

import logging

#add a boss thing and show everyone it afterwards

#wfurther troubleshoot the change class function

#still needs to work on shop and balancing and adding new items

token = "NjEzMTc4MDQwMDMzNDc2NjE5.XVtIjQ.H7OKh-4O0BtAvtep3gbPQQZJYo0"

campaigns = {}

id = {
    "guild":811159707757707304,
    "channel":{
        "great-plains":877292758979727390,
        "forest":877292847215292526,
        "mountain":877292917859954688
    },
    "role":{
        "First Floor":877285049324679188,
        "Second Floor":877285228807336027,
        "Third Floor":877285221039501352,
        "Main Island":877288700613132308
    }
}

command_prefix = "."

help_string = '''```
.ping    returns the ping of the bot
.daily   gives the player 50 gold coins
.weekly  gives the player 100 gold coins

.char    returns the description of your character
.inv     returns what's in your inventory
.bank    returns how much money you have

.use <target_item>     uses a consumable item
.change <target_class> changes the user to the target class (needs test seal)

.battle  spawns an enemy for you to fight
.raid    costs 100 dollars and spawns a boss
```'''

stats_target = ["HP","Max HP","STR","MAG","SPD","DEF","LOG"]

ongoing_campaigns = {}

class TBG:
    def __init__(self, token):
        intents = discord.Intents.default()
        intents.members = True
        self.client = Bot(command_prefix=command_prefix,intents=intents)
        self.client.remove_command("help")
        self.token = token
        self.prepare_client()

    def run(self):
        self.client.run(self.token)

    def get_discord_emoji(self,emoji_id):
        return self.client.get_emoji(int(emoji_id))

    async def setup_player(self,user):
        if db.get_user(user.id) is None:
            await user.add_roles([self.guild.get_role(id["role"]["Main Island"]),self.guild.get_role(id["role"]["First Floor"])])
            db.add_user(user.id)
            db.add_character(character.generate_character(user.id,user.display_name,"swordsmen",game.hash_string("stone sword")))
            db.add_bank(user.id,100)

    async def setup_all_players(self):
        async for member in self.guild.fetch_members(limit=150):
            if not member.bot:
                await self.setup_player(member)

    def create_enemy_embed(self,char_data):
        StatEmbed = discord.Embed(colour=discord.Colour.red(),description=f"`LVL` {str(char_data[4])}\n`CLS` {char_data[3]}")
        StatEmbed.set_author(name=char_data[1].upper())
        StatEmbed.set_thumbnail(url=db.get_graphic(char_data[3])[1])
        StatEmbed.add_field(name=f"{str(char_data[6])}/{str(char_data[7])} ❤️",value=f"`STR` {char_data[8]}\n`MAG` {char_data[9]}\n`SPD` {char_data[10]}\n`DEF` {char_data[11]}\n`LOG` {char_data[12]}")
        item_data, itemname = db.get_weapon(char_data[2]), db.get_item(char_data[2])[1]
        StatEmbed.add_field(name=f"{self.get_discord_emoji(db.get_graphic(itemname)[1])} {itemname}",value=f"`PWR` {item_data[2]}\n`CRT` {item_data[3]}")
        enemy_loot = ""
        for loot_items in char_data[13].split("-"):
            loot_values = loot_items.split(".")
            enemy_loot += f"{loot_values[0]} - {loot_values[1]} "
        if char_data[14] != "": StatEmbed.set_footer(text=char_data[14])
        return StatEmbed

    def create_character_embed(self,char_data):
        StatEmbed = discord.Embed(colour=discord.Colour.light_grey(),description=f"`LVL` {str(char_data[4])} ({str(int(char_data[5]*100/character.next_level(char_data[5])))}%) \n `CLS` {char_data[3]}")
        StatEmbed.set_author(name=char_data[1].upper())
        StatEmbed.set_thumbnail(url=db.get_graphic(char_data[3])[1])
        StatEmbed.add_field(name=f"{str(char_data[6])}/{str(char_data[7])} ❤️",value=f"`STR` {char_data[8]}\n`MAG` {char_data[9]}\n`SPD` {char_data[10]}\n`DEF` {char_data[11]}\n`LOG` {char_data[12]}")
        item_data, itemname = db.get_weapon(char_data[2]), db.get_item(char_data[2])[1]
        StatEmbed.add_field(name=f"{self.get_discord_emoji(db.get_graphic(itemname)[1])} {itemname}",value=f"`PWR` {item_data[2]}\n`CRT` {item_data[3]}")
        return StatEmbed

    def create_inventory_embed(self,inventory_data):
        weapons, usables = "",""
        for item_name in inventory_data:
            if db.get_usable(game.hash_string(item_name)) is not None: usables += f"{self.get_discord_emoji(db.get_graphic(item_name)[1])} {item_name} \n"*inventory_data[item_name]
            if db.get_weapon(game.hash_string(item_name)) is not None: weapons += f"{self.get_discord_emoji(db.get_graphic(item_name)[1])} {item_name} \n"*inventory_data[item_name]
        InventoryEmbed = discord.Embed(colour=discord.Colour.green())
        InventoryEmbed.set_author(name="INVENTORY")
        if weapons != "": InventoryEmbed.add_field(name="`Weapons`",value=weapons)
        if usables != "": InventoryEmbed.add_field(name="`Usables`",value=usables)
        return InventoryEmbed

    def prepare_client(self):
        @self.client.event
        async def on_ready():
            self.guild = await self.client.fetch_guild(811159707757707304)
            await self.setup_all_players()
            print("ready for an adventure")

        @self.client.event
        async def on_message_delete(message):
            TBG_logger.info("message deleted")

        @self.client.event
        async def on_member_join(member):
            await member.add_roles(self.guild.get_role(id["role"]["Main Island"]))
            await member.add_roles(self.guild.get_role(id["role"]["First Floor"]))
            print(f"{member.name} joined")
            await self.setup_player(member)

        @self.client.event
        async def on_reaction_add(reaction,user):
            if user != self.client.user:
                msg = reaction.message
                if user.id in ongoing_campaigns and msg.id not in ongoing_campaigns[user.id].enemy_ids:
                    await msg.channel.send("unable to fight outside of a campaign, during a campaign")
                    return
                if db.get_enemy(msg.id) is not None and reaction.emoji == "⚔️":
                    fight = game.battle(list(db.get_character(user.id)),list(db.get_enemy(msg.id)))
                    player_character, enemy_character = fight.get_characters()
                    db.update_character(player_character)
                    await reaction.message.channel.send(embed=fight.combat_result_embed())
                    if enemy_character[6] == 0:
                        db.delete_enemy(msg.id)
                        if user.id in ongoing_campaigns.keys() and msg.id in ongoing_campaigns[user.id].enemy_ids: await ongoing_campaigns[user.id].remove_enemy(msg.id)
                        await msg.edit(embed=self.create_enemy_embed(enemy_character))
                        return
                    db.update_enemy(enemy_character)
                    await msg.edit(embed=self.create_enemy_embed(enemy_character))

        @self.client.command()
        async def ping(ctx):
            user = ctx.message.author
            await ctx.message.channel.send(f"pong! {round(self.client.latency*1000)}ms")

        @self.client.command()
        async def help(ctx):
            await ctx.message.channel.send(help_string)

        @self.client.command()
        async def info(ctx):
            user = ctx.message.author
            message_contents = ctx.message.content[6:]
            usable_data = db.get_usable(game.hash_string(message_contents))
            weapon_data = db.get_weapon(game.hash_string(message_contents))
            class_data = db.get_class(message_contents)
            if usable_data is not None:
                InfoEmbed = discord.Embed(colour=discord.Colour.light_grey(),description=db.get_item(game.hash_string(message_contents))[4])
                InfoEmbed.set_author(name=message_contents)
                InfoEmbed.set_thumbnail(url=self.get_discord_emoji(db.get_graphic(message_contents)[1]).url)
                InfoEmbed.add_field(name="`TARGET`",value=stats_target[usable_data[2]-6])
                InfoEmbed.add_field(name="`AMT`",value=usable_data[1])
                await ctx.message.channel.send(embed=InfoEmbed)
            elif weapon_data is not None:
                InfoEmbed = discord.Embed(colour=discord.Colour.light_grey(),description=db.get_item(game.hash_string(message_contents))[4])
                InfoEmbed.set_author(name=message_contents)
                InfoEmbed.set_thumbnail(url=self.get_discord_emoji(db.get_graphic(message_contents)[1]).url)
                InfoEmbed.add_field(name="`TYPE`",value=weapon_data[1])
                InfoEmbed.add_field(name="`PWR`",value=weapon_data[2])
                InfoEmbed.add_field(name="`CRT`",value=weapon_data[3])
                await ctx.message.channel.send(embed=InfoEmbed)
            elif class_data is not None:
                InfoEmbed = discord.Embed(colour=discord.Colour.light_grey(),description=class_data[2])
                InfoEmbed.set_author(name=message_contents)
                InfoEmbed.set_thumbnail(url=db.get_graphic(message_contents)[1])
                InfoEmbed.add_field(name="`GROWTH RATE`",value=class_data[1])
                if class_data[3] == "": InfoEmbed.add_field(name="`ATTRIBUTE`",value="None")
                else: InfoEmbed.add_field(name="`ATTRIBUTE`",value=class_data[3])
                InfoEmbed.add_field(name="`WEAPON CHOICE`",value=class_data[4])
                await ctx.message.channel.send(embed=InfoEmbed)
            else:
                await ctx.message.channel.send(f"{message_contents} does not exist")

        @self.client.command()
        async def char(ctx):
            user = ctx.message.author
            char_data = db.get_character(user.id)
            StatEmbed = self.create_character_embed(char_data)
            await ctx.message.channel.send(embed=StatEmbed)

        @self.client.command()
        async def profile(ctx):
            target_id = ctx.message.content[9:]
            if not target_id.isdigit():
                await ctx.message.channel.send(f"{target_id} is not a number")
                return
            char_data = db.get_character(int(target_id))
            if char_data is None:
                await ctx.message.channel.send(f"{target_id} is not a valid user")
                return
            StatEmbed = self.create_character_embed(char_data)
            await ctx.message.channel.send(embed=StatEmbed)

        @self.client.command()
        async def inv(ctx):
            await ctx.message.channel.send(embed=self.create_inventory_embed(db.get_inventory(ctx.message.author.id)))

        @self.client.command()
        async def bank(ctx):
            await ctx.message.channel.send(f"You have {db.get_bank(ctx.message.author.id)[1]}{self.get_discord_emoji(822330641559191573)}")

        @self.client.command()
        async def battle(ctx):
            if ctx.message.channel.id not in id["channel"].values():
                await ctx.message.channel.send("This is not a place for battle")
                return
            else:
                level = 5
                if ctx.message.channel.id == id["channel"]["great-plains"]:
                    level = random.randint(5,20)
                elif ctx.message.channel.id == id["channel"]["forest"]:
                    level = random.randint(20,40)
                elif ctx.message.channel.id == id["channel"]["mountain"]:
                    level = random.randint(40,70)
                character_class = character.determine_enemy_class(level)
                enemy_data = character.generate_enemy("enemy",level,character_class,game.hash_string(character.generate_class_weapon(character_class,level)))
                enemy_embed = self.create_enemy_embed(enemy_data)
                msg = await ctx.message.channel.send(embed=enemy_embed)
                enemy_data[0] = msg.id
                db.add_enemy(enemy_data)
                await msg.add_reaction("⚔️")

        @self.client.command()
        async def raid(ctx):
            if ctx.message.channel.id == id["channel"]["great-plains"]:
                character_class = "Fortress"
                level = 20
            elif ctx.message.channel.id == id["channel"]["forest"]:
                character_class = "Sharpshooter"
                level = 40
            elif ctx.message.channel.id == id["channel"]["mountain"]:
                character_class = "Warlord"
                level = 60
            user = ctx.message.author
            if db.get_character(user.id)[4] < level:
                await ctx.message.channel.send(f"you need to be at least level {level} to challenge this boss")
                return
            if not game.update_money(user.id,-100):
                await ctx.message.channel.send("you need at least 100 dollars to challenge the boss")
                return
            level = max(db.get_character(user.id)[4],level)
            boss_data = character.generate_enemy("boss",level,character_class,game.hash_string(character.generate_class_weapon(character_class,level)))
            boss_embed = self.create_enemy_embed(boss_data)
            msg = await ctx.message.channel.send(embed=boss_embed)
            boss_data[0] = msg.id
            db.add_enemy(boss_data)
            await msg.add_reaction("⚔️")
            TBG_logger.info(f"spawning a {character_class}")

        @self.client.command()
        async def campaign(ctx):
            if db.get_campaign(ctx.message.channel.name) is None:
                await ctx.message.channel.send(f"{ctx.message.channel.name} is not a proper place to campaign")
                return
            campaign_msg = await ctx.message.channel.send("starting")
            await ctx.message.author.send(f"```You have started the {ctx.message.channel.name} campaign```")
            campaign = game.campaign(ctx.message.author,ctx.message.channel.name,ctx.message.guild)
            ongoing_campaigns[ctx.message.author.id] = campaign
            await campaign.spawn_wave()


        @self.client.command()
        async def use(ctx):
            user = ctx.message.author
            target_item = ctx.message.content[5:]
            if db.get_user_item(user.id,game.hash_string(target_item)) is None:
                await ctx.message.channel.send(f"you don't have a {target_item}")
                return
            item_data = db.get_usable(game.hash_string(target_item))
            if item_data is None or item_data[0] == game.hash_string("transportation ticket") or item_data[0] == game.hash_string("test seal"):
                await ctx.message.channel.send(f"{target_item} is not a valid item")
                return
            char_data = list(db.get_character(user.id))
            db.add_item(user.id,game.hash_string(target_item),-1)
            char_data[item_data[1]]+=item_data[2]
            char_data = character.character_check(char_data)
            db.update_character(char_data)
            await ctx.message.channel.send(f"you gained {item_data[2]} {stats_target[item_data[1]-6]}")

        @self.client.command()
        async def travel(ctx):
            user = ctx.message.author
            target_location = ctx.message.content[8:]
            char_data = list(db.get_character(user.id))
            locations = ["Main Island"]
            if char_data[4] >= 10:
                locations.append("Caspian Confederation")
            if char_data[4] >= 30:
                locations.append("Lost Peninsula")
            if char_data[4] >= 50:
                locations.append("Far East")
                locations.append("Boarderlands")
            if target_location == "":
                location_string = ""
                for location in locations:
                    location_string += f"{location} \n"
                location_string = f"```possible travel locations \n{location_string}```"
                await ctx.message.channel.send(location_string)
                return
            if target_location not in locations:
                await ctx.message.channel.send(f"{target_location} is not a valid location")
                return
            if db.get_user_item(user.id,game.hash_string("transportation ticket")) is None:
                await message.channel.send(f"you don't have a transportation ticket")
                return
            member = await self.guild.fetch_member(user.id)
            target_role = self.guild.get_role(id["role"][target_location])
            for role in member.roles:
                if role == target_role:
                    await ctx.message.channel.send(f"you're already in {target_location}")
                    return
            db.add_item(user.id,game.hash_string("transportation ticket"),-1)
            for role_obj in member.roles:
                if role_obj.id in id["role"].values():  await member.remove_roles(role_obj)
            await member.add_roles(target_role)

        @self.client.command()
        async def equip(ctx):
            user = ctx.message.author
            message_contents = ctx.message.content[7:]
            weapon_id = game.hash_string(message_contents)
            if db.get_user_item(user.id,weapon_id) is not None:
                if db.get_weapon(weapon_id) is not None:
                    character_data = list(db.get_character(user.id))
                    if db.get_weapon(weapon_id)[1] in character.get_class_weapons(character_data[3]):
                        if character_data[2] != game.hash_string("fist"):
                            db.add_item(user.id,character_data[2],1)
                        character_data[2] = weapon_id
                        db.add_item(user.id,weapon_id,-1)
                        db.update_character(character_data)
                        await ctx.message.channel.send(f"{message_contents} has been equiped")
                        return
                    await ctx.message.channel.send(f"{character_data[3]} cannot equip {db.get_weapon(weapon_id)[1]}")
                    return
                await ctx.message.channel.send(f"{message_contents} is not a valid weapon")
                return
            await ctx.message.channel.send(f"you don't have a {message_contents}")

        @self.client.command()
        async def daily(ctx):
            user = ctx.message.author
            user_data = list(db.get_user(user.id))
            dif = datetime.datetime.now()-user_data[1]
            if dif.days >= 1:
                user_data[1] = datetime.datetime.now()
                db.update_user(user_data)
                game.update_money(user.id,50)
                await ctx.message.channel.send(f"{user.mention} has claimed his daily 50{self.get_discord_emoji(822330641559191573)}")
                return
            await ctx.message.channel.send(f"{str(datetime.timedelta(seconds=86400-int(dif.total_seconds())))} left")

        @self.client.command()
        async def weekly(ctx):
            user = ctx.message.author
            user_data = list(db.get_user(user.id))
            dif = datetime.datetime.now()-user_data[2]
            if dif.days >= 7:
                user_data[2] = datetime.datetime.now()
                db.update_user(user_data)
                game.update_money(user.id,100)
                await ctx.message.channel.send(f"{user.mention} has claimed his weekly 100{self.get_discord_emoji(822330641559191573)}")
                return
            await ctx.message.channel.send(f"{str(datetime.timedelta(seconds=604800-int(dif.total_seconds())))} left")

        @self.client.command()
        async def change(ctx):
            user = ctx.message.author
            target_class = ctx.message.content[8:]
            if db.get_class(target_class) is None:
                await ctx.message.channel.send(f"{target_class} is not a valid class")
                return
            character_data = list(db.get_character(user.id))
            if character.change_class(character_data,target_class):
                character_data[3] = target_class
                db.update_character(character_data)
                db.add_item(user.id,game.hash_string("test seal"),-1)
                await ctx.message.channel.send(f"{character_data[1]}'s class has been changed to {target_class}")
            else:
                await ctx.message.channel.send(f"{character_data[1]} doesn't meet the requirement for {target_class}")

        @self.client.command()
        async def level(ctx):
            user = ctx.message.author
            user_data = list(db.get_character(user.id))
            user_data[5] = 1000
            user_data = character.character_check(user_data)
            db.update_character(user_data)
            await ctx.message.channel.send(f"{user.mention} leveled up!")

        @self.client.command()
        async def money(ctx):
            user = ctx.message.author
            game.update_money(user.id,1000)


if __name__ == "__main__":
    db = database.Database()
    db.setup()
    db.clear_game_data()
    db.setup()
    db.load_game_data()
    TBG_logger = logging.getLogger('user')
    handler = logging.FileHandler('logs/TBG.log')
    handler.setLevel(logging.INFO)
    TBG_logger.addHandler(handler)
    TBGBot = TBG(token)
    TBGBot.run()
