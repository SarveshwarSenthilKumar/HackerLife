from flask import Flask, render_template, request, redirect, session, jsonify
from flask_session import Session 
from datetime import datetime
import pytz
from sql import *
import os
import random
import yagmail
import time
import math
import re

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = True 
app.config["SESSION_TYPE"] = "filesystem" 
Session(app)

def clr(): 
  os.system("clear")

@app.route("/surrenderduel", methods=["GET","POST"])
def surrenderduel():
  if not session.get("name"):
    return redirect("/")
  else:
    db2 = SQL("sqlite:///duels.db")
    results=db2.execute("SELECT * FROM duels WHERE status = :status AND player1 = :name OR status = :status AND player2 = :name", status="accepted and playing", name=session.get("name"))

    if len(results) < 0:
      return render_template("sentence.html", sentence="You don't have any duels to surrender!") 

    if results[0]["player1"] == session.get("name"):
        winner = results[0]["player2"]
        playerNo = "player1"
    else:
        winner = results[0]["player1"]
        playerNo = "player2"
    
    status = winner + " won! Opponent Surrendered!"

    username = results[0][playerNo]

    db=SQL("sqlite:///users.db")
    resultse=db.execute("SELECT * FROM users WHERE username = :name", name=username)

    db2=SQL("sqlite:///duels.db")
    results=db2.execute("SELECT * FROM duels WHERE status = :status AND player1 = :name OR status = :status AND player2 = :name", status="accepted and playing", name=session.get("name"))

    if results[0]["player1"] == session.get("name"):
            resultse2=db.execute("SELECT * FROM users WHERE username = :name", name=results[0]["player2"])
    else:
            resultse2=db.execute("SELECT * FROM users WHERE username = :name", name=results[0]["player1"])

    status = session.get("name") + " won!"

    db2.execute("UPDATE duels SEt status = :status WHERE id = :id", status=status, id=results[0]["id"])

    money = resultse[0]["money"]

    money2 = resultse2[0]["money"]

    if money == None or money == "0":
          money=0
    else:
          money=int(money)

    moneyAdded=results[0]["bet"]

    money2 =money2+moneyAdded

    money=money-moneyAdded

    db=SQL("sqlite:///users.db")
    db.execute("UPDATE users SET money = :money WHERE username = :name", money=money, name=session.get("name"))
    db.execute("UPDATE users SET money = :money WHERE username = :name", money=money2, name=resultse2[0]["username"])

    db2.execute("UPDATE duels SET status = :status WHERE id = :id", status=status, id=results[0]["id"])

    return render_template("sentence.html", sentence="You have surrendered!")

@app.route("/mainduel", methods=["GET","POST"])
def mainduel():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      db2 = SQL("sqlite:///duels.db")
      results=db2.execute("SELECT * FROM duels WHERE status = :status AND player1 = :name OR status = :status AND player2 = :name", status="accepted and playing", name=session.get("name"))
      print(results)
      
      if len(results) == 0:
  
        db2 = SQL("sqlite:///duels.db")
        results=db2.execute("SELECT * FROM duels WHERE player1 = :name OR player2 = :name AND status IS NOT NULL", name=session.get("name"))

        if len(results) > 0:
          if results[-1]["status"] != None:
            sentence="You are not participating in any duels! But for your last duel, " + results[-1]["status"]
          elif results[-2]["status"] != None:
            sentence="You are not participating in any duels! But for your last duel! Your last duel has ended, refresh to see the results if you don't see them!" 
          else:
            sentence="You are not participating in any duels!"
        else:
          sentence="You are not participating in any duels!"
          
        return render_template("sentence.html", sentence=sentence)

      currentTask = results[0]["currentTask"]
      currentCode = results[0]["currentCode"]
      id = results[0]["id"]

      playerNo = "play"
      
      if results[0]["player1"] == session.get("name"):
        playerNo = "player1"
        opponent = results[0]["player2"]
      else:
        playerNo = "player2"
        opponent = results[0]["player1"]

      if currentTask == None and currentCode == None:
        file = open("fakeCompanies.txt", "r")

        fakeCompanies = []
        
        for i in file:
          fakeCompanies.append(i)
        file.close()

        companyNO = random.randint(0, len(fakeCompanies)-1)

        file = open("sixLetter.txt", "r")

        words = []
        
        for i in file:
          words.append(i)
        file.close()

        wordNO = random.randint(0, len(words)-1)
          
        task=fakeCompanies[companyNO] + " has hired you to find weaknesses in their system, to do this, you must figure out the six letter codeword! But this time, they've looked at another possible candidate, so you must be the first one to figure out the codeword. You are currently competing against " + str(opponent) + "."
        
        code=words[wordNO].strip()

        db=SQL("sqlite:///duels.db")
        db.execute("UPDATE duels SET currentTask = :task, currentCode = :word WHERE id = :id", task=task, word=code, id=id)

      db=SQL("sqlite:///duels.db")
      results=db.execute("SELECT * FROM duels WHERE id = :id", id=id)

      currentCode=results[0]["currentCode"]

      correctPlaceLetters=[]
      wrongPlaceLetters=[]

      if playerNo == "player1":
        guessesList=results[0]["guesses1"]
      else:
        guessesList=results[0]["guesses2"]

      if guessesList!=None:
        if "," in guessesList:
          guessesList=guessesList.split(",")
        else:
          guessesList=[guessesList]

      print(guessesList)

      if guessesList != None:
        for guess in guessesList:
          for count, i in enumerate(guess):
            if i == currentCode[count] and i not in correctPlaceLetters:
              print(count, i)
              correctPlaceLetters.append(i)
            elif i in currentCode and i not in wrongPlaceLetters:
              wrongPlaceLetters.append(i)
      trueWrongLetters=[]
      for i in wrongPlaceLetters:
        if i not in correctPlaceLetters and i != currentCode[0] and i != currentCode[-1]:
          trueWrongLetters.append(i)

      licp=""

      for i in correctPlaceLetters:
        licp += i + ", "

      licp=licp[:-2]

      liwp=""

      for i in trueWrongLetters:
        liwp += i + ", "

      liwp=liwp[:-2]
        
      task=results[0]["currentTask"]

      wordform=""
      
      for i in currentCode:
        if i in correctPlaceLetters:
          wordform+=i
        else:
          wordform+="_"

      wordform = currentCode[0] + wordform[1:5] + currentCode[-1]

      liwp=""
      for i in trueWrongLetters:
        liwp += i+","
      liwp=liwp[:-1]

      if playerNo == "player1":
        guesses=results[0]["guesses1"]
      else:
        guesses=results[0]["guesses2"]

      if guessesList == None or currentCode not in guessesList:
        db2 = SQL("sqlite:///duels.db")
        results=db2.execute("SELECT * FROM duels WHERE status = :status AND player1 = :name OR status = :status AND player2 = :name", status="accepted and playing", name=session.get("name"))

        coolBeans=["sarveshwar", "lemsa", "imagine_dragons", "elon musk"]

        if results[0]["player1"] == session.get("name"):
          playerNo = "player1"
          opponent = results[0]["player2"]
        else:
          playerNo = "player2"
          opponent = results[0]["player1"]

        if results[0]["player1"] in coolBeans:
          return render_template("game2.html", task=task, liwp=liwp, licp=licp, last=wordform, guesses=guesses, forced="true")
        
        return render_template("game2.html", task=task, liwp=liwp, licp=licp, last=wordform, guesses=guesses)
      else:
        file = open("fakeCompanies.txt", "r")

        fakeCompanies = []
        
        for i in file:
          fakeCompanies.append(i)
        file.close()

        companyNO = random.randint(0, len(fakeCompanies)-1)

        file = open("sixLetter.txt", "r")

        words = []
        
        for i in file:
          words.append(i)
        file.close()

        wordNO = random.randint(0, len(words)-1)
          
        task=fakeCompanies[companyNO] + " has hired you to find weaknesses in their system, to do this, you must figure out the six-letter codeword! But this time, they've looked at another possible candidate, so you must be the first one to figure out the codeword. You are currently competing against " + opponent  + "."
        
        code=words[wordNO].strip()

        username = results[0][playerNo]

        db=SQL("sqlite:///users.db")
        resultse=db.execute("SELECT * FROM users WHERE username = :name", name=username)

        db2=SQL("sqlite:///duels.db")
        results=db2.execute("SELECT * FROM duels WHERE status = :status AND player1 = :name OR status = :status AND player2 = :name", status="accepted and playing", name=session.get("name"))

        if results[0]["player1"] == session.get("name"):
            resultse2=db.execute("SELECT * FROM users WHERE username = :name", name=results[0]["player2"])
        else:
            resultse2=db.execute("SELECT * FROM users WHERE username = :name", name=results[0]["player1"])

        status = session.get("name") + " won!"

        db2.execute("UPDATE duels SEt status = :status WHERE id = :id", status=status, id=id)

        money = resultse[0]["money"]

        money2 = resultse2[0]["money"]

        if money == None or money == "0":
          money=0
        else:
          money=int(money)

        moneyAdded=results[0]["bet"]

        money2 = money2-moneyAdded

        money=money+moneyAdded
 
        db=SQL("sqlite:///users.db")
        db.execute("UPDATE users SET money = :money WHERE username = :name", money=money, name=session.get("name"))
        db.execute("UPDATE users SET money = :money WHERE username = :name", money=money2, name=resultse2[0]["username"])

        sentence="The payment being the bet for the duel."

        return render_template("finished.html", sentence=sentence)
    elif request.method == "POST":
        file = open("sixLetter.txt", "r")
  
        words = []
          
        for i in file:
            words.append(i.strip())
        file.close()
        
        guess=request.form.get("guess").strip().lower()
  
  
        if guess in words:
        
          db=SQL("sqlite:///users.db")
          results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))
          db2=SQL("sqlite:///duels.db")
          results2=db2.execute("SELECT * FROM duels WHERE status = :status AND player1 = :name OR status = :status AND player2 = :name", status="accepted and playing", name=session.get("name"))
          if len(results2) < 1:
            return redirect("/mainduel")
          if len(results) < 1:
            return redirect("/mainduel")
          if results2[0]["player1"] == session.get("name"):
            currentGuesses=results2[0]["guesses1"]
          else:
            currentGuesses=results2[0]["guesses2"]
          newGuesses=""
          if currentGuesses == None or currentGuesses == "":
            newGuesses = guess
          else:
            newGuesses = currentGuesses+","+guess


          db2=SQL("sqlite:///duels.db")
          results=db2.execute("SELECT * FROM duels WHERE status = :status AND player1 = :name OR status = :status AND player2 = :name", status="accepted and playing", name=session.get("name"))

          if len(results) < 1:
            return redirect("/mainduel")

          if results[0]["player1"] == session.get("name"):
            db=SQL("sqlite:///duels.db")
            db.execute("UPDATE duels SET guesses1 = :guesses WHERE id = :id", guesses=newGuesses, id=results[0]["id"])
          else:
            db=SQL("sqlite:///duels.db")
            db.execute("UPDATE duels SET guesses2 = :guesses WHERE id = :id", guesses=newGuesses, id=results[0]["id"])
        
        return redirect("/mainduel")
      
    return render_template("sentence.html", sentence="Working on it!")

@app.route("/challengeduel", methods=["GET","POST"])
def challengeduel():
  if not session.get("name"):
    return redirect("/")
  else:
    username = request.form.get("username").strip().lower()
    db2 = SQL("sqlite:///duels.db")
    results=db2.execute("SELECT * FROM duels WHERE status = :status AND player1 = :name OR status = :status AND player2 = :name", status="accepted and playing", name=session.get("name"))
    if len(results) > 0:
      return render_template("sentence.html", sentence="You are already participating in a duel!")
    bet = request.form.get("amount")
    if "," in bet:
      bet=bet.replace(",", "")
    bet = float(bet)

    if bet < 1000:
      return render_template("sentence.html", sentence="The bet is less than the minimum bet!")

    myname = session.get("name")

    usersDB = SQL("sqlite:///users.db")
    
    player1 = usersDB.execute("SELECT * FROM users WHERE username = :name", name=myname)[0]
    player2 = usersDB.execute("SELECT * FROM users WHERE username = :name", name=username)[0]

    if player2["blocked"] == None:
      player2["blocked"] = []

    if player1["username"] in player2["blocked"]:
      return render_template("sentence.html", sentence="You have been blocked by this user so you may not request a duel!")

    if bet > player1["money"]:
      return render_template("sentence.html", sentence="You can't afford this bet!")
    elif bet > player2["money"]:
      return render_template("sentence.html", sentence="Your opponent can't afford this bet :(") 
 
    db = SQL("sqlite:///duels.db")
    db.execute("INSERT INTO duels (player1, player2, bet, guesses1, guesses2) VALUES (?,?,?,?,?)", myname, username, bet, "", "")
    results=db.execute("SELECT * FROM duels")[-1]

    duelID = results["id"]

    req="Duel with " + str(myname) + " for " + str(bet) + "$ (ID: " + str(duelID) + ")"
        
    db = SQL("sqlite:///requests.db")
    db.execute("INSERT INTO requests (sender, receiver, money) VALUES(?,?,?)", myname, username, req)
    
    return render_template("sentence.html", sentence="You have successfully challenged your opponent for a duel!")

