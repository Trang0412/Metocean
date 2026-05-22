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

import linecache



def read_typhoon_wink_metadata(dir_tp):
    ''' Read metadata from WINK typhoon data
    Parameters:
        -dir_tp: str, directory to typhoon wind data from WINK
    Returns:
        -typhoons: pd.DataFrame, with 4 columns of [Name, Start time, End time, Time inteval(min)]
    '''
    mdata_typhoon =  pd.read_csv(dir_tp+'HYB_TC_INPUTS.dat', sep='./', header=None)
    typhoons = mdata_typhoon.iloc[:,1].dropna()
    typhoons = typhoons.apply(lambda x: x.split('_BATCH')[0])
    typhoons = typhoons.to_frame(name='Name')
    typhoons['Start time'] = None
    typhoons['End time'] = None
    typhoons['Time iterval (min)'] = None

    for i in typhoons.index:
        time_info = mdata_typhoon.iloc[i+2,0].split(' ')
        start_d = f'{time_info[1][:4]}-{time_info[1][4:6]}-{time_info[1][6:8]}'
        start_h = f'{time_info[1][9:11]}:{time_info[1][11:13]}:{time_info[1][13:15]}'
        typhoons.at[i, 'Start time'] = pd.to_datetime(f'{start_d} {start_h}')
        end_d = f'{time_info[-1][:4]}-{time_info[-1][4:6]}-{time_info[-1][6:8]}'
        end_h = f'{time_info[-1][9:11]}:{time_info[-1][11:13]}:{time_info[-1][13:15]}'
        typhoons.at[i, 'End time'] = pd.to_datetime(f'{end_d} {end_h}')
        typhoons.at[i, 'Time iterval (min)'] = 60
    
    return typhoons.reset_index(drop=True)
    

def read_typhoon_specific_loc(ws, wd, wind_grid, loc):
    '''
    Return wind speed, wind direction of typhoon for specific location with all occurrence time
    Paramters:
        -ws: np.ndarray, dim of (time, lat space, lon space), wind speed of typhoon
        -wd: np.ndarray, dim of (time, lat space, lon space), wind direction of typhoon
        -wind_grid: dict, contain points for lat and lon 
            'lat': np.array of latitiude in grid
            'lon': np.arrau of longitude in grid 
        -loc: list, [lat, lon] of location.
            
    Returns:
        -ws: np.array, dim of (time, 1), wind speed of typhoon for specific location
        -wd: np.array, dim of (time, 1), wind direction of typhoon for specific location
        
    '''
    lat_idx = np.where(wind_grid['lat'] == min(wind_grid['lat'], key=lambda x: abs(x-loc['lat'])))
    lon_idx = min(wind_grid['lon'], key=lambda x: abs(x-loc['lon']))

    return ws[:,lat_idx,lon_idx ], wd[:,lat_idx,lon_idx]



def load_fort61(dir_hot, simul_start_time, time_from_fort26=True, 
                col_names=['관측시간', '조위(cm)'], start_reading_idx=None, 
                to_kst=True, start_lidx=3, first_data_lidx=4, to_future=None):
    ''' Load modeled data from ADCIRC 
    Parameters:
        -dir_hot: str, directory of 'hot_' folder from simulation
        -simul_start_time: pd.Datetime, start time on simulation time, from fort.26
        -col_names: list, list of columne name for loading in data to pd.DataFrame, 1st: timestamp, 2: Name of parameters checking
        -start_lidx: int, index of line with time step of writing 
            Content will look like this: 3.4620000000E+005         346200), 
            Line count start from 1. 
        -first_data_lidx: int, index of first line of data writing
            Content will look like this: 1     6.5347367811E-001), where 1: point index, 2nd value is modeled data
        -to_future: int, move modeled data to future of days, added May 22, 2026 for debug
    Returns:
        -Dictionary with key as stations' names and values are pd.DataFrame writen with columns of ['Timestamp', 'Water level (m)']


    '''
    # reading control parameters from fort.15
    adcirc_params, wl_stations = read_fort15_wl(dir_hot)
    # fix to use metadata for water elevation at current moment, April 30, 2026
    # write_inerval is set to unit of minutes
    write_interval = pd.to_timedelta(int(adcirc_params['ELEV_interval']), unit='s')/pd.Timedelta(minutes=1) 

    with open(dir_hot + 'fort.61', 'r') as f:
        line_count = sum(1 for line in f)

    fname_61 = dir_hot + 'fort.61'
    n_stations = len(wl_stations)
    start_time_line = linecache.getline(fname_61, start_lidx)
    all_stations_data = dict()

    for si in range(n_stations):
        if time_from_fort26:
            write_time = simul_start_time
        else: # sometime simulation unsuccefully finished, input of data is simulation time
            write_time = simul_start_time + pd.to_timedelta(float(start_time_line.split()[1]), unit='s')
        statn_lidxs = np.arange(first_data_lidx+si, line_count, n_stations+1)
        statn_data = pd.DataFrame(columns=col_names)

        for lidx in statn_lidxs:
            statn_data.loc[len(statn_data)] = [write_time,float(linecache.getline(fname_61, lidx).split()[1])]
            write_time = write_time+pd.Timedelta(minutes=write_interval)
            
        if start_reading_idx is not None: 
            statn_data = statn_data[statn_data[col_names[0]]>=statn_data.iloc[0,0]+
                                    pd.Timedelta(seconds=int(start_reading_idx-float(start_time_line.split()[1])))]
        # shift to kst time
        if to_kst:
            statn_data[col_names[0]] = statn_data[col_names[0]] + pd.Timedelta(hours=9)

        # shift data to future ot to_future day
        if to_future is not None:
            statn_data[col_names[0]] = statn_data[col_names[0]] + pd.Timedelta(days=to_future)

        # modeled data return water with unit of meter while observation recorded in cm level
        if col_names[1] == '조위(cm)':
            statn_data[col_names[1]] = statn_data[col_names[1]]*100 
        all_stations_data[wl_stations['Name'][si]] = statn_data

    return all_stations_data


