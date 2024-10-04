from extensions.trigger.group import cmd_group, plugin
from library.memory import mem
import lightbulb, hikari
import datetime
import sqlite3
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'logs/{datetime.datetime.now().strftime("%Y-%m-%d")}.log',
)

class bot_plugin(lightbulb.Plugin):
    @staticmethod
    @cmd_group.child
    @lightbulb.app_command_permissions(dm_enabled=False)
    @lightbulb.option(
        name='trigger',
        description='The trigger word to add to the list.',
        required=True,
        type=hikari.OptionType.STRING
    )
    @lightbulb.option(
        name='category',
        description='The category of the trigger word.',
        required=True,
        type=hikari.OptionType.STRING
    )
    @lightbulb.command(name="add", description="Add a trigger for a category to the bot.")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def add_trigger_cmd(ctx: lightbulb.SlashContext) -> None:
        trigger = ctx.options.trigger
        category = ctx.options.category

        category_did_exist = mem.does_category_exists(category)
        try:
            mem.add_trigger(trigger, category, ctx.author.id)
        except sqlite3.IntegrityError as err:
            logging.error(err, exc_info=True)
            embed = (
                hikari.Embed(
                    title="Uh oh!",
                    description=f"The trigger already exists!",
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
                    description=f"An error occurred while adding the trigger '{trigger}' to the '{category}' category!",
                    color=plugin.bot.d['colourless'],
                )
            )

            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return

        embed = (
            hikari.Embed(
                title="Trigger added",
                description=f"The trigger '{trigger}' has been added to the '{category}' category!",
                color=plugin.bot.d['colourless'],
            )
            .set_footer(text=f"Note: Triggers that are too similar to each other will cause problems. Eg, You and your.")
        )

        facts_count = mem.len_facts(category)
        if not category_did_exist and facts_count == 0:
            embed.add_field(
                name="New category",
                value=f"That category did not exist before, so it has been created.\n"
                      "This category now has only 1 trigger, but no facts associated with it.\n"
                      "You can add a fact to the category using the /add_fact command.",
            )
        elif category_did_exist and facts_count == 0:
            embed.add_field(
                name="No facts",
                value=f"The category already existed, but it does not have any facts for the category saved.\n"
                      "You can add a fact to the category using the /add_fact command.",
            )

        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))