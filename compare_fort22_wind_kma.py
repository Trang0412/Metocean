'''
- Compare wind from fort.22 to KMA observation wind for 2002 to 2025 years
1. Compare ERA5 data interpolated to KMA stations using bilinear approach, 'remapbil'command from CDO
2. Extract data from KMA station at exact time of ERA5, for example 12:00 
    As '10 m u/v wind components are generally treated as instantaneous parameters valid at the specified time, not as a 10-minute mean or a 1-hour mean'
    Source: https://forum.ecmwf.int/t/wind-averaging-duration-for-10m-u-component-of-wind/1251/2

3. Skip stations measuring wind at height larger than 20m to match with 10-m height of ERA5


@Author: Le Thi Trang
@Date: May 21, 2026

'''
#%%
import sys
import os
sys.path.append('D:\\InProbation\\Metocean\\scripts')

import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

from data_loading import *
from wind_data_processing import *
from metocean_metadata import *
import logging

#%%
dir_obs = 'D:\\InProbation\\Metocean\\Data\\Observations\\'
dir_era5 = 'D:\\InProbation\\Metocean\\Data\\ERA5\\'
kma_interp_folder = 'kma_stations_interp'
dir_working = 'D:\\InProbation\\Metocean\\Analysis\\fort22_KMA\\'

logger = logging.getLogger(__name__)
logging.basicConfig(filename= dir_working +'compare_fort22_KMA.log', filemode='w', encoding='utf-8', level=logging.WARNING)


obs_metadata = pd.read_excel(f'{dir_obs}KMA_extent\\Observation_Stations_Metadata_All.xlsx', sheet_name='All')
interp_metadata = pd.read_csv(f'{dir_era5}Order_in_kma_extent_interpolation.csv')
years = np.arange(2022, 2026)
kma_ws_name = '풍속(m/s)'
kma_wd_name = '풍향(deg)'
kma_timestamp = '일시'

# skip comparison to station measuring wind at higher than 20 meters
cutoff_wind_obs_height = 20
skipped_stations = ['오륙도_984', '간여암_961', '갈매여_958', '지귀도_960', '이덕서_963', '해수서_959'] # sue to monthly saving data, handle later

