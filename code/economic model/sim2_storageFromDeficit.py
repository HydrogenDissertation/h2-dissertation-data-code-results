# SIMULATION 2
#
# This script analyses electricity deficit periods in each scenario and year,
# identifying the worst single-hour and cumulative deficit sequences.
# From these, it estimates the required hydrogen storage capacity and
# fuel cell sizing needed to fully cover system deficits.
# This establishes the baseline for storage dimensioning in later simulations.

import pandas as pd
from extract_data import get_data, df_electrolyzers, df_NT_installed_cap, df_fuel_cells, df_GA_installed_cap, df_DE_installed_cap, df_storage_pressurisedTanks, df_storage_saltCaverns

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
    
    eff_tanks = df_storage_pressurisedTanks.loc[year, "Efficiency (%)"]
    eff_caverns = df_storage_saltCaverns.loc[year, "Efficiency (%)"]
    eff_storage = (eff_tanks + eff_caverns) / 2

    # 1. Identify worst hourly deficit
    worst_hourly_deficit = df["Balance with Exchanges [MW]"].min()

    # 2. If there is deficit (1) if not (0)
    df["IsDeficit"] = (df["Balance with Exchanges [MW]"] < -1).astype(int)

    # 3. Create groups of continuous sequences of deficits
    df["DeficitGroup"] = (df["IsDeficit"] != df["IsDeficit"].shift()).cumsum()
    deficit_sequences = df[df["IsDeficit"] == 1].groupby("DeficitGroup")

    if df["IsDeficit"].sum() == 0:
        print(f"\n--- {scenario} {year} Deficit Analysis ---")
        print("No significant deficits found (below 0 MW).")
        return df

    # 4. Calculate the cumulative total by sequence
    sequence_summaries = deficit_sequences["Balance with Exchanges [MW]"].agg(
        TotalDeficitMW=lambda x: -x.sum(),  
        DurationHours="count",
        StartHour=lambda x: x.index[0],
        EndHour=lambda x: x.index[-1]
    )

    # 5. Find the sequence with the largest accumulated deficit
    worst_sequence = sequence_summaries.sort_values("TotalDeficitMW", ascending=False).iloc[0]

    LHV_H2 = 33.33  # kWh/kg
    eff_fuel_cell = df_fuel_cells.loc[year, "Efficiency (%)"]
    total_deficit_kWh = worst_sequence["TotalDeficitMW"] * 1000
    h2_required_kg = total_deficit_kWh / (eff_fuel_cell * LHV_H2)
    fuel_cell_cap = worst_hourly_deficit / eff_fuel_cell
    storage_cap = (total_deficit_kWh / 1000) / (eff_fuel_cell * eff_storage)

    print(f"\n--- {scenario} {year} Deficit Analysis ---")
    print(f"Worst single-hour deficit: {worst_hourly_deficit:.2f} MW")
    print(f"Fuel Cells Capacity: {fuel_cell_cap:.2f} MW")
    print(f"Worst deficit sequence:")
    print(f"  • Total deficit: {worst_sequence['TotalDeficitMW']:.2f} MW")
    print(f"  • Estimated H2 required: {h2_required_kg:.2f} kg")
    print(f"  • Storage Capacity: {storage_cap:.2f} MW")
    print(f"  • Duration: {worst_sequence['DurationHours']} hours")
    print(f"  • From hour {worst_sequence['StartHour']} to {worst_sequence['EndHour']}")
    return df
    

storage_simulation("DE", 2050)

