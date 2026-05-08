'''
- separate_tide_nontide(): Harmonic tidal analysis using U-tide toolbox
    ref: https://github.com/wesleybowman/UTide

        


@Author: Le Thi Trang
@Date: Mar 10, 2026

DNVGL-GL-2018: Metocean
- Water level consists of a mean

'''

#%%
import sys
import os
sys.path.append('D:\\InProbation\\Metocean\\scripts')

import common_processing
import visualizing
import data_loading
import metocean_metadata
import wind_data_processing
import water_data_processing


from data_loading import *
from common_processing import *
from visualizing import *
from water_data_processing import *
from datetime import timedelta
from statsmodels.distributions.empirical_distribution import ECDF

from pyextremes import EVA

import scipy.stats as sstats
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import gumbel_r, genpareto, expon
from pathlib import Path




#%%
project_dir = 'D:\\InProbation\\Metocean\\'
data_dir = project_dir + 'Data\\'
dir_modeled_data = data_dir + 'Modeled\\'
dir_obs_data = data_dir + 'Observations\\'
modeled_data_name = 'refined_mesh\\simulation_20260422\\'

dir_save_fig = 'D:\\InProbation\\Metocean\\Analysis\\Obs_Modeled\\Water\\simulation_260430\\'
fname_metadata = 'Model_calibration_metadata.xlsx' 
working_dir = project_dir + 'Analysis\\'

vars_metadata = pd.read_excel(working_dir + fname_metadata, sheet_name='Water', header=1)

stations = vars_metadata['Name'].dropna()
providers = vars_metadata['Provider'].dropna()

checking_year = 2024
vars_dtype = ['datetime64[ns]', 'float']
major_tidal_conts = ['M2', 'K1', 'O1', 'S2']


#%% ####################################################################################################
# April 30, 2026: Working with modeled water elevation data

# load observation data
provider = 'KHOA' # depend on the output of simulation
time_stamp = '관측시간'
param_checking = '조위(cm)'
vars_type = [time_stamp, '조위(cm)']
dir_simul = data_dir + 'Modeled\\simulation_260430\\'

# assuming metadata will stay the same for all simulation case
adcirc_params, wl_stations = read_fort15_wl(dir_simul+'hot_20250101\\')
hotfolders = [f.name for f in Path(dir_simul).rglob(f'hot_*') if f.is_dir()]

all_obs_data = dict()
year = 2025 # fix for now, will change accordingly
for si in range(len(wl_stations)):
    data_temp = load_obs_all_data(dir_data + 'Observations\\', 'KHOA', wl_stations['Name'][si], year)
    data_temp = data_temp[vars_type].astype(dict(zip(vars_type, vars_dtype)))
    data_temp = data_temp.groupby(pd.Grouper(key=vars_type[0], freq='10min')).mean().reset_index()
    data_temp[param_checking] = data_temp[param_checking] - data_temp[param_checking].mean()
    all_obs_data[wl_stations['Name'][si]] = data_temp
    del data_temp

# laod modelled data separatedly for each 'hot_' folder
for flder in hotfolders:
    dir_hot = dir_simul + flder + '\\'
    # modeled data will be shifted to KST time by default, it not set to_kst=False
    all_modeled_data = load_fort61(dir_hot, col_names=[time_stamp, param_checking])

    for si in range(len(wl_stations)):
        df_combine = pd.merge(all_obs_data[wl_stations['Name'][si]], all_modeled_data[wl_stations['Name'][si]], 
                               on=time_stamp, how='right', suffixes=['_obs', '_modeled'])


        fname_save = f'{flder}_{wl_stations["Name"][si]}'
        ylabel_text = 'Water elevation'
        fig_title = f'{wl_stations["Name"][si]}, {df_combine.iloc[0,0].date()} - {df_combine.iloc[-1,0].date()}'
        plot_time_series_2vars(df_combine,
                            'Observation', 'Modeled', [9, 4], fig_title, dir_save_fig + '\\'+ fname_save,
                            fc1='#F67A0D', fc2='#3C88BD', plot_type='MIT', lstyle1 = '-', lstyle2='--',
                            ylabel_text=ylabel_text, xtick_rotation=0)
        
        scatter_plot_ERA5_against_meas(df_combine[[time_stamp, param_checking+'_obs', param_checking+'_modeled']], 
                                [9,6], [0, np.max([250, df_combine.iloc[:,1].max()+5, df_combine.iloc[:,2].max()+5])], 
                                bin_width=10, x_tick=50, fig_title=fig_title, fname_save = dir_save_fig + '\\'+ fname_save+'_scatter')
        # del df_combine

        # #%% ####################################################################################################
        # # TIDAL HARMONICS ANALYSIS FOR OBSERVATION AND MODELED DATA
        fname1 = dir_save_fig + '\\'+ f'{flder}_{wl_stations["Name"][si]} harmonic_analysis'
        fname2 = dir_save_fig + '\\'+ f'{flder}_{wl_stations["Name"][si]} tidal_constiuents'
        major_consts_obs, major_consts_mdl = plot_major_tidal_cons_obs_mdl(df_combine, time_stamp, param_checking, wl_stations.loc[si], major_tidal_conts, fname1, fname2)

        nconsts = len(major_consts_mdl)
        if nconsts:
            fig, axs = plt.subplots(nrows=nconsts)
            fig.suptitle(fig_title+' major consituents')
            for i, axi in enumerate(axs):
                const_name = list(major_consts_mdl.keys())[i]
                axi.plot(major_consts_obs[const_name], label='Observation', linestyle='-')
                axi.plot(major_consts_mdl[const_name], label='Modeled', linestyle='--')
                axi.set_title(const_name)
                axi.legend()
            plt.savefig(dir_save_fig + '\\'+ f'{flder}_{wl_stations["Name"][si]} major_consts')

    
