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

class battle:
    def __init__(self,character1,character2,msg,player):
        self.character1 = character1
        self.character2 = character2
        self.constestants = [character1, character2]
        self.attributes = {character1[0]:[],character2[0]:[]}
        self.msg = msg
        self.player = player
        self.combat_log = ""
        random.shuffle(self.constestants)
        for character in self.constestants:
            self.attributes[character[0]].append(db.get_item(character[2])[3])
            self.attributes[character[0]].extend(db.get_class(character[3])[3].split("-"))

    async def run(self):
        self.combat()
        await self.post_combat()
        await self.combat_result_embed()

    def combat(self):
        for x in range(2):
            attacker = self.constestants[0]
            defender = self.constestants[1]
            if defender[6] == 0 or attacker[6] == 0:
                return
            attacker_weapon = list(db.get_weapon(attacker[2]))
            counter_data = db.get_counter(attacker[2])
            if counter_data is not None:
                if set(counter_data[1].split("-")) & set(self.attributes[defender[0]]):
                    attacker_weapon[2]+=int(counter_data[2])
                    attacker_weapon[3]+=int(counter_data[3])
            if not self.dodge(attacker,defender):
                damage = max(self.get_damage(attacker,defender,attacker_weapon),0)
                if self.crit(attacker,defender,attacker_weapon):
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

    def get_damage(self,attacker,defender,attacker_weapon):
        if attacker_weapon[4] == "physical":
            return attacker[8]+attacker_weapon[2]-int(defender[11]*0.8)
        return attacker[9]+attacker_weapon[2]-int(defender[12]*0.8)

    def dodge(self,attacker,defender):
        if rng(min(float((defender[10]-attacker[10])*5),90)):
            return True
        return False

#              0      1        2       3       4    5      6         7          8        9     10      11      12
#character: user_id, name, weapon_id, class, level, exp, health, max_health, strength, magic, speed, defense, logic
    def crit(self,attacker,defender,attacker_weapon):
        if attacker_weapon[4] == "physical":
            return rng(attacker[8]+attacker_weapon[3]-defender[11])
        return rng(attacker[9]+attacker_weapon[3]-defender[12])

    def get_characters(self):
        return self.character1, self.character2

    async def post_combat(self):
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
        self.character1 = await character.character_check(self.character1,self.player,self.msg)
        self.character2 = await character.character_check(self.character2,self.player,self.msg)

    async def combat_result_embed(self):
        if self.combat_log == "":
            self.combat_log = "no combat, you're at 0 health"
        combat_embed = discord.Embed(colour = discord.Color.red(),description=self.combat_log)
        if self.character2[6] == 0 and len(self.character2) == 15: combat_embed.set_footer(text=self.character2[13])
        await self.msg.channel.send(embed=combat_embed)

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
