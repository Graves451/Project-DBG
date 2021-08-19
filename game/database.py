import mysql.connector as mysql
import hashlib
import datetime
import logging

DB_logger = logging.getLogger('user')
handler = logging.FileHandler('logs/database.log')
handler.setLevel(logging.INFO)
DB_logger.addHandler(handler)

#user: user_id,daily,weekly,first
#              0      1        2       3       4    5      6         7          8        9     10      11      12
#character: user_id, name, weapon_id, class, level, exp, health, max_health, strength, magic, speed, defense, logic
#enemies: message_id, name, weapon_id, class, level, exp, health, max_health, strength, magic, speed, defense, logic, loot, combat_log
#classes: class_name, growth_rate, desc, attribute, weapon_choice
#items item_id, name, cost, type, desc
#weapons item_id, type, power, crit, damage_type
#usable: itemname, target, amount
#graphics: graphic_name, value
#campaign: campaign_name, waves, starting_level, level_increase, time

beginner_classes = ["Archer","Barbarian","Infantry","Tactician","Swordsmen"]

intermediate_classes = ["Spearmen","Knight","Brigand","Mercenary","Dueler","Strategist","Longbowmen"]

advanced_classes = ["Assassin","Warrior","Great Knight","Wizard","Swordmaster","Sniper","Rocketeer"]

boss_classes = ["Warlord","Fortress","Sharpshooter"]

weapons = {
    "sword":[],
    "spear":[],
    "axe":[],
    "bow":[],
    "tome":[]
}

forbidden_items = ["fist","gold coin"]

def hash_string(string_input):
    #used to return a relatively unique id with a length of 8 of the string
    return int(hashlib.sha256(string_input.encode('utf-8')).hexdigest(), 16) % 10**8

#the read and write has been updated to this so that the connections requests doesn't crash the mysql server
def read_execute(query,values):
    con = mysql.connect(host="localhost",user="pi",passwd="WUHANpja123",database = "TBG")
    cur = con.cursor()
    cur.execute(query,values)
    answer = cur.fetchone()
    cur.close()
    con.close()
    return answer

def read_all_execute(query,values):
    con = mysql.connect(host="localhost",user="pi",passwd="WUHANpja123",database = "TBG")
    cur = con.cursor()
    cur.execute(query,values)
    answer = cur.fetchall()
    cur.close()
    con.close()
    return answer

def write_execute(query,values):
    con = mysql.connect(host="localhost",user="pi",passwd="WUHANpja123",database = "TBG")
    cur = con.cursor()
    cur.execute(query,values)
    cur.close()
    con.commit()
    con.close()

def execute(query):
    con = mysql.connect(host="localhost",user="pi",passwd="WUHANpja123",database = "TBG")
    cur = con.cursor()
    cur.execute(query)
    cur.close()
    con.commit()
    con.close()

