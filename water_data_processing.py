'''
Suite of function specified for water data processing
- plot_major_tidal_cons_obs_mdl(): 
- remove_water_trend(): 
- separate_tide_nontide(): 


@Author: Le Thi Trang
@Date: May 06, 2026
'''


import numpy as np
import math
import pandas as pd
from scipy.signal import welch
import xarray as xr
from visualizing import *
from geopy.distance import great_circle
from geopy.distance import geodesic
from matplotlib import patches as mpatches
from scipy import signal



def plot_major_tidal_cons_obs_mdl(df_combine, time_stamp, param_checking, wl_station, major_tidal_conts, dir_save_fig, fname1, fname2, 
                                  save_coef=['M2', 'K1', 'O1', 'S2']):
    '''Plot the tidal constituents from observation and modelled data
    Parameters:
        -df_combine: pd.DataFrame, dataframe of water level with 3 columns of [time_stamp, observation, modelled]
        -param_checking: str, column's name of water level. e.g., 조위(cm)
        -wl_stations: pd.DataFrame, dataframe of specific station in check, with 3 columns of [Name, lon, lat]
        -major_tidal_conts: list, list of major tidal consituents for checking
        -fname1: str, saving name for figure file of summation of tidal consituents
        -fname2: str, saving name for figure file of amplitude and phase of consituents interested
    Returns:
    '''
    # TIDAL HARMONICS ANALYSIS FOR OBSERVATION AND MODELED DATA
    obs_data, obs_coefs = separate_tide_nontide(df_combine[[time_stamp, param_checking+'_obs']], wl_station['lat'])
    mdl_data, mdl_coefs = separate_tide_nontide(df_combine[[time_stamp, param_checking+'_modeled']], wl_station['lat'])

    # plot summation of tidal harmonic data
    fig1, (ax0, ax1, ax2) = plt.subplots(figsize=(9,6), nrows=3, sharey=True, sharex=True)

    ax0.plot(obs_data[time_stamp], obs_data[param_checking+'_obs'], label="Observations", 
                color='#F67A0D', linestyle='-')
    ax0.plot(mdl_data[time_stamp], mdl_data[param_checking+'_modeled'], label="Modelled", 
                color='#3C88BD', linestyle='--')
    ax0.set_title('Water level (cm)', fontsize=10)

    ax1.plot(obs_data[time_stamp], obs_data['pred'], 
                color='#F67A0D', linestyle='-')
    ax1.plot(mdl_data[time_stamp], mdl_data['pred'], 
                color='#3C88BD', linestyle='--')
    ax1.set_title('Prediction', fontsize=10)
    
    ax2.plot(obs_data[time_stamp], obs_data['res'], 
                color='#F67A0D', linestyle='-')
    ax2.plot(mdl_data[time_stamp], mdl_data['res'], 
                color='#3C88BD', linestyle='--')
    ax2.set_title('Residual', fontsize=10 )
    
    # ax2.set_ylim(-200, 200)
    fig1.suptitle(f'{wl_station["Name"]}', fontsize=14, fontweight='bold')
    fig1.legend(ncol=3, loc="outside upper right")
    plt.xticks(rotation=45)
    if fname1!='':
        plt.savefig(dir_save_fig+fname1)

    # check coefficients consistency
    common_consts = np.intersect1d(obs_coefs['name'], mdl_coefs['name'])
    if len(save_coef):
        common_consts = np.intersect1d(common_consts, save_coef)
    
    major_consts_obs = dict()
    major_consts_mdl = dict()
    if len(common_consts):
    
        obs_a = dict([(obs_coefs['name'][i], obs_coefs['A'][i]) for i in range(len(obs_coefs['name'])) if obs_coefs['name'][i] in common_consts])
        mdl_a = dict([(mdl_coefs['name'][i], mdl_coefs['A'][i]) for i in range(len(mdl_coefs['name'])) if mdl_coefs['name'][i] in common_consts])

        obs_g = dict([(obs_coefs['name'][i], obs_coefs['g'][i]) for i in range(len(obs_coefs['name'])) if obs_coefs['name'][i] in common_consts])
        mdl_g = dict([(mdl_coefs['name'][i], mdl_coefs['g'][i]) for i in range(len(mdl_coefs['name'])) if mdl_coefs['name'][i] in common_consts])

        if len(save_coef):
            save_coef_df = pd.DataFrame(columns=['name', 'amp_obs', 'amp_mdl', 'phase_obs', 'phase_mdl'])
            save_coef_df['name'] = list(obs_a.keys())
            save_coef_df['amp_obs'] = list(obs_a.values())
            save_coef_df['amp_mdl'] = list(mdl_a.values())
            save_coef_df['phase_obs'] = list(obs_g.values())
            save_coef_df['phase_mdl'] = list(mdl_g.values())
            save_coef_df.to_excel(f'{dir_save_fig}UTide_coefs{wl_station["Name"]}.xlsx')

        fig2, (ax0, ax1) = plt.subplots(figsize=(9, 6), nrows=2)
        ax0.plot(list(obs_a.keys()), list(obs_a.values()), label='Observation',
                    marker='o', color='#F67A0D', linestyle='-')
        ax0.plot(list(mdl_a.keys()), list(mdl_a.values()), label='Modeled', 
                    marker='o', color='#3C88BD', linestyle='--')
        ax0.set_title('Amplitude',fontsize=10)
        # ax0.legend()

        # ax1.plot(list(obs_g.keys()), list(obs_g.values()), label='Observation',
        #             marker='o', color='#F67A0D', linestyle='-')
        # ax1.plot(list(mdl_g.keys()), list(mdl_g.values()), label='Modeled', 
        #             marker='o', color='#3C88BD', linestyle='--')
        ax1.plot(list(obs_g.keys()), list(obs_g.values()),
                    marker='o', color='#F67A0D', linestyle='-')
        ax1.plot(list(mdl_g.keys()), list(mdl_g.values()), 
                    marker='o', color='#3C88BD', linestyle='--')
        ax1.set_title('Phase',fontsize=10)
        fig2.suptitle(f'{wl_station["Name"]}, amplitude and phase of tidal consituents', fontsize=14)
        fig2.legend(ncol=3, loc="outside upper right")
        if fname2!='':
            plt.savefig(dir_save_fig+fname2)

        # reconstruct major tidal consituents
        for consti in major_tidal_conts:
            if consti in common_consts:
                print(consti)
                major_consts_obs[consti] = utide.reconstruct(obs_data[time_stamp], obs_coefs, constit=consti).h
                major_consts_mdl[consti] = utide.reconstruct(mdl_data[time_stamp], mdl_coefs, constit=consti).h

    return major_consts_obs, major_consts_mdl

