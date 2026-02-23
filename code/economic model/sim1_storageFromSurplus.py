# SIMULATION 1
#
# This script implements the baseline simulation of the economic model.
# Hydrogen is produced exclusively from surplus electricity and stored,
# while energy deficits are covered through reconversion via fuel cells.
# It establishes the fundamental storage and conversion dynamics used
# as a reference for the following simulations.


import pandas as pd
from extract_data import get_data, df_electrolyzers, df_NT_installed_cap, df_fuel_cells, df_GA_installed_cap, df_DE_installed_cap

def storage_simulation(scenario, year):

    # Load hourly energy data for the selected scenario and year
    year_string = str(year)
    df = get_data(year_string, f"{scenario}.xlsx", "Index")

    # Select correct installed capacity dataframe
    if scenario == "NT":
        installed_cap_df = df_NT_installed_cap
    elif scenario == "DE":
        installed_cap_df = df_DE_installed_cap
    elif scenario == "GA":
        installed_cap_df = df_GA_installed_cap
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    # Technical parameters
    eff_electrolyzer = df_electrolyzers.loc[year, "Efficiency (kWh/kgH2)"]
    cap_electrolyzer = installed_cap_df.loc[year, "Electrolyzers (MW)"]
    eff_fuel_cell = df_fuel_cells.loc[year, "Efficiency (%)"]# /100

    # Initialization of variables
    storage = 0  # H2 in storage at each hour (kg)
    storage_list = []  # to track storage levels hour by hour
    h2_total_production = 0
    h2_total_conversion = 0
    longest_positive_interval = 0
    current_interval = 0

    # Create columns for outputs
    df["H2_produced [kg]"] = 0.0
    df["H2_converted [kg]"] = 0.0
    df["Storage H2 [kg]"] = 0.0

    for i, row in df.iterrows(): # Iterates each row of the df, i is the index, the row contains the info about balance, cost, etc
        balance = row["Balance with Exchanges [MW]"] # Stores the current balance value

        if balance >= 1:
            # Surplus → use part of it to produce H2
            energy_used = min((balance * 0.33), cap_electrolyzer) # The energy used can not excedd the capacity installed of electrolysers
            h2_produced = (energy_used * 1000) / eff_electrolyzer  # MW to kWh, then to kg H2
            storage += h2_produced # Updates the current stored H2 value
            h2_total_production += h2_produced # Updates the total H2 produced
            df.at[i, "H2_produced [kg]"] = h2_produced # Stores the value of H2 produced in the df
            current_interval += 1 # Counts how many hours there have been surpluses


        else:
            # Deficit → convert H2 to electricity
            deficit_energy = abs(balance)  # turns the negative value into positive in MW
            h2_needed = (deficit_energy * 1000) / (eff_fuel_cell * 33.33)  # Calculates how much H2 is need to cover the deficit using LHV conversion
            h2_converted = min(h2_needed, storage) # We can't convert more H2 then the one that its stored
            storage -= h2_converted # Updates the stored value
            h2_total_conversion += h2_converted # Updates the value of the total of H2 converted
            df.at[i, "H2_converted [kg]"] = h2_converted # Stores the value of H2 converted in the df

            # Update longest interval without deficit
            longest_positive_interval = max(longest_positive_interval, current_interval) 
            current_interval = 0
            

        storage_list.append(storage)  
        df.at[i, "Storage H2 [kg]"] = storage 

    # Final results
    max_storage = max(storage_list)

    print(f"\n--- Storage Simulation Results for {scenario} {year} ---")
    print(f"Maximum H2 stored: {max_storage:.2f} kg")
    print(f"Total H2 produced: {h2_total_production:.2f} kg")
    print(f"Total H2 converted: {h2_total_conversion:.2f} kg")
    print(f"Longest period without deficit: {longest_positive_interval} hours")
    return df


storage_simulation("NT", 2030)