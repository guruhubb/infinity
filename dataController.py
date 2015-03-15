from requests_futures.sessions import FuturesSession
from flask.ext.security import login_required
import models, datetime, math, time, json, flask, requests,subprocess, spur, collections
from flask import Blueprint, Response
from mongoengine import Q
from flask.ext.mail import Message
from infinity import mail, app, Device, Data, Event, Site, Aggr_data, Beagle, Router, Minute, Hour, Day, Month,\
                    Site_data,Site_data_min, Site_data_hour, Site_data_day, Site_data_month
from math import radians, cos, sin, asin, sqrt
import eventlet
import threading
from eventlet.green import urllib2
# from bson import Code
# from multiprocessing import Pool
# from collections import defaultdict
# from multiprocessing import Process
# from multiprocessing.pool import ThreadPool
# from simplexml import dumps
# from flask import make_response, Flask
# from flask.ext.restful import Api, Resource
# from requests import get
# import xml.etree.ElementTree as ET
# from xml2json import json2xml, xml2json
# from xmlutils.xml2json import xml2json
# from xmltodict import parse, unparse, OrderedDict
import xmltodict
import re
import urllib2
# import sys
# import httplib
# import socket
# from urllib2 import URLError, HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, install_opener, build_opener


dataController = Blueprint('dataController', __name__, template_folder='templates')

import pymongo
dbmongo = pymongo.MongoClient('mongodb://localhost:27017/').infinity
from pymongo import Connection
connection = Connection()
db = connection['infinity']
dataCollection = db.data
siteCollection = db.site_data
linkCollection = db.aggr_data

# DISTANCE_MAX = 40
# DISTANCE_MIN = 10
INTERVAL = 14
CUTOFF_CAPACITY = 2
LOW_SNR = 5
CUTOFF_SNR = 3
OUT_OF_NETWORK_SNR = 2
NUM_OF_EVENTS = 10
EVENT_TIME_INTERVAL = 60
MAX_DAYS=1
PROCESS_TIME_DELAY_IN_SECS = 1
AGGR_TIME_DELAY_IN_SECS = 1
SIXTY_TIME_DELAY = 61
TIMEOUT = 10
session = FuturesSession(max_workers=10)        #increase the number of workers based on number of processes we can run
headers = {'Content-Type':'application/json'}
headersXml = {'Content-Type':'application/xml'}
initial_time = 0

def bg_cb(sess, resp):
    resp.data = resp.json()                     # parse the json storing the result on the response object
def f(x):
    return x*x
def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
        else:
            return "Already collecting data"
    wrapper.has_run = False
    return wrapper

# run startdata once - could not implement the forever run logic at startup of the app

class ThreadingExample(object):
    """ Threading example class

    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, interval=INTERVAL):
        """ Constructor

        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        """ Method that runs forever """
        while True:
            # Do something
            # print('Getting data in the background')
            try:
                # getData()
                # processData()
                # aggrData()
                get_data()      # get data from all 'CPE' devices and then from all 'sites'
                # minuteData()
                # hourData()
                # dayData()
                # monthData()
                # siteMinute()
                # siteHour()
                # siteDay()
                # siteMonth()
                # time.sleep(1)

            except Exception, msg:
                app.logger.error('error message in startdata() is: %s, ' % msg)
            time.sleep(self.interval)
# def getData_():
#     try:
#         while True:
#             getData()
#     except Exception, msg:
#             app.logger.error('error message from getData is: %s, ' % msg)

# def processData_():
#     try:
#         while True:
#             processData()
#     except Exception, msg:
#             app.logger.error('error message from processData is: %s, ' % msg)

# def aggrData_():
#     try:
#         while True:
#             aggrData()
#     except Exception, msg:
#             app.logger.error('error message from aggrData is: %s, ' % msg)

def sixtyData_():
    try:
        while True:
            minuteData()
            time.sleep(60)
    except Exception, msg:
            app.logger.error('error message from sixtyData is: %s, ' % msg)

def hourData_():
    try:
        while True:
            hourData()
            time.sleep(60*60)
    except Exception, msg:
            app.logger.error('error message from hourData is: %s, ' % msg)

def dayData_():
    try:
        while True:
            dayData()
            time.sleep(60*60*24)
    except Exception, msg:
            app.logger.error('error message from dayData is: %s, ' % msg)

def get_beagle_():
    try:
        while True:
            get_beagle()
            time.sleep(60*15)
    except Exception, msg:
            app.logger.error('error message from get_beagle is: %s, ' % msg)

def get_router_():
    try:
        while True:
            get_router()
            time.sleep(60*15)
    except Exception, msg:
            app.logger.error('error message from get_router is: %s, ' % msg)

@app.route('/startdata')
# @login_required
@run_once
def startdata():
    example = ThreadingExample()
    # time.sleep(3)
    # print('Checkpoint')
    # time.sleep(2)
    # print('Bye')
    # while True:
    #
    #     try:
    #         # getData()
    #         # processData()
    #         # aggrData()
    #         get_data()      # get data from all 'CPE' devices and then from all 'sites'
    #         # minuteData()
    #         # hourData()
    #         # dayData()
    #         # monthData()
    #         # siteMinute()
    #         # siteHour()
    #         # siteDay()
    #         # siteMonth()
    #         # time.sleep(1)
    #
    #     except Exception, msg:
    #         app.logger.error('error message in startdata() is: %s, ' % msg)
    return "Start getting data from device"


def fetch(url):
    if (valid_url(url)):
        return urllib2.urlopen(url,None,TIMEOUT).read()


def valid_url(url):
    try:
        urllib2.urlopen(url)
        return True
    except Exception, e:
        return False

@app.route('/data/getData', methods=['GET'])
def get_data():

    # get status, device-info, link-info of all ship devices every 5s, we already know the location of the bts devices
    # estimate 5-7kB per get call every 5s or 1kB/s or 8kbps data used for monitoring each device; 100 cpes = 200x 8~1.6Mbps hitting server
    # initial_time = time.now
    #
    # initial_time = 0
    # while True:
    global  initial_time
    if ((int(time.time()) - initial_time) > INTERVAL-5):
        initial_time = int(time.time())
        # get data
        # url_status = []
        # url_device = []
        # url_link = []
        url_list =[]
        # url_full_list = []
        for object in Device.objects(active = True, type = 'CPE'):

            # use this for real radio - it needs https calls
            # url_list.append('https://'+object.url+'/core/api/service/status.php?username=infinity&password=123')
            # url_list.append('https://'+object.url + '/core/api/service/device-info.php?username=infinity&password=123')
            # url_list.append('https://'+object.url + '/core/api/service/link-info.php?username=infinity&password=123')

            # use this for real radio - it needs https calls
            # url_list.append('https://'+object.url+'/core/api/service/status.php?username=gigaknot&password=123')
            # url_list.append('https://'+object.url + '/core/api/service/device-info.php?username=gigaknot&password=123')
            # url_list.append('https://'+object.url + '/core/api/service/link-info.php?username=gigaknot&password=123')

            url_list.append('http://'+object.url+'/core/api/service/status.php?username=infinity&password=123')
            url_list.append('http://'+object.url + '/core/api/service/device-info.php?username=infinity&password=123')
            url_list.append('http://'+object.url + '/core/api/service/link-info.php?username=infinity&password=123')

        doc_=[]
        # pool = eventlet.GreenPool()
        # use multiple threads to get data from each device and parse it
        app.logger.info('Fetching data at %s'  % str(datetime.datetime.now()))

        # for body in pool.imap(fetch, url_list):
        for url in url_list:
            data = urllib2.urlopen(url).read()
            if data:
                doc_.append(xmltodict.parse(data))
        app.logger.info('Fetched data at %s'  % str(datetime.datetime.now()))

        for i in xrange (0,len(doc_),3):
            try:
                status = doc_[i]['response']['mimosaContent']['values']
                device = doc_[i+1]['response']['mimosaContent']['values']
                link = doc_[i+2]['response']['mimosaContent']['values']
                for k,v in device.items():
                    if k in ['DeviceName','Location','Temperature']:
                        if device[k]:
                            status[k] = device[k]
                # add only LinkName, MaxCapacity, and Distance from link-info API
                for k,v in link.items():
                    if k in ['LinkName','MaxCapacity','Distance']:
                        if link[k]:
                            status[k] = link[k]
                        else:
                            status[k] = 0.0
                for k,v in status.items():
                    if k not in ['Chains_1_2', 'Chains_3_4','Details','Rx_MCS','Location','DeviceName','LinkName']:
                        if status[k]:
                            status[k] = float(status[k])
                        else: status[k] = 0.0
                    elif k == 'Rx_MCS':
                        if status[k]:
                            status [k]=int(status[k])
                        else: status[k] = 0.0
                    elif k == 'Location':
                        if status[k]:
                            status [k] = tuple([float(x) for x in re.split(' -- ',status [k])])
                        else: status[k] = (0.,0.)
                    else:
                        if status[k]:
                            status[k] = status[k]
                        else: status[k] = 0.
                if str(status['SignalStrength']) == '-inf':
                    status['SignalStrength'] = -100.0

                # status.update(device)
                # status.update(link)

                # convert string to float, mcs/encoding to int, lat-long to geo
                # add checks for Null data, convert Details to flat dict, remove Details

                details = status['Details']['_ELEMENT']
                for x in range(len(details)):
                    if details[x]['Tx']:
                        status['Tx'+str(x)] = float(details[x]['Tx'])
                    else:
                        status['Tx'+str(x)] = 0.0
                    if details[x]['Rx']:
                        status['Rx'+str(x)] = float(details[x]['Rx'])
                    else:
                        status['Rx'+str(x)] = 0.0
                    if details[x]['Noise']:
                        status['Noise'+str(x)] = float(details[x]['Noise'])
                    else:
                        status['Noise'+str(x)] = 0.0
                    if details[x]['Encoding']:
                        status['Encoding'+str(x)] = int(details[x]['Encoding'])
                    else:
                        status['Encoding'+str(x)] = 0.0

                del status['Details']
                # status ['Time'] = initial_time
                # status ['Process'] = False
                # status ['Aggregate'] = False

                status_=collections.OrderedDict()
                status_['Time']=initial_time
                status_['Data']=status['TxRate']+status['RxRate']
                if status['MaxCapacity'] > CUTOFF_CAPACITY:
                    coverage = True
                else:
                    coverage = False
                status_['Coverage']=coverage
                for k,v in status.items():
                    status_[k]=status[k]
                # copy subset of data table to link table
                link_ = collections.OrderedDict()
                link_['site'] = status['LinkName']
                link_['time'] = initial_time
                link_['tx'] = status['TxRate']
                link_['rx'] = status ['RxRate']
                link_['cap'] = status['MaxCapacity']
                link_['data']=status_['Data']
                link_['coverage']=status_['Coverage']
                link_['distance']=status['Distance']
                link_['geo']=status['Location']

                app.logger.info('Data from %s at %s'  % (url_list[i],str(datetime.datetime.now())))
                dataCollection.insert(status_)
                linkCollection.insert(link_)
                # i=i+3

                # status ['statusSize'] = sys.getsizeof(response_status.content)
                # from pymongo import Connection
                # app.logger.info('data from %s - status_ is %s and dumps is %s' % (url, status_,json.dumps(status_)))
                # return Response(json.dumps(status),  mimetype='application/json')

            except :
                app.logger.info("Bad Access API")
        # time.sleep(1)
        site()
            # url_status = 'https://192.168.1.20:5001/core/api/service/status.php?management-id=mimosa&management-password=pass123'
            # url_device = 'http://127.0.0.1:5001/core/api/service/device-info.php?management-id=mimosa&management-password=pass123'
            # url_link = 'http://127.0.0.1:5001/core/api/service/link-info.php?management-id=mimosa&management-password=pass123'
        # for url, urlStatus, urlDevice, urlLink in zip(url_list,url_status,url_device,url_link):
        #     try :
        #
        #         # password_mgr = HTTPPasswordMgrWithDefaultRealm()
        #         # # Add the username and password.
        #         # feed_url = 'https://192.168.1.20/core/api/service/status.php'
        #         # password_mgr.add_password(None, feed_url, "username=infinity", "password=123")
        #         # opener = build_opener(HTTPBasicAuthHandler(password_mgr))
        #         # file = opener.open(feed_url)
        #         # conn = httplib.HTTPSConnection(str(url))
        #         # conn.request("GET","/core/api/service/status.php?username=infinity&password=123")
        #         # r1 = conn.getresponse()
        #         # response_status= r1.read()
        #         # conn.request("GET","/core/api/service/device-info.php?username=infinity&password=123")
        #         # r1 = conn.getresponse()
        #         # response_device= r1.read()
        #         # conn.request("GET","/core/api/service/link-info.php?username=infinity&password=123")
        #         # r1 = conn.getresponse()
        #         # response_link= r1.read()
        #
        #         # response_status = session.get(urlStatus, headers=headersXml,timeout=2).result()
        #         # response_device = session.get(urlDevice, headers=headersXml,timeout=2).result()
        #         # response_link = session.get(urlLink, headers=headersXml,timeout=2).result()
        #         # response_status = urllib2.urlopen('https://192.168.1.20/core/api/service/status.php?username=infinity&password=123')
        #         # response_device = urllib2.urlopen('https://192.168.1.20/core/api/service/device-info.php?username=infinity&password=123')
        #         # response_link = urllib2.urlopen('https://192.168.1.20/core/api/service/link-info.php?username=infinity&password=123')
        #
        #         # r=requests.get(urlStatus,verify=False)  #same as urllib2
        #         urls = [urlStatus,urlDevice,urlLink]
        #         doc_=[]
        #         pool = eventlet.GreenPool()
        #         i=0
        #         for body in pool.imap(fetch, urls):
        #             doc_.append(xmltodict.parse(body))
        #
        #             # print("got body", len(body))
        #
        #         # response_status = urllib2.urlopen(urlStatus, None,TIMEOUT)
        #         # response_device = urllib2.urlopen(urlDevice, None, TIMEOUT)
        #         # response_link = urllib2.urlopen(urlLink, None, TIMEOUT)
        #
        #         # doc_status = xmltodict.parse(response_status.read())
        #         # doc_device = xmltodict.parse(response_device.read())
        #         # doc_link = xmltodict.parse(response_link.read())
        #
        #         # doc_status = xmltodict.parse(response_status.content)
        #         # doc_device = xmltodict.parse(response_device.content)
        #         # doc_link = xmltodict.parse(response_link.content)
        #
        #         # status = doc_status['response']['mimosaContent']['values']
        #         # device = doc_device['response']['mimosaContent']['values']
        #         # link = doc_link['response']['mimosaContent']['values']
        #
        #         status = doc_[0]['response']['mimosaContent']['values']
        #         device = doc_[1]['response']['mimosaContent']['values']
        #         link = doc_[2]['response']['mimosaContent']['values']
        #
        #         # add only DeviceName and Location from device-info API
        #         for k,v in device.items():
        #             if k in ['DeviceName','Location']:
        #                 if device[k]:
        #                     status[k] = device[k]
        #         # add only LinkName, MaxCapacity, and Distance from link-info API
        #         for k,v in link.items():
        #             if k in ['LinkName','MaxCapacity','Distance']:
        #                 if link[k]:
        #                     status[k] = link[k]
        #                 else:
        #                     status[k] = 0.0
        #         for k,v in status.items():
        #             if k not in ['Chains_1_2', 'Chains_3_4','Details','Rx_MCS','Location','DeviceName','LinkName']:
        #                 if status[k]:
        #                     status[k] = float(status[k])
        #                 else: status[k] = 0.0
        #             elif k == 'Rx_MCS':
        #                 if status[k]:
        #                     status [k]=int(status[k])
        #                 else: status[k] = 0.0
        #             elif k == 'Location':
        #                 if status[k]:
        #                     status [k] = tuple([float(x) for x in re.split(' -- ',status [k])])
        #                 else: status[k] = (0.,0.)
        #             else:
        #                 if status[k]:
        #                     status[k] = status[k]
        #                 else: status[k] = 0.
        #         if status['SignalStrength'] == float('-inf'):
        #             status['SignalStrength'] = -100.0
        #         # status.update(device)
        #         # status.update(link)
        #
        #         # convert string to float, mcs/encoding to int, lat-long to geo
        #         # add checks for Null data, convert Details to flat dict, remove Details
        #
        #         details = status['Details']['_ELEMENT']
        #         for x in range(len(details)):
        #             if details[x]['Tx']:
        #                 status['Tx'+str(x)] = float(details[x]['Tx'])
        #             else:
        #                 status['Tx'+str(x)] = 0.0
        #             if details[x]['Rx']:
        #                 status['Rx'+str(x)] = float(details[x]['Rx'])
        #             else:
        #                 status['Rx'+str(x)] = 0.0
        #             if details[x]['Noise']:
        #                 status['Noise'+str(x)] = float(details[x]['Noise'])
        #             else:
        #                 status['Noise'+str(x)] = 0.0
        #             if details[x]['Encoding']:
        #                 status['Encoding'+str(x)] = int(details[x]['Encoding'])
        #             else:
        #                 status['Encoding'+str(x)] = 0.0
        #
        #         del status['Details']
        #         # status ['Time'] = initial_time
        #         status ['Process'] = False
        #         status ['Aggregate'] = False
        #
        #         status_=collections.OrderedDict()
        #         status_['Time']=initial_time
        #         for k,v in status.items():
        #             status_[k]=status[k]
        #         app.logger.info('Data from %s'  % url)
        #         dataCollection.insert(status_)
        #
        #         # status ['statusSize'] = sys.getsizeof(response_status.content)
        #         # from pymongo import Connection
        #         # app.logger.info('data from %s - status_ is %s and dumps is %s' % (url, status_,json.dumps(status_)))
        #         # return Response(json.dumps(status),  mimetype='application/json')
        #
        #     except :
        #         app.logger.info("Bad Access API")

    # else:
    #     continue

