'''
This file is part of INES FLEX - 
INES (Integrated Energy Systems) FLexibility Energy eXchange

INES FLEX is free software: You can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

INES FLEX is distributed in the hope that it will be useful, but 
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

You should have received a copy of the GNU Lesser General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

Copyright (C) 2021
Department of Integrated Energy Systems, University of Kassel,
Kassel, Germany

---

The DSO test client request time information from the flex server and
passes flex demand to it accordingly, either based on given quantity file
or random if quantity is not available for requested interval.

Required modules: see requirements.txt

Relevant Env. Vars.:

DSO_PARAM_FILENAME (default: ../params/dso_parameters.csv)
DSO_PARAM_ID (default: 1)
DSO_PRODUCTID (default: 3; only considered when not passed and not in params file)
DSO_DEMANDCURVE (default: 1; only considered when not in params file)
DSO_PROTOTYPE_FILENAME (default: smdProto.json)
DSO_QUANTITY_FILENAME (default: ../data/time_series_15min_singleindex_LoadSolarWind_50Hz_JulySep2020.csv)
DSO_QUANTITY_START (default: 2020-08-17)
DSO_QUANTITY_END (default: 2020-08-28)
DSO_QUANTITY_FACTOR (default: 0.01; only considered when not in params file)
---

Created on 02.02.2021

@author: Sascha Holzhauer
'''

from time import sleep
from random import Random
from base64 import b64encode
import numpy as np
import os
import sys
import requests
from requests.exceptions import ConnectionError
import json
import datetime as dt
import logging
from util import *
from math import ceil
import csv
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
import secrets_local


