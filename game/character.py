import random
import database
import hashlib
import discord

db = database.Database()

#give the bosses proper weapons

#implement some kind system of ranged weapons for bows and mages

'''
Damage, the amount taken away from the enemy’s health with each attack.
Damage(physical): (attacker_str - enemy_def)*weapon_power
Damage(magical): (attacker_mag - enemy_log)*weapon_power

'''

#user: user_id,daily,weekly,first
#              0      1        2       3       4    5      6         7          8        9     10      11      12
#character: user_id, name, weapon_id, class, level, exp, health, max_health, strength, magic, speed, defense, logic
#enemies: message_id, name, weapon_id, class, level, exp, health, max_health, strength, magic, speed, defense, logic
#classes: class_name, growth_rate, desc, attribute, weapon_choice
#items item_id, name, cost, type, desc
#weapons item_id, type, power, crit, damage_type
#usable: itemname, target, amount
#graphics: graphic_name, value
def generate_enemy(name,level,class_name,weapon_id):
    #used the 0 at the start as placement for the message id
    enemy_data = [0, name, weapon_id, class_name, level, 0, 0, 0, 0, 0, 0, 0, 0]
    growth_rates = db.get_class(class_name)[1].split("-")
    for x in range(level):
        for num in range(len(growth_rates)):
            if rng(float(growth_rates[num])):
                enemy_data[7+num]+=1
    enemy_data[6] = enemy_data[7]
    return enemy_data

def generate_character(user_id, name, user_class, weapon_id):
    return (user_id, name, weapon_id, user_class, 1, 0, 15, 15, 6, 5, 7, 5, 3)

def create_character_embed(char_data):
    StatEmbed = discord.Embed(colour=discord.Colour.red(),description=f"`LVL` {str(char_data[4])}\n`EXP` {str(int(char_data[5]*100/next_level(char_data[5])))}%")
    StatEmbed.set_author(name=char_data[3].upper())
    stat_name = f"{str(char_data[6])}/{str(char_data[7])} ❤️"
    stat_stats = f"`STR` {char_data[8]}\n`MAG` {char_data[9]}\n`SPD` {char_data[10]}\n`DEF` {char_data[11]}\n`LOG` {char_data[12]}"
    StatEmbed.add_field(name=stat_name,value=stat_stats)
    item_data = db.get_weapon(char_data[2])
    StatEmbed.add_field(name=db.get_item(char_data[2])[1],value=f"`PWR` {item_data[2]}\n`CRT` {item_data[3]}")
    return StatEmbed

def level_check(user_data):
    next_level_requirement = next_level(user_data[4])
    while user_data[5] >= next_level_requirement:
        user_data[5] -= next_level_requirement
        user_data[4] += 1
        growth_rates = db.get_class(user_data[3])[1].split("-")
        for num in range(len(growth_rates)):
            if rng(float(growth_rates[num])):
                user_data[7+num]+=1
        next_level_requirement = next_level(user_data[4])
        print(f"{str(user_data[0])} leveled up")
    return user_data

def change_class(character_data,target_class):
    class_growth = db.get_class(target_class)[1].split("-")[1:]
    stat_requirement = max(class_growth)
    stat_requirements = []
    print(f"max stat is {stat_requirement}")
    for x in range(len(class_growth)):
        if class_growth[x] == stat_requirement:
            stat_requirements.append(x)
    print(stat_requirements)
    print(class_growth)
    for num in range(len(stat_requirements)):
        print(class_growth[stat_requirements[num]])
        print(f"requirement for {num} is {0.4*int(class_growth[stat_requirements[num]])}")
        print(f"charater's stat {character_data[8+stat_requirements[num]]}")
        if character_data[8+stat_requirements[num]] >= 0.4*int(class_growth[stat_requirements[num]]):
            character_data[3] = target_class
            unequip_weapon(character_data)
            return True
    return False

def get_class_attribute(class_name):
    return db.get_character(class_name)[3].split("-")

def unequip_weapon(character_data):
    if character_data[2] != hash_string("fist"):
        db.add_item(character_data[0],character_data[2],1)
    character_data[2] = hash_string("fist")
    return character_data


#would be nice to have something more complex here
def next_level(current_level):
    return 100

def get_class_weapons(class_name):
    return db.get_class(class_name)[4].split("-")

def rng(odds):
    if random.random()*100 < odds:
        return True
    return False

def hash_string(string_input):
    return int(hashlib.sha256(string_input.encode('utf-8')).hexdigest(), 16) % 10**8
