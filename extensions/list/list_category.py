from extensions.list.group import cmd_group, plugin
from library.memory import mem
import lightbulb, hikari

class bot_plugin(lightbulb.Plugin):
    @staticmethod
    @cmd_group.child
    @lightbulb.app_command_permissions(dm_enabled=False)
    @lightbulb.command(name="categories", description="List all the categories in the database.")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def category_list_cmd(ctx: lightbulb.SlashContext) -> None:
        categories = mem.get_all_categories()
        categories = [category[0] for category in categories]

        embed = (
            hikari.Embed(
                title="All Categories",
                description="\n".join(categories),
                color=plugin.bot.d['colourless'],
            )
        )

        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))