@app.route("/duels", methods=["GET","POST"])
def duels():
  if not session.get("name"):
    return redirect("/")
  else:

    return render_template("sentence.html", sentence="working on it")

@app.route("/upgrade", methods=["GET","POST"])
def upgrades():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "POST":
      itemID = int(request.form.get("id"))
      db=SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))
      money = results[0]["money"]
      currentUpgrades = results[0]["upgrades"]
      itemsOwned = results[0]["itemsOwned"]
      if currentUpgrades == None:
        currentUpgrades = []
      elif "," not in currentUpgrades:
        currentUpgrades = [currentUpgrades]
      else:
        currentUpgrades = currentUpgrades.split(",")

      if itemsOwned == None:
          itemsOwned=[""]
      elif "," not in itemsOwned:
          itemsOwned=[itemsOwned]
      else:
          itemsOwned=itemsOwned.split(",")

      if str(itemID) not in itemsOwned:
        return render_template("sentence.html", sentence="You don't own this item!")

      howMany = [0,1,2,3,4,5,6,7,8,9,10]

      howMany[0] = currentUpgrades.count("1")
      howMany[1] = currentUpgrades.count("2")
      howMany[2] = currentUpgrades.count("3")
      howMany[3] = currentUpgrades.count("4")
      howMany[4] = currentUpgrades.count("5")
      howMany[5] = currentUpgrades.count("6")
      howMany[6] = currentUpgrades.count("7")
      howMany[7] = currentUpgrades.count("8")
      howMany[8] = currentUpgrades.count("9")
      howMany[9] = currentUpgrades.count("10")
      howMany[10] = currentUpgrades.count("11")

      if howMany[itemID-1] >= 10:
        return render_template("sentence.html", sentence="You already have upgraded this item ten times")

      currentUpgrades.append(itemID)

      upgradeStr=""

      for upgrade in currentUpgrades:
        upgradeStr += str(upgrade) + ","
      upgradeStr = upgradeStr[:-1]

      items = [
      {
        "name": "SAMmart PowerPuter",
        "price": 19999,
        "description": "This item will allow the player to get an additional 5$ increment on the 15$ increment"
    }
      ,
      {
        "name": "SAMmart Headphones",
        "price": 249,
        "description": "This item will allow the player to get 5$ additional for each mission, they complete"
      }
      ,
      {
        "name": "Rights to “Always gonna give you up!” by Mick Shastley",
        "price": 499999,
        "description": "after buying this item u have all the rights to rickroll anyone including Mick Shastley!"
      }
      ,
      {
      "name": "SAMmart x Darshbury = Darsbars",
        "price":10099,
        "description": "after buying dars bars, you can earn up to 10$ extra per mission!"
      }
      ,
       {
      "name": "SAMmart x Abhimart The World of Abhijayism book",
        "price":499999,
        "description": "now you can learn abhijaism and earn an extra 1000$ for per mission!!"
      },
     {
      "name": "SAMmart x Tunak Tun Jewelers necklace",
        "price":999999999,
        "description": " the legendary necklace will give you 100,000$ per mission!!"
      }
      ,
      {
      "name": "SAMmart x Sarveshwar's Suit Company = gold plated suit",
        "price":499999999,
        "description": "  by buying this, you can earn up to 10,000$ per mission"
      }
      ,
    {
      "name": "SAMsan Universe A22",
        "price":499,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      },
      {
      "name": "Malbo Suru",
        "price":299999,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      },
    {
      "name": "Sarrari Mustange",
        "price":499999,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      },
    {
      "name": "Meltsa Domel Z Flannel",
        "price":149999,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      }
    ]
      itemPrice=(items[itemID-1]["price"]/3)*1.13
      if itemPrice > money:
        return render_template("sentence.html", sentence="You don't have enough for this upgrade!")
      money = money - itemPrice

      db=SQL("sqlite:///users.db")
      db.execute("UPDATE users SET money = :money, upgrades = :upgrades WHERE username = :name", money=money, upgrades=upgradeStr, name=session.get("name"))
      
      return render_template("sentence.html", sentence="Item has been upgraded!")
    return render_template("sentence.html", sentence="WOrking on it")

@app.route("/missionpower", methods=["GET","POST"])
def missionpower():
  if not session.get("name"):
      return redirect("/")
  else:
        db=SQL("sqlite:///users.db")
        results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))
  
        db=SQL("sqlite:///users.db")
        results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))

        experience = results[0]["experience"]
        money = results[0]["money"]

        if experience == None or experience == "0":
          experience=0
        else:
          experience=int(experience)

        if money == None or money == "0":
          money=0
        else:
          money=int(money)

        moneyAdded=500+(15*experience)

        itemsOwned = results[0]["itemsOwned"]
        currentDebt = results[0]["currentDebt"]
        currentUpgrades = results[0]["upgrades"]
        if currentUpgrades == None:
            currentUpgrades = []
        elif "," not in currentUpgrades:
            currentUpgrades = [currentUpgrades]
        else:
            currentUpgrades = currentUpgrades.split(",")
    
        howMany = [0,1,2,3,4,5,6,7,8,9,10]
    
        howMany[0] = currentUpgrades.count("1")
        howMany[1] = currentUpgrades.count("2")
        howMany[2] = currentUpgrades.count("3")
        howMany[3] = currentUpgrades.count("4")
        howMany[4] = currentUpgrades.count("5")
        howMany[5] = currentUpgrades.count("6")
        howMany[6] = currentUpgrades.count("7")
        howMany[7] = currentUpgrades.count("8")
        howMany[8] = currentUpgrades.count("9")
        howMany[9] = currentUpgrades.count("10")
        howMany[10] = currentUpgrades.count("11")

        if currentDebt == None:
          currentDebt = 0
        else:
          currentDebt = currentDebt * 100.5

        if itemsOwned == None:
          itemsOwned=[""]
        elif "," not in itemsOwned:
          itemsOwned=[itemsOwned]
        else:
          itemsOwned=itemsOwned.split(",")

        experience=experience+1

        if "1" in itemsOwned:
          moneyAdded+=(5*(0.5*howMany[0])+1)*experience
          
        if "2" in itemsOwned: 
          moneyAdded+=5*(0.5*howMany[1])+1
        if "4" in itemsOwned: 
          moneyAdded+=10*(0.5*howMany[3])+1
        if "5" in itemsOwned: 
          moneyAdded+=1000*(0.5*howMany[4])+1
        if "6" in itemsOwned: 
          moneyAdded+=100000*(0.5*howMany[5])+1
        if "7" in itemsOwned: 
          moneyAdded+=10000*(0.5*howMany[6])+1
        if "9" in itemsOwned: 
          moneyAdded+=900*(0.5*howMany[8])+1
        if "10" in itemsOwned: 
          moneyAdded+=1000*(0.5*howMany[9])+1
        if "11" in itemsOwned: 
          moneyAdded+=350
          experience=experience+2
        if "100" in itemsOwned: 
          moneyAdded+=400000
        if "101" in itemsOwned: 
          moneyAdded+=10000
        if "201" in itemsOwned: 
          moneyAdded+=200
        if "202" in itemsOwned: 
          moneyAdded+=400
        if "203" in itemsOwned: 
          moneyAdded+=700
        if "204" in itemsOwned: 
          moneyAdded+=900
        if "205" in itemsOwned: 
          moneyAdded+=999
        if "206" in itemsOwned: 
          moneyAdded+=1000
        if "207" in itemsOwned: 
          moneyAdded+=1400
        if "208" in itemsOwned: 
          moneyAdded+=1600
        if "209" in itemsOwned: 
          moneyAdded+=1900
        if "210" in itemsOwned: 
          moneyAdded+=2000

        normalMoneyAdded = moneyAdded

        percentMoney = moneyAdded * 0.4

        startingDebt = currentDebt

        if currentDebt > 0:
          if currentDebt < percentMoney:
            moneyAdded = moneyAdded - currentDebt
            moneyDeducted = currentDebt
            currentDebt = 0    
          else:
            moneyAdded = moneyAdded - percentMoney
            moneyDeducted = percentMoney
            currentDebt = currentDebt - percentMoney

        money=money-moneyAdded
        db = SQL("sqlite:///users.db")
        db.execute("UPDATE users SET money = :money WHERE username = :name", money=money, name=session.get("name"))
        currentCode=results[0]["currentCode"]
  
        correctPlaceLetters=[]
        wrongPlaceLetters=[]
  
        guessesList = results[0]["guesses"]
  
        if guessesList!=None:
          if "," in guessesList:
            guessesList=guessesList.split(",")
          else:
            guessesList=[guessesList]
  
        print(guessesList)
  
        if guessesList != None:
          for guess in guessesList:
            for count, i in enumerate(guess):
              if i == currentCode[count] and i not in correctPlaceLetters:
                print(count, i)
                correctPlaceLetters.append(i)
              elif i in currentCode and i not in wrongPlaceLetters:
                wrongPlaceLetters.append(i)
        trueWrongLetters=[]
        for i in wrongPlaceLetters:
          if i not in correctPlaceLetters and i != currentCode[0] and i != currentCode[-1]:
            trueWrongLetters.append(i)
  
  
        for i in currentCode:
          if i not in trueWrongLetters and i not in correctPlaceLetters and i != currentCode[0] and i != currentCode[-1]:
            theOne = i
        db=SQL("sqlite:///users.db")
        results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))
        currentGuesses=results[0]["guesses"]
        newGuesses=""
        if currentGuesses == None or currentGuesses == "":
            newGuesses = theOne+"_____"
        else:
            newGuesses = currentGuesses+","+theOne+"_____"
    
        db=SQL("sqlite:///users.db")
        db.execute("UPDATE users SET guesses = :guesses WHERE username = :name", guesses=newGuesses, name=session.get("name"))
            
        return redirect("/dotask")

@app.route("/awards", methods=["GET","POST"])
def awards():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      db=SQL("sqlite:///users.db")
    
      results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))
  
      itemsOwned = results[0]["itemsOwned"]

      experience = results[0]['experience']
  
      if itemsOwned == None:
        itemsOwned=[]
      elif "," not in itemsOwned:
        itemsOwned=[itemsOwned]
      else:
        itemsOwned = itemsOwned.split(",")
      return render_template("awards.html", itemsOwned=itemsOwned, experience=experience)
    elif request.method == "POST":
      itemNo = request.form.get("id").strip()
      db = SQL("sqlite:///users.db")
      results = db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))
  
      itemsOwned = results[0]["itemsOwned"]
      if itemsOwned == None:
        itemsOwned = str(itemNo)
      else:
        itemsOwned += ","+str(itemNo)

      db.execute("UPDATE users SET itemsOwned = :itemsOwned WHERE username = :name", itemsOwned=itemsOwned, name=session.get("name"))

      return render_template("sentence.html", sentence="You have successfully redeemed the award!")
      
    return render_template("sentence.html", sentence="working on it")

@app.route("/requestitem", methods=["GET","POST"])
def requestitem():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      return render_template("lenditems.html", link="req")
    elif request.method == "POST":
      user = session.get("name")
      username = request.form.get("username").strip().lower()

      db=SQL("sqlite:///users.db")
      player2=db.execute("SELECT * FROM users WHERE username = :name", name=username)[0]

      if player2["blocked"] == None:
        player2["blocked"] = []

      if user in player2["blocked"]:
        return render_template("sentence.html", sentence="You have been blocked by this user so you may not request a duel!")
      
      itemID = request.form.get("item").strip()

      req="Item: " + str(itemID)
        
      db = SQL("sqlite:///requests.db")
      db.execute("INSERT INTO requests (sender, receiver, money) VALUES(?,?,?)", user, username, req)
  
      return render_template("sentence.html", sentence="You have requested the item successfully!")
  return render_template("sentence.html", sentence="working on it")
      

@app.route("/payloan", methods=["GET","POST"])
def payloan():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "POST":
      amount = request.form.get("amount")
      if "," in amount:
        amount=amount.replace(",", "")
      username = session.get("name")

      db = SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=username)

      currentDebt = results[0]["currentDebt"]
      money = results[0]["money"]

      if currentDebt == None or int(currentDebt) == 0:
        return render_template("sentence.html", sentence="You have no debt to pay off!")

      amount = int(amount)

      if amount > money:
        return render_template("sentence.html", sentence="You don't that much money to pay off the loan!")


      if amount < 2000:
        return render_template("sentence.html", sentence="The minimum amont for additional payments is 2,000$")

      currentDebt = int(currentDebt)
      moneyDeducted = amount
      if currentDebt < amount:
        moneyDeducted = currentDebt
        currentDebt = 0 
      else:
        currentDebt = currentDebt - amount
      money = money - moneyDeducted

      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET money = :money, currentDebt = :currentDebt WHERE username = :name", money=money, currentDebt=currentDebt, name=username)

      moneyDeducted="{:.2f}".format(moneyDeducted)

      if len(str(moneyDeducted)) > 6:
        number=str(moneyDeducted)[:-3]
        print("number:"+str(number))
        
        a=0
        numstring = ""
        number = number[::-1]
        for i in number:
          a+=1
          if a % 3 == 0:
            numstring += i +","
          else:
            numstring += i
        
        numstring = numstring[::-1]
        
        if numstring[0] == ",":
          numstring = numstring[1:]
    
        numstring = numstring+(str(moneyDeducted)[-3:])
    
        print(numstring)
    
        moneyDeducted=(numstring)
      currentDebt="{:.2f}".format(currentDebt)
      if len(str(currentDebt)) > 6:
        number=str(currentDebt)[:-3]
        print(number)
        
        a=0
        numstring = ""
        number = number[::-1]
        for i in number:
          a+=1
          if a % 3 == 0:
            numstring += i +","
          else:
            numstring += i
        
        numstring = numstring[::-1]
        
        if numstring[0] == ",":
          numstring = numstring[1:]
    
        numstring = numstring+(str(currentDebt)[-3:])
    
        print(numstring)
    
        currentDebt=(numstring)

      sentence = "Your account has been deducted " + str(moneyDeducted) + "$ to pay off your loan, you have " + str(currentDebt) + "$ left to pay off"

      return render_template("sentence.html", sentence=sentence)

    return render_template("sentence.html", sentence="Working on it!")
  
