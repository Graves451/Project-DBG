import database
import game
import json
import datetime

import discord
from discord.ext.commands import Bot
from discord.ext import tasks, commands

db = database.Database()

with open("/home/pi/Atom/TBG/game_data/bot_token.json","r") as f:
    file = json.load(f)
    token = file["Karl"]
    f.close()

alcoholic_drinks = ["vodka","whiskey","gin","sake","beer","tequila"]
stats_target = ["HP","Max HP","STR","MAG","SPD","DEF","LOG"]

class tavernkeeper:
    def __init__(self,token):
        self.token = token
        self.client = Bot(command_prefix=".")
        self.client.remove_command("help")
        self.prepare_client()

    def run(self):
        self.client.run(self.token)

    def get_discord_emoji(self,emoji_id):
        return self.client.get_emoji(int(emoji_id))

    def prepare_client(self):
        @self.client.event
        async def on_ready():
            print("ready to drink")

        @self.client.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                return
            raise error

        @self.client.command()
        async def menu(ctx):
            MenuEmbed = discord.Embed(colour=discord.Colour.dark_green())
            MenuEmbed.set_author(name="Tavern Menu")
            for drink_name in alcoholic_drinks:
                item_data = db.get_usable(game.hash_string(drink_name))
                MenuEmbed.add_field(name=f"{self.get_discord_emoji(db.get_graphic(drink_name)[1])} **{drink_name}**",value=f"`TRG` {stats_target[item_data[1]-6]} \n `AMT` {item_data[2]}")
            MenuEmbed.set_footer(text="Karl also offers free water every 30m using .drink")
            await ctx.message.channel.send(embed=MenuEmbed)

        @self.client.command()
        async def order(ctx):
            user = ctx.message.author
            target_drink = ctx.message.content[7:]
            user_data = list(db.get_user(user.id))
            char_data = db.get_character(user.id)
            if user_data[6] >= int(char_data[4]/5):
                await ctx.message.channel.send(f"you need to level up a little more to get more drinks")
                return
            if target_drink not in alcoholic_drinks:
                await ctx.message.channel.send(f"sorry man, i don't carry any {target_drink}")
                return
            cost = min(int(char_data[4]/5),user_data[6]+1)*100
            if game.update_money(user.id,-cost):
                user_data[6]+=1
                db.add_item(user.id,game.hash_string(target_drink),1)
                db.update_user(user_data)
                await ctx.message.channel.send(f"you bought {target_drink} for {cost}{self.get_discord_emoji(822330641559191573)}")
                return
            await ctx.message.channel.send(f"next drink costs {cost}{self.get_discord_emoji(822330641559191573)}")

        @self.client.command()
        async def drink(ctx):
            user = ctx.message.author
            timer_data = db.get_timer(user.id,"drink")
            if timer_data is not None:
                dif = datetime.datetime.now()-timer_data[2]
                if dif.seconds < 1800:
                    await ctx.message.channel.send(f"{str(datetime.timedelta(seconds=1800-int(dif.total_seconds())))} left")
                    return
                else:
                    db.update_timer(user.id,"drink",datetime.datetime.now())
            else:
                db.add_timer(user.id,"drink",datetime.datetime.now())
            db.add_item(user.id,game.hash_string("water"),1)
            await ctx.message.channel.send(f"{user.mention} here's your water {self.get_discord_emoji(db.get_graphic('water')[1])}")

if __name__ == "__main__":
    tavernbot = tavernkeeper(token)
    tavernbot.run()
