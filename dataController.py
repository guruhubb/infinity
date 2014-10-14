from requests_futures.sessions import FuturesSession
from flask.ext.security import login_required
from tools import timeit
import logging
import models
import datetime
import pytz
import math
import time
import json
import flask
import requests
import random
import sys
from mongoengine import Q
#from collections import OrderedDict
from flask.ext.mail import Message
from infinity import mail, app, cache, Device, Data, Event, Site, Aggr_data, Freq, Ssid
from collections import defaultdict

import pymongo
dbmongo = pymongo.MongoClient().infinity

DISTANCE_MAX = 40
DISTANCE_MIN = 10
CUTOFF_CAPACITY = 2
CUTOFF_SNR = 2
LOW_SNR = 10
NUM_OF_EVENTS = 1
EVENT_TIME_INTERVAL = 5
session = FuturesSession(max_workers=10)
headers = {'Content-Type': 'application/json'}

def bg_cb(sess, resp):
    # parse the json storing the result on the response object
    resp.data = resp.json()

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

# @app.route('/startdata')
# @login_required
# @run_once
def startdata():
    try:
        # while True:
            getData()
            time.sleep(1)
    except Exception, msg:
            app.logger.error('error message is: %s, ' % msg)
    return "Start getting data from device"

@app.route('/getData')
@login_required
def getData(ssid_event_counter=0, freq_event_counter=0, start=time.time()):
    urlList = []
    macList = []
    timeList = []
    totaldocuments = []
    msg = ""

    # go through all the devices and make a list of url, mac, latest timestamp of data

    for object in Device.objects(active = True):
        urlList.append(object.url+'/api/device')   # need /api/device affix in the url
        macList.append(object.mac)
        timeStamp = Data.objects(mac = object.mac).order_by('-time').only ('time').first()

        # validate if timestamp is null and format it for the device timestamp if necessary

        if timeStamp:
            timeStamp = timeStamp.time
            # timeStamp = datetime.datetime.strptime(timeStamp,"%Y-%m-%dT%H:%M:%S.%f")
            timeStamp = timeStamp.strftime('%Y-%m-%d %H:%M:%S.%f')
            timeList.append(timeStamp)
        else:
            timeList.append(datetime.datetime.now()-datetime.timedelta(hours=1))

    # do REST calls and get new data

    for url, timeItem in zip(urlList,timeList):

        # get new data gt (time.now - 1 hr), make sure time is in string format

        filters = [dict(name='time', op='gt', val=str(timeItem))]
        params = dict(q=json.dumps(dict(filters=filters)))
        try:
            response = session.get(url,params=params, headers=headers,timeout=5,background_callback=bg_cb).result()
            if len(response.data["objects"]) is 0:
                continue
            documents=[]
            aggr_documents=[]
            for obj in response.data["objects"]:
                mac = obj["mac"]
                connId = obj["connId"]
                timeEntry = datetime.datetime.strptime(obj["time"],"%Y-%m-%dT%H:%M:%S.%f")
                lat = obj["lat"]
                long = obj["long"]
                freqA = obj["freqA"]
                freqB = obj["freqB"]
                snrA = obj["snrA"]
                snrB = obj["snrB"]
                tx = obj["tx"]
                rx = obj["rx"]
                cap = obj["cap"]
                freqList = obj["freqList"].split()  # ordered list of available clear channels separated by whitespace
                ssidList = obj["ssidList"].split()  # ordered list of available ssids channels separated by whitespace

                geo = (lat,long)

                # get the other device records on the ptp link to calculate total capacity and distance
                time_s = timeEntry.replace(microsecond=0)
                ptp_device = Data.objects(connId=connId, mac__ne=mac, time__lt = time_s+datetime.timedelta(seconds=5),
                            time__gt= time_s-datetime.timedelta(seconds=5)).first()  # find a bts match within 10s of data

                if ptp_device:
                    cap_ptp_device = ptp_device.cap
                    total_cap = cap + cap_ptp_device
                    distance = distance_in_miles(ptp_device,geo)
                else:
                    # ptp_device = Device.objects(connId__contains=connId).first().mac
                    total_cap = cap
                    distance = random.uniform(1,10)

                device = Device.objects(mac = mac).first()

                # get the site name for the device

                site = device.site

                if device.type == 'CPE':

                    # get aggr_data of CPE if there is no record

                    if Aggr_data.objects(time=timeEntry, site = site).first() is None:

                        # get the other device for the site

                        second_device = Device.objects(site=site, mac__ne=mac).first()

                        # get the data from the other device with 3 second margin of error
                        if second_device:
                            second_device_data = Data.objects(mac=second_device.mac,
                                    time__lt= timeEntry+datetime.timedelta(seconds=5),
                                    time__gt= timeEntry-datetime.timedelta(seconds=5)).first()

                        # add tx, rx, total_cap; take minimum distance; if total_cap > cutoff_capacity then cov = YES
                            if second_device_data:
                                total_tx = second_device_data.tx + tx
                                total_rx = second_device_data.rx + rx
                                total_total_cap = second_device_data.total_cap + total_cap
                                if second_device_data.distance > distance:
                                    min_distance = distance
                                else :
                                    min_distance = second_device_data.distance
                                if total_total_cap > CUTOFF_CAPACITY:
                                    coverage = 1
                                else:
                                    coverage = 0

                                # prepare for bulk insert

                                aggr_documents.append({"site":site,"time":timeEntry, "tx":total_tx,"rx":total_rx,
                                     "cap":total_total_cap,"data":total_rx+total_tx,"coverage":coverage,
                                     "distance":min_distance, "geo":geo})

                documents.append({"mac":mac,"connId":connId,"time":timeEntry, "geo":geo,"freqA":freqA,
                    "freqB":freqB,"snrA":snrA,"snrB":snrB, "tx":tx,"rx":rx,"cap":cap,
                    "total_cap":total_cap,"distance":distance})

                # generate events for CPE devices only

                if device.type == 'CPE':
                    snr = min(snrA,snrB)

                    # if snr is less than cutoff_snr and within operable distance, change ssid else change frequency

                    if snr < CUTOFF_SNR and distance < DISTANCE_MAX:
                        if ssid_event_counter == 0:
                            start = time.time()
                        ssid_event_counter += 1
                        stop = time.time()
                        delta = stop-start
                        if ssid_event_counter >= NUM_OF_EVENTS and delta <= EVENT_TIME_INTERVAL:
                            event=Event(device=mac, parameter='SNR='+ str(snr), message='Change SSID')
                            event.save()
                            url = device.url+'/api/config'

                            # remove ssid of 2nd device from ssidlist choices

                            if second_device:
                                if second_device.connId in ssidList:
                                    ssidList.remove(second_device.connId)

                                # remove all ssids of bts_site devices that 2nd device is connected to

                                bts_site = Device.objects(connId=second_device.connId, type='BTS').first()
                                if bts_site:
                                    bts_site_ssids = Site.objects(name=bts_site.site).first().ssidList
                                    ssidList=[x for x in ssidList if x not in bts_site_ssids]

                            if ssidList:
                                new_ssid = ssidList[0]
                                payload = {'connId': new_ssid}
                                putRequest = requests.put(url, data=json.dumps(payload), headers=headers)

                                # update Device info

                                device.connId = new_ssid
                                device.save()

                            ssid_event_counter = 0
                            start = time.time()

                    elif snr < LOW_SNR and distance < DISTANCE_MIN:
                        if freq_event_counter == 0:
                            start = time.time()
                        freq_event_counter += 1
                        stop = time.time()
                        delta = stop-start
                        if freq_event_counter >= NUM_OF_EVENTS and delta <= EVENT_TIME_INTERVAL:
                            event=Event(device=mac, parameter='SNR='+ str(snr), message='Change Frequency')
                            event.save()
                            if ptp_device:
                                url = Device.objects(mac = ptp_device.mac).first().url + '/api/config'
                            # else:# Todo remove this test code
                            #     url = device.url+'/api/config' # todo remove this test code
                                # remove freqA and freqB from freqlist choices

                            current_freq = [str(freqA),str(freqB)]
                            freqList=[x for x in freqList if x not in current_freq]


                            if freqList:
                                new_freq = freqList[0]
                                if snrA < snrB:
                                    payload = {'freqA': new_freq}
                                else:
                                    payload = {'freqB': new_freq}
                                putRequest = requests.put(url, data=json.dumps(payload), headers=headers)
                            freq_event_counter = 0
                            start = time.time()

            if documents:   # bulk insert
                totaldocuments.append(documents)
                dbmongo.data.insert(documents)
            if aggr_documents:
                dbmongo.aggr_data.insert(aggr_documents)

                # BE CAREFUL! pymongo client accesses database with whatever name the database is
                # set up by mongoengine.  It seems that mongoengine converts caps to lowercase and
                # multiple caps to underscored lowercase names

        except Exception, msg:
            app.logger.error('error message is: %s, ' % msg)
            pass
    if totaldocuments:
        return str(totaldocuments)
    else:
        if msg:
            return "Some or all devices are down"
        else:
            return "No data from devices"

