import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

dir_data = 'D:\\InProbation\\Metocean\\Analysis\\Extreme conditions\\Wind\\non_typhoon\\'
omni_wind_rp = pd.read_excel(dir_data+'omnidir_RP.xlsx')

m, b = np.polyfit(omni_wind_rp['WS (m/s)'], omni_wind_rp['return period'], 1)

plt.scatter(omni_wind_rp['WS (m/s)'], omni_wind_rp['return period'], s=2,c='#808080')
plt.plot(omni_wind_rp['WS (m/s)'], m*omni_wind_rp['WS (m/s)']+b, color='gray', linestyle='-', linewidth=1)
plt.grid(True)
plt.show()