def read_fort26(dir_hot):
    '''Read time information for this current simulation. Can be replaced by output.log
    Parameters:
        -dir_hot: str, directory of simulation of hot case
    Retuns:
        - simul_time: dictionary, storing time information of [start, end, interval]
    '''
    fname = dir_hot + 'fort.26'
    simul_time = dict()
    with open(fname, 'r') as fortfile:
        for line in reversed(fortfile.readlines()):
            if 'COMPUTE ' in line: 
                time_ = line.split()[1]
                simul_time['start'] = pd.to_datetime(f'{time_[0:4]}-{time_[4:6]}-{time_[6:8]} {time_[9:11]}:{time_[11:13]}:{time_[13:15]}')
                time_ = line.split()[4]
                simul_time['end'] = pd.to_datetime(f'{time_[0:4]}-{time_[4:6]}-{time_[6:8]} {time_[9:11]}:{time_[11:13]}:{time_[13:15]}')
                simul_time['interval'] = float(line.split()[2])*60

                break             

    return simul_time

def read_fort15_wl(dir_fort15):
    ''' Reading control parameters from ADCIRC model by assign value for keys of params in metocean_metadata
    Always check format of fort.15 as the code here is hard-coded for current format
    Parameters:
        -dir_fort15: str, directory to fort.15 file
    Returns:
        -adcirc_params: dict, dictionary of settings of different parameters, e.g., 'DT', 'RNDAY', etc.
        -wl_stations: pd.DataFrame, 3 columns of [Name, lon, lat]

    '''
    adcirc_params = dict()
    fname = dir_fort15 + 'fort.15'
    with open(fname, 'r') as fort15:
        for lidx, line in enumerate(fort15.readlines()):
            if ' DT ' in line: adcirc_params['DT'] = float(line.split()[0])
            if ' RNDAY ' in line: adcirc_params['RNDAY'] = float(line.split()[0])
            if ' DRAMP' in line: adcirc_params['DRAMP'] = float(line.split()[0])
            if 'ELEV ' in line: 
                adcirc_params['ELEV'] = True
                adcirc_params['ELEV_interval'] = float(line.split()[3])
                break             

    if adcirc_params['ELEV']:
        
        adcirc_params['ELEV_num_statns'] = int(linecache.getline(fname, lidx+2).split()[0])
        wl_stations = pd.DataFrame(columns=['Name', 'lon', 'lat'])
        for i in range(adcirc_params['ELEV_num_statns']):
            wl_stations.loc[len(wl_stations)] = [linecache.getline(fname, lidx+3+i).split()[3],
                                                        float(linecache.getline(fname, lidx+3+i).split()[0]),
                                                        float(linecache.getline(fname, lidx+3+i).split()[1])
                                                        ]


    return adcirc_params, wl_stations


def load_obs_all_data(dir_data, provider, station, year=2024):
    '''
    Load yearly measurement data for a certain year in specified station
    Assuming data were saved for full 12-month in year


    Parameter
        -dir_data: str, directory storing measurement data
        -station: str, directory to data according to each provider. E.g., KHOA_제주
        -list_vars: list of string, measured variables to load
        -type_dict: dictionary, mapping measured data to correct type depends on each variable
        -year: integer, data in the year to load

    Return
        - data_year: pd.DataFrame, dataframe of loaded data in requested year with corrected type

    '''

    dir_station = dir_data + provider + '\\' + station + '\\'
    path_station = Path(dir_station)
    data = pd.DataFrame()
    if 'KHOA' in provider:
        matching_files = list(path_station.glob(f'{year}*'))
        if len(matching_files) > 0:
            try:
                data = pd.read_csv(matching_files[0], sep='\t', skiprows=3,)
            except:
                data = pd.read_csv(matching_files[0], sep='\t', skiprows=3,header=0, encoding='cp949')

            data = data.replace('-', np.nan) 

    elif 'KMA' in provider:
        matching_files = list(path_station.glob(f'*_{year}_*'))
        if len(matching_files) >0:
            if matching_files[0].suffix.lower() == '.csv':
                data = pd.read_csv(matching_files[0], sep=',', header=0, encoding='cp949')
            else:
                data = pd.read_excel(matching_files[0], header=0)

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
            wind_monthly = xr.open_dataset(path_load + f"ERA5_{year}{month:02d}_reduced_korea.nc", engine="netcdf4")
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