@app.route("/bank", methods=["GET","POST"])
def bank():
  if not session.get("name"): 
    return redirect("/")
  else:
    print(request.method)
    if request.method == "GET":
      username = session.get("name")
      db = SQL("sqlite:///users.db")
      results = db.execute("SELECT * FROM users WHERE username = :username", username=username)
  
      money = "{:.2f}".format(results[0]["money"])
      if results[0]["currentDebt"] == None:
        results[0]["currentDebt"] = 0
      currentDebt = "{:.2f}".format(results[0]["currentDebt"])
      print(currentDebt)
  
      experience = results[0]["experience"]
      print(experience)
  
      if int(experience) == 0:
        return render_template("sentence.html", sentence="You cannot get approved by the bank for a loan!")

      if len(str(money)) > 6:
        number=str(money)[:-3]
        print(number)
        
        a=0
        numstring = ""
        number = number[::-1]
        for i in number:
          a+=1
          if a % 3 == 0:
            numstring += i +","
          else:
            numstring += i
        
        numstring = numstring[::-1]
        
        if numstring[0] == ",":
          numstring = numstring[1:]
    
        numstring = numstring+(str(money)[-3:])
    
        print(numstring)
    
        money=(numstring)

      if len(str(currentDebt)) > 6:
        number=str(currentDebt)[:-3]
        print(number)
        
        a=0
        numstring = ""
        number = number[::-1]
        for i in number:
          a+=1
          if a % 3 == 0:
            numstring += i +","
          else:
            numstring += i
        
        numstring = numstring[::-1]
        
        if numstring[0] == ",":
          numstring = numstring[1:]
    
        numstring = numstring+(str(currentDebt)[-3:])
    
        print(numstring)
    
        currentDebt=(numstring)
  
      amountAvailable = int(experience) * 5000
  
      amountAvailable = int(experience) * 5000

      amountAvailable = "{:.2f}".format(amountAvailable)
      if len(str(amountAvailable)) > 6:
          number=str(amountAvailable)[:-3]
          print(number)
          
          a=0
          numstring = ""
          number = number[::-1]
          for i in number:
            a+=1
            if a % 3 == 0:
              numstring += i +","
            else:
              numstring += i
          
          numstring = numstring[::-1]
          
          if numstring[0] == ",":
            numstring = numstring[1:]
      
          numstring = numstring
      
          print(numstring)
      
          amountAvailable=(numstring)+"$"
  
      return render_template("bank.html", money=money, experience=experience, amountAvailable=amountAvailable, currentDebt=currentDebt)

    elif request.method == "POST":
      amount = request.form.get("amount")
      if "," in amount:
        amount=amount.replace(",", "")
      username = session.get("name")
      db = SQL("sqlite:///users.db")
      results = db.execute("SELECT * FROM users WHERE username = :username", username=username)

      money = int(results[0]["money"])
  
      formattedMoney = "{:.2f}".format(results[0]["money"])
  
      experience = results[0]["experience"]

      amountAvailable = int(experience) * 5000

      if results[0]["currentDebt"] == None:
        results[0]["currentDebt"] = 0

      if results[0]["currentDebt"] > 0 :
        return render_template("sentence.html", sentence="You already have an outstanding loan!")
  
      if int(experience) == 0:
        return render_template("sentence.html", sentence="You cannot get approved by the bank for a loan!")

      if int(amount) < 2000:
        return render_template("sentence.html", sentence="The amount you requested a loan for is to low!")

      if int(amount) > amountAvailable:
        return render_template("sentence.html", sentence="This loan is too large for your experience, hence the loan has been rejected!")

      money = money + int(amount)
      currentDebt = int(amount)

      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET money = :money, currentDebt = :currentDebt WHERE username = :name", money=money, currentDebt=currentDebt, name=username)

      return render_template("sentence.html", sentence="Your loan has been approved!")
      
    return render_template("sentence.html", sentence="Working on it...")

@app.route("/sellitem",methods=["GET","POST"])
def sellitems():
  if not session.get("name"):
    return redirect("/")
  else:
    id = request.form.get("id")

    items = [
      {
        "name": "SAMmart PowerPuter",
        "price": 19999,
        "description": "This item will allow the player to get an additional 5$ increment on the 15$ increment"
    }
      ,
      {
        "name": "SAMmart Headphones",
        "price": 249,
        "description": "This item will allow the player to get 5$ additional for each mission, they complete"
      }
      ,
      {
        "name": "Rights to “Always gonna give you up!” by Mick Shastley",
        "price": 499999,
        "description": "after buying this item u have all the rights to rickroll anyone including Mick Shastley!"
      }
      ,
      {
      "name": "SAMmart x Darshbury = Darsbars",
        "price":10099,
        "description": "after buying dars bars, you can earn up to 10$ extra per mission!"
      }
      ,
       {
      "name": "SAMmart x Abhimart The World of Abhijayism book",
        "price":499999,
        "description": "now you can learn abhijaism and earn an extra 1000$ for per mission!!"
      },
     {
      "name": "SAMmart x Tunak Tun Jewelers necklace",
        "price":999999999,
        "description": " the legendary necklace will give you 100,000$ per mission!!"
      }
      ,
      {
      "name": "SAMmart x Sarveshwar's Suit Company = gold plated suit",
        "price":499999999,
        "description": "  by buying this, you can earn up to 10,000$ per mission"
      }
      ,
    {
      "name": "SAMsan Universe A22",
        "price":499,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      },
      {
      "name": "Malbo Suru",
        "price":299999,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      },
    {
      "name": "Sarrari Mustange",
        "price":499999,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      },
    {
      "name": "Meltsa Domel Z Flannel",
        "price":149999,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      }
    ]

    item = items[int(id)-1]

    itemPrice = item["price"]

    db = SQL("sqlite:///users.db")
    results = db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))

    userMoney = results[0]["money"]

    itemsOwned = results[0]["itemsOwned"]
    if itemsOwned == None or itemsOwned == "":
      return render_template("sentencee.html", sentence="You do not have the product yet!")
    elif "," not in itemsOwned:
      itemsOwned=[itemsOwned]
    else:
      itemsOwned = itemsOwned.split(",")

    if id not in itemsOwned:
      return render_template("sentence.html", sentence="You don't have this item yet!")

    itemsOwned.remove(id)

    newItems=""

    for item in itemsOwned:
      newItems += item + ","
    newItems=newItems[:-1]

    itemPrice = int(itemPrice) * 0.85
    userMoney = int(userMoney) + int(itemPrice)

    db = SQL("sqlite:///users.db")
    db.execute("UPDATE users SET itemsOwned = :newItems, money = :userMoney WHERE username = :name", newItems=newItems, userMoney=userMoney, name=session.get("name"))

    fakeAmount=str("{:.2f}".format(itemPrice))  
    if len(str(fakeAmount)) > 6:
          number=str(fakeAmount)[:-3]
          print(number)
          
          a=0
          numstring = ""
          number = number[::-1]
          for i in number:
            a+=1
            if a % 3 == 0:
              numstring += i +","
            else:
              numstring += i
          
          numstring = numstring[::-1]
          
          if numstring[0] == ",":
            numstring = numstring[1:]
          fakeAmount = numstring+(str(fakeAmount)[-3:])
      
          print(numstring)
      
          itemPrice=(numstring)
      
    fakeAmount=str("{:.2f}".format(userMoney))  
    if len(str(fakeAmount)) > 6:
          number=str(fakeAmount)[:-3]
          print(number)
          
          a=0
          numstring = ""
          number = number[::-1]
          for i in number:
            a+=1
            if a % 3 == 0:
              numstring += i +","
            else:
              numstring += i
          
          numstring = numstring[::-1]
          
          if numstring[0] == ",":
            numstring = numstring[1:]
          fakeAmount = numstring+(str(fakeAmount)[-3:])
      
          print(numstring)
      
          userMoney=(numstring)

    sentence="You have sold the item! " + str(itemPrice) + "$ has been added to your account, this brings your balance to " + str(userMoney) + "$"
    
    return render_template("sentence.html", sentence=sentence)

@app.route("/trophies", methods=["GET","POST"])
def trophies():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      return render_template("trophies.html")
      
    return render_template("sentence.html", sentence="We're working on it!")
  
@app.route("/allusers")
def see_names():
  db = SQL("sqlite:///users.db")
  results=db.execute("SELECT * FROM users")
  for player in results:
    player["money"] = "{:.2f}".format(float(player["money"]))
    if len(str(player["money"])) > 6:
          number=str(player["money"])[:-3]
          print(number)
          
          a=0
          numstring = ""
          number = number[::-1]
          for i in number:
            a+=1
            if a % 3 == 0:
              numstring += i +","
            else:
              numstring += i
          
          numstring = numstring[::-1]
          
          if numstring[0] == ",":
            numstring = numstring[1:]
          player["money"] = numstring+(str(player["money"])[-3:])
    
  return render_template("users.html", results=results)

@app.route("/powerup", methods=["GET","POST"])
def powerups():
  if not session.get("name"):
    return redirect("/")
  else:
      db = SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=username)
      word=results[0]["currentCode"]
      letter = random.random(word)
      db=SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))

      currentCode=results[0]["currentCode"]

      correctPlaceLetters=[]
      wrongPlaceLetters=[]

      guessesList = results[0]["guesses"]

      if guessesList!=None:
        if "," in guessesList:
          guessesList=guessesList.split(",")
        else:
          guessesList=[guessesList]

      print(guessesList)

      if guessesList != None:
        for guess in guessesList:
          for count, i in enumerate(guess):
            if i == currentCode[count] and i not in correctPlaceLetters:
              print(count, i)
              correctPlaceLetters.append(i)
            elif i in currentCode and i not in wrongPlaceLetters:
              wrongPlaceLetters.append(i)
      trueWrongLetters=[]
      for i in wrongPlaceLetters:
        if i not in correctPlaceLetters and i != currentCode[0] and i != currentCode[-1]:
          trueWrongLetters.append(i)

      licp=""

      for i in correctPlaceLetters:
        licp += i + ", "

      licp=licp[:-2]

      liwp=""

      for i in trueWrongLetters:
        liwp += i + ", "

      liwp=liwp[:-2]
        
      task=results[0]["currentTask"]

      wordform=""
  alreadyHas = ""
  
  return render_template("sentence.html", sentence=sentence)

@app.route("/")
def index():
  if not session.get("name"):
    return render_template("index.html")
    
  else:
    username = session.get("name")
    db = SQL("sqlite:///users.db")
    results = db.execute("SELECT * FROM users WHERE username = :username", username=username)

    money = "{:.2f}".format(results[0]["money"])

    experience = results[0]["experience"]

    if len(str(money)) > 6:
      number=str(money)[:-3]
      print(number)
      
      a=0
      numstring = ""
      number = number[::-1]
      for i in number:
        a+=1
        if a % 3 == 0:
          numstring += i +","
        else:
          numstring += i
      
      numstring = numstring[::-1]
      
      if numstring[0] == ",":
        numstring = numstring[1:]
  
      numstring = numstring+(str(money)[-3:])
  
      print(numstring)
  
      money=(numstring)

      db2 = SQL("sqlite:///duels.db")
      results=db2.execute("SELECT * FROM duels WHERE status = :status AND player1 = :name OR status = :status AND player2 = :name", status="accepted and playing", name=session.get("name"))

      if len(results) == 0:
        return render_template("menu.html", username=username, money=money, experience=experience)
      else:
        player1 = results[0]["player1"]
        player2 = results[0]["player2"]
        print(player1)
        print(player2)
        return render_template("menu.html", username=username, money=money, experience=experience, player1=player1, player2=player2)

    return render_template("menu.html", username=username, money=money, experience=experience)

@app.route("/money")
def money():
  return redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

@app.route("/requestmoney", methods=["GET", "POST"])
def requestmoney():
  if not session.get("name"):
    return redirect("/")
  else:
    user = session.get("name")
    username = request.form.get("username").strip().lower()
    amount = request.form.get("amount")
    db=SQL("sqlite:///users.db")
    player2=db.execute("SELECT * FROM users WHERE username = :name", name=username)[0]

    if player2["blocked"] == None:
      player2["blocked"] = []

    if user in player2["blocked"]:
        return render_template("sentence.html", sentence="You have been blocked by this user so you may not request a duel!")
    if "," in amount:
        amount=amount.replace(",", "")
    amount = float(amount)
    if amount <= 1 or amount > 1000000000:
      return render_template("sentence.html", sentence="Amount requested is outside the limits!.")
      
    db = SQL("sqlite:///requests.db")
    db.execute("INSERT INTO requests (sender, receiver, money) VALUES(?,?,?)", user, username, amount)

    return render_template("sentence.html", sentence="You have request money successfully!")

