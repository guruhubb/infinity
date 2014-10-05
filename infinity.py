from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security, MongoEngineUserDatastore, UserMixin, RoleMixin
from flask_mail import Mail
import getpass, logging, memcache, datetime

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

# Set up debug logger
file_handler = logging.FileHandler("/opt/log/infinity.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s ''[in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)

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
    confirmed_at = db.DateTimeField(default=datetime.datetime.now)
    # role = db.ReferenceField(Role)  #Flask Role Security will not work without ListField
    roles = db.ListField(db.ReferenceField(Role),default=[])

    def __unicode__(self):
        return self.name

# Setup Flask-Security
userDatastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, userDatastore)


# Use Flask to capture exception even in debug mode
def log_exception(sender, exception, **extra):
    sender.logger.debug('Got exception during processing: %s', exception)

from flask import got_request_exception
got_request_exception.connect(log_exception, app)


#Register blueprints to route calls to other modules such as viewController
def register_blueprints(app):
    from viewController import viewController
    app.register_blueprint(viewController)

register_blueprints(app)


