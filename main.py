'''
Working with both ERA5 and measured data

@Author: Le Thi Trang
@Date: Jan 26, 2026

Modification
    - Feb 20: Working with ERA5 data downloaded whole Korean areas 
'''



#%%
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

import os
import seaborn as sb


from find_nearest_location import *
from data_processing import *
from visualizing import *
from data_loading import *

from metadata import *

#%%#######################################################################
# DEFINE CHANGABLE VARIABLES AS USER'S INPUT HERE
path_station = 'D:\\InProbation\\Metocean\\Observation_points\\'


dir_era5_data = 'D:\\InProbation\\Metocean\\Data\\ERA5\\reduced_korea\\'
dir_meas_data = 'D:\\InProbation\\Metocean\\Data\\Measurements\\'

years_to_compare = [2017] # year to plot data for comparison between 2 dataset
checking_loc_era5 = [[33.5,126.5], [33.5, 126.75], [33.5, 127]] # locations for plotting ERA5 data for inspection

era5_vars = ['wind_10m_u_v', 'wind_100m_u_v']
# era5_vars = ['wind_100m', 'mean_sea_level_pressure']

# KHOA stations' variables measured
# KHOA stations provide 1-minute interval data
khoa_years = np.arange(2013, 2025, 1) # can change to years need to check

stations_KHOA = ['제주', '성산포']
khoa_ws_name = '풍속(m/s)'
khoa_wd_name = '풍향(deg)'
khoa_timestamp = '관측시간'
# khoa_wind_vars = ['관측시간', '풍속(m/s)', '풍향(deg)'] # only checking wind variables at the moment



# KMA stations'variables measured
# KHOA stations provide 1-hour interval data 
stations_KMA = ['김녕', '우도', '하도']

kma_station_code = '지점'
kma_timestamp = '일시'
kma_water_temp_name = '수온(°C)'
kma_Hmax = '최대파고(m)'
kma_Hm0 = '유의파고(m)'
kma_Hmean = '평균파고(m)'
kma_Twave = '파주기(sec)'




#%%########################################################################
#                   DO NOT MODIFIY THE CODE BELOW
#########################################################################
# Common and fixed variables for both types of data
# loading stations' name and coordinate

file_coord = 'Model calibration and validation.xlsx'
chosen_stations = pd.read_excel(path_station + file_coord, sheet_name='Stations')



#%% Working with self-downloaded ERA5 data. Jan 26, 2026
checking_year = 2017
khoa_station = 'KHOA_성산포'
kma_station = 'KMA_우도'

#load variables from KHOA as user's input
khoa_wind_vars = [khoa_timestamp, khoa_ws_name, khoa_wd_name]
khoa_vars_type = ['datetime64[s]', 'float', 'float']
khoa_type_dict = dict(zip(khoa_wind_vars, khoa_vars_type))

khoa_data = load_meas_data(dir_meas_data, khoa_station, khoa_wind_vars, khoa_type_dict, year=checking_year)

# filtering based on DHI's report to Wando-Gumil criteria
# remove recprds with wind speed outside of [0, 60] range
khoa_data = khoa_data[(khoa_data[khoa_ws_name] > 60) & (khoa_data[khoa_ws_name] <0)]
# remove recprds with directional data outside of [0, 360] range
khoa_data = khoa_data[(khoa_data[khoa_wd_name] > 360) & (khoa_data[khoa_wd_name] <0)]



# #load variables from KMA as user's input
# kma_vars = [kma_station_code, kma_timestamp, kma_water_temp_name, 
#                   kma_Hmax, kma_Hm0, kma_Hmean, kma_Twave ]
# kma_vars_type = ['int32', 'datetime64[s]', 'float', 'float', 'float', 'float', 'float']
# kma_type_dict = dict(zip(kma_vars, kma_vars_type))

# kma_data = load_meas_data(dir_meas_data, kma_station, kma_vars, kma_type_dict, year=checking_year)



era5_loc = [33.5, 127] #location close to both stations above


