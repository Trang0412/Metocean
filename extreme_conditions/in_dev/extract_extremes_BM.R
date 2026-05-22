# Extract extreme values with Block Maxima approach
# Author: Le Thi Trang
# Date: May 13, 2026


library(extRemes)
library(readxl)
library(tibble)
library(readr)

# define fix parameters here
dir_analysis <- "D:/InProbation/Metocean/Analysis/Extreme conditions/"
rp = c(1.1, 10, 50, 100, 10000)

# Dense return periods
rp_plot <- exp(seq(log(1.1), log(1000), length.out = 200))

#---------------------------------------------
# NEED TO CHANGE DEPEND ON DATA TO BE ANALYZED
ext_data <- "Wind/non_typhoon/"
dir_ext <- paste(dir_analysis, ext_data, sep="")
file_name <- "era5_nontp_126.75E_33.75N.csv"
data_unit <- "m/s"


#---------------------------------------------
# Extract values for EVA
full_path <- paste(dir_ext, file_name ,sep="")
data <- read_csv(full_path)
data$Time <- as.POSIXct(data$Time, format="%Y-%m-%d %H:%M:%S")

# Extract year
data$Year <- format(data$Time, "%Y")

# Annual block maxima
annual_max <- aggregate(
  data$`WS (m/s)`,
  by = list(data$Year),
  FUN = max,
  na.rm = TRUE
)
colnames(annual_max) <- c("Year", "AnnualMax")
annual_max$Year <- as.numeric(annual_max$Year)
write.csv(annual_max, paste(dir_ext,"annual_maxmima.csv",sep=""), row.names=FALSE)


#---------------------------------------------
# FIT GUMBEL 
fit_gumbel <- fevd(x=annual_max$AnnualMax, type="Gumbel", method="MLE", 
                   units=data_unit)

summary(fit_gumbel)
capture.output(summary(fit_gumbel), file=paste(dir_ext, "fit_gumbel_summary.txt", sep=""))


png(filename=paste(dir_ext,"fit_gumbel_plot.png",sep=""), width=900, height=900, res=150)
plot(fit_gumbel)
dev.off()

# only save return period
png(filename=paste(dir_ext,"fit_gumbel_return_level.png",sep=""), width=900, height=900, res=150)
plot(fit_gumbel, type='rl')
dev.off()


# only save return period with bootstrap CI
# Bootstrap CI
rl_ci <- ci(fit_gumbel, type="return.level",return.period=rp_plot, method="boot", R=200)
fit_rl <- return.level( fit_gumbel, return.period=rp_plot)

png(filename=paste(dir_ext,"gumbel_RL_CI_boostrap.png",sep=""), width=700, height=700, res=150)
#plot(fit_gumbel, type='rl')
plot(rp_plot, fit_rl,type="l", log="x", ylim=range(rl_ci),
     xlab="Return Period (years)", ylab = "Return Level",
     main = "Return Level Plot with Bootstrap CI")

# Add bootstrap CI
lines(rp_plot, rl_ci[,1],lty = 2)
lines(rp_plot, rl_ci[,3],lty = 2)
# Internal plotting positions
xdat <- sort(fit_gumbel$x)
n <- length(xdat)
prob <- (1:n - 0.35) / n
emp_rp <- 1 / (1 - prob)
# Add empirical points
points(emp_rp, xdat, pch = 1)
dev.off()


#print(rp_plot)
#print(fit_gumbel$data)

return.level(fit_gumbel, return.period=rp, alpha=0.05, do.ci=TRUE, units=data_unit)


# Convert to data frame
rl_table <- data.frame(ReturnPeriod=rp, ReturnLevel = rl_ci[,1], Lower95 = rl_ci[,2], Upper95 = rl_ci[,3])
write.csv(rl_table, paste(dir_ext,"return_level_curve_with_ci.csv",sep=""), row.names=FALSE)


# Save fit parameters
params <- data.frame(Parameter=names(fit_gumbel$results$par), Value=fit_gumbel$results$par)
write.csv(params, paste(dir_ext, "gumbel_parameters.csv",sep=""), row.names=FALSE)

# Save return levels
rl <- return.level(fit_gumbel, return.period=rp, alpha=0.05, do.ci=TRUE, units=data_uni)
return_levels <- data.frame(ReturnPeriod=rp, Lower95=as.numeric(rl[,1]), ReturnLevel=as.numeric(rl[,2]), Upper95=as.numeric(rl[,3]))
write_csv(return_levels, paste(dir_ext,"return_levels_gumbel.csv", sep=""))