@app.route('/data/siteData')
@login_required
def site_data():

    # aggregate cpe devices on a ship, and bts devices at a port
    now = int(time.time())
    dataObjects = Data.objects(Aggregate = False, Process = False, Time__lt = now-AGGR_TIME_DELAY_IN_SECS,Time__gt = now
                                                                          -24*60*60*MAX_DAYS)
    for data in dataObjects:
        device = Device.objects(name=data.DeviceName).first()
        if device:
            if device.type == 'CPE':
                # if Aggr_data.objects(time__lt = data.time + datetime.timedelta(seconds = 0.5),
                #                         time__gt = data.time - datetime.timedelta(seconds = 0.5),
                #                         site = device.site).first() is None:
                if Aggr_data.objects(time = data.Time,site = device.site).first() is None:

                    # get data from the second device

                    second_device = Device.objects(site=device.site, name__ne=device.name).first()
                    if second_device:
                        # second_device_data = Data.objects(mac=second_device.mac,
                        #         time__lt= data.time+datetime.timedelta(seconds=1),
                        #         time__gt= data.time-datetime.timedelta(seconds=1)).first()
                        second_device_data = Data.objects(DeviceName=second_device.name,Time= data.Time).first()

                        # add aggr_data record with tx, rx, total_cap, minimum distance;
                        # if total_cap > cutoff_capacity then cov = YES

                        if second_device_data:
                            total_tx = second_device_data.TxRate + data.TxRate
                            total_rx = second_device_data.RxRate + data.RxRate
                            total_total_cap = second_device_data.MaxCapacity + data.MaxCapacity
                            if second_device_data.Distance > data.Distance :
                                min_distance = data.Distance
                            else :
                                min_distance = second_device_data.Distance

                            # prevent zero distance condition

                            if second_device_data.Distance == 0:
                                min_distance = data.Distance
                            if data.Distance == 0:
                                min_distance = second_device_data.Distance

                            if total_total_cap > CUTOFF_CAPACITY:
                                coverage = True
                            else:
                                coverage = False
                            aggr_data = Aggr_data(site=device.site, time = data.Time, tx=total_tx, rx=total_rx,
                                 cap = total_total_cap, data = total_rx+total_tx, coverage = coverage,
                                 distance = min_distance, geo = data.Location)
                            aggr_data.save()
                            Data.objects(id=data.id).update(set__Aggregate=True)
                        else:
                            if data.MaxCapacity > CUTOFF_CAPACITY:
                                coverage = True
                            else:
                                coverage = False
                            aggr_data = Aggr_data(site=device.site, time = data.Time, tx=data.TxRate, rx=data.RxRate,
                                 cap = data.MaxCapacity, data = data.TxRate+data.RxRate, coverage = coverage,
                                 distance = data.Distance, geo = data.Location)
                            aggr_data.save()
                            Data.objects(id=data.id).update(set__Aggregate=True)
                            app.logger.error("There is NO data from second device %s on site %s" %
                                             (second_device.name, device.site))
                    else:
                        if data.MaxCapacity > CUTOFF_CAPACITY:
                                coverage = True
                        else:
                                coverage = False
                        aggr_data = Aggr_data(site=device.site, time = data.Time, tx=data.TxRate, rx=data.RxRate,
                                 cap = data.MaxCapacity, data = data.TxRate+data.RxRate, coverage = coverage,
                                 distance = data.Distance, geo = data.Location)
                        aggr_data.save()
                        Data.objects(id=data.id).update(set__Aggregate=True)
                        app.logger.error("There is NO second device on site %s" % device.site)
    return "Done"
    # time.sleep(1)

# @app.route('/aggrData')
# @login_required
# def aggrData():
#
#     # aggregate cpe devices on a ship, and bts devices at a port
#     now = int(time.time())
#     dataObjects = Data.objects(aggregate = False, process = True, time__lt = now-AGGR_TIME_DELAY_IN_SECS,time__gt = now
#                                                                           -24*60*60*MAX_DAYS)
#
#     for data in dataObjects:
#         device = Device.objects(mac=data.mac).first()
#
#         if device.type == 'CPE':
#             # if Aggr_data.objects(time__lt = data.time + datetime.timedelta(seconds = 0.5),
#             #                         time__gt = data.time - datetime.timedelta(seconds = 0.5),
#             #                         site = device.site).first() is None:
#             if Aggr_data.objects(time = data.time,site = device.site).first() is None:
#
#                 # get data from the second device
#
#                 second_device = Device.objects(site=device.site, mac__ne=device.mac).first()
#                 if second_device:
#                     # second_device_data = Data.objects(mac=second_device.mac,
#                     #         time__lt= data.time+datetime.timedelta(seconds=1),
#                     #         time__gt= data.time-datetime.timedelta(seconds=1)).first()
#                     second_device_data = Data.objects(mac=second_device.mac,time= data.time).first()
#
#                     # add aggr_data record with tx, rx, total_cap, minimum distance;
#                     # if total_cap > cutoff_capacity then cov = YES
#
#                     if second_device_data:
#                         total_tx = second_device_data.tx + data.tx
#                         total_rx = second_device_data.rx + data.rx
#                         total_total_cap = second_device_data.total_cap + data.total_cap
#                         if second_device_data.distance > data.distance :
#                             min_distance = data.distance
#                         else :
#                             min_distance = second_device_data.distance
#
#                         # prevent zero distance condition
#
#                         if second_device_data.distance == 0:
#                             min_distance = data.distance
#                         if data.distance == 0:
#                             min_distance = second_device_data.distance
#
#                         if total_total_cap > CUTOFF_CAPACITY:
#                             coverage = True
#                         else:
#                             coverage = False
#                         aggr_data = Aggr_data(site=device.site, time = data.time, tx=total_tx, rx=total_rx,
#                              cap = total_total_cap, data = total_rx+total_tx, coverage = coverage,
#                              distance = min_distance, geo = data.geo)
#                         aggr_data.save()
#                         Data.objects(id=data.id).update(set__aggregate=True)
#                     else:
#                         if data.total_cap > CUTOFF_CAPACITY:
#                             coverage = True
#                         else:
#                             coverage = False
#                         aggr_data = Aggr_data(site=device.site, time = data.time, tx=data.tx, rx=data.rx,
#                              cap = data.total_cap, data = data.tx+data.rx, coverage = coverage,
#                              distance = data.distance, geo = data.geo)
#                         aggr_data.save()
#                         Data.objects(id=data.id).update(set__aggregate=True)
#                         app.logger.error("There is NO data from second device %s on site %s" %
#                                          (second_device.name, device.site))
#                 else:
#                     app.logger.error("There is NO second device on site %s" % device.site)
#
#     return "Done"
#     # time.sleep(1)
# @app.route('/getData')
# @login_required
# def getData():
#     urlList = []
#     urlListXml = []
#     macList = []
#     timeList = []
#     totaldocuments = []
#     msg = ""
#
#     # go through all the devices and make a list of url, mac, latest timestamp of data
#
#     for object in Device.objects(active = True):
#         urlList.append(object.url+'/api/device')   # need /api/device affix in the url
#         macList.append(object.mac) #https://192.168.20.1/core/api/service/status.php?managementid=
# #mimosa&management-password=pass123
#         urlListXml.append(object.url+'/core/api/service/status.php?management-id=mimosa&management-password=pass123')   # need /api/device affix in the url
#
#         timeStamp = Data.objects(mac = object.mac).order_by('-time').only ('time').first()
#
#         # validate if timestamp is null and format it for the device timestamp if necessary
#
#         if timeStamp:
#             # timeStamp = timeStamp.time
#             # timeStamp = datetime.datetime.strptime(timeStamp,"%Y-%m-%dT%H:%M:%S.%f")
#             # timeStamp = timeStamp.strftime('%Y-%m-%d %H:%M:%S.%f')
#             # timeStamp = timeStamp.strftime('%Y-%m-%d %H:%M:%S')
#             timeList.append(timeStamp.time)
#         else:
#             timeList.append(time.time()-2*60)    # append 2 minutes from now ghl;'
#
#     # do REST calls and get new data
#
#     for url, timeItem in zip(urlList,timeList):
#
#         # get new data gt (time.now - 1 hr), make sure time is in string format
#
#         filters = [dict(name='time', op='>', val=str(timeItem))]
#         params = dict(q=json.dumps(dict(filters=filters)))
#         try:  #try with timeout=2 instead of timeout =5
#             response = session.get(url,params=params, headers=headers,timeout=2,background_callback=bg_cb).result()
#             if len(response.data["objects"]) is 0:
#                 continue
#             documents=[]
#             count=0
#             for obj in response.data["objects"]:
#                 count += 1
#                 if count == 1:   # remove redundant first object
#                     continue
#                 else:
#                     mac = obj["mac"]
#                     connId = obj["connId"]
#                     timeEntry = obj["time"]
#                     # timeEntry = datetime.datetime.strptime(obj["time"],"%Y-%m-%dT%H:%M:%S.%f").replace(microsecond=0)
#                     lat = obj["lat"]
#                     long = obj["long"]
#                     freqA = obj["freqA"]
#                     freqB = obj["freqB"]
#                     snrA = obj["snrA"]
#                     snrB = obj["snrB"]
#                     tx = obj["tx"]
#                     rx = obj["rx"]
#                     cap = obj["cap"]
#                     freqList = obj["freqList"].split()  # ordered list of available clear channels separated by whitespace
#                     ssidList = obj["ssidList"].split()  # ordered list of available ssids channels separated by whitespace
#
#                     geo = (lat,long)
#                     geo1=(0.,0.)
#                     documents.append({"mac":mac,"connId":connId,"time":timeEntry, "geo":geo,"geo1":geo1,"freqA":freqA,
#                         "freqB":freqB,"snrA":snrA,"snrB":snrB, "tx":tx,"rx":rx,"cap":cap,"total_cap":0,
#                         "distance":0, "freqList":freqList, "ssidList":ssidList,"process":False,"aggregate":False})
#
#             if documents:   # bulk insert
#                 totaldocuments.append(documents)
#                 dbmongo.data.insert(documents)
#
#         except Exception, msg:
#             app.logger.error('error message is: %s, ' % msg)
#             pass
#     if totaldocuments:
#         return str(totaldocuments)
#     else:
#         if msg:
#             return "Some or all devices are down"
#         else:
#             return "No data from devices"
#     # time.sleep(1)

