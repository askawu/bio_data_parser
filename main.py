import matplotlib.pyplot as plot
import os
import re
import sys
import argparse
import numpy as np

from parser import is_acc, is_ecg, is_ppg, is_ppg512, is_ppg125, parse_data
from annotation import parse_annotation
from filters import power_line_noise_filter
from filters import high_pass_filter
from filters import low_pass_filter
from plots import plot_time_domain
from plots import plot_freq_domain
from plots import plot_power_line_noise_filter
from plots import plot_high_pass_filter
from plots import plot_low_pass_filter
from plots import plot_annotation

ECG_FS = 512
PPG_FS_125 = 63 # we skip a half data point which is ambiance
PPG_FS_512 = 256 # we skip a half data point which is ambiance

#PPG_FS_125 = 125 # we skip a half data point which is ambiance
#PPG_FS_512 = 512 # we skip a half data point which is ambiance
LOW_PASS_CUTOFF = 35
HIGH_PASS_CUTOFF = 0.5

FILTERED_PPG = False

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--export_csv', help='Export to csv file', action='store_true')
    p.add_argument('--spectrum', help='Plot spectrum', action='store_true')
    p.add_argument('raw_data_file', nargs=1, help='Specify the raw data file')
    p.add_argument('annotation_file', nargs='?', help='Specify the annotation file')
    p.add_argument('type', nargs=1, help='5: ECG, 9: PPG 125 Hz, 12: PPG 512 Hz)')
    return p.parse_args()

args = parse_args()
signal_type = int(args.type[0])

if not (is_acc(signal_type) or is_ecg(signal_type) or is_ppg(signal_type)):
    print "Wrong type"
    sys.exit(1)

f = open(args.raw_data_file[0])
data = parse_data(f, signal_type)
# Convert to numpy array
data = np.array(data)

annot = []
if args.annotation_file:
   annot_f = open(args.annotation_file)
   annot = parse_annotation(annot_f)

fs = 0
if is_ecg(signal_type):
    fs = ECG_FS
elif is_ppg125(signal_type):
    fs = PPG_FS_125
else:
    fs = PPG_FS_512

if is_ecg(signal_type):
    filtered = data[:,1]
    # Depends, comment it to favor process speed
    # filtered = power_line_noise_filter(filtered, ECG_FS)
    filtered = high_pass_filter(filtered, fs, HIGH_PASS_CUTOFF)
    filtered = low_pass_filter(filtered, fs, LOW_PASS_CUTOFF)
    filtered = np.column_stack((data[:,0], filtered))
elif is_ppg(signal_type):
    if FILTERED_PPG:
        filtered = data[:,1]
        # Depends, comment it to favor process speed
        #filtered = power_line_noise_filter(filtered, ECG_FS)
        filtered = high_pass_filter(filtered, fs, HIGH_PASS_CUTOFF)
        filtered = low_pass_filter(filtered, fs, LOW_PASS_CUTOFF)
        filtered = np.column_stack((data[:,0], filtered))
    else:
        filtered = data
else:
    filtered = data

if args.export_csv:
    basename = os.path.basename(args.raw_data_file[0])
    if is_ecg(signal_type):
        csvname = os.path.splitext(basename)[0] + "_ecg.csv"
    elif is_ppg125(signal_type):
        csvname = os.path.splitext(basename)[0] + "_ppg125.csv"
    elif is_ppg512(signal_type):
        csvname = os.path.splitext(basename)[0] + "_ppg512.csv"
    elif is_acc(signal_type):
        csvname = os.path.splitext(basename)[0] + "_acc.csv"
    np.savetxt(csvname, filtered, delimiter=",")

if is_acc(signal_type):
    tmp = []
    for i in filtered:
        mag = (i[1] ** 2) + (i[2] ** 2) + (i[3] ** 2)
        tmp.append([i[0], mag])
    filtered = np.array(tmp)
    filtered = filtered[filtered[:,0].argsort()]

if args.spectrum:
    _, (ax1, ax2) = plot.subplots(2, 1)
    plot_time_domain(ax1, filtered)
    plot_freq_domain(ax2, filtered[:,1], fs)
    plot_annotation(ax1, annot)
else:
    _, ax1 = plot.subplots(1, 1)
    plot_time_domain(ax1, filtered)
    plot_annotation(ax1, annot)

plot.show()