@app.route('/histogram/<site>')
@login_required
def generate_histogram(site,fromTimeStamp=None,toTimeStamp=None):

    if toTimeStamp is None:
        toTimeStamp = datetime.datetime.now()
    if fromTimeStamp is None:
        fromTimeStamp=toTimeStamp-datetime.timedelta(days=2)
    dict=[]
    total_records = len(Aggr_data.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site ))

    for x in range(5,40,5):
        records = len(Aggr_data.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site , distance__lt = x, distance__gt = x-5))
        avg_cap = Aggr_data.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site , distance__lt = x, distance__gt = x-5).average('cap')
        dict.append({"Occurences": 100*records/total_records, "Avg_Capacity": avg_cap, "Distance":x})
        # dict.append({ "Avg_Capacity": avg_cap})



    return str(dict)

def aggregate_data():

    # go through all the sites and compute aggregate data

    for object in Site.objects(all):

        # get last entry for this site

        timeStamp = Aggr_data.objects(site = object).order_by('-time').only ('time').first()

        # validate if timestamp is null

        if not timeStamp:
            timeStamp = datetime.datetime.now()

        # get all devices for this site

        devices = Device.objects(site = object)

        # compute aggregate tx, rx, cap values for all devices for this site
        for device in devices:
            records_data = Data.objects(Q(mac = device.mac) & Q(time > timeStamp)).order_by('time').only('mac','time',
                                                                                    'tx','rx','total_cap','distance','geo')
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

