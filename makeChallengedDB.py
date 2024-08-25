import sqlite3
import os

#os.remove("challenges.db")
connection = sqlite3.connect("challenges.db")
crsr = connection.cursor()
crsr.execute("CREATE TABLE challenges (id INTEGER, player1, task, currentCode, guesses,  PRIMARY KEY(id))")
connection.commit()
crsr.close()
connection.close()
test = open("challenges.db", "r")
test.close()