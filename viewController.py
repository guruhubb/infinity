from flask import Blueprint, render_template, Response
from flask.ext.security import login_required, current_user
from flask.ext.admin import Admin
from flask.ext.admin.contrib.mongoengine import ModelView
import infinity
import flask, datetime, time, subprocess, json,calendar
from infinity import app, Site, Aggr_data
from monary import Monary
import numpy
MAX_POINTS = 100
start = datetime.datetime.utcnow() - datetime.timedelta(days=15)
end = datetime.datetime.utcnow()
site = 'ShipA'
# import plotly.plotly as py
# from plotly.graph_objs import *
# py.sign_in("saswata", "mret9csgsi")


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
    admin.add_view(ModelView(infinity.Beagle))
    admin.add_view(ModelView(infinity.Router))
    admin.add_view(ModelView(infinity.Data))
    admin.add_view(ModelView(infinity.Aggr_data))
    admin.add_view(ModelView(infinity.Sixty))
    admin.add_view(ModelView(infinity.Hour))
    # admin.add_view(ModelView(infinity.Config))
    # admin.add_view(ModelView(infinity.Firmware))
    # admin.add_view(ModelView(infinity.Freq))
    # admin.add_view(ModelView(infinity.Power))
    # admin.add_view(ModelView(infinity.Ssid))
    admin.add_view(ModelView(infinity.Site))
    # admin.add_view(ModelView(infinity.Job))
    admin.add_view(ModelView(infinity.Event))
    admin.add_view(ModelView(infinity.Audit))

# Setup Admin Views
adminViews(app)


# Route main page

@app.route('/')
@login_required  # if not logged in, login.html will be the default page
def home():

    # now=datetime.datetime.now()
    # yesterday = now - datetime.timedelta(days=20)
    # now_js = time.mktime(now.timetuple()) * 1000
    # yesterday_js = time.mktime(yesterday.timetuple()) * 1000

    ctx = {
        'chart_url':'/chart',
        'histogram_url':'/histogram',
        'path_url':'/path',
        'lastPoint_url':'/lastpoint',
        'data'     :chart_view_init(),
        'histogram':generate_histogram_init(),
        'path'     :generate_path_init(),
        'site'     :site

    }
    if current_user.has_role('Root'):
        ctx['devices_url'] = '/devices'
    else:
        ctx['devices_url'] = '/devices?type=CPE'
    fromTime = calendar.timegm(start.timetuple()) * 1000
    toTime = calendar.timegm(end.timetuple()) * 1000
    ctx['fromTime']= fromTime
    ctx['toTime']= toTime
    return render_template('index.html',**ctx)

@app.route('/lastpoint', methods= ['POST','GET'])
@login_required
def lastPoint():
    # toTime = datetime.datetime.utcfromtimestamp(int(flask.request.args.get('toTime'))/1000)
    # fromTime = datetime.datetime.utcfromtimestamp(int(flask.request.args.get('fromTime'))/1000)
    site = flask.request.args.get('site')

    ob = Aggr_data.objects(site = site ).\
        only("time","data","cap","distance").order_by("-time").first()

    data = {}
    data["cap"]=[calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.cap))]
    data["data"]=[calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.data))]
    data["distance"]=[calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.distance))]
    # data = []

    # for ob in query_set:
    #
    #     # cap = (calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.cap)))
    #     # # data.append(list(s))
    #     # data = (calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.data)))
    #     # distance = (calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.distance)))
    #
    #
    #     data["cap"].append([calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.cap))])   # multiple by 1.5 to see if data is changing
    #     data["data"].append([calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.data))])
    #     data["distance"].append([calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.distance))])


    data_dumps = Response(json.dumps(data),  mimetype='application/json')
    # data_jsonify = flask.jsonify(**data)  # same as flask.Response but doesn't quite work
    return data_dumps

@app.route('/chart', methods= ['POST','GET'])
@login_required
def chart_view():
    toTime = datetime.datetime.utcfromtimestamp(int(flask.request.args.get('toTime'))/1000)
    fromTime = datetime.datetime.utcfromtimestamp(int(flask.request.args.get('fromTime'))/1000)
    site = flask.request.args.get('site')

    query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site ).\
        only("time","data","cap","distance").order_by("time")

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

        t = calendar.timegm(ob.time.timetuple()) * 1000
        data["cap"].append([t,float("{0:.2f}".format(ob.cap))])   # multiple by 1.5 to see if data is changing
        data["data"].append([t,float("{0:.2f}".format(ob.data))])
        data["distance"].append([t,float("{0:.2f}".format(ob.distance))])


    data_dumps = Response(json.dumps(data),  mimetype='application/json')
    # data_jsonify = flask.jsonify(**data)  # same as flask.Response but doesn't quite work
    return data_dumps


