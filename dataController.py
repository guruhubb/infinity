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
import multiprocessing
from threading import Thread
from flask import json
from flask import request
import threading
from eventlet.green import urllib2
import requests

import xmltodict
import re
import urllib2

dataController = Blueprint('dataController', __name__, template_folder='templates')

import pymongo
dbmongo = pymongo.MongoClient('mongodb://localhost:27017/').infinity
from pymongo import Connection
connection = Connection()
db = connection['infinity']
dataCollection = db.data
data0Collection = db.data0
siteCollection = db.site_data
linkCollection = db.aggr_data

# DISTANCE_MAX = 40
# DISTANCE_MIN = 10
INTERVAL = 0.95
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

        p0 = multiprocessing.Process(target=self.run, args=())
        # p0.daemon = True                            # Daemonize thread
        p0.start()                                  # Start the execution
        p1 = multiprocessing.Process(target=self.sixtyData_(), args=())
        # thread.daemon = True                            # Daemonize thread
        p1.start()
        p2 = multiprocessing.Process(target=self.hourData_(), args=())
        # thread.daemon = True                            # Daemonize thread
        p2.start()
        p3 = multiprocessing.Process(target=self.dayData_(), args=())
        # thread.daemon = True                            # Daemonize thread
        p3.start()

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

def getData_():
    while True:
        try:
            get_data()
        except Exception, msg:
            app.logger.error('error message from getData is: %s, ' % msg)
        # time.sleep(1)

def minuteData_():
    while True:
        try:
            minuteData()
        except Exception, msg:
            app.logger.error('error message from sixtyData is: %s, ' % msg)
        time.sleep(30)

def hourData_():
    while True:
        try:
            hourData()
        except Exception, msg:
            app.logger.error('error message from hourData is: %s, ' % msg)
        time.sleep(60*30)

def dayData_():
    while True:
        try:
            dayData()
        except Exception, msg:
            app.logger.error('error message from dayData is: %s, ' % msg)
        time.sleep(60*60*12)

def monthData_():
    while True:
        try:
            monthData()
        except Exception, msg:
            app.logger.error('error message from monthData is: %s, ' % msg)
        time.sleep(60*60*24*15)

def siteMinuteData_():
    while True:
        try:
            siteMinute()
        except Exception, msg:
            app.logger.error('error message from sixtyData is: %s, ' % msg)
        time.sleep(30)

def siteHourData_():
    while True:
        try:
            siteHour()
        except Exception, msg:
            app.logger.error('error message from hourData is: %s, ' % msg)
        time.sleep(60*30)

def siteDayData_():
    while True:
        try:
            siteDay()
        except Exception, msg:
            app.logger.error('error message from dayData is: %s, ' % msg)
        time.sleep(60*60*12)

def siteMonthData_():
    while True:
        try:
            siteMonth()
        except Exception, msg:
            app.logger.error('error message from monthData is: %s, ' % msg)
        time.sleep(60*60*24*15)

