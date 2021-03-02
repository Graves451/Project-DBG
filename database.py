import mysql.connector as mysql
import hashlib
import datetime

#currently have problems with the insert_class
#make a delete proof table for user characters and inventories
#https://stackoverflow.com/questions/7948302/is-it-possible-to-disable-deletes-on-a-table-on-mysql

#user: user_id,faction,daily,weekly,first
#character: user_id, name, class, level, exp, health, max_health, strength, magic, speed, defense, logic

def hash_string(string_input):
    #used to return a relatively unique id with a length of 8 of the string
    return int(hashlib.sha256(string_input.encode('utf-8')).hexdigest(), 16) % 10**8

db = mysql.connect(
    host="localhost",
    user="pi",
    passwd="WUHANpja123",
    database = "testdb"
)

cursor = db.cursor()

class Database:
    def setup(self):
        #creates a table object for other users
        cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INT(11) NOT NULL PRIMARY KEY, faction VARCHAR(255), daily DATETIME, weekly DATETIME, first DATE)")
        cursor.execute("CREATE TABLE IF NOT EXISTS characters (user_id INT(11) NOT NULL PRIMARY KEY, name VARCHAR(255), class VARCHAR(255), level INT(11), exp INT(11), health INT(11), max_health INT(11), strength INT(11), magic INT(11), speed INT(11), defense INT(11), logic INT(11))")
        cursor.execute("CREATE TABLE IF NOT EXISTS inventories (user_id INT(11) NOT NULL, item_id INT(11), amount INT(11))")
        cursor.execute("CREATE TABLE IF NOT EXISTS classes (class_name VARCHAR(255) NOT NULL PRIMARY KEY, growth_rate VARCHAR(255), description VARCHAR(255), attributes VARCHAR(255), graphic VARCHAR(255))")
        cursor.execute("CREATE TABLE IF NOT EXISTS items (item_id INT(11) NOT NULL PRIMARY KEY, name VARCHAR(255), cost INT(11), type VARCHAR(255), description VARCHAR(255), graphic INT(11))")
        cursor.execute("CREATE TABLE IF NOT EXISTS weapons (item_id INT(11) NOT NULL PRIMARY KEY, type VARCHAR(255), power INT(11), crit INT(11))")
        cursor.execute("CREATE TABLE IF NOT EXISTS usables (item_id INT(11) NOT NULL PRIMARY KEY, target VARCHAR(255), amount INT(11))")

    def load_game_data(self):
        #clears the tables everytime
        #loads all the game's data from the text files into the db
        file_data = open("game_data/item_data.txt","r")
        for line_input in file_data.readlines():
            line = line_input.split(",")
            #item: itemname, cost, item_type, item_description, graphic
            self.insert_item(line[0],int(line[1]),line[2],line[3],int(line[4]))
            if line[2] == "weapon":
                #weapon: itemname, cost, item_type, item_description, graphic, weapon_type, power, crit
                self.insert_weapon(line[0],line[5],line[6],line[7])
            if line[2] == "usable":
                #usable: itemname, cost, item_type, item_description, graphic, target, amount
                self.insert_usable(line[0],line[5],line[6])

        file_data = open("game_data/class_data.txt","r")
        for line_input in file_data.read().splitlines():
            line = line_input.split(",")
            #class: classname, growth_rate, description, attributes, graphic
            self.insert_class(line[0],line[1],line[2],line[3],line[4])

    def clear_game_data(self):
        cursor.execute("DROP TABLE items")
        cursor.execute("DROP TABLE classes")
        cursor.execute("DROP TABLE weapons")
        cursor.execute("DROP TABLE usables")

