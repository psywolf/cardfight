#!/usr/bin/python3
import random
import copy
import enum
import jsonpickle
import pickle
import argparse
from sharedlib import Attr, Card, Config
import json

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
	winner = attack(attacker, defender)
	if winner != None:
		return winner

	if Attr.doubleAttack in attacker.attrs:
		return attack(attacker, defender)

def is_rampage():
	redDie = diceTypes["red"]
	greenDie = diceTypes["green"]
	return random.randint(1, redDie.numSides) <= redDie.mundane or random.randint(1, greenDie.numSides) <= greenDie.mundane

def calculateDamage(attacker, defender):
	if Attr.ethereal in defender.attrs and roll({"black": 2}, "magic") > 0:
		return 0

	totalAttack = roll(attacker.dice, "attack")

	totalDefense = roll(defender.dice, "defense")

	if Attr.damageReduction in defender.attrs:
		totalDefense += 1

	damage = max(0, totalAttack - totalDefense)

	if Attr.anaconda in attacker.attrs:
		damage += roll({"orange": damage}, "mundane")

	return damage

def roll(dice, successSide):
	total = 0
	for key in dice:
		diceType = diceTypes[key]
		for _ in range(0,dice[key]):
			if random.randint(1,diceType.numSides) <= getattr(diceType,successSide):
				total += 1
	return total

def attack(attacker, defender):
	damage = None
	if Attr.theroll in defender.attrs:
		damage = 1
	else:
		damage = calculateDamage(attacker, defender)
		if Attr.magus in attacker.attrs and damage == 0:
			damage = roll({"orange":1}, "magic")
		else:
			if damage == 0:
				if Attr.counterstrike in defender.attrs:
					attacker.wounds += 1
			else:
				if Attr.gorgon in attacker.attrs and roll(attacker.dice, "magic") >= 2:
					return attacker

				if damage > defender.currentLife():
					damage = defender.currentLife()

				if Attr.lifedrain in attacker.attrs and Attr.construct not in defender.attrs:
					attacker.wounds = max(0, attacker.wounds - damage)

	defender.wounds += damage
	if defender.currentLife() <= 0:
		return attacker

	if attacker.currentLife() <= 0:
		return defender

	return None


def is_odd(x):
	return x % 2 != 0

def getStats(attacker, defender, numFights, maxTurns, scriptable):	
	outcomes = dict()
	for w in Winner:
		outcomes[w] = []

	for i in range(0,numFights):
		a = copy.copy(attacker)
		d = copy.copy(defender)
		winner, turns = fightToTheBitterEnd(a, d, maxTurns)

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
			attacker.name, 100 * wins/numFights, winsToAvgTurn(outcomes[Winner.attacker])))

		print("defender ({}) winrate: {}%\n\tavg win on turn {}".format(
			defender.name, 100 * losses/numFights, winsToAvgTurn(outcomes[Winner.defender])))

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

def fightToTheBitterEnd(attacker, defender, maxTurns):
	w, t = fightToTheDeath(attacker, defender, maxTurns)

	deadCard = None
	winCard = None
	if w == Winner.attacker:
		winCard = attacker
		deadCard = defender
	elif w == Winner.defender:
		winCard = defender
		deadCard = attacker

	if deadCard != None and (Attr.isle in deadCard.attrs or (Attr.wyrm in deadCard.attrs and winCard.currentLife() <= 1)):
		return Winner.draw, t

	return w, t

def takeTurn(attacker, defender, distance):
	if Attr.theroll in attacker.attrs:
		attacker.wounds += 1
		if attacker.currentLife() <= 0:
			return defender, distance
	#print("turn",i)
	if distance > attacker.range:
		distance = max(1,distance - attacker.move, attacker.range)
		#print("{} moved.  dintance is now {}".format(attacker.name, distance))

	if distance > attacker.range:
		return None, distance

	winner = fight(attacker, defender)
	#print("{}({}) attacked {}({})".format(attacker.name, attacker.life, defender.name, defender.life))

	if winner != None:
		return winner, distance

	if Attr.falconer in attacker.attrs and defender.range + defender.move < distance + attacker.move:
		#move just out of reach
		distance = defender.range + defender.move + 1

	return None, distance

def fightToTheDeath(initialAttacker, initialDefender, maxTurns):
	distance = max(initialAttacker.range, initialDefender.range) + 1
	#print("distance:",distance)
	winner = None
	i = 1
	for i in range(1,maxTurns+1):
		attacker = None
		defender = None

		if is_odd(i):
			attacker = initialAttacker
			defender = initialDefender
		else:
			attacker = initialDefender
			defender = initialAttacker

		winner, distance = takeTurn(attacker, defender, distance)
		if winner != None:
			break

		if Attr.theroll in attacker.attrs or (Attr.rampage in attacker.attrs and is_rampage()):
			winner, distance = takeTurn(attacker, defender, distance)
			if winner != None:
				break


	if winner == None:
		return Winner.draw, i
	elif winner.name == initialAttacker.name:
		return Winner.attacker, i
	else:
		return Winner.defender, i


if __name__ == '__main__':
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