# %% Plot time series, rose plot, spectral, scatter plot of wind
# Load in interpolated era5 data for kms stations
for si, station in enumerate(interp_metadata['Station']):
    
    # if station in skipped_stations: continue
    # find anemometer height and Skip station measuring wind at height larger than 20m
    wind_height = obs_metadata[obs_metadata["Station ID"]==int(station.split('_')[1])]['Anemometer (m)'].values[0]
    if wind_height > cutoff_wind_obs_height: 
        logger.warning(f'Skip: {station}, anemometer height {wind_height}')
        continue

    long_term_fort22 = None
    long_term_obs = None
    long_term_bool = True
    # load obs adn fort22 data for each year then concatenate to long-term data
    for yi, year in enumerate(years):
        # load observation kma data, as all kma stations are measured  at less than 20 meter height
        year_obs = load_obs_all_data(dir_obs, 'KMA_extent', station, year)
        if len(year_obs) == 0: 
            logger.warning(f'Skip: {station}, {year}, no observation data')
            continue
        print(f'Processing Obs data from {station} at {year}, anemometer height at {wind_height}' )
        
        # assign as missing value to non continuous time observation data
        year_start_date = pd.Timestamp(f"{year}-01-01", unit='second')
        year_end_date = (pd.Timestamp(year_start_date)+ pd.offsets.YearEnd(0))

        year_obs[kma_timestamp] = pd.to_datetime(year_obs[kma_timestamp]) #default is [ns]
        year_obs = year_obs.set_index(kma_timestamp)
        year_obs = year_obs.loc[year_start_date:year_end_date]

        # reindex to full index range as sometime there is gap in time step in observation data
        data_interval = year_obs.index.diff() / pd.Timedelta(minutes=1)
        data_interval = int(np.min(np.unique(data_interval[~np.isnan(data_interval)]))) # data interval in unit of minute

        if data_interval < 60:
            full_time = pd.date_range(start=year_start_date, end=year_end_date, freq=f'min')
        else:
            full_time = pd.date_range(start=year_start_date, end=year_end_date, freq=f'h')

        # Reindex data to full time series
        year_obs = year_obs.reindex(full_time)
        year_obs.index.name = kma_timestamp
        year_obs = year_obs.reset_index()
        
        # apply quality control
        year_obs_qc = wind_quality_control(year_obs[[kma_timestamp, kma_ws_name, kma_wd_name]], 
                                         fixed_qc_criteria, data_interval, station, 
                                         'KMA_extent', year, logger)
        del year_obs

        # concatenate to long-term data
        if long_term_obs is None:
            long_term_obs = year_obs_qc
        else:
            long_term_obs = pd.concat([long_term_obs, year_obs_qc], ignore_index=True)

        # load interpolated ERA5 data
        [year_u, year_v]= load_era5_wind_data(f'{dir_era5}{kma_interp_folder}\\', 'wind_10m', year=year)

        # if there is no interpolated data 
        if len(year_u.u10[:,si][~np.isnan(year_u.u10[:,si])]) == 0: 
            logger.warning(f'Skip: {station}, {year}, no interpolated fort22 data')
            continue

        print(f'Processing fort22 data from {station} at {year}' )
        if 'valid_time' in list(year_u.dims): year_u = year_u.rename({'valid_time': 'time'})
        if 'valid_time' in list(year_v.dims): year_v = year_v.rename({'valid_time': 'time'})
        
        interp_u = pd.DataFrame(dict({'time': year_u.u10[:,si].time.values, 'u10': year_u.u10[:,si].values}))
        interp_v = pd.DataFrame(dict({'time': year_v.v10[:,si].time.values, 'v10': year_v.v10[:,si].values}))

        year_interp_ws, year_interp_wd = compute_ws_wd_from_u_v(interp_u.u10.values, interp_v.v10.values)
        year_interp_wind = pd.DataFrame(dict({kma_timestamp:interp_u.time, 
                                              kma_ws_name:year_interp_ws,
                                              kma_wd_name:year_interp_wd}))
        # concatenate to long-term data
        if long_term_fort22 is None:
            long_term_fort22 = year_interp_wind
        else:
            long_term_fort22 = pd.concat([long_term_fort22, year_interp_wind], ignore_index=True)
        
        del year_interp_wind
        del year_interp_ws
        del year_interp_wd
        del interp_u
        del interp_v
        del year_u
        del year_v

    if long_term_fort22 is None:
        logger.warning(f'{station}: No fort22 data for whole years in check')
        continue
    if long_term_obs is None:
        logger.warning(f'{station}: No observation data for whole years in check')
        continue

    # convert fort.22 wind data to KST time
    long_term_fort22[kma_timestamp] = pd.DatetimeIndex(long_term_fort22[kma_timestamp] ) + timedelta(hours=9)
    # convert wind speed of observation to 10-m height
    long_term_obs[kma_ws_name] = wind_speed_to_10m_power_law(long_term_obs[kma_ws_name].values, wind_height)
    
    # Compare between long-term obs and long-term fort.22 at hourly interval
    combined_wind = long_term_fort22.set_index(kma_timestamp).join(long_term_obs.set_index(kma_timestamp), 
                                                                   how='inner', lsuffix='_fort22', rsuffix='_obs').dropna()
    # reindex to full time
    long_term_start_date = pd.Timestamp(f"{combined_wind.index[0].year}-01-01", unit='second')
    long_term_end_date = pd.Timestamp(year=year, month=12, day=31, unit='second')
    full_time = pd.date_range(start=long_term_start_date, end=long_term_end_date, freq=f'h')
    combined_wind = combined_wind.reindex(full_time)
    combined_wind.index.name = kma_timestamp
    combined_wind = combined_wind.reset_index()

    # plot and save data
    os.makedirs(f'{dir_working}{station}', exist_ok=True)
    if len(combined_wind)<(len(long_term_fort22)/2): long_term_bool=False

    long_term_obs_match = combined_wind[[kma_timestamp, f'{kma_ws_name}_obs', f'{kma_wd_name}_obs']]
    long_term_obs_match = long_term_obs_match.rename(columns={f'{kma_ws_name}_obs':kma_ws_name, f'{kma_wd_name}_obs':kma_wd_name})

    long_term_fort22_match = combined_wind[[kma_timestamp, f'{kma_ws_name}_fort22', f'{kma_wd_name}_fort22']]
    long_term_fort22_match = long_term_fort22_match.rename(columns={f'{kma_ws_name}_fort22':kma_ws_name, f'{kma_wd_name}_fort22':kma_wd_name})
    fname_save = f'{year}_wind_rose.png'
    fig_title = f'{station}, fort.22 vs. Observations<br>{long_term_fort22_match.iloc[0,0].date()} - {long_term_fort22_match.iloc[-1,0].date()}'
    lg_title1 = f'Observations<br>N={len(long_term_obs_match)}<br>WS<sub>10m</sub>[m/s]<br>WD[{chr(176)}N-from]'
    lg_title2 = f'fort.22<br>N={len(long_term_fort22_match)}<br>WS<sub>10m</sub>[m/s]<br>WD[{chr(176)}N-from]'
    dual_rose_plot(long_term_obs_match, long_term_fort22_match,
                   lg_title1=lg_title1, lg_title2=lg_title2,
                   speed_name=kma_ws_name, dir_name=kma_wd_name, 
                   fig_title=fig_title, fname_save=f'{dir_working}{station}\\{fname_save}')
    
    # extract wind speed for time series and scatter plot, columns of [Time, Observation, ERA5]
    combined_ws = combined_wind[[kma_timestamp, f'{kma_ws_name}_fort22',f'{kma_ws_name}_obs']].iloc[:,[0,2,1]]
    fname_save = f'{year}_time_series_DHI_style.png'
    fig_title = f'{station}, fort.22 vs. Observations{nl}{combined_wind.iloc[0,0].date()} - {combined_wind.iloc[-1,0].date()}'
    plot_time_series_2vars(combined_ws, 'Observations', 'fort22', [12,3], fig_title,f'{dir_working}{station}\\{fname_save}',
                    fc1='#808080', fc2='#3C88BD', plot_type='DHI', lstyle1 = '-', lstyle2='--',
                    ylabel_text=kma_ws_name, xtick_rotation=0, long_term=True)
    fname_save = f'{year}_time_series_MIT_style.png'
    plot_time_series_2vars(combined_ws, 'Observations', 'fort22', [12,3], fig_title,f'{dir_working}{station}\\{fname_save}',
                fc1='#F67A0D', fc2='#3C88BD', plot_type='MIT', lstyle1 = '-', lstyle2='--', 
                ylabel_text=kma_ws_name, xtick_rotation=0, long_term=True)
    # if long_term_bool:
    #     fname_save = f'{year}_time_series.png'
    #     scatter_plot_ERA5_against_meas(combined_ws, [9,6], [0, np.max([32, combined_ws.iloc[:,1].max()+2, combined_ws.iloc[:,2].max()+2])], 
    #                                                             0.2, fig_title, f'{dir_working}{station}\\{fname_save}')
    # else: # plot separately for each month as observation recorded at 
    #     pass

    # delete temporary variables
    del long_term_obs_match
    del long_term_fort22_match
    del combined_ws
    del long_term_obs 
    del long_term_fort22
    #saving combined wind
    combined_wind.to_csv(f'{dir_working}{station}\\combined_wind.csv')
    del combined_wind

logger.warning('--------------Fininsed without error-------------')
   #%% TODO: (May 22, 2026) Plot contour on mesh domain 