class DsoTestClient(object):
    '''
    classdocs
    '''
    
    def __init__(self, flexserver, loglevel="DEBUG", productId=None, flexDemandAdvance=1000*60*60, 
                 username = secrets_local.flexserver_username, password=secrets_local.flexserver_password):
        '''
        Constructor
        
        Parameters
        ----------
        flexserver: string
            flexserver hostname
        loglevel: string
            log level (default: DEBUG)
        productId: int
            considered market product id (default: from param file > env. var. DSO_PRODUCTID) 
        flexDemandAdvance: int
            time to pass flex demand in advance in ms (default: 3600000)
        username: string
            username to access flex server
        passwort: string
            password to access flex server
        '''
        
        numeric_level = getattr(logging, loglevel.upper(), None)
        print("Loglevel: " + loglevel)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        
        logging.basicConfig(level=numeric_level, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%H:%M:%S',)
         
        paramFilename = os.getenv("DSO_PARAM_FILENAME", "../params/dso_parameters.csv")
        paramId = int(os.getenv("DSO_PARAM_ID", "1"))
        with open(paramFilename, newline='') as paramfile:
            params = np.genfromtxt(paramFilename, delimiter=',', names=True)
        self.params = params[params['ID']==paramId]    
        
        if productId is None:
            self.productId = int(self.params['DSO_PRODUCTID']) if \
            ('DSO_PRODUCTID' in self.params.dtype.names and len(self.params) > 0) else int(os.getenv("DSO_PRODUCTID", 3))
        else:
            self.productId = productId
        logging.debug("Operating with market product ID " + str(self.productId))
        
        self.flexDemandAdvance = flexDemandAdvance
        
        
        self.demandcurve =  int(self.params['DSO_DEMANDCURVE']) if \
        ('DSO_DEMANDCURVE' in self.params.dtype.names and len(self.params) > 0) else int(os.getenv('DSO_DEMANDCURVE',1))
        logging.warn("Set demandcurve to :" + str(self.demandcurve))
        
        self.active = True
        
        self.username = username
        userAndPass = b64encode((self.username + ":" + password).encode()).decode("ascii")
        self.authorisation = "Basic %s" % userAndPass
        
        self.flexserver = flexserver
        self.smdPrototypeFilename = os.getenv("DSO_PROTOTYPE_FILENAME", 'smdProto.json')
        self.sendCounter = 0
        
        quantityDataFilename = os.getenv("DSO_QUANTITY_FILENAME", '../data/time_series_15min_singleindex_LoadSolarWind_50Hz_JulySep2020.csv')
        start = os.getenv("DSO_QUANTITY_START",'2020-08-17')
        end = os.getenv("DSO_QUANTITY_END",'2020-08-28')
         
        def parsetime(v): 
            return np.datetime64(dt.datetime.strptime(v.decode("utf-8"), '%Y-%m-%dT%H:%M:%S%z')
        )
        
        with open(quantityDataFilename, newline='') as csvfile:
            self.quantitydata = np.genfromtxt(quantityDataFilename, delimiter=',',#names=True,
                                 skip_header=1,
                                 dtype={
                                    'names': ('timestamp', 'load', 'solar', 'wind'),
                                    'formats': ('datetime64[us]', 'float64', 'float64', 'float64')
                                 }, 
                                 converters={0: parsetime})
        
        selector = np.logical_and(self.quantitydata['timestamp'] >= np.datetime64(start), 
                              self.quantitydata['timestamp'] < np.datetime64(end))
        self.quantitydata = self.quantitydata[selector]
        
        
        self.quantityMaxLoad = np.max(self.quantitydata['load']-self.quantitydata['solar']-self.quantitydata['wind'])
        self.quantityMinLoad = np.min(self.quantitydata['load']-self.quantitydata['solar']-self.quantitydata['wind'])
        self.quantityFactor = float(params['DSO_QUANTITY_FACTOR']) if \
        ('DSO_QUANTITY_FACTOR' in self.params.dtype.names and len(self.params) > 0) else float(os.getenv("DSO_QUANTITY_FACTOR", 0.01))
        
        self.seed = 1
        self.ran = Random(self.seed)
        self.tinfo = None
        self.pinfo = None
        
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
             
        nextDayDeliveryStart = dt.datetime(1970, 1, 1) + dt.timedelta(
            milliseconds = ceil((simMillisNow - firstDeliveryPeriodStart + openingTime) / auctionDeliverySpan) * auctionDeliverySpan +
            firstDeliveryPeriodStart)
        
        logging.debug("Next delivery period start: " + nextDayDeliveryStart.strftime("%Y-%m-%dT%H:%M:%S"))
       
        smd['sender_MarketParticipant']['mRID']['mRID'] = self.username
        smd['createdDateTime'] = self.nowSim.strftime("%Y-%m-%dT%H:%M:%S+02:00")
        smd['timeInterval'] = nextDayDeliveryStart.strftime("%Y-%m-%dT%H:%M:%S+00:00") + "/" \
            + (nextDayDeliveryStart + dt.timedelta(milliseconds = auctionDeliverySpan)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        for ts in smd['timeSeries']:
            points = []
            ts['in']['mRID']['mRID'] = self.username
            duration = self.demandcurve
            # introduce delivery interval as parameter and derive number of slots
            for i in range(0,96):
                
                if i % int(duration) == 0:
                    
                    # check whether self.quantitydata contains data for current date:
                    #nextDayDeliveryStart = dt.datetime.strptime("2020-08-08 00:00:00", '%Y-%m-%d %H:%M:%S')
                    interval = nextDayDeliveryStart + dt.timedelta(minutes = 15 * i)
                    if interval in self.quantitydata['timestamp']:
                        quantityRow = self.quantitydata[np.argwhere(self.quantitydata['timestamp'] == interval) + np.array(range(0,int(duration)))]
                        
                        # quantity =  (np.mean(quantityRow['load'] - self.quantityMeanLoad)) -\
                        #     (np.mean(quantityRow['solar'] - self.quantityMeanSolar))

                        netload = np.mean(quantityRow['load'] - quantityRow['solar'] - quantityRow['wind'])
                            
                        if netload > self.quantityMaxLoad * self.params['GRIDLOAD_UPPER']:
                            quantity = -1 * self.quantityFactor * (netload - (self.quantityMaxLoad * self.params['GRIDLOAD_UPPER']))
                        elif netload < self.quantityMinLoad * self.params['GRIDLOAD_LOWER']:
                            quantity = -1 * self.quantityFactor * (netload - (self.quantityMinLoad * self.params['GRIDLOAD_LOWER']))
                        else:
                            quantity = 0
                    else:        
                        quantity = self.ran.random() * self.quantityFactor
                    
                points.append({
                        "quantity": float(quantity),
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
        while True:
            try:
                headers = {'Content-type': 'application/json', 'Accept': '*/*', 
                           "Accept-Encoding": 'gzip, deflate, br', "Authorization":self.authorisation}
                response = requests.get('https://' + self.flexserver + '/api/config-time', headers=headers, verify=False)
                logging.info("Status code of time information request: " + str(response.status_code))
                break
            except ConnectionError:
                logging.warn("FlexServer not available. Reattempting after %d seconds.", 60)
                sleep(60)
        if response.status_code == 401:
            logging.error("Access denied (username: " + self.username + ")!")
            sys.exit()
        else:
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
        
        if self.pinfo is None:
            logging.error("Product ID " + str(self.productId) + " not available at " + self.flexserver)
            sys.exit()
            
        auctionDeliverySpan = self.pinfo['auctionDeliverySpan']
        firstDeliveryPeriodStart = self.pinfo['firstDeliveryPeriodStart']
        simMillisNow = self.tinfo['currentSimulationTime']
        openingTime = durationString2Millis(self.pinfo['openingTime'])
        
        logging.debug("Simulation now: " +  str(dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds = simMillisNow)))
        logging.debug("First Delivery Period Start: " + str(dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds = firstDeliveryPeriodStart)))
        logging.debug("Opening time: " + (dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds = openingTime)).strftime("%H:%M:%S"))
        logging.debug("AuctionDeliverySpan: " + (dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds = auctionDeliverySpan)).strftime("%-dD %H:%M:%S"))
        
        # get waiting time for next opening time - advance
        # -((simNow - firstDeliveryPeriodStart) mod auctionDeliverySpan) + auctionDeliverySpan - openingTime - advance
        waitMillis = -((simMillisNow - (firstDeliveryPeriodStart - openingTime - self.flexDemandAdvance)) % auctionDeliverySpan) + auctionDeliverySpan 
        logging.debug("Waiting duration: " + dt.datetime.utcfromtimestamp(waitMillis / (1000 * self.tinfo['simulationFactor'])).strftime("%H:%M:%S"))
       
        return waitMillis / self.tinfo['simulationFactor']
        
    def setInactive(self):
        logging.info("Set inactive!")
        self.active = False
        