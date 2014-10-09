from flask import Blueprint, request,render_template
from flask.ext.security import login_required, current_user
from mongoengine.queryset import Q
from flask.ext.admin import Admin
from flask.ext.admin.form import rules
from flask.ext.admin.contrib.mongoengine import ModelView
from infinity import app
from tools import timeit
import infinity, models, dataController
import flask, math, random, collections, datetime, time, calendar, pytz, subprocess
import models
observer_views = Blueprint('observer_views', __name__, template_folder='templates')



# Route calls from app to viewController
viewController = Blueprint('viewController', __name__, template_folder='templates')

#Create Custom Admin views

class UserView(ModelView):
    column_filters = ['name']
    column_searchable_list = ['name']
    column_exclude_list = ('password')
    form_excluded_columns = ('password')
    # form_ajax_refs = {
    #     'roles': {
    #         'fields': ['name']
    #     }
    # }
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('Root')


class RoleView(ModelView):
    # column_filters = ['name']
    # column_searchable_list = ['name']
    # column_searchable_list = ('name')
    # column_exclude_list = ('password')
    # form_excluded_columns = ('password')
    # form_ajax_refs = {
    #     'roles': {
    #         'fields': ['name']
    #     }
    # }
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('Root')


# Add Admin Views
def adminViews(app):
    # Create admin
    admin = Admin(app, 'Infinity Admin')

    # if current_user.is_authenticated() and current_user.has_role('Root'):
        # Add admin views
    admin.add_view(UserView(infinity.User))
    admin.add_view(RoleView(infinity.Role))
    admin.add_view(ModelView(infinity.Company))
    admin.add_view(ModelView(infinity.Tag))
    admin.add_view(ModelView(infinity.Device))
    admin.add_view(ModelView(infinity.Data))
    admin.add_view(ModelView(infinity.Config))
    admin.add_view(ModelView(infinity.Firmware))
    admin.add_view(ModelView(infinity.Job))
    admin.add_view(ModelView(infinity.Event))
    admin.add_view(ModelView(infinity.Audit))

# Setup Admin Views
adminViews(app)


# Route main page
@app.route('/')
@login_required  # if not logged in, login.html will be the default page
def home():
    return render_template('index.html')


@app.route('/observer/cpe_monitor/<mac>')
@login_required
def observer_cpemonitor_view(mac):
    logger = app.logger

    metric_name = "CPE_RXTX"
    metric = models.MetricDefinition.objects.filter(name=metric_name).first()
    cap_metric = models.MetricDefinition.objects.filter(name='CPE_CAP').first()
    #distance_metric = models.MetricDefinition.objects.filter(name='CPE_BTS_DISTANCE').first()

    device = models.ManagedDevice.objects.filter(mac=mac).first()

    end_date = app.utc_now().replace(second=0)
    start_date = end_date - datetime.timedelta(minutes=180)

    start_time = int(calendar.timegm(start_date.timetuple()))
    end_time = int(calendar.timegm(end_date.timetuple()))

    # Get data for metric definition
    metric_min = metric.get_min(device)
    metric_max = metric.get_max(device) * 1.1

    # Get unit interval
    unit_interval = 5
    abs_total = abs(metric_min) + abs(metric_max)
    if abs_total > 100 and abs_total <= 200:
        unit_interval = 10
    elif abs_total > 200:
        unit_interval = 20

    coverage = get_average_coverage(device, start_date, end_date)
    trafic_average = get_metric_numeric_average(device, metric, start_date, end_date)
    capacity_average = get_metric_numeric_average(device, cap_metric, start_date, end_date)
    #distance_average = get_metric_numeric_average(device, distance_metric, start_date, end_date)

   # disp_avg = get_30_data(device.name, metric.name)

    ctx = {
        'device_mac': mac,
        'device_name': device.name,
        'chart_id': 'avg_qos',
        'chart_title': 'Capacity and Traffic for '+device.name + ' in the last 3 hours',
        'chart_data': [
            {'name': 'CPE_CAP', 'type': 'float', 'label': 'Capacity', 'group': 'capacity'},
            #{'name': 'CPE_BTS_DISTANCE', 'type': 'float', 'label': 'Distance', 'group': 'distance'},
            {'name': 'CPE_RXTX', 'type': 'float', 'label': 'Traffic', 'group': 'traffic'},
            # {'name':'CPE_RX', 'type':'float', 'label':'Download', 'group':'traffic'}
        ],
        'chart_groups': [
            {'name': 'capacity', 'type': 'line'},
            #{'name': 'distance', 'type': 'line'},
            {'name': 'traffic', 'type': 'line'}
        ],
        'step_min': '1m',
        'step': '1m',

        'start_time': start_time,
        'end_time': end_time,
        # start_date and end_date are only used for displaying the date&time in a user-friendly manner
        'start_date': datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S'),
        'end_date': datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S'),

        # the chart needs the following to display properly
        'metric_min': metric_min,
        'metric_max': metric_max,
        'unit_interval': unit_interval,
        'css_size': 'small',
        'coverage': coverage,
        'trafic_average': "{:.2f}".format(trafic_average),
        #'distance_average': "{:.2f}".format(distance_average),
        'capacity_average': "{:.2f}".format(capacity_average)
    }

    if 'autoscale_valueaxis' in request.args:
        ctx['autoscale_valueaxis'] = request.args['autoscale_valueaxis']

    return render_template('observer/cpe_monitor.html', **ctx)


