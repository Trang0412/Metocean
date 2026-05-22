'''
Compute various parameters from data
- Wind speed from u,v component (ERA5 data)
- Peal wave period (Tp)

@Author: Le Thi Trang
@Date: Jan 21, 2026

'''

from datetime import datetime, timedelta
import math
import numpy as np
import pandas as pd
import scipy.signal as ssig
from scipy.signal import welch
import utide
from sklearn.linear_model import LinearRegression

from pyextremes import EVA
import scipy.stats as sstats
import matplotlib.pyplot as plt

import linecache


#%% Function definition here
def read_fort15_tidal_const(dir_fort15):
    '''Read tidal consituents from ADCIRC engine from fort.15
    Parameters:
        -dir_fort15: str, directory to fort.15 file
    Returns
        -tidal_params: dict,
    '''
    fname = dir_fort15 + 'fort.15'
    tidal_params = dict().fromkeys(['ntidal_const_forced', 'ntidal_const_freq'])

    with open(fname, 'r') as fort15:
        for lidx, line in enumerate(fort15.readlines()):
            if ' NTIF ' in line: 
                tidal_params['ntidal_const_forced'] = int(line.split()[0])
                continue
            if 'NHARF' in line: 
                tidal_params['ntidal_const_freq'] = int(line.split()[0])
                break
    if tidal_params['ntidal_const_freq'] is not None:
        ntidal_const = int(tidal_params['ntidal_const_freq']) 
        
        for i in range(ntidal_const):
            # getline from linecache start lidx from 1 while lidx stopped in previous for loop start from 0
            lidx = lidx+2 
            conts_name = linecache.getline(fname, lidx).split()[0]
            current_const = dict().fromkeys(['freq', 'nodal factor', 'equi_arg'])
            current_const['freq'] = float(linecache.getline(fname, lidx+1).split()[0])
            current_const['period_hr'] = (2 * np.pi / current_const['freq']) / 3600
            current_const['nodal factor'] = float(linecache.getline(fname, lidx+1).split()[1])
            current_const['equi_arg'] = float(linecache.getline(fname, lidx+1).split()[2])
            tidal_params[conts_name] = current_const
    
    # # start reading amplitude and phase for each tidal consituent
    # lidx = lidx + 2
    # tidal_consts = dict().fromkeys(['freq', 'phase'])
    return tidal_params



def wave_quality_control(data, fixed_qc_criteria, data_interval):
    '''
    QC procedure
    Skip period when there is no change in wind speed for 5 hours in consecutive 
    Example: Seongsanpo 2008 from 2008-02-01 to 2008-06-15, probably error in device
    Mar 16, 2026: Automate the process by checking the flat line/degree of changes between consecutive points then casting 
    those points with no changes between, say, for 20 consecutive points 
    (e.g., 20 minutes for 1-min interval data, 1 hour for 5  minute interval data and 5 hours for 1 hr interval)
    Set wind speed outside the range of [0, 60] is missing value
    

    Parameters: 
        - data: pd.DataFrame, including 3 columns of time stamp, wind speed, wind direction
        - data_interval: integer, temporal interval of observation data, in minutes
        - logger: logger, for logging station and year
        - station: string, for logging station name
        - provider: string, for logging station provider
        - checking_year: integer, for logging data year in process

    
    Return:
        -data: pd.DataFrame, wind data with quality controlled
    '''
    time_stamp = data.columns[0]
    data = data.set_index(time_stamp)
    data[data['파주기(sec)']<fixed_qc_criteria['T02'][0]] = pd.NA
    data[data['유의파고(m)']>fixed_qc_criteria['Hm0'][1]] = pd.NA
    try:
        data[data['파향(deg)']<fixed_qc_criteria['direction'][0]] = pd.NA
    except: pass

    value_groups = (data['유의파고(m)'] != data['유의파고(m)'].shift()).cumsum()
    if data_interval == 1:
        stuck_periods = data.groupby(value_groups).filter(lambda x: len(x) > 20).reset_index()
    if data_interval == 5:
        stuck_periods = data.groupby(value_groups).filter(lambda x: len(x) > 12).reset_index()
    if data_interval == 60:
        stuck_periods = data.groupby(value_groups).filter(lambda x: len(x) > 5).reset_index()

    data.loc[stuck_periods[time_stamp]] = pd.NA
    data = data.reset_index()

    return data