# @app.route('/processData')
# @login_required
# # @run_once
# def processData():
#     # process CPE data continuously, calculate distance and coverage and update both CPE and BTS data
#     # generate snr related events for CPE
#     now = int(time.time())
#     ssid_event_counter=0
#     freq_event_counter=0
#     out_of_network_counter=0
#     start=time.time()
#     distance = 0
#
#     dataObjects = Data.objects(process = False, time__lt = now-PROCESS_TIME_DELAY_IN_SECS,
#                                time__gt = now-MAX_DAYS*24*60*60)
#     for data in dataObjects:
#         device = Device.objects(mac=data.mac).first()
#         if device.type == 'CPE':
#             # get the other device data to calculate total capacity and distance of link
#             bts_device = Data.objects(connId=data.connId, mac__ne=data.mac,time = data.time ).first()
#             if bts_device:
#                 # total_cap = data.cap + cap_of_bts_device
#                 total_cap = (data.cap*data.tx + bts_device.cap*data.rx)/(data.tx + data.rx)
#                 distance = distance_in_miles(bts_device.geo,data.geo)
#                 Data.objects(id=data.id).update(set__distance=distance, set__total_cap=total_cap, set__process=True,
#                                                 set__geo1=bts_device.geo)
#                 Data.objects(id=bts_device.id).update(set__distance=distance, set__total_cap=total_cap,
#                                                       set__process=True, set__geo1=data.geo)
#                 # check CPE SNR and generate alarm if necessary
#                 snr = min(data.snrA,data.snrB)
#                 # if snr is less than cutoff_snr, change ssid else change frequency
#                 if snr < OUT_OF_NETWORK_SNR:
#                     if out_of_network_counter == 0:
#                         start = time.time()
#                     out_of_network_counter += 1
#                     stop = time.time()
#                     delta = stop-start
#                     if out_of_network_counter >= NUM_OF_EVENTS-2 and delta <= EVENT_TIME_INTERVAL-2:
#                         event=Event(device=data.mac, parameter='SNR='+ str(snr), message='Going out of network')
#                         event.save()
#                     out_of_network_counter = 0
#                     start = time.time()
#
#                 elif snr < CUTOFF_SNR:
#                     if ssid_event_counter == 0:
#                         start = time.time()
#                     ssid_event_counter += 1
#                     stop = time.time()
#                     delta = stop-start
#                     if ssid_event_counter >= NUM_OF_EVENTS-1 and delta <= EVENT_TIME_INTERVAL-1:
#                         event=Event(device=data.mac, parameter='SNR='+ str(snr), message='Changing SSID')
#                         event.save()
#                         url = device.url+'/api/config'
#
#                         # remove all ssids of bts_site that 2nd device is connected to
#
#                         second_device = Device.objects(site=device.site, mac__ne=device.mac).first()
#                         if second_device:
#                             # if second_device.connId in ssidList:
#                             #     ssidList.remove(second_device.connId)
#                             bts_device = Device.objects(connId=second_device.connId, type='BTS').first()
#                             if bts_device:
#                                 bts_site = Site.objects(name=bts_device.site).first()
#                                 if bts_site:
#                                     bts_ssids = bts_site.ssidList
#                                     ssidList=[x for x in data.ssidList if x not in bts_ssids]
#                                 else:
#                                     app.logger.error("BTS site %s does not exist" % bts_device.site)
#                             else:
#                                 app.logger.error("There is NO BTS site for ssid %s" % second_device.connId)
#                         else:
#                             app.logger.error("There is NO second device on site %s" % device.site)
#
#                         if ssidList:
#                             new_ssid = ssidList[0]
#                             payload = {'connId': new_ssid}
#                             # putRequest = requests.put(url, data=json.dumps(payload), headers=headers) #TODO uncomment this after test
#
#                             # update Device info - is this needed?
#                             # device.connId = new_ssid
#                             # device.save()
#
#                         # reset counter
#
#                         ssid_event_counter = 0
#                         start = time.time()
#
#                 elif snr < LOW_SNR:
#                     if freq_event_counter == 0:
#                         start = time.time()
#                     freq_event_counter += 1
#                     stop = time.time()
#                     delta = stop-start
#                     if freq_event_counter >= NUM_OF_EVENTS and delta <= EVENT_TIME_INTERVAL:
#                         event=Event(device=data.mac, parameter='SNR='+ str(snr), message='Changing Frequency')
#                         event.save()
#                         # other_connected_device = Data.objects(connId=data.connId, mac__ne=data.mac,
#                         #                 time__lt = data.time + datetime.timedelta(seconds = 1),
#                         #                 time__gt = data.time - datetime.timedelta(seconds = 1)).first()
#                         # bts_device = Data.objects(connId=data.connId, mac__ne=data.mac,time = data.time ).first()
#                         #
#                         # if bts_device:
#                         url = Device.objects(mac = bts_device.mac).first().url + '/api/config'
#                         # else:
#                         #     app.logger.error("No freq changed because bts is not connected to %s" % data.mac)
#                         # else:# Todo remove this test code
#                         #     url = device.url+'/api/config' # todo remove this test code
#                             # remove freqA and freqB from freqlist choices
#
#                         current_freq = [str(data.freqA),str(data.freqB)]
#                         freqList=[x for x in data.freqList if x not in current_freq]
#
#                         if freqList:
#                             new_freq = freqList[0]
#                             if data.snrA < data.snrB:
#                                 payload = {'freqA': new_freq}
#                             else:
#                                 payload = {'freqB': new_freq}
#                             putRequest = requests.put(url, data=json.dumps(payload), headers=headers)
#                         freq_event_counter = 0
#                         start = time.time()
#
#             else:
#                 app.logger.error("There is no bts device connected to CPE %s" % data.mac)
#
#     return "Done"

@app.route('/beagleData')
@login_required
# @run_once
def beagleData():
    # get snr data from device 1 and device 2 and change SSID
    now = int(time.time())
    ssid_event_counter=0
    freq_event_counter=0
    out_of_network_counter=0
    start=time.time()
    distance = 0

    dataObjects = Data.objects(process = False, time__lt = now-PROCESS_TIME_DELAY_IN_SECS,
                               time__gt = now-MAX_DAYS*24*60*60)
    for data in dataObjects:
        device = Device.objects(mac=data.mac).first()
        if device.type == 'CPE':
            # get the other device data to calculate total capacity and distance of link
            bts_device = Data.objects(connId=data.connId, mac__ne=data.mac,time = data.time ).first()
            if bts_device:
                # total_cap = data.cap + cap_of_bts_device
                total_cap = (data.cap*data.tx + bts_device.cap*data.rx)/(data.tx + data.rx)
                distance = distance_in_miles(bts_device.geo,data.geo)
                Data.objects(id=data.id).update(set__distance=distance, set__total_cap=total_cap, set__process=True,
                                                set__geo1=bts_device.geo)
                Data.objects(id=bts_device.id).update(set__distance=distance, set__total_cap=total_cap,
                                                      set__process=True, set__geo1=data.geo)
                # check CPE SNR and generate alarm if necessary
                snr = min(data.snrA,data.snrB)
                # if snr is less than cutoff_snr, change ssid else change frequency
                if snr < OUT_OF_NETWORK_SNR:
                    if out_of_network_counter == 0:
                        start = time.time()
                    out_of_network_counter += 1
                    stop = time.time()
                    delta = stop-start
                    if out_of_network_counter >= NUM_OF_EVENTS-2 and delta <= EVENT_TIME_INTERVAL-2:
                        event=Event(device=data.mac, parameter='SNR='+ str(snr), message='Going out of network')
                        event.save()
                    out_of_network_counter = 0
                    start = time.time()

                elif snr < CUTOFF_SNR:
                    if ssid_event_counter == 0:
                        start = time.time()
                    ssid_event_counter += 1
                    stop = time.time()
                    delta = stop-start
                    if ssid_event_counter >= NUM_OF_EVENTS-1 and delta <= EVENT_TIME_INTERVAL-1:
                        event=Event(device=data.mac, parameter='SNR='+ str(snr), message='Changing SSID')
                        event.save()
                        url = device.url+'/api/config'

                        # remove all ssids of bts_site that 2nd device is connected to

                        second_device = Device.objects(site=device.site, mac__ne=device.mac).first()
                        if second_device:
                            # if second_device.connId in ssidList:
                            #     ssidList.remove(second_device.connId)
                            bts_device = Device.objects(connId=second_device.connId, type='BTS').first()
                            if bts_device:
                                bts_site = Site.objects(name=bts_device.site).first()
                                if bts_site:
                                    bts_ssids = bts_site.ssidList
                                    ssidList=[x for x in data.ssidList if x not in bts_ssids]
                                else:
                                    app.logger.error("BTS site %s does not exist" % bts_device.site)
                            else:
                                app.logger.error("There is NO BTS site for ssid %s" % second_device.connId)
                        else:
                            app.logger.error("There is NO second device on site %s" % device.site)

                        if ssidList:
                            new_ssid = ssidList[0]
                            payload = {'connId': new_ssid}
                            # putRequest = requests.put(url, data=json.dumps(payload), headers=headers) #TODO uncomment this after test

                            # update Device info - is this needed?
                            # device.connId = new_ssid
                            # device.save()

                        # reset counter

                        ssid_event_counter = 0
                        start = time.time()

                elif snr < LOW_SNR:
                    if freq_event_counter == 0:
                        start = time.time()
                    freq_event_counter += 1
                    stop = time.time()
                    delta = stop-start
                    if freq_event_counter >= NUM_OF_EVENTS and delta <= EVENT_TIME_INTERVAL:
                        event=Event(device=data.mac, parameter='SNR='+ str(snr), message='Changing Frequency')
                        event.save()
                        # other_connected_device = Data.objects(connId=data.connId, mac__ne=data.mac,
                        #                 time__lt = data.time + datetime.timedelta(seconds = 1),
                        #                 time__gt = data.time - datetime.timedelta(seconds = 1)).first()
                        # bts_device = Data.objects(connId=data.connId, mac__ne=data.mac,time = data.time ).first()
                        #
                        # if bts_device:
                        url = Device.objects(mac = bts_device.mac).first().url + '/api/config'
                        # else:
                        #     app.logger.error("No freq changed because bts is not connected to %s" % data.mac)
                        # else:# Todo remove this test code
                        #     url = device.url+'/api/config' # todo remove this test code
                            # remove freqA and freqB from freqlist choices

                        current_freq = [str(data.freqA),str(data.freqB)]
                        freqList=[x for x in data.freqList if x not in current_freq]

                        if freqList:
                            new_freq = freqList[0]
                            if data.snrA < data.snrB:
                                payload = {'freqA': new_freq}
                            else:
                                payload = {'freqB': new_freq}
                            putRequest = requests.put(url, data=json.dumps(payload), headers=headers)
                        freq_event_counter = 0
                        start = time.time()

            else:
                app.logger.error("There is no bts device connected to CPE %s" % data.mac)

    return "Done"

# @app.route('/aggrData')
# @login_required
# def aggrData():
#
#     # aggregate cpe devices on a ship, and bts devices at a port
#     now = int(time.time())
#     dataObjects = Data.objects(aggregate = False, process = True, time__lt = now-AGGR_TIME_DELAY_IN_SECS,time__gt = now
#                                                                           -24*60*60*MAX_DAYS)
#
#     for data in dataObjects:
#         device = Device.objects(mac=data.mac).first()
#
#         if device.type == 'CPE':
#             # if Aggr_data.objects(time__lt = data.time + datetime.timedelta(seconds = 0.5),
#             #                         time__gt = data.time - datetime.timedelta(seconds = 0.5),
#             #                         site = device.site).first() is None:
#             if Aggr_data.objects(time = data.time,site = device.site).first() is None:
#
#                 # get data from the second device
#
#                 second_device = Device.objects(site=device.site, mac__ne=device.mac).first()
#                 if second_device:
#                     # second_device_data = Data.objects(mac=second_device.mac,
#                     #         time__lt= data.time+datetime.timedelta(seconds=1),
#                     #         time__gt= data.time-datetime.timedelta(seconds=1)).first()
#                     second_device_data = Data.objects(mac=second_device.mac,time= data.time).first()
#
#                     # add aggr_data record with tx, rx, total_cap, minimum distance;
#                     # if total_cap > cutoff_capacity then cov = YES
#
#                     if second_device_data:
#                         total_tx = second_device_data.tx + data.tx
#                         total_rx = second_device_data.rx + data.rx
#                         total_total_cap = second_device_data.total_cap + data.total_cap
#                         if second_device_data.distance > data.distance :
#                             min_distance = data.distance
#                         else :
#                             min_distance = second_device_data.distance
#
#                         # prevent zero distance condition
#
#                         if second_device_data.distance == 0:
#                             min_distance = data.distance
#                         if data.distance == 0:
#                             min_distance = second_device_data.distance
#
#                         if total_total_cap > CUTOFF_CAPACITY:
#                             coverage = True
#                         else:
#                             coverage = False
#                         aggr_data = Aggr_data(site=device.site, time = data.time, tx=total_tx, rx=total_rx,
#                              cap = total_total_cap, data = total_rx+total_tx, coverage = coverage,
#                              distance = min_distance, geo = data.geo)
#                         aggr_data.save()
#                         Data.objects(id=data.id).update(set__aggregate=True)
#                     else:
#                         if data.total_cap > CUTOFF_CAPACITY:
#                             coverage = True
#                         else:
#                             coverage = False
#                         aggr_data = Aggr_data(site=device.site, time = data.time, tx=data.tx, rx=data.rx,
#                              cap = data.total_cap, data = data.tx+data.rx, coverage = coverage,
#                              distance = data.distance, geo = data.geo)
#                         aggr_data.save()
#                         Data.objects(id=data.id).update(set__aggregate=True)
#                         app.logger.error("There is NO data from second device %s on site %s" %
#                                          (second_device.name, device.site))
#                 else:
#                     app.logger.error("There is NO second device on site %s" % device.site)
#
#     return "Done"
#     # time.sleep(1)

