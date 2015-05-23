from flask import Blueprint, render_template, Response
from flask.ext.security import login_required, current_user
from flask.ext.admin import Admin
from flask.ext.admin.contrib.mongoengine import ModelView
import infinity
import flask, time, subprocess, json,calendar
from infinity import app, Site, Aggr_data, Device, Data, Minute, Hour, Day, Month, Site_data,Site_data_min, \
    Site_data_hour, Site_data_day, Site_data_month
from wtforms.fields import TextField
# from flask import Flask
# from htmlmin.main import minify
from htmlmin.minify import html_minify
import dataController

# @app.after_request
# def response_minify(response):
#     """
#     minify html response to decrease site traffic
#     """
#     if response.content_type == u'text/html; charset=utf-8':
#         response.set_data(
#             minify(response.get_data(as_text=True))
#         )
#         return response
#     return response

class ReadonlyTextField(TextField):
  def __call__(self, *args, **kwargs):
    kwargs.setdefault('readonly', True)
    return super(ReadonlyTextField, self).__call__(*args, **kwargs)
# from monary import Monary
# from collections import defaultdict
# import numpy
INTERVAL_INIT = 60*60
STREAM_INTERVAL = 1*60
MAX_POINTS = 100
DISTANCE_STEP = 2
DISTANCE_MAX = 10
NOW = int(time.time())
start = NOW - INTERVAL_INIT
end = NOW
# site = 'btsA'
# site = 'Catalina'
site = 'Catalina_LongBeach'
link = 'Catalina_LongBeach'
deviceType = 'CPE'
streamInterval = 1000
updateInterval = 6000
# import plotly.plotly as py
# from plotly.graph_objs import *
# py.sign_in("saswata", "mret9csgsi")

# from htmlmin.minify import html_minify
# from flask.ext.assets import Environment, Bundle
# assets.register('app_css', app_css)
# assets.register('app_js', app_js)
# assets.register('app_js_exts', app_js_exts)
#
# assets = Environment(app)
# assets.versions = 'timestamp'
# app_js_exts = Bundle('js/jquery.colorchange.js', 'js/jquery.iframe-transport.js',
#                    filters='jsmin', output='nadzweb.ext.min.js')
# app_js = Bundle('js/home.js', filters='jsmin', output='home.min.js')
# app_css = Bundle('style.css', 'jquery.tableless.css',filters='cssmin', output='nadzweb.min.css')
#
#
# js = Bundle('jquery.js', 'base.js', 'widgets.js',
#             filters='jsmin', output='gen/packed.js')
# assets.register('js_all', js)
# app.config['ASSETS_DEBUG'] = True

from flask.ext.assets import Environment, Bundle
assets = Environment(app)

# css_all = Bundle(
#     'agency.css','base.css','bootstrap.css','jquery.datetimepicker.css',
#     'login.css',
#     filters='cssmin',
#     output='gen/min.css',
# )

# js_all = Bundle(
#     'infinity.js',
#     filters='uglify',
#
#     # filters='jsmin',
#     output='gen/min.js',
# )

# These assets get passed templates to be rendered
# assets.register('css_all', css_all)
# assets.register('js_all', js_all)

# Route calls from app to viewController
viewController = Blueprint('viewController', __name__, template_folder='templates')

#Create Custom Admin views

class UserView(ModelView):
    # column_filters = ['name']
    # column_list =['name']
    # can_edit = True
    # column_searchable_list = ['name']
    # column_exclude_list = ('password')
    # form_excluded_columns = ('password')
    # form_ajax_refs = {
    #     'roles': {
    #         'fields': ['name']
    #     }
    # }
    # form_widget_args = {
    #     'name':{
    #         'disabled':True
    #     },
    #     'email':{
    #         'disabled':True
    #     },
    #     'active':{
    #         'disabled':True
    #     },
    #     'confirmed_at':{
    #         'disabled':True
    #     },
    #     'roles':{
    #         'disabled':True
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

class Aggr_dataView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('Root')
class MinuteView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('Root')
class HourView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('Root')
class DayView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('Root')
class MonthView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('Root')
class Site_data_minView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('Root')
class Site_data_hourView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('Root')
class Site_data_dayView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('Root')
class Site_data_monthView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('Root')
class AuditView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('Root')
class CompanyView(ModelView):
    column_exclude_list = ('users')
    form_excluded_columns = ('users')
class DeviceView(ModelView):
    # if current_user.has_role('Root'):
    form_widget_args = {
        'name':{
            'disabled':True
        },
        'url':{
            'disabled':True
        },
        'type':{
            'disabled':True
        },
        'site':{
            'disabled':True
        },
        'connId':{
            'disabled':True
        }
    }
    def is_accessible(self):
        return current_user.is_authenticated()

class SiteView(ModelView):
    # if current_user.has_role('Root'):
    form_widget_args = {
        'name':{
            'disabled':True
        },
        'deviceList':{
            'disabled':True
        }
    }
    def is_accessible(self):
        return current_user.is_authenticated()
# Add Admin Views
def adminViews(app):
    # Create admin
    admin = Admin(app, 'Infinity Admin')

    # if current_user.is_authenticated() and current_user.has_role('Root'):
        # Add admin views
    admin.add_view(UserView(infinity.User))
    admin.add_view(RoleView(infinity.Role))
    admin.add_view(CompanyView(infinity.Company))

    admin.add_view(ModelView(infinity.Tag))
    admin.add_view(DeviceView(infinity.Device))
    admin.add_view(SiteView(infinity.Site))

    admin.add_view(ModelView(infinity.Data))
    admin.add_view(ModelView(infinity.Site_data))

    admin.add_view(Aggr_dataView(infinity.Aggr_data))
    admin.add_view(MinuteView(infinity.Minute))
    admin.add_view(HourView(infinity.Hour))
    admin.add_view(DayView(infinity.Day))
    admin.add_view(MonthView(infinity.Month))
    admin.add_view(Site_data_minView(infinity.Site_data_min))
    admin.add_view(Site_data_hourView(infinity.Site_data_hour))
    admin.add_view(Site_data_dayView(infinity.Site_data_day))
    admin.add_view(Site_data_monthView(infinity.Site_data_month))

    # admin.add_view(ModelView(infinity.Config))
    # admin.add_view(ModelView(infinity.Firmware))
    # admin.add_view(ModelView(infinity.Freq))
    # admin.add_view(ModelView(infinity.Power))
    # admin.add_view(ModelView(infinity.Ssid))
    # admin.add_view(ModelView(infinity.Job))

    admin.add_view(ModelView(infinity.Beagle))
    admin.add_view(ModelView(infinity.Router))
    admin.add_view(ModelView(infinity.Event))
    admin.add_view(AuditView(infinity.Audit))


# Setup Admin Views
# @login_required  # if not logged in, login.html will be the default page
adminViews(app)


# Route main page


class ReadonlyTextField(TextField):
  def __call__(self, *args, **kwargs):
    kwargs.setdefault('readonly', True)
    return super(ReadonlyTextField, self).__call__(*args, **kwargs)

