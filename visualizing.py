'''
Function definition for visualization

List of fuction supported (to-be-updated, last updated Mar 23, 2026)
    -plot_locs_on_geo_map()
    -plot_time_series_1var()
    -plot_time_series_2vars()
    -truncate_colormap()
    -scatter_plot_ERA5_against_meas()
    -spectra_comparison()

@Author: Le Thi Trang
@Date: Jan 23, 2026
'''

#%%
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io.shapereader import Reader

import windrose
import matplotlib.pyplot as plt
from windrose import WindroseAxes

import matplotlib.font_manager as fm
import matplotlib.dates as mdates
import seaborn as sns
import matplotlib.colors as mcolors
import matplotlib as mpl
from matplotlib import colormaps as cmaps
import matplotlib.patches as patches

import pandas as pd
import statsmodels.api as sm
from scipy import stats
from scipy.stats import binned_statistic_2d
import numpy as np
import xarray as xr

from common_processing import *

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rc
plt.rcParams['axes.unicode_minus'] = False

#%%

# Mar 24, 2026

def plot_nearest_point_era5_regrid_era5(bounding_area, vars_metadata, era5_coor, regrid_era5_coor, compare_statn):
    '''
    Show nearest points for wind comparison between ERA5 and regrided ERA5 to observation 
    Examine whether locs used for comparing wind speed in ERA5 and regrided ERA5 are too far causing 
        performance difference of underestimating observation in case of regrided ERA5

    
    Parameters:
        -bounding_lat_lon: dictionary, with keys of lat/lon for bounding area to llot
            e.g., {'lat': [33, 34], 'lon':[126, 127]}

        -vars_metadata: pd.DataFrame, loading from excel file for prerequite analysis
        -era5_coor: dictionary, full coordinate from downloaded ERA5 data, global variable from metocean_metadata
        -regrid_era5_coor: dictionary, full coordinate from regrided ERA5 data, global variable from metocean_metadata
        -comapre_statn: string, name of station to be checked, in form of {station_name}_{provider}

    Returns:
        None, only show figure
    '''

    
    stations = vars_metadata['Name'].dropna()
    providers = vars_metadata['Provider'].dropna()


    era5_geo_locs = xr.Dataset(coords=era5_coor)
    regrid_era5_geo_locs = xr.Dataset(coords=regrid_era5_coor)

    # values in order of longitude/latitude
    name_as_key = [f'{stations[i]}_{providers[i]}' for i in range(len(stations))]
    disp_locs = dict(zip(name_as_key, zip(vars_metadata['Longitude'][0:len(stations)], vars_metadata['Latitude'][0:len(stations)])))
    disp_locs.update({'PC1': (126.84852780, 33.54219444), 'PC2': (126.85891670, 33.55400000)})

    era5_nearest_point = era5_geo_locs.sel(lat=disp_locs[compare_statn][1], lon=disp_locs[compare_statn][0], method='nearest').coords
    era5_nearest_point = [round(float(era5_nearest_point['lon'].values),2),
                        round(float(era5_nearest_point['lat'].values),2)]

    reg_era5_nearest_point = regrid_era5_geo_locs.sel(lat=disp_locs[compare_statn][1], lon=disp_locs[compare_statn][0], method='nearest').coords
    reg_era5_nearest_point = [round(float(reg_era5_nearest_point['lon'].values),2),
                            round(float(reg_era5_nearest_point['lat'].values),2)]

    plot_points = dict({compare_statn: disp_locs.get(compare_statn), 
                        'Loc in Original ERA5': era5_nearest_point, 
                        'Loc in Regrided ERA5': reg_era5_nearest_point})
    plot_locs_on_geo_map(bounding_area, plot_points, turnon_loc_name=True)


