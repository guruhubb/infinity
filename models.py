from datetime import datetime
# from infinity import User
import mongoengine as db
# from infinity import audit





# class Tag(db.Document):
#     name = db.StringField(max_length=32)
#
#     def __unicode__(self):
#         return self.name
#
#
# class Device(db.Document):
#     name = db.StringField(max_length=64, unique=True)
#     mac = db.StringField(max_length=32, unique = True)
#     url = db.StringField(unique = True)
#     # connId = db.StringField()
#     # connected_to = db.ReferenceField("self")
#     operator = db.ReferenceField(Company)
#     owner = db.ReferenceField(Company)
#     tags = db.ListField(db.ReferenceField('Tag'), default=['all'])
#     timestamp = db.DateTimeField(default=datetime.now)
#     active = db.BooleanField(default=True)
#     geo = db.GeoPointField(default=(33.7,-118.19))
#     firmwareVersion = db.FloatField(default=0)
#     configVersion = db.FloatField(default=0)
#
#     meta = {'indexes': ['name','mac','operator','owner','tags','geo']}
#
#     def __unicode__(self):
#         return self.name
#
#
# class Data(db.Document):
#     mac = db.StringField()
#     connId = db.StringField()
#     time = db.DateTimeField(default=datetime.now)
#     geo = db.GeoPointField()
#     freqA = db.IntField()
#     freqB = db.IntField()
#     snr = db.FloatField()
#     tx = db.FloatField()
#     rx = db.FloatField()
#     cap = db.FloatField()
#     data = db.FloatField()
#     distance = db.FloatField()
#
#
#     meta = {'indexes': ['geo', 'connId']}
#
#
# class Config(db.Document):
#     name = db.StringField(max_length=64)
#     description = db.StringField(max_length=512)
#     timestamp = db.DateTimeField(default=datetime.now)
#     freqChA = db.IntField(default=5200)
#     freqChB = db.IntField(default=5800)
#     dataLimit = db.IntField(default=100)
#     power = db.IntField(default=24)
#
#     def __unicode__(self):
#         return self.name
#
#
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
#     tags = db.ListField(db.ReferenceField('Tag'), default=['all'])
#     config = db.ReferenceField(Config)
#     firmware = db.ReferenceField(Firmware)
#     completed = db.BooleanField()
#     timestamp = db.DateTimeField(default=datetime.now)
#
#
# class Event(db.Document):
#     device = db.ReferenceField(Device)
#     parameter = db.StringField()
#     message = db.StringField()
#     timestamp = db.DateTimeField(default=datetime.now)
#     meta = {'indexes': ['device','parameter']}
#
# audit(Tag)
# audit(Device)
# audit(Config)
# audit(Firmware)
# audit(Job)


