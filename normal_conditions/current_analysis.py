'''
- Conduct Current analysis for Normal conditions, using data from all available period for all analyses
1. Ttime series plot of modelled current data at specific location 
2. Rose plot
3. Probability plot
4. Exceedance probability plot



@Author: Le Thi Trang
@Date: April 17, 2026

'''
#%%
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import logging
import os
import seaborn as sb


from datetime import datetime, timedelta

import sys
import os
sys.path.append('D:\\InProbation\\Metocean\\scripts')

import common_processing
import visualizing
import data_loading
import metocean_metadata
import wind_data_processing

from common_processing import *
from visualizing import *
from data_loading import *

from metocean_metadata import *
from wind_data_processing import *


project_dir = 'D:\\InProbation\\Metocean\\'
obs_data_dir = project_dir + 'Data\\Observations\\'


fname_metadata = 'Prerequisite_wind_data_analysis.xlsx'
working_dir = project_dir + 'Analysis\\'

# directory for saving figures in quality control phase
qc_saving_dir = working_dir + 'Obs_quality_filtering\\Current\\time_series_plot\\'

logger = logging.getLogger(__name__)
logging.basicConfig(filename= working_dir +'Wind_analysis log.log', filemode='w', encoding='utf-8', level=logging.INFO)
running_mode = 'analysis' # 'checking' or 'analysis'

#%%  

vars_metadata = pd.read_excel(working_dir + fname_metadata, sheet_name='Current', header=1)
stations = vars_metadata['Name'].dropna()
providers = vars_metadata['Provider'].dropna()
checking_period = vars_metadata['data available'].values[0]
checking_years = np.arange(int(checking_period.split('-')[0]), int(checking_period.split('-')[1])+1, 1)

for i in range(stations):
    type_params = vars_metadata['parameters'][i].split(',')
    type_params = [s.replace(' ', '') for s in type_params]
    type_params = [s for s in type_params if s!='']
    if providers[i] == 'KHOA':
        time_stamp = '관측시간'  
    elif providers[i] == 'KMA':
        time_stamp = '일시'

    for checking_year in checking_years:
        obs_all_data = load_obs_all_data(obs_data_dir, providers[i], stations[i], year=checking_year)
        cols_to_load = [time_stamp]
        for var in type_params:
            for param in list(obs_all_data.columns):
                if var in param.replace('1', '') and var not in cols_to_load:
                    cols_to_load.append(param)

        data_ = obs_all_data[cols_to_load]
        idxs_to_remove = find_duplicate(data_, time_stamp)
        data_.drop(idxs_to_remove, inplace=True)

        vars_type = ['datetime64[s]']
        vars_type.extend(['float'] * (len(cols_to_load) -1))
        data_ = data_.astype(dict(zip(data_.columns, vars_type)))
        data_.iloc[:,1] = data_.iloc[:,1]/100
        data_.rename(columns={'유속(cm/s)': '유속(m/s)'})


        # compute 1hr-averaged 
        data_interval = np.unique(np.diff(data_[time_stamp]))
        data_interval = data_interval[0] / np.timedelta64(1, 'm')
        data_ = quality_control(data_, fixed_qc_criteria, data_interval, stations[i], providers[i], checking_year, logger)
        data_1hr_qc = data_.groupby(pd.Grouper(key=time_stamp, freq="1h")).mean().reset_index()



