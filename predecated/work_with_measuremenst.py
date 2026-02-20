'''
Reading data from csv file downloaded from national observation stations


@Author: Le Thi Trang
@Date: Jan 22, 2026
'''


#%%
import pandas as pd
import xarray as xr
import numpy as np
from compute_variables import *
from plot_data import *

import os


#%%
dir_data = 'D:\\InProbation\\Metocean_Jeju\\Data\\Measurements\\'
folders = os.listdir(dir_data)

# %% for KHOA stations as it provide 1-minute-interval data
#########################################################################
# compute Wind speed average for 10-minute interval as recommended in DNV Recommended practice

years = np.arange(2013, 2025, 1) # can change to years need to check
months = np.arange(1 ,13, 1) # assuming data are available for 12 months of year
stations_KHOA = ['제주', '성산포']
ws_name = '풍속(m/s)'
wd_name = '풍향(deg)'
timestamp = '관측시간'
wind_variables = ['관측시간', '풍속(m/s)', '풍향(deg)'] # only checking wind variables at the moment

wind_variables = [timestamp, ws_name, wd_name]
variable_type = ['datetime64[s]', 'float', 'float']
type_dict = dict(zip(wind_variables, variable_type))


#% Work with each station's data
for station in stations_KHOA:
    dir_station = dir_data + 'KHOA_' + station + '\\'
    
    for year in years:
        dir_year = dir_station + str(year) + '\\'
        whole_year_files = os.listdir(dir_year)

        # extract postfix of the name then loop through each month
        # name of file are different in month when data were measured
        # 2013년 11월 제주 조위관측소.txt'
        filename_postfix = '제주 조위관측소.txt' # currently set fixed for KHOA station

        for month in months:
            if month<10:
                filename = f'{year}년 0{month}월 {filename_postfix}'
            else:
                filename = f'{year}년 {month}월 {filename_postfix}'

            data_month = pd.read_csv(dir_year + filename, sep='\t', skiprows=3)
            # all data in KHOA stations are read as 'str' type
            # need to extract data and assign the correct data type
            wind_data = data_month[wind_variables]
            # wind_data.loc[:, ['풍속(m/s)', '풍향(deg)']] = wind_data[['풍속(m/s)', '풍향(deg)']].replace('-',np.nan) 
            wind_data.loc[:, [ws_name, wd_name]] = wind_data[[ws_name, wd_name]].replace('-',np.nan) 
            
            wind_data = wind_data.astype(type_dict)
            wind_data = wind_data.ffill()  # fill missing value with value of previous data point 

            rose_plot_title = f'Wind speed at {station} during {year}년 0{month}월'
            plot_wind_rose(wind_data[wd_name].values, wind_data[ws_name].values, rose_plot_title)

            # compute average wind speed over certain minutes
            ws_avg = compute_avg_wind_speed(wind_data[[timestamp, ws_name]], 10, verbose=0)
            ws_avg.plot(0,1,kind='scatter', rot=60, title=f'{station}, {year}년 {month}월')



#%% KMA stations provide 1-hour-interval data
#########################################################################
stations_KMA = ['김녕', '우도', '하도']

station_code = '지점'
timestamp = '일시'
water_temp_name = '수온(°C)'
Hmax = '최대파고(m)'
Hm0 = '유의파고(m)'
Hmean = '평균파고(m)'
Twave = '파주기(sec)'

variable_names = [station_code, timestamp, water_temp_name, 
                  Hmax, Hm0, Hmean, Twave]
variable_type = ['int32', 'datetime64[s]', 'float', 'float', 'float', 'float', 'float']
type_dict = dict(zip(variable_names, variable_type))


for station in stations_KMA:
    dir_station = dir_data + 'KMA_' + station + '\\'
    files_all = os.listdir(dir_station)
    
    for filename in files_all:
        data_year = pd.read_csv(dir_station+filename, sep=',', header=0, encoding='cp949')
        data_year = data_year.astype(type_dict)

        plot_time_series_scatter(data_year, timestamp, Hm0, fig_title="")





