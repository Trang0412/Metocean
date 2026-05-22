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

import scipy.stats as sstats
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import re


#%%
project_dir = 'D:\\InProbation\\Metocean\\'
data_dir = project_dir + 'Data\\'
dir_modeled_data = data_dir + 'Modeled\\'
dir_obs_data = data_dir + 'Observations\\'

# assuming metadata will stay the same for all simulation case
fname_metadata = 'Model_calibration_metadata.xlsx' 
working_dir = project_dir + 'Analysis\\'

vars_metadata = pd.read_excel(working_dir + fname_metadata, sheet_name='Water', header=1)

stations = vars_metadata['Name'].dropna()
providers = vars_metadata['Provider'].dropna()

vars_dtype = ['datetime64[ns]', 'float']
major_tidal_conts = ['M2', 'K1', 'O1', 'S2']

provider = 'KHOA' # depend on the output of simulation
khoa_timestamp = '관측시간'
param_checking = '조위(cm)'
vars_type = [khoa_timestamp, '조위(cm)']

year = 2023 # fix for now, will change accordingly
mdl_to_future = 4 # May 22
simul_flder_name = f'simulation_July2023'
start_reading_idx_fort61 = 432000
dir_save_fig = 'D:\\InProbation\\Metocean\\Analysis\\Obs_Modeled\\Water\\' + simul_flder_name + '\\'
os.makedirs(dir_save_fig, exist_ok=True)

# load observation data
dir_simul = data_dir + 'Modeled\\' + simul_flder_name+ '\\'
_, wl_stations = read_fort15_wl(dir_simul)
hotfolders = [f.name for f in Path(dir_simul).rglob(f'hot_*') if f.is_dir()]

# wl_stations = wl_stations.loc[1:2].reset_index() # temporary for May 22, testing for water level
# wl_stations = pd.DataFrame(dict({'Name': ['성산포', '제주'],
#                                  'lon': [126.92478, 126.544024],
#                                  'lat': [33.47475, 33.528512]}))

#%% ####################################################################################################
# April 30, 2026: Load obsevation data
all_obs_data = dict()

for si in range(len(wl_stations)):
    data_temp = load_obs_all_data(dir_data + 'Observations\\', 'KHOA', wl_stations['Name'][si], year)
    data_temp = data_temp[vars_type].astype(dict(zip(vars_type, vars_dtype)))

    fig, (ax1, ax2) = plt.subplots(figsize=(14,6), nrows=2)
    plt.suptitle(wl_stations['Name'][si])
    ax1.plot(data_temp.iloc[:,0], data_temp.iloc[:,1])
    # ax1.set_title('Before QC')
    ax1.tick_params(axis='x', which='major', labelsize=20)

    ######################## # QC temporary # ######################## 
    # QC temporary
    data_temp = data_temp.set_index(khoa_timestamp)
    data_interval = data_temp.index.to_series().diff().dropna().unique() / pd.Timedelta(minutes=1)
    changes = data_temp.diff()
    if len(data_interval)>1: print('There more than 1 intervals of recording data')

    # value_groups = (changes != changes.shift()).cumsum()
    if data_interval[0]==1: 
        # stuck_periods = data_temp.groupby(value_groups).filter(lambda x: len(x) > 20).reset_index()
        # data_temp.loc[stuck_periods[time_stamp]] = pd.NA
        data_temp[changes.abs() > 5] = pd.NA
    data_temp = data_temp.reset_index()
    ax2.plot(data_temp.iloc[:,0], data_temp.iloc[:,1])
    # ax2.set_title('After QC')
    ax2.tick_params(axis='x', which='major', labelsize=20)
    plt.savefig(f'{dir_save_fig}{wl_stations["Name"][si]}_obs_QC.png')
    plt.show()
    ######################## # End QC # ######################## 

    data_temp = data_temp.groupby(pd.Grouper(key=vars_type[0], freq='1min')).mean().reset_index()
    data_temp[param_checking] = data_temp[param_checking] - data_temp[param_checking].mean()
    all_obs_data[wl_stations['Name'][si]] = data_temp

    del data_temp

#%% load modelled data separatedly for each 'hot_' folder
dir_save_fig = 'D:\\InProbation\\Metocean\\Analysis\\Obs_Modeled\\Water\\' + simul_flder_name + '_separate\\'
os.makedirs(dir_save_fig, exist_ok=True)