def chart_view_init():

    query_set = Aggr_data.objects(time__gt = start, time__lt = end, site = site ).\
        only("time","data","cap","distance").order_by("time")
    global start, end
    start = query_set[0].time
    end = query_set[len(query_set)-1].time
    data = {}
    data["cap"]=[]
    data["data"]=[]
    data["distance"]=[]
    # data =[]

    for ob in query_set:
        # t = (calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.data)),
        #          float("{0:.2f}".format(ob.cap)),float("{0:.2f}".format(ob.distance)))
        # s = (calendar.timegm(ob.time.timetuple()) * 1000,float("{0:.2f}".format(ob.data)))

        # data.append(list(s))
        t = calendar.timegm(ob.time.timetuple()) * 1000
        data["cap"].append([t,float("{0:.2f}".format(ob.cap))])   # multiple by 1.5 to see if data is changing
        data["data"].append([t,float("{0:.2f}".format(ob.data))])
        data["distance"].append([t,float("{0:.2f}".format(ob.distance))])

    return data

@app.route('/devices', methods=['POST','GET'])
@login_required
def get_devices_and_data():
    device_type = flask.request.args.get('type')
    sites = Site.objects.only('name')
    response_data = []
    if device_type is None:
        for site in sites:
            record = Aggr_data.objects(site=site.name).order_by("-time").first()
            if record is not None:
                response_data.append({"site":record.site,"tx":"{:.2f}".format(record.tx), "rx":"{:.2f}".format(record.rx),
                                      "cap":"{:.2f}".format(record.cap), "data":"{:.2f}".format(record.data),
                                        "coverage":record.coverage,"distance":"{:.2f}".format(record.distance)
                                        , "lat":record.geo[0], "lng":record.geo[1], "time":calendar.timegm(record.time.timetuple()) * 1000})
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
    data = {}
    data["avg_cap"]=[]
    data["records"]=[]
    data["distance"]=[]
    total_records = len(Aggr_data.objects(time__gt = start, time__lt = end, site = site ))
    if total_records == 0:
        total_records=1
    step=50
    for x in range(step,251,step):
        data["records"].append( len( Aggr_data.objects(time__gt = start, time__lt = end,
                                   site = site , distance__lt = x, distance__gte = x-step) )*100/total_records )
        data["avg_cap"].append(float("{0:.2f}".format(Aggr_data.objects(time__gt = start, time__lt = end, site = site
                                   , distance__lt = x, distance__gte = x-step).average('cap'))))
        data["distance"].append(x)

    return data



@app.route('/histogram')
@login_required
def generate_histogram():

    toTimeStamp = datetime.datetime.utcfromtimestamp(int(flask.request.args.get('toTime'))/1000)
    fromTimeStamp = datetime.datetime.utcfromtimestamp(int(flask.request.args.get('fromTime'))/1000)
    site = flask.request.args.get('site')

    data = {}
    data["avg_cap"]=[]
    data["records"]=[]
    data["distance"]=[]

    total_records = len(Aggr_data.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site ))
    if total_records == 0:
        total_records=1
    step=50
    for x in range(step,251,step):
        data["records"].append( len( Aggr_data.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp,
                                     site = site , distance__lt = x, distance__gte = x-step) )*100/total_records )
        data["avg_cap"].append(float("{0:.2f}".format(Aggr_data.objects(time__gt = fromTimeStamp, time__lt = toTimeStamp, site = site
                                     , distance__lt = x, distance__gte = x-step).average('cap'))))
        data["distance"].append(x)

    data_dumps= Response(json.dumps(data),  mimetype='application/json')
    return data_dumps

@app.route('/path')
@login_required
def generate_path():

    toTime = datetime.datetime.utcfromtimestamp(int(flask.request.args.get('toTime'))/1000)
    fromTime = datetime.datetime.utcfromtimestamp(int(flask.request.args.get('fromTime'))/1000)
    site = flask.request.args.get('site')
    query_set = Aggr_data.objects(time__gt = fromTime, time__lt = toTime, site = site )
    # start = 0
    # skip = len(query_set)/MAX_POINTS
    data = {}
    data["cap"]=[]
    data["lat"]=[]
    data["lng"]=[]
    data["time"]=[]

    for ob in query_set:
        # if start == 0:
            data["cap"].append(float("{0:.2f}".format(ob.cap)))
            data["lat"].append(float("{0:.2f}".format(ob.geo[0])))
            data["lng"].append(float("{0:.2f}".format(ob.geo[1])))
            data["time"].append(calendar.timegm(ob.time.timetuple()) * 1000)
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

    query_set = Aggr_data.objects(time__gt = start, time__lt = end, site = site )
    # start = 0
    # skip = len(query_set)/MAX_POINTS
    data = {}
    data["cap"]=[]
    data["lat"]=[]
    data["lng"]=[]
    data["time"]=[]

    for ob in query_set:
        # if start == 0:
            data["cap"].append(float("{0:.2f}".format(ob.cap)))
            data["lat"].append(float("{0:.2f}".format(ob.geo[0])))
            data["lng"].append(float("{0:.2f}".format(ob.geo[1])))
            data["time"].append(calendar.timegm(ob.time.timetuple()) * 1000)

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