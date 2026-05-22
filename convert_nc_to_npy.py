'''
Convert netcdf file to npy file with shape of (time*lat*lon, u->v->msl)'''

#%%
import numpy as np
import xarray as xr
import pandas as pd
import os

#%%
dir_orig = 'D:\\InProbation\\Metocean\\Data\\ERA5\\pacific_0.25\\'
dir_save = 'D:\\InProbation\\Metocean\\Data\\ERA5\\model_grid\\'

model_grid = dict({'lat': [18, 53],
    'lon': [115, 147]})

years = np.arange(2018, 2022)

for year in years:
    dir_year = f'{dir_save}{year}\\'
    os.makedirs(dir_year, exist_ok=True)
    for month in range(1,13):
        if month < 10:
            fname = f'ERA5_{year}0{month}_reduced_pacific.nc'
        else:
            fname = f'ERA5_{year}{month}_reduced_pacific.nc'
        monthly_data = xr.open_dataset(dir_orig + f'{year}/{fname}')
        mdl_data = monthly_data.sel(
            latitude=slice(53, 18), 
            longitude=slice(115, 147))
        
        # loop through each day
        df_u = mdl_data.u10.to_dataframe(name='u10').reset_index()
        df_v = mdl_data.v10.to_dataframe(name='v10').reset_index()
        df_msl = mdl_data.msl.to_dataframe(name='msl').reset_index()

        start_date = f"{year}-{month:02d}-01"

        end_date = (
            pd.Timestamp(start_date)
            + pd.offsets.MonthEnd(0)
        )

        days = pd.date_range(
            start=start_date,
            end=end_date,
            freq="D"
        )

        # stack data into new shape of (time*lat*lon, u->v->msl)
        for day in days:
            date_str = day.strftime("%Y%m%d")
            try:
                u_day = mdl_data.u10.sel(time=slice(
                    f"{date_str} 00:00:00", f"{date_str} 23:00:00"
                ))
                v_day = mdl_data.v10.sel(time=slice(
                    f"{date_str} 00:00:00", f"{date_str} 23:00:00"
                ))

                msl_day = mdl_data.msl.sel(time=slice(
                    f"{date_str} 00:00:00", f"{date_str} 23:00:00"
                ))

                total_day = np.column_stack((
                    u_day.values.ravel(),
                    v_day.values.ravel(),
                    msl_day.values.ravel()
                    ))
            except:
                u_day = mdl_data.u10.sel(valid_time=slice(
                    f"{date_str} 00:00:00", f"{date_str} 23:00:00"
                ))
                v_day = mdl_data.v10.sel(valid_time=slice(
                    f"{date_str} 00:00:00", f"{date_str} 23:00:00"
                ))

                msl_day = mdl_data.msl.sel(valid_time=slice(
                    f"{date_str} 00:00:00", f"{date_str} 23:00:00"
                ))

                total_day = np.column_stack((
                    u_day.values.ravel(),
                    v_day.values.ravel(),
                    msl_day.values.ravel()
                    ))
                
            np.save(f"{dir_year}era_{day.strftime('%Y%m%d')}_1h.npy", total_day)





# %%