# @app.route('/siteData')
# @login_required
# def siteData():
#     timeStamp=None
#     # a=defaultdict(lambda :defaultdict())
#     # go through all sites, go through device list for site, get Data for device with False aggregate and True process
#     # order records by time.
#     for site in Site.objects():
#         a = {}
#         for device in site.deviceList:
#             dataObjects = Data.objects(mac = device, aggregate = False, process = True,
#                                        time__lt = time.time() - AGGR_TIME_DELAY_IN_SECS,
#                                        time__gt = time.time() - 24*60*60*MAX_DAYS).order_by("time")
#             for data in dataObjects:
#                 # a[data.time][data.mac]= {'rx':data.rx, 'tx':data.tx,'cap':data.cap,'distance':data.distance,
#                 #                               'site':site.name, 'coverage':0, 'data':data.rx+data.tx, 'geo':data.geo}
#                 a= {data.time:{data.mac:{'rx':data.rx, 'tx':data.tx,'cap':data.cap,'distance':data.distance,
#                      'site':site.name, 'coverage':0, 'data':data.rx+data.tx, 'geo':data.geo, 'time':data.time}}}
#                 Data.objects(id=data.id).update(set__aggregate=True)
#
#         # go through data, add rx,tx,cap and minimize distance values for same site, and put it new list(dict) format
#         # save the new list
#         documents=[]
#         for t, mac in a.items():
#             total_rx = 0
#             total_tx = 0
#             total_cap = 0
#             distance=[]
#             records={}
#
#             for macId, value in mac.items():
#                 total_rx += a[t][macId]['rx']
#                 total_tx += a[t][macId]['tx']
#                 total_cap += a[t][macId]['cap']
#                 distance.append(a[t][macId]['distance'])
#                 if total_cap > CUTOFF_CAPACITY:
#                     coverage = 1
#                 records[t]={'rx':total_rx, 'tx':total_tx,'cap':total_cap,'distance':min(distance),
#                          'site':a[t][macId]['site'], 'coverage':coverage, 'data':total_rx+total_tx,
#                          'geo':a[t][macId]['geo'],'time':a[t][macId]['time']}
#
#             documents.append(records[t])
#
#         if documents:
#             dbmongo.aggr_data.insert(documents)
#     # time.sleep(1)
#     return "Done"


@app.route('/minuteData')
# @login_required
def minuteData():
    timeStamp=None
    try:
    # go through all sites, look at last timestamp and aggregate records for one minute and store it in the Minute colleciton
        for device in Device.objects(type = 'CPE'):
            if Minute.objects:
                lastObject = Minute.objects(site = device.connId).order_by('-time').only ('time').first()  # last record from Minute
                if lastObject:
                    timeStamp=lastObject.time
            # work on aggr_data records that has a timestamp more than 1 minute
            if timeStamp is None:
                timeStamp = int(time.time()) - 60*60*24    # TODO: change Aggr_data to link_data, 'site' to 'link', 'connId' to 'linkname'
            firstRecord = Aggr_data.objects(site = device.connId, time__gt = timeStamp).order_by('time').first()
            lastRecord = Aggr_data.objects(site = device.connId).order_by('-time').first()
            if lastRecord:
                lastTime = lastRecord.time
                if firstRecord:
                    time1 = firstRecord.time
                    time2 = firstRecord.time+60
                    if lastTime > time1+60-1:
                        while time1 < lastTime and firstRecord:
                            dataObject = dbmongo.aggr_data.aggregate([
                                {'$match':{ 'time' : { '$gt' : time1, '$lt':time2}
                                    , 'site':device.connId}},
                                # {'$limit' : 60 },
                                {'$group':{ '_id':'$site','cap' :{'$avg' : '$cap'},'tx' :{'$avg' : '$tx'},
                                       'rx' :{'$avg' : '$rx'},'data' :{'$avg' : '$data'},'distance' :{'$avg' : '$distance'}
                                }}
                            ])
                            if len(dataObject['result']) > 0:
                                minute_data = Minute( site=device.connId, time = firstRecord.time+60, tx = dataObject['result'][0]['tx'],
                                                rx = dataObject['result'][0]['rx'],cap = dataObject['result'][0]['cap'],
                                                data = dataObject['result'][0]['data'], coverage = firstRecord.coverage,
                                                distance = dataObject['result'][0]['distance'], geo = firstRecord.geo )
                                minute_data.save()
                            time1 = time1 + 60
                            time2 = time1 + 60
                            firstRecord = Aggr_data.objects(site = device.connId, time__gte = time1).first()
                else:
                    continue
    except Exception, msg:
        app.logger.error('error message in minuteData() is: %s, ' % msg)
    # time.sleep(61)
    hourData()
    return "Done"

@app.route('/hourData')
# @login_required
def hourData():
    timeStamp=None
    try:
    # go through all sites, look at last timestamp and aggregate records for one minute and store it in the Hour colleciton
        for device in Device.objects(type = 'CPE'):
            if Hour.objects:
                lastObject = Hour.objects(site = device.connId).order_by('-time').only ('time').first()  # last record from Hour
                if lastObject:
                    timeStamp=lastObject.time
            # work on aggr_data records that has a timestamp if it is more than 1 hour
            if timeStamp is None:
                timeStamp = int(time.time()) - 60*60*24
            firstRecord = Minute.objects(site = device.connId, time__gt = timeStamp).order_by('time').first()
            lastRecord = Minute.objects(site = device.connId).order_by('-time').first()
            if lastRecord:
                lastTime = lastRecord.time
                if firstRecord:
                    time1 = firstRecord.time
                    time2 = firstRecord.time+60*60
                    if lastTime > time1+60*60-60:
                        while time1 < lastTime and firstRecord:
                            dataObject = dbmongo.minute.aggregate([
                                {'$match':{ 'time' : { '$gt' : time1, '$lt':time2}
                                    , 'site':device.connId}},
                                # {'$limit' : 60 },
                                {'$group':{ '_id':'$site','cap' :{'$avg' : '$cap'},'tx' :{'$avg' : '$tx'},
                                       'rx' :{'$avg' : '$rx'},'data' :{'$avg' : '$data'},'distance' :{'$avg' : '$distance'}
                                }}
                            ])
                            if len(dataObject['result']) > 0:
                                hour_data = Hour( site=device.connId, time = firstRecord.time+60*60, tx = dataObject['result'][0]['tx'],
                                                rx = dataObject['result'][0]['rx'],cap = dataObject['result'][0]['cap'],
                                                data = dataObject['result'][0]['data'], coverage = firstRecord.coverage,
                                                distance = dataObject['result'][0]['distance'], geo = firstRecord.geo )
                                hour_data.save()
                            time1 = time1 + 60*60
                            time2 = time1 + 60*60
                            firstRecord = Minute.objects(site = device.connId, time__gte = time1).first()
                else:
                    continue
        # time.sleep(60*60+1)
    except Exception, msg:
        app.logger.error('error message in hourData(): %s, ' % msg)
    dayData()
    return "Done"

@app.route('/dayData')
# @login_required
def dayData():
    timeStamp=None
    try:
    # go through all sites, look at last timestamp and aggregate records for one day and store it in the Day colleciton
        for device in Device.objects(type = 'CPE'):
            if Day.objects:
                lastObject = Day.objects(site = device.connId).order_by('-time').only ('time').first()  # last record from Day
                if lastObject:
                    timeStamp=lastObject.time
            # work on aggr_data records that has a timestamp if it is more than 1 hour
            if timeStamp is None:
                timeStamp = int(time.time()) - 60*60*24*31
            firstRecord = Hour.objects(site = device.connId, time__gt = timeStamp).order_by('time').first()
            lastRecord = Hour.objects(site = device.connId).order_by('-time').first()
            if lastRecord:
                lastTime = lastRecord.time
                if firstRecord:
                    time1 = firstRecord.time
                    time2 = firstRecord.time+60*60*24
                    if lastTime > time1+60*60*24-60*60:
                        while time1 < lastTime and firstRecord:
                            dataObject = dbmongo.hour.aggregate([
                                {'$match':{ 'time' : { '$gt' : time1, '$lt':time2}
                                    , 'site':device.connId}},
                                # {'$limit' : 60 },
                                {'$group':{ '_id':'$site','cap' :{'$avg' : '$cap'},'tx' :{'$avg' : '$tx'},
                                       'rx' :{'$avg' : '$rx'},'data' :{'$avg' : '$data'},'distance' :{'$avg' : '$distance'}
                                }}
                            ])
                            if len(dataObject['result']) > 0:
                                day_data = Day( site=device.connId, time = firstRecord.time+60*60*24, tx = dataObject['result'][0]['tx'],
                                                rx = dataObject['result'][0]['rx'],cap = dataObject['result'][0]['cap'],
                                                data = dataObject['result'][0]['data'], coverage = firstRecord.coverage,
                                                distance = dataObject['result'][0]['distance'], geo = firstRecord.geo )
                                day_data.save()
                            time1 = time1 + 60*60*24
                            time2 = time1 + 60*60*24
                            firstRecord = Hour.objects(site = device.connId, time__gte = time1).first()
                else:
                    continue
        # time.sleep(60*60*24+1)
    except Exception, msg:
        app.logger.error('error message in dayData(): %s, ' % msg)
    monthData()
    return "Done"

@app.route('/monthData')
# @login_required
def monthData():
    try:
        timeStamp=None
        # go through all sites, look at last timestamp and aggregate records for one month and store it in the Month colleciton
        for device in Device.objects(type = 'CPE'):
            if Month.objects:
                lastObject = Day.objects(site = device.connId).order_by('-time').only ('time').first()  # last record from Month
                if lastObject:
                    timeStamp=lastObject.time
            # work on aggr_data records that has a timestamp if it is more than 1 hour
            if timeStamp is None:
                timeStamp = int(time.time()) - 60*60*24*31*12
            firstRecord = Day.objects(site = device.connId, time__gt = timeStamp).order_by('time').first()
            lastRecord = Day.objects(site = device.connId).order_by('-time').first()
            if lastRecord:
                lastTime = lastRecord.time
                if firstRecord:
                    time1 = firstRecord.time
                    time2 = firstRecord.time+60*60*24*31
                    if lastTime > time1+60*60*24*31-60*60*24:

                        while time1 < lastTime and firstRecord:
                            dataObject = dbmongo.day.aggregate([
                                {'$match':{ 'time' : { '$gt' : time1, '$lt':time2}
                                    , 'site':device.connId}},
                                # {'$limit' : 60 },
                                {'$group':{ '_id':'$site','cap' :{'$avg' : '$cap'},'tx' :{'$avg' : '$tx'},
                                       'rx' :{'$avg' : '$rx'},'data' :{'$avg' : '$data'},'distance' :{'$avg' : '$distance'}
                                }}
                            ])
                            if len(dataObject['result']) > 0:
                                month_data = Month( site=device.connId, time = firstRecord.time+60*60*24*31, tx = dataObject['result'][0]['tx'],
                                                rx = dataObject['result'][0]['rx'],cap = dataObject['result'][0]['cap'],
                                                data = dataObject['result'][0]['data'], coverage = firstRecord.coverage,
                                                distance = dataObject['result'][0]['distance'], geo = firstRecord.geo )
                                month_data.save()
                            time1 = time1 + 60*60*24*31
                            time2 = time1 + 60*60*24*31
                            firstRecord = Day.objects(site = device.connId, time__gte = time1).first()
                else:
                    continue
        # time.sleep(60*60*24+31+1)
    except Exception, msg:
            app.logger.error('error message in monthData(): %s, ' % msg)
    return "Done"

@app.route('/site')
# @login_required
def site():
    # go through all sites, add all cpe data and all bts data for each site
    global initial_time
    # time1 = initial_time
    # get all device data for current time
    try:
        dataObjects = Data.objects(Time = initial_time)
        if len(dataObjects) > 0:
            for site in Site.objects:
            # for each site iterate over all the devices
            # initialize
                site_data_cpe = {}
                site_data_cpe['tx']=0.0
                site_data_cpe['rx']=0.0
                site_data_cpe['cap']= 0.0
                site_data_cpe['data']= 0.0
                site_data_cpe['distance']=100.0
                site_data_bts = {}
                site_data_bts['tx']=0.0
                site_data_bts['rx']=0.0
                site_data_bts['cap']= 0.0
                site_data_bts['data']= 0.0
                site_data_bts['distance']=100.0
                cpePresent = False
                btsPresent = False

                for device in site.deviceList:
                    #check if device is cpe, else if device is bts get the cpe for the link
                    deviceObject = Device.objects(name = device).first()
                    deviceType = deviceObject.type
                    if deviceType == 'CPE':
                        # get all device related data objects
                        record = Data.objects(DeviceName=device, Time = initial_time).first()
                        if record:
                            site_data_cpe['geo'] = record.Location
                            site_data_cpe['type'] = 'CPE'
                            site_data_cpe['name'] = site.name
                            site_data_cpe['time'] = initial_time
                            site_data_cpe['tx'] += record.TxRate
                            site_data_cpe['rx']+= record.RxRate
                            site_data_cpe['data']+= record.Data
                            site_data_cpe['cap']+= record.MaxCapacity
                            site_data_cpe['distance']=min(record.Distance,site_data_cpe['distance'] )
                            cpePresent = True
                    else:
                        # get cpe related to the bts link
                        cpeDevice = Device.objects(name__ne = device, connId = deviceObject.connId).first()
                        if cpeDevice:
                            record = Data.objects(DeviceName=cpeDevice.name, Time = initial_time).first()
                            if record and deviceObject:
                                site_data_bts['tx']+= record.TxRate                         # data from cpe connected to bts
                                site_data_bts['rx']+= record.RxRate
                                site_data_bts['data']+= record.Data
                                site_data_bts['cap']+= record.MaxCapacity
                                site_data_bts['geo'] = (deviceObject.lat,deviceObject.lng)  # bts device location
                                site_data_bts['type'] = 'BTS'
                                site_data_bts['name'] = site.name
                                site_data_bts['time'] = initial_time
                                site_data_bts['distance']=min(record.Distance,site_data_bts['distance'] )
                                btsPresent = True

                if cpePresent:
                    siteCollection.insert(site_data_cpe)
                if btsPresent:
                    siteCollection.insert(site_data_bts)
    except Exception, msg:
        app.logger.error('error message in site(): %s, ' % msg)
    siteMinute()
    return "Done"

