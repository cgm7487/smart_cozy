#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from pyonep import onep
import HTMLParser
import json
import urllib2
import time

class weatherParser(HTMLParser.HTMLParser):
    data = {}

    def __init__(self):
        self.processingTag  = None
        self.processingData = None
        self.handledTags    = ['td']
        self.handledData    = [
            '時間', '天氣狀況', '溫度(℃)', '相對溼度', '降雨機率'
        ]
        HTMLParser.HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag in self.handledTags:
            self.processingTag = tag

        if tag == 'img':
            if self.processingData == '天氣狀況':
                for name, value in attrs:
                    if name == 'alt':
                        if self.processingData in self.data:
                            self.data[ self.processingData ].append(value)
                        else:
                            self.data[ self.processingData ] = [value]

    def handle_endtag(self, tag):
        if tag == self.processingTag:
            self.processingTag = None

        if tag == 'tr':
            self.processingData = None

    def handle_data(self, data):
        if self.processingTag:
            if self.processingData:
                if self.processingData in self.data:
                    self.data[ self.processingData ].append(data)
                else:
                    self.data[ self.processingData ] = [data]
            else:
                if data in self.handledData:
                    self.processingData = data

    def dumpData(self):
        print "data: %s\n\n" % (self.data)

        for key in self.handledData:
            print "%s: %s\n" % (key, self.data[key])

class naunnanWeather:
    pm25      = 0.0
    windSpeed = 0.0
    curTemp   = 0.0
    CurHum    = 0.0
    preTemp   = 0.0
    preHum    = 0.0
    curStat   = ''
    preStat   = ''
    CIK       = 'c7daa5a76badd48e8b8a7b71560670f66ba23c4b'

    # Parse HTML documeent to get data wanted and return as a Json object
    def _parseCwbHTML(self, htmlData):
        return None

    def _getWeatherData(self, weatherType):
        if weatherType == 'epa':
            f = urllib2.urlopen('http://opendata.epa.gov.tw/ws/Data/AQX/?$filter=SiteName%20eq%20%27%E5%BF%A0%E6%98%8E%27&$orderby=SiteName&$skip=0&$top=1000&format=json')
            return json.loads( f.read() )[0]
        elif weatherType == 'cwb':
            f2 = urllib2.urlopen('http://www.cwb.gov.tw/V7/forecast/town368/3Hr/6600400.htm')
            wp = weatherParser()
            wp.feed( f2.read() )

            return wp.data
        else:
            return None

    # Download weather information from EPA
    def getWeatherInfo(self):
        epaData        = self._getWeatherData('epa')
        self.pm25      = epaData['PM2.5']
        self.windSpeed = epaData['WindSpeed']

        cwbData      = self._getWeatherData('cwb')
        self.curTemp = cwbData['溫度(℃)'][0]
        self.curHum  = cwbData['相對溼度'][0]
        self.curStat = cwbData['天氣狀況'][0]
        self.preTemp = cwbData['溫度(℃)'][1]
        self.preHum  = cwbData['相對溼度'][1]
        self.preStat = cwbData['天氣狀況'][1]

    def dumpData(self):
        print "pm25: %s" % (nw.pm25)
        print "windSpeed: %s" % (nw.windSpeed)
        print "curTemp: %s" % (nw.curTemp)
        print "preTemp: %s" % (nw.preTemp)
        print "curHum: %s" % (float(nw.curHum.strip('%')) / 100)
        print "preHum: %s" % (float(nw.preHum.strip('%')) / 100)
        print "curStat: %s" % (nw.curStat)
        print "preStat: %s" % (nw.preStat)

    # Write data to OneP
    def updateWeatherDataToCloud(self):
        # Connect to Oneplatform
        oc = onep.OnepV1()
        oc.write(self.CIK, {"alias": "outdoor_pm25"}, self.pm25)
        oc.write(self.CIK, {"alias": "outdoor_windspeed"}, self.windSpeed)
        oc.write(self.CIK, {"alias": "outdoor_curTemp"}, self.curTemp)
        oc.write(self.CIK, {"alias": "outdoor_preTemp"}, self.preTemp)
        oc.write(self.CIK, {"alias": "outdoor_curHumidity"}, self.curHum.strip('%'))
        oc.write(self.CIK, {"alias": "outdoor_preHumidity"}, self.preHum.strip('%'))
        oc.write(self.CIK, {"alias": "outdoor_curStat"}, self.curStat)
        oc.write(self.CIK, {"alias": "outdoor_preStat"}, self.preStat)

if __name__ == '__main__':
    nw = naunnanWeather()
    while True:
        time.sleep(60)
        nw.getWeatherInfo()
        nw.dumpData()
        nw.updateWeatherDataToCloud()
