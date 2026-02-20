'''
Find nearest locations in grid to a speficic location based on lat/lon cooridnate

@Author: Le Thi Trang
@Date: Jan 21, 2026

'''

import math
import numpy as np
import matplotlib.pyplot as plt
import string
import matplotlib.font_manager as fm

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rc


def plot_grid_locations(ref_lats, ref_lons, inter_locs):
    '''
    Plot meshgrid of regions from which ERA5 data were retrieved.
    Manually choose the reference location by inspection
    
    Parameters:
        ref_lats: List, location's latitude extracted from ERA5 data
        ref_lats: List, location's longitude from ERA5 data
        inter_locs: DataFrame, chosen locations read from excel file. 

    Return: 
        None, only show the image for inspection with interest location is in red while reference locations are in gray.
        Show the legend for also?

    '''

    lons, lats = np.meshgrid(ref_lons, ref_lats)
    plt.plot(lons, lats , marker='o', color='gray', linestyle='none')
    plt.xticks(ref_lons)
    plt.yticks(ref_lats)
    n_inter_locs = len(inter_locs)

    for i in range(n_inter_locs):
        if 'PC' in inter_locs.iloc[i].Name:
            color_code = 'green'
            dot_marker = 's'
            xytext_loc = (-15,-15)
      
        if 'KHOA' in inter_locs.iloc[i].Provider:
            color_code = 'yellow'
            dot_marker = 'o'
            xytext_loc = (-35,-10)

        if 'KMA' in inter_locs.iloc[i].Provider:
            color_code = 'red'
            dot_marker = 'P'
            xytext_loc = (5,5)
        

        plt.plot(inter_locs.iloc[i].Longitude, inter_locs.iloc[i].Latitude, 
                 marker=dot_marker, color=color_code, markeredgecolor='black', markersize=10)
        plt.annotate(inter_locs.iloc[i].Name, (inter_locs.iloc[i].Longitude, inter_locs.iloc[i].Latitude),
                             xytext=xytext_loc, textcoords="offset points", fontsize=10)

    plt.legend()

    plt.show()