@app.route("/decline", methods=["GET","POST"])
def decline():
  if not session.get("name"):
    return redirect("/")
  else:
    id=request.form.get("id")
    
    db1 = SQL("sqlite:///requests.db")

    db1.execute("UPDATE requests SET status = :status WHERE id = :id", status="declined", id=id)

    return render_template("sentence.html", sentence="You have declined the request!")

@app.route("/accept", methods=["GET", "POST"])
def accept():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "POST":
      id=request.form.get("id")
      
      db1 = SQL("sqlite:///requests.db")
      request1=db1.execute("SELECT * FROM requests WHERE id = :id", id=id)
      db1.execute("UPDATE requests SET status = :status WHERE id = :id", status="accepted", id=id)

      username = request1[0]["receiver"]
      sendItemTo = request1[0]["sender"] 

      #req="Duel with " + str(myname) + " for " + str(bet) + "$ (ID: " + str(duelID) + ")"

      if "Duel" in request1[0]["money"]:
        id = int(request1[0]["money"].split("(ID: ")[1][:-1])
        print(id)
        db2 = SQL("sqlite:///duels.db")
        post1=db2.execute("SELECT * FROM duels WHERE id = :id", id=id)
        results=db2.execute("SELECT * FROM duels WHERE status = :status AND player1 = :name OR status = :status AND player2 = :name", status="accepted and playing", name=session.get("name"))

        if len(results) > 0:
          return render_template("sentence.html", sentence="You are already in a duel, quit that one before starting another one!")

        db2 = SQL("sqlite:///duels.db")
        db2.execute("UPDATE duels SET status = :status WHERE id = :id", status="accepted and playing", id=id)

        print("accepted")
    
        return redirect("/mainduel")

      if "Item" in request1[0]["money"]:
        itemID = request1[0]["money"].split(": ")[1]
        db=SQL("sqlite:///users.db")
        results = db.execute("SELECT * FROM users WHERE username = :name", name=username)
  
        sender = results[0]
  
        if not itemID.isdigit():
          return redirect("/itemids")
  
        userItem = sender["itemsOwned"]
  
        if userItem == None or userItem == "":
          return render_template("sentence.html", sentence="You don't have items to transfer!")
  
        if "," not in userItem:
          items = [userItem]
        else:
          items=userItem.split(",")
  
        if itemID not in items:
          return render_template("sentence.html", sentence="You don't have the item you are trying to transfer!")
  
        db = SQL("sqlite:///users.db")
        receiver = db.execute("SELECT * FROM users WHERE username = :name", name=sendItemTo)[0]
        receiverItems=receiver["itemsOwned"]
  
        if receiverItems == None:
          receiverItems = str(itemID)
        else:
          receiverItems += ","+str(itemID)
  
        items.remove(str(itemID))
        newItems=""
        for i in items:
          newItems += i + ","
        newitems=newItems[:-1]
  
        db.execute("UPDATE users SET itemsOwned = :itemsOwned WHERE username = :name", itemsOwned=receiverItems, name=sendItemTo)
  
        db = SQL("sqlite:///users.db")
        db.execute("UPDATE users SET itemsOwned = :itemsOwned WHERE username = :name", itemsOwned=newItems, name=username)
        
        return render_template("sentence.html", sentence="You have successfully sent the item!")
      
      db = SQL("sqlite:///users.db")
      user1 = db.execute("SELECT * FROM users WHERE username = :id", id=request1[0]["receiver"])[0]["money"]
      
      user2 = db.execute("SELECT * FROM users WHERE username = :id", id=request1[0]["sender"])[0]["money"]
  
      if user1 < request1[0]["money"]:
        return render_template("sentence.html", sentence="You have less than the amount of money requested!")
      user1=user1-request1[0]["money"]
      user2=user2+request1[0]["money"]
  
      db = SQL("sqlite:///users.db")
  
      db.execute("UPDATE users SET money = :money WHERE username = :id", money=user1, id=request1[0]["receiver"])
      db.execute("UPDATE users SET money = :money WHERE username = :id", money=user2, id=request1[0]["sender"])
  
      return render_template("sentence.html", sentence="You have accepted the request for money!")

@app.route("/inbox", methods=["GET", "POST"])
def checkinbox():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      db = SQL("sqlite:///requests.db")
      results=db.execute("SELECT * FROM requests WHERE receiver = :receiver AND status IS NULL", receiver=session.get("name"))

      items = [
      {
        "name": "SAMmart PowerPuter",
        "price": 19999,
        "description": "This item will allow the player to get an additional 5$ increment on the 15$ increment"
    }
      ,
      {
        "name": "SAMmart Headphones",
        "price": 249,
        "description": "This item will allow the player to get 5$ additional for each mission, they complete"
      }
      ,
      {
        "name": "Rights to “Always gonna give you up!” by Mick Shastley",
        "price": 499999,
        "description": "after buying this item u have all the rights to rickroll anyone including Mick Shastley!"
      }
      ,
      {
      "name": "SAMmart x Darshbury = Darsbars",
        "price":10099,
        "description": "after buying dars bars, you can earn up to 10$ extra per mission!"
      }
      ,
       {
      "name": "SAMmart x Abhimart The World of Abhijayism book",
        "price":499999,
        "description": "now you can learn abhijaism and earn an extra 1000$ for per mission!!"
      },
     {
      "name": "SAMmart x Tunak Tun Jewelers necklace",
        "price":999999999,
        "description": " the legendary necklace will give you 100,000$ per mission!!"
      }
      ,
      {
      "name": "SAMmart x Sarveshwar's Suit Company = gold plated suit",
        "price":499999999,
        "description": "  by buying this, you can earn up to 10,000$ per mission"
      }
      ,
    {
      "name": "SAMsan Universe A22",
        "price":499,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      },
      {
      "name": "Malbo Suru",
        "price":299999,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      },
    {
      "name": "Sarrari Mustange",
        "price":499999,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      },
    {
      "name": "Meltsa Domel Z Flannel",
        "price":149999,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      }
    ]
     
      for i in results:
        if type(i["money"]) == type("str"):
          if "Item" in i["money"]:
            itemNo = i["money"].split(": ")[1]
            item = items[int(itemNo)-1]
            i["money"] = item["name"]
          
      pending=db.execute("SELECT * FROM requests WHERE sender = :receiver AND status IS NULL", receiver=session.get("name"))
      
      accepted=db.execute("SELECT * FROM requests WHERE sender = :receiver AND status = :status", receiver=session.get("name"), status="accepted")

      db2 = SQL("sqlite:///duels.db")
      pendingDuels=db2.execute("SELECT * FROM duels WHERE player2 = :receiver AND status IS NULL", receiver=session.get("name"))

      for i in pending:
        if type(i["money"]) == type("str"):
          if "Item" in i["money"]:
            itemNo = i["money"].split(": ")[1]
            item = items[int(itemNo)-1]
            i["money"] = item["name"]
      for i in accepted:
        if type(i["money"]) == type("str"):
          if "Item" in i["money"]:
            itemNo = i["money"].split(": ")[1]
            item = items[int(itemNo)-1]
            i["money"] = item["name"]
      
      return render_template("inbox.html", requests=results, pending=pending, accepted=accepted, pendingDuels=pendingDuels)

@app.route("/gamble", methods=["GET", "POST"])
def gamble():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      return render_template("gamble.html")
    elif request.method == "POST":
      amount=request.form.get("amount").strip()
      if "," in amount:
        amount=amount.replace(",", "")
      amount = float(amount)
      pick=request.form.get("pick").strip()

      if amount == 0 or amount < 100:
        return render_template("sentence.html", sentence="You have not bet enough!")

      randomNumber = str(random.randint(1, 4))
      jackpotNumber = random.randint(1, 250)

      db=SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))

      money = results[0]["money"]

      if amount > money:
        return render_template("sentence.html", sentence="You have less than the amount you gambled!")

      if pick != randomNumber:
        
        fakeAmount=str("{:.2f}".format(amount))
        if len(str(fakeAmount)) > 6:
          number=str(fakeAmount)[:-3]
          print(number)
          
          a=0
          numstring = ""
          number = number[::-1]
          for i in number:
            a+=1
            if a % 3 == 0:
              numstring += i +","
            else:
              numstring += i
          
          numstring = numstring[::-1]
          
          if numstring[0] == ",":
            numstring = numstring[1:]
          fakeAmount = numstring+(str(fakeAmount)[-3:])
      
          print(numstring)
      
          fakeAmount=(numstring)
        sentence = "You bet " + fakeAmount + "$ on " + pick + " and it came out " + randomNumber + ", you lost " + fakeAmount + "$ on this gamble!"
        money=money-amount
        moneyEach = amount/4
      else:
        fakeAmount=str("{:.2f}".format(amount))
        if len(str(fakeAmount)) > 6:
          number=str(fakeAmount)[:-3]
          print(number)
          
          a=0
          numstring = ""
          number = number[::-1]
          for i in number:
            a+=1
            if a % 3 == 0:
              numstring += i +","
            else:
              numstring += i
          
          numstring = numstring[::-1]
          
          if numstring[0] == ",":
            numstring = numstring[1:]
          fakeAmount = numstring+(str(fakeAmount)[-3:])
      
          print(numstring)
      
          fakeAmount=(numstring)
        sentence = "You bet " + fakeAmount + "$ on " + pick + " and it came out " + randomNumber + ", you won  " + fakeAmount + "$ on this gamble!"
        money=money+amount
        moneyEach = 0

      if jackpotNumber == 1:
        money+=10000000
        sentence+=" You won the jackpot! 10 million dollars has been added to your account!"
        
      db.execute("UPDATE users SET money = :money WHERE username = :name", money=money, name=session.get("name"))

      sarveshwarMoney = 0

      db = SQL("sqlite:///users.db")
      """

      sarveshwarMoney = db.execute("SELECT * FROM users WHERE username = :name", name="sarveshwar")[0]["money"] + moneyEach
      imagine_dragonsMoney = db.execute("SELECT * FROM users WHERE username = :name", name="imagine_dragons")[0]["money"] + moneyEach
      liamMoney = db.execute("SELECT * FROM users WHERE username = :name", name="lemsa")[0]["money"] + moneyEach
      abhijayMoney = db.execute("SELECT * FROM users WHERE username = :name", name="elon musk")[0]["money"] + moneyEach

      db = SQL("sqlite:///users.db")

      db.execute("UPDATE users SET money = :money WHERE username = :name", money=sarveshwarMoney, name="sarveshwar")

      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET money = :money WHERE username = :name", money=liamMoney, name="lemsa")
   
      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET money = :money WHERE username = :name", money=imagine_dragonsMoney, name="imagine_dragons")
      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET money = :money WHERE username = :name", money=abhijayMoney, name="elon musk")"""

      return render_template("sentence.html", sentence=sentence)
      

@app.route("/viewitems")
def viewitems():
  if not session.get("name"):
    return redirect("/")
  else:
    db = SQL("sqlite:///users.db")
    results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))
    itemsOwned = results[0]["itemsOwned"]
    if itemsOwned == None:
          itemsOwned=[""]
    elif "," not in itemsOwned:
          itemsOwned=[itemsOwned]
    else:
          itemsOwned=itemsOwned.split(",")
    currentUpgrades = results[0]["upgrades"]
    if currentUpgrades == None:
        currentUpgrades = []
    elif "," not in currentUpgrades:
        currentUpgrades = [currentUpgrades]
    else:
        currentUpgrades = currentUpgrades.split(",")

    howMany = [0,1,2,3,4,5,6,7,8,9,10]

    howMany[0] = currentUpgrades.count("1")
    howMany[1] = currentUpgrades.count("2")
    howMany[2] = currentUpgrades.count("3")
    howMany[3] = currentUpgrades.count("4")
    howMany[4] = currentUpgrades.count("5")
    howMany[5] = currentUpgrades.count("6")
    howMany[6] = currentUpgrades.count("7")
    howMany[7] = currentUpgrades.count("8")
    howMany[8] = currentUpgrades.count("9")
    howMany[9] = currentUpgrades.count("10")
    howMany[10] = currentUpgrades.count("11")
    
    return render_template("view.html", itemsOwned=itemsOwned, howMany=howMany)
  
