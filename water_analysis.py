'''
- separate_tide_nontide(): Harmonic tidal analysis using U-tide toolbox
    ref: https://github.com/wesleybowman/UTide

        


@Author: Le Thi Trang
@Date: Mar 10, 2026

DNVGL-GL-2018: Metocean
- Water level consists of a mean

'''

#%%

from data_loading import *
from common_processing import *
from visualizing import *
from datetime import timedelta
from statsmodels.distributions.empirical_distribution import ECDF

from pyextremes import EVA

import scipy.stats as sstats
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import gumbel_r, genpareto, expon

#%%
project_dir = 'D:\\InProbation\\Metocean\\'
data_dir = project_dir + 'Data\\'

fname_metadata = 'Model_calibration_metadata.xlsx' 
working_dir = project_dir + 'Analysis\\'

vars_metadata = pd.read_excel(working_dir + fname_metadata, sheet_name='Water', header=1)

stations = vars_metadata['Name'].dropna()
providers = vars_metadata['Provider'].dropna()

checking_year = 2024
vars_dtype = ['datetime64[ns]', 'float']

#%% Loading historical data (20 years of water level data for Seongsanpo, Mar 30)
# for i in range(len(stations)):
i = 2 # testing Seongsanpo (0), Seoguipo (2) for extreme water level   
print(f'------------------------------ Load data for {stations[i]} ------------------------------')    

if providers[i] == 'KHOA':
    time_stamp = '관측시간'
    
elif providers[i] == 'KMA':
    time_stamp = '일시'

vars_type = [time_stamp, '조위(cm)']


checking_durations = vars_metadata['Data available'][i]
checking_durations = checking_durations.split('-')
checking_years = np.arange(int(checking_durations[0]), int(checking_durations[1]), 1)
all_year_data = pd.DataFrame(columns=vars_type)

for checking_year in checking_years:

    data = load_obs_all_data(dir_data + 'Observations\\', providers[i], stations[i], checking_year)
    water_data = data[vars_type].astype(dict(zip(vars_type, vars_dtype)))
    water_data = water_data.groupby(pd.Grouper(key=vars_type[0], freq='1h')).mean().reset_index()

    all_year_data = pd.concat([all_year_data, water_data])

#%% Convert data to meter level and relative to MSL
all_year_data.columns = ['Time', 'Water level [m]']
all_year_data['Water level [m]'] = all_year_data['Water level [m]']/100

# checking gap in data before running tide separation
time_deltas = all_year_data['Time'].diff()
large_gaps = time_deltas[time_deltas > timedelta(days=3)]
if len(large_gaps) == 0:
    print('There is no data gap time more than 3 days')
else:
    print(f'!!! There are large data gap more than 3 days, e.g., at{large_gaps.iloc[0]}')

#%% Harmonic analysis
all_year_data = separate_tide_nontide(all_year_data, vars_metadata['Latitude'][i])
hat = all_year_data['pred'].max()
lat = all_year_data['pred'].min()
msl = all_year_data['Water level [m]'].mean()

fig, (ax0, ax1, ax2) = plt.subplots(figsize=(12,3), nrows=3, sharey=True, sharex=True)

ax0.plot(all_year_data['Time'], all_year_data['anomaly'], label="Observations", color="C0")
ax1.plot(all_year_data['Time'], all_year_data['pred'], label="Prediction", color="C1")
ax2.plot(all_year_data['Time'], all_year_data['res'], label="Residual", color="C2")
fig.legend(ncol=3, loc="upper center")
plt.show()

#%% plot tide peak
all_year_data = all_year_data.set_index('Time')

high_tide_model = EVA(all_year_data['pred'])
high_tide_model.get_extremes(method='BM', extremes_type='high',
                             block_size="365.2425D", )
high_tide_model.plot_extremes(figsize=(9,3))
plt.show()

low_tide_model = EVA(all_year_data['pred'])
low_tide_model.get_extremes(method='BM', extremes_type='low',
                             block_size="365.2425D", )
low_tide_model.plot_extremes(figsize=(9,3))
plt.show()
# %%