def plot_locs_on_geo_map(bounding_area, plot_points, tick_res=0.25, minor_res=0.05, turnon_loc_name=False):
    '''
    Plot location of on contoured geographical map using geopandas/cartopy packages

    Parameters:
        -bounding_lat_lon: dictionary, with keys of lat/lon for bounding area to llot
            e.g., {'lat': [33, 34], 'lon':[126, 127]}

        -disp_locs: dictionary, with keys as name of station_provider, values of tuple of (lon, lat) coordinate

    Returns:
        -None, only show figure
    '''

    fig = plt.figure(figsize=(5, 5))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Set map extent 
    ax.set_extent([bounding_area['lon'][0], bounding_area['lon'][1],
                   bounding_area['lat'][0], bounding_area['lat'][1]], 
                   crs=ccrs.PlateCarree())
    coast = cfeature.GSHHSFeature(scale='full')
    ax.add_feature(coast)

    # Gridlines with labels
    x_ticks = np.arange(bounding_area['lon'][0]-tick_res, bounding_area['lon'][1]+tick_res, tick_res)
    y_ticks = np.arange(bounding_area['lat'][0]-tick_res, bounding_area['lat'][1]+tick_res, tick_res)   

    gl1 = ax.gridlines(draw_labels=True, xlocs = x_ticks, ylocs=y_ticks, 
                      xlim=[bounding_area['lon'][0]-tick_res, bounding_area['lon'][1]+tick_res], 
                      ylim=[bounding_area['lat'][0]-tick_res, bounding_area['lat'][1]+tick_res],
                      linewidth=0.2, linestyle='--', color='grey')
    
    gl1.top_labels = False
    gl1.right_labels = False

    # Axis labels formatting
    # gl1.xlabel_style = {'size': 9, 'fontfamily':'sans-serif', 'weight':'bold'}
    # gl1.ylabel_style = {'size': 9, 'fontfamily':'sans-serif', 'weight':'bold'}
    gl1.xlabel_style = {'size': 9, 'fontfamily':'sans-serif'}
    gl1.ylabel_style = {'size': 9, 'fontfamily':'sans-serif'}

    x_ticks_minor = np.arange(bounding_area['lon'][0], bounding_area['lon'][1], minor_res)
    y_ticks_minor = np.arange(bounding_area['lat'][0], bounding_area['lat'][1], minor_res)

    gl2 = ax.gridlines(draw_labels=False, xlocs = x_ticks_minor, ylocs=y_ticks_minor, 
                      linewidth=0.1, linestyle='--', color='grey')
    
    for loc_name in plot_points:

    
        if 'Original ERA5' in loc_name:
            dot_marker = 'o'
            xytext_loc = (-10,-15)
            circle = patches.Circle((plot_points[loc_name][0], plot_points[loc_name][1]), radius=0.07, color='green', fill=False)
            circle.set(label=loc_name)
            ax.add_patch(circle)
            continue

        if 'Regrided ERA5' in loc_name:
            dot_marker = 'o'
            xytext_loc = (-10,-30)
            circle = patches.Circle((plot_points[loc_name][0], plot_points[loc_name][1]), radius=0.05, color='blue', fill=False)
            circle.set(label=loc_name)
            ax.add_patch(circle)
            continue
    
        if 'PC' in loc_name:
            color_code = 'green'
            dot_marker = 's'
            xytext_loc = (-15,-15)
      
        if 'KHOA' in loc_name:
            color_code = 'yellow'
            dot_marker = 'o'
            xytext_loc = (-35,-10)

        if 'KMA' in loc_name:
            color_code = 'red'
            dot_marker = 'P'
            xytext_loc = (5,5)

        # print(loc_name)
        if turnon_loc_name:
            plt.annotate(loc_name.split('_')[0], (plot_points[loc_name][0], plot_points[loc_name][1]),
                                xytext=xytext_loc, textcoords="offset points", color=color_code, fontsize=9)
        plt.plot(plot_points[loc_name][0], plot_points[loc_name][1], 
                 marker=dot_marker, color=color_code, markeredgecolor='black', markersize=10)
        del dot_marker
    ax.legend()

    plt.show()


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


