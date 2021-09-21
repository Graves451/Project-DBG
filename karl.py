import database
import game

import discord
from discord.ext.commands import Bot
from discord.ext import tasks, commands

db = database.Database()

token = "NjY1MDQzOTE3MjM4MTczNzM2.Xhf4aQ.YLNNlI9uVInZ0DLkLpICpWoak0M"

class tavernkeeper:
    def __init__(self,token):
        self.token = token
        self.client = Bot(command_prefix=".")
        self.client.remove_command("help")
        self.prepare_client()

    def run(self):
        self.client.run(self.token)

    def prepare_client(self):
        @self.client.event
        async def on_ready():
            print("ready to drink")

        @self.client.event
        async def on_command_error(ctx, error):
            return

        @self.client.command()
        async def drink(ctx):
            user = ctx.message.author
            if game.update_money(user.id,-5):
                await ctx.message.channel.send(f"{user.mention} here's your beer 🍺")
                return
            await ctx.message.channel.send("check your wallet, there might be a hole in it")

if __name__ == "__main__":
    tavernbot = tavernkeeper(token)
    tavernbot.run()
