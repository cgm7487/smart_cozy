#!/usr/bin/env python

# Gene Cheng(cgm). Nov. 2015

import csv as csv
import numpy as np
import time
from sklearn.naive_bayes import GaussianNB
from daemon import runner

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
	clf.fit(trainingData, labelData)
	print 'learning finished'

class LearningEngine():
	def __init__(self):
		self.stdin_path = '/dev/null'
		self.stdout_path = '/dev/tty'
		self.stderr_path = '/dev/tty'
		self.pidfile_path = '/tmp/learnEnging.pid'
		self.pidfile_timeout = 5

		self.clf = GaussianNB()

		start_to_learn(self.clf)

		self.onepInst = onep.OnepV1()

		self.cik = 'c7daa5a76badd48e8b8a7b71560670f66ba23c4b'

		self.learnCnt = 0

	def run(self):

		while True:
			self.learnCnt += 1

			if self.learnCnt == 10:
				self.learnCnt = 0
				start_to_learn(self.clf)

			while True:
				print 'try to calc index'
				isok, response = self.onepInst.read(self.cik, {'alias': 'indoor_temp'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})

				if isok != True:
					print 'indoor temp error'
					break

				indoorTemp = response[0][1]

				isok, response = self.onepInst.read(self.cik, {'alias': 'indoor_humi'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})

				if isok != True:
					print 'indoor humi error'
					break

				indoorHumi = response[0][1]
				indoorComfortIndex = self.clf.predict([[indoorTemp, indoorHumi, 0.0]])

				print indoorComfortIndex
				self.onepInst.write(self.cik,
					{"alias": "indoor_comfort_index"},
					indoorComfortIndex[0],
					{})
				break

			while True:
				isok, response = self.onepInst.read(self.cik, {'alias': 'outdoor_curTemp'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})
				if isok != True:
					break

				outdoorTemp = response[0][1]

				isok, response = self.onepInst.read(self.cik, {'alias': 'outdoor_curHumidity'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})
				if isok != True:
					break

				outdoorHumi = response[0][1]

				isok, response = self.onepInst.read(self.cik, {'alias': 'outdoor_windspeed'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})
				if isok != True:
					break

				wind = response[0][1]

				outdoorComfortIndex = self.clf.predict([[outdoorTemp, outdoorHumi, wind]])

				print outdoorComfortIndex
				self.onepInst.write(self.cik,
					{"alias": "outdoor_comfort_index"},
					outdoorComfortIndex[0],
					{})
				break

			time.sleep(10)

learningEngine = LearningEngine()
daemonRunner = runner.DaemonRunner(learningEngine)
daemonRunner.do_action()


