'''
- Harmonic tidal analysis
        


@Author: Le Thi Trang
@Date: Mar 10, 2026

DNVGL-GL-2018: Metocean
- Water level consists of a mean

'''

def correct_to_MSL(water_data, data_interval):
    water_data = MSL = water_data['조위(m)'].mean()
    return MSL