@app.route('/siteMinute')
# @login_required
def siteMinute():
    try:
        timeStamp=None
        # go through all sites, look at last timestamp and aggregate records for one minute and store it in the Minute colleciton
        for site in Site.objects():
            if Site_data_min.objects:
                lastObject = Site_data_min.objects(name = site.name).order_by('-time').only ('time').first()  # last record from Minute
                if lastObject:
                    timeStamp=lastObject.time
            # work on aggr_data records that has a timestamp more than 1 minute
            if timeStamp is None:
                timeStamp = int(time.time()) - 60*60*24
            firstRecord = Site_data.objects(name = site.name, time__gt = timeStamp).order_by('time').first()
            lastRecord = Site_data.objects(name = site.name).order_by('-time').first()
            if lastRecord:
                lastTime = lastRecord.time
                if firstRecord:
                    time1 = firstRecord.time
                    time2 = firstRecord.time+60
                    if lastTime > time1+60-1:
                        while time1 < lastTime and firstRecord:
                            dataObject = dbmongo.site_data.aggregate([
                                {'$match':{ 'time' : { '$gt' : time1, '$lt':time2}
                                    , 'name':site.name}},
                                # {'$limit' : 60 },
                                {'$group':{ '_id':'$site','cap' :{'$avg' : '$cap'},'tx' :{'$avg' : '$tx'},
                                       'rx' :{'$avg' : '$rx'},'data' :{'$avg' : '$data'},'distance' :{'$avg' : '$distance'}
                                }}
                            ])
                            if len(dataObject['result']) > 0:
                                minute_data = Site_data_min( name=site.name, time = firstRecord.time+60, tx = dataObject['result'][0]['tx'],
                                                rx = dataObject['result'][0]['rx'],cap = dataObject['result'][0]['cap'],
                                                data = dataObject['result'][0]['data'], distance = dataObject['result'][0]['distance'],
                                                type = firstRecord.type, geo = firstRecord.geo )
                                minute_data.save()
                            time1 = time1 + 60
                            time2 = time1 + 60
                            firstRecord = Site_data.objects(name = site.name, time__gte = time1).first()
                else:
                    continue
        # time.sleep(61)
    except Exception, msg:
            app.logger.error('error message in siteMinute(): %s, ' % msg)
    siteHour()
    return "Done"

@app.route('/siteHour')
# @login_required
def siteHour():
    try:
        timeStamp=None
        # go through all sites, look at last timestamp and aggregate records for one minute and store it in the Minute colleciton
        for site in Site.objects():
            if Site_data_hour.objects:
                lastObject = Site_data_hour.objects(name = site.name).order_by('-time').only ('time').first()  # last record from Minute
                if lastObject:
                    timeStamp=lastObject.time
            # work on aggr_data records that has a timestamp more than 1 minute
            if timeStamp is None:
                timeStamp = int(time.time()) - 60*60*24
            firstRecord = Site_data_min.objects(name = site.name, time__gt = timeStamp).order_by('time').first()
            lastRecord = Site_data_min.objects(name = site.name).order_by('-time').first()

            if lastRecord:
                lastTime = lastRecord.time
                if firstRecord:
                    time1 = firstRecord.time
                    time2 = firstRecord.time+60*60
                    if lastTime > time1+60*60-60:
                        while time1 < lastTime and firstRecord:
                            dataObject = dbmongo.site_data_min.aggregate([
                                {'$match':{ 'time' : { '$gt' : time1, '$lt':time2}
                                    , 'name':site.name}},
                                # {'$limit' : 60 },
                                {'$group':{ '_id':'$site','cap' :{'$avg' : '$cap'},'tx' :{'$avg' : '$tx'},
                                       'rx' :{'$avg' : '$rx'},'data' :{'$avg' : '$data'},'distance' :{'$avg' : '$distance'}
                                }}
                            ])
                            if len(dataObject['result']) > 0:
                                hour_data = Site_data_hour( name=site.name, time = firstRecord.time+60*60, tx = dataObject['result'][0]['tx'],
                                                rx = dataObject['result'][0]['rx'],cap = dataObject['result'][0]['cap'],
                                                data = dataObject['result'][0]['data'],distance = dataObject['result'][0]['distance'],
                                                type = firstRecord.type, geo = firstRecord.geo )
                                hour_data.save()
                            time1 = time1 + 60*60
                            time2 = time1 + 60*60
                            firstRecord = Site_data_min.objects(name = site.name, time__gte = time1).first()
                else:
                    continue
        # time.sleep(61)
    except Exception, msg:
            app.logger.error('error message in siteHour(): %s, ' % msg)
    siteDay()
    return "Done"

@app.route('/siteDay')
# @login_required
def siteDay():
    timeStamp=None
    try:
    # go through all sites, look at last timestamp and aggregate records for one minute and store it in the Minute colleciton
        for site in Site.objects():
            if Site_data_day.objects:
                lastObject = Site_data_day.objects(name = site.name).order_by('-time').only ('time').first()  # last record from Minute
                if lastObject:
                    timeStamp=lastObject.time
            # work on aggr_data records that has a timestamp more than 1 minute
            if timeStamp is None:
                timeStamp = int(time.time()) - 60*60*24*31
            firstRecord = Site_data_hour.objects(name = site.name, time__gt = timeStamp).order_by('time').first()
            lastRecord = Site_data_hour.objects(name = site.name).order_by('-time').first()
            if lastRecord:
                lastTime = lastRecord.time
                if firstRecord:
                    time1 = firstRecord.time
                    time2 = firstRecord.time+60*60*24
                    if lastTime > time1+60*60*24-60*60:
                        while time1 < lastTime and firstRecord:
                            dataObject = dbmongo.site_data_hour.aggregate([
                                {'$match':{ 'time' : { '$gt' : time1, '$lt':time2}
                                    , 'name':site.name}},
                                # {'$limit' : 60 },
                                {'$group':{ '_id':'$site','cap' :{'$avg' : '$cap'},'tx' :{'$avg' : '$tx'},
                                       'rx' :{'$avg' : '$rx'},'data' :{'$avg' : '$data'},'distance' :{'$avg' : '$distance'}
                                }}
                            ])
                            if len(dataObject['result']) > 0:
                                day_data = Site_data_day( name=site.name, time = firstRecord.time+60*60*24, tx = dataObject['result'][0]['tx'],
                                                rx = dataObject['result'][0]['rx'],cap = dataObject['result'][0]['cap'],
                                                data = dataObject['result'][0]['data'],distance = dataObject['result'][0]['distance'],
                                                type = firstRecord.type, geo = firstRecord.geo )
                                day_data.save()
                            time1 = time1 + 60*60*24
                            time2 = time1 + 60*60*24
                            firstRecord = Site_data_hour.objects(name = site.name, time__gte = time1).first()
                else:
                    continue
        # time.sleep(61)
    except Exception, msg:
            app.logger.error('error message in siteDay(): %s, ' % msg)
    siteMonth()
    return "Done"

@app.route('/siteMonth')
# @login_required
def siteMonth():
    try:
        timeStamp=None
        # go through all sites, look at last timestamp and aggregate records for one minute and store it in the Minute colleciton
        for site in Site.objects():
            if Site_data_month.objects:
                lastObject = Site_data_month.objects(name = site.name).order_by('-time').only ('time').first()  # last record from Minute
                if lastObject:
                    timeStamp=lastObject.time
            # work on aggr_data records that has a timestamp more than 1 minute
            if timeStamp is None:
                timeStamp = int(time.time()) - 60*60*24*31*12
            firstRecord = Site_data_day.objects(name = site.name, time__gt = timeStamp).order_by('time').first()
            lastRecord = Site_data_day.objects(name = site.name).order_by('-time').first()
            if lastRecord:
                lastTime = lastRecord.time
                if firstRecord:
                    time1 = firstRecord.time
                    time2 = firstRecord.time+60*60*24*31
                    if lastTime > time1+60*60*24*31-60*60*24:
                        while time1 < lastTime and firstRecord:
                            dataObject = dbmongo.site_data_month.aggregate([
                                {'$match':{ 'time' : { '$gt' : time1, '$lt':time2}
                                    , 'name':site.name}},
                                # {'$limit' : 60 },
                                {'$group':{ '_id':'$site','cap' :{'$avg' : '$cap'},'tx' :{'$avg' : '$tx'},
                                       'rx' :{'$avg' : '$rx'},'data' :{'$avg' : '$data'},'distance' :{'$avg' : '$distance'}
                                }}
                            ])
                            if len(dataObject['result']) > 0:
                                month_data = Site_data_month( name=site.name, time = firstRecord.time+60*60*24*31, tx = dataObject['result'][0]['tx'],
                                                rx = dataObject['result'][0]['rx'],cap = dataObject['result'][0]['cap'],
                                                data = dataObject['result'][0]['data'],distance = dataObject['result'][0]['distance'],
                                                type = firstRecord.type, geo = firstRecord.geo )
                                month_data.save()
                            time1 = time1 + 60*60*24*31
                            time2 = time1 + 60*60*24*31
                            firstRecord = Site_data_day.objects(name = site.name, time__gte = time1).first()
                else:
                    continue
    except Exception, msg:
        app.logger.error('error message in siteMonth(): %s, ' % msg)
    # time.sleep(61)
    minuteData()
    return "Done"

def get_ping(ip):
    result = [line.rpartition('=')[-1] for line in subprocess.check_output(['ping', '-c', '2', ip]).splitlines()[1:-4]]
    resultWithNoString = [findNumber(result[0]),findNumber(result[1])]
    average = sum(resultWithNoString) / float(len(resultWithNoString))
    return average

def get_ping_status(ip):
    value = get_status(ip)
    if value != 0:
        return get_status(ip)   # ping twice
    else:
        return value

def get_status(ip):
    res = subprocess.call(['ping', '-c', '1', '-W', '1', ip])
    if res == 0:
        app.logger.info('successfully pinged to ip: %s, ' % ip)
    elif res == 2:
        app.logger.info('no response for the pinged to ip: %s, ' % ip)
    else:
        res = -1
        app.logger.info('failed to ping the ip: %s, ' % ip)
    return  res

def findNumber (s):
    l = []
    for t in s.split():
        try:
            l.append(float(t))
        except ValueError:
            pass
    return l

def check_bandwidth(cmdOutput):
    # cmd = subprocess.Popen('speedtest', shell=True, stdout=subprocess.PIPE)
    # for line in cmd.stdout:
    for line in cmdOutput:
        if "ms" in line:
            ms = findNumber(line)
        elif "Download" in line:
            download = findNumber(line)
        elif "Upload" in line:
            upload = findNumber(line)
    return ms, download, upload

def check_iperf(cmdOutput):
    # cmd = subprocess.Popen('speedtest', shell=True, stdout=subprocess.PIPE)
    # for line in cmd.stdout:
    for line in cmdOutput:
        if "Mbits/sec" in line:
            ms = findNumber(line)
    return ms

def get_beagle():
    urlList=[]
    siteList=[]
    now = int(time.time())
    for object in Device.objects(active = True, type = 'BEAGLE'):
        urlList.append(object.url)
        siteList.append(object.site)
    for url, site in urlList, siteList:
        shell = spur.SshShell(hostname=url, username="admin", password="infinity")
        with shell:
            result = shell.run(["speedtest"])
            latency, download, upload = check_bandwidth(result.output)

        beagle_data = Beagle(site=site, time = now, latency=latency, download=download, upload=upload)
        beagle_data.save()
    # time.sleep(60*15)

def get_iperf():
    # urlList=[]
    # siteList=[]
    # now = int(time.time())
    # for object in Device.objects(active = True, type = 'BEAGLE'):
    #     urlList.append(object.url)
    #     siteList.append(object.site)
    # for url, site in urlList, siteList:
    ip = '10.0.0.8'
    result = subprocess.call(['iperf', '-c', ip, '-i1', '-w', '0.3M', '-t30'])
        # shell = spur.SshShell(hostname="10.0.0.8", username="admin", password="infinity")
        # with shell:
        #     result = shell.run(["iperf -c 10.0.0.8 -w 4M -i1 -t30"])
        #     download = check_iperf(result.output)
        #
        # beagle_data = Beagle(site=site, time = now, latency=latency, download=download, upload=upload)
        # beagle_data.save()
    # time.sleep(60*15)

def get_router():
    urlList=[]
    siteList=[]
    now = int(time.time())
    for object in Device.objects(active = True, type = 'ROUTER'):
        urlList.append(object.url)
        siteList.append(object.site)
    for url, site in urlList, siteList:
        router_data = Router(site = site, time = now, ping = get_ping(url))
        router_data.save()
    # time.sleep(60*15)

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # 6367 km is the radius of the Earth
    km = 6367 * c
    return km

def distance_in_miles(geo_bts, geo_cpe):

    try:
        dist = 0.621371 * haversine(geo_bts[1], geo_bts[0], geo_cpe[1], geo_cpe[0])
        return dist
    except :
        app.logger.exception("Value error calculating distance in miles for (%s,%s)-(%s,%s)" %(geo_bts[0], geo_bts[1],
                                                                                               geo_cpe[0], geo_cpe[1]))

def convert(data):   # convert unicode to ascii
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data


        # validate if timestamp is null and format it for the device timestamp if necessary
