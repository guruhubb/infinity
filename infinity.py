from requests_futures.sessions import FuturesSession
from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security, MongoEngineUserDatastore, UserMixin, RoleMixin
from flask_mail import Mail
from datetime import datetime
import getpass, logging, memcache, time, json, pymongo, flask_security
import mongoengine as dbmongo
# from dataController import dataLayer


TYPE = ('BTS', 'CPE', 'BEAGLE', 'ROUTER')
session = FuturesSession(max_workers=10)
dbpy = pymongo.MongoClient().infinity
headers = {'Content-Type': 'application/json'}

def bg_cb(sess, resp):
    # parse the json storing the result on the response object
    resp.data = resp.json()

# Create mongo database settings based on live, development, and local machine
rootUser = getpass.getuser()
if rootUser == 'live':  # Live Server
    db_settings = {"DB": "infinity", 'host': 'mongodb://live:27017/infinity', "tz_aware":True}
elif rootUser == 'stage':  # Development Server
    db_settings = {"DB": "infinity", 'host': 'mongodb://stage:27017/infinity', "tz_aware":True}
else:  # Local machine
    db_settings = {"DB": "infinity", "tz_aware":True}

VER = "0.1"

# Create application
app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = db_settings
app.config["SECRET_KEY"] = "KeepThisS3cr3t"
app.config['SECURITY_LOGIN_USER_TEMPLATE'] = 'login.html'
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_PASSWORD_SALT'] = '$2a$12$F6jRQYQK9xU4OQjt8gtCo.'
app.config['SECURITY_CHANGEABLE'] = True
app.config['SECURITY_CONFIRMABLE'] = False
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_REGISTERABLE'] = True
app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'infinitynms@gmail.com'
app.config['MAIL_PASSWORD'] = 'infinity1234'


# Create mail connection object
mail = Mail(app)

# Create database connection object
db = MongoEngine(app)


# Setup cache - not sure if we need this at all - we can go with varnish for UI page cache; no need for polling data from devices
class Cache(object):
    def __init__(self):
        self.dict = memcache.Client(['127.0.0.1:11211'], debug=1)
cache = Cache()

# Define security mongoengine documents

class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)

    def __unicode__(self):
        return self.name

class User(db.Document, UserMixin):
    name = db.StringField(max_length=64)
    email = db.StringField(max_length=255)
    password = db.StringField(max_length=255, default="infinity")
    active = db.BooleanField(default=True)
    confirmed_at = db.DateTimeField(default=datetime.now)
    # role = db.ReferenceField(Role)  #Flask Role Security will not work without ListField
    roles = db.ListField(db.ReferenceField(Role),default=[])

    def __unicode__(self):
        return self.name

    # meta = {
    #     'indexes': [
    #         {'fields': ['-confirmed_at'], 'unique': True,
    #           'sparse': True, 'types': False },
    #     ],
    # }

# Setup Flask-Security
userDatastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, userDatastore)

