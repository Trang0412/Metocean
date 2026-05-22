'''
Mapping variables's long name to short name according to Nomenclature in DHI-Wando-Gumil report (p6-8)


@Author: Le Thi Trang
@Date: Jan 23, 2026
'''

import numpy as np
import pandas as pd
import xarray as xr


# path anf filename definition here
dir_data = 'D:\\InProbation\\Metocean\\Data\\'
dir_analysis = 'D:\\InProbation\\Metocean\\Analysis\\'
dir_tp_jra3q = dir_data + 'Typhoon_wind\\JRA_3Q\\'
dir_tp_wink = dir_data + 'Typhoon_wind\\Reanalyzed_HYB_TC_Wind_Data\\'
dir_btd = dir_data + 'Typhoon_wind\\JMA_BestTrackData\\'
dir_tp_selected = dir_data + 'Typhoon_wind\\typhoons_selected\\'
dir_tp_track_graphic = dir_tp_selected + '\\track_graphic\\'
dir_era5_wind = dir_data + 'ERA5\\'
dir_turbine_info = dir_data + 'Turbine design\\'

#%% Tidal harmonic analysis
# "Z0" should be added also 
# extracted from Annual report 2025 of KHOA
khoa_tidal_consts = [
    'Z0', "Sa", "Ssa", "Mm", "Msf", "Mf", "2Q1", "SIG1", "Q1", "RO1", 
    "O1", "MP1", "M1", "CHI1", "PI1", "P1", "S1", "K1", "PSI1", "PHI1", 
    "TH1", "J1", "SO1", "OO1", "OQ2", "MNS2", "2N2", "MU2", "N2", "NU2", 
    "OP2", "M2", "MKS2", "LAM2", "L2", "T2", "S2", "R2", "K2", "MSN2", 
    "KJ2", "2SM2", "MO3", "M3", "SO3", "MK3", "SK3", "MN4", "M4", "SN4", 
    "MS4", "MK4", "S4", "SK4", "2MN6", "M6", "MSN6", "2MS6", "2MK6", "2SM6", 
    "MSK6", "MA2", "MB2"
]

#monthly
khoa_tidal_consts = [ 'Z0','MSF','Q1','O1','M1','K1','J1','OO1','MU2','N2','M2','L2','S2','2SM2']

# utide.ut_constants
utide_tidal_consts =  ['Z0','SA','SSA','MSM','MM','MSF','MF','ALP1','2Q1','SIG1','Q1','RHO1',
                       'O1','TAU1','BET1','NO1','CHI1','PI1','P1','S1','K1','PSI1','PHI1','THE1',
                       'J1','2PO1','SO1','OO1','UPS1','ST36','2NS2','ST37','ST1','OQ2','EPS2','ST2',
                        'ST3','O2','2N2','MU2','SNK2','N2','NU2','ST4','OP2','GAM2','H1','M2','H2',
                        'MKS2','ST5','ST6','LDA2','L2','2SK2','T2','S2','R2','K2','MSN2','ETA2','ST7',
                        '2SM2','ST38','SKM2','2SN2','NO3','MO3','M3','NK3','SO3','MK3','SP3','SK3','ST8',
                        'N4','3MS4','ST39','MN4','ST9','ST40','M4','ST10','SN4','KN4','MS4','MK4','SL4',
                        'S4','SK4','MNO5','2MO5','3MP5','MNK5','2MP5','2MK5','MSK5','3KM5','2SK5','ST11',
                        '2NM6','ST12','2MN6','ST13','ST41','M6','MSN6','MKN6','ST42','2MS6','2MK6','NSK6',
                        '2SM6','MSK6','S6','ST14','ST15','M7','ST16','3MK7','ST17','ST18','3MN8','ST19','M8',
                        'ST20','ST21','3MS8','3MK8','ST22','ST23','ST24','ST25','ST26','4MK9','ST27','ST28','M10',
                        'ST29','ST30','ST31','ST32','ST33','M12','ST34','ST35']

#%% Wind analysis
# refer to picture in file '02. 도의회 보완 1차_21년 10월' in email, [WindS5500/140 Technical Specification]
# from DooSan Heavy Industries and Construction, Co., Ltd
tubrine_hub_height = 100

# search criteria for typhoon selection, refer to DHI report (section 2.4-WRF, Typhoon wind data),
# may change accordingly

# using 10-min maximum wind speed, directly provided by JMA-BTD and WINK for minimum speed constraints (in knot)
# conversion between 10-min to 1-min to match dhi criteria of 1.1, might change accordingly