#     # Look at all devices 4 mins ago that has activity completion=False.
#     # Fill in total capacity and distance, calc aggr_data
#
#     now = datetime.datetime.now()
#     for device in Device.objects(active = True):
#         for data in Data.objects(mac=device.mac, completed = False, time__lt = now-datetime.timedelta(minutes=2)):
#             other_connected_device = Data.objects(connId=data.connId, mac__ne=data.mac,
#                                         time__lt = data.time + datetime.timedelta(seconds = 1),
#                                         time__gt = data.time - datetime.timedelta(seconds = 1)).first()
#             # device = Device.objects(mac = mac).first()
#
#             # get the site name for the device
#
#             site = device.site
#
#             if device.type == 'CPE':
#
#                 # get aggr_data of CPE if there is no record
#
#                 if Aggr_data.objects(time=data.time, site = site).first() is None:
#
#                     # get the other device for the site
#
#                     second_device = Device.objects(site=site, mac__ne=mac).first()
#
#                     # get the data from the other device with 1 second margin of error
#
#                     if second_device:
#                         second_device_data = Data.objects(mac=second_device.mac,
#                                 time__lt= data.time+datetime.timedelta(seconds=1),
#                                 time__gt= data.time-datetime.timedelta(seconds=1)).first()
#
#                     # add tx, rx, total_cap; take minimum distance; if total_cap > cutoff_capacity then cov = YES
#
#                         if second_device_data:
#                             total_tx = second_device_data.tx + data.tx
#                             total_rx = second_device_data.rx + data.rx
#                             total_total_cap = second_device_data.total_cap + total_cap
#                             if second_device_data.distance > distance:
#                                 min_distance = distance
#                             else :
#                                 min_distance = second_device_data.distance
#                             if total_total_cap > CUTOFF_CAPACITY:
#                                 coverage = 1
#                             else:
#                                 coverage = 0
#
#                             # prepare for bulk insert
#
#                             aggr_documents.append({"site":site,"time":timeEntry, "tx":total_tx,"rx":total_rx,
#                                  "cap":total_total_cap,"data":total_rx+total_tx,"coverage":coverage,
#                                  "distance":min_distance, "geo":geo})
#
#                 documents.append({"mac":mac,"connId":connId,"time":timeEntry, "geo":geo,"freqA":freqA,
#                     "freqB":freqB,"snrA":snrA,"snrB":snrB, "tx":tx,"rx":rx,"cap":cap,
#                     "total_cap":total_cap,"distance":distance})

    # # go through all the sites and compute aggregate data
    #
    # for object in Site.objects(all):
    #
    #     # get last entry for this site
    #
    #     timeStamp = Aggr_data.objects(site = object).order_by('-time').only ('time').first()
    #
    #     # validate if timestamp is null
    #
    #     if not timeStamp:
    #         timeStamp = datetime.datetime.now()
    #
    #     # get all devices for this site
    #
    #     devices = Device.objects(site = object)
    #
    #     # compute aggregate tx, rx, cap values for all devices for this site
    #     for device in devices:
    #         records_data = Data.objects(Q(mac = device.mac) & Q(time > timeStamp)).order_by('time').only('mac','time',
    #                           'tx','rx','total_cap','distance','geo')

# def generate_events:
#
#     if device.type == 'CPE':
#                     snr = min(snrA,snrB)
#
#                     # if snr is less than cutoff_snr and within operable distance, change ssid else change frequency
#
#                     if snr < CUTOFF_SNR and distance < DISTANCE_MAX:
#                         if ssid_event_counter == 0:
#                             start = time.time()
#                         ssid_event_counter += 1
#                         stop = time.time()
#                         delta = stop-start
#                         if ssid_event_counter >= NUM_OF_EVENTS and delta <= EVENT_TIME_INTERVAL:
#                             event=Event(device=mac, parameter='SNR='+ str(snr), message='Change SSID')
#                             event.save()
#                             url = device.url+'/api/config'
#
#                             # remove ssid of 2nd device from ssidlist choices
#
#                             if second_device:
#                                 if second_device.connId in ssidList:
#                                     ssidList.remove(second_device.connId)
#
#                                 # remove all ssids of bts_site devices that 2nd device is connected to
#
#                                 bts_site = Device.objects(connId=second_device.connId, type='BTS').first()
#                                 if bts_site:
#                                     bts_site_ssids = Site.objects(name=bts_site.name).first().ssidList
#                                     ssidList=[x for x in ssidList if x not in bts_site_ssids]
#
#                             if ssidList:
#                                 new_ssid = ssidList[0]
#                                 payload = {'connId': new_ssid}
#                                 # putRequest = requests.put(url, data=json.dumps(payload), headers=headers)
#                                 # update Device info - is this needed?
#
#                                 device.connId = new_ssid
#                                 device.save()
#
#                             # reset counter
#
#                             ssid_event_counter = 0
#                             start = time.time()
#
#                     elif snr < LOW_SNR and distance < DISTANCE_MIN:
#                         if freq_event_counter == 0:
#                             start = time.time()
#                         freq_event_counter += 1
#                         stop = time.time()
#                         delta = stop-start
#                         if freq_event_counter >= NUM_OF_EVENTS and delta <= EVENT_TIME_INTERVAL:
#                             event=Event(device=mac, parameter='SNR='+ str(snr), message='Change Frequency')
#                             event.save()
#                             if ptp_device:
#                                 url = Device.objects(mac = ptp_device.mac).first().url + '/api/config'
#                             # else:
#                             #     url = device.url+'/api/config'
#                                 # remove freqA and freqB from freqlist choices
#
#                             current_freq = [str(freqA),str(freqB)]
#                             freqList=[x for x in freqList if x not in current_freq]
#
#
#                             if freqList:
#                                 new_freq = freqList[0]
#                                 if snrA < snrB:
#                                     payload = {'freqA': new_freq}
#                                 else:
#                                     payload = {'freqB': new_freq}
#                                 putRequest = requests.put(url, data=json.dumps(payload), headers=headers)
#                             freq_event_counter = 0
#                             start = time.time()



        # for record in records_data:
        #     for item in record:
        #         total_tx[record][item] = total_tx + item.tx
        #         total_rx[record][item] = total_rx + item.rx
        #         total_data[record][item] = total_rx + total_tx
        #         cap[record][item] = cap + total_cap
        #         min_distance[record][item] = min(min_distance,item.distance)
        #         aggr_documents.append({"site":site,"time":time, "tx":total_tx,"rx":total_rx,"cap":total_total_cap,
        #                           "data":total_rx+total_tx,"cov":coverage,"distance":min_distance, "geo":geo})



        #         list[record.mac][record.time]=[{record.tx, record.rx, record.cap, record.distance}]
        # for device in list:
        #     for mac in device.mac:
        #         mac.time =


            # response = requests.get('http://127.0.0.1:5003')
            # response = requests.get(url,params=params, headers=headers,timeout=5).json()  #working
            # response = session.get(url,background_callback=bg_cb).result()  #working
            # response = session.get(url).result()   #working

            # size_of_content = len(response.content)
            # size_of_object = sys.getsizeof(response)
            # size_of_data = sys.getsizeof(response.data)
            # elementlist = response.content.split()

            # timeStamp = str(timeStamp.time)
            # timeStamp = datetime.datetime.strptime(timeStamp, '%Y-%m-%d %H:%M:%S+00:00')

            # timeEntry = datetime.datetime.strptime(obj["time"],"%Y-%m-%dT%H:%M:%S.%f").replace(microsecond=0)

            # ptp_device = Data.objects(Q(connId=connId) & Q(mac__ne=mac) & Q(time__lt = time+datetime.timedelta(seconds=5))).first()
                    # second_device = Device.objects(Q(site=site) & Q(mac__ne=mac)).first() #WORKS
                    # second_device = Device.objects(Q(site=site) and Q(mac__ne=mac)).first()  #DOES NOT WORK

# check data and generate events
# @app.route('/checkEvent')
# @login_required
# def checkEvent():
#     # average SNR from 60*5=300 documents of Data
#     # while True:
#     #     time.sleep(60*5)   #check snr of all devices every 5 minutes
#         for object in Device.objects(active = True):
#             # site_tag = object.tag[0]
#             #
#             # list.append(site_tag)
#             # for tag in object:
#
#             # mean_snr = Data.objects(Q(mac = object.mac) & Q(object.distance < 40) &
#             mean_snr = Data.objects(Q(mac = object.mac) & Q(distance < 40 ) &
#                                     Q(time < datetime.datetime.now() + datetime.timedelta(minutes=5))).average('snr')
#
#             if mean_snr < 4:
#                 Event.save({"device":object.mac, "parameter":mean_snr,"message":'Unexpected drop in capacity'})
#                 # record event, check ship_tag - device.objects(mac = object.mac).tag
#                 # in events method, check ship_tag of device to see if corresponding device had a bad snr
#                 # find corresponding device by device.object(tag = ship_tag). then find mean_snr as above
#                 # if mean_snr of both devices are bad, then record event and send alarm


# check data and change freq, SSID, and power level
# def checkSNR() :
#     site_info = Data.objects.first().mac
#     # while True:
#     #     time.sleep(60)  #check every minute
#         for object in Data.objects:
#             mean_snr = Data.objects(mac = object.mac).average('snr')
#             if mean_snr < 2:
#                 connId = 'A201'
#                 freq = 5120
#                 power = 20
#                 #change ssid

    # if distance from site 1 is high and snr is bad, then select new SSID from adjacent indexed row. e.g. if current
    # SSID of device 1 belong to site 1(id=1 set), and device 2 belong to site 2 (id=2 set), then we should select an
    # open SSID from site 3 (id=3 set)
    # if distance from site 1 is low and snr is bad, change frequency channel of device 1 (does the corresponding PTP
    # device at the site change the frequency too?)
    # Based on freq channel select power level

# def test():
#     response = requests.get('http://127.0.0.1:5002/v2/person')
#     # future = session.get('http://127.0.0.1:5002/v2/person',timeout=2, background_callback=bg_cb)
#     # response = future.result()
#     # response = session.get(url, params=params, headers=headers,timeout=2)
#     # content = response.content
#     # status = response.status_code
#     # # json_content = jsonify(content)
#     # json_content = response.data
#     # lines = json_content.splitlines(False)
#     return response.content

    # urlList = models.Device.objects.only('url')
    # timeList = latestTimeStamp(macList)
    # userData = db.User()
    # payload = {'key1': 'value1', 'key2': 'value2'}
    # response = requests.get('http://127.0.0.1:5002/v2/person')
    # future = session.get('http://127.0.0.1:5002/api/person',timeout=2, background_callback=bg_cb)
    # postRequest = requests.post(url, data=json.dumps(payload), headers=headers)
    # postRequest = requests.post(url, data=payload) //doesn't work with repeated posts, seems payload is not updated
    # deleteRequest = requests.delete(url1) #working
    # putRequest = requests.put(url1, data=json.dumps(payload), headers=headers) #working
    # postRequest = session.post(url, data=payload, headers=headers,timeout=2, background_callback=bg_cb).result()

    # response = session.get(url, params=params, headers=headers,timeout=2, background_callback=bg_cb).result()
    # response = future.result()
    # content = response.content
    # status = response.status_code
    # json_content = response.data
    # list = json_content["objects"]