def plot_time_series_1var(data, x_label, y_label, fig_size=[6.4, 4.8], fig_title="", fname_save="", 
                          face_color ='#808080', txt_box_loc = [1.1, 1.1]):
    '''
    Time series scatter plot
    
    Parameters:
        data: list of pd.DataFrame, one for more data to plot
        x_variable: str, name of variables to plot in x_axis
        y_variable: str, name of variables to plot in y_axis

    Return:
        None, just showing plot
        Xticks are set to first day each month, by funtion DayLocator
    '''

    fig, ax = plt.subplots(1, figsize=fig_size)
    # ax.scatter(data[x_label], data[y_label], marker='.')
    ax.scatter(data[x_label], data[y_label], s=4, c=face_color)

    # fig.autofmt_xdate()
    ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=1))

    # -------------------------------------------------
    # STATISTICS BOX
    # -------------------------------------------------
    data_stats = data[y_label].describe()
    stats_text = (
        f"N = {data_stats['count']:.0f}\n"
        f"MEAN = {data_stats['mean']:.2f}\n"
        f"MAX = {data_stats['max']:.2f}\n"
        f"STD = {data_stats['std']:.2f}\n"
        f"NAN = {data[y_label].isnull().sum():.0f}"
    )

    ax.text(
        txt_box_loc[0], txt_box_loc[1], stats_text,
        transform=ax.transAxes,
        ha="right", va="top",
        fontsize=9,
        bbox=dict(boxstyle="round", fc="white", ec="black")
    )

    plt.ylabel(y_label)
    plt.xticks(rotation=45, ha='right')
    plt.title(fig_title) 
    plt.show()
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)
    if fname_save != "":
        fig.savefig(fname_save, dpi=300, bbox_inches="tight")


def plot_time_series_2vars(data, data1_label, data2_label, fig_size=[6.4, 4.8], fig_title="", fname_save="", 
                           fc1 ='#808080', fc2 ='#069AF3', txt_loc1 = [0.05, 0.95], txt_loc2= [0.05, 0.87]):
    '''
    Scatter plot of 2 time series data for visually comparisons.
    Refer to Figure 2.13 DHI report
    Assuming 2 data have common columns of time stamp and one other common data to compare, e.g., wind speed
    
    Parameters:
        data: pd.DataFrame, at least 3 columns data, 
            1st for x-axis, timestemp
            2nd: 1st data for y-axis
            3rd: 2nd data for y-axis
        data1_label: str, name of 1st variables to plot in x_axis
        data2_label: str, name of 2dn variables to plot in y_axis

    Return:
        None, just showing plot
        Xticks are set to first day each month, by funtion DayLocator
    '''

    df_columns = data.columns.tolist()

    # -------------------------------------------------
    # STATISTICS BOX
    # -------------------------------------------------
    data1_stats = data.iloc[:,1].describe()
    stats1_text = (
        f"{data1_label}: "
        f"N = {data1_stats['count']:.0f}, "
        f"MEAN = {data1_stats['mean']:.2f}, "
        f"MAX = {data1_stats['max']:.2f}, "
        f"STD = {data1_stats['std']:.2f}, "
        f"NAN = {data.iloc[:,1].isnull().sum():.0f}"
    )

    data2_stats = data.iloc[:,2].describe()
    stats2_text = (
        f"{data2_label}: "
        f"N = {data2_stats['count']:.0f}, "
        f"MEAN = {data2_stats['mean']:.2f}, "
        f"MAX = {data2_stats['max']:.2f}, "
        f"STD = {data2_stats['std']:.2f}, "
        f"NAN = {data.iloc[:,2].isnull().sum():.0f}"
    )

    # figure plot
    fig, ax = plt.subplots(1, figsize=fig_size)
    ax.scatter(data.iloc[:,0], data.iloc[:,1], s=4, c=fc1)
    ax.scatter(data.iloc[:,0], data.iloc[:,2], s=4, c=fc2)

    ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=1))

    ax.text(
        txt_loc1[0], txt_loc1[1], stats1_text,
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=9, c = fc1
        
    )
    ax.text(
        txt_loc2[0], txt_loc2[1], stats2_text,
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=9, c=fc2
        # bbox=dict(boxstyle=None, fc="white", ec=None)
    )

    plt.ylabel(df_columns[1].split('_')[0])
    plt.xticks(rotation=45, ha='right')
    plt.title(fig_title) 
    plt.show()
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)

    if fname_save != "":
        fig.savefig(fname_save, dpi=600, bbox_inches="tight")