@app.route("/store", methods=["GET", "POST"])
def store():
  if not session.get("name"):
    return redirect("/")
  if request.method == "GET":
    db=SQL("sqlite:///users.db")
    
    results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))

    itemsOwned = results[0]["itemsOwned"]

    if itemsOwned == None:
      itemsOwned=[]
    elif "," not in itemsOwned:
      itemsOwned=[itemsOwned]
    else:
      itemsOwned = itemsOwned.split(",")
    
    return render_template("store.html", itemsOwned=itemsOwned)
  elif request.method == "POST":
    item=request.form.get("id")
    itemNo=item
    print(item)
    items = [
      {
        "name": "SAMmart PowerPuter",
        "price": 19999,
        "description": "This item will allow the player to get an additional 5$ increment on the 15$ increment"
    }
      ,
      {
        "name": "SAMmart Headphones",
        "price": 249,
        "description": "This item will allow the player to get 5$ additional for each mission, they complete"
      }
      ,
      {
        "name": "Rights to “Always gonna give you up!” by Mick Shastley",
        "price": 499999,
        "description": "after buying this item u have all the rights to rickroll anyone including Mick Shastley!"
      }
      ,
      {
      "name": "SAMmart x Darshbury = Darsbars",
        "price":10099,
        "description": "after buying dars bars, you can earn up to 10$ extra per mission!"
      }
      ,
       {
      "name": "SAMmart x Abhimart The World of Abhijayism book",
        "price":499999,
        "description": "now you can learn abhijaism and earn an extra 1000$ for per mission!!"
      },
     {
      "name": "SAMmart x Tunak Tun Jewelers necklace",
        "price":999999999,
        "description": " the legendary necklace will give you 100,000$ per mission!!"
      }
      ,
      {
      "name": "SAMmart x Sarveshwar's Suit Company = gold plated suit",
        "price":499999999,
        "description": "  by buying this, you can earn up to 10,000$ per mission"
      }
      ,
    {
      "name": "SAMsan Universe A22",
        "price":499,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      },
      {
      "name": "Malbo Suru",
        "price":299999,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      },
    {
      "name": "Sarrari Mustange",
        "price":499999,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      },
    {
      "name": "Meltsa Domel Z Flannel",
        "price":149999,
        "description": " this a cheap ip*one 13p*o MAX, enjoy!!"
      }
    ]

    item = items[int(item)-1]

    itemPrice = item["price"]
    tax = item["price"]*0.13
    totalPrice = itemPrice + tax


    db = SQL("sqlite:///users.db")
    results = db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))

    userMoney = results[0]["money"]

    if userMoney < totalPrice:
      return render_template("sentence.html",sentence="You cannot afford this item!")

    newUserMoney = userMoney - totalPrice
    fakenewUserMoney = str(newUserMoney)

    itemsOwned = results[0]["itemsOwned"]
    if itemsOwned == None:
      itemsOwned = str(itemNo)
    else:
      itemsOwned += ","+str(itemNo)
      fakeAmount=str("{:.2f}".format(itemPrice))  
      if len(str(fakeAmount)) > 6:
          number=str(fakeAmount)[:-3]
          print(number)
          
          a=0
          numstring = ""
          number = number[::-1]
          for i in number:
            a+=1
            if a % 3 == 0:
              numstring += i +","
            else:
              numstring += i
          
          numstring = numstring[::-1]
          
          if numstring[0] == ",":
            numstring = numstring[1:]
          fakeAmount = numstring+(str(fakeAmount)[-3:])
      
          print(numstring)
      
          itemPrice=(numstring)
      fakeAmount=str("{:.2f}".format(tax))  
      if len(str(fakeAmount)) > 6:
          number=str(fakeAmount)[:-3]
          print(number)
          
          a=0
          numstring = ""
          number = number[::-1]
          for i in number:
            a+=1
            if a % 3 == 0:
              numstring += i +","
            else:
              numstring += i
          
          numstring = numstring[::-1]
          
          if numstring[0] == ",":
            numstring = numstring[1:]
          fakeAmount = numstring+(str(fakeAmount)[-3:])
      
          print(numstring)
      
          tax=(numstring)
      fakeAmount=str("{:.2f}".format(totalPrice))  
      if len(str(fakeAmount)) > 6:
          number=str(fakeAmount)[:-3]
          print(number)
          
          a=0
          numstring = ""
          number = number[::-1]
          for i in number:
            a+=1
            if a % 3 == 0:
              numstring += i +","
            else:
              numstring += i
          
          numstring = numstring[::-1]
          
          if numstring[0] == ",":
            numstring = numstring[1:]
          fakeAmount = numstring+(str(fakeAmount)[-3:])
      
          print(numstring)
      
          totalPrice=(numstring)
      fakeAmount=str("{:.2f}".format(newUserMoney))  
      if len(str(fakeAmount)) > 6:
          number=str(fakeAmount)[:-3]
          print(number)
          
          a=0
          numstring = ""
          number = number[::-1]
          for i in number:
            a+=1
            if a % 3 == 0:
              numstring += i +","
            else:
              numstring += i
          
          numstring = numstring[::-1]
          
          if numstring[0] == ",":
            numstring = numstring[1:]
          fakeAmount = numstring+(str(fakeAmount)[-3:])
      
          print(numstring)
      
          fakenewUserMoney=(numstring)  
    fakeAmount=str("{:.2f}".format(newUserMoney)) 
    print(str(type(itemPrice)), str(type(1)))
    if len(fakeAmount) <= 6:
        fakenewUserMoney = "{:.2f}".format(newUserMoney)
    if type(itemPrice) == type(1) or type(itemPrice) == type(1.1):
      itemPrice=str("{:.2f}".format(itemPrice))  
    if type(tax) == type(1) or type(tax) == type(1.1):
      tax=str("{:.2f}".format(tax))  
    if type(totalPrice) == type(1) or type(totalPrice) == type(1.1):
      totalPrice=str("{:.2f}".format(totalPrice))
    if not fakenewUserMoney:
      sentence = "The price is " + str(itemPrice) + "$, after taxes of " + str(tax) + "$, the total after taxes is "  + str(totalPrice) + "$. Your new balance after buying the item is " + str(fakeAmount) + "$"
    else:
      sentence = "The price is " + str(itemPrice) + "$, after taxes of " + str(tax) + "$, the total after taxes is "  + str(totalPrice) + "$. Your new balance after buying the item is " + str(fakenewUserMoney) + "$"

    db = SQL("sqlite:///users.db")
    db.execute("UPDATE users SET money = :money, itemsOwned = :itemsOwned WHERE username = :name", money=newUserMoney, itemsOwned=itemsOwned, name=session.get("name"))
    
    return render_template("sentence.html",sentence=sentence)

@app.route("/login", methods=["GET","POST"])
def login():
  if request.method == "GET":
    if not session.get("name"):
      return render_template("login.html")
    else:
      return redirect("/")
  else:
    username=request.form.get("username")
    password=request.form.get("password")

    username=username.lower().strip()
    password=password.lower().strip()

    if username == "" and password == "":
      return render_template("login.html", sentence="Please fill in your information!")
    
    if username == "":
      return render_template("login.html", sentence="Your username is invalid!")
    if password == "":
      return render_template("login.html", sentence="Your password is invalid!")

    db = SQL("sqlite:///users.db")
    results = db.execute("SELECT * FROm users WHERE username = :username", username=username)
    if len(results) == 0:
      return render_template("login.html", sentence="There is no account with that username, try creating an account!")
    elif results[0]["password"] == password:
      session["name"] = username
      return redirect("/")
    else:
      return render_template("login.html", sentence="Incorrect Password!")

@app.route("/companies")
def companies():
  file = open("fakeCompanies.txt", "r")

  fakeCompanies = []
        
  for i in file:
    fakeCompanies.append(i)
  file.close()
  return render_template("companies.html", companies=fakeCompanies)
  

@app.route("/signup", methods=["GET","POST"])
def signup():
  if request.method == "GET":
    if session.get("name"):
      return redirect("/")
    else:
      return render_template("login.html")
  else:
    username=request.form.get("username")
    password=request.form.get("password")

    username=username.lower().strip()
    password=password.lower().strip()

    if "," in username:
      return render_template("login.html", sentence="Your username is invalid! You cannot have a comma in your username!")

    if username == "" and password == "":
      return render_template("login.html", sentence="Please fill in your information!")
    
    if username == "":
      return render_template("login.html", sentence="Your username is invalid!")
    if password == "":
      return render_template("login.html", sentence="Your password is invalid!")

    db = SQL("sqlite:///users.db")
    results = db.execute("SELECT * FROm users WHERE username = :username", username=username)
    if len(results) == 0:
      db = SQL("sqlite:///users.db")
      db.execute("INSERT INTO users (username, password, money, experience) VALUES(?,?,?,?)", username, password, 0, 0)
      session["name"] = username
      return redirect("/")
    else:
      return render_template("login.html", sentence="Username has been taken!")

@app.route("/transfermoney", methods=["GET", "POST"])
def transfermoney():
  if not session.get("name"):
    return redirect("/")
  if request.method == "POST":
    username = session.get("name")
    sendMoneyTo = request.form.get("username").lower().strip()
    amount = request.form.get("amount")
    if "," in amount:
        amount=amount.replace(",", "")
    amount = float(amount)
    amount = "{:.2f}".format(amount)

    if float(amount) < 200:
      return render_template("sentence.html", sentence="Your transfer amount is under the minimum of 200$")

    db=SQL("sqlite:///users.db")
    results=db.execute("SELECT * FROM users WHERE username = :name", name=username)

    money1 = results[0]["money"]

    results2=db.execute("SELECT * FROM users WHERE username = :name", name=sendMoneyTo)

    if len(results2) == 0:
      return render_template("sentence.html", sentence="The username you entered is invalid!")
    money2 = results2[0]["money"]

    if money1 < float(amount)+500:
      return render_template("sentence.html", sentence="You have less than the amount of this transfer!")

    newMoney1 = money1-float(amount)-500
    newMoney2 = money2+float(amount)

    db=SQL("sqlite:///users.db")
    db.execute("UPDATE users SET money = :money WHERE username = :name", money=newMoney1, name=username)
    db.execute("UPDATE users SET money = :money WHERE username = :name", money=newMoney2, name=sendMoneyTo)
    db = SQL("sqlite:///users.db")

    sarveshwarMoney = db.execute("SELECT * FROM users WHERE username = :name", name="sarveshwar")[0]["money"] + 125
    imagine_dragonsMoney = db.execute("SELECT * FROM users WHERE username = :name", name="imagine_dragons")[0]["money"] + 125
    liamMoney = db.execute("SELECT * FROM users WHERE username = :name", name="lemsa")[0]["money"] + 125
    abhijayMoney = db.execute("SELECT * FROM users WHERE username = :name", name="elon musk")[0]["money"] + 125
   

    db = SQL("sqlite:///users.db")

    db.execute("UPDATE users SET money = :money WHERE username = :name", money=sarveshwarMoney, name="sarveshwar")
    db = SQL("sqlite:///users.db")
    db.execute("UPDATE users SET money = :money WHERE username = :name", money=liamMoney, name="lemsa")
    db = SQL("sqlite:///users.db")
    db.execute("UPDATE users SET money = :money WHERE username = :name", money=imagine_dragonsMoney, name="imagine_dragons")
    db = SQL("sqlite:///users.db")
    db.execute("UPDATE users SET money = :money WHERE username = :name", money=imagine_dragonsMoney, name="elon musk")
    db = SQL("sqlite:///users.db")

    if len(str(amount)) > 6:
          number=str(amount)[:-3]
          print(number)
          
          a=0
          numstring = ""
          number = number[::-1]
          for i in number:
            a+=1
            if a % 3 == 0:
              numstring += i +","
            else:
              numstring += i
          
          numstring = numstring[::-1]
          if numstring[0] == ",":
            numstring = numstring[1:]
  
          numstring = numstring+(str(amount)[-3:])
      
          print(numstring)
      
          amount=(numstring[:-1])

  return render_template("sentence.html", sentence="You have sent " + str(amount) + "$ to " + sendMoneyTo)

@app.route("/changepassword", methods=["GET", "POST"])
def changepassword():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      return render_template("changepassword.html")
    else:
      password=request.form.get("password")
      newpassword=request.form.get("newpassword")

      db = SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))

      if results[0]["password"] == password:
        db.execute("UPDATE users SET password = :password WHERE id = :id", password=newpassword, id=results[0]["id"])

      return render_template("sentence.html", sentence="You have successfully changed your password!")
     

