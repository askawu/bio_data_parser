import matplotlib.pyplot as plot
import numpy as np
from scipy import signal

PNG_W_INCH = 18
PNG_H_INCH = 8

def plot_freq_domain(ax, data, fs):
    win = len(data)
    half = win / 2
    amp = np.abs(np.fft.fft(data)) / float(win)
    amp = amp[:half]
    band = np.fft.fftfreq(win, 1/float(fs))
    band = band[:half]
    ax.plot(band, 20. * np.log10(amp))

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

def plot_time_domain(ax, data):
    ax.plot(data[:,0], data[:,1])
    ax.set_xlabel("Epoch Time (ms)")
    ax.set_ylabel("MV")

def ecg_to_png(data, png_name):
    figsize = plot.rcParams['figure.figsize']
    figsize[0] = PNG_W_INCH
    figsize[1] = PNG_H_INCH
    plot.rcParams['figure.figsize'] = figsize

    s = np.array_split(data, 4)
    _, (ax1, ax2, ax3, ax4) = plot.subplots(4, 1)
    ax1.set_xlim(s[0][0][0], s[0][-1][0])
    ax2.set_xlim(s[1][0][0], s[1][-1][0])
    ax3.set_xlim(s[2][0][0], s[2][-1][0])
    ax4.set_xlim(s[3][0][0], s[3][-1][0])
    ax1.set_ylim(-0.3, 1.2)
    ax2.set_ylim(-0.3, 1.2)
    ax3.set_ylim(-0.3, 1.2)
    ax4.set_ylim(-0.3, 1.2)
    ax1.autoscale(False)
    ax2.autoscale(False)
    ax3.autoscale(False)
    ax4.autoscale(False)
    plot_time_domain(ax1, s[0])
    plot_time_domain(ax2, s[1])
    plot_time_domain(ax3, s[2])
    plot_time_domain(ax4, s[3])
    plot.savefig(png_name)
