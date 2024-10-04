from extensions.list.group import cmd_group, plugin
from library.memory import mem
import lightbulb, hikari
import os

class bot_plugin(lightbulb.Plugin):
    @staticmethod
    @cmd_group.child
    @lightbulb.app_command_permissions(dm_enabled=False)
    @lightbulb.command(name="facts", description="List all facts in the database.")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def fact_listing_cmd(ctx: lightbulb.SlashContext) -> None:
        category_facts = mem.list_all_facts()
        count = len(category_facts)

        if count == 0:
            embed = (
                hikari.Embed(
                    title="Uh oh!",
                    description=f"No facts were found in the database!",
                    color=plugin.bot.d['colourless'],
                )
            )

            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        else:
            # Handles a dict like: {'category': ['fact1', 'fact2']}
            fun_fact_body = ""
            for category in category_facts:
                for fun_fact in category_facts[category]:
                    fun_fact_body += f"**{category}**\n{fun_fact}\n\n"

            if len(fun_fact_body) <= 2000:
                await ctx.respond(f"Here's all the fun facts we have saved!\n\n{fun_fact_body}")
            else:
                # Saves it in a file to send as an attachment
                with open(f"library/fun_facts.txt", "w") as f:
                    f.write(fun_fact_body)

                await ctx.respond(
                    f"Here's all the fun facts we have saved! (Too long to send in a message)",
                    attachment=hikari.files.File(f"library/fun_facts.txt"),
                )

                # Deletes the file after sending
                os.remove(f"library/fun_facts.txt")

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))