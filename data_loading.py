'''
For loading different data set

@Author: Le Thi Trang
@Date: Jan 26, 2026

'''
import os
import xarray as xr
import pandas as pd
import numpy as np
import glob
from pathlib import Path
pd.set_option('future.no_silent_downcasting', True)
from metocean_metadata import *




def load_obs_all_data(dir_data, provider, station, year=2024):
    '''
    Load yearly measurement data for a certain year in specified station
    Assuming data were measured for full 12-month in year


    Parameter
        -dir_data: str, directory storing measurement data
        -station: str, directory to data according to each provider. E.g., KHOA_제주
        -list_vars: list of string, measured variables to load
        -type_dict: dictionary, mapping measured data to correct type depends on each variable
        -year: integer, data in the year to load

    Return
        - data_year: pd.DataFrame, dataframe of loaded data in requested year with corrected type

    '''

    dir_station = dir_data +  provider + '\\' + station + '\\'
    path_station = Path(dir_station)

    if provider == 'KHOA':
        matching_files = list(path_station.glob(f'{year}*'))
        try:
            data = pd.read_csv(matching_files[0], sep='\t', skiprows=3,)
        except:
            data = pd.read_csv(matching_files[0], sep='\t', skiprows=3,header=0, encoding='cp949')

        data = data.replace('-', np.nan) 

    elif provider == 'KMA':
        matching_files = list(path_station.glob(f'*_{year}_*'))
        data = pd.read_csv(matching_files[0], sep=',', header=0, encoding='cp949')

        data = data.replace('-', np.nan) 
    return data






def load_era5_wind_data(dir_data, var_name, year=2024):
    '''
    Load newly downloaded era5 data.
    Currently working with newly downloaded data

    Parameter
        -dir_data: str, directory to saved ERA5 data
        -var_name: str, name of variable to load, e.g., wind_10m_u_v
        -year: integer, year of data measurement     

    Return
        list of xarray.dataset seprated for each variables 

    Create date: Jan 26, 2026

    '''
    
    if 'wind_100m' in var_name:

        #load u,v component separately as saved
        path_u = dir_data + var_name + '_u\\'
        path_v =  dir_data + var_name + '_v\\'

        wind_u = xr.open_dataset(path_u + f"era5_{year}_u{var_name.split('_')[1][:-1]}.nc", engine="netcdf4")
        wind_v = xr.open_dataset(path_v + f"era5_{year}_v{var_name.split('_')[1][:-1]}.nc", engine="netcdf4")
        
        return [wind_u, wind_v]

    elif 'wind_10m' in var_name:
        
        path_load = dir_data + 'wind_10m_u_v\\' + str(year) + '\\'
        
        #load data for every month and concate to form yearly data
        wind_u = xr.DataArray()
        wind_v = xr.DataArray()
        for month in range(1,13):
            if month < 10:
                wind_monthly = xr.open_dataset(path_load + f"ERA5_{year}0{month}_reduced_korea.nc", engine="netcdf4")
            else:
                wind_monthly = xr.open_dataset(path_load + f"ERA5_{year}{month}_reduced_korea.nc", engine="netcdf4")
            
            list_dims = list(wind_monthly.dims)
            time_dim = [dim for dim in list_dims if 'time' in dim]
            if len(time_dim) !=1:
                raise Exception(f'There is none or more than 1 dimension of time at {year} ERA5 data')
            if month==1:
                wind_u = wind_monthly.u10
                wind_v = wind_monthly.v10
            else:
                wind_u = xr.concat([wind_u, wind_monthly.u10], dim=time_dim[0], join='outer')
                wind_v = xr.concat([wind_v, wind_monthly.v10], dim=time_dim[0], join='outer')
            
        return [wind_u.to_dataset(), wind_v.to_dataset()]

    else: # load mean sea level level
        path_load = dir_data + var_name + '\\'
        mslp = xr.open_dataset(path_load + f"era5_{year}_mslp.nc", engine="netcdf4")
        return [mslp]


def load_era5_regrid_wind_data(dir_data, year=2024):
    '''
    Load regrided ERA5 wind field data.
    Currently working with newly downloaded data

    Parameter
        -dir_data: str, directory to saved ERA5 data
        -var_name: str, name of variable to load, e.g., wind_10m_u_v
        -year: integer, year of data measurement     

    Return
        list of xarray.dataset seprated for each variables 

    Create date: Jan 26, 2026

    '''
    #load u,v component separately as saved
    wind_data = xr.DataArray()
    for month in range(1,13):
        if month < 10:
            wind_monthly = xr.open_dataset(dir_data + '\\' + str(year) + f"\\ERA5_windfield_{year}0{month}.nc", engine="netcdf4")
        else:
            wind_monthly = xr.open_dataset(dir_data + '\\' + str(year) + f"\\ERA5_windfield_{year}{month}.nc", engine="netcdf4")
        
        list_dims = list(wind_monthly.dims)
        time_dim = [dim for dim in list_dims if 'time' in dim.lower()]

        if len(time_dim) !=1:
            raise Exception(f'There is none or more than 1 dimension of time at {year} ERA5 data')
        if month==1:
            wind_data = wind_monthly
        else:
            wind_data = xr.concat([wind_data, wind_monthly], dim=time_dim[0], join='outer')

    return wind_data



def load_obs_wind_data(dir_data, provider, station, year=2024):
    '''
    Load yearly measurement data for a certain year in specified station
    Assuming data were measured for full 12-month in year


    Parameter
        -dir_data: str, directory storing measurement data
        -station: str, directory to data according to each provider. E.g., KHOA_제주
        -list_vars: list of string, measured variables to load
        -type_dict: dictionary, mapping measured data to correct type depends on each variable
        -year: integer, data in the year to load

    Return
        - data_year: pd.DataFrame, dataframe of loaded data in requested year with corrected type

    '''

    dir_station = dir_data +  provider + '\\' + station + '\\'

    if provider == 'KHOA':
        # extract postfix of the name then loop through each month
        # name of file are different in month when data were measured
        # 2013년 11월 제주 조위관측소.txt'
        filename_postfix = f'{station} 조위관측소.txt' # currently set fixed for KHOA station
        
        filename = f'{year}년 {filename_postfix}'

        try:
            data = pd.read_csv(dir_station + filename, sep='\t', skiprows=3,)
        except:
            data = pd.read_csv(dir_station + filename, sep='\t', skiprows=3,header=0, encoding='cp949')

        data = data.replace('-', np.nan) 
        data = data[khoa_wind_vars]
        data = data.astype(khoa_wind_type_dict)
        

    elif provider == 'KMA':

        path_station = Path(dir_station)
        matching_files = list(path_station.glob(f'*_{year}_*'))

        data = pd.read_csv(matching_files[0], sep=',', header=0, encoding='cp949')
        data = data.replace('-', np.nan) 
        data = data[kma_wind_vars]
        data = data.astype(kma_wind_type_dict)

    return data

