'''
- Conduct WIND analysis
1. Compare original ERA5 wind data with observation data
2. Compare rescaled ERA5 wind data with observation data
3. Compare WRF wind data with Observation? (optional)

@Author: Le Thi Trang
@Date: Mar 10, 2026

'''
#%%
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

import os
import seaborn as sb

import logging


from find_nearest_location import *
from common_processing import *
from visualizing import *
from data_loading import *

from metocean_metadata import *
from wind_data_processing import *

project_dir = 'D:\\InProbation\\Metocean\\'
obs_data_dir = project_dir + 'Data\\Observations\\'
era5_data_dir = 'D:\\InProbation\\Metocean\\Data\\ERA5\\'

fname_metadata = 'Prerequisite_wind_data_analysis.xlsx'
working_dir = project_dir + 'Analysis\\'
saving_dir = working_dir + 'ERA5_vs_Obs\\'
path_save = 'D:\\InProbation\\Metocean\\Analysis\\ERA5_vs_Obs\\original_ERA5\\yearly\\'
path_save_time_series_plot = working_dir + 'Obs_quality_filtering\\Wind\\time_series_plot\\'

logger = logging.getLogger(__name__)
logging.basicConfig(filename= path_save +'Wind_analysis.log', filemode='w', encoding='utf-8', level=logging.INFO)
nl  = '\n'


#%%  1. Original ERA5 with Observations

vars_metadata = pd.read_excel(working_dir + fname_metadata, sheet_name='ERA5_wind_obs', header=1)
stations = vars_metadata['Name'].dropna()
providers = vars_metadata['Provider'].dropna()
data_intervals = vars_metadata['Data inteval (min)']
data_duration = vars_metadata['Wind data available']

skipping_stations =['추자도_해양기상부이', '지귀도', '중문해수욕장']


