'''
Suite of function specific for wind data processing
- compute_ws_wd_from_u_v(): compute wind speed for u,v component
- wind_speed_to_10m_power_law(): convert wind speed measured at specific height to 10-m height
- quality_control(): apply quality control to wind data according to set of criteria

@Author: Le Thi Trang
@Date: Jan 21, 2026

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
import glob

from data_loading import *




#TODO
def compare_wink_jra3q_vs_ERA5_typhoon_wind():
    pass

def convert_wind_gust_temporal(gust_data, cond='TC', gf_orig=1.22, gf_conv=1.06):
    '''Conversion wind speed between different duration averaged. 
    E.g., 1-min wind speed to 10-min wind speed
    values of gust factor is to refered to Table 1.1 of WMO/TD-No.1555 
    'Guidelines for converting between various wind averaging periods in tropical cyclone conditions'
    
    Parameters:
        -gust_data: np.ndarray, wind gusts at originate time. 
        -cond: float, condition of wind gust measurement, eg., 'TC': tropical cyclone
        -gf_orig: float, gust factor relating to wind gust measured
        -gf_conv: float, gust factor relating to wind gust to be converted

    Returns:
        -conv_gust: np.ndarray, wind gusts at conversion time
    '''
    return gust_data * (gf_conv/gf_orig)

#TODO
def combine_typhoon_wind_data():
    '''
    Combine typhoon wind data with non-typhoon for extreme combined (typhoon-nontyphoon) extreme wind analysis 
    '''
    pass


def extract_era5_non_typhoon_wind(typhoon_sel, era5_wind, time_col_name):
    '''
    Remove wind data during typhoon affected period from ERA5 wind data for non-typhoon extreme wind analysis 
    and return non-typhoon wind data for all 50 years of data from 1979-2025
    Parameters:
        -typhoon_sel: pd.DataFrame, information on [Name, Start time, End time] of typhoons selected, 
            where time here is affecting time to the study site
        -era5_wind: pd.DataFrame, ERA5 wind data for whole period of 1979-2025
        -time_col_name: str, column name of time stamp, varies between data type
    Returns:
        -era5_wind: pd.DataFrame, 3 columns of [Time, wind speed, wind direction] with data during typhoon period dropped

    '''
    
    for i in range(len(typhoon_sel)):
        era5_wind = era5_wind[~((era5_wind[time_col_name]>typhoon_sel['Start time'][i]) & (era5_wind[time_col_name]<typhoon_sel['End time'][i]))]
    
    return era5_wind


def sel_typhoon_affected(ref_point, search_cri, dir_btd, dir_wink, dir_jra3q, fname_save=''):
    '''
    Select which typhoons to be included for analysis points during analysis period
    Use JMA typhoon best track data (BTD) and follow DHI section 2.4 for criteria of choosing typhoons

    Date: April 28, 2026

    Parameters:
        -ref_point: list, list of float number of latitude and longitude, e.g, [34.3, 127,9]
        -search_cri: pd.DataFrame, search criteria, loaded from metocean_metadata 
        -dir_btd: str, directory to Best Track Data
        -dir_wink: str, directory to Wink typhoon wind field data
        -dir_jra3q: str, directory to JRA-3Q reanalysis data for reading wind during typhoon duration from 2001-2025

    Returns:
        -typhoons_sel: pd.DataFrame, 2 columns of [Year, Name] for a list of typhoons selected  
    '''
    
    # read all typhoon information from best track data and wink
    btd_typhoons = read_jma_btd(dir_btd)
    cols = ['Name', 'Start time', 'End time']
    typhoons_selected = pd.DataFrame(columns=cols)
    #%% TYPHOON OCCURRED IN 1979-2000 USING WIND FIELD DATA FROM WINK
    if dir_wink !='':
        # compute distance between reference point to all the point in wink grid
        d_wink = np.zeros((len(wink_lat_points), len(wink_lon_points)))
        for i in range(len(wink_lat_points)):
            for j in range( len(wink_lon_points)):
                point = (wink_grid_lat[i,j], wink_grid_lon[i,j])
                d_wink[i,j] = geodesic(list(ref_point.values()), point).km  # distance in km

        wink_mdata = read_typhoon_wink_metadata(dir_wink)

        typhoons_selected = pd.DataFrame(columns=cols)
        for i in range(len(wink_mdata)):
            tp_name = wink_mdata.loc[i]['Name']
            if tp_name not in btd_typhoons['Name'].values: continue
        
            tp_track = btd_typhoons[btd_typhoons['Name']==tp_name][['DateTime', 'center_lat', 'center_lon']]   
            wind_tp_wink = read_typhoon_wink(dir_wink, f'{tp_name}_WIND.dat') # dictionary of ws, and wd in shape of (time, lat_points, lon_points)
            tp_mdata = wink_mdata.loc[i]

            # check track of typhoon whether it satisfied to be considered passing the study site 
            tp_track['Distance_km'] = np.array([geodesic(list(ref_point.values()), (p_lat, p_lon)).km for (p_lat, p_lon) in zip(tp_track['center_lat'], tp_track['center_lon'])])
            
            for ci in range(len(search_cri)):
                if len(np.argwhere(tp_track['Distance_km']<search_cri['radius_km'][ci])) == 0: continue
                passing_time = tp_track[tp_track['Distance_km']<search_cri['radius_km'][ci]]['DateTime'].to_list()
                if len(passing_time) == 0: continue

                # get maximum wind speed during passing time, 'hours' set to 1 as interval in WINK is 60 minutes
                start_time_idx = max(int((passing_time[0] - tp_mdata['Start time'])/pd.Timedelta(hours=wink_dt)), 0)
                end_time_idx = min(int((passing_time[-1] - tp_mdata['Start time'])/pd.Timedelta(hours=wink_dt)), wind_tp_wink['ws'].shape[0])

                # extract wind speed of points in checking areas                  
                radius_mask = (d_wink - search_cri['radius_km'][ci]) < 0
                ws_masked = wind_tp_wink['ws'][start_time_idx:end_time_idx+1,:,:] * radius_mask
                if ws_masked.max() > search_cri['min_ws'][ci]: 
                    start_time = tp_mdata['Start time'] + pd.Timedelta(hours=start_time_idx)
                    end_time = tp_mdata['Start time'] + pd.Timedelta(hours=end_time_idx)
                    typhoons_selected.loc[len(typhoons_selected)] = [tp_name, pd.to_datetime(start_time), pd.to_datetime(end_time)]
                break

        if fname_save != '':
            typhoons_selected.to_excel(fname_save, 'WINK')


    #%% TYPHOON OCCURRED IN 2001 ONWARD USING JRA_3Q WIND FIELD
    if dir_jra3q !='':
        wink_areas = dict()
        wink_areas['lat'] = wink_lat_range
        wink_areas['lon'] = wink_lon_range
        
        # compute distance between reference point to all the point in jra3q grid
        # reading example from 1-month data of any year to get information on grid and temporal
        temp_jra = xr.open_dataset(dir_jra3q + 'jra3q.anl_surf.0_2_3.vgrd10m-hgt-an-gauss.2025030100_2025033118.nc')
        lat_subset_jra = temp_jra.lat.sel(lat=slice(wink_areas['lat'][1], wink_areas['lat'][0])).values[::-1]
        lon_subset_jra = temp_jra.lon.sel(lon=slice(wink_areas['lon'][0], wink_areas['lon'][1])).values
        jra_grid_lat, jra_grid_lon = np.meshgrid(lat_subset_jra, lon_subset_jra, indexing='ij')

        d_jra = np.zeros((len(lat_subset_jra), len(lon_subset_jra)))
        for i in range(len(lat_subset_jra)):
            for j in range( len(lon_subset_jra)):
                point = (jra_grid_lat[i,j], jra_grid_lon[i,j])
                d_jra[i,j] = geodesic(list(ref_point.values()), point).km  # distance in km

        cols = ['Name', 'Start time', 'End time']
        typhoons_selected = pd.DataFrame(columns=cols)

        btd_typhoons = btd_typhoons[btd_typhoons['DateTime'] >= pd.to_datetime('2001-01-01')]
        list_tps = btd_typhoons['Name'].unique()

        for i in range(len(list_tps)):
            tp_name = list_tps[i]
            tp_track = btd_typhoons[btd_typhoons['Name']==tp_name][['DateTime', 'center_lat', 'center_lon']]   
            wind_tp_jma = read_typhoon_jra3q(dir_jra3q, tp_name, btd_typhoons, wink_areas)
            start_time = btd_typhoons[btd_typhoons['Name'] == tp_name]['DateTime'].iloc[0]
            end_time = btd_typhoons[btd_typhoons['Name'] == tp_name]['DateTime'].iloc[-1]

            # check track of typhoon whether it satisfied to be considered passing the study site 
            tp_track['Distance_km'] = np.array([geodesic(list(ref_point.values()), (p_lat, p_lon)).km for (p_lat, p_lon) in zip(tp_track['center_lat'], tp_track['center_lon'])])
            
            for ci in range(len(search_cri)):
                if len(np.argwhere(tp_track['Distance_km']<search_cri['radius_km'][ci])) == 0: continue
                passing_time = tp_track[tp_track['Distance_km']<search_cri['radius_km'][ci]]['DateTime'].to_list()
                if len(passing_time) == 0: continue

                # get maximum wind speed during passing time, 'hours' set to interval of database
                start_time_idx = max(int((passing_time[0] - start_time)/pd.Timedelta(hours=jra3q_dt)), 0)
                end_time_idx = min(int((passing_time[-1] - start_time)/pd.Timedelta(hours=jra3q_dt)), wind_tp_jma['ws'].shape[0])

                # extract wind speed of points in checking areas                  
                radius_mask = (d_jra - search_cri['radius_km'][ci]) < 0
                ws_masked = wind_tp_jma['ws'][start_time_idx:end_time_idx+1,:,:] * radius_mask
                start_time_ = btd_typhoons[btd_typhoons['Name'] == tp_name]['DateTime'].iloc[0]
                if ws_masked.max() > search_cri['min_ws'][ci]: 
                    start_time_ = start_time + pd.Timedelta(hours=start_time_idx)
                    end_time_ = start_time + pd.Timedelta(hours=end_time_idx)
                    typhoons_selected.loc[len(typhoons_selected)] = [tp_name, pd.to_datetime(start_time_), pd.to_datetime(end_time_)]
                break
        
        if fname_save != '':
            typhoons_selected.to_excel(fname_save, 'JMA')


    # later dump to excel file
    return typhoons_selected


def read_typhoon_jra3q(dir_tp, typhoon_name, btd_typhoons, inter_areas):
    ''' Read u,v-componentat duration of specific typhoon 
    Wind u,v-component at 10m height as monthly manner
    Return wind speed and wind direction for specific typhoon

    Parameters:
        -dir_tp: str, directory to typhoon's wind u,v-component from 2001 to 2025
        -typhoon_name: str, name of current typhoon with format in WINK, e.g., 2527_KOTO
        -btd_typhoons: pd.DataFrame, dataframe of typhoons' information, from read_jma_btd()
        -inter_areas: dictionary, range of lat, lon to small grid matching with WINK,read from metocean_metadata
    Returns:
        -current_typhoon: dictionary of wind speed and wind direction
            ws: np.ndarray, wind speed of typhoon wind, in shape of (time, lat, lon)
            wd: np.ndarray, wind direction of typhoon wind, in shape of (time, lat, lon)

    '''  
    # define year and month of currence of current typhoon from its name and time
    year_prefix = int(typhoon_name[0:2])
    if year_prefix > 51: year = int(f'19{year_prefix}')
    elif year_prefix < 10: year = int(f'200{year_prefix}')
    else: year = int(f'20{year_prefix}')
    months = np.unique(btd_typhoons[btd_typhoons['Name'] == typhoon_name]['DateTime'].dt.month)
    start_time = btd_typhoons[btd_typhoons['Name'] == typhoon_name]['DateTime'].iloc[0]
    end_time = btd_typhoons[btd_typhoons['Name'] == typhoon_name]['DateTime'].iloc[-1]

    ws = []
    wd = []

    # load u,v-component of wind during 
    for month in months:
        if month<10:
            u_search_str = f'ugrd10m-hgt-an-gauss.{year}0{month}'
            v_search_str = f'vgrd10m-hgt-an-gauss.{year}0{month}'
        else:
            u_search_str = f'ugrd10m-hgt-an-gauss.{year}{month}'
            v_search_str = f'vgrd10m-hgt-an-gauss.{year}{month}'      
        u_file = glob.glob(dir_tp + f'*{u_search_str}*', recursive=False)
        v_file = glob.glob(dir_tp + f'*{v_search_str}*', recursive=False)

        u_temp = xr.load_dataset(u_file[0])
        v_temp = xr.load_dataset(v_file[0])
        
        u_temp = u_temp.sel(time=slice(start_time, end_time),
                            lat=slice(inter_areas['lat'][1],inter_areas['lat'][0]), 
                            lon=slice(inter_areas['lon'][0],inter_areas['lon'][1]))
        
        v_temp = v_temp.sel(time=slice(start_time, end_time),
                            lat=slice(inter_areas['lat'][1],inter_areas['lat'][0]), 
                            lon=slice(inter_areas['lon'][0],inter_areas['lon'][1]))

        ws_temp, wd_temp = compute_ws_wd_from_u_v(u_temp['ugrd10m-hgt-an-gauss'].values, 
                                        v_temp['vgrd10m-hgt-an-gauss'].values)
        ws.append(ws_temp)
        wd.append(wd_temp)
        
    current_typhoon = dict({'ws':np.concatenate(ws, axis=0), 'wd':np.concatenate(wd, axis=0)})

    return current_typhoon


def read_typhoon_wink(dir_tp, typhoon_name, plot_=False):
    '''
    Read information about specific typhoon wind data from WINK for whole grid provided by WINK
    Parameters:
        -dir_tp: str, folder storing WINK wind data field
        -typhoon_name: str, name of typhoon, in format of Code_Name, e.g., 5609_BABS

    Returns:
        -current_typhoon: dictionary of wind speed and wind direction
            ws: np.ndarray, wind speed of typhoon wind, in shape of (time, lat, lon)
            wd: np.ndarray, wind direction of typhoon wind, in shape of (time, lat, lon)

    '''
    # metadata = read_typhoon_wink_metadata(dir_tp)
    data = np.loadtxt(dir_tp+typhoon_name)
    wind_grid = np.reshape(data, (-1,2, 901, 901))
    
    # compute wind speed, wind direction
    u_comp = wind_grid[:,0,:,:]
    v_comp = wind_grid[:,1,:,:]
    ws, wd = compute_ws_wd_from_u_v(u_comp, v_comp)

    current_typhoon = dict({'ws':ws, 'wd':wd})
    if plot_:
        lon_start, lat_start = 117.0, 20.0
        res = 0.03333333
        size = 901
        plot_typhoon_windfield(u_comp[0,:,:], v_comp[0,:,:], lon_start, lat_start, res, size, typhoon_name + 'first hours tracked')

    return current_typhoon

def plot_typhoon_track_with_radii(tp_track, ref_point, radii_cri, fig_title, dir_save, 
                                  tp_wind=None, wind_grid=None):
    ''' Plot roughly track of typhoon along with different areas accoridng to radii of 2.5, 3, 5 degree from the reference point
    Areas within radius is plot with Circle patch, which is not correctly in geographic distance, only use for rough visualization purpose
    Parameters:
        -tp_track: pd.DataFrame, track of current typhoon [Datetime, center_lat, center_lon], loaded from read_jma_btd()
        -ref_point: dictionary, lat and lon of reference point, loaded from metocean_metadata
        -radii: list, different radii (in degree unit) from reference point to check if typhon track pass the area or not
        -fig_title: str, figure title, usually to be typhoon name
    Returns:
        - only show figure
    '''
    
    temp_dist = [geodesic(list(ref_point.values()), [tp['center_lat'], tp['center_lon']]).km  for _, tp in tp_track.iterrows()]
    if wind_grid=='jra_3q':
        wind_grid_lat = jra_grid_lat
        wind_grid_lon = jra_grid_lon
    elif wind_grid=='wink':
        wind_grid_lat = wink_grid_lat
        wind_grid_lon = wink_grid_lon
         
    # Plotting with Cartopy
    fig = plt.figure(figsize=(12, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Add Geography for the Korean Peninsula context
    ax.set_extent([wink_lon_points[0], wink_lon_points[-1], wink_lat_points[0], wink_lat_points[-1]], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=1)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
    ax.plot(tp_track['center_lon'].values, tp_track['center_lat'].values,
            marker='o', markerfacecolor='none', markersize=3, linewidth=1, label='Typhon track')
    ax.scatter(ref_point['lon'], ref_point['lat'], marker='o', color='red', s=3, label='Reference point')

    # add wind speed and date time, 0 and 12UTC, information if typhoon track come near study site at either determined radii
    radii_alpha = [0.05, 0.08, 0.1]
    radii_deg = list(radii_cri['radius_deg'].values)
    radii_km = list(radii_cri['radius_km'].values)

    for i in range(len(temp_dist)):
        if temp_dist[i] > max(radii_km):continue
        if tp_track['DateTime'].iloc[i].hour in [0, 12]:
            month_str = tp_track['DateTime'].iloc[i].date().strftime('%B')[0:3]
            day_str = tp_track['DateTime'].iloc[i].date().day
            ax.annotate(f'{day_str} {month_str} ( {tp_track["DateTime"].iloc[i].hour}UTC)',
                        (tp_track['center_lon'].values[i], tp_track['center_lat'].values[i]))
            
        # plot wind field if there is data
        if tp_wind is not None:
            btd_typhoons = read_jma_btd(dir_btd)


    for i in range(len(radii_deg)):
        circ = mpatches.Circle((ref_point['lon'], ref_point['lat']), radii_deg[i], 
                            edgecolor='red', fc='m', alpha=radii_alpha[i],)
        ax.add_patch(circ)


    ax.grid(color='gray')
    ax.legend()
    ax.set_title(fig_title)
    if dir_save != '': plt.savefig(dir_save+fig_title)
    plt.show()


def read_jma_btd(dir_btd):
    '''
    Read typhoon best track data from JMA, return formated of typhoon track data 
    for all the available period

    Parameters:
        -dir_btd: str, directory of Best Track Data
    Returns:
        -typhoons: pd.DataFrame, mulitple columns, including [Year, Name] for a list of typhoons during input period  
    '''
    
    col_names = ['Year', 'Name', 'DateTime', 'center_lat', 'center_lon', 'pressure', 
                 'max_wind_speed', 'lgest_radius_50kt', 'shtest_radius_50kt',
                 'lgest_radius_30kt', 'shtest_radius_30kt']
    typhoons = []
    current_storm = {}

    with open(dir_btd+'bst_all.txt') as file:
        for line in file:
            if line.startswith('66666'): # header lines
                current_storm = {
                'Id': line[6:10],
                'Year': int('19' + line[6:8]) if int(line[6:8]) > 50 else int('20' + line[6:8]),
                'Name': line[31:51],
                }
            else: # data lines
                data = {
                    'Name': f"{current_storm['Id']}_{current_storm['Name'].strip()}",
                    'DateTime': pd.to_datetime(f'{current_storm["Year"]}-{int(line[2:4])}-{int(line[4:6])} {int(line[6:8])}:00:00'),
                    'center_lat': int(line[15:18])/10 if line[15:18].strip() else pd.NA,
                    'center_lon': int(line[18:24])/10 if line[18:24].strip() else pd.NA,
                    'pressure': float(line[24:28]) if line[24:28].strip() else pd.NA,
                    'max_wind_speed': float(line[33:36]) if line[33:36].strip() else pd.NA,
                    'lgest_radius_50kt': float(line[42:46]) if line[42:46].strip() else pd.NA,
                    'shtest_radius_50kt': float(line[47:51]) if line[47:51].strip() else pd.NA,
                    'lgest_radius_30kt': float(line[53:57]) if line[53:57].strip() else pd.NA,
                    'shtest_radius_30kt': float(line[58:62]) if line[58:62].strip() else pd.NA,
                }
                typhoons.append(data)
    return pd.DataFrame(typhoons)


def knot2ms(ws_knot):
    '''
    Convert knot to m/s for wind speed
    Parameters:
        -ws_knot: np.array, array of wind speed in knot
    Returns:
        -ws_ms: np.array, array of wind speed in m/s
    '''
    return ws_knot/2


def compute_u_v_from_ws_wd(ws, wd):
    ''' Convert observation data of wind speed and direction to u, v component 
        Parameters:
            -ws: np.ndarray, wind speed data
            -wd: np.ndarray, wind direction data, in degree
        Returns:
            -u_comp: np.ndarray, wind u component
            -v_comp: np.ndarray, wind v component
    '''
    u = -ws * np.sin(np.radians(ws)) 
    v = -ws * np.cos(np.radians(wd))  
    return u, v
    

def compute_ws_wd_from_u_v(u, v):
    '''
    Compute wind speed and wind direction from u,v-component from ERA5 data
    All the computation were element-wise operator
    
    Parameters:
        -u: np.ndarray data 
        -v: np.ndarray data 
    
    Return:
        -wind_speed: np.ndarray data
        -wind_direction: np.array data
    '''
    wind_speed = np.sqrt(np.power(u, 2) + np.power(v, 2))
    # wind_direction = 180 + (180/math.pi) * np.atan2(u, v)
    wind_direction = (180 + np.degrees(np.arctan2(u, v))) % 360

    return wind_speed, wind_direction


# Jan 26, 2026
# Refer to DHI report for Wando-Gumil:
# measurements (60mMSL) were converted to 10mMSL using a power wind profile and a shear factor of 0.11.
def wind_speed_to_10m_power_law(U_z, z, z_ref=10, a=0.11):
    '''
    Convert wind averaging at certain vertical level(height, e.g., 100 m) to certain vertical level (e.g., 10 m)
    Using power law to convert wind speed at measured height (e.g., 60mMSL) to reference height (e.g., 10mMSL)
    Refer to formula 5-2, page 97, DNV-GL Metocean Characterization Recommended Practices for U.S. Offshore Wind Energy

    Parameter
        -U: numpy.array, of wind speed data at height measured
        -z: integer, height at that level wind profile was measured and/or computed
        -z_ref: integer, height at that level wind profile should be converted (i.e., reference height, usually 10 m)
        -profile: string, wind profile in used, logarithmic or power law
        -a: float, shear exponent factor used for conversion. default 0.11

    Return
        -cwind_data: numpy.array, converted wind data to expected vertical level
    '''

    return np.multiply(U_z, np.power(z_ref/z, a))

#May 21, 2206. Logarithm law of wind conversion between heights
def wind_speed_to_10m_log(ws, z0, wind_height):
    '''
    '''
    wind_10m = ws * ((math.log(10 / z0))/(math.log(wind_height / z0)))
    return wind_10m

def wind_quality_control(wind_data, fixed_qc_criteria, data_interval, station, provider, checking_year, logger):
    '''
    QC procedure
    Skip period when there is no change in wind speed for 5 hours in consecutive 
    Example: Seongsanpo 2008 from 2008-02-01 to 2008-06-15, probably error in device
    Mar 16, 2026: Automate the process by checking the flat line/degree of changes between consecutive points then casting 
    those points with no changes between, say, for 20 consecutive points 
    (e.g., 20 minutes for 1-min interval data, 1 hour for 5  minute interval data and 5 hours for 1 hr interval)
    Set wind speed outside the range of [0, 60] is missing value
    

    Parameters: 
        - wind_data: pd.DataFrame, including 3 columns of time stamp, wind speed, wind direction
        - data_interval: integer, temporal interval of observation data, in minutes
        - logger: logger, for logging station and year
        - station: string, for logging station name
        - provider: string, for logging station provider
        - checking_year: integer, for logging data year in process

    
    Return:
        -wind_data: pd.DataFrame, wind data with quality controlled
    '''
    time_stamp = wind_data.columns[0]
    wind_data = wind_data.set_index(time_stamp)
    wind_data[wind_data['풍속(m/s)']<fixed_qc_criteria['ws'][0]] = pd.NA
    wind_data[wind_data['풍속(m/s)']>fixed_qc_criteria['ws'][1]] = pd.NA
    wind_data[wind_data['풍향(deg)']<fixed_qc_criteria['direction'][0]] = pd.NA
    wind_data[wind_data['풍향(deg)']>fixed_qc_criteria['direction'][1]] = pd.NA
    
    value_groups = (wind_data['풍속(m/s)'] != wind_data['풍속(m/s)'].shift()).cumsum()
    if data_interval == 1:
        stuck_periods = wind_data.groupby(value_groups).filter(lambda x: len(x) > 20).reset_index()
    if data_interval == 5:
        stuck_periods = wind_data.groupby(value_groups).filter(lambda x: len(x) > 12).reset_index()
    if data_interval == 60:
        stuck_periods = wind_data.groupby(value_groups).filter(lambda x: len(x) > 5).reset_index()

    if len(stuck_periods)>2:
        logger.info(f'QC (stuck periods) applied to: {station}_{provider}, {checking_year}')
    wind_data.loc[stuck_periods[time_stamp]] = pd.NA
    wind_data = wind_data.reset_index()

    return wind_data
# %%