# def beacon_process_file(file_content, mac_addr, archived=False):
#     logger = app.logger
#     if not file_content or not mac_addr:
#         logger.error('Invalid upload content: %s' % file_content)
#         return False
#     start_job = datetime.datetime.now()
#
#     lines = []
#     try:
#         lines = file_content.splitlines(False)
#     except AttributeError, msg:
#         logger.error('Error while splitting the lines of an upload file: %s' % msg)
#         return False
#     logger.debug("Processing "+mac_addr+" upload of "+str(len(lines)))
#
#     # build a cache of metric definitions
#     metric_definition_cache = {}
#     mdef_qs = models.MetricDefinition.objects()
#     for mdef in mdef_qs:
#         metric_definition_cache[mdef.name] = mdef
#
#     # build a cache of devices
#     devices_cache = {}
#     devices_qs = models.ManagedDevice.objects()
#     for device in devices_qs:
#         devices_cache[device.mac] = device
#
#
#     # create a cache with format records_cache[time][metric_def][target_mac]=MetricRecord
#     records_cache = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None)))
#
#     request_device = devices_cache[mac_addr]
#     if request_device is None:
#         app.logger.error(' Requested device could not be found using this mac: %s.' % mac_addr)
#         return False
#
#     is_bts = request_device.device_class.type == 'BTS'
#
#     # we will be storing all the metrics and their values into a multi-dimensional dictionary
#     #    with the following format
#     #
#     # all['METRIC_NAME']['mac:add:res'][time] = value
#     # all[time]['METRIC_NAME']['mac:add:res'] = value
#     all = defaultdict(lambda: defaultdict(lambda: defaultdict()))
#     for line in lines:
#         mline = line.replace('  ', ' ')
#         elements = mline.split(' ')
#         name = elements[0]
#         mac = elements[1]
#         time_and_value = elements[2].split(':', 1)
#         mtime = datetime.datetime.fromtimestamp(float(time_and_value[0]), pytz.utc)
#         value = time_and_value[1]
#
#         if name in ('BTS_AGGR_RX', 'CPE_RX', 'BTS_AGGR_TX', 'CPE_TX', 'BTS_PING_RESPONSE'):
#             if value != '0':
#                 value = value[:-1]+'.'+value[-1:]
#
#         all[mtime][name][mac] = value
#
#         if not archived:
#             dict_key = mac
#             dict_value = [mtime, value]
#             cache.put(dict_key, dict_value)
#
#
#     delta_onepass = datetime.datetime.now() - start_job
#     # Find out if this device is a bts or a cpe
#
#     for mtime, metrics_dict in all.items():
#         for metric, mac_dict in metrics_dict.items():
#
#             if is_bts and metric in ['CPE_LAT', 'CPE_LONG', 'CPE_SPEED', 'CPE_ALT']:
#                 # print "%s debug me" % metric
#                 continue  # these values are also provided by the CPE, no need to record them twice
#
#             for target_mac, value in mac_dict.items():
#
#                 if is_bts:
#                     cpe_device = None
#                     if target_mac != request_device.mac:
#                         cpe_device = devices_cache.get(target_mac)
#                     bts_device = request_device  # is bts
#                 else:  # is cpe
#                     cpe_device = request_device
#                     bts_device = None
#                     try:
#                         bts_mac = metrics_dict['CONNECTED_TO_BTS'][request_device.mac]
#                         bts_device = devices_cache.get(bts_mac)
#                         if not archived and request_device.connected_to != bts_device:
#                             update_connected_to_for_device(request_device.mac, bts_device.mac)
#
#
#                     except KeyError:
#                         pass  # bts_device remains None
#
#                     if metric == 'CPE_LAT':
#                         compute_composite_metrics_for_cpe(request_device, bts_device, mtime, metrics_dict, metric_definition_cache, devices_cache, record_cache=records_cache)
#
#                 process_metric_record(metric_definition_cache[metric], request_device, cpe_device, bts_device, mtime, value, with_cache=records_cache)
#         # all metrics have been parsed at this stage
#         # time to compute the composites
#         num_active = 0
#         try:
#             num_active = int(metrics_dict['NUM_ACTIVE'][request_device.mac])
#         except KeyError:
#             pass
#
#         if is_bts and num_active > 0:  # only if there are connected cpe-s it is worth calculating the composites
#             compute_composite_metrics_for_bts(request_device, mtime, metrics_dict, metric_definition_cache, devices_cache, record_cache=records_cache)
#         elif is_bts:
#             pass  # app.logger.debug("NUM_ACTIVE = 0 fro  %s at %s " % (request_device.mac, mtime))
#
#     a = 0
#     # iterate the cache and write all records
#     for time, metrics_dict in records_cache.items():
#         for metric, mac_dict in metrics_dict.items():
#             for mac, record in mac_dict.items():
#                 if record is not None:
#                     record.save()
#                 else:
#                     logger.error("MetricRecord is null for time: %s metric: %s target_mac: %s" % (time, metric, mac))
#
#     delta_end = datetime.datetime.now() - start_job
#     logger.debug("Package processed in %s.  First pass took: %s" % (delta_end, delta_onepass))
#
#     return True
#
#
# def process_metric_record(metric_definition, request_device, cpe_device, bts_device, time, value, with_cache=None):
#
#     # if metric_definition.name == "CPE_RXTX":
#     #     app.logger.debug("CPE_RX_TX =  %s at %s " %(value, time))
#
#     if not metric_definition.store:
#         return  # no need to store this metric record
#
#     ##  first of all we need to register this record
#     dt = time.replace(second=0)
#
#     target_mac = request_device.mac
#     if cpe_device is not None:
#         target_mac = cpe_device.mac
#
#     mr = None
#     if with_cache is not None:
#         mr = with_cache[dt][metric_definition.name][target_mac]
#
#     if mr is None:
#         mr = models.MetricRecord.objects(metric_definition=metric_definition, cpe_device=cpe_device, bts_device=bts_device,
#                                      time=dt).first()
#         if with_cache is not None:
#             with_cache[dt][metric_definition.name][target_mac] = mr
#
#
#     if mr is None:
#         mr = models.MetricRecord()
#         mr.bts_device = bts_device
#         mr.cpe_device = cpe_device
#         mr.metric_definition = metric_definition
#         mr.time = dt
#         mr.values = []
#         if with_cache is not None:
#             with_cache[dt][metric_definition.name][target_mac] = mr
#
#     mtick = models.MetricTick()
#     mtick.value = value
#     mtick.sec = time.time().second
#
#     if mr.metric_definition.numeric:
#         if mr.avg_numeric is None:
#             mr.avg_numeric = 0
#
#         intv = float(mtick.value)
#         mr.avg_numeric = (mr.avg_numeric * len(mr.values) + intv) / (len(mr.values) + 1)
#
#     elif mr.metric_definition.geo:
#         # for now we just overwrite but should be replaced with a geo average
#         mr.avg_geo = value
#         # update the average
#     mr.values.append(mtick)
#
#     if not mr.metric_definition.geo and not mr.metric_definition.numeric:
#         freqs = defaultdict(int)
#         for tick in mr.values:
#             freqs[tick.value] += 1
#
#         mr.avg_obj = max(freqs, key=freqs.get)
#
#     if with_cache is None:
#         mr.save()
#         # if with_cache is on it will be saved when the cache is saved
#
#
# def update_connected_to_for_device(mac_addr, bts_addr):
#     logger = logging.getLogger('metrics')
#
#     cpe_device = models.ManagedDevice.objects.filter(mac=mac_addr).first()
#     if cpe_device is None:
#         logger.error('Database Managed Device entry could not be found using MAC [ %s ].' % mac_addr)
#         return False
#
#     bts_device = models.ManagedDevice.objects.filter(mac=bts_addr).first()
#     if bts_device is None:
#         logger.error('Database Managed Device entry could not be found using MAC [ %s ].' % mac_addr)
#         return False
#
#     prior_connected_to = cpe_device.connected_to
#     cpe_device.connected_to = bts_device
#     cpe_device.save()
#     logger.info('CPE device [ %s ] disconnected from [ %s ] and is now connected to [ %s ].' %
#                 (cpe_device.name, prior_connected_to.name, cpe_device.connected_to))
#
#     return True
#
#
# def compute_composite_metrics_for_bts(request_device, mtime, metrics_dict, metric_definition_cache, devices_cache, record_cache=None):
#
#     # compute the composite metrics for a given device
#     # TPW_NOW, CPE_CAP
#     # add the code here for the computations
#
#     # invoke process_metric_record for each composite metric
#
#     # all['METRIC_NAME']['mac:add:res'][time] = value
#
#     metric_def_cpe_cap = metric_definition_cache.get('CPE_CAP')
#     metric_def_tpw_now = metric_definition_cache.get('TPW_NOW')
#     metric_def_cpe_rxtx = metric_definition_cache.get('CPE_RXTX')
#
#     # estimate the CAP
#     snr_dict = metrics_dict['CPE_SNR']
#     for target_mac, value in snr_dict.items():
#         cpe_device = devices_cache.get(target_mac)
#         # dt = datetime.datetime.fromtimestamp(float(time)).replace(tzinfo=pytz.utc)
#         snr_value = float(value)
#         mcs_value = float(metrics_dict['BTS_MCS'][target_mac])
#         rtx_value = float(metrics_dict['BTS_ARQ_RETX_PERCENT'][target_mac])
#         rx_value = float(metrics_dict['CPE_RX'][target_mac])
#         tx_value = float(metrics_dict['CPE_TX'][target_mac])
#         cpe_mcs_value = float(metrics_dict['CPE_MCS'][target_mac])
#         bts_snr_value = float(metrics_dict['BTS_SNR'][target_mac])
#
#         # modified capacity algorithm
#         number_of_cpes_value = len(snr_dict)
#
#         cpe_cap_value = get_capacity_estimate(snr_value, mcs_value, rtx_value, number_of_cpes_value)
#         #app.logger.debug('--- CPE_CAP for %s is %s' % (target_mac, str(cpe_cap_value)))
#
#         bts_cap_value = get_capacity_estimate(bts_snr_value, cpe_mcs_value, rtx_value, 1)
#         rxtx = rx_value + tx_value
#         combined_capacity = 0.0
#         if rxtx > 0:
#             combined_capacity = (tx_value/rxtx)*cpe_cap_value + (rx_value/rxtx)*bts_cap_value
#         else:
#             combined_capacity = 0.8*cpe_cap_value + 0.2*bts_cap_value
#
#         if rxtx > combined_capacity:
#             combined_capacity = rxtx
#
#         process_metric_record(metric_def_cpe_cap, request_device, cpe_device, request_device, mtime, combined_capacity, with_cache=record_cache)
#
#         tpw_now_value = 'TPW'
#         if combined_capacity < CUTOFF_CAPACITY:
#             tpw_now_value = 'SAT'
#         # if snr_value < CUTOFF_SNR:
#         #     tpw_now_value = 'SAT'
#
#         process_metric_record(metric_def_tpw_now, request_device, cpe_device, request_device, mtime, tpw_now_value, with_cache=record_cache)
#
#         #RXTX
#         process_metric_record(metric_def_cpe_rxtx, request_device, cpe_device, request_device, mtime, rx_value + tx_value, with_cache=record_cache)
#
#
# def compute_composite_metrics_for_cpe(request_device, bts_device, mtime, metrics_dict, metric_definition_cache, devices_cache, record_cache=None):
#
#     # compute the composite metrics for a given device
#     # CPE_GEO
#     # add the code here for the computations
#
#     # invoke process_metric_record for each composite metric
#
#     metric_def_cpe_geo = metric_definition_cache.get('CPE_GEO')
#     metric_def_cpe_bts_distance = metric_definition_cache.get('CPE_BTS_DISTANCE')
#
#     lat_value = float(metrics_dict['CPE_LAT'][request_device.mac])
#     long_value = float(metrics_dict['CPE_LONG'][request_device.mac])
#
#     #compute distance
#     bts_lat = float(bts_device.lat)
#     bts_long = float(bts_device.long)
#     if bts_device.mac != request_device.mac:
#         cpe_bts_distance = distance_in_miles(bts_lat, bts_long, lat_value, long_value)
#     else: # prevent distance = 0 by taking the previous value from the database
#         app.logger.error('Distance calc error - Requested device mac is equal to BTS mac: %s.' % bts_device.mac)
#         metric = models.MetricDefinition.objects.filter(name="CPE_BTS_DISTANCE").first()
#         record = models.MetricRecord.objects.only('avg_numeric').filter(cpe_device=request_device, metric_definition=metric).first()
#         cpe_bts_distance = record.avg_numeric
#     process_metric_record(metric_def_cpe_geo, request_device, request_device, bts_device, mtime, [lat_value, long_value], with_cache=record_cache)
#     process_metric_record(metric_def_cpe_bts_distance, request_device, request_device, bts_device, mtime, cpe_bts_distance,with_cache=record_cache)
#
#
# def get_capacity_estimate(snr, mcs, retransmit_percentage, number_of_cpes):
#     table = [4.47, 8.5, 12.8, 17.0, 24.5, 37.3, 40, 40, 9.0, 17, 26, 34, 48, 55, 60, 60, 13.9, 26.2, 36.8, 48, 55, 60,
#              60, 60, 18, 32, 44, 55, 60, 60, 60, 60
#             ]
#
#     mcs_low_snr = table[0]
#     capacity_estimate = table[int(round(mcs))]
#
#     #app.logger.debug('parameters are snr: %s, mcs: %s, ' % (snr, mcs))
#     #app.logger.debug('retransmit_percentage: %s, CPEs: %s, ' % (retransmit_percentage, number_of_cpes))
#
#     try:
#
#         if snr < 4:
#             capacity_estimate += (snr / 1.2) - mcs_low_snr
#             # app.logger.debug('capacity_estimate in snr < 4: %s, ' % capacity_estimate)
#
#         if snr < 7:
#             exponent = 2
#         else:
#             exponent = 1.2
#
#
#         # app.logger.debug("average capacity estimate x is : %s" % x)
#
#         capacity_estimate *= (1-(retransmit_percentage/100.0))**exponent
#         avg_capacity_estimate = capacity_estimate/number_of_cpes
#
#         # app.logger.debug("average capacity estimate is : %s" % avg_capacity_estimate)
#
#     except Exception, msg:
#         app.logger.error('error message is: %s, ' % msg)
#         app.logger.error('parameters are snr: %s, mcs: %s, ' % (snr, mcs))
#         app.logger.error('retransmit_percentage: %s, CPEs: %s, ' % (retransmit_percentage, number_of_cpes))
#
#         return 0
#
#     return avg_capacity_estimate
#
#
# def get_30_data(p_cpe_device,p_metric_name):
#     logger = app.logger
#
#     #thirtydays_data = OrderedDict()
#     start_date = datetime.datetime.now() + datetime.timedelta(-30)
#     #for filter_data in models.MetricDefinition.objects(name = p_metric_name):
#      #   for t_data in models.MetricRecord.find({"time": {"$gt": start_date}}):
#             #print t_data
#     try:
#
#
#         metric_def = models.MetricDefinition.objects(name=p_metric_name).first()
#         app.logger.info("Metric passed to func: %s" % metric_def)
#
#
#         device = models.ManagedDevice.objects(name=p_cpe_device).first()
#         app.logger.info("Device passed to func: %s" % device)
#
#         metric_record_qset = models.MetricRecord.objects(metric_definition=metric_def, cpe_device=device,
#                                                         time__gte=start_date)
#
#         sum = 0
#         for metric_record in metric_record_qset:
#             sum += metric_record.avg_numeric
#         total_avg = sum / len(metric_record_qset)
#
#         app.logger.info("Total Avg from func: %s" % total_avg)
#
#
#     except Exception, msg:
#         app.logger.error('could not get last know metric[%s] value for %s. Error message: %s' % (p_metric_name, p_cpe_device, msg))
#         return None
#
#     return total_avg
#
#
# def get_lastvalue_for_metric(device, metric_name, use_beacon_cache=False, use_beacon_only=False):
#
#     logger = app.logger
#     if use_beacon_cache:
#         # first try to get it from the beacon_cache
#         value = cache.get(device.mac)
#         if value is not None:
#             return value[1]
#
#     # Get metric definition
#     metric = None
#     try:
#         metric_def = models.MetricDefinition.objects.filter(name=metric_name).first()
#         metric_record = models.MetricRecord.objects.filter(metric_definition=metric_def, cpe_device=device).order_by('-time').limit(1).first()
#         return metric_record.values[-1].value
#     except Exception, msg:
#         logger.error('could not get last know metric[%s] value for %s. Error message: %s' % (metric_name, device.name, msg))
#         if metric_name == 'CPE_GEO':
#             return [device.lat, device.long]
#         else:
#             return None
#
#
# def get_lastknown_latlong(device):
#     value = get_lastvalue_for_metric(device, 'CPE_GEO', use_beacon_cache=True)
#     if value is None:
#         return [device.lat, device.long]
#     else:
#         return value
#
#
def distance_on_unit_sphere(lat1, long1, lat2, long2):

    if lat1 == lat2 and long1 == long2:
        return 0

    # Convert latitude and longitude to
    # spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0

    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians

    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians

    # Compute spherical distance from spherical coordinates.

    # For two locations in spherical coordinates
    # (1, theta, phi) and (1, theta, phi)
    # cosine( arc length ) =
    #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length

    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) +
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos(cos)

    # Remember to multiply arc by the radius of the earth
    # in your favorite set of units to get length.
    return arc


# def distance_in_miles(lat1, long1, lat2, long2):
#     logger = app.logger
#     try:
#         arc = distance_on_unit_sphere(lat1, long1, lat2, long2)
#         return 3960 * arc
#     except ValueError as ve:
#         logger.exception("Value error calculating distance in miles for (%s,%s)-(%s,%s)" %(lat1,long1, lat2, long2))


def distance_in_miles_latlong(lat1, long1, lat2, long2):
    logger = app.logger
    try:
        arc = distance_on_unit_sphere(lat1, long1, lat2, long2)
        return 3960 * arc
    except ValueError as ve:
        logger.exception("Value error calculating distance in miles for (%s,%s)-(%s,%s)" %(lat1,long1, lat2, long2))


