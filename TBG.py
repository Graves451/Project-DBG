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

token = "NjEzMTc4MDQwMDMzNDc2NjE5.XVtIjQ.CpuCgjgWJNHsT1WwmUoNRNy8I2o"

id = {
    "guild":811159707757707304,
    "channel":{
        "great-plains":877292758979727390,
        "greater-plains":878788939966730270,
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
.info <target_name>    gives you valuable information
.reset (needs lvl.60)  resets your character to level 1 and 200 gold, with small permanent stat increases

.battle  spawns an enemy for you to fight
.raid    costs 100 dollars and spawns a boss
```'''

stats_target = ["HP","Max HP","STR","MAG","SPD","DEF","LOG"]

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
            db.add_user(user.id)
            db.add_character(character.generate_character(user.id,user.display_name,"swordsmen",game.hash_string("stone sword"),0))
            db.add_bank(user.id,100)

    async def setup_all_players(self):
        async for member in self.guild.fetch_members(limit=150):
            if not member.bot:
                await self.setup_player(member)

    def create_enemy_embed(self,char_data):
        coloring = discord.Colour.red()
        if char_data[6] == 0: coloring = discord.Colour.dark_grey()
        StatEmbed = discord.Embed(colour=coloring,description=f"`LVL` {str(char_data[4])}\n`CLS` {char_data[3]}")
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
        StatEmbed = discord.Embed(colour=discord.Colour.dark_green(),description=f"`LVL` {str(char_data[4])} ({int((char_data[5]/character.next_level(char_data[4]))*100)}%) \n `CLS` {char_data[3]}")
        StatEmbed.set_author(name=char_data[1].upper())
        StatEmbed.set_thumbnail(url=db.get_graphic(char_data[3])[1])
        StatEmbed.add_field(name=f"{str(char_data[6])}/{str(char_data[7])} ❤️",value=f"`STR` {char_data[8]}\n`MAG` {char_data[9]}\n`SPD` {char_data[10]}\n`DEF` {char_data[11]}\n`LOG` {char_data[12]}")
        item_data, itemname = db.get_weapon(char_data[2]), db.get_item(char_data[2])[1]
        StatEmbed.add_field(name=f"{self.get_discord_emoji(db.get_graphic(itemname)[1])} {itemname}",value=f"`PWR` {item_data[2]}\n`CRT` {item_data[3]}")
        return StatEmbed

    def create_inventory_embed(self,inventory_data):
        weapons, usables = "",""
        for item_name in inventory_data:
            if db.get_usable(game.hash_string(item_name)) is not None: usables += f"{self.get_discord_emoji(db.get_graphic(item_name)[1])} {item_name} X {inventory_data[item_name]}\n"
            if db.get_weapon(game.hash_string(item_name)) is not None: weapons += f"{self.get_discord_emoji(db.get_graphic(item_name)[1])} {item_name} X {inventory_data[item_name]}\n"
        InventoryEmbed = discord.Embed(colour=discord.Colour.green())
        InventoryEmbed.set_author(name="INVENTORY")
        if weapons != "": InventoryEmbed.add_field(name="`Weapons`",value=weapons)
        if usables != "": InventoryEmbed.add_field(name="`Usables`",value=usables)
        return InventoryEmbed

    def create_info_embed(self,name):
        item_data = db.get_item(game.hash_string(name))
        usable_data = db.get_usable(game.hash_string(name))
        weapon_data = db.get_weapon(game.hash_string(name))
        class_data = db.get_class(name)
        if usable_data is not None:
            InfoEmbed = discord.Embed(colour=discord.Colour.light_grey(),description=db.get_item(game.hash_string(name))[4])
            InfoEmbed.set_author(name=name)
            InfoEmbed.set_thumbnail(url=self.get_discord_emoji(db.get_graphic(name)[1]).url)
            InfoEmbed.add_field(name="`TARGET`",value=stats_target[usable_data[1]-6])
            InfoEmbed.add_field(name="`AMT`",value=usable_data[2])
            InfoEmbed.add_field(name="`COST`",value=item_data[2])
            return InfoEmbed
        elif weapon_data is not None:
            InfoEmbed = discord.Embed(colour=discord.Colour.light_grey(),description=db.get_item(game.hash_string(name))[4])
            InfoEmbed.set_author(name=name)
            InfoEmbed.set_thumbnail(url=self.get_discord_emoji(db.get_graphic(name)[1]).url)
            InfoEmbed.add_field(name="`TYPE`",value=weapon_data[1])
            InfoEmbed.add_field(name="`PWR`",value=weapon_data[2])
            InfoEmbed.add_field(name="`CRT`",value=weapon_data[3])
            InfoEmbed.add_field(name="`COST`",value=item_data[2])
            return InfoEmbed
        elif class_data is not None:
            InfoEmbed = discord.Embed(colour=discord.Colour.light_grey(),description=class_data[2])
            InfoEmbed.set_author(name=name)
            InfoEmbed.set_thumbnail(url=db.get_graphic(name)[1])
            InfoEmbed.add_field(name="`GROWTH RATE`",value=class_data[1])
            if class_data[3] == "": InfoEmbed.add_field(name="`ATTRIBUTE`",value="None")
            else: InfoEmbed.add_field(name="`ATTRIBUTE`",value=class_data[3])
            InfoEmbed.add_field(name="`WEAPON CHOICE`",value=class_data[4])
            return InfoEmbed
        else:
            return None

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
                if db.get_enemy(msg.id) is not None and reaction.emoji == "⚔️":
                    fight = game.battle(list(db.get_character(user.id)),list(db.get_enemy(msg.id)),reaction.message)
                    await fight.run()
                    player_character, enemy_character = fight.get_characters()
                    if player_character[6] == 0:
                        db.update_bank(user.id,int(db.get_bank(user.id)[1]*0.9))
                    db.update_character(player_character)
                    if enemy_character[6] == 0:
                        db.delete_enemy(msg.id)
                        if enemy_character[1] == "boss":
                            user_data = list(db.get_user(user.id))
                            user_data[4]+=f"{reaction.message.channel.name}."
                            db.update_user(user_data)
                        await msg.edit(embed=self.create_enemy_embed(enemy_character))
                        return
                    db.update_enemy(enemy_character)
                    await msg.edit(embed=self.create_enemy_embed(enemy_character))

        @self.client.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandOnCooldown):
                await ctx.send(f'{ctx.author.mention} {ctx.message.content} is on a {str(datetime.timedelta(seconds=int(error.retry_after)))}s cooldown')
                return
            raise error

        @self.client.command()
        async def ping(ctx):
            await ctx.message.channel.send(f"pong! {round(self.client.latency*1000)}ms")

        @self.client.command()
        async def help(ctx):
            await ctx.message.channel.send(help_string)

        @self.client.command()
        async def info(ctx):
            target_thing = ctx.message.content[6:]
            if target_thing == "":
                embed = self.create_info_embed(db.get_character(ctx.message.author.id)[3])
            else:
                embed = self.create_info_embed(target_thing)
            if embed is None:
                await ctx.message.channel.send(f"{target_thing} does not exist")
                return
            else:
                await ctx.message.channel.send(embed=embed)

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
            await ctx.message.channel.send(embed=self.create_inventory_embed(db.get_inventory(ctx.message.author.id)[0]))

        @self.client.command()
        async def bank(ctx):
            await ctx.message.channel.send(f"You have {db.get_bank(ctx.message.author.id)[1]}{self.get_discord_emoji(822330641559191573)}")

        @commands.cooldown(2,5)
        @self.client.command()
        async def battle(ctx):
            if ctx.message.channel.id not in id["channel"].values():
                await ctx.message.channel.send("This is not a place for battle")
                return
            else:
                level = 5
                if ctx.message.channel.id == id["channel"]["great-plains"] or ctx.message.channel.id == id["channel"]["greater-plains"]:
                    level = random.randint(5,20)
                elif ctx.message.channel.id == id["channel"]["forest"]:
                    level = random.randint(20,40)
                elif ctx.message.channel.id == id["channel"]["mountain"]:
                    level = random.randint(40,70)
                enemy_data = character.generate_enemy("enemy",level)
                print(enemy_data)
                enemy_embed = self.create_enemy_embed(enemy_data)
                msg = await ctx.message.channel.send(embed=enemy_embed)
                enemy_data[0] = msg.id
                db.add_enemy(enemy_data)
                await msg.add_reaction("⚔️")

        @self.client.command()
        async def prestige(ctx):
            user = ctx.message.author
            char_data = list(db.get_character(user.id))
            user_data = list(db.get_user(user.id))
            if char_data[4] < 60:
                await ctx.message.channel.send("you're not level 60 yet")
                return
            num = int((char_data[4]-60)/20)+1
            user_data[5] += num
            char_data = character.generate_character(user.id,user.display_name,"swordsmen",game.hash_string("stone sword"),user_data[5])
            db.update_user(user_data)
            db.update_character(char_data)
            db.update_bank(user.id,-db.get_bank(user.id)[1])
            db.update_bank(user.id,200)
            await ctx.message.channel.send(f"{user.mention} have been reset to level 1, and gained some bonus permanent {num} to all stats, and you get 200 gold coins to start off")
            return

        @commands.cooldown(1,3600)
        @self.client.command()
        async def raid(ctx):
            level = 5
            if ctx.message.channel.id == id["channel"]["great-plains"]:
                character_class = "Warlord"
                level = 20
            elif ctx.message.channel.id == id["channel"]["forest"]:
                character_class = "Sharpshooter"
                level = 40
            elif ctx.message.channel.id == id["channel"]["mountain"]:
                character_class = "General"
                level = 60
            user = ctx.message.author
            if db.get_character(user.id)[4] < level:
                await ctx.message.channel.send(f"you need to be at least level {level} to challenge this boss")
                return
            if not game.update_money(user.id,-100):
                await ctx.message.channel.send("you need at least 100 coins to challenge the boss")
                return
            boss_data = character.generate_boss("boss",level,character_class,game.hash_string(character.generate_class_weapon(character_class,level)))
            boss_embed = self.create_enemy_embed(boss_data)
            msg = await ctx.message.channel.send("a boss fight ig")
            thread = await msg.create_thread(name="thread for ur boss fight")
            boss_msg = await thread.send(embed=boss_embed)
            await boss_msg.add_reaction("⚔️")
            boss_data[0] = boss_msg.id
            db.add_enemy(boss_data)
            TBG_logger.info(f"spawning a {character_class}")

        @self.client.command()
        async def use(ctx):
            user = ctx.message.author
            target_item = ctx.message.content[5:]
            for abbreviation in database.abbreviations:
                target_item = target_item.replace(abbreviation[0],abbreviation[1])
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
            char_data = await character.character_check(char_data,ctx.message)
            db.update_character(char_data)
            await ctx.message.channel.send(f"you gained {item_data[2]} {stats_target[item_data[1]-6]}")

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
            target_class = ctx.message.content[8:].title()
            if db.get_class(target_class) is None:
                await ctx.message.channel.send(f"{target_class} is not a valid class")
                return
            character_data = list(db.get_character(user.id))
            if target_class in character.beginner_classes and character_data[4] < 10:
                await ctx.message.channel.send(f"you need to be at least level 10 to changed to {target_class}")
            elif target_class in character.intermediate_classes and character_data[4] < 20:
                await ctx.message.channel.send(f"you need to be at least level 20 to changed to {target_class}")
            elif target_class in character.advanced_classes and character_data[4] < 40:
                await ctx.message.channel.send(f"you need to be at least level 40 to changed to {target_class}")
            elif character.change_class(character_data,target_class):
                character_data[3] = target_class
                db.update_character(character_data)
                db.add_item(user.id,game.hash_string("test seal"),-1)
                await ctx.message.channel.send(f"{character_data[1]}'s class has been changed to {target_class}")
            else:
                requirements = character.class_requirement(target_class)
                requirement_str = ""
                for num in range(len(requirements)):
                    requirement_str += f"{requirements[num][1]} for {stats_target[requirements[num][0]+2]}"
                    if num != 0:
                        requirement_str += " or "
                await ctx.message.channel.send(f"{character_data[1]} doesn't meet the requirement for {target_class}, class requirements: {requirement_str}")

        @self.client.command()
        async def level(ctx):
            user = ctx.message.author
            char_data = list(db.get_character(user.id))
            char_data[4] += 20
            db.update_character(char_data)

        @self.client.command()
        async def money(ctx):
            user = ctx.message.author
            game.update_money(user.id,1000)


if __name__ == "__main__":
    db = database.Database()
    db.setup()
    db.clear_game_data()
    db.load_game_data()
    TBG_logger = logging.getLogger('user')
    handler = logging.FileHandler('logs/TBG.log')
    handler.setLevel(logging.INFO)
    TBG_logger.addHandler(handler)
    TBGBot = TBG(token)
    TBGBot.run()
