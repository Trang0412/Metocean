'''
-Prepare grid details (txt file) for spatial interpolation of ERA5 wind 10m to KMA stations 
-Interpolation will be done using CDO with remapbil command

@Author: Le Thi Trang
@Date: May 21, 2026
'''


#%%
import pandas as pd
import numpy as np
import xarray as xr
from pathlib import Path

#%%
dir_kma_extent = 'D:\\InProbation\\Metocean\\Data\\Observations\\KMA_extent\\'

dir_save = 'D:\\InProbation\\Metocean\\Data\\ERA5\\'
metadata_fname = 'Observation_Stations_Metadata_All.xlsx'
ks_metadata = pd.read_excel(f'{dir_kma_extent}{metadata_fname}', sheet_name='All')

with open(f'{dir_save}kma_extent_grid.txt', 'w') as wf:
    wf.write('gridtype = unstructured\n')
    list_lat = []
    list_lon = []
    list_station_ordered = []

    list_lat.extend([str(lat) for lat in ks_metadata['Latitude']])
    list_lon.extend([str(lon) for lon in ks_metadata['Longitude']])
    list_station_ordered.extend([f'{name}_{code}' for name,code in zip(ks_metadata["KR Name"], ks_metadata["Station ID"])])

    wf.write(f'gridsize = {len(list_lat)}\n')
    wf.write(f'xsize = {len(list_lat)}\n')
    wf.write(f'ysize = 1\n')
    wf.write(f'xvals = {" ".join(list_lon)}\n')
    wf.write(f'yvals = {" ".join(list_lat)}\n')
    list_station_ordered = pd.DataFrame(data=list_station_ordered, columns=['Station'])
    list_station_ordered.to_csv(f'{dir_save}Order_in_kma_extent_interpolation.csv')

        


    




# %%