@app.route('/observer/old-capacity/<mac>')
@login_required
def observer_cpereports_view(mac):
    app.logger.info("Capacity observer called for mac: %s" % mac)
    cap_metric = "CPE_CAP"
    metric = models.MetricDefinition.objects.filter(name=cap_metric).first()
    # distance_metric = models.MetricDefinition.objects.filter(name='CPE_BTS_DISTANCE').first()


    device = models.ManagedDevice.objects.filter(mac=mac).first()

    end_date = infinity.utc_now().replace(second=0)
    start_date = end_date - datetime.timedelta(days=1)

    start_time = int(calendar.timegm(start_date.timetuple()))
    end_time = int(calendar.timegm(end_date.timetuple()))

    # Get data for metric definition
    metric_min = metric.get_min(device)
    metric_max = metric.get_max(device) * 1.1

    # Get unit interval
    unit_interval = 5
    abs_total = abs(metric_min) + abs(metric_max)
    if abs_total > 100 and abs_total <= 200:
        unit_interval = 10
    elif abs_total > 200:
        unit_interval = 20


    router_ip  = device.get_config_param_value('router_ip')
    if router_ip is None:
        app.logger.warn("Device %s does not have router_ip config param" % device.name)
        router_ip = "9.8.8.8"

    #router_ip="8.8.8.8"
    router_status = get_status(router_ip)
    traffic_metric = models.MetricDefinition.objects.filter(name='CPE_RXTX').first()
    coverage = get_average_coverage(device, start_date, end_date)
    traffic_average = get_metric_numeric_average(device, traffic_metric, start_date, end_date)
    capacity_average = get_metric_numeric_average(device, metric, start_date, end_date)
    # distance_average = get_metric_numeric_average(device, distance_metric, start_date, end_date)

    latlong = dataController.get_lastknown_latlong(device)
    ctx = {
        'chart_id': 'avg_qos',
        'chart_title': 'Capacity,Traffic and Distance for '+device.name,
        'chart_data': [
            {'name': 'CPE_CAP', 'type': 'float', 'label': 'Capacity', 'group': 'capacity'},
            {'name': 'CPE_BTS_DISTANCE', 'type': 'float', 'label': 'Distance', 'group': 'distance'},
            {'name': 'CPE_RXTX', 'type': 'float', 'label': 'Traffic', 'group': 'traffic'},
            {'name': 'CPE_RX', 'type': 'float', 'label': 'Download', 'group': 'traffic'},
            {'name': 'CPE_TX', 'type': 'float', 'label': 'Upload', 'group': 'traffic'}
        ],
        'chart_groups': [
            {'name': 'distance', 'type': 'line'},
            {'name': 'capacity', 'type': 'line'},
            {'name': 'traffic', 'type': 'line'}
        ],
        'device_mac': mac,
        'device_name': device.name,
        'start_time': start_time,
        'end_time': end_time,
        'start_date': datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S'),
        'end_date': datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S'),

        # the chart needs the following to display properly
        'metric_min': metric_min,
        'metric_max': metric_max,
        'unit_interval': unit_interval,
        'css_size': 'small',
        'center_lat': latlong[0],
        'center_long': latlong[1],
        'router_status': router_status,
        'router_ip': router_ip,
        'coverage': coverage,
        'traffic_average': "{:.2f}".format(traffic_average),
        # 'distance_average': "{:.2f}".format(distance_average),
        'capacity_average': "{:.2f}".format(capacity_average)
    }
    return render_template('observer/capacity_reports.html', **ctx)