#load ERA5 data wind at 100m height
[wind_100m_u, wind_100m_v] = load_era5_data(dir_era5_data, 'wind_100m', checking_year)
era5_ws_100m, ear5_wd_100m = compute_ws_wd_from_u_v(wind_100m_u.sel(latitude=era5_loc[0], longitude=era5_loc[1]).u100.values, 
                                              wind_100m_v.sel(latitude=era5_loc[0], longitude=era5_loc[1]).v100.values)
era5_ws_100m = pd.DataFrame(era5_ws_100m, columns=[khoa_ws_name])
era5_ws_100m[khoa_timestamp] = wind_100m_u.valid_time.values
era5_ws_100m = era5_ws_100m.iloc[:, [1,0]]

# checking consistency of 1-hour measured wind speed versus ERA5 hourly wind speed
khoa_1hr_ws_100m = compute_avg_wind_speed(khoa_data[[khoa_timestamp, khoa_ws_name]], 60, verbose=0)
df_ws_combine = pd.merge(khoa_1hr_ws_100m, era5_ws_100m, on=khoa_timestamp, how='right', suffixes=['_khoa_1hour', '_era5'])


nl = '\n'
fig_title = f'{khoa_station}{nl}{df_ws_combine.iloc[0,0].date()} - {df_ws_combine.iloc[-1,0].date()}, Ta=1h,  wind at 100 m  '
scatter_plot_ERA5_against_meas(df_ws_combine, [0, 32], 0.2, fig_title)

#%%load ERA5 data wind at 10m height
[wind_10m_u, wind_10m_v] = load_era5_data(dir_era5_data, 'wind_10m', checking_year)
era5_ws_10m, ear5_wd_10m = compute_ws_wd_from_u_v(wind_10m_u.sel(latitude=era5_loc[0], longitude=era5_loc[1]).u10.values, 
                                              wind_10m_v.sel(latitude=era5_loc[0], longitude=era5_loc[1]).v10.values)

era5_ws_10m = pd.DataFrame(era5_ws_10m, columns=[khoa_ws_name])
try:
    era5_ws_10m[khoa_timestamp] = wind_10m_u.valid_time.values
except:
    era5_ws_10m[khoa_timestamp] = wind_10m_u.time.values

era5_ws_10m = era5_ws_10m.iloc[:, [1,0]]


# checking consistency of 1-hour measured wind speed versus ERA5 hourly wind speed
khoa_1hr_ws_10m = compute_avg_wind_speed(khoa_data[[khoa_timestamp, khoa_ws_name]], 60, verbose=0)
# merge wind speed from ERA5 and measurement, remove time where not common in both
# but why era5 has less data than measurement?? check the time column in both data sets.
df_ws_combine = pd.merge(khoa_1hr_ws_10m, era5_ws_10m, on=khoa_timestamp, how='right', suffixes=['_khoa_1hour', '_era5'])


fig_title = f'{khoa_station}{nl}{df_ws_combine.iloc[0,0].date()} - {df_ws_combine.iloc[-1,0].date()}, Ta=1h, wind at 10 m '
scatter_plot_ERA5_against_meas(df_ws_combine, [0, 32], 0.2, fig_title)

# %% 

plot_time_series_scatter(era5_ws_100m, khoa_timestamp, khoa_ws_name, fig_title="ERA5")
plot_time_series_scatter(khoa_1hr_ws_10m, khoa_timestamp, khoa_ws_name, fig_title="KHOA")

# Need to check size consistency before plotting time series of 2 data 
# era5_ws_100m.compare(khoa_1hr_ws_10m, khoa_ws_name)
union = pd.Series(np.union1d(era5_ws_10m[khoa_timestamp], khoa_1hr_ws_10m[khoa_timestamp]))
intersect = pd.Series(np.intersect1d(era5_ws_10m[khoa_timestamp], khoa_1hr_ws_10m[khoa_timestamp]))
time_diff = khoa_1hr_ws_10m[khoa_timestamp][~khoa_1hr_ws_10m[khoa_timestamp].isin(era5_ws_10m[khoa_timestamp])]


#%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Plot scatter plot for wind speed data between ERA5 data with different observations data
# Mar 03, 2026 
checking_years = [2023]

# Check the similarity of data in 1-year period at the moment
# load ERA5 data
path_era5_data = 'D:\\InProbation\\Metocean\\Data\\ERA5\\reduced_korea\\'
var_name = 'wind_10m_u_v'


