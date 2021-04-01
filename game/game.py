import database
import random

db = database.Database()

shop_items = []

def generate_shop():
    all_item_names = list(db.get_all_item())
    return random.sample(all_item_names,6)

def update_shop(new_list):
    shop_items = new_list

def get_shop():
    return shop_items
