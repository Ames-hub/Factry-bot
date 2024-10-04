import lightbulb, hikari

pl_name = __name__
plugin = lightbulb.Plugin(pl_name)

class bot_plugin(lightbulb.Plugin):
    @staticmethod
    @plugin.command
    @lightbulb.app_command_permissions(dm_enabled=True)
    @lightbulb.command(name="github", description="Get the github link for the bot.")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def github_cmd(ctx: lightbulb.SlashContext) -> None:
        embed = (
            hikari.Embed(
                title="https://github.com/Ames-hub/Factry-bot",
                description="This is the github link for the bot! If you encounter a problem, you can open a pull request here.",
                color=plugin.bot.d['colourless'],
            )
        )

        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))