def separate_tide_nontide(water_data, lat):
    '''
    Separate tide from non-tide water level using U-tide toolbox
    Parameters:
        -water_data: pd.DataFrame, 2 columns: [Timestamp, total_water]
        -lat: coordiate degree, latitude of checking station

    Returns:
        -water_data: pd.DataFrame, orignal water_data with 2 added columns of prediction, residual
            
    '''
    # separate tide from non-tide
    # water_data = water_data.dropna()
    # water_data.iloc[:,0] = pd.DatetimeIndex(water_data.iloc[:,0]) + timedelta(hours=-9)
    water_data['anomaly'] = water_data.iloc[:,1] - water_data.iloc[:,1].mean()
    # water_data['anomaly'] = water_data['anomaly'].interpolate()
    

    # coef = utide.solve(
    #     water_data.iloc[:,0].values,
    #     water_data['anomaly'],
    #     lat=lat,
    #     method="ols",
    #     conf_int="MC",
    #     verbose=False,
    # )

    # gemini suggested for short time
    coef = utide.solve(
        water_data.iloc[:,0].values,
        water_data['anomaly'],
        lat=lat,
        method="ols",
        # conf_int="auto",
        constit='auto',
        verbose=False,
    )

    # # gemini suggested for short time
    # coef = utide.solve(
    #     water_data.iloc[:,0].values,
    #     water_data['anomaly'],
    #     lat=lat,
    #     method="ols",
    #     # conf_int="auto",
    #     constit=khoa_tidal_consts,
    #     verbose=False,
    # )


    tide = utide.reconstruct(water_data.iloc[:,0].values, coef, verbose=False)
    water_data['pred'] = tide.h 
    water_data['res'] = water_data['anomaly'] - tide.h

    return water_data, coef

