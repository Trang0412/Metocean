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
crit_ws_min = convert_wind_gust_temporal(typhoon_search_cri_dhi['min_ws'])
typhoon_search_cri_mit = typhoon_search_cri_dhi.copy()
typhoon_search_cri_mit['min_ws'] = crit_ws_min


#%% Load typhoon information


# select typhoons for analysis based on criteria of wind speed relative to study site (reference point), one-time running
fname_hist_tp = dir_tp_selected + 'typhoon_selected_combine.xlsx'
# typhoon_selected = sel_typhoon_affected(typhoon_ref_point, typhoon_search_cri_mit, 
#                                         dir_btd, '', dir_tp_jra3q, fname_save=fname_hist_tp)

tp_sel_wink = pd.read_excel(fname_hist_tp, sheet_name='WINK')
tp_sel_jma = pd.read_excel(fname_hist_tp, sheet_name='JMA')
btd_typhoons = read_jma_btd(dir_btd)

# plot typhoon track 
for i in range(len(tp_sel_wink)):
    plot_typhoon_track_with_radii(btd_typhoons[btd_typhoons['Name']==tp_sel_wink['Name'][i]], 
                                  typhoon_ref_point, typhoon_search_cri_dhi, 
                                  tp_sel_wink['Name'][i], dir_tp_track_graphic)
    # tp_wink = read_typhoon_wink(dir_tp_wink, tp_sel_wink['Name'][i]+'_WIND.DAT')
    if i>=len(tp_sel_jma): continue
    # tp_wink = read_typhoon_wink(dir_tp_jra3q, tp_sel_jma['Name'][i]+'_WIND.DAT')
    plot_typhoon_track_with_radii(btd_typhoons[btd_typhoons['Name']==tp_sel_jma['Name'][i]], 
                                  typhoon_ref_point, typhoon_search_cri_dhi, 
                                  tp_sel_jma['Name'][i], dir_tp_track_graphic)
    
#%% DEFINE DELIVERY LOCATION HERE
conds = ['non_typhoon', 'typhoon', 'combined']

cond = 'non_typhoon'

hub_height = 100 # 
turbine_locs = pd.read_csv(dir_turbine_info + 'turbine_locs.txt', index_col=False)
turbine_locs = turbine_locs[['lon', 'lat']]
delivery_locs = dict({'loc1':[33.75, 126.75]}) # chosen of delivery location for wind and other parameter also

era5_type = 'korea_0.25' # korea_0.25, windfield_0.05
typhoon_sel = pd.read_excel(dir_tp_selected+'typhoon_selected_combine.xlsx')


#%% LOAD ERA5 DATA
era5_all_year = pd.DataFrame()
for year in range(1979, 2026):
    [era5_u, era5_v]= load_era5_wind_data(dir_era5_wind + era5_type +'\\', 'wind_10m', year=year)
    era5_ws, era5_wd = compute_ws_wd_from_u_v(era5_u.sel(latitude=delivery_locs['loc1'][0], longitude=delivery_locs['loc1'][1], method='nearest').u10.values, 
                                                era5_v.sel(latitude=delivery_locs['loc1'][0], longitude=delivery_locs['loc1'][1], method='nearest').v10.values)
    era5_ws = pd.DataFrame(era5_ws, columns=['WS (m/s)'])
    era5_wd = pd.DataFrame(era5_wd, columns=['WD (deg)'])

    try:
        era5_ws['Time'] = era5_u.valid_time.values
        era5_wd['Time'] = era5_u.valid_time.values
    except:
        era5_ws['Time'] = era5_u.time.values
        era5_wd['Time'] = era5_u.time.values
    era5_ws = era5_ws.iloc[:, [1,0]]
    era5_ws['Time'] = pd.DatetimeIndex(era5_ws['Time']) + timedelta(hours=9)
    era5_wd['Time'] = pd.DatetimeIndex(era5_wd['Time']) + timedelta(hours=9)
    era5_yearly = pd.merge(era5_ws, era5_wd, how='right', on='Time')
    era5_all_year = pd.concat([era5_all_year, era5_yearly])
    

