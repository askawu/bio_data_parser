import matplotlib.pyplot as plot
import os
import re
import sys
import argparse
import numpy as np

from parser import is_ecg, is_ppg, parse_data
from filters import power_line_noise_filter
from filters import high_pass_filter
from filters import low_pass_filter
from plots import plot_time_domain
from plots import plot_freq_domain
from plots import plot_power_line_noise_filter
from plots import plot_high_pass_filter
from plots import plot_low_pass_filter

ECG_FS = 512
LOW_PASS_CUTOFF = 35
HIGH_PASS_CUTOFF = 0.5

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--export_csv', help='export to csv file', action='store_true')
    p.add_argument('raw_data_file', nargs=1, help='raw data file')
    p.add_argument('type', nargs=1, help='5: ECG, 9: PPG 125 Hz, 12: PPG 512 Hz)')
    return p.parse_args()

args = parse_args()
signal_type = int(args.type[0])

if not (is_ecg(signal_type) or is_ppg(signal_type)):
    print "Wrong type"
    sys.exit(1)

f = open(args.raw_data_file[0])
data = parse_data(f, signal_type)
# Convert to numpy array
data = np.array(data)

if is_ecg(signal_type):
    filtered = data[:,1]
    filtered = power_line_noise_filter(filtered, ECG_FS)
    filtered = high_pass_filter(filtered, ECG_FS, HIGH_PASS_CUTOFF)
    filtered = low_pass_filter(filtered, ECG_FS, LOW_PASS_CUTOFF)
    filtered = np.column_stack((data[:,0], filtered))

    _, (ax1, ax2, ax3, ax4) = plot.subplots(4, 1)
    plot_time_domain(ax1, data)
    plot_freq_domain(ax2, data[:,1], ECG_FS)
    plot_power_line_noise_filter(ax2, ECG_FS)
    plot_high_pass_filter(ax2, ECG_FS, HIGH_PASS_CUTOFF)
    plot_low_pass_filter(ax2, ECG_FS, LOW_PASS_CUTOFF)
    plot_time_domain(ax3, filtered)
    plot_freq_domain(ax4, filtered[:,1], ECG_FS)

    if args.export_csv:
        basename = os.path.basename(args.raw_data_file[0])
        csvname = os.path.splitext(basename)[0] + "_ecg.csv"
        np.savetxt(csvname, filtered, delimiter=",")

elif is_ppg(signal_type):
    _, ax1 = plot.subplots(1, 1)
    ax1.set_yscale('log')
    plot_time_domain(ax1, data)

    if args.export_csv:
        basename = os.path.basename(args.raw_data_file[0])
        if is_ppg125(args.type[0]):
            csvname = os.path.splitext(basename)[0] + "_ppg125.csv"
        else:
            csvname = os.path.splitext(basename)[0] + "_ppg512.csv"
        np.savetxt(csvname, data, delimiter=",")

plot.show()