class Database:
    def setup(self):
        execute("CREATE TABLE IF NOT EXISTS users (user_id BIGINT(11) NOT NULL PRIMARY KEY, daily DATETIME, weekly DATETIME, first DATE)")
        execute("CREATE TABLE IF NOT EXISTS characters (user_id BIGINT(11) NOT NULL PRIMARY KEY, name VARCHAR(255), weapon_id INT(11), class VARCHAR(255), level INT(11), exp INT(11), health INT(11), max_health INT(11), strength INT(11), magic INT(11), speed INT(11), defense INT(11), logic INT(11))")
        execute("CREATE TABLE IF NOT EXISTS inventories (user_id BIGINT(11) NOT NULL, item_id INT(11), amount INT(11))")
        execute("CREATE TABLE IF NOT EXISTS bank (user_id BIGINT(11) NOT NULL, money BIGINT(11))")
        execute("CREATE TABLE IF NOT EXISTS enemies (message_id BIGINT(11) NOT NULL PRIMARY KEY, name VARCHAR(255), weapon_id INT(11), class VARCHAR(255), level INT(11), exp INT(11), health INT(11), max_health INT(11), strength INT(11), magic INT(11), speed INT(11), defense INT(11), logic INT(11), loot VARCHAR(255), combat_log VARCHAR(255))")
        execute("CREATE TABLE IF NOT EXISTS campaigns (campaign_name VARCHAR(255) NOT NULL PRIMARY KEY, waves INT(11), starting_level INT(11), level_increase INT(11), time INT(11))")
        execute("CREATE TABLE IF NOT EXISTS classes (class_name VARCHAR(255) NOT NULL PRIMARY KEY, growth_rate VARCHAR(255), description VARCHAR(255), attributes VARCHAR(255), weapon_choices VARCHAR(255))")
        execute("CREATE TABLE IF NOT EXISTS items (item_id INT(11) NOT NULL PRIMARY KEY, name VARCHAR(255), cost INT(11), type VARCHAR(255), description VARCHAR(255))")
        execute("CREATE TABLE IF NOT EXISTS weapons (item_id INT(11) NOT NULL PRIMARY KEY, type VARCHAR(255), power INT(11), crit INT(11), damage_type VARCHAR(255))")
        execute("CREATE TABLE IF NOT EXISTS usables (item_id INT(11) NOT NULL PRIMARY KEY, target INT(11), amount INT(11))")
        execute("CREATE TABLE IF NOT EXISTS graphics (graphic_name VARCHAR(255) NOT NULL PRIMARY KEY, value VARCHAR(255))")

    def load_game_data(self):
        #clears the tables everytime
        #loads all the game's data from the text files into the db
        file_data = open("game_data/item_data.txt","r")
        for line_input in file_data.readlines():
            line = line_input.split(",")
            #item: itemname, cost, item_type, item_description
            self.insert_item(line[0],int(line[1]),line[2],line[3])
            if line[2] == "weapon":
                #weapon: itemname, cost, item_type, item_description, graphic, weapon_type, power, crit, physical
                self.insert_weapon(line[0],line[4],line[5],line[6],line[7].replace("\n",""))
                if line[4] in weapons: weapons[line[4]].append(line[0])
            if line[2] == "usable":
                self.insert_usable(line[0],line[4],line[5].replace("\n",""))

        #classes: class_name, growth_rate, desc, attribute, weapon_choice
        file_data = open("game_data/class_data.txt","r")
        for line_input in file_data.read().splitlines():
            line = line_input.split(",")
            self.insert_class(line[0],line[1],line[2],line[3],line[4].replace("\n",""))

        file_data = open("game_data/campaign_data.txt","r")
        for line_input in file_data.read().splitlines():
            line = line_input.split(",")
            self.insert_campaign(line[0],line[1],line[2],line[3],line[4].replace("\n",""))

        file_data = open("game_data/graphic.txt","r")
        for line_input in file_data.read().splitlines():
            line = line_input.split(",")
            self.insert_graphic(line[0],line[1].replace("\n",""))

    def clear_game_data(self):
        execute("DROP TABLE items")
        execute("DROP TABLE classes")
        execute("DROP TABLE weapons")
        execute("DROP TABLE usables")
        execute("DROP TABLE enemies")