def run_EVA(extremes, lambda_val, method, dist, n_boot):
    '''
    Implement extreme value analysis with scipy package
    
    Parameters:
        -extremes: np.array
        -lambda_val: float, number of events per year
        -method: fitting method, e.g., MLE or LS.
        -dist: scipy.stats.rv_continuous
    Returns:
    '''

    n_boot = 1000
    # the data below is annual maxima of water level observation in  Seongsanpo from 2005 to 2023
    extremes = [1.67015374, 1.43289266, 1.40997653, 1.20210067, 1.52954745,
       1.67473259, 1.52111837, 1.151129  , 1.57407068, 1.31543996,
       1.41652406, 1.62690578, 1.351144  , 1.30937085, 1.3373861 ,
       1.34301544, 1.55128144, 1.70173519, 1.51813407, 1.40527482,
       1.38776519, 1.31808503, 1.26137727, 1.22153415, 2.01295661,
       1.25276447, 2.10148656, 1.39815181, 1.63293536, 1.30324747,
       1.29225385, 1.23411466, 1.35503323, 2.29583226, 1.77616051,
       1.95658643, 1.31342783, 1.2196131 , 1.30735572, 1.70144015,
       1.33276883, 1.70839311, 1.36754139, 1.5621796 , 1.32059285,
       1.51901091, 1.55059889, 1.33983393, 1.1873526 , 1.3093231 ,
       1.53079275, 1.79188616, 1.43536119, 1.61609417, 1.29006074,
       1.22047454, 1.34422221, 1.76126473, 1.61996553, 1.31136114,
       1.67433556, 1.27915859, 1.3983121 , 1.29791285, 1.79748456,
       1.28310562, 2.10828448, 1.40977466, 1.29211513, 1.67189802,
       1.4337882 , 1.4713478 , 1.327887  , 1.24492218, 1.19244187,
       1.25186284, 1.46947683, 1.33171907, 1.37144485, 1.4345746 ,
       1.43411848, 1.41803528, 1.47092009, 1.79576925, 1.96858465,
       3.35721758, 1.35275823, 1.40191904, 1.31662476, 1.49880755,
       1.36267196, 1.62302015, 1.38779227, 1.20164883]

    
    T = np.linspace(1.1, 200, 200)
    F = 1 - 1/T

    n = len(extremes)
    
    loc, scale = sstats.gumbel_r.fit(extremes)
    gumbel_rl = sstats.gumbel_r.ppf(F, loc=loc, scale=scale)

    rl_boot = []
    for _ in range(n_boot):
        sample = np.random.choice(extremes, size=len(extremes), replace=True)
        loc_b, scale_b = sstats.gumbel_r.fit(sample)
        rl_boot.append(sstats.gumbel_r.ppf(F, loc=loc_b, scale=scale_b))

    rl_boot = np.array(rl_boot)

    lower = np.percentile(rl_boot, 2.5, axis=0)
    upper = np.percentile(rl_boot, 97.5, axis=0)

    sorted_data = np.sort(extremes)
    P = np.arange(1, n+1) / (n+1)
    T_emp = 1 / (1 - P)

    # -----------------------------
    # Plot
    # -----------------------------
    plt.figure(figsize=(8,6))

    plt.scatter(T_emp, sorted_data, label="Observed AM")
    plt.plot(T, gumbel_rl, 'r-', label="Gumbel fit")

    plt.fill_between(T, lower, upper, alpha=0.3, label="95% CI")

    plt.xscale('log')
    plt.xlabel("Return Period (years)")
    plt.ylabel("Water Level")
    plt.title("Gumbel Fit with Bootstrap Confidence Interval")
    plt.legend()
    plt.grid(True)
    plt.show()

    # probability density plot
    x_r = np.linspace(sstats.gumbel_r.ppf(0.001, loc=loc, scale=scale),
                sstats.gumbel_r.ppf(0.999, loc=loc, scale=scale), 1000)
    
    plt.figure()
    plt.hist(extremes, bins=np.histogram_bin_edges(extremes, bins='auto'), 
             density=True,
             rwidth=0.8, lw=0, zorder=5)
    
    plt.plot(x_r, sstats.gumbel_r.pdf(x_r, loc=loc, scale=scale))