@app.route('/observer/capacity/<mac>')
@login_required
def observer_rcpereports_view(mac):
    app.logger.info("Capacity observer called for mac: %s" % mac)
    cap_metric = "CPE_CAP"
    metric = models.MetricDefinition.objects.filter(name=cap_metric).first()

    device = models.ManagedDevice.objects.filter(mac=mac).first()

    end_date = infinity.utc_now().replace(second=0)
    start_date = end_date - datetime.timedelta(days=1)

    start_time = int(calendar.timegm(start_date.timetuple()))
    end_time = int(calendar.timegm(end_date.timetuple()))

    # Get data for metric definition
    metric_min = metric.get_min(device)
    metric_max = metric.get_max(device) * 1.1

    # Get unit interval
    unit_interval = 5
    abs_total = abs(metric_min) + abs(metric_max)
    if abs_total > 100 and abs_total <= 200:
        unit_interval = 10
    elif abs_total > 200:
        unit_interval = 20


    router_ip  = device.get_config_param_value('router_ip')
    if router_ip is None:
        app.logger.warn("Device %s does not have router_ip config param" % device.name)
        router_ip = "9.8.8.8"

    router_status = get_status(router_ip)
    traffic_metric = models.MetricDefinition.objects.filter(name='CPE_RXTX').first()
    coverage = get_average_coverage(device, start_date, end_date)
    traffic_average = get_metric_numeric_average(device, traffic_metric, start_date, end_date)
    capacity_average = get_metric_numeric_average(device, metric, start_date, end_date)

    latlong = dataController.get_lastknown_latlong(device)
    ctx = {
        'chart_id': 'avg_qos',
        'chart_title': 'Capacity and Traffic for '+device.name,
        'chart_data': [
            {'name': 'CPE_CAP', 'type': 'float', 'label': 'Capacity',
                'group': 'capacity', 'yAxis': 0},
            {'name': 'CPE_RXTX', 'type': 'float', 'label': 'Traffic',
                'group': 'traffic', 'yAxis': 0},
            {'name': 'CPE_RX', 'type': 'float', 'label': 'Download',
                'group': 'traffic', 'yAxis': 0},
            {'name': 'CPE_TX', 'type': 'float', 'label': 'Upload',
                'group': 'traffic', 'yAxis': 0},
            {'name': 'CPE_BTS_DISTANCE', 'type': 'float', 'label': 'Distance',
                'group': 'distance', 'yAxis': 1, 'dashStyle': 'ShortDot'}
        ],
        'chart_groups': [
            {'name': 'capacity', 'type': 'line'},
            {'name': 'traffic', 'type': 'line'}
        ],
        'device_mac': mac,
        'device_name': device.name,
        'start_time': start_time,
        'end_time': end_time,
        'start_date': datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S'),
        'end_date': datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S'),
        'data_url': '/reports/metrics_with_gps_trail',

        # the chart needs the following to display properly
        'metric_min': metric_min,
        'metric_max': metric_max,
        'unit_interval': unit_interval,
        'css_size': 'small',
        'center_lat': latlong[0],
        'center_long': latlong[1],
        'router_status': router_status,
        'router_ip': router_ip,
        'coverage': coverage,
        'traffic_average': "{:.2f}".format(traffic_average),
        'capacity_average': "{:.2f}".format(capacity_average)
    }
    return render_template('observer/capacity_high_reports.html', **ctx)


def get_30_data(p_cpe_device, p_metric_name):
    logger = app.logger

    # thirtydays_data = OrderedDict()
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
        app.logger.error(
            'could not get last know metric[%s] value for %s. Error message: %s' % (p_metric_name, p_cpe_device, msg))
        return None

    return total_avg