@app.route('/')
@login_required  # if not logged in, login.html will be the default page
def home():

    # now=datetime.datetime.now()
    # yesterday = now - datetime.timedelta(days=20)
    # now_js = time.mktime(now.timetuple()) * 1000
    # yesterday_js = time.mktime(yesterday.timetuple()) * 1000
    NOW = int(time.time())
    start = NOW - INTERVAL_INIT
    end = NOW
    ctx = {
        'chart_url':'/chart',
        'histogram_url':'/histogram',
        'path_url':'/path',
        'lastpoint_url':'/lastpoint',
        'stream_url':'/stream',

        'chart_url_site':'/chart_site',
        'histogram_url_site':'/histogram_site',
        'path_url_site':'/path_site',
        'lastpoint_url_site':'/lastpoint_site',
        'stream_url_site':'/stream_site',

        'data'     :chart_view_init(),
        'histogram':generate_histogram_init(),
        'path'     :generate_path_init(),
        'stream'   :stream_view_init(),

        'links_url':'/links',
        # 'onSite'   :'false',
        'site'     :site,
        'link'     :site,
        'fromTime' :start*1000,
        'toTime'   :end*1000,
        'lastTime' :end*1000,
        'type'     :deviceType,
        'streamInterval':streamInterval,
        'updateInterval':updateInterval
    }
    # if current_user.has_role('Root'):
    #     ctx['devices_url'] = '/devices'
    # else:
    #     ctx['devices_url'] = '/devices?type=CPE'

    ctx['devices_url'] = '/devices'
    dataController.startdata()
    # fromTime = calendar.timegm(start.timetuple()) * 1000
    # toTime = calendar.timegm(end.timetuple()) * 1000
    # ctx['fromTime']= fromTime
    # ctx['toTime']= toTime
    return html_minify(render_template('index.html',**ctx))
    # return render_template('index.html',**ctx)

@app.route('/lastpoint', methods= ['POST','GET'])
@login_required
def lastPoint():
    lastTime = int(flask.request.args.get('lastTime'))/1000
    site = flask.request.args.get('site')
    # type = flask.request.args.get('type')
    # if type == 'BTS':
    #     site = Device.objects(site = site).first()
    #     site = Device.objects(connId = site.connId, type = 'CPE').first().site
    # nowtime = int(time.time())
    # start = nowtime-15*60  # 15 mins
    # if lastTime > start and lastTime != nowtime:   # if lastTime is less than 15 mins, use it for start time
    #     start = lastTime
    # end = nowtime  # end time = current time
    # query_set = Aggr_data.objects(time__gt = start, time__lt = end, site = site ).order_by('time')\
    #     .only('time',"data","cap","distance")
    # ob = Aggr_data.objects(time__gte = lastTime, site = site ).first()
    # ob = Aggr_data.objects(site = site ).order_by("-time").first()
    # data = defaultdict(lambda :defaultdict)  # one-liner to initialize dictionary containing lists
    # data = defaultdict(list)
    query_set = Aggr_data.objects(time__gte = lastTime, site = site ).order_by('time')
    data = {}
    data["cap"]=[]
    data["data"]=[]
    data["distance"]=[]
    for ob in query_set:
    # if ob:
        t = ob.time*1000
        data["cap"].append([t,float("{0:.2f}".format(ob.cap))])
        data["data"].append([t,float("{0:.2f}".format(ob.data))])
        data["distance"].append([t,float("{0:.2f}".format(ob.distance))])
    data_dumps = Response(json.dumps(data),  mimetype='application/json')
    return data_dumps       # if there is no data it will return zero

@app.route('/lastpoint_site', methods= ['POST','GET'])
@login_required
def lastPoint_site():
    lastTime = int(flask.request.args.get('lastTime'))/1000
    site = flask.request.args.get('site')
    # type = flask.request.args.get('type')
    # if type == 'BTS':
    #     site = Device.objects(site = site).first()
    #     site = Device.objects(connId = site.connId, type = 'CPE').first().site
    # nowtime = int(time.time())
    # start = nowtime-15*60  # 15 mins
    # if lastTime > start and lastTime != nowtime:   # if lastTime is less than 15 mins, use it for start time
    #     start = lastTime
    # end = nowtime  # end time = current time
    # query_set = Site_data.objects(time__gt = start, time__lt = end, name = site ).order_by('time')\
    #     .only('time',"data","cap","distance")
    # ob = Aggr_data.objects(site = site ).order_by("-time").first()
    # data = defaultdict(lambda :defaultdict)  # one-liner to initialize dictionary containing lists
    # data = defaultdict(list)

    query_set = Site_data.objects(time__gte = lastTime, name = site ).order_by('time')

    data = {}
    data["cap"]=[]
    data["data"]=[]
    data["distance"]=[]
    for ob in query_set:
    # if ob:
        t = ob.time*1000
        data["cap"].append([t,float("{0:.2f}".format(ob.cap))])
        data["data"].append([t,float("{0:.2f}".format(ob.data))])
        data["distance"].append([t,float("{0:.2f}".format(ob.distance))])
    data_dumps = Response(json.dumps(data),  mimetype='application/json')
    return data_dumps       # if there is no data it will return zero


@app.route('/chart', methods= ['POST','GET'])
@login_required
def chart_view():
    toTime = int(flask.request.args.get('toTime'))/1000
    fromTime = int(flask.request.args.get('fromTime'))/1000
    site = flask.request.args.get('site')
    if fromTime == toTime:
        fromTime = toTime - INTERVAL_INIT
    # type = flask.request.args.get('type')
    # if type == 'BTS':
    #     site = Device.objects(site = site).first()
    #     site = Device.objects(connId = site.connId, type = 'CPE').first().site
    range = toTime - fromTime
    # 25 min range loads second data - 15s x 4 x 25 = 100 pts
    if (range < 5 * 60 ):
        query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
        only('time',"data","cap","distance").order_by('time')
        # if len(query_set)> 100:
        #     query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
        #     only('time',"data","cap","distance").order_by('time')
    # 100 min range loads minute data - 100 mins = 1hr 40 mins
    elif (range < 100 * 60 ):
        query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
        only('time',"data","cap","distance").order_by('time')
        # if len(query_set)< 50:
        #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
        #     only('time',"data","cap","distance").order_by('time')
    # 4 day range loads hourly data - 100 hours ~ 4 days
    elif (range < 25 * 3600 ):
        query_set = Hour.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
        only('time',"data","cap","distance").order_by('time')
        if len(query_set)< 12:
            query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
            only('time',"data","cap","distance").order_by('time')
            # if len(query_set)< 50:
            #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
            #     only('time',"data","cap","distance").order_by('time')
    # 1 yr range loads daily data = 100 days ~ 3.5 months
    elif (range < 30 * 24 * 3600 ):
        query_set = Day.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
        only('time',"data","cap","distance").order_by('time')
        if len(query_set)< 12:
            query_set = Hour.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
            only('time',"data","cap","distance").order_by('time')
            if len(query_set)< 12:
                query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
                only('time',"data","cap","distance").order_by('time')
                # if len(query_set)< 50:
                #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
                #     only('time',"data","cap","distance").order_by('time')
    # greater range loads monthly data
    else:
        query_set = Month.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
        only('time',"data","cap","distance").order_by('time')
        if len(query_set)< 12:
            query_set = Day.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
            only('time',"data","cap","distance").order_by('time')
            if len(query_set)< 12:
                query_set = Hour.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
                only('time',"data","cap","distance").order_by('time')
                if len(query_set)< 12:
                    query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
                    only('time',"data","cap","distance").order_by('time')
                    # if len(query_set)< 50:
                    #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
                    #     only('time',"data","cap","distance").order_by('time')
    # else :
    # #     query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
    # #     only('time',"data","cap","distance").order_by('time')
    #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
    #     only('time',"data","cap","distance").order_by('time')
    # if len(query_set) < 100 :
    #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
    #     only('time',"data","cap","distance").order_by('time')
    app.logger.info("chart size is %s " % len(query_set))
    data = {}
    data["cap"]=[]
    data["data"]=[]
    data["distance"]=[]
    # data = []

    for ob in query_set:
        # cap = (calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.cap)))
        # # data.append(list(s))
        # data = (calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.data)))
        # distance = (calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.distance)))

        t = ob.time*1000
        data["cap"].append([t,float("{0:.2f}".format(ob.cap))])   # multiple by 1.5 to see if data is changing
        data["data"].append([t,float("{0:.2f}".format(ob.data))])
        data["distance"].append([t,float("{0:.2f}".format(ob.distance))])

    data_dumps = Response(json.dumps(data),  mimetype='application/json')
    # data_jsonify = flask.jsonify(**data)  # same as flask.Response but doesn't quite work
    return data_dumps

