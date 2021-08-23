'''
Created on 02.02.2021

@author: Sascha Holzhauer
'''
from time import sleep
from random import Random
from base64 import b64encode
import os
import sys
import requests
import json
import datetime as dt
import logging
from util import *
from math import ceil

# namedtuple not used because of issues with keys ("in") and immutability
#def smdDecoder(smdDict):
#    return namedtuple('X', smdDict.keys())(*smdDict.values())

class DsoTestClient(object):
    '''
    classdocs
    '''
    
    def __init__(self, flexserver, loglevel="DEBUG", productId=3, flexDemandAdvance=1000*60*60, 
                 username = "username = secrets_local.flexserver_username", password=secrets_local.flexserver_password):
        '''
        Constructor
        '''
        self.productId = productId
        self.flexDemandAdvance = flexDemandAdvance
        
        self.active = True
        
        self.username = username
        userAndPass = b64encode((self.username + ":" + password).encode()).decode("ascii")
        self.authorisation = "Basic %s" % userAndPass
        
        self.flexserver = flexserver
        self.smdPrototypeFilename = 'smdProto.json'
        self.sendCounter = 0
        
        self.maxQuantity = 100
        self.seed = 1
        self.ran = Random(self.seed)
        self.tinfo = None
        self.pinfo = None
        
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        logging.basicConfig(level=numeric_level)

    def run(self):
        # read time information and schedule next flex demand message
        logging.info("Starting DsoTestClient...")
        while(self.active):
            sleeptime = self.getNextSleepDuration()
            logging.info("Sleeping for " + (dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds = sleeptime)).strftime("%H:%M:%S"))
            sleep(sleeptime/1000)
            self.sendFlexDemand()
            
    def getHeaders(self):
        headers = {'Content-type': 'application/json', 'Accept': '*/*', 
           "Accept-Encoding": 'gzip, deflate, br', "Authorization": self.authorisation}
        return headers

    def sendFlexDemand(self):
        smdPrototype = open(os.path.join(os.path.dirname(__file__), self.smdPrototypeFilename))
        smd = json.loads(smdPrototype.read())
        smdPrototype.close()
        
        self.getTimeInformation()
        
        smd['mRID'] = "TestDsoFlexDemandSmd" + "{:04.0f}".format(self.sendCounter)
        logging.info("Send Flex demand (" + smd['mRID'] + ")...")
        
        # determine next delivery:
        auctionDeliverySpan = self.pinfo['auctionDeliverySpan']
        firstDeliveryPeriodStart = self.pinfo['firstDeliveryPeriodStart']
        simMillisNow = self.tinfo['currentSimulationTime']
        openingTime = durationString2Millis(self.pinfo['openingTime'])
             
        nextDayDeliveryStart = dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds = ceil((simMillisNow - firstDeliveryPeriodStart) / auctionDeliverySpan) * auctionDeliverySpan +
            firstDeliveryPeriodStart)
        
        logging.debug("Next delivery period start: " + nextDayDeliveryStart.strftime("%Y-%m-%dT%H:%M:%S"))
       
        smd['sender_MarketParticipant']['mRID']['mRID'] = self.username
        smd['createdDateTime'] = self.nowSim.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        smd['timeInterval'] = nextDayDeliveryStart.strftime("%Y-%m-%dT%H:%M:%S+00:00") + "/" \
            + (nextDayDeliveryStart + dt.timedelta(milliseconds = auctionDeliverySpan)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        for ts in smd['timeSeries']:
            points = []
            ts['in']['mRID']['mRID'] = self.username
            for i in range(0,96):
                points.append({
                        "quantity": self.ran.random() * self.maxQuantity ,
                        "position": i
                    })
            ts['period']['points'] = points 
            ts['period']['timeInterval'] = smd['timeInterval']
            logging.debug(ts['mRID'] + ": " + json.dumps(ts['period'], indent=4, sort_keys=False))
        

        response = requests.post('https://' + self.flexserver + '/api/dso/cim/flexdemand', 
                                 json=smd, headers=self.getHeaders(), verify=False)
        
        logging.info("Status code of sending flex demand: " + str(response.status_code))
        logging.debug(response.content)
        self.sendCounter += 1

    def getTimeInformation(self):
        logging.info("Requesting time information...")
        headers = {'Content-type': 'application/json', 'Accept': '*/*', 
                   "Accept-Encoding": 'gzip, deflate, br', "Authorization":self.authorisation}
        response = requests.get('https://' + self.flexserver + '/api/config-time', headers=headers, verify=False)
        logging.info("Status code of time information request: " + str(response.status_code))
        self.tinfo = json.loads(response.content)
        self.nowSim = dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds = self.tinfo['currentSimulationTime'])
        self.nextDayStart = self.nowSim.replace(day=self.nowSim.day, hour=0, minute=0, second = 0) + dt.timedelta(days=1)
        logging.debug(json.dumps(self.tinfo, indent=4, sort_keys=False))

    def getNextSleepDuration(self):
        self.getTimeInformation()
        logging.info("Requesting product information...")
        response = requests.get('https://' + self.flexserver + '/api/config-products', headers=self.getHeaders(), verify=False)
        logging.info("Status code of product information request: " + str(response.status_code))
        if response.content.decode('utf-8') == "":
            logging.error("Probably, the market has not been started (empty active product list)!")
            sys.exit()
        pInfos = json.loads(response.content.decode('utf-8'))
        logging.debug(json.dumps(pInfos, indent=4, sort_keys=False))

        for pi in pInfos['tradedProducts']:
            logging.debug(pi)
            if pi['productId'] == self.productId:
                self.pinfo = pi
                break
        
        auctionDeliverySpan = self.pinfo['auctionDeliverySpan']
        firstDeliveryPeriodStart = self.pinfo['firstDeliveryPeriodStart']
        simMillisNow = self.tinfo['currentSimulationTime']
        openingTime = durationString2Millis(self.pinfo['openingTime'])
        
        logging.debug("Simulation now: " +  str(dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds = simMillisNow)))
        logging.debug("First Delivery Period Start: " + str(dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds = firstDeliveryPeriodStart)))
        logging.debug("Opening time: " + (dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds = openingTime)).strftime("%H:%M:%S"))
        logging.debug("AuctionDeliverySpan: " + (dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds = auctionDeliverySpan)).strftime("%H:%M:%S"))
        
        # get waiting time for next opening time - advance
        # -((simNow - firstDeliveryPeriodStart) mod auctionDeliverySpan) + auctionDeliverySpan - openingTime - advance
        waitMillis = -((simMillisNow - (firstDeliveryPeriodStart - openingTime - self.flexDemandAdvance)) % auctionDeliverySpan) + auctionDeliverySpan 
        logging.debug("Waiting duration: " + dt.datetime.utcfromtimestamp(waitMillis / (1000 * self.tinfo['simulationFactor'])).strftime("%H:%M:%S"))
       
        return waitMillis / self.tinfo['simulationFactor']
        
    def setInactive(self):
        self.active = False
        