from difflib import SequenceMatcher
import datetime
import logging
import sqlite3
import os

os.makedirs('logs', exist_ok=True)

def get_conn():
    conn = sqlite3.connect('memory.sqlite3')
    return conn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'logs/{datetime.datetime.now().strftime("%Y-%m-%d")}.log',
)

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
                'fact': 'TEXT NOT NULL UNIQUE'
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
    def remove_fact(fact):
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                DELETE FROM category_facts
                WHERE fact = ?;
            ''', (fact,))
            conn.commit()
        return True

    @staticmethod
    def list_all_facts() -> dict:
        """
        Returns fact and catagory in a dict
        :return:
        """
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT category, fact
                FROM category_facts;
            ''')
            data = cur.fetchall()

        # Return a dict with the category as the key and the facts as the value
        facts_catagory_dict = {}
        # Formats it like this: {'category': ['fact1', 'fact2', 'fact3']}
        for category, fact in data:
            if category not in facts_catagory_dict:
                facts_catagory_dict[category] = []
            facts_catagory_dict[category].append(fact)

        return facts_catagory_dict

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

    @staticmethod
    def get_fact_author(fact: str) -> str:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT added_by
                FROM category_facts
                WHERE fact = ?;
            ''', (fact,))
            return cur.fetchone()[0]