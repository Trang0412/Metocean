'''
Loading raw wind data from ERA5 dataset
Compute Wind direction and Wind speed from u,v-component of wind


@Author: Le Thi Trang
@Date: Jan 21, 2026
'''
#%%
import numpy as np
import os
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import geopy
import math
from compute_variables import *
from find_nearest_location import *

from plot_data import *


# loading stations' name and coordinate
path_station = 'D:\\InProbation\\Metocean_Jeju\\Observation_points\\'
file_coord = 'Model calibration and validation.xlsx'
chosen_stations = pd.read_excel(path_station + file_coord, sheet_name='Stations')


#%% Working with grib file now, checking only data from 1976-1978 
##############################################################################
# path_data = 'D:\\InProbation\\Metocean_Jeju\\Data\\wind_era5\\medium_area\\'

# data_files = []
# for filename in os.listdir(path_data):
#     if '.grib' in filename:
#         full_name = os.path.join(path_data, filename)
#         data_files.append(full_name)

# era5_wind = xr.open_dataset(path_data + "wind_1979_1980.grib", engine="cfgrib")


#%% Working with netCDF file now, Jan 22, 2026
##############################################################################
path_data = 'D:\\InProbation\\Metocean_Jeju\\Data\ERA5\\ERA5_test\\pacific\\'
era5_wind = xr.open_dataset(path_data + "ERA5_197401_reduced_pacific.nc")

checking_loc_coor = [[33.5,126.5], [33.5, 126.75], [33.5, 127]]
# checking location at (33.5, 126.5) at the current moment
loc_data = era5_wind.sel(latitude=33.5, longitude=126.5)


#%% compute wind speed from u,v component
loc_ws10, loc_wd10 = compute_ws_wd_from_u_v(loc_data.u10.values, loc_data.v10.values)
# all_ws100, all_wd100 = compute_ws_wd_from_u_v(era5_wind.u100.values, era5_wind.v100.values)

plot_wind_rose(loc_wd10, loc_ws10)


#%% Working with self-downloaded ERA5 data. Jan 26, 2026

path_data = 'D:\\InProbation\\Metocean_Jeju\\Data\\ERA5\\'
path_u = path_data + 'wind_100m_u\\'
path_v = path_data + 'wind_100m_v\\'

wind_u100 = xr.open_dataset(path_u + "era5_1976_u100.nc", engine="netcdf4")
wind_v100 = xr.open_dataset(path_v + "era5_1976_v100.nc", engine="netcdf4")

# chosen location to plot: latitude=33.5, longitude=127
loc_plot = [33.5, 126.75]

all_ws100, all_wd100 = compute_ws_wd_from_u_v(wind_u100.sel(latitude=loc_plot[0], longitude=loc_plot[1]).u100.values, 
                                              wind_v100.sel(latitude=loc_plot[0], longitude=loc_plot[1]).v100.values)
plot_wind_rose(all_ws100, all_wd100)


# plot time series of wind speed
df_ws = pd.DataFrame(all_ws100, columns=['wind speed [m/s]'])
df_ws['timestamp']  = wind_u100.valid_time

fig_title = f'ERA5 wind speed data at 100 m, 1976 at location of ({loc_plot[0]}, {loc_plot[1]})'
plot_time_series_scatter(df_ws, 'timestamp', 'wind speed [m/s]', fig_title)