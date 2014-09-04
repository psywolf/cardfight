#!/usr/bin/python3
import argparse
import csv
from sharedlib import Attr, Card
from pprint import pprint
import pickle

def buildAttrs(row):
	attrs = dict()
	for attr in Attr:
		attrVal = row[col[attr.value]]
		if attrVal != "":
			attrs[attr] = attrVal
	return attrs

def buildDice(row):
	dice = dict()
	for colName in col:
		words = colName.split()
		if len(words) > 1 and words[1] == "Dice":
			diceCount = row[col[colName]]
			if diceCount not in ("", "0"):
				dice[words[0].lower()] = int(diceCount)
	return dice

parser = argparse.ArgumentParser(description='generate card files from excel spreadsheet')
parser.add_argument('spreadsheet', metavar='spreadsheet.csv', type=str, help='the file path of CSV format spreadsheet')
#parser.add_argument('-e','--excel', metavar='spreadsheet.csv', type=bool, help='the file path of CSV format spreadsheet')

args = parser.parse_args()


col = dict()

with open(args.spreadsheet, newline='') as csvfile:
	reader = csv.reader(csvfile, 'excel')

	#use header row to set up col dict
	header = next(reader, None)
	index = 0
	for colName in header:
		col[colName] = index
		index += 1

	rowNum = 2
	for row in reader:
		rowNum +=1
		if(len(row) == 0):
			continue
		card = Card(row[col["Name"]],
				int(row[col["Life"]]),
				int(row[col["Range"]]),
				int(row[col["Move"]]),
				buildDice(row),
				buildAttrs(row))

		with open(card.name + '.card', 'wb') as f:
			#f.write(jsonpickle.encode(card))
			pickle.dump(card,f)


