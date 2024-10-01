from difflib import SequenceMatcher
import lightbulb
import datetime
import sqlite3
import logging
import hikari
import dotenv
import os

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'logs/{datetime.datetime.now().strftime("%Y-%m-%d")}.log',
)

if not os.path.exists('secrets.env'):
    print("Welcome to bot setup. Please enter your bot token below.")
    token = input("Token: ")
    with open('secrets.env', 'w') as f:
        f.write(f'TOKEN={token}')
    print("Token has been saved to secrets.env. The bot will now start.")

if os.path.exists('secrets.env'):
    dotenv.load_dotenv('secrets.env')

bot = lightbulb.BotApp(
    token=os.environ.get("TOKEN"),
    intents=hikari.Intents.MESSAGE_CONTENT,
)

bot.d['colourless'] = hikari.Colour(0x2b2d31)  # Dark theme color of discord used in the embeds

def get_conn():
    conn = sqlite3.connect('memory.sqlite3')
    return conn

class mem:
    @staticmethod
    def modernize():
        """
        This function is used to modernize the database to the current version. It will check if the tables exist and
        if they don't, it will create them. If the tables do exist, it will check if the columns are up to date and if
        they aren't, it will update them.

        :return:
        """
        # Function I pulled from another project.
        # Using this dict, it formats the SQL query to create the tables if they don't exist
        table_dict = {
            'triggers': {
                'trigger': 'TEXT NOT NULL UNIQUE PRIMARY KEY',
                'added_by': 'TEXT NOT NULL',  # Set to be a UUID
                # category is connected to the category_facts table's category column
                'category': 'TEXT NOT NULL REFERENCES category_facts(category)'
            },
            'category_facts': {
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'category': 'TEXT NOT NULL',
                'added_by': 'TEXT NOT NULL',  # Set to be a UUID
                'fact': 'TEXT NOT NULL'
            }
        }

        for table_name, columns in table_dict.items():
            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute(f'''
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table' AND name='{table_name}';
                ''')
                table_exist = cur.fetchone() is not None

            # If the table exists, check and update columns
            if table_exist:
                for column_name, column_properties in columns.items():
                    # Check if the column exists
                    cur.execute(f'''
                        PRAGMA table_info({table_name});
                    ''')
                    columns_info = cur.fetchall()
                    column_exist = any(column_info[1] == column_name for column_info in columns_info)

                    # If the column doesn't exist, add it
                    if not column_exist:
                        cur.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_properties};')

            # If the table doesn't exist, create it with columns
            else:
                columns_str = ', '.join(
                    [f'{column_name} {column_properties}' for column_name, column_properties in columns.items()]
                )
                try:
                    cur.execute(f'CREATE TABLE {table_name} ({columns_str});')
                except sqlite3.OperationalError as e:
                    logging.info(f"Could not create table '{table_name}'. Error: {e}")
                    exit(1)

    @staticmethod
    def does_category_exists(category):
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT category
                FROM triggers
                WHERE category = ?;
            ''', (category,))
            return cur.fetchone() is not None

    @staticmethod
    def does_trigger_exists(trigger):
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT trigger
                FROM triggers
                WHERE trigger = ?;
            ''', (trigger,))
            return cur.fetchone() is not None

    @staticmethod
    def is_fact_already_exists(category, fact):
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT fact
                FROM category_facts
                WHERE category = ? AND fact = ?;
            ''', (category, fact))
            return cur.fetchone() is not None

    @staticmethod
    def add_fact(category, author_id, fact):
        if mem.is_fact_already_exists(category, fact):
            raise sqlite3.IntegrityError("The fact already exists in the database")

        author_id = str(author_id)

        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO category_facts (category, added_by, fact)
                VALUES (?, ?, ?);
            ''', (category, author_id, fact))
            conn.commit()
        return True

    @staticmethod
    def remove_fact(category, fact):
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                DELETE FROM category_facts
                WHERE category = ? AND fact = ?;
            ''', (category, fact))
            conn.commit()
        return True

    @staticmethod
    def add_trigger(trigger, category, user_id):
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO triggers (trigger, added_by, category)
                VALUES (?, ?, ?);
            ''', (trigger, str(user_id), category))
            conn.commit()

    @staticmethod
    def remove_trigger(trigger):
        if not mem.does_trigger_exists(trigger):
            raise sqlite3.IntegrityError("The trigger does not exist in the database")

        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                DELETE FROM triggers
                WHERE trigger = ?;
            ''', (trigger,))
            conn.commit()

    @staticmethod
    def get_all_triggers():
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT trigger
                FROM triggers;
            ''')
            return cur.fetchall()

    @staticmethod
    def get_all_categories():
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT category
                FROM triggers;
            ''')
            return cur.fetchall()

    @staticmethod
    def len_triggers(category=None):
        with get_conn() as conn:
            cur = conn.cursor()
            if category is None:
                cur.execute('''
                    SELECT COUNT(*)
                    FROM triggers;
                ''')
            else:
                cur.execute('''
                    SELECT COUNT(*)
                    FROM triggers
                    WHERE category = ?;
                ''', (category,))
            return cur.fetchone()[0]

    @staticmethod
    def len_facts(category=None):
        with get_conn() as conn:
            cur = conn.cursor()
            if category is None:
                cur.execute('''
                    SELECT COUNT(*)
                    FROM category_facts;
                ''')
            else:
                cur.execute('''
                    SELECT COUNT(*)
                    FROM category_facts
                    WHERE category = ?;
                ''', (category,))
            return cur.fetchone()[0]

    @staticmethod
    def is_trigger(msg: str) -> dict:
        triggers = mem.get_all_triggers()
        for trigger in triggers:
            # Detects if the trigger and the message are similiar using the difflib library
            if SequenceMatcher(None, trigger[0], msg).ratio() > 0.8:
                # Finds the category of the trigger
                with get_conn() as conn:
                    cur = conn.cursor()
                    cur.execute('''
                        SELECT category
                        FROM triggers
                        WHERE trigger = ?;
                    ''', (msg,))
                    category = cur.fetchone()

                return {'result': True, 'trigger': trigger[0], 'category': category[0]}

        return {'result': False, 'trigger': None, 'category': None}

    @staticmethod
    def find_most_similar(trigger) -> str:
        """
        This function is used to find the most similar trigger to the one provided.
        :return: The most similar trigger or the original trigger if no close match is found
        """
        category = mem.get_all_categories()
        most_similar = trigger
        highest_similarity = 0
        similarity_threshold = 0.8  # Define a threshold for similarity

        for category in category:
            category = category[0]
            similarity = SequenceMatcher(None, trigger, category).ratio()
            if similarity > highest_similarity:
                highest_similarity = similarity
                most_similar = category

        # Return the original trigger if no match exceeds the threshold
        if highest_similarity < similarity_threshold:
            return trigger

        return most_similar

    @staticmethod
    def get_fact(trigger: str) -> str:
        """
        This function is used to get a random fact from the database based on the trigger provided.
        :param trigger:
        :return:
        """
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(f'''
                SELECT fact
                FROM category_facts
                WHERE category = ?
                ORDER BY RANDOM()
                LIMIT 1;
            ''', (trigger,))
            data = cur.fetchone()
        if data is not None:
            return data[0]
        return "There are no fun facts found for this category. :("

mem.modernize()

# ALl the categories and facts that the bot starts off with.
category_fact_dict = {
    'train': [
        'The first public railway to use steam locomotives was the Stockton and Darlington Railway in 1825.',
        'Japan\'s Shinkansen, also known as the bullet train, can reach speeds of up to 320 km/h (200 mph).',
        'The longest railway in the world is the Trans-Siberian Railway, which spans over 9,289 kilometers (5,772 miles).',
        'The world\'s first underground railway, the London Underground, opened in 1863.',
        'The fastest train in the world is the Shanghai Maglev, which can reach speeds of up to 431 km/h (267 mph).',
        'The first electric train was built in 1879 by Siemens & Halske in Berlin, Germany.',
        'The Glacier Express in Switzerland is known as the slowest express train in the world, taking around 8 hours to travel 291 kilometers (181 miles).'
    ],
    'space': [
        'A day on Venus is longer than a year on Venus.',
        'There are more stars in the universe than grains of sand on all the Earth\'s beaches.',
        'The largest volcano in the solar system is Olympus Mons on Mars, which is about 13.6 miles (22 kilometers) high.',
        'Neutron stars are so dense that a sugar-cube-sized amount of material from one would weigh about a billion tons on Earth.',
        'The Milky Way galaxy is on a collision course with the Andromeda galaxy, and they are expected to merge in about 4.5 billion years.',
        'The footprints left by astronauts on the Moon are likely to remain there for millions of years because there is no wind or water to erode them.',
        'Jupiter has the shortest day of all the planets in the solar system, with a rotation period of just under 10 hours.'
    ],
    'literature': [
        'The longest novel ever written is "In Search of Lost Time" by Marcel Proust, which contains an estimated 1.2 million words.',
        'William Shakespeare is credited with inventing over 1,700 words in the English language.',
        'The first book ever written using a typewriter was "The Adventures of Tom Sawyer" by Mark Twain.',
        'The world\'s most expensive book ever sold is Leonardo da Vinci\'s "Codex Leicester," which was purchased by Bill Gates for $30.8 million in 1994.',
        'The shortest war in history was between Britain and Zanzibar on August 27, 1896, lasting between 38 and 45 minutes.',
        'The first novel ever written is considered to be "The Tale of Genji," written by Murasaki Shikibu in the early 11th century.',
        'The Library of Congress in Washington, D.C., is the largest library in the world, with over 170 million items in its collections.'
    ],
    'science': [
        'Water can boil and freeze at the same time, a phenomenon known as the "triple point".',
        'Bananas are naturally radioactive due to their high potassium content.',
        'The speed of light in a vacuum is approximately 299,792 kilometers per second (186,282 miles per second).',
        'The human body contains about 37.2 trillion cells.',
        'The DNA in a single human cell, if stretched out, would be about 2 meters (6.5 feet) long.',
        'The Earth\'s core is as hot as the surface of the Sun, with temperatures reaching up to 5,500 degrees Celsius (9,932 degrees Fahrenheit).',
        'A single bolt of lightning contains enough energy to toast 100,000 slices of bread.'
    ]
}

# Load the categories from text files in the 'categories' directory
if os.path.exists('categories'):
    for category in os.listdir('categories'):
        # If the file type is not .txt, skip it
        if not category.endswith('.txt'):
            continue
        with open(f'categories/{category}', 'r') as f:
            category = category.replace('.txt', '')
            category_fact_dict[category] = [line.strip() for line in f.readlines()]

# Add triggers to the database for each category
for category in category_fact_dict.keys():
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO triggers (trigger, added_by, category)
                VALUES (?, '1090899298650169385', ?);
            ''', (category, category))
    except sqlite3.IntegrityError:
        continue