for i in range(len(stations)):

    if stations[i] in skipping_stations:
            continue
    
    if providers[i] == 'KHOA':
        time_stamp = '관측시간'
        
    elif providers[i] == 'KMA':
        time_stamp = '일시'

    checking_duration = data_duration[i].split('-')
    checking_period = list(np.arange(int(checking_duration[0]), int(checking_duration[1])))
    type_params = vars_metadata['Wind parameters'][i].split(',')
    type_params = [s.replace(' ', '') for s in type_params]
    type_params = [s for s in type_params if s!='']
   
    
    for checking_year in checking_period:

        # loading observation data
        obs_all_data = load_obs_all_data(obs_data_dir, providers[i], stations[i], year=checking_year)
        
        cols_to_load = [time_stamp]
        for var in type_params:
            for wind_param in list(obs_all_data.columns):
                if var in wind_param.replace('1', '') and var not in cols_to_load:
                    cols_to_load.append(wind_param)

        wind_data = obs_all_data[cols_to_load]
        new_cols_name = [s.replace('1','') for s in cols_to_load]
        wind_data = wind_data.rename(columns=dict(zip(cols_to_load,new_cols_name)))
        idxs_to_remove = find_duplicate(wind_data, time_stamp)
        wind_data.drop(idxs_to_remove, inplace=True)


        vars_type = ['datetime64[s]']
        vars_type.extend(['float'] * (len(cols_to_load) -1))
        wind_data = wind_data.astype(dict(zip(new_cols_name, vars_type)))
        
        # set wind speed outside the range of [0, 60] is missing value
        wind_data[wind_data['풍속(m/s)']<0 ] = pd.NA
        wind_data[wind_data['풍속(m/s)']>60 ] = pd.NA
        wind_data[wind_data['풍향(deg)']<0] = pd.NA
        wind_data[wind_data['풍향(deg)']>360 ] = pd.NA
        
        # compute 1hr-averaged 
        wind_obs_1hr = wind_data.groupby(pd.Grouper(key=time_stamp, freq="1h")).mean().reset_index()

        ####################################################################################
        # Plot time series of observation data
        plot_saving_dir = path_save_time_series_plot+stations[i]+'_'+providers[i]+'\\'
        if not os.path.exists(plot_saving_dir):
             os.makedirs(plot_saving_dir)

        fname_save = plot_saving_dir + f'{checking_year}_WS.png'
        fig_title = f'{stations[i]}{nl}{wind_obs_1hr.iloc[0,0].date()} - {wind_obs_1hr.iloc[-1,0].date()}, Ta=1h,  wind at 10 m  '
        plot_time_series_1var(wind_obs_1hr, time_stamp, '풍속(m/s)', fig_size=[12, 3], fig_title=fig_title, fname_save=fname_save)
        
        ####################################################################################
        # skip analysis when more than 6 months of data are missed
        if wind_obs_1hr['풍속(m/s)'].isna().sum() > (len(wind_obs_1hr)/2):  
            logger.info(f'{stations[i]}, {checking_year} have missing value more than 6 months -> skip')
            continue
    
        # skip period when there is no change in wind speed for 5 hours in consecutive 
        # example: Seongsanpo 2008 from 2008-02-01 to 2008-06-15, probably error in device
        # do manualy for now
        # TODO: automate this process by checking the flat line/degree of changes between consecutive points then casting 
        # those points with no changes between, say, for 5 consecutive points
        if stations[i] == '성산포' and providers[i] == 'KHOA': 
            if checking_year == 2008:
                wind_obs_1hr = wind_obs_1hr.set_index(time_stamp)
                wind_obs_1hr.loc['2008-01-20':'2008-06-15',:] = pd.NA
                wind_obs_1hr = wind_obs_1hr.reset_index()
                
                fname_save = plot_saving_dir + f'{checking_year}_WS_cast_missing_value.png'
                plot_time_series_1var(wind_obs_1hr, time_stamp, '풍속(m/s)', fig_size=[12, 3], fig_title=fig_title, fname_save=fname_save)
            elif checking_year == 2005:

        ####################################################################################
        # Load ERA5 orignal data. 
        # data loadded in xarray.Dataset
        [era5_u, era5_v]= load_era5_wind_data(era5_data_dir + 'reduced_korea\\', 'wind_10m', year=checking_year)\
        
        era5_ws, era5_wd = compute_ws_wd_from_u_v(era5_u.sel(latitude=vars_metadata['Lat in ERA5'][i], longitude=vars_metadata['Lon in ERA5'][i]).u10.values, 
                                                    era5_v.sel(latitude=vars_metadata['Lat in ERA5'][i], longitude=vars_metadata['Lon in ERA5'][i]).v10.values)
        era5_ws = pd.DataFrame(era5_ws, columns=['풍속(m/s)'])
        era5_wd = pd.DataFrame(era5_wd, columns=['풍향(deg)'])
        try:
            era5_ws[time_stamp] = era5_u.valid_time.values
            era5_wd[time_stamp] = era5_u.valid_time.values
        except:
            era5_ws[time_stamp] = era5_u.time.values
            era5_wd[time_stamp] = era5_u.time.values

        era5_ws = era5_ws.iloc[:, [1,0]]

        ####################################################################################
        # Comparison between Observation with ERA5 
        # yearly comparison
        df_ws_combine = pd.merge(wind_obs_1hr[[time_stamp, '풍속(m/s)']], era5_ws, on=time_stamp, how='right', suffixes=['_obs', '_era5'])


        # TODO: drop records where there is no data observed

        saving_dir = path_save + '\\' + stations[i] + '_' + providers[i] + '\\scatter_plot\\'
        if not os.path.exists(saving_dir):
             os.makedirs(saving_dir)

        fname_save = f'{checking_year}_WS.png'

        fig_title = f'{stations[i]}{nl}{df_ws_combine.iloc[0,0].date()} - {df_ws_combine.iloc[-1,0].date()}, Ta=1h,  wind at 10 m  '
        try:
            scatter_plot_ERA5_against_meas(df_ws_combine, [0, 32], 0.2, fig_title, saving_dir+'\\'+fname_save)
        except:
            logger.error(f'Need to double check the data in {stations[i]}, {checking_year}')

        del wind_obs_1hr
        del era5_wd
        del df_ws_combine
        del obs_all_data
        del wind_data
        del cols_to_load
        del idxs_to_remove
        del era5_u
        del era5_v
             
        # fig_title = f'{stations[i]} ({providers[i]}) wind speed {checking_year}'
        # fname_save = f"{stations[i]}_{providers[i]}_{checking_year}.png"
        # plot_time_series_1var(ws_1hr, time_stamp, '풍속(m/s)', fig_size=[12,3], fig_title=fig_title, fname_save=save_dir+'WS\\'+fname_save)
    

        # rose_plot(wind_data['풍향(deg)'], wind_data['풍속(m/s)'], fig_title=f'{stations[i]} ({providers[i]}) wind rose {checking_year}')
        


#%% Rescaled wind ERA5 with Observations