@app.route("/dotask", methods=["GET", "POST"])
def dotask():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      username = session.get("name")
      db = SQL("sqlite:///users.db")
      results = db.execute("SELECT * FROM users WHERE username = :username", username=username)
      currentTask = results[0]["currentTask"]
      currentCode = results[0]["currentCode"]

      if currentTask == None and currentCode == None:
        file = open("fakeCompanies.txt", "r")

        fakeCompanies = []
        
        for i in file:
          fakeCompanies.append(i)
        file.close()

        companyNO = random.randint(0, len(fakeCompanies)-1)

        file = open("sixLetter.txt", "r")

        words = []
        
        for i in file:
          words.append(i)
        file.close()

        wordNO = random.randint(0, len(words)-1)
          
        task=fakeCompanies[companyNO] + " has hired you to find weaknesses in their system, to do this, you must figure out the six letter codeword!"
        
        code=words[wordNO].strip()

        db=SQL("sqlite:///users.db")
        db.execute("UPDATE users SET currentTask = :task, currentCode = :word WHERE username = :name", task=task, word=code, name=session.get("name"))

      db=SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))

      currentCode=results[0]["currentCode"]

      correctPlaceLetters=[]
      wrongPlaceLetters=[]

      guessesList = results[0]["guesses"]

      if guessesList!=None:
        if "," in guessesList:
          guessesList=guessesList.split(",")
        else:
          guessesList=[guessesList]

      print(guessesList)

      if guessesList != None:
        for guess in guessesList:
          for count, i in enumerate(guess):
            if i == currentCode[count] and i not in correctPlaceLetters:
              print(count, i)
              correctPlaceLetters.append(i)
            elif i in currentCode and i not in wrongPlaceLetters:
              wrongPlaceLetters.append(i)
      trueWrongLetters=[]
      for i in wrongPlaceLetters:
        if i not in correctPlaceLetters and i != currentCode[0] and i != currentCode[-1]:
          trueWrongLetters.append(i)

      licp=""

      for i in correctPlaceLetters:
        licp += i + ", "

      licp=licp[:-2]

      liwp=""

      for i in trueWrongLetters:
        liwp += i + ", "

      liwp=liwp[:-2]
        
      task=results[0]["currentTask"]

      wordform=""
      
      for i in currentCode:
        if i in correctPlaceLetters:
          wordform+=i
        else:
          wordform+="_"

      wordform = currentCode[0] + wordform[1:5] + currentCode[-1]

      liwp=""
      for i in trueWrongLetters:
        liwp += i+","
      liwp=liwp[:-1]
      
      guesses=results[0]["guesses"]

      if guessesList == None or currentCode not in guessesList:
        return render_template("game.html", task=task, liwp=liwp, licp=licp, last=wordform, guesses=guesses)
      else:
        file = open("fakeCompanies.txt", "r")

        fakeCompanies = []
        
        for i in file:
          fakeCompanies.append(i)
        file.close()

        companyNO = random.randint(0, len(fakeCompanies)-1)

        file = open("sixLetter.txt", "r")

        words = []
        
        for i in file:
          words.append(i)
        file.close()

        wordNO = random.randint(0, len(words)-1)
          
        task=fakeCompanies[companyNO] + " has hired you to find weaknesses in their system, to do this, you must figure out the six-letter codeword!"
        
        code=words[wordNO].strip()

        db=SQL("sqlite:///users.db")
        results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))

        experience = results[0]["experience"]
        money = results[0]["money"]

        if experience == None or experience == "0":
          experience=0
        else:
          experience=int(experience)

        if money == None or money == "0":
          money=0
        else:
          money=int(money)

        moneyAdded=500+(15*experience)

        itemsOwned = results[0]["itemsOwned"]
        currentDebt = results[0]["currentDebt"]
        currentUpgrades = results[0]["upgrades"]
  
        if currentUpgrades == None:
          currentUpgrades = []
        elif "," not in currentUpgrades:
          currentUpgrades = [currentUpgrades]
        else:
          currentUpgrades = currentUpgrades.split(",")
  
        howMany = [0,1,2,3,4,5,6,7,8,9,10]
  
        howMany[0] = currentUpgrades.count("1")
        howMany[1] = currentUpgrades.count("2")
        howMany[2] = currentUpgrades.count("3")
        howMany[3] = currentUpgrades.count("4")
        howMany[4] = currentUpgrades.count("5")
        howMany[5] = currentUpgrades.count("6")
        howMany[6] = currentUpgrades.count("7")
        howMany[7] = currentUpgrades.count("8")
        howMany[8] = currentUpgrades.count("9")
        howMany[9] = currentUpgrades.count("10")
        howMany[10] = currentUpgrades.count("11")

        if currentDebt == None:
          currentDebt = 0
        else:
          currentDebt = currentDebt * 100.5

        if itemsOwned == None:
          itemsOwned=[""]
        else:
          itemsOwned=itemsOwned.split(",")

        experience=experience+1

        if "1" in itemsOwned:
          moneyAdded+=(5*((0.5*howMany[0])+1))*experience
        if "2" in itemsOwned: 
          moneyAdded+=5*((0.5*howMany[1])+1)
        if "4" in itemsOwned: 
          moneyAdded+=10*((0.5*howMany[3])+1)
        if "5" in itemsOwned: 
          moneyAdded+=1000*((0.5*howMany[4])+1)
        if "6" in itemsOwned: 
          moneyAdded+=100000*((0.5*howMany[5])+1)
        if "7" in itemsOwned: 
          moneyAdded+=10000*((0.5*howMany[6])+1)
        if "9" in itemsOwned: 
          moneyAdded+=900*((0.5*howMany[8])+1)
        if "10" in itemsOwned: 
          moneyAdded+=1000*((0.5*howMany[9])+1)
        if "11" in itemsOwned: 
          moneyAdded+=350
          experience=experience+2
        if "100" in itemsOwned: 
          moneyAdded+=400000
        if "101" in itemsOwned: 
          moneyAdded+=10000
        if "201" in itemsOwned: 
          moneyAdded+=200
        if "202" in itemsOwned: 
          moneyAdded+=400
        if "203" in itemsOwned: 
          moneyAdded+=700
        if "204" in itemsOwned: 
          moneyAdded+=900
        if "205" in itemsOwned: 
          moneyAdded+=999
        if "206" in itemsOwned: 
          moneyAdded+=1000
        if "207" in itemsOwned: 
          moneyAdded+=1400
        if "208" in itemsOwned: 
          moneyAdded+=1600
        if "209" in itemsOwned: 
          moneyAdded+=1900
        if "210" in itemsOwned: 
          moneyAdded+=2000

        normalMoneyAdded = moneyAdded

        percentMoney = moneyAdded * 0.4

        startingDebt = currentDebt

        if currentDebt > 0:
          if currentDebt < percentMoney:
            moneyAdded = moneyAdded - currentDebt
            moneyDeducted = currentDebt
            currentDebt = 0    
          else:
            moneyAdded = moneyAdded - percentMoney
            moneyDeducted = percentMoney
            currentDebt = currentDebt - percentMoney

        money=money+moneyAdded

        db=SQL("sqlite:///users.db")
        db.execute("UPDATE users SET currentTask = :task, currentCode = :word, money = :money, experience = :experience, guesses = :guesses, currentDebt = :currentDebt WHERE username = :name", task=task, word=code, money=money, experience=experience, guesses="", currentDebt=currentDebt, name=session.get("name"))

        if startingDebt > 0:
          normalAdded = normalMoneyAdded
          deductedAmount = moneyDeducted
          newPayout = normalAdded - deductedAmount
  
          sentence=f"So your original pay would have been {normalAdded} but because you have a loan from the bank, we have to deduct 40% of the payout, so your final total is {newPayout}!"
          
          return render_template("finished.html", sentence=sentence)
        return render_template("finished.html")
    else:
      file = open("sixLetter.txt", "r")

      words = []
        
      for i in file:
          words.append(i.strip())
      file.close()
      
      guess=request.form.get("guess").strip().lower()

      if guess == "powerup":
        return redirect("/missionpower")

      if guess in words:
      
        db=SQL("sqlite:///users.db")
        results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))
        currentGuesses=results[0]["guesses"]
        newGuesses=""
        if currentGuesses == None or currentGuesses == "":
          newGuesses = guess
        else:
          newGuesses = currentGuesses+","+guess
  
        db=SQL("sqlite:///users.db")
        db.execute("UPDATE users SET guesses = :guesses WHERE username = :name", guesses=newGuesses, name=session.get("name"))
      
      return redirect("/dotask")

@app.route("/abandontask")
def abandontask():
  if not session.get("name"):
    return redirect("/")
  else:
        file = open("fakeCompanies.txt", "r")

        fakeCompanies = []
        
        for i in file:
          fakeCompanies.append(i)
        file.close()

        companyNO = random.randint(0, len(fakeCompanies)-1)

        file = open("sixLetter.txt", "r")

        words = []
        
        for i in file:
          words.append(i)
        file.close()

        wordNO = random.randint(0, len(words)-1)
          
        task=fakeCompanies[companyNO] + " has hired you to find weaknesses in their system, to do this, you must figure out the six-letter codeword!"
        
        code=words[wordNO].strip()

        db=SQL("sqlite:///users.db")
        results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))

        money = results[0]["money"]

        money=money-(500+(500*0.13))

        if money < 0:
          return render_template("sentence.html", sentence="You don't have enough money to abandon this task!")

        db=SQL("sqlite:///users.db")
        db.execute("UPDATE users SET currentTask = :task, currentCode = :word, money = :money, experience = :experience, guesses = :guesses WHERE username = :name", task=task, word=code, money=money, experience=results[0]["experience"], guesses="", name=session.get("name"))
        return redirect("/")

@app.route("/leaderboard")
def leaderboard():
  if not session.get("name"):
    return redirect("/")
  else:
    db = SQL("sqlite:///users.db")
    results = db.execute("SELECT * FROM users WHERE username <> :u1 AND username <> :u2 AND username <> :u3 AND username <> :u4 AND username <> :u5", u1="sarveshwar", u2="elon musk", u3="lemsa", u4="imagine_dragons", u5="hibanana")
    creators=["sarveshwar", "lemsa", "imagine_dragons", "elon musk"]

    for player in results:
      if player["currentDebt"] != None and player["currentDebt"] > 0:
        player["money"] = int(player["money"]) - int(player["currentDebt"])

    results1=sorted(results, key=lambda x: x['money'])[::-1][:6]
    for player in results1:
      player["money"] = "{:.2f}".format(float(player["money"]))
      if len(str(player["money"])) > 6:
          number=str(player["money"])[:-3]
          print(number)
          
          a=0
          numstring = ""
          number = number[::-1]
          for i in number:
            a+=1
            if a % 3 == 0:
              numstring += i +","
            else:
              numstring += i
          
          numstring = numstring[::-1]
          
          if numstring[0] == ",":
            numstring = numstring[1:]
          player["money"] = numstring+(str(player["money"])[-3:])
    experienced=sorted(results, key=lambda x: x['experience'])[::-1][:6]

    creatorInfo=[]

    for creator in creators:
      db = SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=creator)
      creatorInfo.append(results[0])
    for player in creatorInfo:
      player["money"] = "{:.2f}".format(float(player["money"]))
      if len(str(player["money"])) > 6:
          number=str(player["money"])[:-3]
          print(number)
          
          a=0
          numstring = ""
          number = number[::-1]
          for i in number:
            a+=1
            if a % 3 == 0:
              numstring += i +","
            else:
              numstring += i
          
          numstring = numstring[::-1]
          
          if numstring[0] == ",":
            numstring = numstring[1:]
          player["money"] = numstring+(str(player["money"])[-3:])
    
    return render_template("leaderboard.html", moneys=results1, experienced=experienced, creators=creatorInfo)

@app.route("/deleteaccount", methods=["GET","POST"])
def deleteaccount():
  coolBeans=["sarveshwar", "lemsa", "imagine_dragons", "elon musk"]
  if not session.get("name"):
    return redirect("/")
  elif session.get("name") not in coolBeans:
    return redirect("/")
  else:
    if request.method == "GET":
      return render_template("deleteaccount.html")
    else:
      username=request.form.get("username")
      username=username.replace(","," ")
      print(username)
      db = SQL("sqlite:///users.db")
      if username not in coolBeans:
        db.execute("DELETE FROM users WHERE username = :name", name=username)
      else:
        return render_template("sentence.html", sentence="You cannot delete the account of an admin!")
      return redirect("/")

@app.route("/challenge", methods=["GET","POST"])
def challenge():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      return render_template("problems.html")
    return render_template("sentence.html", sentence="This page is currently being worked on")


