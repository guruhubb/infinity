from requests_futures.sessions import FuturesSession
from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security, MongoEngineUserDatastore, UserMixin, RoleMixin
from flask_mail import Mail
from datetime import datetime
import getpass, logging, memcache, time, json, pymongo, flask_security
import mongoengine as dbmongo

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
    timestamp = db.DateTimeField(default=datetime.now)
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


class Device(db.Document):
    name = db.StringField(max_length=64, unique=True)
    mac = db.StringField(max_length=32, unique = True)
    url = db.StringField(unique = True)
    # connId = db.StringField()
    # connected_to = db.ReferenceField("self")
    operator = db.ReferenceField(Company)
    owner = db.ReferenceField(Company)
    tags = db.ListField(db.ReferenceField('Tag'), default=['all'])
    timestamp = db.DateTimeField(default=datetime.now)
    active = db.BooleanField(default=True)
    geo = db.GeoPointField(default=(33.7,-118.19))
    firmwareVersion = db.FloatField(default=0)
    configVersion = db.FloatField(default=0)

    meta = {'indexes': ['name','mac','operator','owner','tags','geo']}

    def __unicode__(self):
        return self.name


class Data(db.Document):
    mac = db.StringField()
    connId = db.StringField()
    time = db.DateTimeField(default=datetime.now)
    geo = db.GeoPointField()
    freqA = db.IntField()
    freqB = db.IntField()
    snr = db.FloatField()
    tx = db.FloatField()
    rx = db.FloatField()
    cap = db.FloatField()
    data = db.FloatField()
    distance = db.FloatField()


    meta = {'indexes': ['geo', 'connId']}


class Config(db.Document):
    name = db.StringField(max_length=64)
    description = db.StringField(max_length=512)
    timestamp = db.DateTimeField(default=datetime.now)
    freqChA = db.IntField(default=5200)
    freqChB = db.IntField(default=5800)
    dataLimit = db.IntField(default=100)
    power = db.IntField(default=24)

    def __unicode__(self):
        return self.name


class Firmware (db.Document):
    name = db.StringField()
    description = db.StringField()
    timestamp = db.DateTimeField(default=datetime.now)
    file = db.FileField()

    def __unicode__(self):
        return self.name


class Job(db.Document):
    tags = db.ListField(db.ReferenceField('Tag'), default=['all'])
    config = db.ReferenceField(Config)
    firmware = db.ReferenceField(Firmware)
    completed = db.BooleanField()
    timestamp = db.DateTimeField(default=datetime.now)


class Event(db.Document):
    device = db.ReferenceField(Device)
    parameter = db.StringField()
    message = db.StringField()
    timestamp = db.DateTimeField(default=datetime.now)
    meta = {'indexes': ['device','parameter']}

audit(Tag)
audit(Device)
audit(Config)
audit(Firmware)
audit(Job)
audit(Company)


# Register blueprints to route calls to other modules such as viewController
def register_blueprints(app):
    from viewController import viewController
    app.register_blueprint(viewController)

register_blueprints(app)


def startData():
    try:
        # while True:
            getData()
            time.sleep(1)
    except Exception, msg:
            app.logger.error('error message is: %s, ' % msg)


def getData():
    urlList = []
    macList = []
    timeList = []
    totaldocuments = []
    msg = ""

    for object in Device.objects(active = True):
        urlList.append(object.url)
        macList.append(object.mac)
        timeStamp = Data.objects(mac = object.mac).order_by('-time').only ('time').first()
        # timeStamp = timeStamp.time.strftime("%Y-%m-%d %H:%M:%S.%f")

        if timeStamp:
            timeStamp = datetime.strptime(timeStamp.time, '%Y-%m-%dT%H:%M:%S.%f')
            timeStamp = timeStamp.strftime('%Y-%m-%d %H:%M:%S.%f')
            timeList.append(timeStamp)
        else:
            timeList.append(str(datetime.now()-datetime.timedelta(hours=1)))

    for url, time in zip(urlList,timeList):
        filters = [dict(name='time', op='gt', val=time)]
        params = dict(q=json.dumps(dict(filters=filters)))
        try:
            response = session.get(url,params=params, headers=headers,timeout=5,background_callback=bg_cb).result()
            documents=[]
            for obj in response.data["objects"]:
                mac = obj["mac"]
                connId = obj["connId"]
                time = obj["time"]
                lat = obj["lat"]
                long = obj["long"]
                freqA = obj["freqA"]
                freqB = obj["freqB"]
                snr = obj["snr"]
                tx = obj["tx"]
                rx = obj["rx"]
                cap = obj["cap"]
                documents.append({"mac":mac,"connId":connId,"time":time, "geo":(lat,long),"freqA":freqA,
                                  "freqB":freqB,"snr":snr, "tx":tx,"rx":rx,"cap":cap})
            if documents:
                totaldocuments.append(documents)
                dbpy.data.insert(documents) # Bulk Insert using pymongo - mongoengine cannot do it
                # BE CAREFUL! pymongo client accesses database with actual name of collection, and not class name

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

# startData()