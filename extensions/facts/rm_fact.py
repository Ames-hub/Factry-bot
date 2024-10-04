from extensions.facts.group import cmd_group, plugin
from library.memory import mem
import lightbulb, hikari
import sqlite3

class bot_plugin(lightbulb.Plugin):
    @staticmethod
    @cmd_group.child
    @lightbulb.app_command_permissions(dm_enabled=False)
    @lightbulb.option(
        name='fact',
        description='The fact that you want to remove from the category.',
        required=True,
        type=hikari.OptionType.STRING
    )
    @lightbulb.command(name="remove", description="Add a fact to a category.")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def remove_fact_cmd(ctx: lightbulb.SlashContext) -> None:
        fact = ctx.options.fact

        try:
            mem.remove_fact(fact)
        except sqlite3.IntegrityError:
            embed = (
                hikari.Embed(
                    title="Uh oh!",
                    description=f"The fact was not found in the category!",
                    color=plugin.bot.d['colourless'],
                )
            )

            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return

        embed = (
            hikari.Embed(
                title="Fact removed",
                description=f"The fact has been deleted from the record.",
                color=plugin.bot.d['colourless'],
            )
        )

        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))