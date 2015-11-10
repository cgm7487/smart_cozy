#!/usr/bin/env python

# Gene Cheng(cgm). Nov. 2015
# This application uses some functions from the https://github.com/msaunby/ble-sensor-pi

import pexpect
import sys
import time

import csv as csv

from daemon import runner

from pyonep import onep

def floatfromhex(h):
	t = float.fromhex(h)
	if t > float.fromhex('7FFF'):
		t = -(float.fromhex('FFFF') - t)
		pass
	return t


# This algorithm borrowed from 
# http://processors.wiki.ti.com/index.php/SensorTag_User_Guide#Gatt_Server
# which most likely took it from the datasheet.  I've not checked it, other
# than noted that the temperature values I got seemed reasonable.
#
def calcTmpTarget(objT, ambT):
	m_tmpAmb = ambT/128.0
	Vobj2 = objT * 0.00000015625
	Tdie2 = m_tmpAmb + 273.15
	S0 = 6.4E-14            # Calibration factor
	a1 = 1.75E-3
	a2 = -1.678E-5
	b0 = -2.94E-5
	b1 = -5.7E-7
	b2 = 4.63E-9
	c2 = 13.4
	Tref = 298.15
	S = S0*(1+a1*(Tdie2 - Tref)+a2*pow((Tdie2 - Tref),2))
	Vos = b0 + b1*(Tdie2 - Tref) + b2*pow((Tdie2 - Tref),2)
	fObj = (Vobj2 - Vos) + c2*pow((Vobj2 - Vos),2)
	tObj = pow(pow(Tdie2,4) + (fObj/S),.25)
	tObj = (tObj - 273.15)
	print "%.2f C" % tObj
	return tObj

def calcHum(rawT, rawH):
    # -- calculate temperature [deg C] --
    t = -46.85 + 175.72/65536.0 * rawT

    rawH = float(int(rawH) & ~0x0003); # clear bits [1..0] (status bits)
    # -- calculate relative humidity [%RH] --
    rh = -6.0 + 125.0/65536.0 * rawH # RH= -6 + 125 * SRH/2^16
    return (t, rh)

def read_temperature_from_sensortag(tool):

	tool.sendline('char-read-hnd 0x25')
	tool.expect('descriptor: .*') 
	rval = tool.after.split()
	objT = floatfromhex(rval[2] + rval[1])
	ambT = floatfromhex(rval[4] + rval[3])
	#print rval
	return calcTmpTarget(objT, ambT)

def read_humidility_from_sensortag(tool):

	tool.sendline('char-read-hnd 0x3b')
	tool.expect('descriptor: .*')

	rval = tool.after.split()
	rawT = floatfromhex(rval[2] + rval[1])
	rawH = floatfromhex(rval[4] + rval[3])
	(t, rh) = calcHum(rawT, rawH)

	rh = rh if rh > 0 else rh * -1

	return rh

def open_the_window(tool):
	print 'open the window'
	tool.sendline('char-write-cmd 0x0025 02')
	time.sleep(1)
	tool.sendline('char-write-cmd 0x0025 ff')

def close_the_window(tool):
	print 'close the window'
	tool.sendline('char-write-cmd 0x0025 01')
	time.sleep(1)
	tool.sendline('char-write-cmd 0x0025 ff')

class BleController:
	def __init__(self):
		self.stdin_path = '/dev/null'
		self.stdout_path = '/dev/tty'
		self.stderr_path = '/dev/tty'
		self.pidfile_path = '/tmp/bleController.pid'
		self.pidfile_timeout = 5

		self.onepInst = onep.OnepV1()
		self.windowStat = self.preWindowStat = 1
		self.cik = 'c7daa5a76badd48e8b8a7b71560670f66ba23c4b'
		self.indoorComfortIndex = 3

	def connectToDevice(self):

        sensorTagAddr = sys.argv[1]
		motorAddr = sys.argv[2]

		self.tool = pexpect.spawn('gatttool -b ' + sensorTagAddr + ' --interactive')
		self.tool.expect('\[LE\]>')
		print "Preparing to connect. You might need to press the side button..."
		self.tool.sendline('connect')
		self.tool.expect('Connection successful')
		self.tool.sendline('char-write-cmd 0x29 01')
		self.tool.expect('\[LE\]>')

		self.tool.sendline('char-write-cmd 0x3f 01')
		self.tool.expect('\[LE\]>')

		print 'sensorTag connect success'

		self.tool2 = pexpect.spawn('gatttool -b ' + motorAddr + ' --interactive')
		self.tool2.expect('\[LE\]>')
		self.tool2.sendline('connect')
		self.tool2.expect('Connection successful')
		print 'motor connect success'

	def run(self):

		while True:
			time.sleep(1)
			tempVal = read_temperature_from_sensortag(tool)
			rh = read_humidility_from_sensortag(tool)

			print 'indoor temperature = %f' % tempVal
			print 'indoor humilidity = %f' % rh
			self.onepInst.write(self.cik,
					{"alias": "indoor_temp"},
					tempVal,
					{})

			self.onepInst.write(self.cik,
					{"alias": "indoor_humi"},
					rh,
					{})

			isok, response = self.onepInst.read(self.cik, {'alias': 'manual_trigger'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})

			if isok:
				manualTrigger = response[0][1]
			else:
				manualTrigger = 0
				isok, response = self.onepInst.read(self.cik, {'alias': 'indoor_comfort_index'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})
				if isok:
					self.indoorComfortIndex = response[0][1]
				else:
					continue

	 		print 'comfortable index = %f' % self.indoorComfortIndex

			if manualTrigger == 1:
				isok, response = self.onepInst.read(self.cik, {'alias': 'manual_window_status'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})
				if isok:
					self.windowStat = response[0][1]

					if self.windowStat != self.preWindowStat:

						fd = open('train.csv', 'ab')
						csvFileObj = csv.writer(fd)

						if self.windowStat == 1:
							adjVal = (self.indoorComfortIndex - 1) if (self.indoorComfortIndex - 1) > 0 else 0
							csvFileObj.writerow([float(tempVal), float(rh), float(0), adjVal])
						else:
							adjVal = (self.indoorComfortIndex + 1) if (self.indoorComfortIndex + 1) < 5 else 5
							csvFileObj.writerow([float(tempVal), float(rh), float(0), adjVal])

						fd.close()

			else:
				if self.indoorComfortIndex > 3:
					print 'change window status to 0'
					self.windowStat = 0
				else:
					print 'change window status to 1'
					self.windowStat = 1

			isok, response = self.onepInst.read(self.cik, {'alias': 'outdoor_pm25'}, {'limit': 1, 'sort': 'desc', 'selection': 'all'})
			if isok:
				pm25 = response[0][1]
				if pm25 > 70:
					self.windowStat = 1

			print 'window status = %d' % self.windowStat
			print 'pre-window status = %d' % self.preWindowStat
			if self.windowStat != self.preWindowStat:
				print 'try to control window'
				if self.windowStat > 0:
					close_the_window(tool2)
				else:
					open_the_window(tool2)
				self.preWindowStat = self.windowStat


bleController = BleController()
bleController.connectToDevice()
daemonRunner = runner.DaemonRunner(bleController)
daemonRunner.do_action()


