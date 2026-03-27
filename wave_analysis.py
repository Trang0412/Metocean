'''
- Conduct WAVE analysis
1. Compare observation wave data with modeled data


@Author: Le Thi Trang
@Date: Mar 24, 2026

'''
#%%
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import glob
import re

import os
import seaborn as sb

import logging
from datetime import datetime, timedelta

from common_processing import *
from visualizing import *
from data_loading import *

from metocean_metadata import *
from wind_data_processing import *


#%%
dir_modeled_data = dir_data + 'Modeled\\'
dir_obs_data = dir_data + 'Observations\\'
modeled_data_name = 'origmesh_site_bathymetry_v1\\simulation_260324\\'


dir_fig_save = dir_analysis + 'Obs_Modeled\\Wave\\' + modeled_data_name
if not os.path.exists(dir_fig_save):
    os.makedirs(dir_fig_save)


model_locs = {'Buoy1': '구엄', 'Buoy2': '우도', 'Buoy3': '하도', 'Buoy4': '김녕'}  # all from KMA
wave_period_var = 'Tm_10'

subfolders = [x for x in Path(dir_modeled_data+modeled_data_name).iterdir() if x.is_dir()]

#%%
# load modeled data
for checking_loc in model_locs:

    modeled_data = pd.DataFrame(columns=modeled_all_vars)

    for checking_folder in subfolders:
        # matching_files = list(Path(dir_modeled_data + modeled_data_name).glob(f'{checking_loc}_hot*'))
        # modeled_data = pd.DataFrame(columns=modeled_all_vars)

        clean_lines = []
        loading_file = f'{checking_folder}\\{checking_loc}.out'
        with open(loading_file, "r", encoding="utf-8") as f:
            for line in f:
                # replace all whitespace-like chars with single space
                line = re.sub(r"\s+", " ", line.strip())
                clean_lines.append(line)

            data = pd.read_csv(
                pd.io.common.StringIO("\n".join(clean_lines)),
                sep=" ", index_col=False,
                header=None, skiprows=7, names=modeled_all_vars, dtype=dict(zip(modeled_all_vars, modeled_vars_type)))

            # convert 1st colum to datetime
            data['Time'] = data['Time'].apply(lambda x: pd.to_datetime(datetime(year=int(x[0:4]), month=int(x[4:6]), day=int(x[6:8]), hour=int(x[9:11]))))
            modeled_data = pd.concat([modeled_data, data], ignore_index=True).drop_duplicates(subset=['Time'], keep='first')
            del data

    obs_data = load_obs_all_data(dir_obs_data, 'KMA', model_locs[checking_loc],2025)

    if '파향(deg)' in obs_data.columns:
        # vars_to_check = ['Time', 'Hsig', 'Tm_10', 'Dir']
        vars_to_check = ['Time', 'Hsig', wave_period_var, 'Dir']
        vars_type=['datetime64[ns]', 'float', 'float', 'float']
        wave_params = [kma_timestamp, '유의파고(m)', '파주기(sec)', '파향(deg)']
    else:
        vars_to_check = ['Time', 'Hsig', wave_period_var]
        vars_type=['datetime64[ns]', 'float', 'float']
        wave_params = [kma_timestamp, '유의파고(m)', '파주기(sec)']

    modeled_wave = modeled_data[vars_to_check]
    modeled_wave.rename(columns=dict(zip(vars_to_check, wave_params)), inplace=True)
    # correct to 9h head
    modeled_wave[kma_timestamp] = pd.DatetimeIndex(modeled_wave[kma_timestamp]) + timedelta(hours=-9)

    obs_wave = obs_data[wave_params].astype(dict(zip(wave_params, vars_type)))
    # obs_wave_qc = quality_control(obs_wave)

    obs_wave_1hr = obs_wave.groupby(pd.Grouper(key=kma_timestamp, freq="1h")).mean().reset_index()

    ####################################################################################
    # Comparison between Observation with Modeled data 
    df_wave_combine = pd.merge(obs_wave_1hr, modeled_wave, on=kma_timestamp, how='right', suffixes=['_obs', '_modeled'])


    for param_checking in wave_params[1:]:
        print(param_checking)
        if '파주기' in param_checking:
            fname_save = f'{checking_loc}_{param_checking}_{wave_period_var}_minus_9hour'
        else: 
            fname_save = f'{checking_loc}_{param_checking}_minus_9hour'
        fig_title = f'{checking_loc} ({model_locs[checking_loc]}) {df_wave_combine.iloc[0,0].date()} - {df_wave_combine.iloc[-1,0].date()} - 9hrs'
        plot_time_series_2vars(df_wave_combine[[kma_timestamp, param_checking+'_obs', param_checking+'_modeled']], 'Observation', 'Modeled', 
                            [12, 3], fig_title, dir_fig_save + '\\'+ fname_save)
        # scatter_plot_ERA5_against_meas(df_wave_combine[[kma_timestamp, param_checking+'_obs', param_checking+'_modeled']], 
        #                                [9,6], [0, np.max([32, df_wave_combine.iloc[:,1].max()+5, df_wave_combine.iloc[:,2].max()+5])], 
        #                                bin_width=0.2, fig_title=fig_title, fname_save = dir_fig_save + '\\'+ fname_save)


# %%
def quality_control(data, fixed_qc_criteria, data_interval, station='', provider='', checking_year=''):
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
# %%
