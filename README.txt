Arrange the code later (Jan 27, 2026)




%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Script hierarchy (Jan 26, 2026)

-script/
	-predecated/
			- work_with_era5.py: 	main code for integratively working with ERA5 data
			- work_with_measurement.py: 	main code for integratively working with measurement data

	- main.py: main code for working with both ERA5 and measurement data
	- plot_data.py:		composite of useful plotting functions
	- compute_variables.py: 	composite of useful functions for computing different variables from both ERA5 and measurement data
	- useful_mappings.py: 		mappings of Korean names of measurement to English name for easy use. (not used yet)
	- find_nearest_location.py:		Plot of grid of area where ERA5 were retrieved
	- convert_excel_to_csv.py:		Convert excel to csv file
	- request_ERA5_data_all_year(_2nd_thread).py:		API for requesting ERA5 data with certain variables, years, month, etc.  from Copernicus website