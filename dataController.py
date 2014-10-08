from requests_futures.sessions import FuturesSession
import logging
import models
import datetime
import pytz
import math
import time
from tools import timeit
import  json

import flask
from mongoengine import Q
#from collections import OrderedDict

from flask.ext.mail import Message
from infinity import mail, app, cache,User,db
from collections import defaultdict
# import json

import pymongo
db = pymongo.MongoClient().infinity

# db = MongoClient('mongodb://localhost:27017/')
CUTOFF_CAPACITY = 2
CUTOFF_SNR = 5
session = FuturesSession(max_workers=10)
import requests
# from flask import jsonify
# from pprint import pprint

url = 'http://127.0.0.1:5002/api/person'
url1 = 'http://127.0.0.1:5002/api/person/4'

headers = {'Content-Type': 'application/json'}
filters = [dict(name='id', op='ge', val='0')]
params = dict(q=json.dumps(dict(filters=filters)))
payload = {'first_name':'Sean','last_name':'Basu'}
# response = requests.get(url, params=params, headers=headers)

def bg_cb(sess, resp):
    # parse the json storing the result on the response object
    resp.data = resp.json()



@app.route('/test')
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
def test():
    # userData = db.User()
    # response = requests.get('http://127.0.0.1:5002/v2/person')
    # future = session.get('http://127.0.0.1:5002/api/person',timeout=2, background_callback=bg_cb)
    # postRequest = requests.post(url, data=json.dumps(payload), headers=headers)
    # postRequest = requests.post(url, data=payload) //doesn't work with repeated posts, seems payload is not updated

    # deleteRequest = requests.delete(url1) #working
    # putRequest = requests.put(url1, data=json.dumps(payload), headers=headers) #working

    # postRequest = session.post(url, data=payload, headers=headers,timeout=2, background_callback=bg_cb).result()
    response = session.get(url, params=params, headers=headers,timeout=2, background_callback=bg_cb).result()

    # response = future.result()
    # content = response.content
    # status = response.status_code
    # json_content = jsonify(content)
    # json_content = response.data
    # list = json_content["objects"]

    documents=[]
    for obj in response.data["objects"]:
        first_name = obj["first_name"]
        last_name = obj["last_name"]
        Id = obj["id"]
        documents.append({"name":first_name + " " + last_name})
    # for document in documents:
    #     userData.name=document
    db.user.insert(documents)
    # lines = json_content.splitlines(False)
    return str(documents)

# assert response.status_code == 200
# print(response.json())


@timeit
def getDeviceData():
    newDeviceData = models.DeviceData()
    while True:
        for device in models.Device:
            # r = requests.get(device.url, timeout=1)
            # r = requests.delete(device.url, timeout=2)
            r = session.get(device.url, timeout=2)
            lines = []
            try:
                lines = r.splitlines(False)
                for line in lines:
                    # mline = line.replace('  ', ' ')
                    elements = line.split(' ')
                    newDeviceData.mac = elements[0]
                    newDeviceData.geo = [elements[1],elements[2]]  #geo has lat, long values
                    newDeviceData.time = elements[3]
                    newDeviceData.freqA = elements[4]
                    newDeviceData.freqB = elements[5]
                    newDeviceData.snr = elements[6]
                    newDeviceData.tx = elements[7]
                    newDeviceData.rx = elements[8]
                    newDeviceData.cap = elements[9]
                    newDeviceData.connId =elements[10]
                    newDeviceData.data = tx + rx
                    newDeviceData.distance = distance_in_miles(newDeviceData.connId,newDeviceData.geo,newDeviceData.mac)
            except AttributeError, msg:
                logger.error('Error while splitting the lines of an upload file: %s' % msg)
            return False
            logger.debug("Processing "+newDeviceData.mac+" upload of "+str(len(lines)))

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

def distance_in_miles(connId, geo, mac):
    logger = app.logger
    otherDevice = models.Device.objects(Q(connId=connId) & Q(mac__ne=mac))
    geo1 = otherDevice.geo
    try:
        arc = distance_on_unit_sphere(geo1[0], geo1[1], geo[0], geo[1])
        return 3960 * arc
    except :
        logger.exception("Value error calculating distance in miles for (%s,%s)-(%s,%s)" %(geo1[0], geo1[1], geo[0], geo[1]))


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