from library.memory import mem
import lightbulb, hikari
import datetime
import logging

pl_name = __name__
plugin = lightbulb.Plugin(pl_name)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'logs/{datetime.datetime.now().strftime("%Y-%m-%d")}.log',
)

class bot_plugin(lightbulb.Plugin):
    @staticmethod
    @plugin.listener(hikari.events.MessageCreateEvent)
    async def msg_listener(event: hikari.events.MessageCreateEvent) -> None:
        if event.author.is_bot:
            return

        # Make case-insensitive and remove leading/trailing whitespace
        content = str(event.message.content.lower().strip())
        # remove symbols from the content.
        content = ''.join(e for e in content if e.isalnum() or e.isspace())

        for word in content.split(" "):
            closest_match = mem.find_most_similar(word)
            is_trigger = mem.is_trigger(closest_match)
            if is_trigger['result']:
                fun_fact = mem.get_fact(is_trigger['category'])
                if not "fun fact" in fun_fact.lower():
                    body = f"Fun {is_trigger['trigger']} fact! {fun_fact}"
                else:
                    body = fun_fact

                body += f"\n\n*This fact was contributed by <@{mem.get_fact_author(fun_fact)}>!*"

                embed = (
                    hikari.Embed(
                        title=is_trigger['trigger'],
                        description=body,
                        color=plugin.bot.d['colourless'],
                    )
                )
                await event.message.respond(embed=embed)

                # return so as to prevent multiple responses from the bot
                return

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))