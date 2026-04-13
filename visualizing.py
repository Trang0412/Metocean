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
import plotly

from common_processing import *

plt.rcParams['font.family'] = 'Malgun Gothic'

plt.rc
plt.rcParams['axes.unicode_minus'] = False
from matplotlib.ticker import PercentFormatter


#%%
def plot_hist_cdf(data, bin_step, xlabel, ylabel_l, ylabel_r, fig_title):
    ''' Plot histogram of data with cumulative distribution function overlays

    Parameters:
        -data: pd.DataFrame, 2 column with 1st: Timestamp, 2nd: measurement (e.g., wind speed)
    Returns:
    '''

    fig, ax1 = plt.subplots()
    upper_bound = max(max(data.iloc[:,1]), np.ceil(max(data.iloc[:,1])/2)*2)
    bins = np.arange(0, upper_bound+bin_step, bin_step)
    style = {'facecolor': 'none', 'edgecolor': 'C0', 'linewidth': 1}

    counts, edges = np.histogram(data.iloc[:,1], bins=bins)
    bar = ax1.bar(edges[:-1], counts, width=np.diff(edges), 
                  align='edge', **style, 
                  label = 'Histogram')
    ax1.set_xlim(edges[0], edges[-1])
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(ylabel_l)
    ax1.set_xticks(bins)
    ax1.set_xlim(bins[0], bins[-1])
    ax1.margins(x=0)

    ax1.legend(handles=[bar], loc='upper left', bbox_to_anchor=(0.5, 0.8))
    
    ax2 = ax1.twinx()

    cum = np.cumsum(counts) / np.sum(counts) * 100

    y_cdf = np.insert(cum, 0, 0)
    cdf_line = ax2.plot(
        edges,  # align with left bin edges
        y_cdf,
        linestyle='--',
        color='black',
        linewidth=1.5, 
        label = 'Cumulative Histogram',
    )
    ax2.legend(handles=cdf_line, loc='upper left', bbox_to_anchor=(0.5, 0.9))

    ax2.set_ylim(0, 100)
    ax2.set_ylabel(ylabel_r)
    fig.suptitle(fig_title)

    plt.show()


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
def rose_plot(speed, direction, fig_title="", speed_step=2,
                   dir_sector=30, bins=[4,6,8,10,12,14,16,18,20], calm_limit=4,
                   label_pos=260, rticks_label=[5, 10, 15, 20], rmax_val = 20, 
                   ytick_labels=['5%', '10%', '15%', '20%'], bbox_anchor=(1, 0.1)):
    '''
    Rose plot for wind direction and wind_speed
    
    Parameters:
        -speed: np.array, speed of measurement
        -direction: np.array, direction of measurement
        -fig_title: string, figure's title
        -sector_width: float, width of degree sector. IEC suggest of 30, 22.5
            default: 30
        -bins: np.array, array of values as bins to put in legend
        -calm_limit: float, upper bound value of wind when it is considered as calm
            default: 2 (m/s)
        -rmax_val: float, percentage 
    
    Return:
        None. Just showing plot

    '''
    nsector = int(360/dir_sector)

    bins = np.arange(calm_limit, max(speed)+speed_step, speed_step)
    fig = plt.figure(figsize=(3,3))
    ax = WindroseAxes.from_ax()
    ax.bar(direction, speed, nsector=nsector, blowto=False, 
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


def wind_rose_plot(speed, direction, fig_title="", speed_step=2,
                   dir_sector=30, bins=[4,6,8,10,12,14,16,18,20], calm_limit=4,
                   label_pos=260, rticks_label=[5, 10, 15, 20], rmax_val = 20, 
                   ytick_labels=['5%', '10%', '15%', '20%'], bbox_anchor=(1, 0.1)):
    '''
    Rose plot for wind direction and wind_speed
    
    Parameters:
        -speed: np.array, speed of measurement
        -direction: np.array, direction of measurement
        -fig_title: string, figure's title
        -sector_width: float, width of degree sector. IEC suggest of 30, 22.5
            default: 30
        -bins: np.array, array of values as bins to put in legend
        -calm_limit: float, upper bound value of wind when it is considered as calm
            default: 2 (m/s)
        -rmax_val: float, percentage 
    
    Return:
        None. Just showing plot

    '''
    ax = plt.subplot(111, projection='polar')
    ax.bar(direction, speed)


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


def spectra_comparison(df, dt_modeled, x_lim, y_lim, fig_title):
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
def plot_wind_spectra_comparison(df_ws_combine, sampling_interval, f_ref, x_lim, y_lim, fig_title):
    ''' Visualize sepctrum density of wind for ERA5 and observed data averaged over 1,2,3h
    Parameters:
        -df: pd.DataFrame, 3 columnes   
            1st: timestemp
            2nd: oberved wind speed
            3rd: era5 wind speed
        -sampling_interval: float, sampling interval of data, represented in seconds 

    Returns:
        dict_spect: dictionary of frequency as keys and spectra as values
    '''

    plt.rcParams['text.usetext'] = True
    df_ws_combine = df_ws_combine.dropna()
 
    col_names = df_ws_combine.columns
    obs_1h = df_ws_combine.iloc[:,[0,1]]

    obs_2h = obs_1h.groupby(pd.Grouper(key=col_names[0], freq='2h')).mean().reset_index()
    obs_3h = obs_1h.groupby(pd.Grouper(key=col_names[0], freq='3h')).mean().reset_index()

    obs_2h.dropna(inplace=True)
    obs_3h.dropna(inplace=True)

    # compute spectrum
    f_1h, S_1h = compute_spectrum(obs_1h.iloc[:,1].values, sampling_interval)
    f_2h, S_2h = compute_spectrum(obs_2h.iloc[:,1].values, sampling_interval*2)
    f_3h, S_3h = compute_spectrum(obs_3h.iloc[:,1].values, sampling_interval*3)

    f_era5, S_era5 = compute_spectrum(df_ws_combine.iloc[:,2].values, sampling_interval)

    # plot
    plt.loglog(f_era5, S_era5/np.power(df_ws_combine.iloc[:,2].std(),2), 'k', label='ERA5', linewidth=1)

    plt.loglog(f_1h, S_1h/np.power(obs_1h.iloc[:,1].std(),2), 'royalblue', label='Measurements (1h)', linewidth=1)
    plt.loglog(f_2h, S_2h/np.power(obs_2h.iloc[:,1].std(),2), 'forestgreen', label='Measurements (2h)', linewidth=1)
    plt.loglog(f_3h, S_3h/np.power(obs_3h.iloc[:,1].std(),2), 'darkorange', label='Measurements (3h)', linewidth=1)

    # plot -5/3 line (slope line)
    # f_ref = 1e-5 # roughly 1 hour
    S_ref = np.interp(f_ref, f_1h, S_1h/np.power(obs_1h.iloc[:,1].std(),2))
    k = np.logspace(-6.5,-3,100)
    slope_line = S_ref *(k / f_ref)**(-5/3) # why??
    plt.loglog(k, slope_line, 'grey', linewidth=1)
    plt.text(1e-6, 1e6, r'$k^{-5/3}$')
    plt.grid(color='0.8', linestyle='-', linewidth=0.3, which='minor')
    
    # add timeline of 20 mins, 1h, 2h, 3h, 12h, 1day, 1 year
    time_lines = [20*60, 60*60, 2*60*60,  3*60*60,  12*60*60,  24*60*60, 365*24*60*60]
    freq_spot = [1/time for time in time_lines]

    vline_legends = ['20 min', '1 h', '2 h', '3 h', '12 h', '1 Day', '1 Year']
    for i, x_vline in enumerate(freq_spot):
        plt.vlines(x_vline, y_lim[0], y_lim[1], linestyles='--', linewidth=0.7, colors='k')
        plt.text(x_vline*np.power(10, 0.03), np.power(10, -0.7), vline_legends[i], rotation='vertical')

    # setting tick labels as minus sign is not correctly displayed by matplotlib
    x_ticks = np.logspace(-8, -2, 7)
    y_ticks = np.logspace(-1, 7, 9)

    x_tick_labels =[r'$10^{-8}$', r'$10^{-7}$', r'$10^{-6}$', r'$10^{-5}$', 
                    r'$10^{-4}$', r'$10^{-3}$', r'$10^{-2}$']
    y_tick_labels =[r'$10^{-1}$', r'$10^0$', r'$10^1$', r'$10^2$', 
                    r'$10^3$', r'$10^4$', r'$10^5$', r'$10^6$', r'$10^7$']

    plt.xlim(x_lim)
    plt.ylim(y_lim)
    plt.xticks(x_ticks, x_tick_labels)
    plt.yticks(y_ticks, y_tick_labels)
    plt.xlabel('f [Hz]')
    plt.ylabel(r'$S/\sigma^2$ [s]')

    plt.legend(fontsize=9)
    plt.title(fig_title)

    plt.show
