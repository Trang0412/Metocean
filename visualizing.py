
import windrose
import matplotlib.pyplot as plt
from windrose import WindroseAxes

import matplotlib.font_manager as fm
import matplotlib.dates as mdates
import seaborn as sns
import matplotlib.colors as mcolors
import matplotlib as mpl
from matplotlib import colormaps as cmaps
from scipy.signal import welch

import statsmodels.api as sm
from scipy import stats
from scipy.stats import binned_statistic_2d
import numpy as np

import pandas as pd
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rc
plt.rcParams['axes.unicode_minus'] = False



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

def compute_spectrum(u, dt, nperseg=256):
    '''
    Compute spectrum of time series data
    Parameters:
        -u: np.array, time series data
        -dt: float, sampling interval of data, in unit of seconds
        -nperseg: length of each segment 

    Returns:
        -f: array of sample frequencies
        - S: power spectral density
    '''
    fs = 1 / dt
    u = u - np.mean(u)
    f, S = welch(u, fs=fs, nperseg=nperseg)
    return f[1:], S[1:]  # remove zero freq
    

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

