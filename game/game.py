import database
import random
import discord

db = database.Database()

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

    def combat(self):
        for x in range(2):
            attacker = self.constestants[0]
            defender = self.constestants[1]
            if defender[6] == 0 or attacker[6] == 0:
                return
            print(f"{attacker[1]} is attacking")
            if not self.dodge(attacker,defender):
                damage = self.get_damage(attacker,defender)
                if self.crit(attacker,defender):
                    damage*=2
                    print("crit")
                self.combat_log += f"{attacker[1]} - {damage} \n"
                defender[6] = max(0,defender[6]-damage)
            else:
                self.combat_log += f"{attacker[1]} - Missed \n"
                print("dodged")
            #check if the defender's still alive
            if defender[6] == 0:
                print(f"{defender[1]} has been killed")
            self.constestants.reverse()

    def get_damage(self,attacker,defender):
        attacker_weapon = db.get_weapon(attacker[2])
        if attacker_weapon[4] == "physical":
            return attacker[8]+attacker_weapon[2]-defender[11]
        return attacker[9]+attacker_weapon[2]-defender[12]

    def dodge(self,attacker,defender):
        if rng(float((attacker[10]-defender[10])*5)):
            return True
        return False

    def crit(self,attacker,defender):
        attacker_weapon = db.get_weapon(attacker[2])
        if rng(attacker[8]+attacker_weapon[3]-defender[8]):
            return True
        return False

    def get_characters(self):
        return self.character1, self.character2

    def combat_result_embed(self):
        if self.combat_log == "":
            self.combat_log = "no combat, you're at 0 health"
        combat_embed = discord.Embed(colour = discord.Color.red(),description=self.combat_log)
        return combat_embed

def rng(odds):
    if random.random()*100 < odds:
        return True
    return False

###########################################################################################################################

shop_items = []

def generate_shop():
    all_item_names = list(db.get_all_item())
    return random.sample(all_item_names,6)

def update_shop(new_list):
    shop_items = new_list

def get_shop():
    return shop_items