def beacon_process_file(file_content, mac_addr, archived=False):
    logger = app.logger
    if not file_content or not mac_addr:
        logger.error('Invalid upload content: %s' % file_content)
        return False
    start_job = datetime.datetime.now()

    lines = []
    try:
        lines = file_content.splitlines(False)
    except AttributeError, msg:
        logger.error('Error while splitting the lines of an upload file: %s' % msg)
        return False
    logger.debug("Processing "+mac_addr+" upload of "+str(len(lines)))

    # build a cache of metric definitions
    metric_definition_cache = {}
    mdef_qs = models.MetricDefinition.objects()
    for mdef in mdef_qs:
        metric_definition_cache[mdef.name] = mdef

    # build a cache of devices
    devices_cache = {}
    devices_qs = models.ManagedDevice.objects()
    for device in devices_qs:
        devices_cache[device.mac] = device


    # create a cache with format records_cache[time][metric_def][target_mac]=MetricRecord
    records_cache = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None)))

    request_device = devices_cache[mac_addr]
    if request_device is None:
        app.logger.error(' Requested device could not be found using this mac: %s.' % mac_addr)
        return False

    is_bts = request_device.device_class.type == 'BTS'

    # we will be storing all the metrics and their values into a multi-dimensional dictionary
    #    with the following format
    #
    # all['METRIC_NAME']['mac:add:res'][time] = value
    # all[time]['METRIC_NAME']['mac:add:res'] = value
    all = defaultdict(lambda: defaultdict(lambda: defaultdict()))
    for line in lines:
        mline = line.replace('  ', ' ')
        elements = mline.split(' ')
        name = elements[0]
        mac = elements[1]
        time_and_value = elements[2].split(':', 1)
        mtime = datetime.datetime.fromtimestamp(float(time_and_value[0]), pytz.utc)
        value = time_and_value[1]

        if name in ('BTS_AGGR_RX', 'CPE_RX', 'BTS_AGGR_TX', 'CPE_TX', 'BTS_PING_RESPONSE'):
            if value != '0':
                value = value[:-1]+'.'+value[-1:]

        all[mtime][name][mac] = value

        if not archived:
            dict_key = mac
            dict_value = [mtime, value]
            cache.put(dict_key, dict_value)


    delta_onepass = datetime.datetime.now() - start_job
    # Find out if this device is a bts or a cpe

    for mtime, metrics_dict in all.items():
        for metric, mac_dict in metrics_dict.items():

            if is_bts and metric in ['CPE_LAT', 'CPE_LONG', 'CPE_SPEED', 'CPE_ALT']:
                # print "%s debug me" % metric
                continue  # these values are also provided by the CPE, no need to record them twice

            for target_mac, value in mac_dict.items():

                if is_bts:
                    cpe_device = None
                    if target_mac != request_device.mac:
                        cpe_device = devices_cache.get(target_mac)
                    bts_device = request_device  # is bts
                else:  # is cpe
                    cpe_device = request_device
                    bts_device = None
                    try:
                        bts_mac = metrics_dict['CONNECTED_TO_BTS'][request_device.mac]
                        bts_device = devices_cache.get(bts_mac)
                        if not archived and request_device.connected_to != bts_device:
                            update_connected_to_for_device(request_device.mac, bts_device.mac)


                    except KeyError:
                        pass  # bts_device remains None

                    if metric == 'CPE_LAT':
                        compute_composite_metrics_for_cpe(request_device, bts_device, mtime, metrics_dict, metric_definition_cache, devices_cache, record_cache=records_cache)

                process_metric_record(metric_definition_cache[metric], request_device, cpe_device, bts_device, mtime, value, with_cache=records_cache)
        # all metrics have been parsed at this stage
        # time to compute the composites
        num_active = 0
        try:
            num_active = int(metrics_dict['NUM_ACTIVE'][request_device.mac])
        except KeyError:
            pass

        if is_bts and num_active > 0:  # only if there are connected cpe-s it is worth calculating the composites
            compute_composite_metrics_for_bts(request_device, mtime, metrics_dict, metric_definition_cache, devices_cache, record_cache=records_cache)
        elif is_bts:
            pass  # app.logger.debug("NUM_ACTIVE = 0 fro  %s at %s " % (request_device.mac, mtime))

    a = 0
    # iterate the cache and write all records
    for time, metrics_dict in records_cache.items():
        for metric, mac_dict in metrics_dict.items():
            for mac, record in mac_dict.items():
                if record is not None:
                    record.save()
                else:
                    logger.error("MetricRecord is null for time: %s metric: %s target_mac: %s" % (time, metric, mac))

    delta_end = datetime.datetime.now() - start_job
    logger.debug("Package processed in %s.  First pass took: %s" % (delta_end, delta_onepass))

    return True


