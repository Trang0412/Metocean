'''
Compute Wind direction and Wind speed from u,v-component of wind

@Author: Le Thi Trang
@Date: Jan 21, 2026

'''

import math
import numpy as np
import pandas as pd


def compute_avg_wind_speed(ws_data, min_to_avg, verbose=0):
    '''
    Compute 10-minute average wind speed from 1-minute interval data measured at KHOA stations

    Parameters:
        ws_data: pd.DataFrame, with 2 colum,    
                1st: time measured with 1-min resolution
                2nd: wind speed in unit of m/s 
        min_to_avg: int, number of minutes that data be averaged out
        verbose: int, for later used as indicating sampling scheme for quantizing data (DNV, 2.3.1.4)
                Currently, average data are calculated from only one period every hour

    Return
        ws_avg: pd.DataFrame, with 2 colum,
            1st: time measured with 1-min resolution
            2nd: average wind speed over predefined minutes (m/s) 
         

    '''
    columns_name = ws_data.columns

    points_per_hour = 60

    #########################################################################
    # TODO: Sampling scheme. later, need to change according to use input

    points_avg_per_hour = 1 # taking average for only one period every 1 hour
    total_points = int(ws_data.shape[0]/points_per_hour) * points_avg_per_hour # compute number of returned data points 

    # always taking same part of data in 1 hour. 
    # E.g., always taking first 10 minutes in that hour for computing average wind speed
    taken_mins = np.arange(0, min_to_avg, 1)
    #########################################################################

    ws_avg = np.zeros(total_points)
    idx_count = 0
    count = 0
    while count < ws_data.shape[0]:

        ws_avg[idx_count] = ws_data.iloc[count:(idx_count+1)*points_per_hour,1].loc[count+taken_mins].mean()
        idx_count = idx_count+1
        count = count + points_per_hour

    ws_avg = pd.DataFrame(ws_avg, columns=[columns_name[1]]).round(2) # keep 2 number after decimal point
    ws_avg[columns_name[0]] = ws_data.iloc[0:-1:points_per_hour,0].values # adding time data back to dataframe

    return ws_avg.iloc[:,[1,0]]

    

def compute_ws_wd_from_u_v(u, v):
    '''
    Compute wind speed and wind direction from u,v-component from ERA5 data
    
    Parameters:
        u: array data 
        v: array data 
    '''
    wind_speed = np.sqrt(np.power(u, 2) + np.power(v, 2))
    wind_direction = 180 + (180/math.pi) * np.atan2(u, v)

    return wind_speed, wind_direction


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

    
#TODO: Jan 23, 2026
def compute_wind_parameters():
    '''
    Function for obtaining wind parameters.
    Refer to DNV-GL-2018 Metocean Characterization 
    Recommended practice for US offshore wind energy

    Wind parameters including:
        Wind speed statistics (min, mean, std, max) and distribution
        Wind directionality
        Wind profile, wind shear, turbulence
    '''
    pass


def compute_wind_speed_spectrum():
    '''
    For spectral comparion of ERA5 and measured wind speed 
    Refer to Figure 2.11 from DHI report for Wando-Gumil, page 22
    '''
    pass

#TODO: convert surface wind from measurement data to 10-m height as in ERA5?
# Jan 26, 2026
# Refer to DHI report for Wando-Gumil:
# measurements (60mMSL) were converted to 10mMSL using a power wind profile and a shear factor of 0.11.
# Check if data were measured at what heights. For exampple, 10m, 50m mMSL
def convert_wind_speed_height_power(U_ref, z, z_ref, a_w):
    '''
    Convert wind averaging at certain vertical level(height, e.g., 100 m) to certain vertical level (e.g., 10 m)
    Using power law to convert wind speed at measured height (e.g., 60mMSL) to reference height (e.g., 10mMSL)
    Refer to formula 5-2, page 97, DNV-GL Metocean Characterization Recommended Practices for U.S. Offshore Wind Energy

    Parameter
        -U: numpy.array, of wind speed data at height measured
        -z: integer, height at that level wind profile was measured and/or computed
        -z_ref: integer, height at that level wind profile should be converted (i.e., reference height, usually 10 m)
        -a_w: float, shear exponent factor used for conversion

    Return
        -cwind_data: numpy.array, converted wind data to expected vertical level
    '''

    # z = 60
    # z_ref = 10


    return np.multiply(U_ref, np.power(z/z_ref, a_w))