def deleteOld_():
    while True:
        try:
            deleteOld()
        except Exception, msg:
            app.logger.error('error message from deleteOld is: %s, ' % msg)
        time.sleep(60*60*24)

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
    t2 = Thread(target = minuteData_)
    t3 = Thread(target = hourData_)
    t4 = Thread(target = dayData_)
    t5 = Thread(target = monthData_)
    t6 = Thread(target = siteMinuteData_)
    t7 = Thread(target = siteHourData_)
    t8 = Thread(target = siteDayData_)
    t9 = Thread(target = siteMonthData_)
    t10 = Thread(target = deleteOld_)
    # t1.setDaemon(True)
    t2.setDaemon(True)
    t3.setDaemon(True)
    t4.setDaemon(True)
    t5.setDaemon(True)
    t6.setDaemon(True)
    t7.setDaemon(True)
    t8.setDaemon(True)
    t9.setDaemon(True)
    t10.setDaemon(True)
    # t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t6.start()
    t7.start()
    t8.start()
    t9.start()
    t10.start()
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
    global  initial_time
    if ((int(time.time()) - initial_time) > INTERVAL):
        initial_time = int(time.time())

        url_list =[]
        for object in Device.objects(active = True, type = 'CPE'):

            url_list.append('http://'+object.url+'/core/api/service/status.php?username=infinity&password=123')
            url_list.append('http://'+object.url + '/core/api/service/device-info.php?username=infinity&password=123')
            url_list.append('http://'+object.url + '/core/api/service/link-info.php?username=infinity&password=123')

        doc_=[]
        pool = eventlet.GreenPool()
        # use multiple threads to get data from each device and parse it
        app.logger.info('Fetching data at %s'  % str(datetime.datetime.now()))

        for data in pool.imap(fetch, url_list):
        # for url in url_list:
        #     data = urllib2.urlopen(url).read()
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
    # hourData()
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
    # dayData()
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
    # monthData()
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
        dataObjects = Data.objects(time = initial_time)
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
                        record = Data.objects(deviceName=device, time = initial_time).first()
                        if record:
                            site_data_cpe['geo'] = (record.lat, record.long)
                            site_data_cpe['type'] = 'CPE'
                            site_data_cpe['name'] = site.name
                            site_data_cpe['time'] = initial_time
                            site_data_cpe['tx'] += record.tx
                            site_data_cpe['rx']+= record.rx
                            site_data_cpe['data']+= record.data
                            site_data_cpe['cap']+= record.cap
                            site_data_cpe['distance']=min(record.distance,site_data_cpe['distance'] )
                            cpePresent = True
                    else:
                        # get cpe related to the bts link
                        cpeDevice = Device.objects(name__ne = device, connId = deviceObject.connId).first()
                        if cpeDevice:
                            record = Data.objects(deviceName=cpeDevice.name, time = initial_time).first()
                            if record and deviceObject:
                                site_data_bts['tx']+= record.tx                         # data from cpe connected to bts
                                site_data_bts['rx']+= record.rx
                                site_data_bts['data']+= record.data
                                site_data_bts['cap']+= record.cap
                                site_data_bts['geo'] = (deviceObject.lat,deviceObject.lng)  # bts device location
                                site_data_bts['type'] = 'BTS'
                                site_data_bts['name'] = site.name
                                site_data_bts['time'] = initial_time
                                site_data_bts['distance']=min(record.distance,site_data_bts['distance'] )
                                btsPresent = True

                if cpePresent:
                    siteCollection.insert(site_data_cpe)
                if btsPresent:
                    siteCollection.insert(site_data_bts)
    except Exception, msg:
        app.logger.error('error message in site(): %s, ' % msg)
    # siteMinute()
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
    # siteHour()
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
    # siteDay()
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
    # siteMonth()
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
    # minuteData()
    return "Done"

@app.route('/deleteOld')
def deleteOld():
    try:
        now = time.time()
        oldTime = now - 7*24*60*60
        oldTimeMinute = now - 365*24*60*60
        a = Data.objects.count()
        app.logger.info('Data, Aggr_data, Site_data, Minute, Site_data_min counts BEFORE are %s, %s, %s, %s, %s'
                        % (Data.objects.count(), Aggr_data.objects.count(), Site_data.objects.count(),
                        Minute.objects.count(), Site_data_min.objects.count()))
        Data.objects(time__lte = oldTime).delete()
        Aggr_data.objects(time__lte = oldTime).delete()
        Site_data.objects(time__lte = oldTime).delete()
        Minute.objects(time__lte = oldTimeMinute).delete()
        Site_data_min.objects(time__lte = oldTimeMinute).delete()
        app.logger.info('executed deleteOld()')
        app.logger.info('Data, Aggr_data, Site_data, Minute, Site_data_min counts AFTER are %s, %s, %s, %s, %s'
                        % (Data.objects.count(), Aggr_data.objects.count(), Site_data.objects.count(),
                        Minute.objects.count(), Site_data_min.objects.count()))

    except Exception, msg:
            app.logger.error('error message in deleteOld(): %s, ' % msg)

    return "Done"

@app.route('/oldDeviceData', methods = ['GET','POST'])
def oldDeviceData():
    # try:
    a = request.data
    app.logger.info('data: %s ' % a)
    # b = request.get_data(parse_form_data=True)
    # c = request.get_data()
    # d = request.values
    # e = request.args
    # f = request.host_url
    # g = request.host
    # data_dumps = Response(json.dumps(json.loads(a)),  mimetype='application/json')
    return a
    # return json.dumps({'request data': request.data})
    #     # a = "JSON Message: " + json.dumps(request.json)
    #     # print a
    # except Exception, msg:
    #         app.logger.error('error message in deviceData(): %s, ' % msg)

@app.route('/deviceData', methods = ['GET','POST'])
def deviceData():
    # try:
    global  initial_time
    # if ((int(time.time()) - initial_time) > INTERVAL):
    initial_time = int(time.time())
    a = json.loads(request.data)
    app.logger.info('data: %s ' % a)
    c = json.dumps(a)
    a['data'] = a['tx'] + a['rx']
    a['time'] = initial_time
    dataCollection.insert(a)
    # copy subset of data table to link table
    link_ = collections.OrderedDict()
    link_['site'] = a['linkName']
    link_['time'] = initial_time
    link_['tx'] = a['tx']
    link_['rx'] = a ['rx']
    link_['cap'] = a['cap']
    link_['data']= a['data']
    link_['coverage']=True
    link_['distance']=a['distance']
    link_['geo']=(a['lat'],a['long'])
    linkCollection.insert(link_)
    # d=Aggr_data.objects.order_by('-time').first()
    site()
    # startdata()
    return c


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


