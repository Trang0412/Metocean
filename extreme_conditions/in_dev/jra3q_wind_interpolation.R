# =========================================================
# Bilinear interpolation of JRA-3Q wind data
# Location: 33.5N, 126.75E
# Year: 2025
# =========================================================

# Required packages
library(terra)
library(ncdf4)

# ---------------------------------------------------------
# 1. Open JRA-3Q NetCDF file
# ---------------------------------------------------------
# Replace with your actual file path
dir_jra3q = "D:/InProbation/Metocean/Data/Typhoon_wind/JRA_3Q/"
nc_file <- "jra3q.anl_surf.0_2_3.vgrd10m-hgt-an-gauss.2026040100_2026043018.nc"

# Load raster stack
r <- rast(paste(dir_jra3q, nc_file, sep=""))

# Check variable names
names(r)

# ---------------------------------------------------------
# 2. Define target location
# ---------------------------------------------------------
target <- data.frame(
  lon = 126.75,
  lat = 33.5
)

# Convert to spatial vector
target_vect <- vect(
  target,
  geom = c("lon", "lat"),
  crs = "EPSG:4326"
)

# ---------------------------------------------------------
# 3. Bilinear interpolation
# ---------------------------------------------------------
# Extract interpolated values
interp_values <- extract(
  r,
  target_vect,
  method = "bilinear"
)

# ---------------------------------------------------------
# 4. Convert to dataframe
# ---------------------------------------------------------
interp_df <- as.data.frame(interp_values)

# Remove ID column
interp_df$ID <- NULL

# ---------------------------------------------------------
# 5. Add time information
# ---------------------------------------------------------
# Open NetCDF directly
nc <- nc_open(nc_file)

# Read time variable
time <- ncvar_get(nc, "time")

# Read time units
time_units <- ncatt_get(nc, "time", "units")$value

print(time_units)

# Example:
# "hours since 1958-01-01 00:00:00"

origin_time <- sub("hours since ", "", time_units)

datetime <- as.POSIXct(time * 3600,
                       origin = origin_time,
                       tz = "UTC")

interp_df$time <- datetime

# Close NetCDF
nc_close(nc)

# ---------------------------------------------------------
# 6. Reorder columns
# ---------------------------------------------------------
interp_df <- interp_df[, c("time", names(interp_df)[1:(ncol(interp_df)-1)])]

# ---------------------------------------------------------
# 7. Save output
# ---------------------------------------------------------
write.csv(
  interp_df,
  "JRA3Q_2025_33.5N_126.75E.csv",
  row.names = FALSE
)

# ---------------------------------------------------------
# 8. Preview
# ---------------------------------------------------------
head(interp_df)

# =========================================================
# OPTIONAL:
# If your dataset contains u10 and v10 wind components:
# =========================================================

# Example wind speed calculation
# interp_df$wind_speed <- sqrt(interp_df$u10^2 + interp_df$v10^2)