# TODO: 
# Jan 22, 2026: - Check  the correctness of rose plot visualization
def rose_plot(wind_direction, wind_speed, fig_title="", 
                   sector_width=30, bins=[4,6,8,10,12,14,16,18,20], calm_limit=4,
                   label_pos=260, rticks_label=[5, 10, 15, 20], rmax_val = 20, 
                   ytick_labels=['5%', '10%', '15%', '20%'], bbox_anchor=(1, 0.1)):
    '''
    Rose plot for wind direction and wind_speed
    
    Parameters:
        wind_direction: 1-D array, array data of wind direction
        wind_speed: 1-D array, array data of wind speed
        fig_title: string, figure's title
    
    Return:
        None. Just showing plot

    '''

    # sector_width = 30 # plot for every 30 degree bin
    nsector = int(360/sector_width)

    # direction of wind is blow to or from?. Set blowto=True at current moment

    # bins = [4,6,8,10,12,14,16,18,20]
    fig = plt.figure(figsize=(3,3))

    ax = WindroseAxes.from_ax()


    ax.bar(wind_direction, wind_speed, nsector=nsector, blowto=False, 
           bins = bins, normed=True,
           opening=1.0, edgecolor = 'black', calm_limit=calm_limit)


    ax.set_legend()
    ax.set_rmax(rmax_val)
    ax.set_rticks(rticks_label)
    ax.set_yticklabels(ytick_labels)
    ax.set_rlabel_position(label_pos) 
    

    ax.legend(
        title="Wind speed (m/s)",
        loc="center left",
        bbox_to_anchor=bbox_anchor,
        frameon=True,
        fontsize=12
    )
    plt.title(fig_title)
    plt.show()

#TODO: Mar 10, 2026
# Make dual rose plot
def dual_rose_plot():
    pass


#TODO: make custom colormap later  
# Jan 27, 2026
def truncate_colormap(cmap_name, minval=0.0, maxval=1.0, n=100):
    """
    Truncates a given colormap to a specific range.

    Args:
        cmap_name (str): The name of the original colormap (e.g., 'viridis').
        minval (float): The lower bound of the original colormap range (0 to 1).
        maxval (float): The upper bound of the original colormap range (0 to 1).
        n (int): The number of colors in the new colormap.

    Returns:
        matplotlib.colors.ListedColormap: The new truncated colormap.
    """
    cmap = plt.get_cmap(cmap_name)
    # Generate an array of values spanning the desired subset
    new_colors = cmap(np.linspace(minval, maxval, n))
    # Create a new ListedColormap
    new_cmap = mcolors.ListedColormap(
        new_colors, name=f'truncated_{cmap_name}_({minval:.2f}, {maxval:.2f})'
    )
    return new_cmap


