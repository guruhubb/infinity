from json import JSONEncoder
from bson import ObjectId
import pytz
import datetime
from infinity import app


#helper methods - mongoencoder, utc time, timeit
def timeit(method):

    def timed(*args, **kw):
        ts = datetime.datetime.now()
        result = method(*args, **kw)
        te = datetime.datetime.now()

        app.logger.debug('Timer got: %s for %r (%r, %r)' % (te-ts, method.__name__, args, kw))
        return result

    return timed


class MongoEncoder(JSONEncoder):

    def default(self, obj):

        if isinstance(obj, ObjectId):
            return str(obj)

        op = getattr(obj, "to_mongo", None)
        if callable(op):
            return obj.to_mongo()
        else:
            return JSONEncoder.default(self, obj)


def utc_now():
    u = datetime.utcnow()
    u = u.replace(tzinfo=pytz.utc)
    return u
