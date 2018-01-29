#!/usr/bin/env python
import re

TYPE_ECG=5
TYPE_PPG125=9
TYPE_PPG512=12
MSEC_PER_SEC = 1000

def convert_ppg_to_mv(v):
    if v >= 4194304:
        v = v - 8388608
    return (v * 3.2 * 1000) / 65536

def convert_ecg_to_mv(v):
    if v >= 4194304:
        v = v - 8388608
    return (v * 1000) / (6 * 2097152)

def is_ecg(t):
    if t == TYPE_ECG:
        return True
    else:
        return False

def is_ppg125(t):
    if t == TYPE_PPG125:
        return True
    else:
        return False

def is_ppg512(t):
    if t == TYPE_PPG512:
        return True
    else:
        return False

def is_ppg(t):
    if t or is_ppg512(t):
        return True
    else:
        return False

def parse_data(file_obj, signal_type):
    """
    file_obj:    The file obj come from open() or io.BytesIO
    signal_type: 5, 9, or 12
    return:      The list of (timestamp, mv) tuple
    """
    base_ms = 0
    fraction = 0
    buf = []
    data = []
    rule = re.compile("^%d," % signal_type)

    for l in file_obj:
        if not rule.match(l):
            continue

        a = l.rstrip("\n").split(',')
        # extraction
        if is_ecg(signal_type):
            row = a[2:13]
        elif is_ppg(signal_type):
            row = a[2:13:2]

        # timestamp calculation
        new_base_ms = int(a[15]) * MSEC_PER_SEC
        if base_ms == 0:
	    base_ms = new_base_ms
	elif base_ms != new_base_ms:
            fraction = float(new_base_ms - base_ms) / len(buf)
	    for i in range(0, len(buf)):
                ts_ms = base_ms + (fraction * i)
                # sanity check
		if ts_ms >= new_base_ms:
	            print "Error: timestamp equal to or larger than new base timestamp"
                data.append((ts_ms, buf[i]))
	    base_ms = new_base_ms
	    buf[:] = []

        for i in row:
            if is_ecg(signal_type):
                v = convert_ecg_to_mv(float(i))
            elif is_ppg(signal_type):
                v = convert_ppg_to_mv(float(i))
            buf.append(v)

    return data