@app.route("/lotteries", methods=["GET", "POST"])
def lotteries():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      return render_template("lotteries.html")
    elif request.method == "POST":
      ticketPurchased = int(request.form.get("id"))-1
      tickets = [
        {
          "price" : 500,
          "name" : "Abhijayism Centre Lottery",
          "odds" : 500,
          "prize" : 2000000000
        },
        {
          "price" : 1000,
          "name" : "Sarveshwar Suits Lottery",
          "odds" : 1000,
          "prize" : "24k Gold Suit"
        },
        {
          "price" : 1000,
          "name" : "Malaz O' Software Lottery",
          "odds" : 250,
          "prize" : "10,000,000,000 + PowerPc"
        },
        {
          "price" : 2000,
          "name" : "Liam Swim Equipment", 
          "odds" : 300, 
          "prize" : "Liam's Swim Goggles(+$400000 per mission)"
        }
      ]
      riggedtickets = [
        {
          "price" : 500,
          "name" : "Abhijayism Centre Lottery",
          "odds" : 2,
          "prize" : 200000000
        },
        {
          "price" : 1000,
          "name" : "Sarveshwar Suits Lottery",
          "odds" : 2,
          "prize" : "24k Gold Suit"
        },
        {
          "price" : 1000,
          "name" : "Malaz O' Software Lottery",
          "odds" : 2,
          "prize" : "10,000,000,000 + PowerPc"
        },
        {
          "price" : 2000,
          "name" : "Liam Swim Equipment", 
          "odds" : 2, 
          "prize" : "Liam's Swim Goggles(+$400000 per mission)"
        }
      ]

      file = open("yesorno.txt", "r")
      for i in file:
        if i.strip() == "yes":
          ticket = riggedtickets[ticketPurchased]
        else:
          ticket = tickets[ticketPurchased]

      price = ticket["price"]
      name  = ticket["name"]
      odds = ticket["odds"]
      prize = ticket["prize"]

      db = SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROm users WHERE username = :name", name=session.get("name"))

      money=results[0]["money"]
      id=results[0]["id"]

      lotteryNumber = random.randint(1, odds)

      if money > price:
        if lotteryNumber == 1:
          money=money-price
          if type(prize) == "int":
            money=money+prize
          elif prize == "10,000,000,000 + PowerPc":
            money=money+10000000000
            itemsOwned = results[0]["itemsOwned"]
            itemNo = 101
            if itemNo not in itemsOwned:
              if itemsOwned == None:
                itemsOwned = str(itemNo)
              else:
                itemsOwned += ","+str(itemNo)
                db = SQL("sqlite:///users.db")
                db.execute("UPDATE users SET itemsOwned = :itemsOwned WHERE id = :id", itemsOwned=itemsOwned, id=id)
          elif prize == "24k Gold Suit":
            itemsOwned = results[0]["itemsOwned"]
            itemNo = 7
            if str(itemNo) not in itemsOwned:
              if itemsOwned == None:
                itemsOwned = str(itemNo)
              else:
                itemsOwned += ","+str(itemNo)
                db = SQL("sqlite:///users.db")
                db.execute("UPDATE users SET itemsOwned = :itemsOwned WHERE id = :id", itemsOwned=itemsOwned, id=id)
          elif prize == 200000000:
            money=money+2000000000
            db = SQL("sqlite:///users.db")
            db.execute("UPDATE users SET money = :money WHERE username = :name",name=session.get("name"), money=money)
          elif prize == "Liam's Swim Goggles(+$400000 per mission)":
            itemsOwned = results[0]["itemsOwned"]
            itemNo = 100
            if itemsOwned == None:
              itemsOwned = str(itemNo)
            else:
              itemsOwned += ","+str(itemNo)
              db = SQL("sqlite:///users.db")
              db.execute("UPDATE users SET itemsOwned = :itemsOwned WHERE id = :id", itemsOwned=itemsOwned, id=id)
          db = SQL("sqlite:///users.db")
          db.execute("UPDATE users SET money = :money WHERE id = :id",id=id, money=money)
          sentence= f"You have won the {name} lottery, {prize} has been added to your account"
          return render_template("sentence.html", sentence=sentence)
        else:
          money=money-price
          db = SQL("sqlite:///users.db")
          db.execute("UPDATE users SET money = :money WHERE id = :id",id=id, money=money)
          return render_template("sentence.html", sentence="You did not win the lottery!")
      else:
        return render_template("sentence.html", sentence="You cannot afford this ticket!")


@app.route("/change")
def change():
  db = SQL("sqlite:///users.db")
  db.execute("UPDATE users SET password = :password WHERE username = :username", username="imagine_dragons", password="temp")
  return redirect("/")


@app.route("/buymoney", methods=["GET", "POST"])
def buymoney():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      return render_template("moneystore.html")
    if request.method == "POST":
      id = int(request.form.get("id"))
      
      #moneyBought = Amount of HackerLife Bucks bought
      moneyBought = 0
      #moneySpent = The value of the HackerLife Bucks bought
      moneySpent = 0

      if id == 1:
        moneyBought = 5000
        moneySpent = 1
      elif id == 2:
        moneyBought = 15000
        moneySpent = 5
      elif id == 2:
        moneyBought = 25000
        moneySpent = 8
      elif id == 2:
        moneyBought = 70000
        moneySpent = 15
        
      return render_template("sentence.html", sentence="Working on it! Have fun on the rest of HackerLife")

@app.route("/reportuser", methods=["GET","POST"])
def reportuser():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      return render_template("reportbugs.html", type="users")
    else:
      global email
      username = request.form.get("username").lower()
      description=request.form.get("description")
      email=request.form.get("email")
      description=description.strip()
      username=username.strip()
      email=email.strip()
      if description == "":
        return render_template("sentence.html", sentence="You haven't entered a valid reason!")
      if username == "":
        return render_template("sentence.html", sentence="You haven't entered a valid username!")
      if email == "":
        return render_template("sentence.html", sentence="You haven't entered a valid email address!")
        
      db = SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=username)

      if len(results) == 0:
        return render_template("sentence.html", sentence="There is no player with that username!")
      
      file = open("banUsers.txt", "a")
      bug="\n" + username + " - " + description
      file.write(bug)
      file.close()

    def report_email():
      receiver="csbrofficialteam@gmail.com"
      message=(f'the user with the email {email} reported the user {username} describing the situation as {description}')
      sender=yagmail.SMTP("csbrnoreply@gmail.com",               password=os.getenv('emailPassword'))
      sender.send(to=receiver, subject="A New Player Got Reported!!!", contents=message)

    return render_template("sentence.html", sentence="Thank you for reporting this suspicious player, we'll look into it!"), report_email()

@app.route("/reportbugs", methods=["GET","POST"])
def reportbugs():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      return render_template("reportbugs.html", type="bugs")
    else:
      description=request.form.get("description")
      email=request.form.get("email")
      email=email.strip()
      description=description.strip()
      if description == "":
        return render_template("sentence.html", sentence="You haven't entered valid input!")
      file = open("otherProblems.txt", "a")
      bug="\n" + description
      file.write(bug)
      file.close()

      def report_email():
        receiver="csbrofficialteam@gmail.com"
        message=(f'The user with the email {email} is saying {description}')
        sender=yagmail.SMTP("csbrnoreply@gmail.com",               password=os.getenv('emailPassword'))
        sender.send(to=receiver, subject="A New Bug Report Came in!!!", contents=message)
      
      return render_template("sentence.html", sentence="Thank you for reporting this bug, we're already on it!"), report_email()

@app.route("/suggest", methods=["GET","POST"])
def suggestions():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      return render_template("reportbugs.html", type="suggestion")
    else:
      global email

      description=request.form.get("description")
      email=request.form.get("email")
      description=description.strip()
      email=email.strip()
      if description == "":
        return render_template("sentence.html", sentence="You haven't entered a valid suggestion!")
      if email == "":
        return render_template("sentence.html", sentence="You haven't entered a valid email address!")

      def report_email():
        receiver="csbrofficialteam@gmail.com"
        message=(f'The user with the email {email} is saying {description}')
        sender=yagmail.SMTP("csbrnoreply@gmail.com",               password=os.getenv('emailPassword'))
        sender.send(to=receiver, subject="A New Bug Report Came in!!!", contents=message)

      return render_template("sentence.html", sentence="Thank you for the amazing suggetion!"), report_email()

@app.route("/mod", methods=["GET", "POST"])
def modcommands():
  if not session.get("name"):
    return redirect("/")
  else:
    coolBeans=["sarveshwar", "lemsa", "imagine_dragons", "elon musk"]
    if session.get("name") not in coolBeans:
      return redirect("/")
    if request.method == "GET":
      return render_template("command.html")
    username=session.get("name")
    command=request.form.get("command").lower()
    def givemoney(amount):
      db = SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))
      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET money = :money WHERE username = :username", username=username, money=int(results[0]["money"])+amount)
    def givexp(amount):
      db = SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))
      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET experience = :experience WHERE username = :username", username=username, experience=int(results[0]["experience"])+amount)
    commandList=["deleteuser (username)", "givemoney (amount)", "giveother (username) (amount)", "givexp (username) (amount)", "takemoney (username) (amount)", "giveitem (username) (item ID)", "takeitem (username) (item ID)", "showwordduel (player1 username) (player2 username)", "showword (username)", "resetmoney (username)", "resetdebt (username)", "resetxp (username)", "resetall (username)", "resetitem (username)", "changeusername (username) (username2)", "riglottery (yes or no)", "forceduel (player1 username) (player2 username) (bet)", "killduel (player1 username) (player2 username)", "stats (player1 username) (player2 username)", "declineall (username)", "unblockuser (username)", "blockuser (username)", "spectate (player1 username) (player2 username)"]
    if "deleteuser" in command:
      return redirect("/deleteaccount")
      if username in coolBeans:
        amount = command.split()[1]
        amount = amount.replace(",", "")
    elif "givemoney" in command:
      amount = command.split()[1]
      amount = amount.replace(",", "")
          
      givemoney(int(amount))
    elif "giveother" in command:
      username = command.split()[1]
  
      if "," in username:
        username = username.replace(",", " ")
      amount = int(command.split()[2])
      db = SQL("sqlite:///users.db")
      results = db.execute("SELECT * FROM users WHERE username = :name", name=username)
      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET money = :money WHERE username = :username", username=username, money=int(results[0]["money"]) + amount)
    elif "givexp" in command:
      username = command.split()[1]

      if "," in username:
        username = username.replace(",", " ")
      amount = int(command.split()[2])
      db = SQL("sqlite:///users.db")
      results = db.execute("SELECT * FROM users WHERE username = :name", name=username)
      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET experience = :experience WHERE username = :username", username=username, experience=int(results[0]["experience"]) + amount)
    elif "takemoney" in command:
      username = command.split()[1]
   
      if "," in username:
        username = username.replace(",", " ")
      amount = int(command.split()[2])
      db = SQL("sqlite:///users.db")
      results = db.execute("SELECT * FROM users WHERE username = :name", name=username)
      if int(results[0]["money"])-amount < 0:
        return render_template("sentence.html", sentence="The user doesn't have enough money!")
      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET money = :money WHERE username = :username", username=username, money=int(results[0]["money"])-amount)
    elif "giveitem" in command:
      username = command.split()[1]
      if "," in username:
        username = username.replace(",", " ")
      print(username)
      itemID = command.split()[2]
      db = SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("name"))
      itemsOwned=results[0]["itemsOwned"]
      if itemID not in itemsOwned:
        if itemsOwned == None:
          itemsOwned = str(itemID)
        else:
          itemsOwned += ","+str(itemID)
          db = SQL("sqlite:///users.db")
          db.execute("UPDATE users SET itemsOwned = :itemsOwned WHERE username = :username", itemsOwned=itemsOwned, username=session.get("name"))

    elif "takeitem" in command:
      username = command.split()[1]
      if "," in username:
        username = username.replace(",", " ")
      print(username)
      itemID = command.split()[2]
      id=itemID
      db = SQL("sqlite:///users.db")
      results = db.execute("SELECT * FROM users WHERE username = :name", name=username)
  
      userMoney = results[0]["money"]
  
      itemsOwned = results[0]["itemsOwned"]
      if itemsOwned == None or itemsOwned == "":
        return render_template("sentencee.html", sentence="The user does not have the product yet!")
      elif "," not in itemsOwned:
        itemsOwned=[itemsOwned]
      else:
        itemsOwned = itemsOwned.split(",")
  
      if id not in itemsOwned:
        return render_template("sentence.html", sentence="The user does not have this item yet!")
  
      itemsOwned.remove(id)
  
      newItems=""
  
      for item in itemsOwned:
        newItems += item + ","
      newItems=newItems[:-1]
  
  
      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET itemsOwned = :newItems WHERE username = :name", newItems=newItems, name=username)

      return render_template("sentence.html", sentence="You have removed the item from this user's inventory!")

    elif "showwordduel" in command:
      player1 = command.split()[1].strip().lower()
      player2 = command.split()[2].strip().lower()

      player1 = player1.replace(",", " ")
      player2 = player2.replace(",", " ")

      db = SQL("sqlite:///duels.db")
      results=db.execute("SELECT * FROM duels WHERE player1 = :player1 AND player2 = :player2", player1=player1, player2=player2)[-1]

      word = results["currentCode"]

      sentence = "The word is " + str(word)

      return render_template("sentence.html", sentence=sentence)

    elif "showword" in command:
      username = command.split()[1]
    
      if "," in username:
        username=username.replace(",", " ")
   
      db = SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=username)
      word=results[0]["currentCode"]
      sentence="The word is " + word
      return render_template("sentence.html", sentence=sentence)
    elif "resetmoney" in command:
      username = command.split()[1]
      if "," in username:
        username=username.replace(",", " ")
    
      db = SQL("sqlite:///users.db")
      results=db.execute("UPDATE users SET money = :money WHERE username = :username", money=0, username=username)
    elif "resetdebt" in command:
      username = command.split()[1]
      if "," in username:
        username=username.replace(",", " ")
    
      db = SQL("sqlite:///users.db")
      results=db.execute("UPDATE users SET currentDebt = :currentDebt WHERE username = :username", currentDebt=0, username=username)
    elif "resetall" in command:
      username = command.split()[1]
      if "," in username:
        username=username.replace(",", " ")
    
      db = SQL("sqlite:///users.db")
      results=db.execute("UPDATE users SET money = :money, experience = :experience, currentDebt = :currentDebt WHERE username = :username", money=0, experience=0, currentDebt=0, username=username)
      
    elif "resetxp" in command:
      username = command.split()[1]
      if "," in username:
        username=username.replace(",", " ")
    
      db = SQL("sqlite:///users.db")
      results=db.execute("UPDATE users SET experience = :experience WHERE username = :username", experience=0, username=username)

    elif "resetitem" in command:
      username = command.split()[1]
      if "," in username:
        username=username.replace(",", " ")

      db = SQL("sqlite:///users.db")
      results=db.execute("UPDATE users SET itemsOwned = :itemsOwned WHERE username = :username",itemsOwned="", username=username)

      sentence="The items from the account of " + username + " has been reset"
      return render_template("sentence.html", sentence=sentence)
    elif "changeusername" in command:
      username = command.split()[1]
      if "," in username:
        username=username.replace(",", " ")
      username2 = command.split()[2]
      if "," in username2:
        username2=username2.replace(",", " ")
      db = SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=username2)
      coolBeans=["lemsa", "imagine_dragons", "sarveshwar", "elon musk"]
      if username2 in coolBeans:
        return render_template("sentence.html", sentence="You can't change your username to an admin's name!")
      if len(results) == 0:
        db.execute("UPDATE users SET username = :name WHERE username = :name2", name=username2, name2=username)
      return render_template("sentence.html", sentence="You have successfully changed your name!")

    elif "riglottery" in command:
      yesNo = command.split()[1]
      file = open("yesorno.txt", "w")
      file.write(yesNo)
      file.close()

      return render_template("sentence.html", sentence="You have successfully changed the lottery!")

    elif "forceduel" in command:
      opponent = command.split()[1].lower()
      opponent = opponent.replace(",", " ")
      opponent2 = command.split()[2].lower()
      opponent2 = opponent2.replace(",", " ")
      bet = command.split()[3]
      db2 = SQL("sqlite:///duels.db")
      results=db2.execute("SELECT * FROM duels WHERE status = :status AND player1 = :name OR status = :status AND player2 = :name", status="accepted and playing", name=opponent)

      results=db2.execute("SELECT * FROM duels WHERE status = :status AND player1 = :name OR status = :status AND player2 = :name", status="accepted and playing", name=opponent2)
  
      bet = float(bet)
  
      myname = session.get("name")
  
      usersDB  = SQL("sqlite:///users.db")
      
      player1 = usersDB.execute("SELECT * FROM users WHERE username = :name", name=opponent)[0]
      player2 = usersDB.execute("SELECT * FROM users WHERE username = :name", name=opponent2)[0]
  
      if bet > player1["money"]:
        return render_template("sentence.html", sentence="You can't afford this bet!")
      elif bet > player2["money"]:
        return render_template("sentence.html", sentence="Your opponent can't afford this bet :(") 
   
      db = SQL("sqlite:///duels.db")
      db.execute("INSERT INTO duels (player1, player2, bet, guesses1, guesses2, status) VALUES (?,?,?,?,?,?)", opponent, opponent2, bet, "", "", "accepted and playing")
      results=db.execute("SELECT * FROM duels")[-1]

      return redirect("/mainduel")

    elif "killduel" in command:
      opponent = command.split()[1].lower()
      opponent2 = command.split()[2].lower()
      opponent = opponent.replace(",", " ")
      opponent2 = opponent2.replace(",", " ")
      bet = command.split()[2]
      db2 = SQL("sqlite:///duels.db")
      results=db2.execute("SELECT * FROM duels WHERE status = :status AND player1 = :name OR status = :status AND player2 = :name2", status="accepted and playing", name=opponent, name2=opponent2)
  
      db = SQL("sqlite:///duels.db")
      db.execute("UPDATE duels SET status = :status WHERE id = :id", status="This duel has been canceled!", id=results[0]["id"])
 
      return redirect("/mainduel")

    elif "declineall" in command:
      opponent = command.split()[1].lower()
      db = SQL("sqlite:///requests.db")
      db.execute("DELETE FROM requests WHERE receiver = :username", username=opponent)

      db = SQL("sqlite:///duels.db")
      db.execute("DELETE FROM duels WHERE player2 = :username AND status IS NULL", username=opponent)

      return render_template("sentence.html", sentence="All the requests of the user has been deleted!")

    elif "stats" in command:
      opponent = command.split()[1].lower()
      opponent2 = command.split()[2].lower()
      opponent = opponent.replace(",", " ")
      opponent2 = opponent2.replace(",", " ")
      db2 = SQL("sqlite:///duels.db")
      results=db2.execute("SELECT * FROM duels WHERE player1 = :name AND player2 = :name2 OR player1 = :name2 AND player2 = :name", name=opponent, name2=opponent2)
      player1W = 0
      player1L = 0
      checkState = opponent + " won!"
      for result in results:
        if result["status"] != None and checkState in result["status"]:
          player1W += 1
        else:
          player1L += 1

      winRate = player1W/(player1W + player1L)*100

      sentence=opponent + " has won " + str(player1W) + " times to " + opponent2 + ", and has lost " + str(player1L) + " times. The win rate is " + str(winRate) + "%"

      return render_template("sentence.html", sentence=sentence)

    elif "unblockuser" in command:
      name=command.split()[1].strip().lower()

      username = command.split()[2].strip().lower()
  
      db = SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=name)
  
      currentBlocked = results[0]["blocked"]
  
      if currentBlocked == None or currentBlocked == "":
        currentBlocked = []
      elif "," not in currentBlocked:
        currentBlocked = [currentBlocked]
      else:
        currentBlocked = currentBlocked.split(",")
  
      if username not in currentBlocked:
        return render_template("sentence.html", sentence="You have not blocked this person!")
  
      currentBlocked.remove(username)
  
      blockedStr = ""
  
      for i in currentBlocked:
        blockedStr+=i+","
  
      blockedStr=blockedStr[:-1]
  
      db.execute("UPDATE users SET blocked = :blocked WHERE username = :name", name=name, blocked=blockedStr)
      

    elif "blockuser" in command:
      name=command.split()[1].strip().lower()

      username = command.split()[2].strip().lower()
  
      db = SQL("sqlite:///users.db")
      results=db.execute("SELECT * FROM users WHERE username = :name", name=name)
  
      currentBlocked = results[0]["blocked"]
  
      if currentBlocked == None or currentBlocked == "":
        currentBlocked = []
      elif "," not in currentBlocked:
        currentBlocked = [currentBlocked]
      else:
        currentBlocked = currentBlocked.split(",")
  
      if username in currentBlocked:
        return render_template("sentence.html", sentence="You have already blocked this person!")
  
      currentBlocked.append(username)
  
      blockedStr = ""
  
      for i in currentBlocked:
        blockedStr+=i+","
  
      blockedStr=blockedStr[:-1]
  
      db.execute("UPDATE users SET blocked = :blocked WHERE username = :name", name=name, blocked=blockedStr)

    elif "listcommands" in command:
      sentence=""
      for command in commandList:
        sentence+=command+", "
      sentence=sentence[:-2]
      return render_template("sentence.html", sentence="", sentenceList=commandList)
    elif "spectate" in command:
      opponent = command.split()[1].lower()
      opponent2 = command.split()[2].lower()
      opponent = opponent.replace(",", " ")
      opponent2 = opponent2.replace(",", " ")
     
      db2 = SQL("sqlite:///duels.db")
      results=db2.execute("SELECT * FROM duels WHERE player1 = :name AND player2 = :name2", name=opponent, name2=opponent2)
      
      status = results[-1]["status"]
      if status == None:
        status = "Not Playing!"
      sentence = "The status in this duel is " + status

      return render_template("sentence.html", sentence=sentence)
      
    return redirect("/")

