import scipy
import numpy as np
from scipy import signal

ACC_FS = 20
ECG_FS = 512
PPG_FS_125 = 63 # we skip a half data point which is ambiance
PPG_FS_512 = 256 # we skip a half data point which is ambiance

LOW_PASS_CUTOFF = 35
HIGH_PASS_CUTOFF = 0.5

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

def ppg512_pl_filter(x):
    """ A map function to perform power line noise filter against ppg512 data
    Input: numpy array
    Output: numpy array
    """
    filtered = x[:,1]
    filtered = power_line_noise_filter(filtered, PPG_FS_512)
    filtered = np.column_stack((x[:,0], filtered))
    return filtered

def ppg512_hp_filter(x):
    """ A map function to perform high pass filter against ppg512 data
    Input: numpy array
    Output: numpy array
    """
    filtered = x[:,1]
    filtered = high_pass_filter(filtered, PPG_FS_512, HIGH_PASS_CUTOFF)
    filtered = np.column_stack((x[:,0], filtered))
    return filtered

def ppg512_lp_filter(x):
    """ A map function to perform low pass filter against ppg512 data
    Input: numpy array
    Output: numpy array
    """
    filtered = x[:,1]
    filtered = low_pass_filter(filtered, PPG_FS_512, LOW_PASS_CUTOFF)
    filtered = np.column_stack((x[:,0], filtered))
    return filtered

def ecg_pl_filter(x):
    """ A map function to perform power line noise filter against ecg data
    Input: numpy array
    Output: numpy array
    """
    filtered = x[:,1]
    filtered = power_line_noise_filter(filtered, ECG_FS)
    filtered = np.column_stack((x[:,0], filtered))
    return filtered

def ecg_hp_filter(x):
    """ A map function to perform high pass filter against ecg data
    Input: numpy array
    Output: numpy array
    """
    filtered = x[:,1]
    filtered = high_pass_filter(filtered, PPG_FS_512, HIGH_PASS_CUTOFF)
    filtered = np.column_stack((x[:,0], filtered))
    return filtered

def ecg_lp_filter(x):
    """ A map function to perform low pass filter against ecg data
    Input: numpy array
    Output: numpy array
    """
    filtered = x[:,1]
    filtered = low_pass_filter(filtered, PPG_FS_512, LOW_PASS_CUTOFF)
    filtered = np.column_stack((x[:,0], filtered))
    return filtered

def acc_mag_filter(x):
    filtered = x[:,1]
    print filtered
    return x

def acc_flat(x):
    """ A map function to simply the acc data format
    Input: list, e.g. [(timestamp, (x, y, z))]
    Output: list, e.g. [[timestamp, x, y, z]]
    """
    y = []
    for i in x:
        y.append([i[0], i[1][0], i[1][1], i[1][2]])
    return y
