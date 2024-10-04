from library.memory import mem, get_conn
import lightbulb
import datetime
import sqlite3
import logging
import hikari
import dotenv
import os

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

Intents = hikari.Intents.MESSAGE_CONTENT + hikari.Intents.GUILD_MESSAGES

bot = lightbulb.BotApp(
    token=os.environ.get("TOKEN"),
    intents=Intents,
)

bot.d['colourless'] = hikari.Colour(0x2b2d31)  # Dark theme color of discord used in the embeds

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
already_existing_facts_count = 0
for categories, facts in category_fact_dict.items():
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            for fact in facts:
                cur.execute('''
                    INSERT INTO category_facts (category, added_by, fact)
                    VALUES (?, '1090899298650169385', ?);
                ''', (categories, fact))
    except sqlite3.IntegrityError as err:
        already_existing_facts_count += 1
        continue
conn.commit()

print("Database has been updated with new facts.")
print(f"{already_existing_facts_count} facts already existed in the database and were not added.")

bot.load_extensions_from("extensions")
bot.load_extensions_from("extensions/facts")
bot.load_extensions_from("extensions/list")
bot.load_extensions_from("extensions/trigger")

bot.run()
