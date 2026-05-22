# extract specific information 
#%%
import pandas as pd
import numpy as np
dir_data = 'D:\InProbation\Metocean\Data\Observations\KMA\하도\\'
fnames = ['MARINE_CWBUOY_22517_HR_2023_2023_2024.csv', 'MARINE_CWBUOY_22517_HR_2024_2024_2025.csv', 'MARINE_CWBUOY_22517_HR_2025_2025_2026.csv']
dir_save = 'D:\\InProbation\\Metocean\\Shared data\\to_Khawar\\'


for fname in fnames:
    # #KHOA
    # try:
    #     all_data = pd.read_csv(dir_data + fname,  sep='\t', skiprows=3,header=0, encoding='cp949')
    # except: 
    #     all_data = pd.read_csv(dir_data + fname, sep='\t', skiprows=3,)

    # all_data = all_data.replace('-', np.nan) 

    # #KHOA
    # save_data = all_data[['관측시간', '유의파고(m)', '유의파주기(sec)']]

    #kma
    all_data = pd.read_csv(dir_data + fname, sep=',', header=0, encoding='cp949')
    save_data = all_data[['일시', '유의파고(m)', '파주기(sec)']]
    save_data.to_excel(dir_save + fname[:-4] + '.xlsx')

# %%
