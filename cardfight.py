#!/usr/bin/python3
import random
import copy
import enum
import jsonpickle
import pickle
import argparse
from sharedlib import Attr, Card
import json

class Config:
	def __init__(self, numFights, maxTurns):
		self.numFights = numFights
		self.maxTurns = maxTurns

class Die:
	def __init__(self, attack, defense, magic, mundane, numSides=12):
		self.attack = attack
		self.defense = defense
		self.magic = magic
		self.mundane = mundane
		self.numSides = numSides


class Winner(enum.Enum):
	attacker = 1
	defender = -1
	draw = 0

def fight(attacker, defender):
	attack(attacker, defender)
	if Attr.doubleAttack in attacker.attrs and attacker.currentLife() > 0 and defender.currentLife() > 0:
		attack(attacker, defender)

def attack(attacker, defender):
	totalAttack = 0

	if Attr.ethereal in defender.attrs:
		blackDie = diceTypes["black"]
		for _ in range(0,2):
			if random.randint(1,blackDie.numSides) <= blackDie.magic:
				return

	for key in attacker.dice:
		diceType = diceTypes[key]
		for _ in range(0,attacker.dice[key]):
			if random.randint(1,diceType.numSides) <= diceType.attack:
				totalAttack += 1

	totalDefense = 0
	for key in defender.dice:
		diceType = diceTypes[key]
		for _ in range(0,defender.dice[key]):
			if random.randint(1,diceType.numSides) <= diceType.defense:
				totalDefense += 1

	damage = max(0, totalAttack - totalDefense)

	if damage == 0:
		if Attr.counterstrike in defender.attrs:
			attacker.wounds += 1
		return

	if damage > defender.currentLife():
		damage = defender.currentLife()

	defender.wounds += damage
	if Attr.lifedrain in attacker.attrs and Attr.construct not in defender.attrs:
		attacker.wounds = max(0, attacker.wounds - damage)


def is_odd(x):
	return x % 2 != 0

def getStats(attacker, defender, numFights, maxTurns, scriptable):	
	outcomes = dict()
	for w in Winner:
		outcomes[w] = []

	for i in range(0,numFights):
		a = copy.copy(attacker)
		d = copy.copy(defender)
		winner, turns = fightToTheDeath(a, d, maxTurns)
		outcomes[winner].append(turns)

	wins = len(outcomes[Winner.attacker])
	losses = len(outcomes[Winner.defender])
	draws = len(outcomes[Winner.draw])

	if scriptable:
		output = dict()
		output["WINS"] = wins
		output["LOSSES"] = losses
		output["DRAWS"] = draws
		print(json.dumps(output))
	else:
		print("attacker ({}) winrate: {}%\n\tavg win on turn {}".format(
			attacker.name, 100 * wins/numFights, winsToAvgTurn(outcomes[Winner])))

		print("defender ({}) winrate: {}%\n\tavg win on turn {}".format(
			defender.name, 100 * losses/numFights, winsToAvgTurn(outcomes[Winner])))

		if draws > 0:
			print("drawrate (after {} turns): {}%".format(maxTurns, 100 * draws/numFights))
	

	if wins > losses:
		return True
	elif losses > wins:
		return False
	else:
		return None

def winsToAvgTurn(winTimes):
	if len(winTimes) == 0:
		return "N/A"
	return round(sum(winTimes)/len(winTimes))

def fightToTheDeath(initialAtacker, initialDefender, maxTurns):
	distance = max(initialAtacker.range, initialDefender.range) + 1
	#print("distance:",distance)
	for i in range(1,maxTurns+1):
		attacker = None
		defender = None
		if is_odd(i):
			attacker = initialAtacker
			defender = initialDefender
		else:
			attacker = initialDefender
			defender = initialAtacker

		#print("turn",i)
		if(distance > attacker.range):
			distance = max(1,distance - attacker.move, attacker.range)
			#print("{} moved.  dintance is now {}".format(attacker.name, distance))

		if(distance <= attacker.range):
			fight(attacker, defender)
			#print("{}({}) attacked {}({})".format(attacker.name, attacker.life, defender.name, defender.life))

		if initialDefender.currentLife() <= 0:
			return Winner.attacker, i
		elif initialAtacker.currentLife() <= 0:
			return Winner.defender, i

	return Winner.draw, maxTurns

diceTypes = None
with open("dice.json") as f:
	diceTypes = jsonpickle.decode(f.read())

parser = argparse.ArgumentParser(description='Fight two cards to the death')
parser.add_argument('card1', metavar='Card_1', type=str, help='the file path of card #1')
parser.add_argument('card2', metavar='Card_2', type=str, help='the file path of card #2')
parser.add_argument('-s','--scriptable', action="store_true", help='print output in a more easily parsable way')
parser.add_argument('-a', '--attack-only', action="store_true", help='attack only (don\'t run the simulation both ways)')

args = parser.parse_args()

card1 = None
with open(args.card1, 'rb') as f:
	card1 = pickle.load(f)

card2 = None
with open(args.card2, 'rb') as f:
	card2 = pickle.load(f)

config = None
with open("config.json") as f:
	config = jsonpickle.decode(f.read())

print()
getStats(card1, card2, config.numFights, config.maxTurns, args.scriptable)
print()
if not args.attack_only:
	getStats(card2, card1, config.numFights, config.maxTurns, args.scriptable)
	print()