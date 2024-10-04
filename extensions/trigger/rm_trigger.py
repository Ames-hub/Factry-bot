from extensions.trigger.group import cmd_group, plugin
from library.memory import mem
import lightbulb, hikari
import datetime
import logging
import sqlite3

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'logs/{datetime.datetime.now().strftime("%Y-%m-%d")}.log',
)

class bot_plugin(lightbulb.Plugin):
    @staticmethod
    @cmd_group.child()
    @lightbulb.app_command_permissions(dm_enabled=False)
    @lightbulb.option(
        name='trigger',
        description='The trigger word to delete from the list.',
        required=True,
        type=hikari.OptionType.STRING
    )
    @lightbulb.command(name="remove", description="Get rid of a trigger.")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def rm_trigger_cmd(ctx: lightbulb.SlashContext) -> None:
        trigger = ctx.options.trigger

        try:
            mem.remove_trigger(trigger)
        except sqlite3.IntegrityError:
            embed = (
                hikari.Embed(
                    title="Trigger not found",
                    description=f"The trigger '{trigger}' was not found!",
                    color=plugin.bot.d['colourless'],
                )
            )

            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        except Exception as err:
            logging.error(err, exc_info=True)
            embed = (
                hikari.Embed(
                    title="Error",
                    description=f"An error occurred while removing the trigger '{trigger}'!",
                    color=plugin.bot.d['colourless'],
                )
            )

            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return

        embed = (
            hikari.Embed(
                title="Trigger removed",
                description=f"The trigger '{trigger}' has been removed!",
                color=plugin.bot.d['colourless'],
            )
        )

        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))