import random
import database
import hashlib
import discord
import logging

db = database.Database()

#give the bosses proper weapons

#implement some kind system of ranged weapons for bows and mages

#user: user_id,daily,weekly,first
#              0      1        2       3       4    5      6         7          8        9     10      11      12
#character: user_id, name, weapon_id, class, level, exp, health, max_health, strength, magic, speed, defense, logic
#enemies: message_id, name, weapon_id, class, level, exp, health, max_health, strength, magic, speed, defense, logic
#classes: class_name, growth_rate, desc, attribute, weapon_choice
#items item_id, name, cost, type, desc
#weapons item_id, type, power, crit, damage_type
#usable: itemname, target, amount
#graphics: graphic_name, value

logging.basicConfig(handlers=[logging.FileHandler(filename="logs/TBG.log",
                                                 encoding='utf-8', mode='a+')],
                    format="%(asctime)s %(name)s:%(levelname)s:%(message)s",
                    datefmt="%F %A %T",
                    level=logging.INFO)

beginner_classes = ["Archer","Barbarian","Infantry","Tactician","Swordsmen"]

intermediate_classes = ["Spearmen","Knight","Brigand","Mercenary","Dueler","Strategist","Crossbowmen"]

advanced_classes = ["Assassin","Warrior","Great Knight","Wizard","Swordmaster","Sniper","Rocketeer"]

weapons = {}

def determine_enemy_class(level):
    if level > 40:
        return random.choice(database.advanced_classes)
    if level > 20:
        return random.choice(database.intermediate_classes)
    return random.choice(database.beginner_classes)

def generate_enemy(name,level,class_name,weapon_id):
    #used the 0 at the start as placement for the message id
    enemy_data = [0, name, weapon_id, class_name, level, 0, 0, 0, 0, 0, 0, 0, 0,generate_enemy_loot(level),""]
    growth_rates = db.get_class(class_name)[1].split("-")
    for x in range(level):
        for num in range(len(growth_rates)):
            if rng(float(growth_rates[num])):
                enemy_data[7+num]+=1
    enemy_data[6] = enemy_data[7]
    return enemy_data

def generate_boss(name,level,class_name,weapon_id):
    #used the 0 at the start as placement for the message id
    boss_data = [0, name, weapon_id, class_name, level, 0, 0, 30, 10, 10, 10, 10, 10,generate_enemy_loot(level),""]
    growth_rates = db.get_class(class_name)[1].split("-")
    for x in range(level):
        for num in range(len(growth_rates)):
            if rng(float(growth_rates[num])):
                boss_data[7+num]+=1
    boss_data[6] = boss_data[7]
    return boss_data

def generate_class_weapon(class_name,level):
    weapon_choice = random.choice(db.get_class(class_name)[4].split("-"))
    return database.weapons[weapon_choice][int(min(level/80,0.99)*len(database.weapons[weapon_choice]))]

def generate_enemy_loot(level):
    return f"{str(int((random.randint(5,10)/10)*level))}.gold coin-{str(int((random.randint(7,10)/10)*level))}.exp"

def generate_character(user_id, name, user_class, weapon_id):
    return (user_id, name, weapon_id, user_class, 1, 0, 15, 15, 6, 5, 7, 5, 3)

def change_class(character_data,target_class):
    class_growth = db.get_class(target_class)[1].split("-")[1:]
    stat_requirement = max(class_growth)
    stat_requirements = []
    for x in range(len(class_growth)):
        if class_growth[x] == stat_requirement:
            stat_requirements.append(x)
    for num in range(len(stat_requirements)):
        if character_data[8+stat_requirements[num]] >= 0.3*int(class_growth[stat_requirements[num]]):
            character_data[3] = target_class
            unequip_weapon(character_data)
            return True
    return False

def character_check(user_data):
    next_level_requirement = next_level(user_data[4])
    while user_data[5] >= next_level_requirement:
        user_data[5] -= next_level_requirement
        user_data[4] += 1
        growth_rates = db.get_class(user_data[3])[1].split("-")
        for num in range(len(growth_rates)):
            if rng(float(growth_rates[num])):
                user_data[7+num]+=1
        next_level_requirement = next_level(user_data[4])
        logging.info(f"{str(user_data[0])} leveled up")
    user_data[6] = min(user_data[6],user_data[7])
    user_data[6] = max(user_data[6],0)
    return user_data

def get_class_attribute(class_name):
    return db.get_character(class_name)[3].split("-")

def unequip_weapon(character_data):
    if character_data[2] != hash_string("fist"):
        db.add_item(character_data[0],character_data[2],1)
    character_data[2] = hash_string("fist")
    return character_data

#would be nice to have something more complex here
def next_level(current_level):
    if current_level < 60:
        return int(current_level*10.25)+100
    return int(1.12**current_level)

def get_class_weapons(class_name):
    return db.get_class(class_name)[4].split("-")

def rng(odds):
    if random.random()*100 < odds:
        return True
    return False

def hash_string(string_input):
    return int(hashlib.sha256(string_input.encode('utf-8')).hexdigest(), 16) % 10**8
