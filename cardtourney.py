#!/usr/bin/python3
import glob
import subprocess
import sys
import json
import csv
from sharedlib import Card, Config, Attr
import jsonpickle
import pickle

cards = glob.glob('./*.card')
notImplementedCards = []
notImplementedAttrs = frozenset([])

for cardFile in cards:
	card = None
	with open(cardFile, 'rb') as f:
		card = pickle.load(f)

	niAttrs = notImplementedAttrs.intersection(card.attrs)
	if len(niAttrs) > 0:
		print("Card '" + card.name + "' not implement yet due to the attribute(s): "+",".join([a.value for a in niAttrs]))
		cards.remove(cardFile)

results = []
rankingFileName = 'ranking.csv'

config = None
with open("config.json") as f:
	config = jsonpickle.decode(f.read())

defenseDict = dict()
for card in cards:
	defenseDict[card] = [0,0]

for attacker in cards:
	totalWins = 0
	totalDraws = 0
	totalLosses = 0
	cardsBeaten = 0

	attackCard = None
	with open(attacker, 'rb') as f:
		attackCard = pickle.load(f)

	for defender in cards:
		if attacker == defender:
			continue

		outcomeJson = subprocess.check_output([sys.executable, "cardfight.py",attacker,defender, "-s", "-a"])
		outcome = json.loads(outcomeJson.decode(encoding='UTF-8'))
		wins = outcome["WINS"]
		losses = outcome["LOSSES"]

		defenseScore = defenseDict[defender]

		totalWins += wins
		defenseScore[0] += losses

		if wins > losses:
			cardsBeaten += 1
		else:
			defenseScore[1] += 1


	results.append([attacker, attackCard.name, totalWins, cardsBeaten])
	print("{} won {} battles beating {} opponents".format(attackCard.name, totalWins, cardsBeaten))

for card in results:
	defenseScore = defenseDict[card[0]]
	card[2] += defenseScore[0]
	card[3] += defenseScore[1] 

results.sort(key=lambda x: x[2], reverse=True)

with open(rankingFileName, 'w', newline='') as rankingFile:
	rankWriter = csv.writer(rankingFile)
	maxCardsToBeat = (len(cards)-1) * 2
	maxWins = config.numFights * maxCardsToBeat
	rankWriter.writerow(["Ranking","Name", "Total Fights won (out of {})".format(maxWins), "Cards Beaten (out of {})".format(maxCardsToBeat)])
	rank = 1
	for card in results:
		rankWriter.writerow([rank] + card[1:])
		rank += 1

		
print("rankings saved to " + rankingFileName)