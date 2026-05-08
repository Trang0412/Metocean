'''
- Conduct WIND analysis
1. Compare original ERA5 wind data with observation data
2. Compare rescaled ERA5 wind data with observation data
3. Compare WRF wind data with Observation? (optional)

@Author: Le Thi Trang
@Date: Mar 10, 2026

'''
#%%
import sys
import os
sys.path.append('D:\\InProbation\\Metocean\\scripts')

import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

import os
import seaborn as sb

import logging
from datetime import datetime, timedelta

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


era5_type = 'korea_0.25' # korea_0.25, windfield_0.05
analysis_saving_dir = working_dir + 'ERA5_vs_Obs\\' + era5_type
if not os.path.exists(analysis_saving_dir):
    os.makedirs(analysis_saving_dir)

running_mode = 'analysis' # 'checking' or 'analysis'

#%%  1. Original ERA5 with Observations

vars_metadata = pd.read_excel(working_dir + fname_metadata, sheet_name='ERA5_wind_obs', header=1)

stations = vars_metadata['Name'].dropna()
providers = vars_metadata['Provider'].dropna()


#%% plot location of stations for wind checking (ERA5 vs. Regrided ERA5) and Jeju (PC1, PC2)

# bounding_area = {'lat':[33, 34.25], 'lon':[126, 127.75]}
# compare_statn = '성산포_KHOA'

# plot_nearest_point_era5_regrid_era5(bounding_area, vars_metadata, compare_statn, era5_coor, regrid_era5_coor )


#%%