def process_metric_record(metric_definition, request_device, cpe_device, bts_device, time, value, with_cache=None):

    # if metric_definition.name == "CPE_RXTX":
    #     app.logger.debug("CPE_RX_TX =  %s at %s " %(value, time))

    if not metric_definition.store:
        return  # no need to store this metric record

    ##  first of all we need to register this record
    dt = time.replace(second=0)

    target_mac = request_device.mac
    if cpe_device is not None:
        target_mac = cpe_device.mac

    mr = None
    if with_cache is not None:
        mr = with_cache[dt][metric_definition.name][target_mac]

    if mr is None:
        mr = models.MetricRecord.objects(metric_definition=metric_definition, cpe_device=cpe_device, bts_device=bts_device,
                                     time=dt).first()
        if with_cache is not None:
            with_cache[dt][metric_definition.name][target_mac] = mr


    if mr is None:
        mr = models.MetricRecord()
        mr.bts_device = bts_device
        mr.cpe_device = cpe_device
        mr.metric_definition = metric_definition
        mr.time = dt
        mr.values = []
        if with_cache is not None:
            with_cache[dt][metric_definition.name][target_mac] = mr

    mtick = models.MetricTick()
    mtick.value = value
    mtick.sec = time.time().second

    if mr.metric_definition.numeric:
        if mr.avg_numeric is None:
            mr.avg_numeric = 0

        intv = float(mtick.value)
        mr.avg_numeric = (mr.avg_numeric * len(mr.values) + intv) / (len(mr.values) + 1)

    elif mr.metric_definition.geo:
        # for now we just overwrite but should be replaced with a geo average
        mr.avg_geo = value
        # update the average
    mr.values.append(mtick)

    if not mr.metric_definition.geo and not mr.metric_definition.numeric:
        freqs = defaultdict(int)
        for tick in mr.values:
            freqs[tick.value] += 1

        mr.avg_obj = max(freqs, key=freqs.get)

    if with_cache is None:
        mr.save()
        # if with_cache is on it will be saved when the cache is saved


