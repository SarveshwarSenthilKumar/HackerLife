import sqlite3
import os

connection = sqlite3.connect("users1.db")
crsr = connection.cursor()
crsr.execute("CREATE TABLE users (id INTEGER, username, password, money, experience, currentTask, currentCode, guesses, itemsOwned, currentDebt, upgrades, blocked, PRIMARY KEY(id))")
connection.commit()
crsr.close()
connection.close()
test = open("users1.db", "r")
test.close()