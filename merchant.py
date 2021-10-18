import database
import game
import json

import discord
import logging
from discord.ext.commands import Bot
from discord.ext import tasks, commands

help_string = '''```
.shop    returns what's current in shop

.buy <item> <amount>  buy a certain amount of items
.sell <item> <amount> sell a certain amount of items

The shop rotates every 3 hours
and you will always be able to buy small healing potions and large healing potions
```'''

logging.basicConfig(handlers=[logging.FileHandler(filename="logs/merchant.log",
                                                 encoding='utf-8', mode='a+')],
                    format="%(asctime)s %(name)s:%(levelname)s:%(message)s",
                    datefmt="%F %A %T",
                    level=logging.INFO)

with open("/home/pi/Atom/TBG/game_data/bot_token.json","r") as f:
    file = json.load(f)
    token = file["Merchant"]
    f.close()

db = database.Database()

class merchant:
    def __init__(self,token):
        self.token = token
        self.client = Bot(command_prefix=".")
        self.shop = game.shop()
        self.client.remove_command("help")
        self.prepare_client()

    def run(self):
        self.client.run(self.token)

    def get_discord_emoji(self,emoji_id):
        return self.client.get_emoji(int(emoji_id))

    def prepare_client(self):
        @self.client.event
        async def on_ready():
            print("ready to trade")

        @self.client.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                return
            raise error

        @tasks.loop(hours=3.0)
        async def rotate_items():
            self.shop.generate_items()

        @self.client.command()
        async def help(ctx):
            await ctx.message.channel.send(help_string)

        @self.client.command()
        async def shop(ctx):
            ShopEmbed = discord.Embed(colour=discord.Colour.green())
            ShopEmbed.set_author(name="MERCHANT'S SHOP")
            for item_name in self.shop.return_items():
                ShopEmbed.add_field(name=f"{self.get_discord_emoji(db.get_graphic(item_name)[1])} **{item_name}**",value=f"`COST` {int(db.get_item(game.hash_string(item_name))[2]*0.95)}")
            await ctx.message.channel.send(embed=ShopEmbed)

        @self.client.command()
        async def buy(ctx):
            message_contents = ctx.message.content.split(" ")
            user = ctx.message.author
            amount = 1
            if message_contents[-1].isdigit():
                item_name = " ".join(message_contents[1:-1])
                amount = int(message_contents[-1])
            else:
                item_name = " ".join(message_contents[1:])
            if item_name in database.forbidden_items:
                await ctx.message.channel.send(f"you can't buy {item_name} here")
                return
            if db.get_inventory(ctx.message.author.id)[1]+amount > 20:
                await ctx.message.channel.send("you can't have over 20 items")
                return
            for abbreviation in database.abbreviations:
                item_name = item_name.replace(abbreviation[0],abbreviation[1])
            if db.get_item(game.hash_string(item_name)) is None:
                await ctx.message.channel.send(f"{item_name} is not a valid item")
                return
            price = db.get_item(game.hash_string(item_name))[2]
            if item_name in self.shop.return_items():
                price = price*0.95
            if game.update_money(user.id,-price*amount):
                db.add_item(user.id,game.hash_string(item_name),amount)
                await ctx.message.channel.send(f"{user.mention} bought {str(amount)} X {item_name}")
                logging.info(f"{user.id} bought {str(amount)} X {item_name}")
                return
            await ctx.message.channel.send("you don't have enough money, my friend")

        @self.client.command()
        async def sell(ctx):
            user = ctx.message.author
            user_inv = db.get_inventory(user.id)[0]
            message_contents = ctx.message.content.split(" ")
            amount = 1
            if message_contents[-1].isdigit():
                item_name = " ".join(message_contents[1:-1])
                amount = int(message_contents[-1])
            else:
                item_name = " ".join(message_contents[1:])
            for abbreviation in database.abbreviations:
                item_name = item_name.replace(abbreviation[0],abbreviation[1])
            if item_name not in user_inv.keys():
                await ctx.message.channel.send(f"you don't have any {item_name}")
                return
            if user_inv[item_name] >= amount:
                game.update_money(user.id,int(db.get_item(game.hash_string(item_name))[2]*amount/4))
                await ctx.message.channel.send(f"{user.mention} sold {str(amount)} X {item_name} for {int(db.get_item(game.hash_string(item_name))[2]*amount/4)}{self.get_discord_emoji(822330641559191573)}")
                db.add_item(user.id,game.hash_string(item_name),-amount)
                logging.info(f"{str(user.id)} has removed {str(amount)} X {item_name}")
                return
            await message.channel.send(f"you don't have enough {item_name}, my friend")

if __name__ == "__main__":
    MerchantBot = merchant(token)
    MerchantBot.run()
