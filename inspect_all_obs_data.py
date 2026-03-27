'''
- Conduct prerequisite processing data different parameters for model calibration 
    (DHI report to Wando-Gumil, section 2.2.1)

    1. Measurement's data quality and filtering
        



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


from common_processing import *
from visualizing import *
from data_loading import *

from metocean_metadata import *

project_dir = 'D:\\InProbation\\Metocean\\'
obs_data_dir = project_dir + 'Data\\Observations\\'

fname_metadata = 'Calibration_metadata.xlsx'
working_dir = project_dir + 'Analysis\\Obs_quality_filtering\\'

skipping_stations ={
    'Wind': ['추자도_해양기상부이', '지귀도', '중문해수욕장'],
    'Wave': ['중문해수욕장'],
    'Water': ['추자도_해양기상부이', '지귀도', '중문해수욕장'],
    'Current': []
}
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# PARAMETERS TO CHANGE DEPENDING ON TYPE DATA IN ANALYSIS
checking_years = [2023, 2024] 

type_in_check = 'Water'

# 1. Inspect measurement'data quality (time series plotting) and filtering
# Mar 09
#%%

save_dir = working_dir + type_in_check + '\\'

if not os.path.isdir(save_dir):
    os.makedirs(save_dir)

vars_metadata = pd.read_excel(obs_data_dir + fname_metadata, sheet_name=type_in_check, header=1)
stations = vars_metadata['Name'].dropna()
providers = vars_metadata['Provider'].dropna()
data_intervals = vars_metadata['Data inteval (min)']


for checking_year in checking_years:
    for i in range(len(stations)):

        if stations[i] in skipping_stations[type_in_check]:
            continue

        if providers[i] == 'KHOA':
            time_stamp = '관측시간'
            
        elif providers[i] == 'KMA':
            time_stamp = '일시'

        obs_all_data = load_obs_all_data(obs_data_dir, providers[i], stations[i], year=checking_year)
        type_params = vars_metadata[type_in_check + ' parameters']

        if type_in_check == 'Wind':

            cols_to_load = [var for var in list(wind_var_names.keys()) if var.split('(')[0] in type_params[i]]
            cols_to_load.insert(0, time_stamp)

            wind_data = obs_all_data[cols_to_load]

            vars_type = ['datetime64[s]']
            vars_type.extend(['float'] * (len(cols_to_load) -1))
            wind_data = wind_data.astype(dict(zip(cols_to_load, vars_type)))

            # compute 1hr-averaged 
            if data_intervals[i] < 60: # 1-hour data
                ws_1hr = compute_data_avg_time(wind_data, 60, data_intervals[i], verbose=0)
            else:
                ws_1hr = wind_data[[time_stamp, '풍속(m/s)']]


            fig_title = f'{stations[i]} ({providers[i]}) wind speed {checking_year}'
            fname_save = f"{stations[i]}_{providers[i]}_{checking_year}.png"
            plot_time_series_1var(ws_1hr, time_stamp, '풍속(m/s)', fig_size=[12,3], fig_title=fig_title, fname_save=save_dir+'WS\\'+fname_save)
        

            # rose_plot(wind_data['풍향(deg)'], wind_data['풍속(m/s)'], fig_title=f'{stations[i]} ({providers[i]}) wind rose {checking_year}')
            
        elif type_in_check == 'Wave':

            cols_to_load = [var for var in list(wave_var_names.keys()) if var.split('(')[0] in type_params[i]]
            cols_to_load.insert(0, time_stamp)
        
            wave_data = obs_all_data[cols_to_load]

            vars_type = ['datetime64[s]']
            vars_type.extend(['float'] * (len(cols_to_load) -1))
            wave_data = wave_data.astype(dict(zip(cols_to_load, vars_type)))

            # plot Hm0 [유의파고(m)]
            # All the stations provide 1 hour data, except station from KHOA, which will be separately investigated later
            fig_title = f'{stations[i]} ({providers[i]}), significant wave height, Hm0, {checking_year}'
            fname_save = f"{stations[i]}_{providers[i]}_{checking_year}.png"
            plot_time_series_1var(wave_data, time_stamp, '유의파고(m)', fig_size=[12,3], fig_title=fig_title, fname_save=save_dir+'Hm0\\'+fname_save, txt_box_loc=[1.1,  0.9])
        
            # plot T02 [파주기(s)]
            # All the stations provide 1 hour data, except station from KHOA, which will be separately investigated later
            fig_title = f'{stations[i]} ({providers[i]}), zero-crossing wave period, T02, {checking_year}'
            fname_save = f"{stations[i]}_{providers[i]}_{checking_year}.png"
            plot_time_series_1var(wave_data, time_stamp, '파주기(sec)', fig_size=[12,3], fig_title=fig_title, fname_save=save_dir+'T02\\'+fname_save, txt_box_loc=[1.1,  0.9])
        
        elif type_in_check == 'Water':

            cols_to_load = [var for var in list(water_var_names.keys()) if var.split('(')[0] in type_params[i]]
            cols_to_load.insert(0, time_stamp)

            water_data = obs_all_data[cols_to_load]

            vars_type = ['datetime64[s]']
            vars_type.extend(['float'] * (len(cols_to_load) -1))
            water_data = water_data.astype(dict(zip(cols_to_load, vars_type)))

            # water_data['조위(m)'] = np.round(water_data['조위(cm)'] /1000, decimals=2)
            # plot_time_series_1var(water_data, time_stamp, '조위(m)', fig_size=[16,4], fig_title=fig_title, fname_save=working_dir+fname_save)

            if data_intervals[i] < 60: # 1-hour data
                wl_1hr = compute_data_avg_time(water_data, 60, data_intervals[i], verbose=0)
            else:
                wl_1hr = water_data[[time_stamp, '조위(cm)']]

            # convert to m unit instead of cm
            wl_1hr['조위(m)'] = np.round(wl_1hr['조위(cm)'] /100, decimals=2)

            fig_title = f'{stations[i]} ({providers[i]}) 조위 {checking_year}'
            fname_save = f"{stations[i]}_{providers[i]}_{checking_year}.png"
            plot_time_series_1var(wl_1hr, time_stamp, '조위(m)', fig_size=[12,3], fig_title=fig_title, fname_save=save_dir+'WL\\'+fname_save)
              

            # Correct to MSL 
            # Simply substract mean value 


        elif type_in_check == 'Current':
            cols_to_load = [var for var in list(current_var_names.keys()) if var.split('(')[0] in type_params[i]]
            cols_to_load.insert(0, time_stamp)
        
            current_data = obs_all_data[cols_to_load]
            vars_type = ['datetime64[s]']
            vars_type.extend(['float'] * (len(cols_to_load) -1))
            current_data = current_data.astype(dict(zip(cols_to_load, vars_type)))
            # convert to m/s
            current_data['유속(m/s)'] = np.round(current_data['유속(cm/s)'] /100, decimals=2)

            # current speed
            fig_title = f'{stations[i]} ({providers[i]}) 유속 {checking_year}'
            fname_save = f"{stations[i]}_{providers[i]}_{checking_year}.png"
            plot_time_series_1var(current_data, time_stamp, '유속(m/s)', fig_size=[16,4], fig_title=fig_title, fname_save=save_dir+'CS\\'+fname_save)
        
            # TODO: rose plot for current speed and current direction

        del obs_all_data
# Wave
# Current
# Water

#%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# 2. Wind data checking for model forcing: ERA5 vs Observation 
#%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Mar 03, 2026 
checking_years = [2023]

# Check the similarity of data in 1-year period at the moment
# load ERA5 data
path_era5_data = 'D:\\InProbation\\Metocean\\Data\\ERA5\\reduced_korea\\'
var_name = 'wind_10m_u_v'


# load measurement data
path_meas_data = 'D:\\InProbation\\Metocean\\Data\\Observations\\'
fname_metadata = 'Calibration_metadata.xlsx'
sheet_name = 'Wind'

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
        path_save = 'D:\\InProbation\\Metocean\\Analysis\\ERA5_vs_Obs\\' + providers[i] + '\\'
        if not os.path.exists(path_save):
            os.makedirs(path_save)

        # dataframe with 3 columns of [timestamp, wind speed, wind direction]
        wind_data = load_obs_wind_data(path_meas_data, providers[i], stations[i], year=checking_year)
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

            fname_save = f'Scatter_plot_{stations[i]}_vs_nearest_ERA5.png'
            nl = '\n'
            fig_title = f'{providers[i]} {stations[i]}{nl}{df_ws_combine.iloc[0,0].date()} - {df_ws_combine.iloc[-1,0].date()}, Ta=1h,  wind at 10 m  '
            scatter_plot_ERA5_against_meas(df_ws_combine, [0, 32], 0.2, fig_title, path_save + fname_save)
            # fname_save = f'{providers[i]} {stations[i]} vs. ERA5 ({station_metadata['Lat in ERA5'].loc[i]},{station_metadata['Lon in ERA5'].loc[i]} )'

        else: 
            # TODO: checking data with KMA and data with 1-hr averaged already
            pass


# %%
