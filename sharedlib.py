from enum import Enum
class Attr(Enum):
	lifedrain = "Life Drain"
	haste = "Haste"
	ethereal = "Ethereal"
	counterstrike = "Counterstrike"
	doubleAttack = "Double Attack"
	damageReduction = "Damage Reduction"
	rampage = "Rampage"
	construct = "Construct"



class Card:
	def __init__(self, name, life, attackRange, move, dice, attrs):
		self.name = name
		self.life = life
		self.range = attackRange
		self.move = move
		self.dice = dice
		self.attrs = attrs
		self.wounds = 0

	def __str__(self):
		return str(vars(self))

	def currentLife(self):
		return max(0, self.life - self.wounds)