def send_email(subject, recipients, text_body, html_body, sender=app.config['MAIL_USERNAME']):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

def get_events():
    results = []
    event_qset = models.EventRecord.objects()
    for event in event_qset:
        e = event.detach()
        results.append(e)

    return results


def get_recipients_for_trap(event_trap, device):

    emails = []

    if event_trap.notify_owner_roles is not None:
        for user in device.owner.users:
            if set(user.roles).intersection(event_trap.notify_owner_roles) is not None:
                emails.append(user.email)

    if event_trap.notify_operator_roles is not None:
        for user in device.owner.users:
            if set(user.roles).intersection(event_trap.notify_operator_roles) is not None:
                emails.append(user.email)

    return emails


def handle_status_change(device, current_status, prev_status):

    q = Q(devices=None) | Q(devices__contains=device)
    q = q & Q(type=models.EVENT_TYPES[0]) & Q(active=True)

    traps = models.EventTrap.objects.filter(q)
    if traps is not None:

        message = flask.render_template("notifications/status_change.html", device=device,
                                        current_status=current_status, prev_status=prev_status)

    for trap in traps:
        # trap triggered
        emails = get_recipients_for_trap(trap, device)
        send_email("NMS Event Alert", emails, message, message)


#  def get_scheduled_jobs_for_device(device):
# 62	62	     ctx = {}
# 63	63	     max = 0
# 64	 	-    jobs_qset = models.JobSchedule.objects(device=device, status='scheduled')
#  	64	+    jobs_qset = models.JobSchedule.objects(device=device, status__lte=models.JOB_STATUS_SCHEDULED)
# 65	65	     for job in jobs_qset:
# 66	66	         if job.timestamp > max:
# 67	67	             max = job.timestamp
# 68	68
# 69	69	     return {'jobstamp':max}
#  	70	+
#  	71	+
#  	72	+def get_available_firmware_images_for_device(device):
#  	73	+    # currently we return all active images
#  	74	+    # later we should make the selection firmware version based
#  	75	+
#  	76	+    data = []
#  	77	+    images = models.FirmwareImage.objects.filter(retired=False)
#  	78	+    for img in images:
#  	79	+            data.append({'version':str(img.version),
#  	80	+                         'description':str(img.description),
#  	81	+                         'id':str(img.pk)})
#  	82	+    return data
#
# +@app.route('/config/popup/<mac>/update-firmware', methods=['POST','GET'])
#  	148	+def config_popup_update_firmware(mac):
#  	149	+    device = models.ManagedDevice.objects.filter(mac=mac).first()
#  	150	+    firmwares = config_services.get_available_firmware_images_for_device(device)
#  	151	+    return flask.render_template('config/popups/update_firmware.html', mac=mac, firmwareSource=firmwares)

# +import flask
#  	2	+import models, security
#  	3	+from collections import defaultdict
#  	4	+
#  	5	+
#  	6	+def get_pending_jobs(for_device):
#  	7	+
#  	8	+    schedules = models.JobSchedule.objects.filter(device=for_device, status__lte=models.JOB_STATUS_SCHEDULED)
#  	9	+    groups = defaultdict(int)
#  	10	+    for sch in schedules:
#  	11	+        groups[sch.job_type] += 1
#  	12	+
#  	13	+    return groups
#  	14	+
#  	15	+
#  	16	+def schedule_update(device, firmware, date, auto):
#  	17	+    sch = models.JobSchedule()
#  	18	+    sch.job_type = models.JOB_TYPES[0][0]
#  	19	+    sch.status = models.JOB_STATUS_DEFINED
#  	20	+    sch.device = device
#  	21	+    sch.image = firmware
#  	22	+    sch.time = date
#  	23	+    sch.auto = auto
#  	24	+    sch.save()

from flask_wtf import Form
# 7	7	 import os
# 8	8	 import flask
#  	9	+import datetime
#  	10	+import random
#  	11	+import math
#  	12	+import pytz
# 9	13
# 10	14	 from flask.ext.mongoengine.wtf import model_form
# 11	15	 from mongoengine.queryset import Q
# ...	...	@@ -19,7 +23,7 @@
# 19	23	 from nmsapp import app
# 20	24	 import json
# 21	25
# 22	 	-import config_services, event_services
#  	26	+import config_services, event_services, engineer_services
# 23	27
# 24	28
# 25	29	 @app.route('/manager/inventory')
# ...	...	@@ -31,7 +35,7 @@
# 31	35	 @app.route('/manager/devices', methods=['POST','GET'])
# 32	36	 @login_required
# 33	37	 def inventory_devices():
# 34	 	-    logger = logging.getLogger('metrics')
#  	38	+    logger = app.logger
# 35	39	     from nmsapp import BEACON_DICT
# 36	40	     devices = []
# 37	41	     auser = current_user
# ...	...	@@ -51,7 +55,7 @@
# 51	55	     for device in devices:
# 52	56
# 53	57	         device_data = device.detach(graph='inventory')
# 54	 	-        device_data['jobs']={'fmw':2,'cfg':1}
#  	58	+        device_data['jobs'] = engineer_services.get_pending_jobs(device)
# 55	59
# 56	60	         if dtype is not None:
# 57	61	             if device.device_class.type == dtype:
# ...	...	@@ -68,7 +72,7 @@
# 68	72	     return render_template('config/configuration_packages.html')
# 69	73
# 70	74
# 71	75	-app.route('/config/packages-data', methods=['POST', 'GET'])
# 72	76	+@app.route('/config/packages-data', methods=['POST', 'GET'])
# 73	77	 @login_required
# 74	78	 def config_packages_data():
# 75	79	     logger = logging.getLogger('metrics')
# ...	...	@@ -144,6 +148,24 @@
# 144	148	     code = request.data
# 145	149	     cdir = os.path.dirname(os.path.abspath(__file__))
# 146	150	     open(cdir+'/et_capacity_estimation.py', 'w').write(code)
#  	151	+
#  	152	+    return jsonify(success=True)
#  	153	+
#  	154	+
#  	155	+@app.route('/engineer/<mac>/schedule-firmware-update', methods=['GET', 'POST'])
#  	156	+def schedule_firmware_update(mac):
#  	157	+
#  	158	+    logger = app.logger
#  	159	+
#  	160	+    device = models.ManagedDevice.objects.filter(mac=mac).first()
#  	161	+
#  	162	+    firmware = models.FirmwareImage.objects.filter(pk=flask.request.values['fmw']).first()
#  	163	+
#  	164	+    epoch = int(flask.request.values['date'])
#  	165	+    date = datetime.datetime.fromtimestamp(float(epoch), tz=pytz.utc)
#  	166	+    auto = flask.request.values['auto'] == 'on'
#  	167	+
#  	168	+    engineer_services.schedule_update(device, firmware, date, auto)
# 147	169
# 148	170	     return jsonify(success=True)

   # data_cap=[]
   #  for data in dataObjects2:
   #      data_cap.append(data.cap)
   #  l = data_cap
   #  avg = sum(l) / float(len(l))
   #  map = Code('function() {'
   #                    'var key = this.site;'
   #                    'var value = {'
   #                                  'site: this.site,'
   #                                  'total_time: this.length,'
   #                                  'count: 1,'
   #                                  'avg_time: 0'
   #                                ' };'
   #
   #                    'emit( key, value );'
   #               ' };')
   #  reduce = Code('function(key, values) {'
   #
   #                      'var reducedObject = {'
   #                                            'userid: key,'
   #                                            'total_time: 0,'
   #                                            'count:0,'
   #                                            'avg_time:0'
   #                                          '};'
   #
   #                      'values.forEach( function(value) {'
   #                                            'reducedObject.total_time += value.total_time;'
   #                                            'reducedObject.count += value.count;'
   #                                      '}'
   #                                    ');'
   #                      'return reducedObject;'
   #                   '};'
   #  )
   #  finalize = Code ('function (key, reducedValue) {'
   #                        'if (reducedValue.count > 0)'
   #                            'reducedValue.avg_time = reducedValue.total_time / reducedValue.count;'
   #                        'return reducedValue;'
   #                     '};'
   #  )

    # map_reduce = Code (db.sessions.mapReduce( mapFunction,
    #                    reduceFunction,
    #                    {
    #                      query: { ts: { $gt: ISODate('2011-11-05 00:00:00') } },
    #                      out: { reduce: "session_stat" },
    #                      finalize: finalizeFunction
    #                    }
    #                  );
    #                  )
    #
    # )
    # result = dbmongo.aggr_data.map_reduce(map, reduce, finalize_f=finalize, out={'merge':"sixty"}, query={"time":{"$gt": gtTime})

# @app.route('/sixtyDataProto')
# @login_required
# def sixtyData1():
#     dataObjects0 = Aggr_data.objects(sixty = False, time__lt = datetime.datetime.now()
#                                                           -datetime.timedelta(seconds=SIXTY_TIME_DELAY),
#                            time__gt = datetime.datetime.now()-
#                                       datetime.timedelta(days=MAX_DAYS))[:5]
#     dataObjects1 = Aggr_data.objects(sixty = False, time__lt = datetime.datetime.now()
#                                                           -datetime.timedelta(seconds=SIXTY_TIME_DELAY),
#                            time__gt = datetime.datetime.now()-
#                                       datetime.timedelta(days=MAX_DAYS)).order_by('time')[:5]
#     dataObjects3 = Aggr_data.objects(sixty = False, time__lt = datetime.datetime.now()
#                                                           -datetime.timedelta(seconds=SIXTY_TIME_DELAY),
#                            time__gt = datetime.datetime.now()-
#                                       datetime.timedelta(days=MAX_DAYS)).order_by('time')[:5].sum('cap')
#     dataObjects2 = Aggr_data.objects(sixty = False)[:5]
#     gtTime = datetime.datetime.now()-datetime.timedelta(days=MAX_DAYS)
#     ltTime = datetime.datetime.now()-datetime.timedelta(seconds=SIXTY_TIME_DELAY)
#     dataObjects4 = dbmongo.aggr_data.aggregate([
#                         {'$match':{ 'sixty' : False } },
#                         {'$limit' : 60 },
#                         {'$group':{ '_id':'$site','cap' :{'$avg' : '$cap'},'tx' :{'$avg' : '$tx'},
#                                     'rx' :{'$avg' : '$rx'},'data' :{'$avg' : '$data'},'distance' :{'$avg' : '$distance'}
#                                      }}
#     ])
#     dataObjects5 = dbmongo.aggr_data.distinct('geo')[:5]
#     #, {'time' : { '$gt' : 'gtTime', '$lt' : 'ltTime'} }
#     data_cap=[]
#     for data in dataObjects2:
#         data_cap.append(data.cap)
#     l = data_cap
#     avg = sum(l) / float(len(l))
#     map = Code('function() {'
#                       'var key = this.site;'
#                       'var value = {'
#                                     'site: this.site,'
#                                     'total_time: this.length,'
#                                     'count: 1,'
#                                     'avg_time: 0'
#                                   ' };'
#
#                       'emit( key, value );'
#                  ' };')
#     reduce = Code('function(key, values) {'
#
#                         'var reducedObject = {'
#                                               'userid: key,'
#                                               'total_time: 0,'
#                                               'count:0,'
#                                               'avg_time:0'
#                                             '};'
#
#                         'values.forEach( function(value) {'
#                                               'reducedObject.total_time += value.total_time;'
#                                               'reducedObject.count += value.count;'
#                                         '}'
#                                       ');'
#                         'return reducedObject;'
#                      '};'
#     )
#     finalize = Code ('function (key, reducedValue) {'
#                           'if (reducedValue.count > 0)'
#                               'reducedValue.avg_time = reducedValue.total_time / reducedValue.count;'
#                           'return reducedValue;'
#                        '};'
#     )
#
#     # map_reduce = Code (db.sessions.mapReduce( mapFunction,
#     #                    reduceFunction,
#     #                    {
#     #                      query: { ts: { $gt: ISODate('2011-11-05 00:00:00') } },
#     #                      out: { reduce: "session_stat" },
#     #                      finalize: finalizeFunction
#     #                    }
#     #                  );
#     #                  )
#     #
#     # )
#     # result = dbmongo.aggr_data.map_reduce(map, reduce, finalize_f=finalize, out={'merge':"sixty"}, query={"time":{"$gt": gtTime})
#     return "Done"
# @app.route('/getdata')
# @login_required
# @run_once

# def dataLayer():
#     getDataTime=0
#     processTime =0
#     siteTime =0
#     minuteTime =0
#     hourTime =0
#     dayTime = 0
#     monthTime = 0
#     while True:
#         if time.time()-getDataTime >= 1:
#             getDataTime = time.time()
#             getData()
#         # if time.time()-processTime >= 1:
#         #     processTime = time.time()
#             processData()
#         # if time.time()-siteTime >= 1:
#         #     siteTime = time.time()
#         #     aggrData()
#             siteData()
#         if time.time()-minuteTime >= 60:
#             minuteTime = time.time()
#             minuteData()
#         if time.time()-hourTime >= 60*60:
#             hourTime = time.time()
#             hourData()
#         if time.time()-dayTime >= 60*60*24:
#             dayTime = time.time()
#             dayData()
#         if time.time()-monthTime >= 60*60*24*30:
#             monthTime = time.time()
#             monthData()
#
#     # backProc = Process(target=processData_, args=())
#     #
#     # backProc.start()
#     # pool = Pool(processes=8)
#     # app.run(debug=True, use_reloader=False)
#     # while True:
#     #     getData()
#     #     processData
#     #     siteData()
#     #     minuteData()
#     #     hourData()
#     #     dayData()
#     #     get_beagle()
#     #     get_router()
#
#         # pool = ThreadPool(8)              # start 4 worker processes
#         # # result = pool.apply_async(f, [10])
#         # pool.apply_async(getData())
#         # pool.apply_async(processData, ())
#         # pool.apply_async(siteData, ())
#         # pool.apply_async(minuteData, ())
#         # pool.apply_async(hourData, ())
#         # pool.apply_async(dayData, ())
#         # pool.apply_async(get_beagle, ())
#         # pool.apply_async(get_router, ())
#         # app.logger.info( " %s" % result.get())
#         # app.logger.info("ProcessData in progress...")
#
#         # pool.close()
#         # pool.join()
