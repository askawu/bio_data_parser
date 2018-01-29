import scipy
from scipy import signal

def power_line_noise_filter(data, fs):
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


