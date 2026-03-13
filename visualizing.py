
import windrose
import matplotlib.pyplot as plt
from windrose import WindroseAxes

import matplotlib.font_manager as fm
import matplotlib.dates as mdates
import seaborn as sns
import matplotlib.colors as mcolors
import matplotlib as mpl
from matplotlib import colormaps as cmaps

import statsmodels.api as sm
from scipy import stats
from scipy.stats import binned_statistic_2d
import numpy as np

import pandas as pd
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rc




def plot_time_series_1var(data, x_label, y_label, fig_size=[6.4, 4.8], fig_title="", fname_save="", txt_box_loc = [1.1, 1.1]):
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
    ax.scatter(data[x_label], data[y_label], s=4)

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


def plot_time_series_2vars(data1, data2):
    '''
    Scatter plot of 2 time series data for visually comparisons.
    Refer to Figure 2.13 DHI report
    
    Parameters:
        data: list of pd.DataFrame, one for more data to plot
        x_variable: str, name of variables to plot in x_axis
        y_variable: str, name of variables to plot in y_axis

    Return:
        None, just showing plot
        Xticks are set to first day each month, by funtion DayLocator
    '''
    pass



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
def scatter_plot_ERA5_against_meas(data, axis_lims, bin_width, fig_title, fname_save):
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
    bin_width = 0.2 # separate bin with 0.2 m/s
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
    fig, ax = plt.subplots(figsize=(8, 7))

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
        1.6, 1.1, stats_text,
        transform=ax.transAxes,
        ha="right", va="top",
        fontsize=9,
        bbox=dict(boxstyle="round", fc="white", ec="black")
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