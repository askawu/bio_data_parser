import matplotlib.pyplot as plot
import re
import sys
import argparse
import numpy as np
import scipy
from biosppy.signals import ecg

from scipy import signal

TYPE_ECG=5
TYPE_PPG125=9
TYPE_PPG512=12

ECG_FS = 512
LOW_PASS_CUTOFF = 100
HIGH_PASS_CUTOFF = 0.5

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('raw_data_file', nargs=1, help='raw data file')
    p.add_argument('type', nargs=1, help='5: ECG, 9: PPG 125 Hz, 12: PPG 512 Hz)')
    p.print_help()
    return p.parse_args()

def convert_ppg_to_mv(v):
    if v >= 4194304:
        v = v - 8388608
    return (v * 3.2 * 1000) / 65536

def convert_ecg_to_mv(v):
    if v >= 4194304:
        v = v - 8388608
    return (v * 1000) / (6 * 2097152)

def is_ecg(t):
    if int(t) == TYPE_ECG:
        return True
    else:
        return False

def is_ppg(t):
    if int(t) == TYPE_PPG125 or int(t) == TYPE_PPG512:
        return True
    else:
        return False

def plot_freq_domain(ax, data, fs):
    #s, f = plot.mlab.magnitude_spectrum(x=data, Fs=fs)
    #ax.plot(f, 20. *  np.log10(s))
    win = len(data)
    half = win / 2
    amp = np.abs(np.fft.fft(data)) / float(win)
    amp = amp[:half]
    band = np.fft.fftfreq(win, 1/float(fs))
    band = band[:half]
    ax.plot(band, 20. * np.log10(amp))

def plot_60hz_filter(ax, fs):
    f0 = 65.0
    Q = 30.0
    w0 = f0 / (fs/2)
    b, a = signal.iirnotch(w0, Q)
    w, h = signal.freqz(b, a)

    freq = w*fs/(2*np.pi)
    ax.plot(freq, 20. * np.log10(np.abs(h)), color="c")

def plot_high_pass_filter(ax, fs, cutoff):
    nyq = fs / 2.0
    normalized_cutoff = cutoff / nyq
    b, a = signal.butter(3, normalized_cutoff, btype="highpass", analog=False)
    w, h = signal.freqz(b, a)
    freq = w * fs / (2.0 * np.pi)
    h = 20. * np.log10(np.abs(h))
    ax.plot(freq, h, color="y")

def plot_low_pass_filter(ax, fs, cutoff):
    nyq = fs / 2.0
    normalized_cutoff = cutoff / nyq
    b, a = signal.butter(3, normalized_cutoff, btype="lowpass", analog=False)
    w, h = signal.freqz(b, a)
    # w: radians/sample,  w = freq * 2pi / fs, fs: sample rate
    freq = w * fs / (2.0 * np.pi)
    h = 20. * np.log10(np.abs(h))
    ax.plot(freq, h, color="r")

def plot_time_domain(ax, data):
    ax.plot(data)
    ax.set_xlabel("Time")
    ax.set_ylabel("MV")

def filter_60hz(data, fs):
    f0 = 65.0
    Q = 30.0
    w0 = f0 / (fs/2)
    b, a = signal.iirnotch(w0, Q)
    return scipy.signal.filtfilt(b, a, data)

def high_pass_filter(data, fs, cutoff):
    nyq = fs / 2.0
    normalized_cutoff = cutoff / nyq
    b, a = signal.butter(3, normalized_cutoff, btype="highpass", analog=False)
    return scipy.signal.filtfilt(b, a, data)

def low_pass_filter(data, fs, cutoff):
    nyq = fs / 2.0
    normalized_cutoff = cutoff / nyq
    b, a = signal.butter(3, normalized_cutoff, btype="lowpass", analog=False)
    return scipy.signal.filtfilt(b, a, data)

data = []
args = parse_args()

f = open(args.raw_data_file[0])

if not (is_ecg(args.type[0]) or is_ppg(args.type[0])):
    print "Wrong type"
    sys.exit(1)

rule = re.compile("^%s," % args.type[0])

for l in f:
    if not rule.match(l):
        continue

    a = l.rstrip("\n").split(',')

    # extraction
    if is_ecg(args.type[0]):
        row = a[2:13]
    elif is_ppg(args.type[0]):
        row = a[2:13:2]

    for i in row:
        if is_ecg(args.type[0]):
            v = convert_ecg_to_mv(float(i))
        elif is_ppg(args.type[0]):
            v = convert_ppg_to_mv(float(i))
        data.append(v)

if is_ecg(args.type[0]):
    _, (ax1, ax2, ax3, ax4) = plot.subplots(4, 1)

    filtered = data
    filtered = filter_60hz(filtered, ECG_FS)
    filtered = high_pass_filter(filtered, ECG_FS, HIGH_PASS_CUTOFF)
    filtered = low_pass_filter(filtered, ECG_FS, LOW_PASS_CUTOFF)

    plot_time_domain(ax1, data)
    plot_freq_domain(ax2, data, ECG_FS)
    plot_60hz_filter(ax2, ECG_FS)
    plot_high_pass_filter(ax2, ECG_FS, HIGH_PASS_CUTOFF)
    plot_low_pass_filter(ax2, ECG_FS, LOW_PASS_CUTOFF)
    plot_time_domain(ax3, filtered)
    plot_freq_domain(ax4, filtered, ECG_FS)

elif is_ppg(args.type[0]):
    plot.plot(data)

plot.show()
