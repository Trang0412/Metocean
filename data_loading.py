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



def load_era5_data(dir_data, var_name, year=2024):
    '''
    Load newly downloaded era5 data.
    Currently working with newly downloaded data

    Parameter
        -dir_data: str, directory to saved ERA5 data
        -var_name: str, name of variable to load
        -year: integer, year of data measurement     

    Return
        list of array.dataset seprated for each variales 

    Create date: Jan 26, 2026

    '''
    
    # Working with self-downloaded ERA5 data. Jan 26, 2026

    
    
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





def load_meas_data(dir_data, station, list_vars, type_dict, year=2024):
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

    data_year = pd.DataFrame(columns=list_vars)
    # data_year = data_year.astype(type_dict)

    if 'KHOA' in station:
        
        dir_station = dir_data + station + '\\'
        #folder name with provider always in format of Provider_Station.
        #e.g., KHOA_제주
        station_name = station.split('_')[1] 
        
        dir_year = dir_station + str(year) + '\\'

        # extract postfix of the name then loop through each month
        # name of file are different in month when data were measured
        # 2013년 11월 제주 조위관측소.txt'
        filename_postfix = f'{station_name} 조위관측소.txt' # currently set fixed for KHOA station
        
        for month in np.arange(1,13,1):
            if month<10:
                filename = f'{year}년 0{month}월 {filename_postfix}'
            else:
                filename = f'{year}년 {month}월 {filename_postfix}'

            try:
                data_month = pd.read_csv(dir_year + filename, sep='\t', skiprows=3,)
            except:
                data_month = pd.read_csv(dir_year + filename, sep='\t', skiprows=3,header=0, encoding='cp949')

            data_month = data_month.replace('-',np.nan) 
            
            data_year = pd.concat([data_year, data_month[list_vars]], axis=0, ignore_index=True) 

            del data_month

    elif 'KMA' in station:

        dir_station = dir_data + station + '\\'
        path_station = Path(dir_station)

        matching_files = list(path_station.glob(f'*_{year}_*'))
        data_year = pd.read_csv(matching_files[0], sep=',', header=0, encoding='cp949')
        # data_year = data_year.replace('-',np.nan) 
        

    return data_year.astype(type_dict)

