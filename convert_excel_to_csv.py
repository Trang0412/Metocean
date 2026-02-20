import pandas as pd

coordinate_file = 'D:\\InProbation\\Station_coordinate.xlsx'
coor_data = pd.read_excel(coordinate_file, sheet_name='KHOA')
coor_data.head(5)