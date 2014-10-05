from datetime import datetime
from infinity import User
import flask_security
import mongoengine as db



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
    connId = db.StringField()
    # connected_to = db.ReferenceField("self")
    operator = db.ReferenceField(Company)
    owner = db.ReferenceField(Company)
    tags = db.ListField(db.ReferenceField('Tag'), default=['all'])
    timestamp = db.DateTimeField(default=datetime.now)
    active = db.BooleanField(default=True)
    geo = db.GeoPointField(default='33.7,-118.19')
    firmwareVersion = db.FloatField(default=0)
    configVersion = db.FloatField(default=0)

    meta = {'indexes': ['name','mac','operator','owner','tags','geo']}

    def __unicode__(self):
        return self.name


class DeviceData(db.Document):
    mac = db.ReferenceField(Device)
    connId = db.ReferenceField(Device)
    time = db.DateTimeField(default=datetime.now)
    geo = db.GeoPointField()
    freqA = db.IntField()
    freqB = db.IntField()
    snr = db.FloatField()
    tx = db.FloatField()
    rx = db.FloatField()
    data = db.FloatField()
    cap = db.FloatField()
    distance = db.FloatField()


    meta = {'indexes': ['geo', 'connId']}


class ConfigPackage(db.Document):
    name = db.StringField(max_length=64)
    description = db.StringField(max_length=512)
    timestamp = db.DateTimeField(default=datetime.now)
    freqChA = db.IntField(default=5200)
    freqChB = db.IntField(default=5800)
    dataLimit = db.IntField(default=100)
    power = db.IntField(default=24)

    def __unicode__(self):
        return self.name


class FirmwarePackage (db.Document):
    name = db.StringField()
    description = db.StringField()
    timestamp = db.DateTimeField(default=datetime.now)
    file = db.FileField()

    def __unicode__(self):
        return self.name


class JobSchedule(db.Document):
    tags = db.ListField(db.ReferenceField('Tag'), default=['all'])
    config = db.ReferenceField(ConfigPackage)
    firmware = db.ReferenceField(FirmwarePackage)
    completed = db.BooleanField()
    timestamp = db.DateTimeField(default=datetime.now)


class EventRecord(db.Document):
    device = db.ReferenceField(Device)
    parameter = db.StringField()
    message = db.StringField()
    timestamp = db.DateTimeField(default=datetime.now)
    meta = {'indexes': ['device','parameter']}


class AuditRecord(db.Document):
    user = db.ReferenceField(User)
    timestamp = db.DateTimeField(default=datetime.now)
    description = db.StringField(max_length=255)

    def __unicode__(self):
        return self.name



def audit(modelClass):
    db.signals.post_save.connect(recordChanged, sender=modelClass)
    db.signals.post_delete.connect(recordDeleted, sender=modelClass)


def recordChanged(sender, document, **kwargs):
    ar = AuditRecord()
    ar.user = User.objects.filter(pk=flask_security.current_user.id).first()
    # ar.date = tools.utc_now()
    if kwargs['created']:
        ar.description = "%s created." % str(document)
    else:
        ar.description = "%s modified." % str(document)
    ar.save()


def recordDeleted(sender, document, **kwargs):
    ar = AuditRecord()
    ar.user = User.objects.filter(pk=flask_security.current_user.id).first()
    # ar.date = tools.utc_now()
    ar.description = "%s deleted." % str(document)
    ar.save()

audit(Company)
audit(Tag)
audit(Device)
audit(ConfigPackage)
audit(FirmwarePackage)
audit(JobSchedule)