#####################################################################################################################################################

    def add_user(self,user_id):
        now = datetime.datetime.now()
        query = "INSERT IGNORE INTO users (user_id, daily, weekly, first) VALUES (%s, %s, %s, %s)"
        values = (user_id, now-datetime.timedelta(days=1), now-datetime.timedelta(days=7), now.date())
        write_execute(query,values)
        DB_logger.info(str(user_id)+" has been added")

    def add_character(self,values):
        query = "INSERT IGNORE INTO characters (user_id, name, weapon_id, class, level, exp, health, max_health, strength, magic, speed, defense, logic) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        write_execute(query,values)

    def add_item(self,user_id,item_id,amount):
        #all this is doing is to check that there are no duplicates of the same item_id within the db
        results = read_all_execute('SELECT * FROM inventories WHERE user_id = %s', (user_id,))
        for items in results:
            if items[1] == item_id:
                if items[2]+amount > 0:
                    write_execute('UPDATE inventories SET amount = %s WHERE (user_id, item_id) = (%s, %s)', (items[2]+amount,user_id,item_id))
                    DB_logger.info("%s of %s has been added to %s's inventory" % (amount,item_id,user_id))
                    return
                write_execute("DELETE FROM inventories WHERE user_id = %s AND item_id = %s",(user_id,item_id))
                DB_logger.info("%s has used %s" % (user_id,item_id))
                return
        write_execute("INSERT INTO inventories (user_id, item_id, amount) VALUES (%s, %s, %s)", (user_id, item_id, amount))
        DB_logger.info("%s of %s has been added to %s's inventory" % (amount,item_id,user_id))

    def add_bank(self,user_id,amount):
        query = "INSERT IGNORE INTO bank (user_id, money) VALUES (%s, %s)"
        write_execute(query, (user_id,amount))

    #under construction
    #enemies: message_id, name, weapon_id, class, level, health, max_health, strength, magic, speed, defense, logic
    def add_enemy(self,enemy_data):
        query = "INSERT INTO enemies (message_id, name, weapon_id, class, level, exp, health, max_health, strength, magic, speed, defense, logic, loot, combat_log) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        write_execute(query, (enemy_data[0],enemy_data[1],enemy_data[2],enemy_data[3],enemy_data[4],enemy_data[5],enemy_data[6],enemy_data[7],enemy_data[8],enemy_data[9],enemy_data[10],enemy_data[11],enemy_data[12],enemy_data[13],enemy_data[14]))

#####################################################################################################################################################

    def insert_item(self,itemname,cost,item_type,item_description):
        write_execute("INSERT IGNORE INTO items (item_id, name, cost, type, description) VALUES (%s, %s, %s, %s, %s)", (hash_string(itemname), itemname, cost, item_type, item_description))

    def insert_weapon(self,itemname,type,power,crit,physical):
        write_execute("INSERT IGNORE INTO weapons (item_id, type, power, crit, damage_type) VALUES (%s, %s, %s, %s, %s)", (hash_string(itemname), type, power, crit, physical))

    def insert_usable(self,itemname,target,amount):
        write_execute("INSERT IGNORE INTO usables (item_id, target, amount) VALUES (%s, %s, %s)", (hash_string(itemname), target, amount))

    def insert_campaign(self,campaign_name, waves, starting_level, level_increase, time):
        write_execute("INSERT IGNORE INTO campaigns (campaign_name, waves, starting_level, level_increase, time) VALUES (%s, %s, %s, %s, %s)", (campaign_name, waves, starting_level, level_increase, time))

    def insert_class(self,classname,growth_rate,description,attributes,weapon_choices):
        write_execute("INSERT INTO classes (class_name, growth_rate, description, attributes, weapon_choices) VALUES (%s, %s, %s, %s, %s)", (classname,growth_rate,description,attributes,weapon_choices))

    def insert_graphic(self,graphic_name, value):
        write_execute("INSERT IGNORE INTO graphics (graphic_name, value) VALUES (%s, %s)", (graphic_name, value))

#####################################################################################################################################################

#user: user_id,faction,daily,weekly,first
    def update_user(self,user_data):
        query = "UPDATE users SET daily = %s, weekly = %s, first=%s WHERE user_id = %s"
        write_execute(query,(user_data[1],user_data[2],user_data[3],user_data[0]))
        DB_logger.info(f"{user_data[0]} has been updated")

