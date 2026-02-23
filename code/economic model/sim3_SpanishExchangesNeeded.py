# SIMULATION 3
#
# This script integrates cross-border electricity exchanges with Spain.
# When Portugal has a surplus, part of it is first exported to cover Spanish deficits.
# Only the remaining surplus is available for hydrogen production.
# This simulation refines the storage dynamics by introducing export constraints,
# representing a more realistic Iberian market interaction.


import pandas as pd
from extract_data import get_data, df_electrolyzers, df_NT_installed_cap, df_fuel_cells, df_GA_installed_cap, df_DE_installed_cap

def storage_simulation_exchanges(scenario, year):

    # Load hourly energy data for the selected scenario and year
    year_string = str(year)
    df = get_data(f"Exchanges {year_string}", f"{scenario}.xlsx", "Index")

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
    eff_fuel_cell = df_fuel_cells.loc[year, "Efficiency (%)"] / 100

    # Calculate Spain's deficit (positive values only when Spain has negative balance)
    df["Deficit ES [MW]"] = df["ES Balance [MW]"].apply(lambda x: abs(x) if x < 0 else 0)

    # Determine how much excess Portugal can use for H2 production
    def available_for_h2(row):
        pt_balance = row["PT Balance [MW]"]
        es_deficit = row["Deficit ES [MW]"]

        if pt_balance <= 0:
            return 0  # No excess in Portugal
        elif es_deficit > 0:
            # Export to cover Spain's deficit, use the remaining for H2
            remaining = pt_balance - es_deficit
            return remaining if remaining > 0 else 0
        else:
            # Spain has no deficit → all excess stays in PT
            return pt_balance

    df["Available for H2 [MW]"] = df.apply(available_for_h2, axis=1)

    # Initialize H2 tracking
    storage = 0
    storage_list = []
    h2_total_production = 0
    h2_total_conversion = 0
    longest_positive_interval = 0
    current_interval = 0

    # Create output columns
    df["H2_produced [kg]"] = 0.0
    df["H2_converted [kg]"] = 0.0
    df["Storage H2 [kg]"] = 0.0

    for i, row in df.iterrows():
        balance = row["Available for H2 [MW]"]

        if balance >= 1:
            energy_used = min((balance * 0.33), cap_electrolyzer)
            h2_produced = (energy_used * 1000) / eff_electrolyzer
            storage += h2_produced
            h2_total_production += h2_produced
            df.at[i, "H2_produced [kg]"] = h2_produced
            current_interval += 1
        else:
            deficit_energy = abs(balance)  # not expected, but kept for consistency
            h2_needed = (deficit_energy * 1000) / (eff_fuel_cell * 33.33)
            h2_converted = min(h2_needed, storage)
            storage -= h2_converted
            h2_total_conversion += h2_converted
            df.at[i, "H2_converted [kg]"] = h2_converted
            longest_positive_interval = max(longest_positive_interval, current_interval)
            current_interval = 0

        storage_list.append(storage)
        df.at[i, "Storage H2 [kg]"] = storage

    # Final results
    max_storage = max(storage_list)

    print(f"\n--- Storage Simulation with Export Logic for {scenario} {year} ---")
    print(f"Maximum H2 stored: {max_storage:.2f} kg")
    print(f"Total H2 produced: {h2_total_production:.2f} kg")
    print(f"Total H2 converted: {h2_total_conversion:.2f} kg")
    print(f"Longest period without deficit: {longest_positive_interval} hours")
    return df

# Example run
storage_simulation_exchanges("NT", 2030)