def update_connected_to_for_device(mac_addr, bts_addr):
    logger = logging.getLogger('metrics')

    cpe_device = models.ManagedDevice.objects.filter(mac=mac_addr).first()
    if cpe_device is None:
        logger.error('Database Managed Device entry could not be found using MAC [ %s ].' % mac_addr)
        return False

    bts_device = models.ManagedDevice.objects.filter(mac=bts_addr).first()
    if bts_device is None:
        logger.error('Database Managed Device entry could not be found using MAC [ %s ].' % mac_addr)
        return False

    prior_connected_to = cpe_device.connected_to
    cpe_device.connected_to = bts_device
    cpe_device.save()
    logger.info('CPE device [ %s ] disconnected from [ %s ] and is now connected to [ %s ].' % 
                (cpe_device.name, prior_connected_to.name, cpe_device.connected_to))

    return True


def compute_composite_metrics_for_bts(request_device, mtime, metrics_dict, metric_definition_cache, devices_cache, record_cache=None):

    # compute the composite metrics for a given device
    # TPW_NOW, CPE_CAP
    # add the code here for the computations

    # invoke process_metric_record for each composite metric

    # all['METRIC_NAME']['mac:add:res'][time] = value

    metric_def_cpe_cap = metric_definition_cache.get('CPE_CAP')
    metric_def_tpw_now = metric_definition_cache.get('TPW_NOW')
    metric_def_cpe_rxtx = metric_definition_cache.get('CPE_RXTX')

    # estimate the CAP
    snr_dict = metrics_dict['CPE_SNR']
    for target_mac, value in snr_dict.items():
        cpe_device = devices_cache.get(target_mac)
        # dt = datetime.datetime.fromtimestamp(float(time)).replace(tzinfo=pytz.utc)
        snr_value = float(value)
        mcs_value = float(metrics_dict['BTS_MCS'][target_mac])
        rtx_value = float(metrics_dict['BTS_ARQ_RETX_PERCENT'][target_mac])
        rx_value = float(metrics_dict['CPE_RX'][target_mac])
        tx_value = float(metrics_dict['CPE_TX'][target_mac])
        cpe_mcs_value = float(metrics_dict['CPE_MCS'][target_mac])
        bts_snr_value = float(metrics_dict['BTS_SNR'][target_mac])

        # modified capacity algorithm
        number_of_cpes_value = len(snr_dict)

        cpe_cap_value = get_capacity_estimate(snr_value, mcs_value, rtx_value, number_of_cpes_value)
        #app.logger.debug('--- CPE_CAP for %s is %s' % (target_mac, str(cpe_cap_value)))

        bts_cap_value = get_capacity_estimate(bts_snr_value, cpe_mcs_value, rtx_value, 1)
        rxtx = rx_value + tx_value
        combined_capacity = 0.0
        if rxtx > 0:
            combined_capacity = (tx_value/rxtx)*cpe_cap_value + (rx_value/rxtx)*bts_cap_value
        else:
            combined_capacity = 0.8*cpe_cap_value + 0.2*bts_cap_value

        if rxtx > combined_capacity:
            combined_capacity = rxtx

        process_metric_record(metric_def_cpe_cap, request_device, cpe_device, request_device, mtime, combined_capacity, with_cache=record_cache)

        tpw_now_value = 'TPW'
        if combined_capacity < CUTOFF_CAPACITY:
            tpw_now_value = 'SAT'
        # if snr_value < CUTOFF_SNR:
        #     tpw_now_value = 'SAT'

        process_metric_record(metric_def_tpw_now, request_device, cpe_device, request_device, mtime, tpw_now_value, with_cache=record_cache)

        #RXTX
        process_metric_record(metric_def_cpe_rxtx, request_device, cpe_device, request_device, mtime, rx_value + tx_value, with_cache=record_cache)


