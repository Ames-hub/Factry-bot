import lightbulb
plugin_name = "trigger"
plugin = lightbulb.Plugin(plugin_name)

@plugin.command
@lightbulb.command(plugin_name, "A Plugin command group.")
@lightbulb.implements(lightbulb.SlashCommandGroup)
# This is what you import V to use the group.child
async def cmd_group(_) -> None:
    pass

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