#####################################################################################################################################################

    def add_user(self,user_id,faction):
        now = datetime.datetime.now()
        ## defining the Query
        query = "INSERT IGNORE INTO users (user_id, faction, daily, weekly, first) VALUES (%s, %s, %s, %s, %s)"
        ## storing values in a variable
        values = (user_id, faction, now-datetime.timedelta(days=1), now-datetime.timedelta(days=7), now.date())
        ## executing the query with values
        cursor.execute(query, values)
        ## to make final output we have to run the 'commit()' method of the database object
        db.commit()

    def add_character(self,user_id,name,user_class):
        query = "INSERT IGNORE INTO characters (user_id, name, class, level, exp, health, max_health, strength, magic, speed, defense, logic) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (user_id, name, user_class, 1, 0, 15, 15, 6, 5, 7, 5, 3)
        cursor.execute(query, values)
        db.commit()

    def add_item(self,user_id,item_id,amount):
        #all this is doing is to check that there are no duplicates of the same item_id within the db
        cursor.execute('SELECT * FROM inventories WHERE user_id = %s', (user_id,))
        results = cursor.fetchall()
        for items in results:
            if items[1] == item_id:
                cursor.execute('UPDATE inventories SET amount = %s WHERE (user_id, item_id) = (%s, %s)', (items[2]+amount,user_id,item_id))
                print("%s of %s has been added to %s's inventory" % (amount,item_id,user_id))
                db.commit()
                return
        cursor.execute("INSERT INTO inventories (user_id, item_id, amount) VALUES (%s, %s, %s)", (user_id, item_id, amount))
        print("%s of %s has been added to %s's inventory" % (amount,item_id,user_id))
        db.commit()


#####################################################################################################################################################

    def insert_item(self,itemname,cost,item_type,item_description,graphic):
        cursor.execute("INSERT IGNORE INTO items (item_id, name, cost, type, description, graphic) VALUES (%s, %s, %s, %s, %s, %s)", (hash_string(itemname), itemname, cost, item_type, item_description, graphic))
        db.commit()

    def insert_weapon(self,itemname,type,power,crit):
        cursor.execute("INSERT IGNORE INTO weapons (item_id, type, power, crit) VALUES (%s, %s, %s, %s)", (hash_string(itemname), type, power, crit))
        db.commit()

    def insert_usable(self,itemname,target,amount):
        cursor.execute("INSERT IGNORE INTO usables (item_id, target, amount) VALUES (%s, %s, %s)", (hash_string(itemname), target, amount))
        db.commit()

    def insert_class(self,classname,growth_rate,description,attributes,graphic):
        cursor.execute("INSERT INTO classes (class_name, growth_rate, description, attributes, graphic) VALUES (%s, %s, %s, %s, %s)", (classname,growth_rate,description,attributes,graphic))
        db.commit()

#####################################################################################################################################################

#user: user_id,faction,daily,weekly,first
    def update_user(self,user_data):
        query = "UPDATE users SET faction = %s, daily = %s, weekly = %s, first=%s WHERE user_id = %s"
        cursor.execute(query,(user_data[1],user_data[2],user_data[3],user_data[4],user_data[0]))
        db.commit()

#character: user_id, name, class, level, exp, health, max_health, strength, magic, speed, defense, logic
    def update_character(self,character_data):
        query = "UPDATE characters SET name = %s, class = %s, level = %s, exp = %s, health = %s, max_health = %s, strength = %s, magic = %s, speed = %s, defense = %s, logic = %s WHERE user_id = %s"
        cursor.execute(query,(character_data[1],character_data[2],character_data[3],character_data[4],character_data[5],character_data[6],character_data[7],character_data[8],character_data[9],character_data[10],character_data[11],character_data[0]))
        db.commit()

#####################################################################################################################################################

    def get_item(self,item_id):
        query = "SELECT item_id FROM items WHERE item_id = "+str(item_id)
        cursor.execute(query)
        return cursor.fetchone()

    def get_user(self,user_id):
        query = "SELECT * FROM users WHERE user_id = "+str(user_id)
        cursor.execute(query)
        return cursor.fetchone()

    def get_character(self,user_id):
        query = "SELECT * FROM characters WHERE user_id = "+str(user_id)
        cursor.execute(query)
        return cursor.fetchone()

    def get_class(self,classname):
        query = "SELECT * FROM classes WHERE class_name = "+classname
        cursor.execute(query)
        return cursor.fetchone()

#####################################################################################################################################################

    def delete_table(self):
        cursor.execute("SHOW TABLES")

        tables = cursor.fetchall() ## it returns list of tables present in the database

        ## showing all the tables one by one
        for table in tables:
            cursor.execute("DROP TABLE "+table[0])

    def show_table(self):
        cursor.execute("SHOW TABLES")

        tables = cursor.fetchall() ## it returns list of tables present in the database

        ## showing all the tables one by one
        for table in tables:
            print(table)

    def table_values(self,table):
        cursor.execute("SELECT * FROM "+table)

        tables = cursor.fetchall() ## it returns list of tables present in the database

        ## showing all the tables one by one
        for table in tables:
            print(table)

    def get_info(self):
        cursor.execute("DESCRIBE items")

        tables = cursor.fetchall()
        for table in tables:
            print(table)