#character: user_id, name, money, class, level, exp, health, max_health, strength, magic, speed, defense, logic
    def update_character(self,character_data):
        query = "UPDATE characters SET name = %s, weapon_id = %s, class = %s, level = %s, exp = %s, health = %s, max_health = %s, strength = %s, magic = %s, speed = %s, defense = %s, logic = %s WHERE user_id = %s"
        write_execute(query,(character_data[1],character_data[2],character_data[3],character_data[4],character_data[5],character_data[6],character_data[7],character_data[8],character_data[9],character_data[10],character_data[11],character_data[12],character_data[0]))
        DB_logger.info(f"{character_data[0]} has been updated")

    def update_enemy(self,enemy_data):
        query = "UPDATE enemies SET name = %s, weapon_id = %s, class = %s, level = %s, exp = %s, health = %s, max_health = %s, strength = %s, magic = %s, speed = %s, defense = %s, logic = %s, loot = %s, combat_log = %s WHERE message_id = %s"
        write_execute(query,(enemy_data[1],enemy_data[2],enemy_data[3],enemy_data[4],enemy_data[5],enemy_data[6],enemy_data[7],enemy_data[8],enemy_data[9],enemy_data[10],enemy_data[11],enemy_data[12],enemy_data[13],enemy_data[14],enemy_data[0]))
        DB_logger.info(f"{enemy_data[0]} has been updated")

    def update_bank(self,user_id,amount):
        query = "UPDATE bank SET money = %s WHERE user_id = %s"
        current_balance = self.get_bank(user_id)[1]
        if amount > current_balance:
            DB_logger.info(f"{user_id} has gained {amount-current_balance} dollars")
        else:
            DB_logger.info(f"{user_id} has lost {current_balance-amount} dollars")
        write_execute(query,(amount,user_id))

    def delete_enemy(self,msg_id):
        write_execute("DELETE FROM enemies WHERE message_id = %s", (msg_id,))


#####################################################################################################################################################

    def get_item(self,item_id):
        query = "SELECT * FROM items WHERE item_id = %s"
        return read_execute(query,(str(item_id),))

    def get_usable(self,item_id):
        query = "SELECT * FROM usables WHERE item_id = %s"
        return read_execute(query,(str(item_id),))

    def get_user(self,user_id):
        query = "SELECT * FROM users WHERE user_id = %s"
        return read_execute(query,(str(user_id),))

    def get_user_item(self,user_id,item_id):
        query = "SELECT * FROM inventories WHERE user_id = %s AND item_id = %s"
        return read_execute(query,(user_id,item_id))

    def get_character(self,user_id):
        query = "SELECT * FROM characters WHERE user_id = %s"
        return read_execute(query,(str(user_id),))

    def get_bank(self,user_id):
        query = "SELECT * FROM bank WHERE user_id = %s"
        return read_execute(query,(str(user_id),))

    def get_inventory(self,user_id):
        ans = {}
        results = read_all_execute('SELECT * FROM inventories WHERE user_id = %s', (user_id,))
        for items in results:
            ans[self.get_item(items[1])[1]] = items[2]
        return ans

    def get_class(self,classname):
        query = "SELECT * FROM classes WHERE class_name = %s"
        return read_execute(query,(classname,))

    def get_weapon(self,weapon_id):
        query = "SELECT * FROM weapons WHERE item_id = %s"
        return read_execute(query,(weapon_id,))

    def get_enemy(self,msg_id):
        query = "SELECT * FROM enemies WHERE message_id = %s"
        return read_execute(query,(msg_id,))

    def get_campaign(self,campaign_name):
        query = "SELECT * FROM campaigns WHERE campaign_name = %s"
        return read_execute(query,(campaign_name,))

    def get_graphic(self,graphic_name):
        query = "SELECT * FROM graphics WHERE graphic_name = %s"
        return read_execute(query,(graphic_name,))

#####################################################################################################################################################

    def get_all_item(self):
        query = "SELECT name FROM items"
        return read_all_execute(query,"")

    def delete_table(self):
        tables = read_all_execute("SHOW TABLES","")
        ## showing all the tables one by one
        for table in tables:
            execute(f"DROP TABLE {table[0]}")

    def show_table(self):
        tables = read_all_execute("SHOW TABLES","")
        for table in tables:
            print(table)

    def table_values(self,table):
        con = mysql.connect(host="localhost",user="pi",passwd="WUHANpja123",database = "TBG")
        cur = con.cursor()
        cur.execute("SELECT * FROM enemies")
        answer = cur.fetchall()
        cur.close()
        con.close()
        print(answer)

    def get_info(self):
        tables = read_all_execute("DESCRIBE items","")
        for table in tables:
            print(table)