@app.route("/monitor/get-ping-status/<ip>", methods=['GET','POST'])
def get_ping_status(ip):
    value = get_status(ip)
    if value != 0:
        return get_status(ip)
    else:
        return value


@timeit
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


@app.route('/observer/averages', methods=['GET'])
@login_required
def observer_get_averages():
    logger = app.logger

    mac = flask.request.args.get('mac')
    device = models.ManagedDevice.objects.filter(mac=mac).first()
    startTime = flask.request.args.get('startTime')
    endTime  = flask.request.args.get('endTime')


    start_date = datetime.datetime.fromtimestamp(float(startTime), pytz.utc)
    end_date = datetime.datetime.fromtimestamp(float(endTime), pytz.utc)

    cap_metric = models.MetricDefinition.objects.filter(name='CPE_CAP').first()
    rxtx_metric = models.MetricDefinition.objects.filter(name='CPE_RXTX').first()


    coverage = get_average_coverage(device, start_date, end_date)
    traffic_average = get_metric_numeric_average(device, rxtx_metric, start_date, end_date)
    capacity_average = get_metric_numeric_average(device, cap_metric, start_date, end_date)

    return flask.jsonify(coverage="{:.2f}".format(coverage),
                         traffic_average="{:.2f}".format(traffic_average),
                         capacity_average="{:.2f}".format(capacity_average))



@timeit
def get_records_average_by_step(bts, metric_definitions, start_time, end_time, step, cpe=None, max_sections=180):

    start_date = datetime.datetime.fromtimestamp(float(start_time), tz=pytz.utc)
    end_date = datetime.datetime.fromtimestamp(float(end_time), tz=pytz.utc)

    q = Q(metric_definition__in=metric_definitions) & Q(time__gte=start_date) & Q(time__lte=end_date )
    if bts:
        q = q & Q(bts_device=bts)

    if cpe:
        q = q & Q(cpe_device=cpe)


    only_fields = ['time','metric_definition','avg_numeric']
    if step < 60:  # we also need seconds
        only_fields += ['values']

    records = models.MetricRecord.objects.only(*only_fields).filter(q).select_related()
    section_size = int(math.ceil(end_time - start_time + 1) / max_sections)
    values = {}
    for x in range(0, max_sections+1):
        values[x] = {
            'number': x,
            'time': (start_time + x * section_size)*1000
        }
        for mdef in metric_definitions:
            values[x][mdef.name] = {'sum': 0,
                                    'count': 0,
                                    'average': 0}

    for record in records:

        dt = record.time
        if step >= 60:  # step is higher then 1m - we will work with minute averages, no ticks necessary
                ticks = [record.avg_numeric]  # just a placeholder
        else:
            ticks = record.values

        for tick in ticks:
            if step < 60:
                dt = dt.replace(second=tick.sec)

            record_time = int(calendar.timegm(dt.timetuple()))
            nrs = (record_time - start_time) + 1
            section_nr = int(math.ceil(nrs / section_size))

            if section_nr > max_sections:
                print "ERROR"

            old_sum = values[section_nr][record.metric_definition.name]['sum']
            old_count = values[section_nr][record.metric_definition.name]['count']
            old_average = values[section_nr][record.metric_definition.name]['average']

            try:
                if step >= 60:  # work with averages
                    record_value = float(record.avg_numeric)
                else:
                    record_value = float(tick.value)  # otherwise take the tick value

            except Exception as ex:
                continue

            new_sum = old_sum + record_value
            new_count = old_count + 1
            new_average = ((old_average * old_count) + record_value) / new_count

            values[section_nr][record.metric_definition.name]['sum'] = new_sum
            values[section_nr][record.metric_definition.name]['count'] = new_count
            values[section_nr][record.metric_definition.name]['average'] = new_average

    for x in range(0, max_sections):
        for mdef in metric_definitions:
            values[x][mdef.name] = float("{:.2f}".format(values[x][mdef.name]['average']))

    ordered = collections.OrderedDict(values.items())

    return ordered


