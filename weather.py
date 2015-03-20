#!/usr/bin/python
import subprocess 
import re 
import os 
import sys 
import time 
import grovepi
import smbus
import math
from grove_barometic_sensor import BMP085

#Gewitter 			#12
#Regen		 		#0
#vereinzelt Regen	#1
#wechselhaft		#2
#bedeckt			#3
#bewoelkt 			#4
#heiter    			#5
#sonnig 			#6
class Weather():
	global bmp
	global bus
	global backupFileLocationPress
	global backupFileLocationTrend
	global dht_sensor_port
	global tem_correction
	global moist_sensor_port
	global forecast_trend
	global forecast_max
	global forecast_min
	global forecast_storm
	forecast_trend = 3
	forecast_max = 6
	forecast_min = 0
	forecast_strom = 12
	dht_sensor_port = 7		# Connect the DHt sensor to port D7
	temp_correction = - 0.5   # correction of measured temperature
	moist_sensor_port = 0   # Connect the Moisture sensor to port A0
	bmp = BMP085(0x77, 1)
	bus = smbus.SMBus(1)    # I2C 1
	backupFileLocationPress="/home/pi/Wurmfarm/dataPressure.txt"
	backupFileLocationTrend="/home/pi/Wurmfarm/dataTrend.txt"

	def init(self):
		self.press = []
		i = 0
		press = self.getPressData()
		self.trendPress = self.getPressData()
		while i < 12:
			self.addPress(press)
			i = i + 1
		self.actTrend = 1	
		self.savePressToFile()
		self.actTrend = 3	
		self.saveTrendToFile()
		
	def __init__(self):
				
		if ((True == self.is_non_zero_file(backupFileLocationPress)) and (True == self.is_non_zero_file(backupFileLocationTrend))): 
			self.checkPress()
		else: 
			self.init()
			
		
	def is_non_zero_file(self,fpath):  
		return True if os.path.isfile(fpath) and os.path.getsize(fpath) > 0 else False
	def checkPress(self):
		file = open(backupFileLocationPress, 'r')
		for lines in file:
			items        = []
			items        = lines.split()
		file.close	
		actPress = self.getPressData()
		oldPress = int(items[0])
		deltaPress = actPress - oldPress
		#print actPress, "-", oldPress,"=",deltaPress
		if ( deltaPress <= -5 ):
			items[11] = actPress
			self.press = []
			i = 0
			while i < 11:
				items[i] = items[i+1]
				i = i + 1
			i = 0
			while i < 12:
				self.addPress(items[i])
				i = i + 1
			self.savePressToFile()
			return forecast_strom
		else:
			return self.checkTrend()
	def checkTrend(self):		
		file = open(backupFileLocationTrend, 'r')
		for lines in file:
			items        = []
			items        = lines.split()
		file.close	
		actPress = self.getPressData()
		actTrend = int(items[0])
		oldPress = int(items[1])
		deltaPress = actPress - oldPress
		self.deltaPress = deltaPress
		#print actTrend, actPress, "-", oldPress,"=",deltaPress
		if (deltaPress >= forecast_trend):
			if (actTrend <> forecast_max):
				self.actTrend = actTrend + 1
			self.trendPress = actPress
			self.saveTrendToFile()
			return self.actTrend
		if (deltaPress <= -forecast_trend):
			if (actTrend <> forecast_min):
				self.actTrend = actTrend - 1
			self.trendPress = actPress
			self.saveTrendToFile()
			return self.actTrend
		if (deltaPress > -forecast_trend and deltaPress < forecast_trend ):
			return actTrend			
		
	def addPress(self,press):
		self.press.append(press)
	def getList(self):
		return self.sensor
	def getTrend(self):
		if (self.deltaPress == 0):
			return "="
		if	(self.deltaPress > 0):
			return "+"
		if (self.deltaPress < 0):
			return "-"	
	def getBTempData(self):
		btemp = bmp.readTemperature()
		return btemp 
	def getPressData(self):
		pressure = bmp.readPressure()/100   # /100 -> hPa
		return pressure
	def getAltData(self):
		altitude = bmp.readAltitude(102000)
		return altitude
	def getMoistData(self):
		#moist = grovepi.analogRead(moist_sensor_port)
		return 0
	def getHumData(self):
		[ temp,hum ] = grovepi.dht(dht_sensor_port,3)
		return hum
	def getTempData(self):
		[ temp,hum ] = grovepi.dht(dht_sensor_port,3)
		return temp		
	def savePressToFile(self):
		file = open(backupFileLocationPress, 'w')
		for press in self.press:
			data = str(press) + " "
			file.write(data)
		file.close 
	def saveTrendToFile(self):
		file = open(backupFileLocationTrend, 'w')
		data = str(self.actTrend) + " " + str(self.trendPress)
		file.write(data) 
		file.close
	def getDewPoint(self):
		t = self.getTempData()
		relF = self.getHumData()
		# Ortshoehe
		hNN = 114
		pNN = self.getPressData()
		#Luftdruck Ortshoehe
		pO= pNN-(hNN/(8.7 - hNN * 0.0005))
		#Luftdicht
		LD = (0.349 * pO) / (273.15 + t)
		#Saettigungsdampfdruck
		pS= 6.1078 * (10**(t * 7.5/(t + 273.15)))
		#Saettigungsdefizit
		Sd = pS - ((pS/100) * relF)
		#Dampfdruck
		pD = pS - Sd
		#Taupunkt
		TP = (234.67 * (math.log(pD) / math.log(10)) - 184.2) / (8.233 - ( math.log(pD) / (math.log(10))))
		#spez Luftfeuchte gramm/Kubikmeter Luft
		spezF = ((pD/pO)*0.622)*10**3
		self.spezF =spezF* LD
		#Saettigungsfeuchte gramm/Kubikmeter Luft 
		sattF = (spezF/relF)*100
		self.sattF = sattF * LD
		return TP
	def getspezF(self):
		return self.spezF
	def getsattF(self):
		return self.sattF



