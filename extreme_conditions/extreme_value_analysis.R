# Conduct Extreme Value Analysis
# Author: Le Thi Trang
# Date: May 13, 2026


library(extRemes)
library(readxl)
library(tibble)
library(readr)

# define path information here
dir_analysis <- "D:/InProbation/Metocean/Analysis/Extreme conditions/"

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# NEED TO CHANGE DEPEND ON DATA TO BE ANALYZED
ext_data <- "Wind/non_typhoon/"
dir_ext <- paste(dir_analysis, ext_data, sep="")
file_name <- "era5_nontp_126.75E_33.75N.csv"
col_name <- "WS (m/s)"


# fitting approach use
fit_dist = "Gumbel"
fit_method = "MLE"

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Load data for EVA, e.g., ERA5 for wind
full_path <- paste(dir_ext, file_name ,sep="")
data <- read_csv(full_path)
data_anl <- as.matrix(data[,col_name])


# Extract extremes value 
ext_type = "BM"



# Fit Generalized Extreme Value distribution
fit_gumbel <- fevd(x=extremes_ws, type = "Gumbel", method="MLE", units="m/s")

# Summary
summary(fit_gumbel)

# Plot diagnostics
plot(fit_gumbel)
plot(fit_gumbel, "trace")

# Return levels
return.level(fit_gumbel, return.period = c(1.1, 10, 50, 100),
             do_ci=TRUE, alpha=0.05, units='m/s')


# ===============================
# 4. QQ plot
# ===============================

qqnorm(extremes_ws)
qqline(extremes_ws)


