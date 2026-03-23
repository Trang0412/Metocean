'''
Suite of function specific for wind data processing
- compute_ws_wd_from_u_v(): compute wind speed for u,v component
- wind_speed_to_10m_power_law(): convert wind speed measured at specific height to 10-m height
- quality_control(): apply quality control to wind data according to set of criteria
'''


import numpy as np
import math
import pandas as pd
from scipy.signal import welch

#TODO: what are variance of wind speed at height 10 m (sigma) and turbulence intensity(TI)
# as TI=sigma/U
# know TI will help use to define sigma

def Kaimal_spectrum(U10, var_U10, fs, z, z0, Lu_option='IEC'):
    """
    Compute power spectral density using Kaimal spectrum
    Parameters:

        -U10: pd.DataFrame, 10-minute mean wind speed at 10 m height, in units of m/s
        -var_U10: float or DataFrame?, variance of wind speed at height 10m
        -fs: float, sampling frequency (Hz)
        -z: float, height above the ground or above sea water level, in units of m
        -z0: terrain roughness, in units of m
    Returns:
    f, S : frequency and spectral density
    """
    # data = data - np.mean(data)  # detrend (important)
    # f, S = welch(data, fs=fs, nperseg=1024, scaling='density')
    if  Lu_option=='IEC':
        Lu = 3.33*z if z<60 else 200
    else:
        Lu = 300 * (np.power(z/300, 0.46+0.074*np.log(z0)))

    S = np.pow(var_U10, 2) * (6.868*Lu/U10) / (np.power(1+10.32*fs*Lu/U10,5/3))

    return S

def compute_ws_wd_from_u_v(u, v):
    '''
    Compute wind speed and wind direction from u,v-component from ERA5 data
    
    Parameters:
        -u: array data 
        -v: array data 
    '''
    wind_speed = np.sqrt(np.power(u, 2) + np.power(v, 2))
    wind_direction = 180 + (180/math.pi) * np.atan2(u, v)

    return wind_speed, wind_direction


#TODO: Jan 23, 2026
def compute_wind_parameters():
    '''
    Function for obtaining wind parameters.
    Refer to DNV-GL-2018 Metocean Characterization 
    Recommended practice for US offshore wind energy

    Wind parameters including:
        Wind speed statistics (min, mean, std, max) and distribution
        Wind directionality
        Wind profile, wind shear, turbulence
    '''
    pass


#TODO: convert surface wind from measurement data to 10-m height as in ERA5?
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

    # U(z)  = U(z_ref)*(z/z_ref)^a
    return np.multiply(U_z, np.power(z_ref/z, a))


def quaility_control(wind_data, fixed_qc_criteria, data_interval, station, provider, checking_year, logger):
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