#%% NON-TYPHOO CONDITION

cond = 'non_typhoon' #  non-typhoon condition

# remove period when typhoons affecting study site
dir_working = dir_extreme_anal + cond + '\\'
era5_non_tp = extract_era5_non_typhoon_wind(typhoon_sel, era5_all_year)
era5_non_tp = era5_non_tp.dropna()

# Time series and rose plot
fig_title = f'JJ_nearby ({delivery_locs["loc1"][1]}E; {delivery_locs["loc1"][0]}N){nl}Time series (1979-2025)'
plot_time_series_1var(data=era5_non_tp, x_label='Time', y_label='WS (m/s)', fig_size=[9,4],face_color ='#808080',
                        fig_title=fig_title, fname_save=dir_working+'JJ_nearby_timeseries.png', long_term=True)

fig_title= f'JJ_nearby ({delivery_locs["loc1"][1]}E; {delivery_locs["loc1"][0]}N)<br>Rose plot (1979-2025)'
lg_title = f'ERA5<br>N={len(era5_non_tp)}<br>WS<sub>10m</sub>[m/s]<br>WD[{chr(176)}N-from]'
rose_plot(era5_non_tp, lg_title=lg_title, speed_name='WS (m/s)', dir_name='WD (deg)', 
            fig_title=fig_title, fname_save=dir_working+'JJ_nearby_rose_plot.png')

# remove data from 2026 as changing to KST time
era5_non_tp = era5_non_tp[era5_non_tp['Time'] < pd.to_datetime("2026-01-01")]
# save ERA5 data for nontyphon condition to run extreme analysis in R, already remove gap data
era5_non_tp.to_csv(f'{dir_working}era5_nontp_{delivery_locs["loc1"][1]}E_{delivery_locs["loc1"][0]}N.csv')

# # % %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# # do extreme analysis, fixed with AM and Gumbel for now. May 12
# era5_non_tp = era5_non_tp.set_index('Time')

# ex_type = 'high'
# block_size = '365.2425D'
# ex_method = 'BM'
# rp_size = '365.2425D'

# # omni directional analysis
# nontp_extreme = pyextremes.get_extremes(era5_non_tp['WS (m/s)'], ex_method, extremes_type=ex_type, 
#                                         block_size=block_size, errors='raise', min_last_block=None)
# nontp_extreme.to_excel(dir_working+'extremes.xlsx')

# #%% Using Scipy 
# # fit gumbel_r
# loc, scale = sstats.gumbel_r.fit(nontp_extreme)

# # probabilities
# F = sstats.gumbel_r.cdf(nontp_extreme, loc=loc, scale=scale)

# # exceedance probability
# Pex = 1 - F

# # return period
# T = 1 / Pex

# df = pd.DataFrame({
#     'value': nontp_extreme,
#     'F(x)': F,
#     'P_exceed': Pex,
#     'ReturnPeriod_years': T
# })

# print(df)


# # return period
# Ts = [1, 10, 50, 100]

# # non-exceedance probability
# ps = 1 - 1/Ts

# # 100-year return level
# [x100 ]= stats.gumbel_r.ppf(ps, loc=loc, scale=scale)

# print(f"100-year event = {x100:.2f} m/s")


# #%% Using pyextreme

# nontp_wind_rp = pyextremes.get_return_periods(
#     ts=era5_non_tp['WS (m/s)'],
#     extremes=nontp_extreme,
#     extremes_method=ex_method,
#     extremes_type=ex_type,
#     block_size=block_size,
#     return_period_size=rp_size,
#     plotting_position="weibull",
# )


# nontp_ext_model = pyextremes.get_model(model='MLE', extremes=nontp_extreme,
#                              distribution='gumbel_r')
# nontp_ext_model.fit()
# Ts = np.array([1.1, 10, 50, 100, 10000])
# return_values = nontp_ext_model.get_return_value(nontp_wind_rp['exceedance probability'], alpha=0.95)

# #%%

# # nontp_wind_rp.to_excel(dir_working+'omnidir_RP.xlsx')
# # nontp_wind_model.fit_model(model='MLE', distribution='gumbel_r')