@app.route('/chart_site', methods= ['POST','GET'])
@login_required
def chart_view_site():
    toTime = int(flask.request.args.get('toTime'))/1000
    fromTime = int(flask.request.args.get('fromTime'))/1000
    site = flask.request.args.get('site')
    if fromTime == toTime:
        fromTime = toTime - INTERVAL_INIT
    # type = flask.request.args.get('type')
    # if type == 'BTS':
    #     site = Device.objects(site = site).first()
    #     site = Device.objects(connId = site.connId, type = 'CPE').first().site
    range = toTime - fromTime
    # 25 min range loads second data - 25 x 4
    if (range < 5 * 60 ):
        query_set = Site_data.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
        only('time',"data","cap","distance").order_by('time')
        # if len(query_set)> 100:
        #     query_set = Site_data_min.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
        #     only('time',"data","cap","distance").order_by('time')
    # 100 min range loads minute data
    elif (range < 100 * 60 ):
        query_set = Site_data_min.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
        only('time',"data","cap","distance").order_by('time')
        # if len(query_set)< 50:
        #     query_set = Site_data.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
        #     only('time',"data","cap","distance").order_by('time')
    # 100 hrs range loads hourly data
    elif (range < 25 * 3600 ):
        query_set = Site_data_hour.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
        only('time',"data","cap","distance").order_by('time')
        if len(query_set)< 12:
            query_set = Site_data_min.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
            only('time',"data","cap","distance").order_by('time')
            # if len(query_set)< 50:
            #     query_set = Site_data.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
            #     only('time',"data","cap","distance").order_by('time')
    # 100 day range loads daily data
    elif (range < 30 * 24 * 3600 ):
        query_set = Site_data_day.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
        only('time',"data","cap","distance").order_by('time')
        if len(query_set)< 12:
            query_set = Site_data_hour.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
            only('time',"data","cap","distance").order_by('time')
            if len(query_set)< 12:
                query_set = Site_data_min.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
                only('time',"data","cap","distance").order_by('time')
                # if len(query_set)< 50:
                #     query_set = Site_data.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
                #     only('time',"data","cap","distance").order_by('time')
    # greater range loads monthly data
    else:
        query_set = Site_data_month.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
        only('time',"data","cap","distance").order_by('time')
        if len(query_set)< 12:
            query_set = Site_data_day.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
            only('time',"data","cap","distance").order_by('time')
            if len(query_set)< 12:
                query_set = Site_data_hour.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
                only('time',"data","cap","distance").order_by('time')
                if len(query_set)< 12:
                    query_set = Site_data_min.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
                    only('time',"data","cap","distance").order_by('time')
                    # if len(query_set)< 50:
                    #     query_set = Site_data.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
                    #     only('time',"data","cap","distance").order_by('time')
    # else :
    # #     query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
    # #     only('time',"data","cap","distance").order_by('time')
    #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
    #     only('time',"data","cap").order_by('time')

    # if len(query_set) < 100 :
    #     query_set = Site_data.objects(time__gt = fromTime, time__lt = toTime, name = site ).\
    #     only('time',"data","cap","distance").order_by('time')
    data = {}
    data["cap"]=[]
    data["data"]=[]
    data["distance"]=[]
    # data = []
    app.logger.info("chart_site size is %s " % len(query_set))

    for ob in query_set:
        # cap = (calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.cap)))
        # # data.append(list(s))
        # data = (calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.data)))
        # distance = (calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.distance)))

        t = ob.time*1000
        data["cap"].append([t,float("{0:.2f}".format(ob.cap))])   # multiple by 1.5 to see if data is changing
        data["data"].append([t,float("{0:.2f}".format(ob.data))])
        data["distance"].append([t,float("{0:.2f}".format(ob.distance))])

    data_dumps = Response(json.dumps(data),  mimetype='application/json')
    # data_jsonify = flask.jsonify(**data)  # same as flask.Response but doesn't quite work
    return data_dumps

def chart_view_init():
    # global start, end
    now = int(time.time())
    start = now - INTERVAL_INIT
    end = now
    # if start == end:
    #     start = end - INTERVAL_INIT
    query_set = Minute.objects(time__gt = start, time__lt = end, site = site ).\
        only('time',"data","cap","distance").order_by('time')
    data = {}
    data["cap"]=[]
    data["data"]=[]
    data["distance"]=[]
    # if query_set:
    #     start = query_set[0].time
    #     end = query_set[len(query_set)-1].time
    # # data =[]

    for ob in query_set:
        # t = (calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.data)),
        #          float("{0:.2f}".format(ob.cap)),float("{0:.2f}".format(ob.distance)))
        # s = (calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.data)))

        # data.append(list(s))
        t = ob.time*1000
        data["cap"].append([t,float("{0:.2f}".format(ob.cap))])   # multiple by 1.5 to see if data is changing
        data["data"].append([t,float("{0:.2f}".format(ob.data))])
        data["distance"].append([t,float("{0:.2f}".format(ob.distance))])

    return data

