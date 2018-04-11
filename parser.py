import numpy as np
import re

TYPE_ECG=5
TYPE_PPG125=9
TYPE_PPG512=12
MSEC_PER_SEC = 1000

acc_data = []
ppg_data = []
ecg_data = []

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

def parse_raw_acc(x):
    """ Parse one line of raw acc data and add it to acc data """
    items = x.split(',')
    nums = map(int, items)
    ts_ms = nums[15] * MSEC_PER_SEC
    acc_data.append((ts_ms, (nums[2], nums[3], nums[4])))
    acc_data.append((ts_ms, (nums[6], nums[7], nums[8])))
    acc_data.append((ts_ms, (nums[10], nums[11], nums[12])))

def parse_raw_ppg(x):
    """ Parse one line of raw ppg data and add it to ppg data """
    items = x.split(',')
    # convert ppg to mv
    strs = items[2:13:2]
    nums = map(int, strs)
    nums = map(convert_ppg_to_mv, nums)
    # convert ts to ms
    ts_ms = int(items[15]) * MSEC_PER_SEC
    for n in nums:
        ppg_data.append((ts_ms, n))

def parse_raw_ecg(x):
    """ Parse one line of raw ecg data and add it to ecg data """
    items = x.split(',')
    # convert ppg to mv
    strs = items[2:13]
    nums = map(int, strs)
    nums = map(convert_ecg_to_mv, nums)
    # convert ts to ms
    ts_ms = int(items[15]) * MSEC_PER_SEC
    for n in nums:
        ecg_data.append((ts_ms, n))

def calc_ts(x):
    base_ms = 0
    data = []
    buf = []
    for l in x:
        new_ms = l[0]
        mv = l[1]
        if base_ms == 0:
            base_ms = new_ms
        elif base_ms != new_ms:
            fraction = float(new_ms - base_ms) / len(buf)
            for i in range(0, len(buf)):
                ts_ms = base_ms + (fraction * i)
                if ts_ms >= new_ms:
                    print "Error: timestamp equal to or larger than new base timestamp"
                data.append((ts_ms, buf[i]))
            base_ms = new_ms
            buf[:] = []
        buf.append(mv)
    return data

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

#x = '12,20164,8380828,8380830,8380832,8380832,8380835,8380838,8380839,8380841,8380844,8380844,8380847,8380845,12345,1519268239'
#parse_raw_ppg(x)
#print ppg_data
