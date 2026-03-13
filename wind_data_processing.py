import numpy as np
import math

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


def compute_wind_speed_spectrum():
    '''
    For spectral comparion of ERA5 and measured wind speed 
    Refer to Figure 2.11 from DHI report for Wando-Gumil, page 22
    '''
    pass

#TODO: convert surface wind from measurement data to 10-m height as in ERA5?
# Jan 26, 2026
# Refer to DHI report for Wando-Gumil:
# measurements (60mMSL) were converted to 10mMSL using a power wind profile and a shear factor of 0.11.
# Check if data were measured at what heights. For exampple, 10m, 50m mMSL
def convert_wind_speed_height_power(U_ref, z, z_ref, a_w):
    '''
    Convert wind averaging at certain vertical level(height, e.g., 100 m) to certain vertical level (e.g., 10 m)
    Using power law to convert wind speed at measured height (e.g., 60mMSL) to reference height (e.g., 10mMSL)
    Refer to formula 5-2, page 97, DNV-GL Metocean Characterization Recommended Practices for U.S. Offshore Wind Energy

    Parameter
        -U: numpy.array, of wind speed data at height measured
        -z: integer, height at that level wind profile was measured and/or computed
        -z_ref: integer, height at that level wind profile should be converted (i.e., reference height, usually 10 m)
        -a_w: float, shear exponent factor used for conversion

    Return
        -cwind_data: numpy.array, converted wind data to expected vertical level
    '''

    # z = 60
    # z_ref = 10


    return np.multiply(U_ref, np.power(z/z_ref, a_w))