# Add default facts to the database
for categories, facts in category_fact_dict.items():
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            for fact in facts:
                cur.execute('''
                    INSERT INTO category_facts (category, added_by, fact)
                    VALUES (?, '1090899298650169385', ?);
                ''', (categories, fact))
    except sqlite3.IntegrityError:
        continue

conn.commit()

print("Database has been updated with new facts.")

@bot.listen()
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
            await event.message.respond(f"Fun {is_trigger['trigger']} fact! {fun_fact}")
            # return so as to prevent multiple responses from the bot
            return

@bot.command
@lightbulb.app_command_permissions(dm_enabled=True)
@lightbulb.command(name="github", description="Get the github link for the bot.")
@lightbulb.implements(lightbulb.SlashCommand)
async def github_cmd(ctx: lightbulb.SlashContext) -> None:
    embed = (
        hikari.Embed(
            title="'https://github.com/Ames-hub/Factry-bot'",
            description="This is the github link for the bot! If you encounter a problem, you can open a pull request here.",
            color=bot.d['colourless'],
        )
    )

    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@bot.command
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
@lightbulb.command(name="add_trigger", description="Add a trigger for a category to the bot.")
@lightbulb.implements(lightbulb.SlashCommand)
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
                color=bot.d['colourless'],
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
                color=bot.d['colourless'],
            )
        )

        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return

    embed = (
        hikari.Embed(
            title="Trigger added",
            description=f"The trigger '{trigger}' has been added to the '{category}' category!",
            color=bot.d['colourless'],
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

@bot.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='trigger',
    description='The trigger word to delete from the list.',
    required=True,
    type=hikari.OptionType.STRING
)
@lightbulb.command(name="rm_trigger", description="Get rid of a trigger.")
@lightbulb.implements(lightbulb.SlashCommand)
async def rm_trigger_cmd(ctx: lightbulb.SlashContext) -> None:
    trigger = ctx.options.trigger

    try:
        mem.remove_trigger(trigger)
    except sqlite3.IntegrityError:
        embed = (
            hikari.Embed(
                title="Trigger not found",
                description=f"The trigger '{trigger}' was not found!",
                color=bot.d['colourless'],
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
                color=bot.d['colourless'],
            )
        )

        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return

    embed = (
        hikari.Embed(
            title="Trigger removed",
            description=f"The trigger '{trigger}' has been removed!",
            color=bot.d['colourless'],
        )
    )

    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@bot.command
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
@lightbulb.command(name="add_fact", description="Add a fact to a category.")
@lightbulb.implements(lightbulb.SlashCommand)
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
                color=bot.d['colourless'],
            )
        )

        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return

    embed = (
        hikari.Embed(
            title="Fact added",
            description=f"The fact has been added to the '{category}' category!",
            color=bot.d['colourless'],
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

@bot.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='fact',
    description='The fact that you want to remove from the category.',
    required=True,
    type=hikari.OptionType.STRING
)
@lightbulb.option(
    name='category',
    description='The category of the fact.',
    required=True,
    type=hikari.OptionType.STRING
)
@lightbulb.command(name="rm_fact", description="Add a fact to a category.")
@lightbulb.implements(lightbulb.SlashCommand)
async def remove_fact_cmd(ctx: lightbulb.SlashContext) -> None:
    fact = ctx.options.fact
    category = ctx.options.category

    try:
        mem.remove_fact(category, fact)
    except sqlite3.IntegrityError:
        embed = (
            hikari.Embed(
                title="Uh oh!",
                description=f"The fact was not found in the '{category}' category!",
                color=bot.d['colourless'],
            )
        )

        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return

    embed = (
        hikari.Embed(
            title="Fact removed",
            description=f"The fact '{fact}' has been deleted from the record.",
            color=bot.d['colourless'],
        )
    )

    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

bot.run()