#TODO: April 17, 2026
def derive_current_log_profile(cs_depth_avg, d, z):
    '''Derive surface/near sea-bed currents using log profile expression, 
    namely a 1/17th power law (used by DHI, section 2.6, Current speed profile)
    
    Parameters
        -cs_depth_avg: pd.DataFrame, (modelled) depth-averaged current speed
            2 columns; 1st: timestamp, 2nd: current speed [m/s]
        -d: float, local water depth
        -z: float, distance z from the seabed relative to d

    Returns
        -cs_z: np.array
    '''
    return np.power(8/7*cs_depth_avg.iloc[:,1].values + z/d, 1/7)


def compute_spectrum(u, dt, nperseg=256):
    '''
    Compute spectrum of time series data
    Parameters:
        -u: np.array, time series data
        -dt: float, sampling interval of data, in unit of seconds
        -nperseg: length of each segment 

    Returns:
        -f: array of sample frequencies
        -S: power spectral density
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

   
def quality_control(data, data_type, fixed_qc_criteria, data_interval, station, provider, checking_year, logger):
    '''
    QC procedure
    Skip period when there is no change in wind speed for 5 hours in consecutive 
    Example: Seongsanpo 2008 from 2008-02-01 to 2008-06-15, probably error in device
    Mar 16, 2026: Automate the process by checking the flat line/degree of changes between consecutive points then casting 
    those points with no changes between, say, for 20 consecutive points 
    (e.g., 20 minutes for 1-min interval data, 1 hour for 5  minute interval data and 5 hours for 1 hr interval)
    Set wind speed outside the range of [0, 60] is missing value
    

    Parameters: 
        - wind_data: pd.DataFrame, including 3 columns of time stamp, wind speed, wind direction
        - data_interval: integer, temporal interval of observation data, in minutes
        - logger: logger, for logging station and year
        - station: string, for logging station name
        - provider: string, for logging station provider
        - checking_year: integer, for logging data year in process

    
    Return:
        -wind_data: pd.DataFrame, wind data with quality controlled
    '''
    time_stamp = data.columns[0]
    data = data.set_index(time_stamp)
    if data_type=='wind':
        data[data['풍속(m/s)']<fixed_qc_criteria['ws'][0]] = pd.NA
        data[data['풍속(m/s)']>fixed_qc_criteria['ws'][1]] = pd.NA
        data[data['풍향(deg)']<fixed_qc_criteria['direction'][0]] = pd.NA
        data[data['풍향(deg)']>fixed_qc_criteria['direction'][1]] = pd.NA
        
        value_groups = (data['풍속(m/s)'] != data['풍속(m/s)'].shift()).cumsum()

    elif data_type=='current':
        data[data['유속(m/s)']<fixed_qc_criteria['ws'][0]] = pd.NA
        data[data['유속(m/s)']>fixed_qc_criteria['ws'][1]] = pd.NA
        data[data['풍향(deg)']<fixed_qc_criteria['direction'][0]] = pd.NA
        data[data['풍향(deg)']>fixed_qc_criteria['direction'][1]] = pd.NA

    if data_interval == 1:
        stuck_periods = data.groupby(value_groups).filter(lambda x: len(x) > 20).reset_index()
    if data_interval == 5:
        stuck_periods = data.groupby(value_groups).filter(lambda x: len(x) > 12).reset_index()
    if data_interval == 60:
        stuck_periods = data.groupby(value_groups).filter(lambda x: len(x) > 5).reset_index()

    if len(stuck_periods)>2:
        logger.info(f'QC (stuck periods) applied to: {station}_{provider}, {checking_year}')
    data.loc[stuck_periods[time_stamp]] = pd.NA
    data = data.reset_index()
    return data