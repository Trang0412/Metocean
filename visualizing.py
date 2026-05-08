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
from plotly.subplots import make_subplots



from metocean_metadata import *
from common_processing import *
plt.rcParams.update({
    "text.usetex": False,
    "font.family": "Malgun Gothic"
})

# 1. Ensure Unicode minus is handled safely
plt.rcParams['axes.unicode_minus'] = False

# 2. Use the "Computer Modern" font (the LaTeX look) internally
plt.rcParams['mathtext.fontset'] = 'cm'
from matplotlib.ticker import PercentFormatter
import plotly.graph_objects as go

#%%
def plot_typhoon_windfield(u, v, lon_start, lat_start, res, size, fig_title):
    ''' Plot wind field (u,v) for typhoon at specific time on grid
    Parameters: 
        -u: np.ndarray, u-component of wind
        -v: np.ndarray, v-component of wind
        -lon_start: float, smallest longitude of grid
        -lat_start: float, smallest latitude of grid
        -res: float, resolution of grid
        -size: float, number of node of grid on each dimension

    Returns:
    '''
    # lon_start, lat_start = 117.0, 20.0
    # res = 0.03333333
    # size = 901

    # 2. Generate Coordinates
    lons = lon_start + np.arange(size) * res
    lats = lat_start + np.arange(size) * res
    lon_2d, lat_2d = np.meshgrid(lons, lats)

    # 3. Load and Reshape your Data

    # 4. Plotting with Cartopy
    fig = plt.figure(figsize=(12, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Add Geography for the Korean Peninsula context
    ax.set_extent([117, 135, 20, 45], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=1)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)

    # 5. The Quiver Command
    # 'skip' is critical so arrows don't overlap
    skip = 15

    q = ax.quiver(lon_2d[::skip, ::skip], 
                lat_2d[::skip, ::skip], 
                u[::skip, ::skip], 
                v[::skip, ::skip],
                color='blue', 
                scale=700,        # Adjust for arrow length
                width=0.002,      # Adjust for arrow thickness
                transform=ccrs.PlateCarree())

    # Add a reference arrow (Key)
    ax.quiverkey(q, 0.9, 0.05, 20, r'$20 \frac{m}{s}$', labelpos='E', coordinates='figure')

    plt.title(fig_title, fontsize=15)
    plt.show()



def plot_tidal_timeseries_harmonic(wl_all, coefs, fig_title, fname_save):
    '''Plot Time series of water level for Total, Tide and Residual components from Harmonic analysis 
    using UTide python-based package

    Parameters:
        -wl_all: pd.DataFrame, 4 columns 
            1st: Timestamp 
            2nd: total water level, relative to mean sea level (MSL)
            3rd: predicted tide
            4th: residual 

    Returns:
        None, plot figure only; can be dumped to excel file later

    '''

    # calculations for some quantities to put in text box
    wl_all = wl_all.dropna()
    msl = wl_all.iloc[:,2].mean()
    hat = wl_all.iloc[:,2].max()
    lat = wl_all.iloc[:,2].min()

    # get index of some tidal (harmonic) consituents
    m2_idx = np.argwhere(coefs['name']=='M2').ravel()[0]
    s2_idx = np.argwhere(coefs['name']=='S2').ravel()[0]
    k1_idx = np.argwhere(coefs['name']=='K1').ravel()[0]
    o1_idx = np.argwhere(coefs['name']=='O1').ravel()[0]
    
    
    mhws = msl + (coefs['A'][m2_idx] + coefs['A'][s2_idx])
    mhwn = msl + abs(coefs['A'][m2_idx] - coefs['A'][s2_idx])

    mlws = msl - (coefs['A'][m2_idx] + coefs['A'][s2_idx])
    mlwn = msl - abs(coefs['A'][m2_idx] - coefs['A'][s2_idx])

    f_min = min(coefs['aux']['frq'])/(2*math.pi)


    # compute form factor, as DHI report 'Type'
    ff_num = coefs['A'][k1_idx]+coefs['A'][o1_idx]
    ff_den = coefs['A'][m2_idx]+coefs['A'][s2_idx]
    ff = ff_num/ff_den
    if ff < 0.25:
        ff_type = 'Semidiurnal'
    elif ff < 1.5:
        ff_type = 'Mixed, mainly semidiurnal'
    elif ff <= 3:
        ff_type = 'Mixed, mainly dirunal'
    else:
        ff_type = 'Dirunal'

    fig, ax = plt.subplots(figsize=(9,3))
    ax.plot(wl_all.iloc[:,0], wl_all.iloc[:,1], c='#C0C0C0', label='Total', 
             linewidth='1')
    ax.plot(wl_all.iloc[:,0], wl_all.iloc[:,2], c='#069AF3', label='Tide',
             linewidth='1')
    ax.plot(wl_all.iloc[:,0], wl_all.iloc[:,3], c='#FFA500', label='Residual',
             linewidth='1')
    ax.legend(loc='upper right', bbox_to_anchor=(0.5, 0., 0.5, 0.5))

    textstr = '\n'.join((
        r'$Max\ Total=%.2f mMSL$' % (wl_all.iloc[:,1].max(), ),
        r'$Max\ Residual=%.2f mMSL$' % (wl_all.iloc[:,2].max(), ),
        '\n',
        r'$HAT = %.2f\ mMSL$' % (hat,),
        r'$MHWS = %.2f\ mMSL$' % (mhws,),
        r'$MHWN = %.2f\ mMSL$' % (mhwn,),
        r'$MLWS = %.2f\ mMSL$' % (mlws,),
        r'$MLWN = %.2f\ mMSL$' % (mlwn,),
        r'$LAT = %.2f\ mMSL$' % (lat),
        '\n',
        r'$Min\ Residual = %.2f\ mMSL$' % (wl_all.iloc[:,2].min(),),
        r'$Min\ Total = %.2f\ mMSL$' % (wl_all.iloc[:,1].min(),),
        '\n',
        r'$N = %.0f$' % (len(wl_all)),
        r'$Method = IOS(UTide)$',
        r'$Levels = Timeseries$',
        f'Type = {ff_type}',
        r'$f_{min} = %.3f Hz$' % (f_min),
        r'$N_{const} = %.0f$' % (len(coefs['name']))
    ))

    ax.text(
        1.1, 0.0, textstr, transform=ax.transAxes, fontsize=8
    )

    n_ticks = np.ceil(max(wl_all.iloc[:,1:4].max())/0.5)
    y_lim = n_ticks*0.5
    y_ticks = list(np.linspace(-y_lim, y_lim, int(n_ticks*2+1)))
    y_ticks_labels = [''.join(r'$%.2f$' % y) for y in y_ticks]

    ax.set(ylabel='WL [mMSL]', title=fig_title, 
           yticks=y_ticks, yticklabels=y_ticks_labels)
    ax.tick_params(axis='x', labelrotation=45)

    plt.tight_layout(pad=0)
    plt.show()

def plot_probability(data, bin_step, fig_title, xlabel, ylabel_l, ylabel_r=''):
    '''
    Plot empirical density and cumulative distribution (optional) of measurement

    Parameters:
        -data: pd.Series/pd.DataFrame of data
        -bin_step: float, bin width for measurement
        -xlabel: str, label for xaxis
        -ylabel_l: str, label for yaxis on the left
        -ylabel_r: str, label for yaxis on the right
        -fig_title: str, title of the figure
    
    Returns:
        -None, maybe dump to excel file later
    '''
    fig, ax1 = plt.subplots()
    upper_bound = max(max(data.values), np.ceil(max(data.values)/2)*2)
    bins = np.arange(0, upper_bound+bin_step, bin_step)
    style = {'facecolor': '#c5c7c9', 'edgecolor': '#929591', 'linewidth': 1}

    counts, edges = np.histogram(data.values, bins=bins)
    if 'prob' in ylabel_l.lower():
        bar = ax1.bar(edges[:-1], counts/len(data)*100, width=np.diff(edges), 
                    align='edge', **style, 
                    label = 'Histogram')
    else:
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
    
    if ylabel_r!='':
        ax2 = ax1.twinx()

        cum = np.cumsum(counts) / np.sum(counts) * 100

        y_cdf = np.insert(cum, 0, 0)
        cdf_line = ax2.plot(
            edges,  # align with left bin edges
            y_cdf,
            linestyle='-',
            color='#030764',
            linewidth=1.5, 
            label = 'Cumulative Histogram',
        )
        ax2.legend(handles=cdf_line, loc='upper left', bbox_to_anchor=(0.5, 0.9))

        ax2.set_ylim(0, 100)
        ax2.set_ylabel(ylabel_r)
    fig.suptitle(fig_title)

    plt.show()


def dual_rose_plot(data1, data2, lg_title1='', lg_title2='',
                   speed_name='풍속(m/s)', dir_name='풍향(deg)', 
                   fig_title='', fname_save='', 
                   speed_step=2, dir_step=30, calm_limit=2, max_val=22):
    ''' Dual rose plot to compare 2 data, e.g., measurement and ERA5
    
    Parameters:
    Returns:
    '''
    hole_r = 0.15 # radius of hole in middle center of the plot for Calm condition
    line_color = '#5D6166'
    data1 = data1.dropna()
    data2 = data2.dropna()
    speed_bins = np.arange(calm_limit, min(np.ceil(data1.iloc[:,1].max()/speed_step)*speed_step, max_val) + speed_step, speed_step)
    dir_bins = np.arange(dir_step, 360+dir_step, dir_step)

    trace_names = [f'{s_-speed_step}-{s_}' for s_ in speed_bins]
    n_traces = len(trace_names)
    range_radialaxis1 = np.zeros(n_traces)
    range_radialaxis2 = np.zeros(n_traces)

    count_each_dir1 = [((data1[dir_name]>=d-dir_step) & (data1[dir_name]<d)).sum() for d in dir_bins]
    count_each_dir1[-1] = (data1[dir_name]>=dir_bins[-2]).sum()
    ratio_each_dir1 = [c/len(data1) for c in count_each_dir1]

    count_each_dir2 = [((data2[dir_name]>=d-dir_step) & (data2[dir_name]<d)).sum() for d in dir_bins]
    count_each_dir2[-1] = (data2[dir_name]>=dir_bins[-2]).sum()
    ratio_each_dir2 = [c/len(data2) for c in count_each_dir2]

    # plot calm text for wind data less than 2 m/s
    calm_data_1 = data1[(data1[speed_name]>=0) & (data1[speed_name]<calm_limit)]
    r_calm_1 = [((calm_data_1[dir_name]>=d-dir_step) & (calm_data_1[dir_name]<d)).sum() for d in dir_bins]
    r_calm_1[-1] = (calm_data_1[dir_name]>=dir_bins[-2]).sum() 
    r_calm_1 = [100*r_calm_1[i]*ratio_each_dir1[i]/count_each_dir1[i] for i in range(len(dir_bins))]
    range_radialaxis1[0] = sum(r_calm_1)

    calm_data_2 = data2[(data2[speed_name]>=0) & (data2[speed_name]<calm_limit)]
    r_calm_2 = [((calm_data_2[dir_name]>=d-dir_step) & (calm_data_2[dir_name]<d)).sum() for d in dir_bins]
    r_calm_2[-1] = (calm_data_2[dir_name]>=dir_bins[-2]).sum() 
    r_calm_2 = [100*r_calm_2[i]*ratio_each_dir2[i]/count_each_dir2[i] for i in range(len(dir_bins))]
    range_radialaxis2[0] = sum(r_calm_2)

    trace_names[-1] = f'>={speed_bins[-2]}'

    # plot
    fig = go.Figure()
    # traces of data 1
    fig.add_trace(go.Barpolar(
        r=[0],
        name=f'<{calm_limit}({sum(r_calm_1):.2f}%)',
        legend='legend1',
        legendgroup='g1', 
        legendgrouptitle={'text':lg_title1},
        marker=dict(
            color=windrose_colors_1[0],
            line=dict(color='#000000', width=1)
        ),
    ))
    for ti in range(1, n_traces):
        if ti == n_traces -1:
            trace_data1 = data1[data1[speed_name]>=speed_bins[ti]-speed_step]
        else:
            trace_data1 = data1[(data1[speed_name]>=speed_bins[ti]-speed_step) & (data1[speed_name]<speed_bins[ti])]

        r1 = [((trace_data1[dir_name]>=d-dir_step) & (trace_data1[dir_name]<d)).sum() for d in dir_bins]
        r1[-1] = (trace_data1[dir_name]>=dir_bins[-2]).sum()
        r1 = [100*r1[i]*ratio_each_dir1[i]/count_each_dir1[i] for i in range(len(dir_bins))]
        fig.add_trace(go.Barpolar(
            r=r1,
            name = trace_names[ti],
            legend='legend1',
            legendgroup='g1', 
            legendgrouptitle={'text':lg_title1},
            marker=dict(
            color=windrose_colors_1[ti],
            line=dict(color='#000000', width=1)
        ),
        ))

    # trace of data 2
    fig.add_trace(go.Barpolar(
        r=[0],
        name=f'<{calm_limit}({sum(r_calm_2):.2f}%)',
        legend='legend2',
        legendgroup='g2', 
        legendgrouptitle={'text':lg_title2},
        marker=dict(
            color=windrose_colors_1[0],
            line=dict(color='#000000', width=1)
        ),
    ))
    r2_stacked = np.zeros(len(dir_bins))
    for ti in range(1, n_traces):
        if ti == n_traces -1:
            trace_data2 = data2[data2[speed_name]>=speed_bins[ti]-speed_step]
        else:
            trace_data2 = data2[(data2[speed_name]>=speed_bins[ti]-speed_step) & (data2[speed_name]<speed_bins[ti])]

        r2 = [((trace_data2[dir_name]>=d-dir_step) & (trace_data2[dir_name]<d)).sum() for d in dir_bins]
        r2[-1] = (trace_data2[dir_name]>=dir_bins[-2]).sum()
        r2 = [100*r2[i]*ratio_each_dir2[i]/count_each_dir2[i] for i in range(len(dir_bins))]
       
        fig.add_trace(go.Barpolar(
            r=r2,
            name=trace_names[ti],
            base=r2_stacked,
            legend='legend2',
            legendgroup='g2',
            legendgrouptitle={'text':lg_title2},
            width=15,
            marker=dict(
            color=windrose_colors_2[ti],
            line=dict(color='#000000', width=1),
            
        ),
        ))
        r2_stacked = r2_stacked + r2

    # updata layout
    fig.update_layout(
        template=None,
        annotations=[
            dict(
                x=0.5,
                y=0.5,
                text='Calm',
                showarrow=False,
                font=dict(size=13, color="black"),
                xref="paper",
                yref="paper",
                xanchor="center",
                yanchor="middle"
            ),

        ],
        title=dict(text=fig_title),
        font_size=13,
        legend_font_size=13,
        legend_font_color='#000000',
        polar_radialaxis_ticksuffix='%',
        polar_angularaxis_rotation=90,
        polar_angularaxis_direction='clockwise',
        # legend_traceorder="reversed",
        legend1=dict(
            xanchor='right',
            x=1.1,
            y=0.5,
            traceorder="reversed",
        ),
        legend2=dict(
            xanchor='left',
            x=-0.1,
            y=0.5,
            traceorder="reversed",
        )
    )   

    fig.update_polars(
        hole=hole_r,
        radialaxis=dict(
            # range=[0, max(np.ceil(max(ratio_each_dir1[1:-1])*100/5)*5, 20)],
            range=[0, max(np.ceil(max(max(ratio_each_dir1[1:-1]),max(ratio_each_dir2[1:-1]))*100/5)*5, 20)],
            dtick=5,
            tick0=5,
            gridcolor=line_color,
            linecolor=None,
            autotickangles=[0, 45, 90,],
            layer='below traces',
            tickfont_size = 13,
            categoryorder="total ascending",
            linewidth=0,
            ticklen=0,
        ),
        angularaxis=dict(
            tickmode='array',
            tickvals=[0, 90, 180, 270],
            ticktext=['North', 'East', 'South', 'West'],
            tickcolor=None,
            ticklen=0,
            tickfont_color=None,
        )
        )
    # fig.show()
    if fname_save != '':
        fig.write_image(fname_save, format="png")


def rose_plot(data, speed_name='풍속(m/s)', dir_name='풍향(deg)', fig_title='', fname_save='', speed_step=2,
                    dir_step=30, calm_limit=2, max_val=22):
    '''
    Rose plot for wind direction and wind_speed
    
    Parameters:
        -data: pd.DataFrame, 3 columns of 1st is time, 2nd is speed, and 3rd is degree
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
    # prepare data to as standard input format for plotly, using pandas MultiIndex
    data = data.dropna()
    dir_bins = np.arange(dir_step, 360+dir_step, dir_step)
    speed_bins = np.arange(calm_limit, min(np.ceil(data[speed_name].max()/speed_step)*speed_step, max_val)+speed_step, speed_step) # lower bound of bins
    line_color = '#5D6166'

    trace_names = [f'{speed-speed_step:.0f} - {speed:.0f}' for speed in speed_bins]
    
    n_traces = len(trace_names)
    lb_dir = [dir_val - dir_step for dir_val in dir_bins]
    count_data_each_dir = [((data[dir_name]>=lb_dir[i]) & (data[dir_name]<dir_bins[i])).sum() for i in range(len(dir_bins)-1)]
    count_data_each_dir.extend([(data[dir_name]>=lb_dir[-1]).sum()])
    ratio_each_dir = [c/len(data) for c in count_data_each_dir]
    
    # plot
    fig = go.Figure()
    # in calm condition, only present name
    range_radialaxis = np.zeros(n_traces)
    calm_data = data[(data[speed_name]>=0) & (data[speed_name]<calm_limit)]
    r_calm = [(((calm_data[dir_name]>=dir_bins[i]-dir_step) & (calm_data[dir_name]<dir_bins[i])).sum()) for i in range(len(dir_bins))]
    r_calm[-1] = (calm_data[dir_name]>=dir_bins[-2]).sum()
    r_calm = [100*ratio_each_dir[i]*r_calm[i]/count_data_each_dir[i] for i in range(len(dir_bins))]
    trace_names[0] = f'<{calm_limit} ({sum(r_calm):.2f}%)'
    range_radialaxis[0] = sum(r_calm)
    fig.add_trace(go.Barpolar(
        r=[0], 
        name=trace_names[0],
        marker=dict(
            color=windrose_colors_1[0],
            line=dict(color='#000000', width=1)
        ),
    ))

    for ti in range(1, n_traces):
        if ti==n_traces-1:
            trace_data = data[data[speed_name]>=speed_bins[ti]-speed_step]
            trace_names[-1] = f'>={speed_bins[-2]:.0f} ({sum(r):.2f}%)'
        else:
            trace_data = data[(data[speed_name]>=speed_bins[ti]-speed_step) & (data[speed_name]<speed_bins[ti])]
        r = [(((trace_data[dir_name]>=d-dir_step) & (trace_data[dir_name]<d)).sum()) for d in dir_bins]
        r[-1] = (trace_data[dir_name]>=dir_bins[-2]).sum()
        r = [100*ratio_each_dir[i]*r[i]/count_data_each_dir[i] for i in range(len(dir_bins))]
        range_radialaxis[ti] = sum(r)

        fig.add_trace(go.Barpolar(
            r = r,
            name = trace_names[ti],
            marker=dict(
                color=windrose_colors_1[ti],
                line=dict(color=line_color, width=1)
            )  
        ))

    fig.update_layout(
        template=None,
        annotations=[
            dict(
                x=0.5,
                y=0.5,
                text='Calm',
                showarrow=False,
                font=dict(size=13, color="black"),
                xref="paper",
                yref="paper",
                xanchor="center",
                yanchor="middle"
            ),

        ],
        title=dict(text=fig_title),
        font_size=13,
        legend_font_size=13,
        legend_font_color='#000000',
        polar_radialaxis_ticksuffix='%',
        polar_angularaxis_rotation=90,
        polar_angularaxis_direction='clockwise',

    )   

    fig.update_polars(
        hole=0.15,
        radialaxis=dict(
            range=[0, max(np.ceil(max(ratio_each_dir[1:-1])*100/5)*5, 20)],
            gridcolor=line_color,
            linecolor=None,
            autotickangles=[0, 45, 90,],
            layer = 'below traces',
            tickfont_size = 13,
            categoryorder= "total ascending",
            linewidth=0,
            ticklen=0,
        ),
        angularaxis=dict(
            tickmode='array',
            tickvals=[0, 90, 180, 270],
            ticktext=['North', 'East', 'South', 'West'],
            tickcolor=None,
            ticklen=0,
            tickfont_color=None,
        )
        )
    
    # fig.show()
    if fname_save != '':
        fig.write_image(fname_save, format="png")


def plot_nearest_point_era5_regrid_era5(bounding_area, vars_metadata, compare_statn, era5_coor, regrid_era5_coor=None):
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

    if regrid_era5_coor != None:
        reg_era5_nearest_point = regrid_era5_geo_locs.sel(lat=disp_locs[compare_statn][1], lon=disp_locs[compare_statn][0], method='nearest').coords
        reg_era5_nearest_point = [round(float(reg_era5_nearest_point['lon'].values),2),
                                round(float(reg_era5_nearest_point['lat'].values),2)]

        plot_points = dict({compare_statn: disp_locs.get(compare_statn), 
                            'Loc in Original ERA5': era5_nearest_point, 
                            'Loc in Regrided ERA5': reg_era5_nearest_point})
    else:         
        plot_points = dict({compare_statn: disp_locs.get(compare_statn), 
                    'Loc in Original ERA5': era5_nearest_point})
    plot_locs_on_geo_map(bounding_area, plot_points, minor_res = 0.05, turnon_loc_name=True)


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

    if minor_res != None:
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
                                xytext=xytext_loc, textcoords="offset points", color='k', fontsize=9)
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
    # plt.show()
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)
    if fname_save != "":
        fig.savefig(fname_save, dpi=300, bbox_inches="tight")


def plot_time_series_2vars(data, data1_label, data2_label, fig_size=[6.4, 4.8], fig_title="", fname_save="", 
                           fc1 ='#808080', fc2 ='#069AF3', txt_loc1 = [0.05, 0.95], txt_loc2= [0.05, 0.87], 
                           plot_type='scatter', lstyle1 = '-', lstyle2='--', ylabel_text='Hs', xtick_rotation=45):
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
    data = data.dropna()

    # figure plot
    fig, ax = plt.subplots(1, figsize=fig_size)
    if plot_type=='DHI':
        fc1 = '#808080'
        fc2 ='#069AF3'

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

        # -------------------------------------------------
        # PLOT
        # -------------------------------------------------
        ax.scatter(data.iloc[:,0], data.iloc[:,1], s=4, c=fc1)
        ax.scatter(data.iloc[:,0], data.iloc[:,2], s=4, c=fc2)
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


    elif plot_type=='MIT':

        # -------------------------------------------------
        # STATISTICS BOX
        # -------------------------------------------------
        N = len(data)
        bias = np.mean(data.iloc[:,2] - data.iloc[:,1])
        mse = np.mean(np.abs(data.iloc[:,2] - data.iloc[:,1])**2)
        rmse = np.sqrt(np.mean((data.iloc[:,2] - data.iloc[:,1]) ** 2))
        cc = np.corrcoef(data.iloc[:,2],data.iloc[:,1])[0, 1]

        stats_text = (
            f"MSE = {mse:.3f} {nl}"
            f"RMSE = {rmse:.3f} {nl}"
            f"Bias = {bias:.3f} {nl}"
            f"Corr = {cc:.3f} {nl}"
            f"Matches = {N:.0f}"
        )

        # -------------------------------------------------
        # PLOT
        # -------------------------------------------------
        ax.plot(data.iloc[:,0], data.iloc[:,1], linestyle=lstyle1, c=fc1, linewidth=1.5, label=data1_label)
        ax.plot(data.iloc[:,0], data.iloc[:,2], linestyle=lstyle2, c=fc2, linewidth=1.5, label=data2_label)
        ax.text(
        txt_loc1[0], txt_loc1[1], stats_text,
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=9, c = 'k',
        bbox=dict(boxstyle='round', facecolor='none')
        )

        ax.grid(visible=True, c="lightgrey")
        ax.legend()


    ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=1))

    if ylabel_text != '':
        plt.ylabel(ylabel_text)
    else:
        plt.ylabel(df_columns[1].split('_')[0])
    plt.xticks(rotation=xtick_rotation, ha='right')
    plt.title(fig_title) 
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)
    # plt.show()

    if fname_save != "":
        fig.savefig(fname_save, dpi=600, bbox_inches="tight")

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

def scatter_plot_ERA5_against_meas(data, fig_size, axis_lims, bin_width, x_tick, fig_title='', fname_save=''):
    '''
    Scatter plot of ERA5 against measurements for checking ERA5 validity as a 
    reliable source to force the hydrodynamic and wave models for FEED metocean study
    
    Refer to Figure 2.10 from DHI report for Wando-Gumil, page 22

    Paratemeter
        -data: pd.DataFrame, of 3 columns, where each column is a variable and each row is an observation
            Col 0: Timestamp, Col 1: measurement, Col 2: ERA5 data
        -axis_lims: array or list, of minimum and maximum limits for ticks in x-y axis
        -bin_width: float, bin of value for variables quantization for density plot
        -x_tick: int, tick distance for x, y
        -fig_title: str, title of figure

    Return

        -None, only show figure
        Later can return stats information
    '''

    # Mar 18, 2026: explicitly remove missing value
    data = data.dropna()
    param_unit = data.columns[1].split('(')[1]
    param_unit = param_unit.split(')')[0]

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
    ax.set_xticks(np.arange(xlims[0],xlims[1],x_tick))
    ax.set_yticks(np.arange(ylims[0],ylims[1],x_tick))

    ax.set_xlabel(f'{data.columns[1]}')
    ax.set_ylabel(f'{data.columns[2]}')

    ax.grid(True, ls=":", lw=0.8)

    # -------------------------------------------------
    # COLORBAR
    # -------------------------------------------------
    cbar = plt.colorbar(sc, ax=ax, fraction=0.046, pad=0.02)
    cbar.set_label(f'Number of data points in each {bin_width} {param_unit} bin')

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
    # plt.show()

    if fname_save != '':
        fig.savefig(fname_save) 


def plot_wind_spectra_comparison(df_ws_combine, sampling_interval, fig_title, f_ref=1e-5, fname_save=''):
    ''' Visualize sepctrum density of wind for ERA5 and observed data averaged over 1,2,3h
    Parameters:
        -df: pd.DataFrame, 3 columns   
            1st: timestemp
            2nd: oberved wind speed
            3rd: era5 wind speed
        -sampling_interval: float, sampling interval of data, represented in seconds 

    Returns:
        dict_spect: dictionary of frequency as keys and spectra as values
    '''

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
    plt.figure()
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
    x_lim = [1e-8, 1e-2]
    y_lim = [1e-1, 1e7]

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

    plt.xticks(x_ticks, x_tick_labels)
    plt.yticks(y_ticks, y_tick_labels)
    plt.xlabel('f [Hz]')
    plt.ylabel(r'$S/\sigma^2$ [s]')

    plt.legend(fontsize=9)
    plt.title(fig_title)

    if fname_save != '':
        plt.savefig(fname_save) 
    # plt.show()
# %%
