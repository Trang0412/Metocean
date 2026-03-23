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
from datetime import datetime, timedelta

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

# directory for saving figures in quality control phase
qc_saving_dir = working_dir + 'Obs_quality_filtering\\Wind\\time_series_plot\\'

logger = logging.getLogger(__name__)
logging.basicConfig(filename= working_dir +'Wind_analysis log.log', filemode='w', encoding='utf-8', level=logging.INFO)
nl  = '\n'

era5_type = 'windfield_0.05' # korea_0.25, windfield_0.05
analysis_saving_dir = working_dir + 'ERA5_vs_Obs\\' + era5_type
if not os.path.exists(analysis_saving_dir):
    os.makedirs(analysis_saving_dir)

running_mode = 'analysis' # 'checking' or 'analysis'


#%%  1. Original ERA5 with Observations

vars_metadata = pd.read_excel(working_dir + fname_metadata, sheet_name='ERA5_wind_obs', header=1)
stations = vars_metadata['Name'].dropna()
providers = vars_metadata['Provider'].dropna()

skipping_stations =['중문해수욕장']

for checking_year in range(longest_checking_duration_wind[0],longest_checking_duration_wind[1]):
    print(f'===================== Process data year {checking_year} ====================')
    if running_mode == 'analysis':
        print(f'====================== Loading ERA5 data ======================')
        if era5_type == 'korea_0.25':
            # Load ERA5 orignal data. 
            # data loadded in xarray.Dataset
            [era5_u, era5_v]= load_era5_wind_data(era5_data_dir + era5_type +'\\', 'wind_10m', year=checking_year)
        elif era5_type == 'windfield_0.05':
            # Load regrided ERA5 data
            try:
                era5_ws_all_locs = load_era5_regrid_wind_data(era5_data_dir + era5_type, year=checking_year)
            except:
                logger.error(f'{pd.Timestamp.today().date} Loading data error: Cannot load regrided ERA5 for {checking_year}')
        
    for i in range(len(stations)):
        print(f'====================== Loading Observation data ======================')
        if stations[i] not in skipping_stations: continue

        checking_duration = vars_metadata['Wind data available'][i].split('-')
        checking_period = list(np.arange(int(checking_duration[0]), int(checking_duration[1])))
        
        if checking_year not in checking_period: continue
        type_params = vars_metadata['Wind parameters'][i].split(',')
        type_params = [s.replace(' ', '') for s in type_params]
        type_params = [s for s in type_params if s!='']

        if providers[i] == 'KHOA':
            time_stamp = '관측시간'
            
        elif providers[i] == 'KMA':
            time_stamp = '일시'
            
        ####################################################################################
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
        
        # compute 1hr-averaged 
        wind_obs_1hr = wind_data.groupby(pd.Grouper(key=time_stamp, freq="1h")).mean().reset_index()
        
        # quality control
        wind_data = quaility_control(wind_data, fixed_qc_criteria, vars_metadata['Data inteval (min)'][i], stations[i], providers[i], checking_year, logger)

        # compute 1hr-averaged 
        wind_obs_1hr_qc = wind_data.groupby(pd.Grouper(key=time_stamp, freq="1h")).mean().reset_index()

        # Mar 18, 2026: Convert to 10-m height 
        wind_obs_1hr_qc['풍속(m/s)'] = wind_speed_to_10m_power_law(wind_obs_1hr_qc['풍속(m/s)'].values, vars_metadata['Anemometer height'][i])
        
        if running_mode == "analysis":
            # skip analysis when more than 6 months of data are missed
            if wind_obs_1hr_qc['풍속(m/s)'].isna().sum() > (len(wind_obs_1hr)/2):  
                logger.info(f'{pd.Timestamp.today().date} Excessive missing values detected: {stations[i]}_{providers[i]}, {checking_year} more than 6 months of wind speed -> skip')
                continue
            if era5_type == 'korea_0.25':
                era5_ws, era5_wd = compute_ws_wd_from_u_v(era5_u.sel(latitude=vars_metadata['Latitude'][i], longitude=vars_metadata['Longitude'][i], method='nearest').u10.values, 
                                                            era5_v.sel(latitude=vars_metadata['Latitude'][i], longitude=vars_metadata['Longitude'][i], method='nearest').v10.values)
                era5_ws = pd.DataFrame(era5_ws, columns=['풍속(m/s)'])
                # era5_wd = pd.DataFrame(era5_wd, columns=['풍향(deg)'])
                try:
                    era5_ws[time_stamp] = era5_u.valid_time.values
                    # era5_wd[time_stamp] = era5_u.valid_time.values
                except:
                    era5_ws[time_stamp] = era5_u.time.values
                    # era5_wd[time_stamp] = era5_u.time.values

                era5_ws = era5_ws.iloc[:, [1,0]]

                # Mar 18, 2026: Convert ERA5 data to KST time
                era5_ws[time_stamp] = pd.DatetimeIndex(era5_ws[time_stamp]) + timedelta(hours=9)
                # era5_wd[time_stamp] = pd.DatetimeIndex(era5_wd[time_stamp]) + timedelta(hours=9)

            elif era5_type == 'windfield_0.05':
                era5_ws = era5_ws_all_locs.sel(Lat=vars_metadata['Latitude'][i], Lon=vars_metadata['Longitude'][i], method='nearest').Wind
                
                # assign time index to era5_ws data in UTC
                era5_ws = pd.DataFrame(era5_ws, columns=['풍속(m/s)'])
                era5_ws.insert(0, time_stamp, pd.date_range(start=f'{checking_year}-01-01', end=f'{checking_year+1}-01-01', freq='h', inclusive='left'), allow_duplicates=False)
                
                # Convert ERA5 data to KST time
                era5_ws[time_stamp] = pd.DatetimeIndex(era5_ws[time_stamp]) + timedelta(hours=9)

            ####################################################################################
            # Comparison between Observation with ERA5 
            # yearly comparison
            df_ws_combine = pd.merge(wind_obs_1hr_qc[[time_stamp, '풍속(m/s)']], era5_ws, on=time_stamp, how='right', suffixes=['_obs', '_era5'])

            scatter_saving_dir = analysis_saving_dir + '\\scatter_plot\\' + stations[i] + '_' + providers[i] 
            ts_saving_dir = analysis_saving_dir + '\\time_series_plot\\' + stations[i] + '_' + providers[i] 
            
            if not os.path.exists(scatter_saving_dir):
                os.makedirs(scatter_saving_dir)
            if not os.path.exists(ts_saving_dir):
                os.makedirs(ts_saving_dir)

            fname_save = f'{checking_year}_WS.png'
            fig_title = f'{stations[i]}{nl}{df_ws_combine.iloc[0,0].date()} - {df_ws_combine.iloc[-1,0].date()}, Ta=1h '

            try:
                plot_time_series_2vars(df_ws_combine, 'Observation', 'ERA5', [12, 3], fig_title, ts_saving_dir+'\\'+fname_save)
                scatter_plot_ERA5_against_meas(df_ws_combine, [9,6], [0, np.max([32, df_ws_combine.iloc[:,1].max()+2, df_ws_combine.iloc[:,2].max()+2])], 
                                                                        0.2, fig_title, scatter_saving_dir+'\\'+fname_save)
            except:
                logger.error(f'{pd.Timestamp.today().date} Time series and/or scatter plot are not successfully finished for {stations[i]}, {checking_year}')

            ####################################################################################
            #TODO: Wind spectral comparison between Observation with ERA5 
            fname_save = f'Spectral comparison of ERA5 and measured WS'
            fig_title = f'{stations[i]}_{providers[i]}{nl}Temporal Average {df_ws_combine.iloc[0,0].date()} - {df_ws_combine.iloc[-1,0].date()}'
            spectra_comparison(df_ws_combine, 3600, fig_title)

            try:
                del era5_wd
            except:
                pass
            del era5_ws
            del df_ws_combine


        ####################################################################################
        # Plot time series of observation data before and after QC
        elif running_mode == 'checking':
            plot_saving_dir = qc_saving_dir+stations[i]+'_'+providers[i]+'\\'
            if not os.path.exists(plot_saving_dir):
                os.makedirs(plot_saving_dir)

            fname_save = plot_saving_dir + f'{checking_year}_WS.png'
            fig_title = f'{stations[i]}{nl}{wind_obs_1hr.iloc[0,0].date()} - {wind_obs_1hr.iloc[-1,0].date()}, Ta=1h '
            plot_time_series_1var(wind_obs_1hr, time_stamp, '풍속(m/s)', fig_size=[9, 3], fig_title=fig_title, fname_save=fname_save)
            
            fname_save = plot_saving_dir + f'{checking_year}_WD.png'
            fig_title = f'{stations[i]}{nl}{wind_obs_1hr.iloc[0,0].date()} - {wind_obs_1hr.iloc[-1,0].date()}, Ta=1h '
            plot_time_series_1var(wind_obs_1hr, time_stamp, '풍향(deg)', fig_size=[9, 3], fig_title=fig_title, fname_save=fname_save)


            fname_save = plot_saving_dir + f'{checking_year}_WS_QC.png'
            fig_title = f'{stations[i]}{nl}{wind_obs_1hr_qc.iloc[0,0].date()} - {wind_obs_1hr_qc.iloc[-1,0].date()}, Ta=1h, QC '
            plot_time_series_1var(wind_obs_1hr_qc, time_stamp, '풍속(m/s)', fig_size=[9, 3], fig_title=fig_title, fname_save=fname_save, face_color="#008080")
            
            fname_save = plot_saving_dir + f'{checking_year}_WD_QC.png'
            fig_title = f'{stations[i]}{nl}{wind_obs_1hr_qc.iloc[0,0].date()} - {wind_obs_1hr_qc.iloc[-1,0].date()}, Ta=1h, QC '
            plot_time_series_1var(wind_obs_1hr_qc, time_stamp, '풍향(deg)', fig_size=[9, 3], fig_title=fig_title, fname_save=fname_save, face_color="#A9561E")

        del wind_obs_1hr
        del obs_all_data
        del wind_data
        del cols_to_load
        del idxs_to_remove
        del wind_obs_1hr_qc




#%% Rescaled wind ERA5 with Observations