# using 1-min maximum wind speed for minimum speed constraints
typhoon_search_cri_dhi = pd.DataFrame(data=[ [5, 500, 30], [3, 300, 25], [2.5, 250, 7.5]], 
    columns=['radius_deg', 'radius_km', 'min_ws']
)
# reference point for choosing typhoon with different radii criteria above
typhoon_ref_point = dict({'lat':33.5, 'lon':126.75}) # chosen near PC1, PC2; might change accordingly


data_sources = ['KMA', 'KHOA', 'WINK']

# WINK typhoon grid info; April 24, 2026
wink_lon_range = [117, 147]
wink_lat_range = [20, 50]

wink_n_points = 901
wink_res_deg = 0.03333333

# wink_lon_points = np.linspace(wink_lon_range[0], wink_lon_range[1], wink_n_points, endpoint=False)
# wink_lat_points = np.linspace(wink_lat_range[0], wink_lat_range[1], wink_n_points, endpoint=False)

# to match with interpolated grid of ERA5 and JRA3Q using cdo
wink_lon_points = np.arange(wink_lon_range[0], wink_lon_range[1], wink_res_deg)
wink_lat_points = np.arange(wink_lat_range[0], wink_lat_range[1], wink_res_deg)

wink_grid_lat, wink_grid_lon = np.meshgrid(wink_lat_points, wink_lon_points, indexing='ij')

wink_dt = 1 # wink record wind at 1hr inteval
jra3q_dt = 6 # jra-3q record wind at 1hr inteval

# study site coordination, lon/lon
PC1_loc = dict({'lat':33.54219444, 'lon':126.84852780})
PC2_loc = dict({'lat':33.55400000, 'lon':126.85891670})

temp_jra = xr.open_dataset(dir_tp_jra3q + 'jra3q.anl_surf.0_2_3.vgrd10m-hgt-an-gauss.2025030100_2025033118.nc')
lat_subset_jra = temp_jra.lat.sel(lat=slice(wink_lat_range[1], wink_lat_range[0])).values[::-1]
lon_subset_jra = temp_jra.lon.sel(lon=slice(wink_lon_range[0], wink_lon_range[1])).values
jra_grid_lat, jra_grid_lon = np.meshgrid(lat_subset_jra, lon_subset_jra, indexing='ij')

#%% Rose plot colormap
windrose_colors_1 = ['#BD2102', '#EE5611', '#FF8849', '#FDAF45', '#FFD642', '#7BC64D',  
              '#A0D5E3', '#0B93D7', '#4F71BA', '#93509E', '#FFFFFF']
windrose_colors_1 = windrose_colors_1[::-1]

windrose_colors_2 = ['#101010', '#3C3C3C', '#525252', '#686868', '#7E7E7E', '#939393',
                      '#A9A9A9', '#BFBFBF', '#D5D5D5', '#EBEBEB', '#FFFFFF']
windrose_colors_2 = windrose_colors_2[::-1]

#%% Modeled data
#  control parameters needed to read from ADCIRC (fort.15), April 30, 2026
# need to add specific parameters for checking.e.g, 'ELEV': water elevation
# IF PARAMETERS UPATED HERE, THEN IT SHOULD BE UPDATED IN read_adcirc_params() ACCORDINGLY
# PARAMETERS STATED HERE IS JUST PLACE HOLDER FOR DOUBLE CHECK WHAT SHOULD BE LOAD IN read_adcirc_params()
adcirc_control_params_head = ['DT', 'RNDAY'] # shoule be read in order
adcirc_control_params_tail = ['NSPOOLE']



#%% Observation data metadata
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
longest_checking_duration_wind = [2000, 2026]

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
    '조위(cm)':'WL' # tide level
}

current_var_names = {
    '유속(cm/s)': 'CS',
    '유향(deg)': 'CD',
}

#%% Criteria for filtering wrong or bad data from measurements
# Refer to DHI Wando-Gumil section 2.2.1. Measurement's data quality and filtering
# Need to change according to study site
# Data outside of the following limits are being removed

fixed_qc_criteria = {
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
nl  = '\n'
# ERA5 coordination
era5_coor = {
    'lat': np.arange(32, 40, 0.25),
    'lon': np.arange(120, 180, 0.25)
}
regrid_era5_coor = {
    'lat': np.arange(20, 50, 0.05),
    'lon': np.arange(120, 150, 0.05)
}