@app.route('/stream', methods= ['POST','GET'])
@login_required
def stream_view():
    # global start, end
    startStream = int(time.time())-STREAM_INTERVAL
    endStream = int(time.time())
    site = flask.request.args.get('site')
    type = flask.request.args.get('type')
    # if type == 'BTS':
    #     site = Device.objects(site = site).first()
    #     site = Device.objects(connId = site.connId, type = 'CPE').first().site
    query_set = Aggr_data.objects(time__gt = startStream, time__lt = endStream, site = site ).\
        only('time',"data","cap","distance").order_by('time')
    # if query_set:
    #     pass
    # else:
    #     query_set = Aggr_data.objects(time__gt = start, time__lt = end, site = site ).\
    #         only('time',"data","cap","distance").order_by('time')
    data = {}
    data["cap"]=[]
    data["data"]=[]
    data["distance"]=[]

    for ob in query_set:
        t = ob.time*1000
        data["cap"].append([t,float("{0:.2f}".format(ob.cap))])
        data["data"].append([t,float("{0:.2f}".format(ob.data))])
        data["distance"].append([t,float("{0:.2f}".format(ob.distance))])

    data_dumps = Response(json.dumps(data),  mimetype='application/json')

    return data_dumps

@app.route('/stream_site', methods= ['POST','GET'])
@login_required
def stream_view_site():
    # global start, end
    startStream = int(time.time())-STREAM_INTERVAL
    endStream = int(time.time())
    site = flask.request.args.get('site')
    type = flask.request.args.get('type')
    # if type == 'BTS':
    #     site = Device.objects(site = site).first()
    #     site = Device.objects(connId = site.connId, type = 'CPE').first().site
    query_set = Site_data.objects(time__gt = startStream, time__lt = endStream, name = site ).\
        only('time',"data","cap","distance").order_by('time')
    # if query_set:
    #     pass
    # else:
    #     query_set = Site_data.objects(time__gt = start, time__lt = end, name = site ).\
    #         only('time',"data","cap","distance").order_by('time')
    data = {}
    data["cap"]=[]
    data["data"]=[]
    data["distance"]=[]

    for ob in query_set:
        t = ob.time*1000
        data["cap"].append([t,float("{0:.2f}".format(ob.cap))])
        data["data"].append([t,float("{0:.2f}".format(ob.data))])
        data["distance"].append([t,float("{0:.2f}".format(ob.distance))])

    data_dumps = Response(json.dumps(data),  mimetype='application/json')

    return data_dumps

def stream_view_init():
    # global start, end
    startStream = int(time.time())-STREAM_INTERVAL
    endStream = int(time.time())
    # global start, end

    query_set = Aggr_data.objects(time__gt = startStream, time__lt = endStream, site = site ).\
        only('time',"data","cap","distance").order_by('time')
    # if query_set:
    #     pass
    # else:
    #     query_set = Aggr_data.objects(time__gt = start, time__lt = end, site = site ).\
    #         only('time',"data","cap","distance").order_by('time')
    data = {}
    data["cap"]=[]
    data["data"]=[]
    data["distance"]=[]

    for ob in query_set:
        t = ob.time*1000
        data["cap"].append([t,float("{0:.2f}".format(ob.cap))])
        data["data"].append([t,float("{0:.2f}".format(ob.data))])
        data["distance"].append([t,float("{0:.2f}".format(ob.distance))])

    return data

@app.route('/devices', methods=['POST','GET'])
@login_required
def get_devices_and_data():
    device_type = flask.request.args.get('type')
    response_data = []
    if device_type is None:
        for site in Site.objects:
            # recordObjects = Site_data.objects(name=site.name).order_by('-time').limit(5)   # todo: limit # of records to 5
            record = Site_data.objects(name=site.name).order_by('-time').first()   # todo: limit # of records to 5
            if record:
            # cpeDevice = Device.objects(type = 'CPE',site = site.name).first()
            # if len(recordObjects) > 3:
                # record = recordObjects [2]  # don't take the latest timestamp data, but a few seconds earlier
                response_data.append({"site":record.name,"tx":"{:.2f}".format(record.tx), "rx":"{:.2f}".format(record.rx),
                     "cap":"{:.2f}".format(record.cap), "data":"{:.2f}".format(record.data),
                     # "coverage":record.coverage,"distance":"{:.2f}".format(record.distance),
                     "lat":record.geo[0], "lng":record.geo[1], "time":record.time * 1000,"type":record.type})
                # btsDevice = Device.objects(type = 'BTS',connId = cpeDevice.connId).first()
                # response_data.append({"site":btsDevice.site,"tx":"{:.2f}".format(record.tx), "rx":"{:.2f}".format(record.rx),
                #  "cap":"{:.2f}".format(record.cap), "data":"{:.2f}".format(record.data),
                #  "coverage":record.coverage,"distance":"{:.2f}".format(record.distance),
                #  "lat":btsDevice.lat, "lng":btsDevice.lng, "time":record.time * 1000, "type":'BTS'})
    data_dumps= Response(json.dumps(response_data),  mimetype='application/json')
    return data_dumps

@app.route('/links', methods=['POST','GET'])
@login_required
def get_links():
    response_data = []
    timeStamp = int(flask.request.args.get('time'))/1000
    for device in Device.objects:
        if device.type == 'CPE':
            record = Data.objects(mac = device.name, time = timeStamp).first()
            if record:
                record = Aggr_data.objects(site = record.connId, time = record.time).first()
                site = Site.objects(deviceList__icontains = device.name).first()
                if site:
                    siteRecord = Site_data.objects(name = site.name, time = record.time).first()
                if siteRecord:
                    btsDevice = Device.objects(connId = record.site, type = 'BTS').first()
            #     btsRecord = Aggr_data.objects(site = btsDevice.site).order_by('-time').first()
            #     # distance = distance_in_miles(record.geo,btsRecord.geo)
                    if btsDevice is None:
                      app.logger.error("There is NO bts device corresponding to link %s " % record.site)
                    else:
                        response_data.append({"connId":record.site,"tx":"{:.2f}".format(record.tx),
                     "rx":"{:.2f}".format(record.rx),"cap":"{:.2f}".format(record.cap),
                     "data":"{:.2f}".format(record.data),
                     "lat":siteRecord.geo[0], "lng":siteRecord.geo[1], "lat1":btsDevice.lat, "lng1":btsDevice.lng,
                     "time":record.time * 1000, "distance":"{:.2f}".format(record.distance)})
                else:
                    app.logger.error("There is NO data corresponding to cpe %s " % device.name)

    data_dumps= Response(json.dumps(response_data),  mimetype='application/json')
    return data_dumps
    # data_jsonify= flask.jsonify(*response_data)
    # if (data_jsonify==data_dumps):
    #     print "data_jsonify is equal to data_dumps"
    # return Response(json.dumps(response_data),  mimetype='application/json')
    # return flask.jsonify(*response_data)  # same as flask.Response but doesn't work


def generate_histogram_init():
    # toTimeStamp = datetime.datetime.now()
    # fromTimeStamp = toTimeStamp-datetime.timedelta(days=15)
    # site = 'ShipA'
    now = int(time.time())
    start = now - INTERVAL_INIT
    end = now
    data = {}
    data["avg_cap"]=[]
    data["records"]=[]
    data["distance"]=[]
    total_records = len(Minute.objects(time__gt = start, time__lt = end, site = site ))
    if total_records == 0:   # prevent divide by zero condition
        total_records=1
    step=DISTANCE_STEP
    for x in range(step,DISTANCE_MAX,step):
        data["records"].append( len( Minute.objects(time__gt = start, time__lt = end,
                                   site = site , distance__lt = x, distance__gte = x-step) )*100/total_records )
        data["avg_cap"].append(float("{0:.2f}".format(Minute.objects(time__gt = start, time__lt = end, site = site
                                   , distance__lt = x, distance__gte = x-step).average('cap'))))
        data["distance"].append(x)

    return data


