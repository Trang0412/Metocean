'''
Mapping variables's long name to short name according to Nomenclature in DHI-Wando-Gumil report (p6-8)


@Author: Le Thi Trang
@Date: Jan 23, 2026
'''

# TODO: Later change or add more variables to this dictionary
# Mapping current available variables for naimg column in dataframe. 
# E.g., used in measurements from different stations and provider
# Adding more variables later

# later put in station_metadata file and load as batch
ws_name = '풍속(m/s)' # same for KMA and KHOA
wd_name = '풍향(deg)' # same for KMA and KHOA

khoa_timestamp = '관측시간'
khoa_wind_vars = [khoa_timestamp, ws_name, wd_name]


kma_timestamp = '일시'
kma_wind_vars = [kma_timestamp, ws_name, wd_name]

# same for KMA and KHOA
vars_type = ['datetime64[s]', 'float', 'float']
kma_wind_type_dict = dict(zip(kma_wind_vars, vars_type))
khoa_wind_type_dict = dict(zip(khoa_wind_vars, vars_type))


wave_direction_stations = ['거문도', '마라도', '추자도_해양기상부이', '서귀포']


timestamp_names = {
    # KHOA stations
    '관측시간':'timestamp_khoa',
    '일시':'timestamp_kma',
}

wind_var_names = {
    '풍속(m/s)':'ws',
    '풍향(deg)':'wd',
}

wave_var_names = {
    '최대파고(m)':'Hmax',
    '유의파고(m)':'Hm0',
    '평균파고(m)':'Hmean',
    '파주기(sec)':'T02',
    '파향(deg)':'waveD',
}

water_var_names = {
    '조위(cm)':'WL'
}

current_var_names = {
    '유속(cm/s)': 'CS',
    '유향(deg)': 'CD',
}

#%% Criteria for filtering wrong or bad data from measurements
# Refer to DHI Wando-Gumil section 2.2.1. Measurement's data quality and filtering
# Need to change according to study site
# Data outside of the following limits are being removed

mapping_QAed = {
    # KMA stations
    'wl':[-5, 5], # water level [mMSL]
    'Hm0':[0, 12], # significant wave height [m]
    'Tp':[0, 30], # peak wave interval [s]
    'T02':[0, 30], # peak wave interval [s]
    'cs':[0, 2], # current speed [m/s]
    'ws':[0, 60], # wind speed [m/s]
    'direction': [0, 360], # directional data, degree
    'num_bad_sector': [0, 60],
    'roll_var': [-5, 5], # roll variability, degree
    'pitch_var': [-5, 5] # pitch variability, degree

}

