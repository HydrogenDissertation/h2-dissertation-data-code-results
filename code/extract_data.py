# EXTRACT DATA
#
# This file extracts the values from the excels and 
# stores them in dataframes according to the different 
# scenarios and equipements

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Pathway to the folder where the file is (extract_data.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Function that gets the data from the excels and stores them in the respective dataframes
# It receives the sheet_name where the table is found, the file_path that is the name of the excel and the index
# that can be the years or the actual index of the table
def get_data(sheet_name, file_path, index):

    try:
        # Read Excel
        df = pd.read_excel(os.path.join(BASE_DIR, file_path), sheet_name=sheet_name)
        #df = pd.read_excel(file_path, sheet_name=sheet_name)
        df.set_index(index, inplace=True)
        return df
    
    except FileNotFoundError:
        print(f" File '{file_path}' not found.")
        return None
    
    except ValueError:
        print(f" The sheet '{sheet_name}' does not exist in '{file_path}'.")
        return None


# This dfs store data of every equipement in study 

df_electrolyzers = get_data("Electrolyzer","data.xlsx","Years")
df_fuel_cells = get_data("Fuel Cells","data.xlsx","Years")
df_storage_saltCaverns = get_data("Storage Salt Caverns","data.xlsx","Years")
df_compressors_saltCaverns = get_data("Compressors Reciprocating","data.xlsx","Years")
df_storage_pressurisedTanks = get_data("Storage Pressurised Tanks","data.xlsx","Years")
df_compressors_pressurisedTanks = get_data("Compressor Reciprocating Piston","data.xlsx","Years")

# This dfs store the installed capacity predicted of every equipement for the diferent scenairos according to the years in study 

df_NT_installed_cap = get_data("NT Installed Capacity","data.xlsx","Years")
df_GA_installed_cap = get_data("GA Installed Capacity","data.xlsx","Years")
df_DE_installed_cap = get_data("DE Installed Capacity","data.xlsx","Years")

