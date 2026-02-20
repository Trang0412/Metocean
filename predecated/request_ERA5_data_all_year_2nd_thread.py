
## This file only for downloading win data##
# Date: June 19, 2026
# TrangLe
# Change values of "year" for other years as current limit on data request are 2 years of data

# Data are available from 1940-2026

#%%
import cdsapi
import numpy as np
import time
import logging 
import os

# Define the number of hours to wait
HOURS_TO_WAIT = 10

# Calculate the equivalent time in seconds (1 hour = 3600 seconds)
seconds_to_wait = HOURS_TO_WAIT * 60 * 60

print(f"Starting wait of {HOURS_TO_WAIT} hours...")

# The program will pause here for the specified duration
time.sleep(seconds_to_wait)

print("Wait finished. Running the delayed code now.")
path_save = 'D:\\InProbation\\Metocean_Jeju\\Data\\ERA5\\wind_100m_v\\'

# request for 50 years of data, from 1976 to 2025
years_in_request = np.arange(1976,2026,1)

# CDS client and dataset
request = {
    "product_type": ["reanalysis"],
    "variable": [
        # "100m_u_component_of_wind",
        "100m_v_component_of_wind",
        # "mean_sea_level_pressure",
    ],
    "month": [
        "01", "02", "03",
        "04", "05", "06",
        "07", "08", "09",
        "10", "11", "12"
    ],
    "day": [
        "01", "02", "03",
        "04", "05", "06",
        "07", "08", "09",
        "10", "11", "12",
        "13", "14", "15",
        "16", "17", "18",
        "19", "20", "21",
        "22", "23", "24",
        "25", "26", "27",
        "28", "29", "30",
        "31"
    ],
    "time": [
        "00:00", "01:00", "02:00",
        "03:00", "04:00", "05:00",
        "06:00", "07:00", "08:00",
        "09:00", "10:00", "11:00",
        "12:00", "13:00", "14:00",
        "15:00", "16:00", "17:00",
        "18:00", "19:00", "20:00",
        "21:00", "22:00", "23:00"
    ],
    "data_format": "netcdf",
    "download_format": "unarchived",
    "area": [33.25, 126.25, 33.75, 127.25]
}

dataset = "reanalysis-era5-single-levels"

#%%
os.chdir(path_save)

client = cdsapi.Client() 
for year in years_in_request:

    request['year'] = str(year)

    # have to change according to variables are being dowloaded
    target_file  = f'era5_{year}_v100.nc'

    year_data = client.retrieve(dataset, request)
    year_data.download(target_file)


