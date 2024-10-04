from extensions.list.group import cmd_group, plugin
from library.memory import mem
import lightbulb, hikari

class bot_plugin(lightbulb.Plugin):
    @staticmethod
    @cmd_group.child
    @lightbulb.app_command_permissions(dm_enabled=False)
    @lightbulb.command(name="triggers", description="List all the triggers in the database.")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def trigger_list_cmd(ctx: lightbulb.SlashContext) -> None:
        triggers = mem.get_all_triggers()
        triggers = [trigger[0] for trigger in triggers]

        embed = (
            hikari.Embed(
                title="All Triggers",
                description="\n".join(triggers),
                color=plugin.bot.d['colourless'],
            )
        )

        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))