# checking_stations =['추자도']
for checking_year in range(longest_checking_duration_wind[0],longest_checking_duration_wind[1]):
    print(f'===================== Process data year {checking_year} ====================')
    if running_mode == 'analysis':
        print(f'====================== Loading ERA5 data ======================')
        if era5_type == 'korea_0.25':
            [era5_u, era5_v]= load_era5_wind_data(era5_data_dir + era5_type +'\\', 'wind_10m', year=checking_year)
        elif era5_type == 'windfield_0.05':
            try:
                era5_ws_all_locs = load_era5_regrid_wind_data(era5_data_dir + era5_type, year=checking_year)
            except:
                logger.error(f'{pd.Timestamp.today().date} Loading data error: Cannot load regrided ERA5 for {checking_year}')
        
    for i in range(len(stations)):

        # for checking specific stations
        # if (stations[i] not in checking_stations) or (providers[i]!='KHOA'): continue

        # checking_duration = vars_metadata['Wind data available'][i].split('-')
        # checking_period = list(np.arange(int(checking_duration[0]), int(checking_duration[1])))
        
        # if checking_year not in checking_period: continue
        type_params = vars_metadata['Wind parameters'][i].split(',')
        type_params = [s.replace(' ', '') for s in type_params]
        type_params = [s for s in type_params if s!='']

        if providers[i] == 'KHOA':
            time_stamp = '관측시간'
            
        elif providers[i] == 'KMA':
            time_stamp = '일시'
            
        ####################################################################################
        # compute ERA5 data for specific location
        if era5_type == 'korea_0.25':
            era5_ws, era5_wd = compute_ws_wd_from_u_v(era5_u.sel(latitude=vars_metadata['Latitude'][i], longitude=vars_metadata['Longitude'][i], method='nearest').u10.values, 
                                                        era5_v.sel(latitude=vars_metadata['Latitude'][i], longitude=vars_metadata['Longitude'][i], method='nearest').v10.values)
            era5_ws = pd.DataFrame(era5_ws, columns=['풍속(m/s)'])
            era5_wd = pd.DataFrame(era5_wd, columns=['풍향(deg)'])
            try:
                era5_ws[time_stamp] = era5_u.valid_time.values
                era5_wd[time_stamp] = era5_u.valid_time.values
            except:
                era5_ws[time_stamp] = era5_u.time.values
                era5_wd[time_stamp] = era5_u.time.values
            era5_ws = era5_ws.iloc[:, [1,0]]
            era5_ws[time_stamp] = pd.DatetimeIndex(era5_ws[time_stamp]) + timedelta(hours=9)
            era5_wd[time_stamp] = pd.DatetimeIndex(era5_wd[time_stamp]) + timedelta(hours=9)
            
        elif era5_type == 'windfield_0.05':
            era5_ws = era5_ws_all_locs.sel(Lat=vars_metadata['Latitude'][i], Lon=vars_metadata['Longitude'][i], method='nearest').Wind 
            # assign time index to era5_ws data in UTC
            era5_ws = pd.DataFrame(era5_ws, columns=['풍속(m/s)'])
            era5_ws.insert(0, time_stamp, pd.date_range(start=f'{checking_year}-01-01', end=f'{checking_year+1}-01-01', freq='h', inclusive='left'), allow_duplicates=False)
            # Convert ERA5 data to KST time
            era5_ws[time_stamp] = pd.DatetimeIndex(era5_ws[time_stamp]) + timedelta(hours=9)

        ####################################################################################
        # loading observation data
        obs_all_data = load_obs_all_data(obs_data_dir, providers[i], stations[i], year=checking_year)
        if obs_all_data.empty: continue
        print(f'====================== Loaded {stations[i]}, {providers[i]} data ======================')
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
        wind_obs_1hr = wind_data.groupby(pd.Grouper(key=time_stamp, freq="1h")).mean().reset_index() # for checking

        # compute 1hr-averaged 
        data_interval = np.unique(np.diff(wind_data[time_stamp]))
        data_interval = data_interval[0] / np.timedelta64(1, 'm') # convert to minute, assuming data are recoreded with same interval for whole year period
        wind_data = quality_control(wind_data, fixed_qc_criteria, vars_metadata['Data inteval (min)'][i], stations[i], providers[i], checking_year, logger)
        wind_obs_1hr_qc = wind_data.groupby(pd.Grouper(key=time_stamp, freq="1h")).mean().reset_index()

        # Mar 18, 2026: Convert to 10-m height 
        wind_obs_1hr_qc['풍속(m/s)'] = wind_speed_to_10m_power_law(wind_obs_1hr_qc['풍속(m/s)'].values, vars_metadata['Anemometer height'][i])
        
        
        if running_mode == "analysis":
            # skip analysis when more than 6 months of data are missed
            if wind_obs_1hr_qc['풍속(m/s)'].isna().sum() > (len(wind_obs_1hr)/2):  
                logger.info(f'{pd.Timestamp.today().date} Excessive missing values detected: {stations[i]}_{providers[i]}, {checking_year} more than 6 months of wind speed -> skip')
                continue

            ####################################################################################
            # # Wind rose plot
            # wind_rose_dir = working_dir + 'ERA5_vs_Obs\\Obs\\wind_rose\\' + stations[i] + '_' + providers[i] 
            # if not os.path.exists(wind_rose_dir):
            #     os.makedirs(wind_rose_dir)
            # fname_save = f'{checking_year}.png'
            # fig_title = f'Observation data, {stations[i]}{nl}{wind_obs_1hr_qc.iloc[0,0].date()} - {wind_obs_1hr_qc.iloc[-1,0].date()}, Ta=1h '
            # wind_rose_plot(wind_obs_1hr_qc, speed_name='풍속(m/s)', dir_name='풍향(deg)', 
            #                fig_title=fig_title, fname_save=wind_rose_dir +'\\'+fname_save, speed_step=2, dir_step=30, calm_limit=2)
            ####################################################################################
            # Dual wind rose plot
            era5 = pd.merge(era5_ws, era5_wd, how='right', on=time_stamp)
            dual_rose_dir = working_dir + 'ERA5_vs_Obs\\' +era5_type+ '\\dual_rose\\' + stations[i] + '_' + providers[i] + '\\'
            if not os.path.exists(dual_rose_dir):
                os.makedirs(dual_rose_dir)
            fname_save = f'{era5_type}_measurement, {checking_year}.png'
            fig_title = f'Wind data, {era5_type} vs. Measurements {nl} {stations[i]}{nl}{wind_obs_1hr_qc.iloc[0,0].date()} - {wind_obs_1hr_qc.iloc[-1,0].date()}, Ta=1h '
            dual_rose_plot(wind_obs_1hr_qc, era5, lg_title1='Measurements', lg_title2='ERA5',
                   speed_name='풍속(m/s)', dir_name='풍향(deg)', 
                   fig_title=fig_title, fname_save=dual_rose_dir + fname_save)


            ####################################################################################
            # Comparison between Observation with ERA5 
            # yearly comparison
            df_ws_combine = pd.merge(wind_obs_1hr_qc[[time_stamp, '풍속(m/s)']], era5_ws, on=time_stamp, how='right', suffixes=['_obs', '_era5'])

            # time series based comparisons
            scatter_saving_dir = analysis_saving_dir + '\\scatter_plot\\' + stations[i] + '_' + providers[i] 
            ts_saving_dir = analysis_saving_dir + '\\time_series_plot\\' + stations[i] + '_' + providers[i] 
            if not os.path.exists(scatter_saving_dir):
                os.makedirs(scatter_saving_dir)
            if not os.path.exists(ts_saving_dir):
                os.makedirs(ts_saving_dir)
            fname_save = f'{checking_year}_WS.png'
            fig_title = f'{stations[i]}{nl}{df_ws_combine.iloc[0,0].date()} - {df_ws_combine.iloc[-1,0].date()}, Ta=1h '

            try:
                plot_time_series_2vars(df_ws_combine,
                    'Observation', 'ERA5', [12,3], fig_title, ts_saving_dir+'\\'+fname_save,
                    fc1='#808080', fc2='#3C88BD', plot_type='DHI', lstyle1 = '-', lstyle2='--',
                    ylabel_text='풍속(m/s)', xtick_rotation=0)
                        
                # plot_time_series_2vars(df_ws_combine, 'Observation', 'ERA5', [12, 3], fig_title, ts_saving_dir+'\\'+fname_save)
                scatter_plot_ERA5_against_meas(df_ws_combine, [9,6], [0, np.max([32, df_ws_combine.iloc[:,1].max()+2, df_ws_combine.iloc[:,2].max()+2])], 
                                                                        0.2, fig_title, scatter_saving_dir+'\\'+fname_save)
            except:
                logger.error(f'{pd.Timestamp.today().date} Time series and/or scatter plot are not successfully finished for {stations[i]}, {checking_year}')

            ####################################################################################
            # spectral comparison
            spectral_saving_dir = analysis_saving_dir + '\\spectral_plot\\' + stations[i] + '_' + providers[i] 
            if not os.path.exists(spectral_saving_dir):
                os.makedirs(spectral_saving_dir)
            fname_save = f'{checking_year}_spectral.png'
            fig_title = f'{stations[i]}_{providers[i]}{nl}Temporal Average {df_ws_combine.iloc[0,0].date()} - {df_ws_combine.iloc[-1,0].date()}'
            # plot_wind_spectra_comparison(df_ws_combine, 3600, fig_title, f_ref=1e-5, fname_save=spectral_saving_dir+'\\'+fname_save)
            try:
                plot_wind_spectra_comparison(df_ws_combine, 3600, fig_title, f_ref=1e-5, fname_save=spectral_saving_dir+'\\'+fname_save)
            except:
                logger.error(f'{pd.Timestamp.today().date} Spectral plot are not successfully finished for {stations[i]}, {checking_year}')

            try:
                del era5_ws
                del df_ws_combine
                del era5_wd
            except:
                pass

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
