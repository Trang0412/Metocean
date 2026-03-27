'''
Compute various parameters from data
- Wind speed from u,v component (ERA5 data)
- Peal wave period (Tp)

@Author: Le Thi Trang
@Date: Jan 21, 2026

'''

import math
import numpy as np
import pandas as pd
from scipy.signal import welch

def compute_spectrum(u, dt, nperseg=256):
    '''
    Compute spectrum of time series data
    Parameters:
        -u: np.array, time series data
        -dt: float, sampling interval of data, in unit of seconds
        -nperseg: length of each segment 

    Returns:
        -f: array of sample frequencies
        - S: power spectral density
    '''
    fs = 1 / dt
    u = u - np.mean(u)
    f, S = welch(u, fs=fs, nperseg=nperseg)
    return f[1:], S[1:]  # remove zero freq

def compute_data_avg_time(data, min_to_avg, data_interval, verbose=0):
    '''
    - Compute 10-minute average wind speed from 1-minute interval data measured
    - Only used for calculating avg for interval less than or equal to 1 hour
    - For retrieving data for interval large than 1 hour -> create new function

    Parameters:
        -ws_data: pd.DataFrame, with 3 colums,    
                1st: time measured with 1-min resolution
                2nd: wind speed in unit of m/s 
                3rd: wind direction in unit of degree
        -min_to_avg: int, number of minutes that data be averaged out
        -data_interval: int, interval of data in minutes (e.g., 1, 5, 60 minutes)
        -verbose: int, for later used as indicating sampling scheme for quantizing data (DNV, 2.3.1.4)
                Currently, average data are calculated from only one period every hour

    Return
        -ws_avg: pd.DataFrame, with 2 colums,
            1st: time measured with 1-min resolution
            2nd: average wind speed over predefined minutes (m/s) 
         

    '''
    columns_name = data.columns

    points_per_hour = int(60 / data_interval) # for data with 1-min interval 

    #########################################################################
    # TODO: Sampling scheme. later, need to change according to use input

    times_avg_per_hour = 1 # taking average for only one period every 1 hour
    total_points = int(data.shape[0]/points_per_hour) * times_avg_per_hour # compute number of returned data points 

    # always taking same part of data in 1 hour. 
    # E.g., always taking first 10 minutes in that hour for computing average wind speed
    taken_mins = np.arange(0, min_to_avg, 1)
    #########################################################################

    data_avg = np.zeros(total_points)
    idx_count = 0
    count = 0
    while count < data.shape[0]:

        data_avg[idx_count] = data.iloc[count:(idx_count+1)*points_per_hour,1].loc[count+taken_mins].mean(skipna=True)
        idx_count = idx_count+1
        count = count + points_per_hour

    data_avg = pd.DataFrame(data_avg, columns=[columns_name[1]]).round(2) # keep 2 number after decimal point
    data_avg[columns_name[0]] = data.iloc[0:-1:points_per_hour,0].values # adding time data back to dataframe

    return data_avg.iloc[:,[1,0]]


def deal_with_missing_value(wind_data, num_point=-99):
    '''
    This function aim to deal with missing value according to various approach.
    Namely: by mean of certain variables prior and after the missing point

    Parameters:
        wind_data: pandas.DataFrame of wind data, contain only numerical type
        num_point: integer, vary depends on purpose. Default value is set to -99
            -1: filling as the value of one data point prior
            0: filling as the value of one data point prior
            TODO: n: filling as mean of n data points prior and n data points after.
            -99: simply drop missing value

    '''
    if num_point == -1:
        wind_data.ffill()  
    elif num_point == 0:
        wind_data.bfill()
    elif num_point == -99:
        wind_data.dropna()
    else:
       pass
    return wind_data

        
def filter_wind_meas_data(data, variable_names, quality_criteria):
    '''
    Function for filtering of data and removal of wrong data from measurements
    Refer to DHI Wando-Gumil section 2.2.1. Measurement's data quality and filtering

    Parameter
    Return
    '''
    pass

    
def find_duplicate(data, time_stamp):
    '''
    Remove duplicated records in observation data based on time information.
    Currently doing manually: remove duplicate records
    Representative data: Seongsanpo 2006 year

    Parameters:
        - data: pd.Dataframe with first colume is Time. 

    Return:
        - idxs_to_remove: list, list of indexes of duplidates which should be removed

    '''
    # check if data were all duplicated
    # Representative 2022년 거문도 조위관측소
    # 8760 = 24 * 365
    fist_records = data.index[data[time_stamp] == data[time_stamp].iloc[0]]
    if fist_records.size>1 and np.diff(fist_records)>8760:
        removed_idxs = np.arange(fist_records[1],len(data))
        data.drop(removed_idxs, inplace=True)
        # frop four metadata line
        data.drop(np.arange(len(data)-4,len(data)), inplace=True)

    row_duplicated = data.index[data.duplicated(subset=time_stamp) == True].tolist()
    
    idxs_to_remove = np.zeros_like(row_duplicated)
    for i, ri in enumerate(row_duplicated):
        if pd.isna(data.iloc[ri,1:-1]).all():
            idxs_to_remove[i] = ri
        else:
            idxs_to_remove[i] = ri-1

    return idxs_to_remove
