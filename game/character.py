import random
import database

db = database.Database()

#give the bosses proper weapons

#implement some kind system of ranged weapons for bows and mages

bosses = [("Tyrannt","king",60038410),("Duelies","dueler",60038410),("Masked Assassin","assassin",60038410)]
#has not finished yet
def generate_boss(lvl):
    stats = [10,1,1,1,1,1]
    boss_type = random.choice(bosses)
    growth_rates = db.get_class(boss_type[1])[1].split("-")
    for x in range(lvl):
        for num in range(len(growth_rates)):
            if rng(float(growth_rates[num])):
                stats[num]+=1
    #bosses: message_id, name, weapon_id, class, level, health, max_health, strength, magic, speed, defense, logic
    return (boss_type[0],boss_type[2],boss_type[1],lvl,0,stats[0],stats[0],stats[1],stats[2],stats[3],stats[4],stats[5])

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

#would be nice to have something more complex here
def next_level(current_level):
    return 100

#              0      1       2         3     4      5    6        7          8          9      10     11      12
#character: user_id, name, weapon_id, class, level, exp, health, max_health, strength, magic, speed, defense, logic
#bosses: message_id, name, weapon_id, class, level, exp, health, max_health, strength, magic, speed, defense, logic
def combat(char1_data,char2_data):
    damage1_string = "evaded"
    if not evasion(char1_data,char2_data):
        damage1, damage1_string = get_damage(char1_data,char2_data)
        print(f"damage is {str(damage1)}")
        char2_data[6] = max(char2_data[6]-damage1,0)
    if char2_data[6] == 0 or char1_data[6] == 0:
        return char1_data, char2_data, damage1_string, "None"
    damage2_string = "evaded"
    if not evasion(char2_data,char1_data):
        damage2, damage2_string = get_damage(char2_data,char1_data)
        print(f"counter damage is {str(damage2)}")
        char1_data[6] = max(char1_data[6]-damage2,0)
    return char1_data, char2_data, damage1_string, damage2_string

def get_damage(attacker_data,defender_data):
    #means attack is physical
    damage_string = ""
    attacker_weapon = db.get_weapon(attacker_data[2])
    if attacker_weapon[4] == "physical":
        damage = (attacker_data[8])+attacker_weapon[2]-defender_data[11]
        damage_string = str(damage)
        if rng(attacker_data[8]-defender_data[8]):
            damage = damage * 2
            damage_string = f"{str(damage)} **crit**"
        return max(damage,0), damage_string
    damage = (attacker_data[9])+attacker_weapon[2]-defender_data[12]
    damage_string = str(damage)
    if rng(attacker_data[9]-defender_data[9]):
        damage = damage * 2
        damage_string = f"{str(damage*2)} **crit**"
    return max(damage,0), damage_string

def evasion(attacker_data,defender_data):
    print(f"evasion rate is {str((attacker_data[10]-defender_data[10])*5)}")
    if rng((attacker_data[10]-defender_data[10])*5):
        print("evaded")
        return True
    return False

def rng(odds):
    if random.random()*100 < odds:
        return True
    return False
