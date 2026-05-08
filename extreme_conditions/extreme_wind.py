'''
- Perform extreme analysis for wind data for 3 conditions:
1. Non-typhon condition: 
    Using ERA5 data for whole period of 49 years from 1979-2025
2. Typhoon conditions:
    From 1979-2000: WINK typhoon wind field
    from 2000-now: JMA-MSM data (?), might have to purchase
3. Combined typhoon and non-typhoon data 

- WINK typhoon wind field data characteristics:
    +) grid point value (GPV) with space resolution of 0.03333 degree
    +) space grid of 900 x900 from 117E, 20N
    +) time step of 1hour


- Refer to part 7.10 from DHI report for Extreme wind speed:
    Extreme wind speed was analyzed at 10mMSL (WS at 10m height) 
    and at hub height 130 mMSL and 145 mMSL (WS at 100m height)

- At what height should we consider for analysis at hub heights?


@Author: Le Thi Trang
@Date: April 24, 2026
'''
#%%

import sys
sys.path.append('D:\\InProbation\\Metocean\\scripts')
import metocean_metadata
import visualizing
import wind_data_processing
import data_loading
import common_processing

from metocean_metadata import *
from visualizing import *
from data_loading import *
from common_processing import *
from wind_data_processing import *

import pandas as pd
import cartopy

#%% Path definition here
dir_tp_msm = dir_data + 'Typhoon_wind\\JRA_3Q\\'
dir_tp_wink = dir_data + 'Typhoon_wind\\Reanalyzed_HYB_TC_Wind_Data\\'



#%%
conds = ['non-typhoon', 'typhoon', 'combined']

cond = 'non-typhoon'
hub_heights = [130, 145] # April 28, follow Wando-Gumil, need to correct for our study
hub_height = 130 # 
delivery_locs = dict({}) # chosen of delivery location for wind and other parameter also


# load tyhoon selected
typhoon_selected = sel_typhoon_affected()

if cond == 'non-typhoon': #  non-typhoon condition
    non_typhoon_wind = remove_typhoon_wind_data()
    do_extreme_wind_analysis()

elif cond == 'typhoon': # 2. Typhoon conditions

    crit_ws_min = convert_wind_gust_temporal(typhoon_search_cri_dhi['min_ws'])
    typhoon_search_cri_mit = typhoon_search_cri_dhi.copy()
    typhoon_search_cri_mit['min_ws'] = crit_ws_min

    


    select_typhoons = pd.read_excel(dir_data + 'Typhoon_wind\\typhoon_historical_data.xlsx', 
                                    sheet_name='Typhoons selected', skiprows=2)
    col_names = ['Code', 'Name', 'Impact period']
    select_typhoons = select_typhoons[col_names]
    select_typhoons['Code'] = select_typhoons['Code'].apply(lambda x: f'{x:04d}')

    # metadata will read as 2-columns with information on 1 tyhoon are presented using 3 rows
    mdata_typhoon = read_typhoon_wink_metadata(dir_tp_wink, 'HYB_TC_INPUTS.dat') 
    wink_grid = dict({'lat':wink_lat_points, 'lon':wink_lon_points})
    # all_typhoons = dict

    for ti in range(len(select_typhoons)):
        try:
            typhoon_name = select_typhoons['Code'][ti] + '_' + select_typhoons['Name'][ti]
            ws, wd = read_typhoon_wink(dir_tp_wink, typhoon_name + '_WIND.dat')
            print(f'Wind field data loaded for typhoon {typhoon_name}')
        except:
            print(f'There is no wind data for typhoon {typhoon_name}')


    do_extreme_wind_analysis()
        
else: # combined condition
    combined_wind = combine_typhoon_wind_data()
    do_extreme_wind_analysis()