# @app.route('/histogram')
# @login_required
# def generate_histogram():
#
#     toTimeStamp = int(flask.request.args.get('toTime'))/1000
#     fromTimeStamp = int(flask.request.args.get('fromTime'))/1000
#     site = flask.request.args.get('site')
#     type = flask.request.args.get('type')
#     if fromTimeStamp == toTimeStamp:
#         fromTimeStamp = toTimeStamp - INTERVAL_INIT
#     # if type == 'BTS':
#     #     site = Device.objects(site = site).first()
#     #     site = Device.objects(connId = site.connId, type = 'CPE').first().site
#     data = {}
#     data["avg_cap"]=[]
#     data["records"]=[]
#     data["distance"]=[]
#
#     total_records = len(Minute.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site ))
#     if total_records == 0:
#         total_records=1
#     step=DISTANCE_STEP
#     for x in range(step,DISTANCE_MAX,step):
#         data["records"].append( len( Minute.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp,
#                                      site = site , distance__lt = x, distance__gte = x-step) )*100/total_records )
#         data["avg_cap"].append(float("{0:.2f}".format(Minute.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site
#                                      , distance__lt = x, distance__gte = x-step).average('cap'))))
#         data["distance"].append(x)

    # data_dumps= Response(json.dumps(data),  mimetype='application/json')
    # return data_dumps
@app.route('/histogram')
@login_required
def generate_histogram():

    toTimeStamp = int(flask.request.args.get('toTime'))/1000
    fromTimeStamp = int(flask.request.args.get('fromTime'))/1000
    site = flask.request.args.get('site')
    if fromTimeStamp == toTimeStamp:
        fromTimeStamp = toTimeStamp - INTERVAL_INIT
    data = {}
    data["avg_cap"]=[]
    data["records"]=[]
    data["distance"]=[]
    range = toTimeStamp - fromTimeStamp
    if (range < 24 * 3600 ):
        total_records = len(Minute.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site ))
        histogramLinkMin(fromTimeStamp,toTimeStamp,site,total_records,data)

    elif (range < 30 * 24 * 3600 ):
        total_records = len(Hour.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site ))
        if total_records < 12:
            total_records = len(Minute.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site ))
            histogramLinkMin(fromTimeStamp,toTimeStamp,site,total_records,data)
        else :
            histogramLinkHour(fromTimeStamp,toTimeStamp,site,total_records,data)

    elif (range < 365 * 24 * 3600 ):
        total_records = len(Day.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site ))
        if total_records < 12:
            total_records = len(Hour.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site ))
            if total_records < 12:
                total_records = len(Minute.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site ))
                histogramLinkMin(fromTimeStamp,toTimeStamp,site,total_records,data)
            else :
                histogramLinkHour(fromTimeStamp,toTimeStamp,site,total_records,data)
        else :
            histogramLinkDay(fromTimeStamp,toTimeStamp,site,total_records,data)
    else:
        total_records = len(Month.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site ))
        if total_records < 12:
            total_records = len(Day.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site ))
            if total_records < 12:
                total_records = len(Hour.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site ))
                if total_records < 12:
                    total_records = len(Minute.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site ))
                    histogramLinkMin(fromTimeStamp,toTimeStamp,site,total_records,data)
                else :
                    histogramLinkHour(fromTimeStamp,toTimeStamp,site,total_records,data)
            else :
                histogramLinkDay(fromTimeStamp,toTimeStamp,site,total_records,data)
        else :
            histogramLinkMonth(fromTimeStamp,toTimeStamp,site,total_records,data)

    data_dumps= Response(json.dumps(data),  mimetype='application/json')
    return data_dumps

@app.route('/histogram_site')
@login_required
def generate_histogram_site():

    toTimeStamp = int(flask.request.args.get('toTime'))/1000
    fromTimeStamp = int(flask.request.args.get('fromTime'))/1000
    site = flask.request.args.get('site')
    # type = flask.request.args.get('type')
    if fromTimeStamp == toTimeStamp:
        fromTimeStamp = toTimeStamp - INTERVAL_INIT
    # if type == 'BTS':
    #     site = Device.objects(site = site).first()
    #     site = Device.objects(connId = site.connId, type = 'CPE').first().site
    data = {}
    data["avg_cap"]=[]
    data["records"]=[]
    data["distance"]=[]
    range = toTimeStamp - fromTimeStamp
    if (range < 24 * 3600 ):
        total_records = len(Site_data_min.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, name = site ))
        histogramSiteMin(fromTimeStamp,toTimeStamp,site,total_records,data)

    elif (range < 30 * 24 * 3600 ):
        total_records = len(Site_data_hour.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, name = site ))
        if total_records < 12:
            total_records = len(Site_data_min.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, name = site ))
            histogramSiteMin(fromTimeStamp,toTimeStamp,site,total_records,data)
        else :
            histogramSiteHour(fromTimeStamp,toTimeStamp,site,total_records,data)

    elif (range < 365 * 24 * 3600 ):
        total_records = len(Site_data_day.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, name = site ))
        if total_records < 12:
            total_records = len(Site_data_hour.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, name = site ))
            if total_records < 12:
                total_records = len(Site_data_min.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, name = site ))
                histogramSiteMin(fromTimeStamp,toTimeStamp,site,total_records,data)
            else :
                histogramSiteHour(fromTimeStamp,toTimeStamp,site,total_records,data)
        else :
            histogramSiteDay(fromTimeStamp,toTimeStamp,site,total_records,data)
    else:
        total_records = len(Site_data_month.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, name = site ))
        if total_records < 12:
            total_records = len(Site_data_day.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, name = site ))
            if total_records < 12:
                total_records = len(Site_data_hour.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, name = site ))
                if total_records < 12:
                    total_records = len(Site_data_min.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, name = site ))
                    histogramSiteMin(fromTimeStamp,toTimeStamp,site,total_records,data)
                else :
                    histogramSiteHour(fromTimeStamp,toTimeStamp,site,total_records,data)
            else :
                histogramSiteDay(fromTimeStamp,toTimeStamp,site,total_records,data)
        else :
            histogramSiteMonth(fromTimeStamp,toTimeStamp,site,total_records,data)

    # total_records = len(Site_data_min.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, name = site ))
    # doc = Site_data_min()
    # histSiteMin(fromTimeStamp,toTimeStamp,site,total_records,data,doc)

    # if total_records == 0:
    #     total_records=1
    # step=DISTANCE_STEP
    # for x in range(step,DISTANCE_MAX,step):
    #     # data["records"].append( len( Site_data.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp,
    #     #                              name = site , cap__lt = x, cap__gte = x-step) )*100/total_records )
    #     # # data["avg_cap"].append(float("{0:.2f}".format(Aggr_data.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site
    #     # #                              , distance__lt = x, distance__gte = x-step).average('cap'))))
    #     # data["avg_cap"].append(x)
    #     data["records"].append( len( Site_data_min.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp,
    #                                  name = site , distance__lt = x, distance__gte = x-step) )*100/total_records )
    #     data["avg_cap"].append(float("{0:.2f}".format(Site_data_min.objects(time__gt = fromTimeStamp,
    #                     time__lt = toTimeStamp,name = site, distance__lt = x, distance__gte = x-step).average('cap'))))
    #     data["distance"].append(x)
    #
    data_dumps= Response(json.dumps(data),  mimetype='application/json')
    return data_dumps