@timeit
def get_average_coverage(device, start_date, end_date):

    metric_definition = models.MetricDefinition.objects.filter(name="TPW_NOW").first()

    records = models.MetricRecord.objects.only('avg_obj').filter(cpe_device=device, metric_definition=metric_definition, time__gte=start_date, time__lte=end_date).order_by('time')

    minutes_on = 0
    for record in records:
        if record.avg_obj == 'TPW':
            minutes_on += 1

    delta = end_date - start_date

    total_minutes = int(delta.total_seconds() / 60)
    if len(records) > total_minutes:
        total_minutes = len(records)

    coverage = int(float(minutes_on * 100) / total_minutes)

    return coverage


@timeit
def get_metric_numeric_average(device, metric_definition, start_date, end_date):

    records = models.MetricRecord.objects.only('avg_numeric').filter(cpe_device=device, metric_definition=metric_definition, time__gte=start_date, time__lte=end_date).order_by('time')

    sum = 0
    for record in records:
        sum += record.avg_numeric

    delta = end_date - start_date
    #total_minutes = int(delta.total_seconds() / 60)
    denominator = 1
    if len(records) > 0:
        denominator = len(records)

    average = float(sum) / denominator

    return average


def convert_enddate_to_seconds(ts):
#   """Takes ISO 8601 format(string) and converts into epoch time."""
   dt = datetime.datetime.strptime(ts[:-7],'%Y-%m-%dT%H:%M:%S.%f')-\
       datetime.timedelta(hours=int(ts[-5:-3]),
       minutes=int(ts[-2:]))*int(ts[-6:-5]+'1')
   seconds = calendar.timegm(dt.timetuple()) + dt.microsecond/1000000.0
   return seconds


def get_gps_trail(device, start_date, end_date, max_steps=200, min_step_distance=0.25, max_step_distance = 3):

    logger = app.logger

    geoMetric = models.MetricDefinition.objects.filter(name="CPE_GEO").first()
    tpwNowMetric = models.MetricDefinition.objects.filter(name="TPW_NOW").first()
    capMetric = models.MetricDefinition.objects.filter(name="CPE_CAP").first()
    trafficMetric = models.MetricDefinition.objects.filter(name="CPE_RXTX").first()
    distanceMetric = models.MetricDefinition.objects.filter(name="CPE_BTS_DISTANCE").first()



    q = Q(cpe_device=device) & Q(time__gte=start_date) & Q(time__lte=end_date)

    delta = end_date - start_date
    step_unit = 90

    qmetric = Q(metric_definition=geoMetric) | Q(metric_definition=tpwNowMetric) | Q(metric_definition=capMetric)| Q(metric_definition=trafficMetric)| Q(metric_definition=distanceMetric)


    response_data = []
    # group all records by time
    records_set = dict()
    records = models.MetricRecord.objects.only('time', 'metric_definition','avg_geo','avg_obj','avg_numeric').filter(qmetric & q).select_related()  # .order_by('time')

    prev_record = None
    for record in records:

        a = records_set.get(record.time)
        if a is None:
            a = {}
            records_set[record.time] = a

        a[record.metric_definition.name] = record

    # now iterate the group records and prepare the returned value


    COLORS = {'TPW':'green', 'SAT':'orange', 'NONE':'red'}

    # ordered_records_set =
    ptime = None
    ptpw_now = None
    last_lat = None
    last_long = None
    for rtime in sorted(records_set):
        record_dict = records_set[rtime]
        delta = None
        if ptime is not None:
            delta = rtime - ptime
        #gpstime =datetime.datetime.fromtimestamp(float(rtime), pytz.utc)
        #gpstime = dateutil.parser.parse(rtime)
        #gpstime = json.dumps(rtime.isoformat())
        gpstime=int(calendar.timegm(rtime.timetuple()))
        #gpstime = json.dumps(rtime)
        #gpstime = rtime[:19]
        #gpstime = int(time.mktime(time.strptime(gpstime,'%Y-%m-%d %H:%M:%S')))-time.timezone
        if ptime is None or delta.total_seconds() > step_unit:
            try:
                tpw_now = record_dict.get('TPW_NOW')
                if tpw_now is not None:
                    tpw_now = tpw_now.avg_obj
                else:
                    tpw_now = 'NONE'

                color = COLORS[tpw_now]

                geo = record_dict.get('CPE_GEO')
                latlong = geo.avg_geo
                cpe_bts_distance = round(record_dict.get('CPE_BTS_DISTANCE').avg_numeric,2)
                cap = round(record_dict.get('CPE_CAP').avg_numeric,2)
                if cap is None:
                    pass
                if color == "green":
                    if cap > 30:
                        color = "#003300"
                    elif cap > 20:
                        color = "#006600"
                    elif cap > 10:
                        color = "#009933"
                    elif cap > 5:
                        color = "#33CC33"
                    else:
                        color = "#99FF33"
                traffic = round(record_dict.get('CPE_RXTX').avg_numeric,2)
                if traffic is None:
                    pass
                if latlong is None:
                    continue
                #latlong = geo.avg_geo
                if len(response_data) > 0:
                    #distance = dataController.distance_in_miles(response_data[-1]['lat'], response_data[-1]['lng'],
                    #                                                latlong[0], latlong[1])
                    distance = dataController.distance_in_miles(last_lat, last_long, latlong[0], latlong[1])
                    # add the point only if the distance has been higher min_distance
                    #     or there was a change in coverage
                    #if distance > min_step_distance or tpw_now != ptpw_now or len(response_data) < 3 :
                    if (distance > min_step_distance or tpw_now != ptpw_now or len(response_data) < 3) and distance < max_step_distance:
                        response_data.append({'lat': latlong[0], 'lng': latlong[1], 'color': color, 'time':gpstime, 'cap':cap, 'traffic':traffic,'cpe_bts_distance' :cpe_bts_distance})
                else:
                    response_data.append({'lat': latlong[0], 'lng': latlong[1], 'color': color, 'time':gpstime, 'cap':cap, 'traffic':traffic,'cpe_bts_distance' :cpe_bts_distance})
                ptime = rtime
                ptpw_now=tpw_now
                last_lat = latlong[0]
                last_long = latlong[1]

            except Exception as e:
                logger.error("Something went wrong while filtering gps coordinates: %s" % e)

    return response_data


