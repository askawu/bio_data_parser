import datetime
import time

def parse_annotation(f):
    annot = []
    for l in f:
        timespec, label = l.rstrip('\r\n').split(',')
        label = label.lstrip(' ')
        # E.g. 2018/01/25 14:05
        dt = datetime.datetime.strptime(timespec, "%Y/%m/%d %H:%M")
        secs = time.mktime(dt.timetuple())
        ms = secs * 1000
        annot.append((ms, label))
    return annot
