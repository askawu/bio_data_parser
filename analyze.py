import matplotlib.pyplot as plot
import os
import re
import sys
import argparse
import numpy as np

from parser import is_ecg, is_ppg, is_ppg512, is_ppg125, parse_data
from parser import TYPE_ECG, TYPE_PPG512
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
PPG_FS_125 = 63 # # we skip a half data point that is ambiance
PPG_FS_512 = 256 # we skip a half data point that is ambiance
LOW_PASS_CUTOFF = 35
HIGH_PASS_CUTOFF = 0.5

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('raw_data_file', nargs=1, help='Specify the raw data file')
    p.add_argument('annotation_file', nargs='?', help='Specify the annotation file')
    p.add_argument('start_data_point', nargs='?', help='Specify the start data point')
    p.add_argument('num_data_point', nargs='?', help='Specify the number of data point to be displayed')
    return p.parse_args()

args = parse_args()

f = open(args.raw_data_file[0])
ecg_data = parse_data(f, TYPE_ECG)

# back to begining
f.seek(0)
ppg_data = parse_data(f, TYPE_PPG512)

# Convert to numpy array
ecg_data = np.array(ecg_data)
ppg_data = np.array(ppg_data)

print ecg_data.shape
print ppg_data.shape

# Slice ECG data as specified
if args.start_data_point:
    start = int(args.start_data_point)
else:
    start = 0

if args.num_data_point:
    size = int(args.num_data_point)
else:
    size = len(ecg_data)

ecg_data = ecg_data[start:size]

# Slice PPG data as specified
if args.num_data_point:
    size = int(args.num_data_point)
else:
    size = len(ppg_data)

ppg_data = ppg_data[start:size]

# Read annotation file
annot = []
if args.annotation_file:
   annot_f = open(args.annotation_file)
   annot = parse_annotation(annot_f)

filtered_ecg_data = ecg_data[:,1]
filtered_ecg_data = high_pass_filter(filtered_ecg_data, ECG_FS, HIGH_PASS_CUTOFF)
filtered_ecg_data = low_pass_filter(filtered_ecg_data, ECG_FS, LOW_PASS_CUTOFF)
filtered_ecg_data = np.column_stack((ecg_data[:,0], filtered_ecg_data))

filtered_ppg_data = ppg_data[:,1]
filtered_ppg_data = high_pass_filter(filtered_ppg_data, PPG_FS_512, HIGH_PASS_CUTOFF)
filtered_ppg_data = low_pass_filter(filtered_ppg_data, PPG_FS_512, LOW_PASS_CUTOFF)
filtered_ppg_data = np.column_stack((ppg_data[:,0], filtered_ppg_data))

fig = plot.figure()
ax1 = fig.add_subplot(2, 1, 1)
ax2 = fig.add_subplot(2, 1, 2, sharex=ax1)
plot_time_domain(ax1, filtered_ppg_data, color='blue')
plot_time_domain(ax2, filtered_ecg_data, color='black')
plot_annotation(ax1, annot)
plot_annotation(ax2, annot)

plot.show()
