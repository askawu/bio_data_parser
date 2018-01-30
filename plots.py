import matplotlib.pyplot as plot
import numpy as np
from scipy import signal

PNG_W_INCH = 18
PNG_H_INCH = 8

MV_LOW_BOUND = -1.5
MV_HIGH_BOUND = 1.5
MV_STEP = 0.5

MS_STEP = 200

def plot_freq_domain(ax, data, fs, color='b'):
    win = len(data)
    half = win / 2
    amp = np.abs(np.fft.fft(data)) / float(win)
    amp = amp[:half]
    band = np.fft.fftfreq(win, 1/float(fs))
    band = band[:half]
    ax.plot(band, 20. * np.log10(amp), color)

def plot_filter(ax, fs, w, h, color=None):
    """
    ax: The matplotlib plot axis
    w: The normalized frequencies (radians/sample)
    h: The frequency response (complex)
    """
    # radians/sample => fs
    freq = w * fs / (2.0 * np.pi)
    mag_db = 20. * np.log10(np.abs(h))
    ax.plot(freq, mag_db, color=color)

def plot_power_line_noise_filter(ax, fs):
    f0 = 65.0
    Q = 30.0
    w0 = f0 / (fs/2)
    b, a = signal.iirnotch(w0, Q)
    w, h = signal.freqz(b, a)
    plot_filter(ax, fs, w, h, color='c')

def plot_high_pass_filter(ax, fs, cutoff):
    nyq = fs / 2.0
    normalized_cutoff = cutoff / nyq
    b, a = signal.butter(3, normalized_cutoff, btype="highpass", analog=False)
    w, h = signal.freqz(b, a)
    plot_filter(ax, fs, w, h, color='y')

def plot_low_pass_filter(ax, fs, cutoff):
    nyq = fs / 2.0
    normalized_cutoff = cutoff / nyq
    b, a = signal.butter(3, normalized_cutoff, btype="lowpass", analog=False)
    w, h = signal.freqz(b, a)
    plot_filter(ax, fs, w, h, color='r')

def plot_time_domain(ax, data, color='b'):
    ax.plot(data[:,0], data[:,1], color)
    ax.set_xlabel("Epoch Time (ms)")
    ax.set_ylabel("MV")

def plot_ecg(data):
    figsize = plot.rcParams['figure.figsize']
    figsize[0] = PNG_W_INCH
    figsize[1] = PNG_H_INCH
    plot.rcParams['figure.figsize'] = figsize

    num_seg = 4
    s = np.array_split(data, num_seg)
    _, axes = plot.subplots(num_seg, 1)

    for i in range(0, num_seg):
        start_ts = s[i][0][0]
        end_ts = s[i][-1][0]
        # vertical lines every 0.2s
        vl = np.arange(start_ts, end_ts, MS_STEP)
        # horizontal lines every 0.5 mV
        hl = np.arange(MV_LOW_BOUND, MV_HIGH_BOUND, MV_STEP)

        axes[i].set_xlim(start_ts, end_ts)
        axes[i].set_ylim(MV_LOW_BOUND, MV_HIGH_BOUND)
        # disable autoscale since it will be difficult to compare, e.g., RR interval.
        axes[i].autoscale(False)
        axes[i].vlines(vl, MV_LOW_BOUND, MV_HIGH_BOUND, color='r', alpha=0.2)
        axes[i].hlines(hl, start_ts, end_ts, color='r', alpha=0.2)
        plot_time_domain(axes[i], s[i])

    # adjust layout
    plot.tight_layout(pad=0.3, h_pad = 0.2)

def plot_to_png(png_name):
    plot.savefig(png_name)

def plot_annotation(ax, data):
    # randomize the color of vertical lines
    cmap = plot.cm.get_cmap('hsv', len(data))
    for i in range(0, len(data)):
        ms = data[i][0]
        label = data[i][1]
        ax.axvline(ms, label=label, color=cmap(i), ls='dashed')
    # make label work
    ax.legend()