def compute_composite_metrics_for_cpe(request_device, bts_device, mtime, metrics_dict, metric_definition_cache, devices_cache, record_cache=None):

    # compute the composite metrics for a given device
    # CPE_GEO
    # add the code here for the computations

    # invoke process_metric_record for each composite metric

    metric_def_cpe_geo = metric_definition_cache.get('CPE_GEO')
    metric_def_cpe_bts_distance = metric_definition_cache.get('CPE_BTS_DISTANCE')

    lat_value = float(metrics_dict['CPE_LAT'][request_device.mac])
    long_value = float(metrics_dict['CPE_LONG'][request_device.mac])

    #compute distance
    bts_lat = float(bts_device.lat)
    bts_long = float(bts_device.long)
    if bts_device.mac != request_device.mac:
        cpe_bts_distance = distance_in_miles(bts_lat, bts_long, lat_value, long_value)
    else: # prevent distance = 0 by taking the previous value from the database
        app.logger.error('Distance calc error - Requested device mac is equal to BTS mac: %s.' % bts_device.mac)
        metric = models.MetricDefinition.objects.filter(name="CPE_BTS_DISTANCE").first()
        record = models.MetricRecord.objects.only('avg_numeric').filter(cpe_device=request_device, metric_definition=metric).first()
        cpe_bts_distance = record.avg_numeric
    process_metric_record(metric_def_cpe_geo, request_device, request_device, bts_device, mtime, [lat_value, long_value], with_cache=record_cache)
    process_metric_record(metric_def_cpe_bts_distance, request_device, request_device, bts_device, mtime, cpe_bts_distance,with_cache=record_cache)


