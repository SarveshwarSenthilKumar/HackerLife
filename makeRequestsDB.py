import sqlite3
import os

os.remove("requests.db")
connection = sqlite3.connect("requests.db")
crsr = connection.cursor()
crsr.execute("CREATE TABLE requests (id INTEGER, sender, receiver, money, status, PRIMARY KEY(id))")
connection.commit()
crsr.close()
connection.close()
test = open("requests.db", "r")
test.close()