# #%% ####################################################################################################
# # EXTREME VALUE ANALYSIS
# # Loading historical data (20 years of water level data for Seongsanpo, Mar 30)
# # for i in range(len(stations)):
# i = 0 # testing Seongsanpo (0), Seoguipo (2) for extreme water level   
# print(f'------------------------------ Load data for {stations[i]} ------------------------------')    

# if providers[i] == 'KHOA':
#     time_stamp = '관측시간'
    
# elif providers[i] == 'KMA':
#     time_stamp = '일시'

# vars_type = [time_stamp, '조위(cm)']


# checking_durations = vars_metadata['Data available'][i]
# checking_durations = checking_durations.split('-')
# checking_years = np.arange(int(checking_durations[0]), int(checking_durations[1]), 1)
# all_year_data_orig = pd.DataFrame(columns=vars_type)

# for checking_year in checking_years:

#     data = load_obs_all_data(dir_data + 'Observations\\', providers[i], stations[i], checking_year)
#     water_data = data[vars_type].astype(dict(zip(vars_type, vars_dtype)))
#     water_data = water_data.groupby(pd.Grouper(key=vars_type[0], freq='1h')).mean().reset_index()

#     all_year_data_orig = pd.concat([all_year_data_orig, water_data])

# #%% Convert data to meter level and relative to MSL
# all_year_data_orig.columns = ['Time', 'Water level [m]']

# # TODO: April 21, remove trend of water data 
# # all_year_data = remove_water_trend(water_data)


# all_year_data_orig['Water level [m]'] = all_year_data_orig['Water level [m]']/100

# # checking gap in data before running tide separation
# time_deltas = all_year_data_orig['Time'].diff()
# large_gaps = time_deltas[time_deltas > timedelta(days=3)]
# if len(large_gaps) == 0:
#     print('There is no data gap time more than 3 days')
# else:
#     print(f'!!! There are large data gap more than 3 days, e.g., at{large_gaps.iloc[0]}')

#%% Harmonic analysis to compare with previous data from MIT pdf file JEBCO
# Load Seongsanpo data for 2016 and 2017
i=0 # Seongsanpo
vars_type = [time_stamp, '조위(cm)']
checking_years = [2025]
all_year_data_orig = pd.DataFrame(columns=vars_type)
param_checking = '조위(cm)'

for checking_year in checking_years:
    data = load_obs_all_data(dir_data + 'Observations\\', providers[i], stations[i], checking_year)
    water_data = data[vars_type].astype(dict(zip(vars_type, vars_dtype)))
    all_year_data_orig = pd.concat([all_year_data_orig, water_data])

spec_data_orig =  all_year_data_orig[(all_year_data_orig.iloc[:,0]>='2016-12-09') & (all_year_data_orig.iloc[:,0]<='2017-01-08')]
spec_data_orig =  all_year_data_orig[(all_year_data_orig.iloc[:,0]>='2025-01-01') & (all_year_data_orig.iloc[:,0]<='2025-02-01')]



spec_data, coefs = separate_tide_nontide(spec_data_orig, vars_metadata['Latitude'][i])
hat = spec_data['pred'].max()
lat = spec_data['pred'].min()
msl = spec_data[param_checking].mean()
spec_data['pred'] = spec_data['pred'] + msl


# plot excerpt of data
fig, (ax0, ax1, ax2) = plt.subplots(figsize=(9,6), nrows=3)

ax0.plot(spec_data_orig.iloc[:,0], spec_data_orig[param_checking], color="C0", linewidth=1)
ax0.set_yticks(list(np.arange(-50, 350, 50)))
ax0.grid(axis='y', color='lightgray')
ax0.xaxis.set_major_formatter(mdates.DateFormatter("%d"))
ax0.xaxis.set_major_locator(mdates.DayLocator())
ax0.set_ylabel('Observation [cm]')

ax1.plot(spec_data.iloc[:,0], spec_data['pred'], color="C1", linewidth=1)
ax1.set_yticks(np.arange(-50, 350, 50))
ax1.grid(axis='y', color='lightgray')
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d"))
ax1.xaxis.set_major_locator(mdates.DayLocator())
ax1.set_ylabel('Prediction [cm]')

ax2.plot(spec_data.iloc[:,0], spec_data['res'], color="C2", linewidth=1)
ax2.set_yticks(np.arange(-60, 90, 30))
ax2.grid(axis='y', color='lightgray')
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d"))
ax2.xaxis.set_major_locator(mdates.DayLocator())
ax2.set_ylabel('Residual [cm]')
fig.suptitle(stations[i])
fig.autofmt_xdate() 
plt.xticks(rotation=0)
plt.show()

# get amplitude and phase of major tidal consituents
pd_major_conts = pd.DataFrame(index=major_tidal_conts, columns =['amplitude', 'phase'])
consts_index = [i for i in range(len(coefs['name'])) if coefs['name'][i] in major_tidal_conts]
for i in consts_index:
    pd_major_conts.loc[coefs['name'][i], 'amplitude']= coefs['A'][i]
    pd_major_conts.loc[coefs['name'][i], 'phase']= coefs['g'][i]

# extract data from hwp file


# #%% plot tide peak
# all_year_data = all_year_data.set_index('Time')

# high_tide_model = EVA(all_year_data['pred'])
# high_tide_model.get_extremes(method='BM', extremes_type='high',
#                              block_size="365.2425D", )
# high_tide_model.plot_extremes(figsize=(9,3))
# plt.show()

# low_tide_model = EVA(all_year_data['pred'])
# low_tide_model.get_extremes(method='BM', extremes_type='low',
#                              block_size="365.2425D", )
# low_tide_model.plot_extremes(figsize=(9,3))
# plt.show()
# %%
