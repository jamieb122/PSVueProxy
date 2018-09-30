import sqlite3
import globals
import os

TAG = "DatabaseManger: "

class DatabaseManager():

    db_conn = None
    db_file = "psvueproxy.db"
    cursor = None

    def __init__(self):
        #create connection to DB file
        self.db_conn = sqlite3.connect(self.db_file)

        cursor = self.db_conn.cursor()

        #create the configuration table if it doesn't exist, should just be key/val pairs
        cursor.execute('''CREATE TABLE IF NOT EXISTS configuration (key text PRIMARY KEY, value text)''')
        self.migrate_data_file_to_db(cursor)

        self.db_conn.commit()

    def migrate_data_file_to_db(self, cursor):
        #check if old style data file exists, if so, migrate it to the database and delete it

        if not os.path.exists(globals.DATA_FILE):
            return

        settingsFileContents = globals.get_all_settings()

        if settingsFileContents is None:
            return


        for key in settingsFileContents.keys():
            print(TAG + key + " " + settingsFileContents[key])
            cursor.execute('INSERT INTO configuration VALUES (?,?)', (key, settingsFileContents[key]))

        #remove the old style file as it is now migrated to the db
        os.unlink(globals.DATA_FILE)

    def save_setting(self, key, value):
        self.db_conn.execute("INSERT OR REPLACE INTO configuration VALUES (?,?)", (key,value))
        self.db_conn.commit()

    def get_setting(self, key):
        self.cursor = self.db_conn.cursor()
        self.cursor.execute("SELECT * FROM configuration WHERE key=?", (key,))

        results = self.cursor.fetchone()

        if results is None:
        	return None
        else:
        	return self.cursor.fetchone()[1]


    def __del__(self):
        self.db_conn.close()