@app.route("/itemids")
def itemids():
  if not session.get("name"):
    return redirect("/")
  return render_template("lenditems.html")

@app.route("/giveitems", methods=["GET","POST"])
def lenditems():
  if not session.get("name"):
    return redirect("/")
  else:
    if request.method == "GET":
      return render_template("lenditems.html")
    if request.method == "POST":
      username = session.get("name")
      sendItemTo = request.form.get("username").lower().strip()
      itemID = request.form.get("item").strip()
      db=SQL("sqlite:///users.db")
      results = db.execute("SELECT * FROM users WHERE username = :name", name=username)

      sender = results[0]

      if not itemID.isdigit():
        return redirect("/itemids")

      userItem = sender["itemsOwned"]

      if userItem == None or userItem == "":
        return render_template("sentence.html", sentence="You don't have items to transfer!")

      if "," not in userItem:
        items = [userItem]
      else:
        items=userItem.split(",")

      if itemID not in items:
        return render_template("sentence.html", sentence="You don't have the item you are trying to transfer!")

      db = SQL("sqlite:///users.db")
      receiver = db.execute("SELECT * FROM users WHERE username = :name", name=sendItemTo)[0]
      receiverItems=receiver["itemsOwned"]

      if receiverItems == None:
        receiverItems = str(itemID)
      else:
        receiverItems += ","+str(itemID)

      items.remove(str(itemID))
      newItems=""
      for i in items:
        newItems += i + ","
      newitems=newItems[:-1]

      db.execute("UPDATE users SET itemsOwned = :itemsOwned WHERE username = :name", itemsOwned=receiverItems, name=sendItemTo)

      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET itemsOwned = :itemsOwned WHERE username = :name", itemsOwned=newItems, name=username)
      
      return render_template("sentence.html", sentence="You have successfully sent the item!")
      
    return render_template("sentence.html", sentence="working on it!")

@app.route("/blockuser", methods=["GET", "POST"])
def blockuser():
  if not session.get("name"):
    return redirect("/")
  else:
    name=session.get("name")

    username = request.form.get("username").strip().lower()

    db = SQL("sqlite:///users.db")
    results=db.execute("SELECT * FROM users WHERE username = :name", name=name)

    currentBlocked = results[0]["blocked"]

    if currentBlocked == None or currentBlocked == "":
      currentBlocked = []
    elif "," not in currentBlocked:
      currentBlocked = [currentBlocked]
    else:
      currentBlocked = currentBlocked.split(",")

    if username in currentBlocked:
      return render_template("sentence.html", sentence="You have already blocked this person!")

    currentBlocked.append(username)

    blockedStr = ""

    for i in currentBlocked:
      blockedStr+=i+","

    blockedStr=blockedStr[:-1]

    db.execute("UPDATE users SET blocked = :blocked WHERE username = :name", name=name, blocked=blockedStr)
    
    return render_template("sentence.html", sentence="You have successfully blocked " + username + "!")

@app.route("/unblockuser", methods=["GET", "POST"])
def unblockuser():
  if not session.get("name"):
    return redirect("/")
  else:
    name=session.get("name")

    username = request.form.get("username").strip().lower()

    db = SQL("sqlite:///users.db")
    results=db.execute("SELECT * FROM users WHERE username = :name", name=name)

    currentBlocked = results[0]["blocked"]

    if currentBlocked == None or currentBlocked == "":
      currentBlocked = []
    elif "," not in currentBlocked:
      currentBlocked = [currentBlocked]
    else:
      currentBlocked = currentBlocked.split(",")

    if username not in currentBlocked:
      return render_template("sentence.html", sentence="You have not blocked this person!")

    currentBlocked.remove(username)

    blockedStr = ""

    for i in currentBlocked:
      blockedStr+=i+","

    blockedStr=blockedStr[:-1]

    db.execute("UPDATE users SET blocked = :blocked WHERE username = :name", name=name, blocked=blockedStr)
    
    return render_template("sentence.html", sentence="You have successfully unblocked " + username + "!")

@app.route("/logout", methods=["GET","POST"])
def logout():
  session["name"] = None
  return redirect("/")

@app.route("/stats")
def datascience():
    coolBeans = ["imagine_dragons", "lemsa", "sarveshwar", "elon musk"]
  
    db = SQL("sqlite:///duels.db")
    data = db.execute("SELECT * FROM duels")

    totalGuesses = 0
    totalWords = 0

    totalBets = 0
    totalDuels = 0

    for i in data:
      if i["player1"] not in coolBeans and i["player2"] not in coolBeans:
        totalBets += int(i["bet"])
        totalDuels += 1
      if i["status"] != None and "won" in i["status"]:
        username = i["status"].split()
        
        nameNum=0
        
        for num in range(len(username)):
          if "won" not in username[num]:
            nameNum += 1
          else:
            break

        playerName = ""

        username=username[:nameNum]

        for part in username:
          playerName += part + " "

        playerName=playerName[:-1]

        if playerName == i["player1"]:
          guesses = "guesses1"
        else:
          guesses = "guesses2"
        
        totalGuesses += len(i[guesses].split(","))
        totalWords += 1

    averageGuesses = totalGuesses/totalWords

    averageBet = totalBets/totalDuels

    usersDB = SQL("sqlite:///users.db")
    results=usersDB.execute("SELECT * FROM users")

    totalMoney = 0
    totalExperience = 0

    coolBeans = ["imagine_dragons", "lemsa", "sarveshwar", "elon musk"]

    for user in results:
      if user["money"] != None:
        if user["username"] not in coolBeans:
          totalMoney += float(user["money"])
          totalExperience += int(user["experience"])

    averageMoney = totalMoney / len(results)
    averageExperience = totalExperience / len(results)

    sentence1 = "There have been a total of " + str(totalGuesses) + " guesses in " + str(totalWords) + " completed duels!" 
    sentence2 = "The average number of guesses it takes to get a word is " + "{:.2f}".format(averageGuesses)
    sentence3 = "In total, there have been " + str(len(results)) + " HackerLife accounts created!"
    sentence4 = "The average money balance on HackerLife accounts is " + "{:.2f}".format(averageMoney) + "$"
    sentence5 = "The average number of missions completed in HackerLife accounts is " + "{:.2f}".format(averageExperience)
    sentence6 = "The average bet on duels is " + "{:.2f}".format(averageBet) + "$"

    lastSentence = "Sign up to suggest other interesting statistics!"
    
    sentences=[sentence1, sentence2, sentence3, sentence4, sentence5, sentence6, "", lastSentence]

    return render_template("sentence.html", sentenceList=sentences)

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=8000)