def get_capacity_estimate(snr, mcs, retransmit_percentage, number_of_cpes):
    table = [4.47, 8.5, 12.8, 17.0, 24.5, 37.3, 40, 40, 9.0, 17, 26, 34, 48, 55, 60, 60, 13.9, 26.2, 36.8, 48, 55, 60,
             60, 60, 18, 32, 44, 55, 60, 60, 60, 60
            ]

    mcs_low_snr = table[0]
    capacity_estimate = table[int(round(mcs))]

    #app.logger.debug('parameters are snr: %s, mcs: %s, ' % (snr, mcs))
    #app.logger.debug('retransmit_percentage: %s, CPEs: %s, ' % (retransmit_percentage, number_of_cpes))

    try:

        if snr < 4:
            capacity_estimate += (snr / 1.2) - mcs_low_snr
            # app.logger.debug('capacity_estimate in snr < 4: %s, ' % capacity_estimate)

        if snr < 7:
            exponent = 2
        else:
            exponent = 1.2


        # app.logger.debug("average capacity estimate x is : %s" % x)

        capacity_estimate *= (1-(retransmit_percentage/100.0))**exponent
        avg_capacity_estimate = capacity_estimate/number_of_cpes

        # app.logger.debug("average capacity estimate is : %s" % avg_capacity_estimate)

    except Exception, msg:
        app.logger.error('error message is: %s, ' % msg)
        app.logger.error('parameters are snr: %s, mcs: %s, ' % (snr, mcs))
        app.logger.error('retransmit_percentage: %s, CPEs: %s, ' % (retransmit_percentage, number_of_cpes))

        return 0

    return avg_capacity_estimate


def get_30_data(p_cpe_device,p_metric_name):
    logger = app.logger

    #thirtydays_data = OrderedDict()
    start_date = datetime.datetime.now() + datetime.timedelta(-30)
    #for filter_data in models.MetricDefinition.objects(name = p_metric_name):
     #   for t_data in models.MetricRecord.find({"time": {"$gt": start_date}}):
            #print t_data
    try:


        metric_def = models.MetricDefinition.objects(name=p_metric_name).first()
        app.logger.info("Metric passed to func: %s" % metric_def)


        device = models.ManagedDevice.objects(name=p_cpe_device).first()
        app.logger.info("Device passed to func: %s" % device)

        metric_record_qset = models.MetricRecord.objects(metric_definition=metric_def, cpe_device=device,
                                                        time__gte=start_date)

        sum = 0
        for metric_record in metric_record_qset:
            sum += metric_record.avg_numeric
        total_avg = sum / len(metric_record_qset)

        app.logger.info("Total Avg from func: %s" % total_avg)


    except Exception, msg:
        app.logger.error('could not get last know metric[%s] value for %s. Error message: %s' % (p_metric_name, p_cpe_device, msg))
        return None

    return total_avg


def get_lastvalue_for_metric(device, metric_name, use_beacon_cache=False, use_beacon_only=False):

    logger = app.logger
    if use_beacon_cache:
        # first try to get it from the beacon_cache
        value = cache.get(device.mac)
        if value is not None:
            return value[1]

    # Get metric definition
    metric = None
    try:
        metric_def = models.MetricDefinition.objects.filter(name=metric_name).first()
        metric_record = models.MetricRecord.objects.filter(metric_definition=metric_def, cpe_device=device).order_by('-time').limit(1).first()
        return metric_record.values[-1].value
    except Exception, msg:
        logger.error('could not get last know metric[%s] value for %s. Error message: %s' % (metric_name, device.name, msg))
        if metric_name == 'CPE_GEO':
            return [device.lat, device.long]
        else:
            return None


def get_lastknown_latlong(device):
    value = get_lastvalue_for_metric(device, 'CPE_GEO', use_beacon_cache=True)
    if value is None:
        return [device.lat, device.long]
    else:
        return value


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

def distance_in_miles(bts_device, geo):
    # logger = app.logger
    # otherDevice = Data.objects(Q(connId=connId) & Q(mac__ne=mac) & Q(time < time+datetime.timedelta(seconds=1))
    #                            & Q(time > time-datetime.timedelta(seconds=1))).first()
    if bts_device:
        geo1 = bts_device.geo #device.objects(connId=connId).only("geo").first()
    else:
        geo1 = (40,118)
    try:
        arc = distance_on_unit_sphere(geo1[0], geo1[1], geo[0], geo[1])
        return 3960 * arc
    except :
        app.logger.exception("Value error calculating distance in miles for (%s,%s)-(%s,%s)" %(geo1[0], geo1[1], geo[0], geo[1]))


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