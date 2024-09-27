<div style="text-align: center;">

# Factry bot
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![Sqlite3](https://img.shields.io/badge/Sqlite-3-blue)

A discord bot that auto-responds to set words/phrases with a random fact in a category of facts.
</div>

## Commands
These are all the slash commands that the bot can respond to.
- `github` - Sends a link to the GitHub repository.
- `add_fact` - Adds a fact to the database for a category.
- `rm_fact` - Removes a fact from the database for a category.
- `add_trigger` - Adds a trigger to the database for a category.
- `rm_trigger` - Removes a trigger from the database for a category.

## Usage
To use the bot, simply type a trigger word/phrase in a discord channel that the bot is in. The bot will then respond
with a random fact from the category of facts that the trigger word/phrase is associated with.

### Adding a category
To add a category, simply use the 'add fact' or 'add trigger' commands and set the 'category' parameter to the desired category name.
The bot will automatically create a new category if it does not already exist.

#### Default Categories / Triggers
- train
- space
- literature
- science

(Technical) Check the `category_fact_dict` variable in bot.py for the default categories and facts

### Removing a category
To remove a category, you must remove all triggers and facts associated with the category.
There will later be a command dedicated to making this a bit easier.