for fi, flder in enumerate(hotfolders):
    # May 13, to be replaced later
    # start_simul_time = pd.to_datetime(f'{flder[4:8]}-{flder[8:10]}-{flder[10:12]} 00:00:00', format="%Y-%m-%d %H:%M:%S")

    dir_hot = dir_simul + flder + '\\'
    # modeled data will be shifted to KST time by default, it not set to_kst=False
    simul_time = read_fort26(dir_hot)
    all_modeled_data = load_fort61(dir_hot, simul_time['start'], time_from_fort26=True,
                                   col_names=[khoa_timestamp, param_checking], 
                                   start_reading_idx=start_reading_idx_fort61, to_future=mdl_to_future)
    
    for si in range(len(wl_stations)):

        df_combine = pd.merge(all_obs_data[wl_stations['Name'][si]], all_modeled_data[wl_stations['Name'][si]], 
                            on=khoa_timestamp, how='right', suffixes=['_obs', '_modeled'])

        fname_save = f'{flder}_{wl_stations["Name"][si]}_{mdl_to_future}_day_to_future'
        ylabel_text = 'Water level (cm)'
        fig_title = f'{wl_stations["Name"][si]}, modeled data move {mdl_to_future} to future{nl}{df_combine.iloc[0,0].date()} - {df_combine.iloc[-1,0].date()}'
        plot_time_series_2vars(df_combine,
                            'Observation', 'Modeled', [9, 4], fig_title, dir_save_fig +  fname_save,
                            fc1='#F67A0D', fc2='#3C88BD', plot_type='MIT', lstyle1 = '-', lstyle2='--',
                            ylabel_text=ylabel_text, xtick_rotation=45)
        
        df_combine.to_excel(dir_save_fig + f'{wl_stations["Name"][si]}_{flder}_{mdl_to_future}_day_to_future.xlsx')


#%% Combine different simulations, May 13, 2026 
dir_save_fig = 'D:\\InProbation\\Metocean\\Analysis\\Obs_Modeled\\Water\\' + simul_flder_name + '_combined\\'
os.makedirs(dir_save_fig, exist_ok=True)
for si in range(len(wl_stations)):
    long_data = pd.DataFrame(columns=[khoa_timestamp, f'{param_checking}_obs', f'{param_checking}_modeled'])

    for fi, flder in enumerate(hotfolders):

        dir_hot = dir_simul + flder + '\\'
        # May 13, Reading directly from folder's name, when simulation crashed 
        # start_simul_time = pd.to_datetime(f'{flder[4:8]}-{flder[8:10]}-{flder[10:12]} 00:00:00', format="%Y-%m-%d %H:%M:%S")

        # Reading directly from fort.26, when simulation finished normally 
        simul_time = read_fort26(dir_hot)

        all_modeled_data = load_fort61(dir_hot, simul_time['start'], time_from_fort26=True,
                                       col_names=[khoa_timestamp, param_checking], 
                                       start_reading_idx=start_reading_idx_fort61,to_future=mdl_to_future)
        df_combine = pd.merge(all_obs_data[wl_stations['Name'][si]], all_modeled_data[wl_stations['Name'][si]], 
                            on=khoa_timestamp, how='right', suffixes=['_obs', '_modeled'])
        # combine data for these two simulations
        long_data = pd.concat([long_data, df_combine], ignore_index=True).drop_duplicates(subset=[khoa_timestamp], keep='first')

    fname_save = f'{wl_stations["Name"][si]}_{mdl_to_future}_day_to_future'
    ylabel_text = 'Water level (cm)'
    fig_title = f'{wl_stations["Name"][si]}, modeled data move {mdl_to_future} to future{nl}{long_data.iloc[0,0].date()} - {long_data.iloc[-1,0].date()}'

    # create full continuous time index
    long_data = long_data.set_index(khoa_timestamp)
    full_index = pd.date_range(start=long_data.index.min(),
                            end=long_data.index.max(),
                            freq='1min')

    long_data = long_data.reindex(full_index)
    long_data.index.name = khoa_timestamp
    long_data = long_data.reset_index()

    plot_time_series_2vars(long_data,
                        'Observation', 'Modeled', [9, 3], fig_title, dir_save_fig +  fname_save,
                        fc1='#F67A0D', fc2='#3C88BD', plot_type='MIT', lstyle1 = '-', lstyle2='--',
                        ylabel_text=ylabel_text, xtick_rotation=45)
    
    long_data.to_excel(dir_save_fig + f'{wl_stations["Name"][si]}_{mdl_to_future}_day_to_future.xlsx')