# Jan 26, 2026
def scatter_plot_ERA5_against_meas(data, fig_size, axis_lims, bin_width, fig_title, fname_save):
    '''
    Scatter plot of ERA5 against measurements for checking ERA5 validity as a 
    reliable source to force the hydrodynamic and wave models for FEED metocean study
    
    Refer to Figure 2.10 from DHI report for Wando-Gumil, page 22

    Paratemeter
        -data: pd.DataFrame, of 3 columns, where each column is a variable and each row is an observation
            Col 0: Timestamp, Col 1: measurement, Col 2: ERA5 data
        -axis_lims: array or list, of minimum and maximum limits for ticks in x-y axis
        -bin_width: float, bin of value for variables quantization for density plot
        -fig_title: str, title of figure

    Return

        -None, only show figure
        Later can return stats information
    '''

    # Mar 18, 2026: explicitly remove missing value
    data = data.dropna()

    qqfit_color = 'lightsteelblue'
    x = data.iloc[:,1].values
    y = data.iloc[:,2].values

    # axis_lims = [0, 32]

    xlims = axis_lims
    ylims = axis_lims


    nan_x_idxs = np.where(np.isnan(x))
    nan_x_idxs = nan_x_idxs[0]
    nan_y_idxs = np.where(np.isnan(y))
    nan_y_idxs = nan_y_idxs[0]

    total_idxs = np.concatenate((nan_x_idxs, nan_y_idxs))
    removed_idxs = np.unique(total_idxs)


    # Remove nan indexes
    x = np.delete(x, removed_idxs)
    y = np.delete(y, removed_idxs)

    xmin = x.min()
    xmax = x.max()

    ymin = y.min()
    ymax = y.max()
    # bin_width = 0.2 # separate bin with 0.2 m/s
    nbins = np.ceil(max(xmax,ymax) / bin_width)

    # -------------------------------------------------
    # 2D BINNING FOR POINT DENSITY
    # -------------------------------------------------
    stat, xedges, yedges, binnumber = binned_statistic_2d(
        x, y, None, statistic='count', bins=nbins, 
        range=[[xmin,xmax], [ymin,ymax]]
    )

    # assign each point its bin count
    ix = np.clip(np.digitize(x, xedges) - 1, 0, stat.shape[0] - 1)
    iy = np.clip(np.digitize(y, yedges) - 1, 0, stat.shape[1] - 1)
    density = stat[ix, iy]

    # -------------------------------------------------
    # STATISTICS
    # -------------------------------------------------
    N = len(x)
    bias = np.mean(y - x)
    ame = np.mean(np.abs(y - x))
    rmse = np.sqrt(np.mean((y - x) ** 2))
    cc = np.corrcoef(x, y)[0, 1]

    # quantile–quantile fit
    q = np.linspace(0, 1, 101)
    qx = np.quantile(x, q)
    qy = np.quantile(y, q)
    coef = np.polyfit(qx, qy, 1)

    # -------------------------------------------------
    # PLOT
    # -------------------------------------------------
    fig, ax = plt.subplots(figsize=fig_size)

    sc = ax.scatter(
        x, y,
        c=density,
        s=6,
        cmap='turbo',
        alpha=0.7,
        edgecolors="none",
        label="Data (linear ±60min)"
    )

    # 1:1 line
    ax.plot(
        axis_lims, axis_lims,
        color="orange", lw=2, label="1:1 Line (45°)"
    )

    # QQ fit line and plot
    xx = np.linspace(xmin, xmax, 200)
    ax.plot(
        xx, coef[0] * xx + coef[1],
        ls="--", lw=2, color=qqfit_color,
        label=f"QQ fit: y={coef[0]:.2f}x+{coef[1]:.2f}"
    )

    # Plot quantiles
    ax.scatter(qx, qy, s=20, marker='o', c='slategray')
    # -------------------------------------------------
    # AXES & GRID
    # -------------------------------------------------
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks(np.arange(xlims[0],xlims[1],2))
    ax.set_yticks(np.arange(ylims[0],ylims[1],2))

    ax.set_xlabel("WS [m/s] - Measurements")
    ax.set_ylabel("WS [m/s] - ERA5")

    ax.grid(True, ls=":", lw=0.8)

    # -------------------------------------------------
    # COLORBAR
    # -------------------------------------------------
    cbar = plt.colorbar(sc, ax=ax, fraction=0.046, pad=0.02)
    cbar.set_label("Number of data points in each 0.2 m/s bin")

    # -------------------------------------------------
    # STATISTICS BOX
    # -------------------------------------------------
    stats_text = (
        f"N = {N}\n"
        f"BIAS = {bias:.2f} m/s\n"
        f"AME = {ame:.2f} m/s\n"
        f"RMSE = {rmse:.2f} m/s\n"
        f"CC = {cc:.2f}"
    )

    ax.text(
        1.4, 1, stats_text,
        transform=ax.transAxes,
        ha="right", va="top",
        fontsize=9,
        bbox=dict(boxstyle="round", fc="white", ec="gray")
    )

    # -------------------------------------------------
    # LEGEND
    # -------------------------------------------------
    bbox_to_anchor = (1.6, 0)
    ax.legend(loc="lower right", bbox_to_anchor=bbox_to_anchor, frameon=True)

    plt.title(fig_title)
    plt.tight_layout()
    plt.show()

    if fname_save != '':
        fig.savefig(fname_save) 