@timeit
def get_averages_and_gps_trail(bts, metric_definitions, start_time, end_time, cpe=None, max_sections=180, heatmap=None):

    logger = app.logger

    start_date = datetime.datetime.fromtimestamp(float(start_time), tz=pytz.utc)
    end_date = datetime.datetime.fromtimestamp(float(end_time), tz=pytz.utc)

    q = Q(metric_definition__in=metric_definitions) & Q(time__gte=start_date) & Q(time__lte=end_date )
    if bts:
        q = q & Q(bts_device=bts)

    if cpe:
        q = q & Q(cpe_device=cpe)

    only_fields = ['time', 'metric_definition', 'avg_numeric', 'avg_geo', 'avg_obj']


    # group by time and metric definition
    records_dd = collections.defaultdict(lambda: dict())
    records = models.MetricRecord.objects.only(*only_fields).filter(q).select_related()
    for record in records:
        rtime = int(calendar.timegm(record.time.timetuple()))
        records_dd[rtime][record.metric_definition.name] = record


    records_od = dict(records_dd)
    section_size = int(math.ceil(end_time - start_time + 1) / max_sections)
    sections = {}
    for x in range(0, max_sections+1):
        stime = start_time + x * section_size
        sections[x] = {
            'time': stime*1000
        }
        for mdef in metric_definitions:
            sections[x][mdef.name] = {'sum': 0, 'count': 0, 'average': 0, 'geo': None,
                                      'freqs': collections.defaultdict(int)}

    prev_marker = None

    for rtime in sorted(records_od):
        metrics_dict = records_od[rtime]

        nrs = (rtime - start_time) + 1
        section_nr = int(math.ceil(nrs / section_size))

        if section_nr > max_sections:
            logger.exception("Sectioning failure.")
            return None

        for metric, record in metrics_dict.iteritems():

            if record.metric_definition.geo:
                a = sections[section_nr][metric]['geo']
                if a is None:
                    a = []
                    sections[section_nr][metric]['geo'] = a

                gps_marker = {'lat': record.avg_geo[0], 'lng': record.avg_geo[1],
                              'time': rtime * 1000, 'stime': 1000 * (start_time + section_nr * section_size),
                              'section': section_nr}

                if len(a) == 0:
                    if heatmap is not None:
                        cap_record = get_closest(records_od, rtime, 'CPE_CAP')
                        if cap_record is None:
                            gps_marker['color'] = 'darkorange'
                        else:
                            gps_marker['color'] = heatmap.get_color_for_value(cap_record.avg_numeric)
                    else:  # no heatmap
                        tpw_record = get_closest(records_od, rtime, 'TPW_NOW')
                        if tpw_record is None:
                            gps_marker['color'] = 'darkorange'
                        elif tpw_record .avg_obj == 'TPW':
                            gps_marker['color'] = 'green'
                        else:
                            gps_marker['color'] = 'orange'

                    if prev_marker is not None:
                        distance = dataController.distance_in_miles(prev_marker['lat'], prev_marker['lng'],
                                                                    gps_marker['lat'], gps_marker['lng'])
                        gps_marker['distance'] = distance

                    a.append(gps_marker)
                    prev_marker = gps_marker
                else:
                    distance = dataController.distance_in_miles(a[-1]['lat'], a[-1]['lng'],
                                                                    gps_marker['lat'], gps_marker['lng'])
                    gps_marker['distance'] = distance
                    if distance < 0.5:
                        continue

                    if heatmap is not None:
                        cap_record = get_closest(records_od, rtime, 'CPE_CAP')
                        if cap_record is None:
                            gps_marker['color'] = 'darkorange'
                        else:
                            gps_marker['color'] = heatmap.get_color_for_value(cap_record.avg_numeric)
                    else:  # no heatmap
                        tpw_record = get_closest(records_od, rtime, 'TPW_NOW')
                        if tpw_record is None:
                            gps_marker['color'] = 'darkorange'
                        elif tpw_record .avg_obj == 'TPW':
                            gps_marker['color'] = 'green'
                        else:
                            gps_marker['color'] = 'orange'

                    a.append(gps_marker)
                    prev_marker = gps_marker

            elif record.metric_definition.numeric:
                old_sum = sections[section_nr][record.metric_definition.name]['sum']
                old_count = sections[section_nr][record.metric_definition.name]['count']
                old_average = sections[section_nr][record.metric_definition.name]['average']

                record_value = float(record.avg_numeric)

                new_sum = old_sum + record_value
                new_count = old_count + 1
                new_average = ((old_average * old_count) + record_value) / new_count

                sections[section_nr][record.metric_definition.name]['sum'] = new_sum
                sections[section_nr][record.metric_definition.name]['count'] = new_count
                sections[section_nr][record.metric_definition.name]['average'] = new_average

            else:  # is not numerical nor geo
                sections[section_nr][record.metric_definition.name]['freqs'][record.avg_obj] += 1

    for x in range(0, max_sections):
        for mdef in metric_definitions:
            if mdef.numeric:
                sections[x][mdef.name] = float("{:.2f}".format(sections[x][mdef.name]['average']))

    ordered = collections.OrderedDict(sections.items())

    return ordered


def get_closest(dictionary, for_time, metric_name, max_delta = 100):

    delta = 0
    found = None
    while delta < max_delta and found is None:
        rd = dictionary.get(for_time + delta)
        if rd is None:
            rd = dictionary.get(for_time - delta)

        if rd is not None:
            found = rd.get(metric_name)

        delta += 1

    return found


def fake_records_average_by_increment(device, metric_definitions, start_time, end_time, step):
#  make some fake data for the demo
        values = {}
        max_sections_nr = int(math.ceil((end_time - start_time + 1) / step))

        if max_sections_nr > 120:
            max_sections_nr = 120

        for x in range(0, max_sections_nr):
            values[x] = {
                    'number': x,
                    'time': (start_time + x * step)*1000
                    # 'time': start_time + x * step
                }

        for x in range(0, max_sections_nr):
            for md in metric_definitions:
                delta = random.randint(-3, 3)
                max = md.get_max(device) * 0.6
                min = md.get_min(device) * 0.8
                if x == 0:
                    val = max / 2
                else:
                    val = values[x-1][md.name] + delta
                    if val > max:
                        val = max
                    if val < min:
                        val = min

                values[x][md.name] = val

        return values