def histogramSiteMin(fromTimeStamp, toTimeStamp, site, total_records,data):
    if total_records == 0:
        total_records=1
    step=DISTANCE_STEP
    for x in range(step,DISTANCE_MAX,step):
        data["records"].append( len( Site_data_min.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp,
                                     name = site , distance__lt = x, distance__gte = x-step) )*100/total_records )
        data["avg_cap"].append(float("{0:.2f}".format(Site_data_min.objects(time__gt = fromTimeStamp,
                        time__lt = toTimeStamp,name = site, distance__lt = x, distance__gte = x-step).average('cap'))))
        data["distance"].append(x)

    return data

def histogramSiteHour(fromTimeStamp, toTimeStamp, site, total_records,data):
    if total_records == 0:
        total_records=1
    step=DISTANCE_STEP
    for x in range(step,DISTANCE_MAX,step):
        data["records"].append( len( Site_data_hour.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp,
                                     name = site , distance__lt = x, distance__gte = x-step) )*100/total_records )
        data["avg_cap"].append(float("{0:.2f}".format(Site_data_hour.objects(time__gt = fromTimeStamp,
                        time__lt = toTimeStamp,name = site, distance__lt = x, distance__gte = x-step).average('cap'))))
        data["distance"].append(x)

    return data

def histogramSiteDay(fromTimeStamp, toTimeStamp, site, total_records,data):
    if total_records == 0:
        total_records=1
    step=DISTANCE_STEP
    for x in range(step,DISTANCE_MAX,step):
        data["records"].append( len( Site_data_day.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp,
                                     name = site , distance__lt = x, distance__gte = x-step) )*100/total_records )
        data["avg_cap"].append(float("{0:.2f}".format(Site_data_day.objects(time__gt = fromTimeStamp,
                        time__lt = toTimeStamp,name = site, distance__lt = x, distance__gte = x-step).average('cap'))))
        data["distance"].append(x)

    return data

def histogramSiteMonth(fromTimeStamp, toTimeStamp, site, total_records,data):
    if total_records == 0:
        total_records=1
    step=DISTANCE_STEP
    for x in range(step,DISTANCE_MAX,step):
        data["records"].append( len( Site_data_month.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp,
                                     name = site , distance__lt = x, distance__gte = x-step) )*100/total_records )
        data["avg_cap"].append(float("{0:.2f}".format(Site_data_month.objects(time__gt = fromTimeStamp,
                        time__lt = toTimeStamp,name = site, distance__lt = x, distance__gte = x-step).average('cap'))))
        data["distance"].append(x)

    return data

def histogramLinkMin(fromTimeStamp, toTimeStamp, site, total_records,data):
    if total_records == 0:
        total_records=1
    step=DISTANCE_STEP
    for x in range(step,DISTANCE_MAX,step):
        data["records"].append( len( Minute.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp,
                                     site = site , distance__lt = x, distance__gte = x-step) )*100/total_records )
        data["avg_cap"].append(float("{0:.2f}".format(Minute.objects(time__gt = fromTimeStamp,
                        time__lt = toTimeStamp,site = site, distance__lt = x, distance__gte = x-step).average('cap'))))
        data["distance"].append(x)

    return data

def histogramLinkHour(fromTimeStamp, toTimeStamp, site, total_records,data):
    if total_records == 0:
        total_records=1
    step=DISTANCE_STEP
    for x in range(step,DISTANCE_MAX,step):
        data["records"].append( len( Hour.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp,
                                     site = site , distance__lt = x, distance__gte = x-step) )*100/total_records )
        data["avg_cap"].append(float("{0:.2f}".format(Hour.objects(time__gt = fromTimeStamp,
                        time__lt = toTimeStamp,site = site, distance__lt = x, distance__gte = x-step).average('cap'))))
        data["distance"].append(x)

    return data

def histogramLinkDay(fromTimeStamp, toTimeStamp, site, total_records,data):
    if total_records == 0:
        total_records=1
    step=DISTANCE_STEP
    for x in range(step,DISTANCE_MAX,step):
        data["records"].append( len( Day.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp,
                                     site = site , distance__lt = x, distance__gte = x-step) )*100/total_records )
        data["avg_cap"].append(float("{0:.2f}".format(Day.objects(time__gt = fromTimeStamp,
                        time__lt = toTimeStamp,site = site, distance__lt = x, distance__gte = x-step).average('cap'))))
        data["distance"].append(x)

    return data

def histogramLinkMonth(fromTimeStamp, toTimeStamp, site, total_records,data):
    if total_records == 0:
        total_records=1
    step=DISTANCE_STEP
    for x in range(step,DISTANCE_MAX,step):
        data["records"].append( len( Month.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp,
                                     site = site , distance__lt = x, distance__gte = x-step) )*100/total_records )
        data["avg_cap"].append(float("{0:.2f}".format(Month.objects(time__gt = fromTimeStamp,
                        time__lt = toTimeStamp,site = site, distance__lt = x, distance__gte = x-step).average('cap'))))
        data["distance"].append(x)

    return data

