'''
- Conduct WAVE analysis
1. Compare observation wave data with modeled data


@Author: Le Thi Trang
@Date: Mar 24, 2026

'''
#%%

import sys
import os
sys.path.append('D:\\InProbation\\Metocean\\scripts')

import common_processing
import visualizing
import data_loading
import metocean_metadata
import wind_data_processing


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
modeled_data_name = 'simulation_July2023\\'
year = 2023

dir_fig_save = dir_analysis + 'Obs_Modeled\\Wave\\' + modeled_data_name
if not os.path.exists(dir_fig_save):
    os.makedirs(dir_fig_save)


# origmesh_site_bathymetry_v1
modeled_all_vars = ['Time', 'Hsig', 'Dir', 'Tm_10', 'RTpeak', 'Tm01', 'Tm02', 'Depth', 'Watlev', 'X-Vel', 'Y-Vel', 'X-Windv', 'Y-Windv', 'PkDir', 'Dspr']
modeled_vars_type = ['string', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float']


model_locs = {'Buoy1': '구엄', 'Buoy2': '우도', 'Buoy3': '하도', 'Buoy4': '김녕'}  # all from KMA
wave_period_var = 'Tm_10'
wl_var = 'Watlev'

subfolders = [x for x in Path(dir_modeled_data+modeled_data_name).iterdir() if x.is_dir()]

#%% load modeled data
for checking_loc in model_locs:
    if checking_loc=='Buoy1': continue # May 21, skip Guom for now

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

    # Mar 30
    if checking_loc == 'Buoy1':
        obs_data = pd.read_csv(dir_obs_data + 'KMA\\구엄\\OBS_CWBUOY_TIM_20260330112010.csv', sep=',', header=0, encoding='cp949')

    else:
        obs_data = load_obs_all_data(dir_obs_data, 'KMA', model_locs[checking_loc], year)

    if '파향(deg)' in obs_data.columns:
        # vars_to_check = ['Time', 'Hsig', 'Tm_10', 'Dir']
        vars_to_check = ['Time', 'Hsig', wave_period_var, 'Dir']
        vars_type=['datetime64[ns]', 'float', 'float', 'float']
        wave_params = [kma_timestamp, '유의파고(m)', '파주기(sec)', '파향(deg)']

        water_params = [kma_timestamp, ]
    else:
        vars_to_check = ['Time', 'Hsig', wave_period_var]
        vars_type=['datetime64[ns]', 'float', 'float']
        wave_params = [kma_timestamp, '유의파고(m)', '파주기(sec)']


    obs_wave = obs_data[wave_params].astype(dict(zip(wave_params, vars_type)))
    data_interval = np.unique(np.diff(obs_wave[kma_timestamp]))
    data_interval = data_interval[0] / np.timedelta64(1, 'm') # convert to minute, assuming data are recoreded with same interval for whole year period
       

    obs_wave_qc = wave_quality_control(obs_wave, fixed_qc_criteria, data_interval)
    obs_wave_1hr = obs_wave.groupby(pd.Grouper(key=kma_timestamp, freq="1h")).mean().reset_index()

    # change time of modeled data
    # Mar 31: Output of modeled is UTC time => move modeled to 9hours forward
    # name_postfix = ['_minus_9hour', '' , '_plus_9hour']
    name_postfix= ['']
    for ti, deltat in enumerate([9]):
        modeled_wave = modeled_data[vars_to_check]
        modeled_wave.rename(columns=dict(zip(vars_to_check, wave_params)), inplace=True)

        ####################################################################################
        # Comparison between Observation with Modeled data 
        # correct to KST time, 9h head
        modeled_wave[kma_timestamp] = pd.DatetimeIndex(modeled_wave[kma_timestamp]) + timedelta(hours=deltat)
        df_wave_combine = pd.merge(obs_wave_1hr, modeled_wave, on=kma_timestamp, how='right', suffixes=['_obs', '_modeled'])


        for param_checking in wave_params[1:]:
            print(param_checking)
            if '파주기' in param_checking:
                fname_save = f'{checking_loc}_{param_checking}_{wave_period_var}{name_postfix[ti]}'
                ylabel_text = 'Tp [s]'
            else: 
                fname_save = f'{checking_loc}_{param_checking}{name_postfix[ti]}'
                ylabel_text = 'Hs [m]'
            fig_title = f'{checking_loc} ({model_locs[checking_loc]}) {df_wave_combine.iloc[0,0].date()} - {df_wave_combine.iloc[-1,0].date()}{name_postfix[ti]}'
            plot_time_series_2vars(df_wave_combine[[kma_timestamp, param_checking+'_obs', param_checking+'_modeled']],
                                    'Observation', 'Modeled', [9, 4], fig_title, dir_fig_save + '\\'+ fname_save,
                                    fc1='#F67A0D', fc2='#3C88BD', plot_type='MIT', lstyle1 = '-', lstyle2='--',
                                    ylabel_text=ylabel_text, xtick_rotation=45)
            # scatter_plot_ERA5_against_meas(df_wave_combine[[kma_timestamp, param_checking+'_obs', param_checking+'_modeled']], 
            #                                [9,6], [0, np.max([10, df_wave_combine.iloc[:,1].max()+5, df_wave_combine.iloc[:,2].max()+5])], 
            #                                bin_width=0.1, x_tick=1, fig_title=fig_title, fname_save = dir_fig_save + '\\'+ fname_save+'_scatter')

        del modeled_wave

# %%

# %%
