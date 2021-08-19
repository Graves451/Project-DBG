import database
import character

import random
import discord
import hashlib
import logging
import threading
import asyncio

db = database.Database()

Game_logger = logging.getLogger('user')
handler = logging.FileHandler('logs/game.log')
handler.setLevel(logging.INFO)
Game_logger.addHandler(handler)

#              0      1        2       3       4    5      6         7          8        9     10      11      12
#character: user_id, name, weapon_id, class, level, exp, health, max_health, strength, magic, speed, defense, logic
#enemies: message_id, name, weapon_id, class, level, exp, health, max_health, strength, magic, speed, defense, logic

class battle:
    def __init__(self,character1,character2):
        self.character1 = character1
        self.character2 = character2
        self.constestants = [character1, character2]
        self.combat_log = ""
        random.shuffle(self.constestants)
        self.combat()
        self.post_combat()

    def combat(self):
        for x in range(2):
            attacker = self.constestants[0]
            defender = self.constestants[1]
            if defender[6] == 0 or attacker[6] == 0:
                return
            if not self.dodge(attacker,defender):
                damage = max(self.get_damage(attacker,defender),0)
                if self.crit(attacker,defender):
                    damage*=2
                    self.combat_log += f"{attacker[1]} dealed {damage}💢 \n"
                else:
                    self.combat_log += f"{attacker[1]} dealed {damage} \n"
                defender[6] = max(0,defender[6]-damage)
                if len(defender) == 15:
                    defender[14] += f"{attacker[1]} - {damage}\n"
            else:
                self.combat_log += f"{attacker[1]} - Missed ❔ \n"
                if len(defender) == 15:
                    defender[14] += f"{attacker[1]} - {0}\n"
            #check if the defender's still alive
            if defender[6] == 0:
                self.combat_log += f"{defender[1]} has been killed 💀 \n"
            self.constestants.reverse()

    def get_damage(self,attacker,defender):
        attacker_weapon = db.get_weapon(attacker[2])
        if attacker_weapon[4] == "physical":
            return attacker[8]+attacker_weapon[2]-defender[11]
        return attacker[9]+attacker_weapon[2]-defender[12]

    def dodge(self,attacker,defender):
        if rng(float((defender[10]-attacker[10])*5)):
            return True
        return False

    def crit(self,attacker,defender):
        attacker_weapon = db.get_weapon(attacker[2])
        if rng(attacker[8]+attacker_weapon[3]-defender[8]):
            return True
        return False

    def get_characters(self):
        return self.character1, self.character2

    def post_combat(self):
        if db.get_enemy(self.character2[0]) is not None:
            if self.character2[6] <= 0:
                for items in self.character2[13].split("-"):
                    item_data = items.split(".")
                    if item_data[1] == "exp":
                        self.character1[5]+=int(item_data[0])
                    elif item_data[1] == "gold coin":
                        update_money(self.character1[0],int(item_data[0]))
                    else:
                        db.add_item(self.character1[0],hash_string(item_data[1]),int(item_data[0]))
        self.character1 = character.character_check(self.character1)
        self.character2 = character.character_check(self.character2)

    def combat_result_embed(self):
        if self.combat_log == "":
            self.combat_log = "no combat, you're at 0 health"
        combat_embed = discord.Embed(colour = discord.Color.red(),description=self.combat_log)
        combat_embed.set_footer(text=self.character2[13])
        return combat_embed

###########################################################################################################################

#campaign: campaign_name, waves, starting_level, level_increase, time

class campaign:
    def __init__(self,user,location,guild):
        self.user = user
        self.guild = guild
        self.campaign_data = db.get_campaign(location)
        self.location = location
        self.wave = 1
        self.level = self.campaign_data[2]
        self.enemy_ids = []

    async def spawn_wave(self):
        await self.user.send(f"```starting of wave {self.wave}```")
        for num in range(3):
            character_class = character.determine_enemy_class(self.level)
            enemy_data = character.generate_enemy("enemy",self.level,character_class,hash_string(character.generate_class_weapon(character_class,self.level)))
            enemy_embed = await create_enemy_embed(enemy_data,self.guild)
            msg = await self.user.send(embed=enemy_embed)
            enemy_data[0] = msg.id
            db.add_enemy(enemy_data)
            await msg.add_reaction("⚔️")
            self.enemy_ids.append(msg.id)
            print(enemy_data)

    async def remove_enemy(self,msg_id):
        self.enemy_ids.remove(msg_id)
        if self.wave == self.campaign_data[1] and len(self.enemy_ids) == 0:
            await self.post_campaign()
            return
        if len(self.enemy_ids) == 0:
            self.level += self.campaign_data[3]
            self.wave += 1
            await self.spawn_wave()

    async def post_campaign(self):
        await self.user.send(f"congrats, you've cleared the {self.location} campaign")

###########################################################################################################################

class shop:
    def __init__(self):
        self.items = []
        self.generate_items()

    def generate_items(self):
        all_item_names = list(db.get_all_item())
        for item_data in all_item_names:
            if item_data[0] in database.forbidden_items:
                all_item_names.remove(item_data)
        self.items = [value[0] for value in random.sample(all_item_names,6)]
        Game_logger.info("refreshing items")

    def return_items(self):
        return self.items

###########################################################################################################################

async def create_enemy_embed(char_data,guild):
    StatEmbed = discord.Embed(colour=discord.Colour.red(),description=f"`LVL` {str(char_data[4])}\n`CLS` {char_data[3]}")
    StatEmbed.set_author(name=char_data[1].upper())
    StatEmbed.set_thumbnail(url=db.get_graphic(char_data[3])[1])
    StatEmbed.add_field(name=f"{str(char_data[6])}/{str(char_data[7])} ❤️",value=f"`STR` {char_data[8]}\n`MAG` {char_data[9]}\n`SPD` {char_data[10]}\n`DEF` {char_data[11]}\n`LOG` {char_data[12]}")
    item_data, itemname = db.get_weapon(char_data[2]), db.get_item(char_data[2])[1]
    StatEmbed.add_field(name=f"{str(await guild.fetch_emoji(db.get_graphic(itemname)[1]))} {itemname}",value=f"`PWR` {item_data[2]}\n`CRT` {item_data[3]}")
    enemy_loot = ""
    for loot_items in char_data[13].split("-"):
        loot_values = loot_items.split(".")
        enemy_loot += f"{loot_values[0]} - {loot_values[1]} "
    return StatEmbed

def update_money(user_id,amount):
    user_money = list(db.get_bank(user_id))
    if amount < 0:
        if user_money[1] < -amount:
            return False
    db.update_bank(user_id,user_money[1]+amount)
    return True

def rng(odds):
    if random.random()*100 < odds:
        return True
    return False

def hash_string(string_input):
    return int(hashlib.sha256(string_input.encode('utf-8')).hexdigest(), 16) % 10**8