# %% May 22, 2026 # Read 
dir_modeled_data = 'D:\\InProbation\Metocean\\Data\\Modeled\\'
simul_folder ='simulation_260522_v2\\hot_20250101'
dir_save = 'D:\\InProbation\\Metocean\\Analysis\\Obs_Modeled\\Water\\'
os.makedirs(f'{dir_save}{simul_folder}', exist_ok=True)

files_out = ['TS1.out', 'TS2.out']

# origmesh_site_bathymetry_v1
modeled_all_vars = ['Time', 'Watlev']
modeled_vars_type = ['string', 'float']

for si in range(len(wl_stations)):
    modeled_data = pd.DataFrame(columns=modeled_all_vars)
    clean_lines = []
    with open(f'{dir_modeled_data}{simul_folder}\\{files_out[si]}', "r", encoding="utf-8") as f:
        for line in f:
            # replace all whitespace-like chars with single space
            line = re.sub(r"\s+", " ", line.strip())
            clean_lines.append(line)

        data_temp = pd.read_csv(
            pd.io.common.StringIO("\n".join(clean_lines)),
            sep=" ", index_col=False,
            header=None, skiprows=7, names=modeled_all_vars, dtype=dict(zip(modeled_all_vars, modeled_vars_type)))

        # convert 1st colum to datetime
        data_temp['Time'] = data_temp['Time'].apply(lambda x: pd.to_datetime(datetime(year=int(x[0:4]), 
                                                                                      month=int(x[4:6]), 
                                                                                      day=int(x[6:8]), 
                                                                                      hour=int(x[9:11]),
                                                                                      minute=int(x[11:13]),
                                                                                      second=int(x[13:15])
                                                                                      )))
        modeled_data = pd.concat([modeled_data, data_temp], ignore_index=True).drop_duplicates(subset=['Time'], keep='first')
        del data_temp

    modeled_data = modeled_data.rename(columns={'Time':khoa_timestamp, 'Watlev':param_checking})
    modeled_data[param_checking] = modeled_data[param_checking]*100 #convert modeled water level to cm
    # correct modeled data to KST time
    modeled_data[khoa_timestamp] = pd.DatetimeIndex(modeled_data[khoa_timestamp]) + timedelta(hours=9)
    modeled_data_moved = modeled_data.copy()

    # Moving modeled date to before and after 1,2, 3 days compared to obs data
    for day_move in range(-4,8,1):
        modeled_data_moved[khoa_timestamp] = pd.DatetimeIndex(modeled_data[khoa_timestamp]) + timedelta(days=day_move)
        combined_wl = modeled_data_moved.set_index(khoa_timestamp).join(all_obs_data[wl_stations['Name'][si]].set_index(khoa_timestamp), 
                                                                    how='inner', lsuffix='_mdl', rsuffix='_obs').dropna().reset_index()
        # save data and plot figure
        combined_wl.to_excel(f'{dir_save}{simul_folder}\\{wl_stations["Name"][si]}{day_move}.xlsx')
        combined_wl = combined_wl[[khoa_timestamp, f'{param_checking}_obs', f'{param_checking}_mdl']]

        #plot figure
        fname_save = f'{dir_save}{simul_folder}\\{wl_stations["Name"][si]}'
        fname_save = ''
        ylabel_text = 'Water level (cm)'
        fig_title = f'{wl_stations["Name"][si]}, Modeled data moving {day_move} compared to Observation{nl}{combined_wl.iloc[0,0].date()} - {combined_wl.iloc[-1,0].date()}'
        plot_time_series_2vars(combined_wl[[khoa_timestamp, param_checking+'_obs', param_checking+'_mdl']],
                                'Observation', 'Modeled', [9, 4], fig_title, fname_save,
                                fc1='#F67A0D', fc2='#3C88BD', plot_type='MIT', lstyle1 = '-', lstyle2='--',
                                ylabel_text=ylabel_text, xtick_rotation=45)

# %%
