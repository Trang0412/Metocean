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
def do_extreme_wind_analysis():
    '''Composite procedure for conducting extreme wind analysis
    '''
    pass
#TODO
def combine_typhoon_wind_data():
    '''
    Combine typhoon wind data with non-typhoon for extreme combined (typhoon-nontyphoon) extreme wind analysis 
    '''
    pass

#TODO
def remove_typhoon_wind_data():
    '''
    Remove wind data during typhoon affected period for non-typhoon extreme wind analysis 
    '''
    pass

#TODO: analyse jma msm data
def sel_typhoon_affected(ref_point, search_cri, dir_btd, dir_wink, fname_save=''):
    '''
    Select which typhoons to be included for analysis points during analysis period
    Use JMA typhoon best track data (BTD) and follow DHI section 2.4 for criteria of choosing typhoons

    Date: April 28, 2026

    Parameters:
        -ref_point: list, list of float number of latitude and longitude, e.g, [34.3, 127,9]
        -search_cri: pd.DataFrame, search criteria, loaded from metocean_metadata 
        -dir_btd: str, directory to Best Track Data
        -dir_wink: str, directory to Wink typhoon wind field data

    Returns:
        -typhoons_sel: pd.DataFrame, 2 columns of [Year, Name] for a list of typhoons selected  
    '''
    
    # read all typhoon information from best track data and wink
    btd_typhoons = read_jma_btd(dir_btd)
    wink_mdata = read_typhoon_wink_metadata(dir_wink)
    
    # compute distance between reference point to all the point in wink grid
    d_wink = np.zeros((len(wink_lat_points), len(wink_lon_points)))
    for i in range(len(wink_lat_points)):
        for j in range( len(wink_lon_points)):
            point = (wink_grid_lat[i, j], wink_grid_lon[i, j])
            d_wink[i,j] = geodesic(list(ref_point.values()), point).km  # distance in km
    
    cols = ['Name', 'Start time', 'End time']
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

            # get maximum wind speed during passing time, 'hours' set to 1 as interval in WINK is 60 minutes
            start_time_idx = max(int((passing_time[0] - tp_mdata['Start time'])/pd.Timedelta(hours=1)), 0)
            end_time_idx = min(int((passing_time[-1] - tp_mdata['Start time'])/pd.Timedelta(hours=1)), wind_tp_wink['ws'].shape[0])

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


    # TODO: choosing typhoon from jma_msm database
    jma_msm_typhoons = read_typhoon_jma_msm()

    # later dump to excel file
    return typhoons_selected


def plot_typhoon_track_with_radii(tp_track, ref_point, radii, fig_title):
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
    radii_alpha = [0.05, 0.08, 0.1]
    for i in range(len(radii)):
        circ = mpatches.Circle((ref_point['lon'], ref_point['lat']), radii[i], 
                            edgecolor='red', fc='m', alpha=radii_alpha[i],)
        ax.add_patch(circ)
    ax.grid(color='gray')
    ax.legend()
    ax.set_title(fig_title)
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

#TODO
def read_typhoon_jma_msm(dir_tp):
    ''' Read information about typhoon wind data from JMA-MSM
    Wind u,v-component at 10m height as monthly manner


    Parameters:
        -dir_tp: str, directory to typhoon's wind u,v-component from 2001 to 2025
    Returns:
    '''
    year = 2021
    month = 1
    fname = 'jra3q.anl_surf.0_2_3.vgrd10m-hgt-an-gauss.2026040100_2026043018.nc'
    u_temp = xr.load_dataset(dir_tp + fname)
    return None

def read_typhoon_wink_metadata(dir_tp):
    ''' Read metadata from WINK typhoon data
    Parameters:
        -dir_tp: str, directory to typhoon wind data from WINK
    Returns:
        -typhoons: pd.DataFrame, with 4 columns of [Name, Start time, End time, Time inteval(min)]
    '''
    mdata_typhoon =  pd.read_csv(dir_tp+'HYB_TC_INPUTS.dat', sep='./', header=None)
    typhoons = mdata_typhoon.iloc[:,1].dropna()
    typhoons = typhoons.apply(lambda x: x.split('_BATCH')[0])
    typhoons = typhoons.to_frame(name='Name')
    typhoons['Start time'] = None
    typhoons['End time'] = None
    typhoons['Time iterval (min)'] = None

    for i in typhoons.index:
        time_info = mdata_typhoon.iloc[i+2,0].split(' ')
        start_d = f'{time_info[1][:4]}-{time_info[1][4:6]}-{time_info[1][6:8]}'
        start_h = f'{time_info[1][9:11]}:{time_info[1][11:13]}:{time_info[1][13:15]}'
        typhoons.at[i, 'Start time'] = pd.to_datetime(f'{start_d} {start_h}')
        end_d = f'{time_info[-1][:4]}-{time_info[-1][4:6]}-{time_info[-1][6:8]}'
        end_h = f'{time_info[-1][9:11]}:{time_info[-1][11:13]}:{time_info[-1][13:15]}'
        typhoons.at[i, 'End time'] = pd.to_datetime(f'{end_d} {end_h}')
        typhoons.at[i, 'Time iterval (min)'] = 60
    
    return typhoons.reset_index(drop=True)
    
def read_typhoon_wink(dir_tp, typhoon_name, plot_=False):
    '''
    Read information about typhoon wind data from WINK for whole grid provided by WINK
    Parameters:
        -dir_tp: str, folder storing WINK wind data field
        -typhoon_name: str, name of typhoon, in format of Code_Name, e.g., 5609_BABS

    Returns:
        -ws: np.ndarray, wind speed of typhoon wind, in shape of (time, lat, lon)
        -wd: np.ndarray, wind direction of typhoon wind, in shape of (time, lat, lon)

    '''
    metadata = read_typhoon_wink_metadata(dir_tp)
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

def read_typhoon_specific_loc(ws, wd, wind_grid, loc):
    '''
    Return wind speed, wind direction of typhoon for specific location with all occurrence time
    Paramters:
        -ws: np.ndarray, dim of (time, lat space, lon space), wind speed of typhoon
        -wd: np.ndarray, dim of (time, lat space, lon space), wind direction of typhoon
        -wind_grid: dict, contain points for lat and lon 
            'lat': np.array of latitiude in grid
            'lon': np.arrau of longitude in grid 
        -loc: list, [lat, lon] of location.
            
    Returns:
        -ws: np.array, dim of (time, 1), wind speed of typhoon for specific location
        -wd: np.array, dim of (time, 1), wind direction of typhoon for specific location
        
    '''
    lat_idx = np.where(wind_grid['lat'] == min(wind_grid['lat'], key=lambda x: abs(x-loc['lat'])))
    lon_idx = min(wind_grid['lon'], key=lambda x: abs(x-loc['lon']))

    return ws[:,lat_idx,lon_idx ], wd[:,lat_idx,lon_idx]

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
    wind_direction = 180 + (180/math.pi) * np.atan2(u, v)

    return wind_speed, wind_direction


# Jan 26, 2026
# Refer to DHI report for Wando-Gumil:
# measurements (60mMSL) were converted to 10mMSL using a power wind profile and a shear factor of 0.11.
# Check if data were measured at what heights. For exampple, 10m, 50m mMSL
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


def quality_control(wind_data, fixed_qc_criteria, data_interval, station, provider, checking_year, logger):
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