# Set up debug logger
file_handler = logging.FileHandler("/opt/log/infinity.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s ''[in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.DEBUG)  #change to ERROR in production?
app.logger.addHandler(file_handler)

# Use Flask to capture exception even in debug mode
def log_exception(sender, exception, **extra):
    sender.logger.debug('Got exception during processing: %s', exception)

from flask import got_request_exception
got_request_exception.connect(log_exception, app)

class Audit(db.Document):
    user = db.ReferenceField(User)
    timestamp = db.DateTimeField(default=datetime.now())
    description = db.StringField(max_length=255)

    def __unicode__(self):
        return self.name

def audit(modelClass):
    dbmongo.signals.post_save.connect(recordChanged, sender=modelClass)
    dbmongo.signals.post_delete.connect(recordDeleted, sender=modelClass)


def recordChanged(sender, document, **kwargs):
    ar = Audit()
    ar.user = User.objects.filter(pk=flask_security.current_user.id).first()
    # ar.date = tools.utc_now()
    if kwargs['created']:
        ar.description = "%s created." % str(document)
    else:
        ar.description = "%s modified." % str(document)
    ar.save()


def recordDeleted(sender, document, **kwargs):
    ar = Audit()
    ar.user = User.objects.filter(pk=flask_security.current_user.id).first()
    # ar.date = tools.utc_now()
    ar.description = "%s deleted." % str(document)
    ar.save()


class Company(db.Document):
    name = db.StringField(max_length=255)
    logo = db.ImageField()
    users = db.ListField(db.ReferenceField(User), default=[])

    def __unicode__(self):
        return self.name


class Tag(db.Document):
    name = db.StringField(max_length=32)

    def __unicode__(self):
        return self.name


# class Device(db.Document):
#     name = db.StringField(max_length=64, unique=True)
#     mac = db.StringField(max_length=32, unique = True)
#     url = db.StringField(unique = True)
#     type = db.StringField(max_length=10, choices=TYPE)
#     operator = db.ReferenceField(Company)
#     owner = db.ReferenceField(Company)
#     tags = db.ListField(db.ReferenceField('Tag'), default=['all'])
#     time = db.DateTimeField(default=datetime.now())
#     active = db.BooleanField(default=True)
#     geo = db.GeoPointField()
#
#     # geo = db.GeoPointField(default = (31.86,116.6))
#     site = db.StringField()                 # TODO may need to reference this at some point
#     connId = db.StringField()
#     # ssid = db.ReferenceField(Ssid)
#     # power = db.ReferenceField(Power)
#     # firmware = db.ReferenceField('Firmware')
#     # config = db.ReferenceField('Config')
#
#     meta = {'indexes': ['mac','operator','owner','tags','geo']}
#
#     def __unicode__(self):
#         return self.name
#
#
# class Data(db.Document):
#     mac = db.StringField()
#     connId = db.StringField()
#     time = db.IntField(default=int(time.time()))
#     geo = db.GeoPointField()
#     geo1 = db.GeoPointField()
#     freqA = db.IntField()
#     freqB = db.IntField()
#     snrA = db.FloatField()
#     snrB = db.FloatField()
#     tx = db.FloatField()
#     rx = db.FloatField()
#     cap = db.FloatField()
#     total_cap = db.FloatField()
#     distance = db.FloatField()
#     freqList = db.StringField()
#     ssidList = db.StringField()
#     process = db.BooleanField(default=False)
#     aggregate = db.BooleanField(default=False)
#
#     meta = {'indexes': ['geo', 'connId','mac','time','distance','process','aggregate']}
#
# #derived data from Data
# class Aggr_data(db.Document):
#     site = db.StringField()
#     time = db.IntField()
#     tx = db.FloatField()
#     rx = db.FloatField()
#     cap = db.FloatField()
#     data = db.FloatField()
#     coverage = db.BooleanField()
#     distance = db.FloatField()
#     geo = db.GeoPointField()
#
#     meta = {'indexes': ['site','time','distance']}
#
#     # meta = {'indexes': ['site','time','distance'],  'auto_create_index':False, 'force_insert':False}  #TODO check this
#
# #derived data from Aggr_Data
# class Minute(db.Document):
#     site = db.StringField()
#     time = db.IntField()
#     tx = db.FloatField()
#     rx = db.FloatField()
#     cap = db.FloatField()
#     data = db.FloatField()
#     coverage = db.BooleanField()
#     distance = db.FloatField()
#     geo = db.GeoPointField()
#
#     meta = {'indexes': ['site','time','distance']}
#
# class Hour(db.Document):
#     site = db.StringField()
#     time = db.IntField()
#     tx = db.FloatField()
#     rx = db.FloatField()
#     cap = db.FloatField()
#     data = db.FloatField()
#     coverage = db.BooleanField()
#     distance = db.FloatField()
#     geo = db.GeoPointField()
#
#     meta = {'indexes': ['site','time','distance']}
#
# class Day(db.Document):
#     site = db.StringField()
#     time = db.IntField()
#     tx = db.FloatField()
#     rx = db.FloatField()
#     cap = db.FloatField()
#     data = db.FloatField()
#     coverage = db.BooleanField()
#     distance = db.FloatField()
#     geo = db.GeoPointField()
#
#     meta = {'indexes': ['site','time','distance']}
#
# class Month(db.Document):
#     site = db.StringField()
#     time = db.IntField()
#     tx = db.FloatField()
#     rx = db.FloatField()
#     cap = db.FloatField()
#     data = db.FloatField()
#     coverage = db.BooleanField()
#     distance = db.FloatField()
#     geo = db.GeoPointField()
#
#     meta = {'indexes': ['site','time','distance']}


class Device(db.Document):
    name = db.StringField(max_length=64, unique=True)
    model = db.StringField(max_length=32)
    version = db.StringField(max_length=32)
    serial = db.StringField(max_length=32)
    # mac = db.StringField(max_length=32, unique = True)
    # url = db.StringField(unique = True)
    url = db.StringField(unique=True)

    type = db.StringField(max_length=10, choices=TYPE)
    operator = db.ReferenceField(Company)
    owner = db.ReferenceField(Company)
    tags = db.ListField(db.ReferenceField('Tag'))
    time = db.DateTimeField(default=datetime.now())
    active = db.BooleanField(default=True)
    # geo = db.GeoPointField(default =(33.783503, -118.198599))   #long beach
    lat = db.FloatField(default = 33.783503)
    lng = db.FloatField(default = -118.198599)
    # geo = db.GeoPointField(default = (31.86,116.6))
    site = db.StringField()                 # TODO may need to reference this at some point
    connId = db.StringField()
    # ssid = db.ReferenceField(Ssid)
    # power = db.ReferenceField(Power)
    # firmware = db.ReferenceField('Firmware')
    # config = db.ReferenceField('Config')

    meta = {'indexes': ['name','operator','owner','site','connId']}

    def __unicode__(self):
        return self.name

# Device.objects(name="BTS02").update(set__geo=[34.099139, -117.240400])
# Device.objects(name="BTS03").update(set__geo=[33.916995, -117.366742])
# Device.objects(name="BTS04").update(set__geo=[33.680001, -117.723440])
# Device.objects(name="BTS05").update(set__geo=[33.659000, -117.967886])

class Data(db.Document):
    Time = db.IntField(default=int(time.time()))
    SignalStrength = db.FloatField()
    TxRate = db.FloatField()
    RxRate = db.FloatField()
    Noise = db.FloatField()
    Chains_1_2 = db.StringField()
    Chains_3_4 = db.StringField()
    Tx_Power = db.FloatField()
    Tx_Phys_Rate = db.FloatField()
    Rx_Phys_Rate = db.FloatField()
    Rx_MCS = db.IntField()
    DeviceName = db.StringField()
    Location = db.GeoPointField()
    LinkName = db.StringField()
    MaxCapacity = db.FloatField()
    Data = db.FloatField()
    Coverage = db.BooleanField(default=True)
    # total_cap = db.FloatField()
    Distance = db.FloatField()
    # freqList = db.StringField()
    # ssidList = db.StringField()
    Tx0 = db.FloatField()
    Rx0 = db.FloatField()
    Noise0 = db.FloatField()
    Encoding0 = db.IntField()
    Tx1 = db.FloatField()
    Rx1 = db.FloatField()
    Noise1 = db.FloatField()
    Encoding1 = db.IntField()
    Tx2 = db.FloatField()
    Rx2 = db.FloatField()
    Noise2 = db.FloatField()
    Encoding2 = db.IntField()
    Tx3 = db.FloatField()
    Rx3 = db.FloatField()
    Noise3 = db.FloatField()
    Encoding3 = db.IntField()
    # Process = db.BooleanField(default=False)
    # Aggregate = db.BooleanField(default=False)
    meta = {'indexes': ['Location', 'LinkName','DeviceName','Time','Distance']}

#derived data from Data
class Aggr_data(db.Document):
    site = db.StringField()
    time = db.IntField()
    tx = db.FloatField()
    rx = db.FloatField()
    cap = db.FloatField()
    data = db.FloatField()
    coverage = db.BooleanField()
    distance = db.FloatField()
    geo = db.GeoPointField()

    meta = {'indexes': ['site','time','distance']}

    # meta = {'indexes': ['site','time','distance'],  'auto_create_index':False, 'force_insert':False}  #TODO check this

#derived data from Aggr_Data

#derived data from Aggr_Data
class Minute(db.Document):
    site = db.StringField()
    time = db.IntField()
    tx = db.FloatField()
    rx = db.FloatField()
    cap = db.FloatField()
    data = db.FloatField()
    coverage = db.BooleanField()
    distance = db.FloatField()
    geo = db.GeoPointField()

    meta = {'indexes': ['site','time','distance']}

class Hour(db.Document):
    site = db.StringField()
    time = db.IntField()
    tx = db.FloatField()
    rx = db.FloatField()
    cap = db.FloatField()
    data = db.FloatField()
    coverage = db.BooleanField()
    distance = db.FloatField()
    geo = db.GeoPointField()

    meta = {'indexes': ['site','time','distance']}

class Day(db.Document):
    site = db.StringField()
    time = db.IntField()
    tx = db.FloatField()
    rx = db.FloatField()
    cap = db.FloatField()
    data = db.FloatField()
    coverage = db.BooleanField()
    distance = db.FloatField()
    geo = db.GeoPointField()

    meta = {'indexes': ['site','time','distance']}

class Month(db.Document):
    site = db.StringField()
    time = db.IntField()
    tx = db.FloatField()
    rx = db.FloatField()
    cap = db.FloatField()
    data = db.FloatField()
    coverage = db.BooleanField()
    distance = db.FloatField()
    geo = db.GeoPointField()

    meta = {'indexes': ['site','time','distance']}

class Router(db.Document):
    url = db.StringField(unique = True)
    site = db.StringField()
    time = db.IntField()
    ping = db.IntField()
    # geo = db.GeoPointField()

    meta = {'indexes': ['site','time','ping']}

class Beagle(db.Document):
    url = db.StringField(unique = True)
    site = db.StringField()
    time = db.IntField()
    latency = db.FloatField()
    download = db.FloatField()
    upload = db.FloatField()
    # geo = db.GeoPointField()

    meta = {'indexes': ['site','time','latency','download','upload']}

# class Freq(db.Document):
#     channel = db.StringField()
#
#     def __unicode__(self):
#         return self.channel
#
# class Ssid(db.Document):
#     name = db.StringField()
#
#     def __unicode__(self):
#         return self.name
#
# class Power(db.Document):
#     power = db.StringField(default='2')
#
#     def __unicode__(self):
#         return self.power

class Site(db.Document):
    name = db.StringField(max_length=32)
    # ssidList = db.ListField(db.StringField())
    deviceList = db.ListField(db.StringField())
    active = db.BooleanField(default=True)
    tags = db.ListField(db.ReferenceField('Tag'))

    meta = {'indexes': ['name','deviceList']}

    def __unicode__(self):
        return self.name

class Site_data(db.Document):
    name = db.StringField()
    time = db.IntField()
    tx = db.FloatField()
    rx = db.FloatField()
    cap = db.FloatField()
    data = db.FloatField()
    type = db.StringField()
    geo = db.GeoPointField()
    distance = db.FloatField()

    meta = {'indexes': ['name','time','geo']}

    # meta = {'indexes': ['site','time','distance'],  'auto_create_index':False, 'force_insert':False}  #TODO check this

class Site_data_min(db.Document):
    name = db.StringField()
    time = db.IntField()
    tx = db.FloatField()
    rx = db.FloatField()
    cap = db.FloatField()
    data = db.FloatField()
    type = db.StringField()
    geo = db.GeoPointField()
    distance = db.FloatField()

    meta = {'indexes': ['name','time','geo']}

class Site_data_hour(db.Document):
    name = db.StringField()
    time = db.IntField()
    tx = db.FloatField()
    rx = db.FloatField()
    cap = db.FloatField()
    data = db.FloatField()
    type = db.StringField()
    geo = db.GeoPointField()
    distance = db.FloatField()

    meta = {'indexes': ['name','time','geo']}

class Site_data_day(db.Document):
    name = db.StringField()
    time = db.IntField()
    tx = db.FloatField()
    rx = db.FloatField()
    cap = db.FloatField()
    data = db.FloatField()
    type = db.StringField()
    geo = db.GeoPointField()

    meta = {'indexes': ['name','time','geo']}

class Site_data_month(db.Document):
    name = db.StringField()
    time = db.IntField()
    tx = db.FloatField()
    rx = db.FloatField()
    cap = db.FloatField()
    data = db.FloatField()
    type = db.StringField()
    geo = db.GeoPointField()
    distance = db.FloatField()

    meta = {'indexes': ['name','time','geo']}
    # meta = {'indexes': ['site','time','distance'],  'auto_create_index':False, 'force_insert':False}  #TODO check this
# class Config(db.Document):
#     name = db.StringField(max_length=64)
#     description = db.StringField(max_length=512)
#     time = db.DateTimeField(default=datetime.now)
#     ssid = db.ListField(db.StringField())
#     power = db.ListField(db.StringField())
#     freq = db.ListField(db.StringField())
#
#     def __unicode__(self):
#         return self.name


# class Firmware (db.Document):
#     name = db.StringField()
#     description = db.StringField()
#     timestamp = db.DateTimeField(default=datetime.now)
#     file = db.FileField()
#
#     def __unicode__(self):
#         return self.name
#
#
# class Job(db.Document):
#     tag = db.ReferenceField('Tag')
#     config = db.ReferenceField(Config)
#     firmware = db.ReferenceField(Firmware)
#     completed = db.BooleanField()
#     timestamp = db.DateTimeField(default=datetime.now)


class Event(db.Document):
    device = db.StringField()
    parameter = db.StringField()
    message = db.StringField()
    timestamp = db.IntField(default=int(time.time()))
    meta = {'indexes': ['device','parameter']}

audit(Tag)
audit(Device)
# audit(Config)
# audit(Firmware)
# audit(Job)
audit(Company)
# audit(Freq)
# audit(Power)
# audit(Ssid)
audit(Site)

# Register blueprints to route calls to other modules such as viewController and dataController
def register_blueprints(app):
    from viewController import viewController
    app.register_blueprint(viewController)
    from dataController import dataController
    app.register_blueprint(dataController)
register_blueprints(app)

# dataLayer()