@app.route('/path')
@login_required
def generate_path():

    toTime = int(flask.request.args.get('toTime'))/1000
    fromTime = int(flask.request.args.get('fromTime'))/1000
    site = flask.request.args.get('site')
    type = flask.request.args.get('type')
    if fromTime == toTime:
        fromTime = toTime - INTERVAL_INIT
    # if type == 'BTS':
    #     site = Device.objects(site = site).first()
    #     site = Device.objects(connId = site.connId, type = 'CPE').first().site
    # query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site )\
    #     .only('time',"cap","geo","distance","coverage")
    # start = 0
    # skip = len(query_set)/MAX_POINTS
    range = toTime - fromTime
    # 25 min range loads second data - 15s x 4 x 25 = 100 pts
    if (range < 5 * 60 ):
        query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site )
        # if len(query_set)> 100:
        #     query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site )
    # 100 min range loads minute data - 100 mins = 1hr 40 mins
    elif (range < 100 * 60 ):
        query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site )
        # if len(query_set)< 50:
        #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site )
    # 1 day range loads hourly data
    elif (range < 25 * 3600 ):
        query_set = Hour.objects(time__gt = fromTime, time__lt = toTime, site = site )
        if len(query_set)< 12:
            query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site )
            # if len(query_set)< 50:
            #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site )
    # 30 day range loads daily data
    elif (range < 30 * 24 * 3600 ):
        query_set = Day.objects(time__gt = fromTime, time__lt = toTime, site = site )
        if len(query_set)< 12:
            query_set = Hour.objects(time__gt = fromTime, time__lt = toTime, site = site )
            if len(query_set)< 12:
                query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site )
                # if len(query_set)< 50:
                #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site )
    # greater range loads monthly data
    else:
        query_set = Month.objects(time__gt = fromTime, time__lt = toTime, site = site )
        if len(query_set)< 12:
            query_set = Day.objects(time__gt = fromTime, time__lt = toTime, site = site )
            if len(query_set)< 12:
                query_set = Hour.objects(time__gt = fromTime, time__lt = toTime, site = site )
                if len(query_set)< 12:
                    query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site )
                    # if len(query_set)< 50:
                    #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site )


    # else :
    # #     query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
    # #     only('time',"data","cap","distance").order_by('time')
    #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
    #     only('time',"data","cap","distance").order_by('time')
    # if len(query_set) < 100 :
    #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site )


    app.logger.info("path size is %s " % len(query_set))



    data = {}
    data["cap"]=[]
    data["lat"]=[]
    data["lng"]=[]
    data["dist"]=[]
    data["cov"]=[]
    data["time"]=[]
    for ob in query_set:
        # if start == 0:
            data["cap"].append(float("{0:.2f}".format(ob.cap)))
            data["lat"].append(float("{0:.2f}".format(ob.geo[0])))
            data["lng"].append(float("{0:.2f}".format(ob.geo[1])))
            data["time"].append(ob.time*1000 )
            data["cov"].append(int(ob.coverage))
            data["dist"].append(float("{0:.2f}".format(ob.distance)))

        #     start +=1
        # else:
        #     if start > skip:
        #         start = 0
        #     else:
        #         start+=1
    data_dumps= Response(json.dumps(data),  mimetype='application/json')
    return data_dumps

@app.route('/path_site')
@login_required
def generate_path_site():

    toTime = int(flask.request.args.get('toTime'))/1000
    fromTime = int(flask.request.args.get('fromTime'))/1000
    site = flask.request.args.get('site')
    type = flask.request.args.get('type')
    if fromTime == toTime:
        fromTime = toTime - INTERVAL_INIT
    range = toTime - fromTime
    # 25 min range loads second data - 25 x 4
    if (range < 5 * 60 ):
        query_set = Site_data.objects(time__gt = fromTime, time__lt = toTime, name = site )
        # if len(query_set)> 100:
        #     query_set = Site_data_min.objects(time__gt = fromTime, time__lt = toTime, site = site )
    # 100 min range loads minute data
    elif (range < 100 * 60 ):
        query_set = Site_data_min.objects(time__gt = fromTime, time__lt = toTime, name = site )
        # if len(query_set)< 50:
        #     query_set = Site_data.objects(time__gt = fromTime, time__lt = toTime, name = site )
    # 100 hrs range loads hourly data
    elif (range < 25 * 3600 ):
        query_set = Site_data_hour.objects(time__gt = fromTime, time__lt = toTime, name = site )
        if len(query_set)< 12:
            query_set = Site_data_min.objects(time__gt = fromTime, time__lt = toTime, name = site )
            # if len(query_set)< 50:
            #     query_set = Site_data.objects(time__gt = fromTime, time__lt = toTime, name = site )
    # 100 day range loads daily data
    elif (range < 30 * 24 * 3600 ):
        query_set = Site_data_day.objects(time__gt = fromTime, time__lt = toTime, name = site )
        if len(query_set)< 12:
            query_set = Site_data_hour.objects(time__gt = fromTime, time__lt = toTime, name = site )
            if len(query_set)< 12:
                query_set = Site_data_min.objects(time__gt = fromTime, time__lt = toTime, name = site )
                # if len(query_set)< 50:
                #     query_set = Site_data.objects(time__gt = fromTime, time__lt = toTime, name = site )
    # greater range loads monthly data
    else:
        query_set = Site_data_month.objects(time__gt = fromTime, time__lt = toTime, name = site )
        if len(query_set)< 12:
            query_set = Site_data_day.objects(time__gt = fromTime, time__lt = toTime, name = site )
            if len(query_set)< 12:
                query_set = Site_data_hour.objects(time__gt = fromTime, time__lt = toTime, name = site )
                if len(query_set)< 12:
                    query_set = Site_data_min.objects(time__gt = fromTime, time__lt = toTime, name = site )
                    # if len(query_set)< 50:
                    #     query_set = Site_data.objects(time__gt = fromTime, time__lt = toTime, name = site )
    # else :
    # #     query_set = Minute.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
    # #     only('time',"data","cap","distance").order_by('time')
    #     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
    #     only('time',"data","cap").order_by('time')

    # if len(query_set) < 100 :
    #     query_set = Site_data.objects(time__gt = fromTime, time__lt = toTime, name = site )

    # if type == 'BTS':
    #     site = Device.objects(site = site).first()
    #     site = Device.objects(connId = site.connId, type = 'CPE').first().site
    # query_set = Site_data.objects(time__gt = fromTime, time__lt = toTime, name = site )\
    #     .only('time',"cap","geo","distance")
    # start = 0
    # skip = len(query_set)/MAX_POINTS
    data = {}
    data["cap"]=[]
    data["lat"]=[]
    data["lng"]=[]
    data["dist"]=[]
    # data["cov"]=[]
    data["time"]=[]
    app.logger.info("path_site size is %s " % len(query_set))

    for ob in query_set:
        # if start == 0:
            data["cap"].append(float("{0:.2f}".format(ob.cap)))
            data["lat"].append(float("{0:.2f}".format(ob.geo[0])))
            data["lng"].append(float("{0:.2f}".format(ob.geo[1])))
            data["time"].append(ob.time*1000 )
            # data["cov"].append(int(ob.coverage))
            data["dist"].append(float("{0:.2f}".format(ob.distance)))

        #     start +=1
        # else:
        #     if start > skip:
        #         start = 0
        #     else:
        #         start+=1
    data_dumps= Response(json.dumps(data),  mimetype='application/json')
    return data_dumps

def generate_path_init():

    # toTime = datetime.datetime.now()
    # fromTime = toTime-datetime.timedelta(days=15)
    # site = 'ShipA'
    now = int(time.time())
    start = now - INTERVAL_INIT
    end = now
    query_set = Minute.objects(time__gt = start, time__lt = end, site = site )\
        .only('time',"cap","geo","distance","coverage")
    # start = 0
    # skip = len(query_set)/MAX_POINTS
    data = {}
    data["cap"]=[]
    data["lat"]=[]
    data["lng"]=[]
    data["time"]=[]
    data["dist"]=[]
    data["cov"]=[]

    for ob in query_set:
        # if start == 0:
            data["cap"].append(float("{0:.2f}".format(ob.cap)))
            data["lat"].append(float("{0:.2f}".format(ob.geo[0])))
            data["lng"].append(float("{0:.2f}".format(ob.geo[1])))
            data["time"].append(ob.time*1000 )
            data["cov"].append(int(ob.coverage))
            data["dist"].append(float("{0:.2f}".format(ob.distance)))

            # start +=1
        # else:
        #     if start > skip:
        #         start = 0
        #     else:
        #         start+=1

    return data



