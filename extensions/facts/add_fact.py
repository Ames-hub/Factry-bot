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
        description='A fact that you want to add to the category.',
        required=True,
        type=hikari.OptionType.STRING
    )
    @lightbulb.option(
        name='category',
        description='The category of the fact.',
        required=True,
        type=hikari.OptionType.STRING
    )
    @lightbulb.command(name="add", description="Add a fact to a category.")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def add_fact_cmd(ctx: lightbulb.SlashContext) -> None:
        fact = ctx.options.fact
        category = ctx.options.category

        category_did_exist = mem.does_category_exists(category)
        try:
            mem.add_fact(category, ctx.author.id, fact)
        except sqlite3.IntegrityError:
            embed = (
                hikari.Embed(
                    title="Uh oh!",
                    description=f"The fact already exists in the '{category}' category!",
                    color=plugin.bot.d['colourless'],
                )
            )

            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return

        embed = (
            hikari.Embed(
                title="Fact added",
                description=f"The fact has been added to the '{category}' category!",
                color=plugin.bot.d['colourless'],
            )
        )
        if not category_did_exist:
            embed.add_field(
                name="New category",
                value=f"That category did not exist before, so it has been created.\n"
                      "This means the category has facts, but no triggers associated with it.\n"
                      "You can add a trigger to the category using the /add_trigger command.",
            )
        elif category_did_exist and mem.len_triggers(category) == 0:
            embed.add_field(
                name="No triggers",
                value=f"The category already existed, but it did not have any triggers associated with it.\n"
                      "You can add a trigger to the category using the /add_trigger command.",
            )

        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))