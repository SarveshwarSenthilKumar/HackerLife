from sql import *
#yay, cool, thanks, and its good, amazing beans
db = SQL("sqlite:///users2.db")
results = db.execute("SELECT * FROM users")

for i in results:
  db2 = SQL("sqlite:///users.db")
  if i["currentTask"] == None:
    i["currentTask"] = ""
  if i["currentCode"] == None:
    i["currentCode"] = ""
  if i["guesses"] == None:
    i["guesses"] = ""
  if i["itemsOwned"] == None:
    i["itemsOwned"] = ""
  db2.execute("INSERT INTO users (username, password, money, experience, currentTask, currentCode, guesses, itemsOwned, currentDebt) VALUES (?,?,?,?,?,?,?,?,?)", i["username"], i["password"], i["money"], i["experience"], i["currentTask"], i["currentCode"], i["guesses"], i["itemsOwned"], 0)
