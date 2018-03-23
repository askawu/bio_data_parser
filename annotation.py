import datetime
import time

annotation_data = []

def parse_annotation(x):
    timespec, label = x.rstrip('\r\n').split(',')
    label = label.lstrip(' ')
    # E.g. 2018/01/25 14:05:00
    dt = datetime.datetime.strptime(timespec, "%Y/%m/%d %H:%M:%S")
    secs = time.mktime(dt.timetuple())
    ms = secs * 1000
    annotation_data.append((ms, label))
