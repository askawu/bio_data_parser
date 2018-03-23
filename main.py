
import os
import argparse
import rx
import numpy as np
import time
import matplotlib.pyplot as plot
from rx import Observable
from parser import calc_ts
from parser import parse_raw_acc, acc_data
from parser import parse_raw_ecg, ecg_data
from parser import parse_raw_ppg, ppg_data
from filters import ppg512_hp_filter, ppg512_lp_filter, ppg512_pl_filter
from filters import ecg_hp_filter, ecg_lp_filter, ecg_pl_filter
from filters import acc_flat
from filters import ACC_FS, ECG_FS, PPG_FS_512
from plots import plot_time_domain, plot_freq_domain, plot_annotation
from annotation import parse_annotation, annotation_data

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--export_csv', help='Export to csv file', action='store_true')
    p.add_argument('raw_data_file', nargs=1, help='Specify the raw data file')
    p.add_argument('annotation_file', nargs='?', help='Specify the annotation file')
    p.add_argument('type', nargs=1, help='5: ECG, 9: PPG 125 Hz, 12: PPG 512 Hz)')
    return vars(p.parse_args())

def validate_args():
    t = int(args["type"][0])
    if t != 0 and t != 5 and t != 9 and t != 12:
        raise Exception("Unknown type")

def group_key_generator(x):
    return x.split(',')[0]

def group_by_handler(x):
    if x.key == '0':
        x.subscribe(on_next=parse_raw_acc, on_completed=acc_data_handler)
    elif x.key == '5':
        x.subscribe(on_next=parse_raw_ecg, on_completed=ecg_data_handler)
    elif x.key == '12':
        x.subscribe(on_next=parse_raw_ppg, on_completed=ppg_data_handler)

def acc_data_handler():
    print "acc data handler!!!"
    def output(x):
        if args["export_csv"]:
            np.savetxt(args["acc_csv"], x, delimiter=',')
        if int(args["type"][0]) == 0:
            s = np.square(x[:,1:])
            mag = np.sum(s, axis=1)
            mag = np.column_stack((x[:,0], mag))
            plot_time_domain(ax1, mag)
            plot_freq_domain(ax2, mag[:,1], ACC_FS)

    # pipeline
    Observable.just(acc_data)             \
              .map(calc_ts)               \
              .map(acc_flat)              \
              .map(lambda x: np.array(x)) \
              .subscribe(output)

def ecg_data_handler():
    print "ecg data handler!!!"
    def output(x):
        if args["export_csv"]:
            np.savetxt(args["ecg_csv"], x, delimiter=',')
        if int(args["type"][0]) == 5:
            plot_time_domain(ax1, x)
            plot_freq_domain(ax2, x[:,1], ECG_FS)

    # pipeline
    Observable.just(ecg_data)             \
              .map(calc_ts)               \
              .map(lambda x: np.array(x)) \
              .map(ecg_pl_filter) \
              .map(ecg_hp_filter) \
              .map(ecg_lp_filter) \
              .subscribe(output)

def ppg_data_handler():
    print "ppg data handler!!!"
    def output(x):
        if args["export_csv"]:
            np.savetxt(args["ppg_csv"], x, delimiter=',')
        if int(args["type"][0]) == 12:
            plot_time_domain(ax1, x)
            plot_freq_domain(ax2, x[:,1], PPG_FS_512)

    # pipeline
    Observable.just(ppg_data)             \
              .map(calc_ts)               \
              .map(lambda x: np.array(x)) \
              .map(ppg512_hp_filter) \
              .map(ppg512_lp_filter) \
              .subscribe(output)

def annotation_handler():
    print "annotation handler !!!"
    plot_annotation(ax1, annotation_data)

def verbose(x):
    print x

######################################################################

_, (ax1, ax2) = plot.subplots(2, 1)

# parse arguments
args = parse_args()

print args

validate_args()

# prepare something for later use
basename = os.path.basename(args["raw_data_file"][0])
args["acc_csv"] = os.path.splitext(basename)[0] + "_acc.csv"
args["ecg_csv"] = os.path.splitext(basename)[0] + "_ecg.csv"
args["ppg_csv"] = os.path.splitext(basename)[0] + "_ppg.csv"

# Ideally, observables can be executed in different threads.
# However, it's difficult becuase matplotlib can only be executed in
# the main thread and pyplot.show() only can be executed once.
# So, we only take advantage of reactivex to build the data pipeline by
# observable::map().

if args["annotation_file"]:
    a = open(args["annotation_file"])
    alines = a.read().split('\n')
    Observable.from_(alines)                            \
              .filter(lambda x: True if x else False)   \
              .subscribe(on_next=parse_annotation, on_completed=annotation_handler)

f = open(args["raw_data_file"][0])
lines = f.read().split('\n')
Observable.from_(lines)                  \
          .group_by(group_key_generator) \
          .subscribe(group_by_handler)

plot.show()