# @app.route("/ping/<ip>", methods=['GET','POST'])
# def get_ping_status(ip):
#     value = get_status(ip)
#     if value != 0:
#         return get_status(ip)
#     else:
#         return value
#
#
#
# def get_status(ip):
#     res = subprocess.call(['ping', '-c', '1', '-W', '1', ip])
#     if res == 0:
#         app.logger.info('successfully pinged to ip: %s, ' % ip)
#     elif res == 2:
#         app.logger.info('no response for the pinged to ip: %s, ' % ip)
#     else:
#         res = -1
#         app.logger.info('failed to ping the ip: %s, ' % ip)
#     return  res


# @app.route('/chart/<mac>')
# @login_required
# def chart_view1(site,fromTime,toTime):
#
#     total_records = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site ).only("time","data","cap","distance")
#
#     timeStamp = time.strftime("%Y-%m-%d %H:%M:%S")
#     time.sleep(1)
#     timeStamp1 = time.strftime("%Y-%m-%d %H:%M:%S")
#     time.sleep(1)
#     timeStamp2 = time.strftime("%Y-%m-%d %H:%M:%S")
#
#     trace1 = Scatter(
#         x=[
#                 timeStamp,
#                 timeStamp1,
#                 timeStamp2,],
#         y=[40, 50, 60],
#         name='Capacity'
#     )
#     trace2 = Scatter(
#         x=[
#                 timeStamp2,
#                 timeStamp1,
#                 timeStamp,],
#         y=[4, 5, 6],
#         name='Traffic',
#         yaxis='y2'
#     )
#     data = Data([trace1, trace2])
#     layout = Layout(
#         title='Capacity and Traffic',
#         yaxis=YAxis(
#             title='Capacity'
#         ),
#         yaxis2=YAxis(
#             title='Traffic',
#             titlefont=Font(
#                 color='rgb(148, 103, 189)'
#             ),
#             tickfont=Font(
#                 color='rgb(148, 103, 189)'
#             ),
#             overlaying='y',
#             side='right'
#         ),
#         xaxis=XAxis(
#             title='AXIS TITLE',
#             titlefont=Font(
#                 family='Arial, sans-serif',
#                 size=18,
#                 color='grey'
#             )
#         )
#     )
#     fig = Figure(data=data, layout=layout)
#     plot_url = py.plot(fig, filename='multiple-axes-double', auto_open=False)
#
#     ctx={}
#     ctx['plot']=plot_url
#     return plot_url



    # trace1 = Bar(
    #     x=distance,
    #     y=avg_cap,
    #     name='Avg Capacity'
    # )
    # trace2 = Bar(
    #     x=distance,
    #     y=records,
    #     name='% Time'
    #     # ,
    #     # yaxis='y2'
    # )
    # data = Data([trace1, trace2])
    #
    # layout = Layout(
    #     barmode='group',
    #
    #     title='Capacity,Time vs Distance',
    #     yaxis=YAxis(
    #         title='Capacity, %Time'
    #     ),
    #     # yaxis2=YAxis(
    #     #     title='% Time',
    #     #     titlefont=Font(
    #     #         color='rgb(148, 103, 189)'
    #     #     ),
    #     #     tickfont=Font(
    #     #         color='rgb(148, 103, 189)'
    #     #     ),
    #     #     overlaying='y',
    #     #     side='right'
    #     # ),
    #     xaxis=XAxis(
    #         title='Distance',
    #         titlefont=Font(
    #             family='Arial, sans-serif',
    #             size=18,
    #             color='grey'
    #         )
    #     )
    # )
    # fig = Figure(data=data, layout=layout)
    # plot_url = py.plot(fig, filename='grouped-bar', auto_open=False)
    # return plot_url

            # x = ob.time.strftime("%Y-%m-%d %H:%M:%S")
        # data["time"].append(time.mktime(ob.time.timetuple()) * 1000)

        # x = time.mktime(ob.time.timetuple()) * 1000
        # data["cap"].append([x,ob.cap])
        # data["data"].append([x,ob.data])
        # data["distance"].append([x,ob.distance])


# app.route('/path')
# @login_required
# def generate_path():
#
#     toTime = datetime.datetime.fromtimestamp(int(flask.request.args.get('toTime'))/1000)
#     fromTime = datetime.datetime.fromtimestamp(int(flask.request.args.get('fromTime'))/1000)
#     site = flask.request.args.get('site')
#     tic = time.time()
#     query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site )
#     toc = time.time()
#     delta = toc-tic
    # skip = len(query_set)/MAX_POINTS
    # data = {}
    # data["cap"]=[]
    # data["lat"]=[]
    # data["lng"]=[]
    # start = 0
    # for ob in query_set:
    #     if start == 0:
    #         data["cap"].append(float("{0:.2f}".format(ob.cap)))
    #         data["lat"].append(float("{0:.2f}".format(ob.geo[0])))
    #         data["lng"].append(float("{0:.2f}".format(ob.geo[1])))
    #
    #         # data["cap"].append(ob.cap)
    #         # data["lat"].append(ob.geo[0])
    #         # data["lng"].append(ob.geo[1])
    #         start +=1
    #     else:
    #         if start > skip:
    #             start = 0
    #         else:
    #             start+=1
    #
    # toc2 = time.time()
    # delta2 = toc2-tic
    # app.logger.info("delta = %s, delta2 = %s"% (delta,delta2))
    # num = query_set.count()
    # data = []
    # for doc in query_set:
    #     data.append((
    #        doc['data'],
    #        doc['tx'],
    #        doc['cap']
    #     ))
    #
    # toc3 = time.time()
    # delta3 = toc3-toc
    #
    # # data1 = zip(*data)
    # arrays = numpy.array(data)
    # data1={}
    # data1['lat']=[]
    # data1['lng']=[]
    # data1['cap']=[]
    # data1['lat']=arrays[: ,0].tolist()
    # data1['lng']=arrays[: ,1].tolist()
    # data1['cap']=arrays[: ,2].tolist()
    # toc4 = time.time()
    # delta4 = toc4-toc3
    #
    #
    #
    # with Monary("127.0.0.1") as monary:
    #     arrays = monary.query(
    #         "infinity",                         # database name
    #         "aggr_data",                   # collection name
    #         {"time":{'$gt':fromTime, '$lt':toTime},'site':site},                             # query spec
    #         ["cap", "data","tx"], # field names (in Mongo record)
    #         ["float64"] * 3                # Monary field types (see below)
    #     )
    # data1={}
    # data1['lat']=arrays[0]
    # data1['lng']=arrays[1]
    # data1['cap']=arrays[2]
    # # data1['lat']=arrays[: ,0].tolist()
    # # data1['lng']=arrays[: ,1].tolist()
    # # data1['cap']=arrays[: ,2].tolist()
    # toc5 = time.time()
    # delta5 = toc5-toc4
    #
    # app.logger.info(" delta = %s, delta3 = %s, delta4 = %s, delta5 = %s"% (delta, delta3, delta4, delta5))
    #
    # data_dumps= Response(json.dumps(data1),  mimetype='application/json')
    # return data_dumps