# # nontp_wind_model.plot_extremes()
# # plt.margins(x=0)
# # plt.show()


# # summary return values and CI corresponding to defined return period
# # summary = nontp_wind_model.get_summary(return_period=[1.1, 10, 50, 100, 1000],
#                                     #    alpha=0.95,n_samples=200,)
# # print(summary)
# # summary.to_excel(dir_working+'extreme_omnidir_RP_summary.xlsx')
# # # # plot_diagnostic seem to run forever
# # import matplotlib
# # matplotlib.use("Agg")
# # nontp_wind_model.plot_diagnostic(alpha=0.95)
# # plt.savefig("diag.png")
# # plt.close()
# # # plt.show()



# # directionaly analysis
# dir_bin_width = 30
# dir_bins = np.arange(0, 361, dir_bin_width)
# for i, dir_bin in enumerate(dir_bins):
#     era5_directional = era5_non_tp[(era5_non_tp['WD (deg)'] >= dir_bins[i]) & (era5_non_tp['WD (deg)'] < dir_bins[i])]
#     nontp_dir_wind_model = pyextremes.EVA(era5_non_tp['WS (m/s)'])
#     nontp_dir_wind_model.get_extremes(ex_method, extremes_type=ex_type, block_size=block_size, errors='raise', min_last_block=None)
#     nontp_dir_wind_model.fit_model(model='MLE', distribution='gumbel_r')

#     # summary = nontp_wind_model.get_summary(return_period=[1.1, 2, 5, 10, 25, 50, 100, 250, 500, 1000],
#     #                                     alpha=0.95,n_samples=1000,)




# #%% TODO: TYPHOON CONDITIONS
# cond = 'typhoon' # 2. Typhoon conditions


# select_typhoons = pd.read_excel(dir_data + 'Typhoon_wind\\typhoon_historical_data.xlsx', 
#                                 sheet_name='Typhoons selected', skiprows=2)
# col_names = ['Code', 'Name', 'Impact period']
# select_typhoons = select_typhoons[col_names]
# select_typhoons['Code'] = select_typhoons['Code'].apply(lambda x: f'{x:04d}')

# # metadata will read as 2-columns with information on 1 tyhoon are presented using 3 rows
# mdata_typhoon = read_typhoon_wink_metadata(dir_tp_wink, 'HYB_TC_INPUTS.dat') 
# wink_grid = dict({'lat':wink_lat_points, 'lon':wink_lon_points})
# # all_typhoons = dict

# for ti in range(len(select_typhoons)):
#     try:
#         typhoon_name = select_typhoons['Code'][ti] + '_' + select_typhoons['Name'][ti]
#         ws, wd = read_typhoon_wink(dir_tp_wink, typhoon_name + '_WIND.dat')
#         print(f'Wind field data loaded for typhoon {typhoon_name}')
#     except:
#         print(f'There is no wind data for typhoon {typhoon_name}')


# do_extreme_wind_analysis()
        
# #%% TODO: COMBINED TYPHOON/NON-TYPHOON CONDITIONS
# combined_wind = combine_typhoon_wind_data()
# do_extreme_wind_analysis()

# %% INSPECT INTERPOLATED JRA3Q_WIND TO WINK GRID USING CDO
import xarray as xr

dir_jra = 'D:\\InProbation\\Metocean\\Data\\Typhoon_wind\\jrq3q_interp_try1\\turbine_interp\\'
dir_era5 = 'D:\\InProbation\\Metocean\\Data\\ERA5\\korea_0.25\\wind_10m_u_v\\2025\\'

jra_turbine_locs = 'u_2001010100_2001013118.nc'
jra_tb = xr.open_dataset(dir_jra + jra_turbine_locs)


jra_wink_grd_name = 'u10_202512_wink_grd.nc'
era5_wink_grd_name = 'u10_202512_wink_grd.nc'

jra_grd = xr.open_dataset(dir_jra + jra_wink_grd_name)
era5_grd = xr.open_dataset(dir_era5 + era5_wink_grd_name)
# %%
