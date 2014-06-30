import datetime

from dateutil.tz import tzutc


def utcnow():
    return datetime.datetime.now(tzutc())


def as_utc(d):
    return d.replace(tzinfo=tzutc())