#TODO: Refer to feasibility assessment stated in DNV-GL-2018, DHI report on Wando-Gumil (section 7.5)
# Part: Wave conditions (p.24)
# 
def plot_wave_height_against_peak_period():
    pass


def spectra_comparison(df, dt_modeled, fig_title):
    '''
    Compute empirical spectrl of wind speed using FFT
    Parameters:
        - df: pd.DataFrame, wind speed/wave data with 
            1st columnm: time_stamp => soon to  be set as index
            2nd column: observation,
            3rd column: era5, 
        - dt_modeled: float, modeled data/era5 data temporal interval. 
            while measurment data are converted to 1hr average
    Return

    '''

    df = df.dropna()
    df = df.set_index(df.columns[0])
    dt_1hr = 3600
    
    modeled_label = [col for col in df.columns if '_obs' not in col]
    f_modeled, S_modeled = compute_spectrum(df[modeled_label[0]].values, dt_modeled)

    # ======================================
    # Obsrvations data, for 1,2,3-hr average
    # ======================================
    # 1-hour
    obs_label = [col for col in df.columns if '_obs' in col]
    obs_1h = df[obs_label[0]].resample('1h').mean()
    f_1h, S_1h = compute_spectrum(obs_1h.dropna().values, dt_1hr)

    # 2-hour
    obs_2h = df[obs_label[0]].resample('2h').mean()
    f_2h, S_2h = compute_spectrum(obs_2h.dropna().values, dt_1hr*2)

    # 3-hour
    obs_3h = df[obs_label[0]].resample('3h').mean()
    f_3h, S_3h = compute_spectrum(obs_3h.dropna().values, dt_1hr*3)

    # ==================================================
    # -5/3 SLOPE, Kolmogorov power law (Wind Turbulence)
    # ==================================================
    f_ref = 1e-4 # defined by some important wind frequency?
    S_ref = np.interp(f_ref, f_1h, S_1h)

    f_slope = np.logspace(-7, -3, 100) # defined by some important wind frequency?
    S_slope = S_ref * (f_slope / f_ref) ** (-5/3)

    # =========================
    # PLOT
    # =========================

    plt.figure(figsize=(8,6))

    # Spectra

    plt.loglog(f_modeled, S_modeled, color='black', label='ERA5')
    plt.loglog(f_1h, S_1h, label='Measurements (1 h)')
    plt.loglog(f_2h, S_2h, label='Measurements (2 h)')
    plt.loglog(f_3h, S_3h, label='Measurements (3 h)')

    # -5/3 slope
    plt.loglog(f_slope, S_slope, 'k--')
    plt.text(2e-6, S_ref*2, r'$k^{-5/3}$')

    # =========================
    # REFERENCE TIME SCALES
    # =========================
    def add_time_line(period_sec, label):
        f = 1 / period_sec
        plt.axvline(f, color='k', linestyle='--', linewidth=0.8)
        plt.text(f, 1e0, label, rotation=90, va='bottom', ha='right')

    add_time_line(365*24*dt_1hr, '1 year')
    add_time_line(24*dt_1hr, '1 day')
    add_time_line(12*dt_1hr, '12 h')
    add_time_line(3*dt_1hr, '3 h')
    add_time_line(1*dt_1hr, '1 h')
    add_time_line(20*60, '20 min')

    # =========================
    # STYLE
    # =========================
    plt.xlabel('f [Hz]')
    plt.ylabel(r'S(f) [m$^2$/s]')
    plt.title(fig_title)

    plt.grid(True, which='both', linestyle='-', alpha=0.3)
    plt.legend()

    plt.xlim(1e-8, 1e-2)
    plt.ylim(1e-1, 1e7)

    plt.tight_layout()
    plt.show()


# %%