# load measurement data
path_meas_data = 'D:\\InProbation\\Metocean\\Data\\Observations\\'
fname_metadata = 'Data description.xlsx'
sheet_name = 'station_metadata_wind'

station_metadata = pd.read_excel(path_meas_data + fname_metadata, sheet_name=sheet_name)

stations = station_metadata['Name'].dropna()
providers = station_metadata['Provider'].dropna()
data_intervals = station_metadata['Data inteval (min)']


# skip 추자도_해양기상부이, 지귀도, 중문해수욕장 for now
skipping_stations = ['추자도_해양기상부이', '지귀도', '중문해수욕장']

# work with data from KHOA first
for checking_year in checking_years:
    # load ERA5 data
    era5_u, era5_v = load_era5_data(path_era5_data, var_name, year=checking_year)
    era5_ws, era5_wd = compute_ws_wd_from_u_v(era5_u.u10.values, era5_v.v10.values)

    # construct xr.Dataset for wind speed and wind direction
    ds_era5_ws = (('time', 'latitude', 'longitude'), era5_ws)
    ds_era5_wd = (('time', 'latitude', 'longitude'), era5_wd)

    era5_wind = era5_u.copy()
    
    era5_wind = era5_wind.assign(ws=ds_era5_ws)
    era5_wind = era5_wind.assign(wd=ds_era5_wd)
    era5_wind = era5_wind.drop_vars('u10')

    del ds_era5_wd
    del ds_era5_ws
    del era5_ws
    del era5_wd
    del era5_u
    del era5_v

    # load measurement data
    for i in range(len(stations)):
        if stations[i] in skipping_stations:
            continue
        path_station = path_meas_data + providers[i] + '\\' + stations[i]
        path_save = 'D:\\InProbation\\Metocean\\Analysis\\' + providers[i] + '\\' + stations[i] + '\\'
        if not os.path.exists(path_save):
            os.makedirs(path_save)

        # dataframe with 3 columns of [timestamp, wind speed, wind direction]
        wind_data = load_meas_data(path_meas_data, providers[i], stations[i], year=checking_year)
        wind_data = deal_with_missing_value(wind_data, num_point=-1) # replace missing value with preceding value

        # return 1-hour average data at the current moment to match with ERA5 data
        # Later convert to 10-min average data
        if data_intervals[i] < 60: # 1-hour data
            meas_ws_1hr = compute_avg_wind_speed(wind_data, 60, data_intervals[i], verbose=0)

            era5_at_nearest_loc = era5_wind.sel(latitude=station_metadata['Lat in ERA5'].loc[i], 
                                                                    longitude=station_metadata[ 'Lon in ERA5'].loc[i])

            # checking consistency of 1-hour measured wind speed versus ERA5 hourly wind speed
            era5_ws_df = pd.DataFrame()
            try:
                era5_ws_df[meas_ws_1hr.columns[0]] = era5_at_nearest_loc.valid_time.values
            except:
                era5_ws_df[meas_ws_1hr.columns[0]] = era5_at_nearest_loc.time.values    

            era5_ws_df[meas_ws_1hr.columns[1]] = era5_at_nearest_loc.ws.values

            df_ws_combine = pd.merge(meas_ws_1hr, era5_ws_df, on=meas_ws_1hr.columns[0], 
                                     how='right', suffixes=['_meas', '_era5'])

            fname_save = f'{providers[i]} {stations[i]} vs. ERA5 at nearest location'
            nl = '\n'
            fig_title = f'{providers[i]} {stations[i]}{nl}{df_ws_combine.iloc[0,0].date()} - {df_ws_combine.iloc[-1,0].date()}, Ta=1h,  wind at 10 m  '
            scatter_plot_ERA5_against_meas(df_ws_combine, [0, 32], 0.2, fig_title, path_save + fname_save)
            # fname_save = f'{providers[i]} {stations[i]} vs. ERA5 ({station_metadata['Lat in ERA5'].loc[i]},{station_metadata['Lon in ERA5'].loc[i]} )'

        else: 
            # TODO: checking data with KMA and data with 1-hr averaged already
            pass


# %%
