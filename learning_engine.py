#!/usr/bin/env python

# Gene Cheng(cgm). Nov. 2015

import csv as csv
import numpy as np
import time
#from sklearn import svm
from sklearn.naive_bayes import GaussianNB

from pyonep import onep

def start_to_learn(clf):
	csvFileObj = csv.reader(open(('train.csv'), 'rb'))
	data = []
	for row in csvFileObj:
		data.append(row)

	data = np.array(data)

	trainingData = data[0::, 0:3].astype(np.float)
	labelData = data[0::, 3].astype(np.float)

	print 'start to learn'
#	clf = svm.SVC()
	clf.fit(trainingData, labelData)
	print 'learning finished'
#	print clf.predict([[12., 56., 2.]])

def main():
	#clf = svm.SVC()
	clf = GaussianNB()

	start_to_learn(clf)

	onepInst = onep.OnepV1()

	#print clf.predict([[28.0, 72, 0.7]])

	cik = 'c7daa5a76badd48e8b8a7b71560670f66ba23c4b'

	learnCnt = 0
	while True:
		time.sleep(10)

		learnCnt += 1

		if learnCnt == 10:
			learnCnt = 0
			start_to_learn(clf)

		while True:
			print 'try to calc index'
			isok, response = onepInst.read(cik, {'alias': 'indoor_temp'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})

			if isok != True:
				print 'indoor temp error'
				break

			indoorTemp = response[0][1]

			isok, response = onepInst.read(cik, {'alias': 'indoor_humi'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})

			if isok != True:
				print 'indoor humi error'
				break

			indoorHumi = response[0][1]
			indoorComfortIndex = clf.predict([[indoorTemp, indoorHumi, 0.0]])

			print indoorComfortIndex
			onepInst.write(cik,
				{"alias": "indoor_comfort_index"},
				indoorComfortIndex[0],
				{})
			break

		while True:
			isok, response = onepInst.read(cik, {'alias': 'outdoor_curTemp'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})
			if isok != True:
				break

			outdoorTemp = response[0][1]

			isok, response = onepInst.read(cik, {'alias': 'outdoor_curHumidity'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})
			if isok != True:
				break

			outdoorHumi = response[0][1]

			isok, response = onepInst.read(cik, {'alias': 'outdoor_windspeed'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})
			if isok != True:
				break

			wind = response[0][1]

			outdoorComfortIndex = clf.predict([[outdoorTemp, outdoorHumi, wind]])

			print outdoorComfortIndex
			onepInst.write(cik,
				{"alias": "outdoor_comfort_index"},
				outdoorComfortIndex[0],
				{})
			break

if __name__ == "__main__":
	main()