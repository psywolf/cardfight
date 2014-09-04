#!/usr/bin/python3
import random
import copy
import enum
import jsonpickle
import pickle
import argparse
from sharedlib import Attr, Card

class Config:
	def __init__(self, numFights, maxTurns):
		self.numFights = numFights
		self.maxTurns = maxTurns

class Die:
	def __init__(self, attack, defense, numSides=12):
		self.attack = attack
		self.defense = defense
		self.numSides = numSides


class Winner(enum.Enum):
	attacker = 1
	defender = -1
	draw = 0

def fight(attacker, defender):
	totalAttacks = 0
	for key in attacker.dice:
		diceType = diceTypes[key]
		for _ in range(0,attacker.dice[key]):
			if random.randint(1,diceType.numSides) <= diceType.attack:
				totalAttacks += 1

	totalDefense = 0
	for key in defender.dice:
		diceType = diceTypes[key]
		for _ in range(0,defender.dice[key]):
			if random.randint(1,diceType.numSides) <= diceType.defense:
				totalDefense += 1

	damage = max(0, totalAttacks - totalDefense)

	if damage == 0:
		return

	if damage > defender.currentLife():
		damage = defender.currentLife()

	defender.wounds += damage
	if Attr.lifedrain in attacker.attrs and Attr.construct not in defender.attrs:
		#print("healing")
		attacker.wounds = max(0, attacker.wounds - damage)


def is_odd(x):
	return x % 2 != 0

def getStats(attacker, defender, numFights, maxTurns):	
	outcomes = dict()
	for w in Winner:
		outcomes[w] = []

	for i in range(0,numFights):
		a = copy.copy(attacker)
		d = copy.copy(defender)
		winner, turns = fightToTheDeath(a, d, maxTurns)
		outcomes[winner].append(turns)

	wins = len(outcomes[Winner.attacker])
	print("attacker ({}) winrate: {}%\n\tavg win on turn {}".format(
		attacker.name, 100 * wins/numFights, winsToAvgTurn(outcomes[Winner.attacker])))

	losses = len(outcomes[Winner.defender])
	print("defender ({}) winrate: {}%\n\tavg win on turn {}".format(
		defender.name, 100 * losses/numFights, winsToAvgTurn(outcomes[Winner.defender])))

	draws = len(outcomes[Winner.draw])
	if draws > 0:
		print("drawrate (after {} turns): {}%".format(maxTurns, 100 * draws/numFights))

def winsToAvgTurn(winTimes):
	if len(winTimes) == 0:
		return "N/A"
	return round(sum(winTimes)/len(winTimes))

def fightToTheDeath(initialAtacker, initialDefender, maxTurns):
	for i in range(1,maxTurns+1):
		attacker = None;
		defender = None
		if is_odd(i):
			attacker = initialAtacker
			defender = initialDefender
		else:
			attacker = initialDefender
			defender = initialAtacker

		fight(attacker, defender)
		

		#print("turn {}: {}({}) attacked {}({}) for {} damage".format(i, attacker.name, attacker.life, defender.name, defender.life, damage))

		if initialDefender.currentLife() <= 0:
			return Winner.attacker, i
		elif initialAtacker.currentLife() <= 0:
			return Winner.defender, i

	return Winner.draw, maxTurns

diceTypes = None
with open("dice.json") as f:
	diceTypes = jsonpickle.decode(f.read())
"""
diceTypes = {
	"red": Die(7,2),
	"black": Die(6,3),
	"orange": Die(5,3),
	"green": Die(5,4),
	"white": Die(4,5),
	"purple": Die(4,4)
}
"""

parser = argparse.ArgumentParser(description='Fight two cards to the death')
parser.add_argument('card1', metavar='Card_1', type=str, help='the file path of card #1')
parser.add_argument('card2', metavar='Card_2', type=str, help='the file path of card #2')

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
getStats(card1, card2, config.numFights, config.maxTurns)
print()
getStats(card2, card1, config.numFights, config.maxTurns)
print()