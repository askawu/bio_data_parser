#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import numpy as np
import os

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('raw_data_file', nargs=1, help='Specify the raw data file')
    return vars(p.parse_args())

MSEC_PER_SEC = 1000

def get_interpolated_ts(ts, ratio):
    new_ts = None
    vals, idx = np.unique(ts, return_index=True)
    idx = np.hstack((idx,ts.shape[0])) # so we can do idx[i+1] - idx[i]
    vals = np.hstack((vals,vals[-1] + MSEC_PER_SEC))
    for i in xrange(vals.size-1):
        num = idx[i+1] - idx[i]
        # we have to expand time intervals according to the ratio for
        # we might have multiple data in one row
        tmp = np.linspace(vals[i], vals[i+1], num * ratio, False)
        new_ts = np.append(new_ts, tmp) if new_ts is not None else tmp
    return new_ts

def convert_ecg_to_mv(raw, ratio=1000./6/2097152):
    idx = np.where(raw >= 4194304)
    raw[idx] -= 8388608
    return raw * ratio

def convert_ppg_to_mv(raw):
    return convert_ecg_to_mv(raw, 3.2*1000/65536)

if __name__ == "__main__":
    args = parse_args()
    input_file = os.path.basename(args["raw_data_file"][0])

    # 0: ACC, 5: ECG, 9: PPG 125 Hz, 12: PPG 512 Hz
    basename = os.path.splitext(input_file)[0]
    params = {
             #type: [filename, wanted indexes, data per row, data per item, convert function (if any)]
              0:  [ basename + "_acc.csv", [2,3,4,6,7,8,10,11,12], 3, 3, None],
              5:  [ basename + "_ecg.csv", range(2,13), 11, 1, convert_ecg_to_mv],
              9:  [ basename + "_ppg125.csv", range(2,13,2), 6, 1, convert_ppg_to_mv],
              12: [ basename + "_ppg512.csv", range(2,14), 12, 1, convert_ppg_to_mv],
             }

    data = np.genfromtxt(input_file, delimiter=",")
    for data_type in params.keys():
        fname, wanted, data_per_row, data_per_item, fn_convert = params[data_type]

        # check if data_type exists in the input file
        idx = np.where(data[:,0] == data_type)[0]
        if len(idx) <= 0:
            continue

        # filter out specific type
        raw = data[idx]
        # filter out columns and reshape into given row, column
        raw = raw[:,wanted].reshape(raw.shape[0] * data_per_row, data_per_item)
        # if further convert() is required, call it
        if fn_convert:
            raw = fn_convert(raw)
        # get the interpolated timestamp
        ts = get_interpolated_ts(data[idx,-1] * MSEC_PER_SEC, data_per_row)
        # match time stamps w/ the parsed data
        output = np.column_stack((ts, raw))
        # dump into output file
        np.savetxt(fname, output, delimiter=',')

