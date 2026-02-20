import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

#%% Create figure and map projection
fig = plt.figure(figsize=(5, 5))
ax = plt.axes(projection=ccrs.PlateCarree())

# Set map extent (Jeju Island region)
ax.set_extent([120, 138, 32, 40], crs=ccrs.PlateCarree())

# Add coastline only
ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=0.3)

# Gridlines with labels
gl = ax.gridlines(draw_labels=True, linewidth=0, linestyle='--')
gl.top_labels = False
gl.right_labels = False

# Axis labels formatting
gl.xlabel_style = {'size': 9}
gl.ylabel_style = {'size': 9}

plt.show()