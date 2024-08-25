import sqlite3
import os

os.remove("duels.db")
connection = sqlite3.connect("duels.db")
crsr = connection.cursor()
crsr.execute("CREATE TABLE duels (id INTEGER, player1, player2, bet, currentTask, currentCode, guesses1, guesses2, status, PRIMARY KEY(id))")
connection.commit()
crsr.close()
connection.close()
test = open("duels.db", "r")
test.close()