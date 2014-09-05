#!/usr/bin/python3
import glob
import subprocess
import sys


cards = glob.glob('./*.card')

if ".\cardTemplate.card" in cards: 
	cards.remove(".\cardTemplate.card")

for attacker in cards:
	for defender in cards:
		print(attacker,defender)
		outcomes = subprocess.check_output([sys.executable, "cardfight.py",attacker,defender, "-s", "-a"])
		print(outcomes)