#TODO
def remove_water_trend(water_data):
    ''' Check for the trend and raise of water data 
    Ref: Figure 3.4 from document of Extreme value analysis from JMA technical report
    Parameters:
        -water_data: pd.DataFrame, 2 columns of 1st: Timestamp, 2nd: observed water level

    Returns:
        -Plot water level with mean, trend, and before and after trend removal
    '''

    # detrend of data
    water_data = all_year_data.iloc[:,0:2].interpolate(method='linear')
    water_data = water_data[water_data['Time']>= '2006-01-01']
    # estimate trend from hourly data
    water_data = water_data.interpolate(method='linear')
    x_temp = np.arange(0,len(water_data),1)
    hourly_line = sstats.linregress(x_temp, water_data.iloc[:,1])
    fig, (ax0,ax1,ax2) = plt.subplots()
    ax0.scatter(x_temp, water_data.iloc[:,1], s=2, label='Data') # Original data points
    ax0.plot(x_temp, hourly_line.slope * x_temp + hourly_line.intercept, color='red', label='Fitted line') # Regression line
    ax0.legend()
    ax0.title('Linear trend estimated from hourly data')


    # estimate trend from daily mean data
    daily_data = water_data.groupby(pd.Grouper(key='Time', freq='1d')).mean().reset_index()
    daily_data = daily_data.dropna()
    x_temp = np.arange(0,len(daily_data),1)
    daily_line = sstats.linregress(x_temp, daily_data.iloc[:,1])

    ax1.scatter(daily_data.iloc[:,0], daily_data.iloc[:,1], s=2, label='Data') # Original data points
    ax1.plot(daily_data.iloc[:,0], daily_line.slope * x_temp + daily_line.intercept, color='red', label='Fitted line') # Regression line
    ax1.legend()
    ax1.title('Linear trend estimated from daily data')
    

    # estimate trend from yearly mean data
    yearly_data = water_data.groupby(pd.Grouper(key='Time', freq='YE')).mean().reset_index()
    x_temp = np.arange(0,len(yearly_data),1)
    regress_line = sstats.linregress(x_temp, yearly_data.iloc[:,1])
    ax2.plot(yearly_data.iloc[:,0], yearly_data.iloc[:,1], marker='o', ms=3, label='Data') # Original data points
    ax2.plot(yearly_data.iloc[:,0], regress_line.slope * x_temp + regress_line.intercept, color='red', label='Fitted line') # Regression line
    ax2.legend()
    ax2.ylabel('Water level [m]')
    ax2.title('Linear trend estimated from yearly mean data')
    plt.show()


# Temporary May 13, 2026
def do_water_QC(data):
    '''
    Assign peaks (change in 1 minute interval larger than 5 cm)
    Return:
        -wind_data: pd.DataFrame, wind data with quality controlled
    '''
    time_stamp = data.columns[0]
    data = data.set_index(time_stamp)

    changes = data.diff()
    data_interval = data.index.to_series().diff().dropna().unique() 
    if len(data_interval)>1: print('There more than 1 intervals of recording data')
    if data_interval[0]==1:  data[changes.abs() > 5] = pd.NA
    data = data.reset_index()

    return data

# %%
