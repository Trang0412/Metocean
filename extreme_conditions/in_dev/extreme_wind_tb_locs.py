'''

Note:

Wind data used in here are interpolated version of ERA5, WINK, and JRA3Q at specific turbine locations

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
@Date: May 19, 2026
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
import pyextremes
from pyextremes.plotting import plot_extremes
import scipy.stats as sstats


#%% Path definition here
# dir_tp_jra3q = dir_data + 'Typhoon_wind\\JRA_3Q\\'
# dir_tp_wink = dir_data + 'Typhoon_wind\\Reanalyzed_HYB_TC_Wind_Data\\'
# dir_btd = dir_data + '\\Typhoon_wind\\JMA_BestTrackData\\'
# dir_tp_selected = dir_data + '\\Typhoon_wind\\typhoons_selected\\'
# dir_tp_track_graphic = dir_tp_selected + '\\track_graphic\\'

dir_extreme_anal = dir_analysis + 'Extreme conditions\\Wind\\'
dir_era5_interp = dir_data + 'ERA5\\interp_bilinear_turbine_locs\\'
#%% DEFINE DELIVERY LOCATION HERE
conds = ['non_typhoon', 'typhoon', 'combined']

cond = 'non_typhoon'

hub_height = 100 # 
turbine_locs = pd.read_csv(dir_turbine_info + 'turbine_locs.txt', index_col=False)
delivery_locs = turbine_locs[['lon', 'lat']]

era5_type = 'korea_0.25' # korea_0.25, windfield_0.05
typhoon_sel = pd.read_excel(dir_tp_selected+'typhoon_selected_combine.xlsx')

wind_heights = [10, 100] # at which height of wind speed that analysis will be conducted 
wind_height = 10


#%% ---------------- NON-TYPHOON CONDITION ----------------- #
dir_working = f'{dir_extreme_anal}{cond}\\'  
os.makedirs(dir_working, exist_ok=True)
# print(dir_working)

era5_time_col = 'time' # time column name of interpolated ERA5
for tbi in range(len(delivery_locs)):


    delivery_loc = delivery_locs.iloc[tbi,:]
    era5_all_year = pd.DataFrame()
    
    for year in range(1979, 2026):
        [era5_u, era5_v]= load_era5_wind_data(dir_era5_interp, 'wind_' + str(wind_height) + 'm', year=year)
        era5_ws, era5_wd = compute_ws_wd_from_u_v(era5_u.u10.values[:,tbi], era5_v.v10.values[:,tbi])
        era5_ws = pd.DataFrame(era5_ws, columns=['WS (m/s)'])
        era5_wd = pd.DataFrame(era5_wd, columns=['WD (deg)'])
        try:
            era5_ws[era5_time_col] = era5_u.valid_time.values
            era5_wd[era5_time_col] = era5_u.valid_time.values
        except:
            era5_ws[era5_time_col] = era5_u.time.values
            era5_wd[era5_time_col] = era5_u.time.values
        era5_ws = era5_ws.iloc[:, [1,0]]
        era5_ws[era5_time_col] = pd.DatetimeIndex(era5_ws[era5_time_col]) + timedelta(hours=9)
        era5_wd[era5_time_col] = pd.DatetimeIndex(era5_wd[era5_time_col]) + timedelta(hours=9)
        era5_yearly = pd.merge(era5_ws, era5_wd, how='right', on=era5_time_col)
        era5_all_year = pd.concat([era5_all_year, era5_yearly])
    
    # remove period when typhoons affecting study site
    era5_non_tp = extract_era5_non_typhoon_wind(typhoon_sel, era5_all_year, era5_time_col)
    era5_non_tp = era5_non_tp.dropna()

    # Time series and rose plot
    fig_title = f'Turbine #{tbi+1} ({delivery_loc["lon"]}E; {delivery_loc["lat"]}N){nl}Time series (1979-2025)'
    plot_time_series_1var(data=era5_non_tp, x_label=era5_time_col, y_label='WS (m/s)', fig_size=[9,4],face_color ='#808080',
                            fig_title=fig_title, fname_save=dir_working+f'Turbine_{tbi+1}_timeseries.png', long_term=True)

    fig_title= f'Turbine #{tbi+1} ({delivery_loc["lon"]}E; {delivery_loc["lat"]}N)<br>Rose plot (1979-2025)'
    lg_title = f'ERA5<br>N={len(era5_non_tp)}<br>WS<sub>10m</sub>[m/s]<br>WD[{chr(176)}N-from]'
    rose_plot(era5_non_tp, lg_title=lg_title, speed_name='WS (m/s)', dir_name='WD (deg)', 
                fig_title=fig_title, fname_save=dir_working+f'Turbine_{tbi+1}_rose_plot.png')

    # remove data from 2026 as changing to KST time
    era5_non_tp = era5_non_tp[era5_non_tp[era5_time_col] < pd.to_datetime("2026-01-01")]
    # save ERA5 data for nontyphon condition to run extreme analysis in R, already remove gap data
    era5_non_tp.to_csv(f'{dir_working}era5_nontp_turbine{tbi+1}_{delivery_loc["lon"]}E_{delivery_loc["lat"]}N.csv')

    del dir_working


# %% Check difference of interpolated wind speed at different turbine locations
import pandas as pd
import matplotlib.pyplot as plt
dir_interp_wind = 'D:\\InProbation\\Metocean\\Analysis\\Extreme conditions\\Wind\\non_typhoon\\'
tb1_wind = pd.read_csv(dir_interp_wind+'turbine_1\\era5_nontp_turbine1_126.846E_33.55N.csv')
tb11_wind = pd.read_csv(dir_interp_wind+'turbine_8\\era5_nontp_turbine8_126.866E_33.562N.csv')

ws_diff = tb11_wind['WS (m/s)'] - tb1_wind['WS (m/s)']
ws_diff = pd.DataFrame(ws_diff)
ws_diff.insert(0, 'time', tb1_wind['time'].astype('datetime64[ns]'))

plt.figure(figsize=(6,2))
plt.plot(ws_diff['time'], ws_diff['WS (m/s)'])
plt.margins(x=0)
plt.title('Differences in wind speed between turbine 1 and turbine 8')
# %%
