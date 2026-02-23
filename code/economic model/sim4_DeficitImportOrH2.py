# SIMULATION 4
#
# The simulation identifies the worst deficit sequences requiring H2,
# and estimates the corresponding fuel cell and storage capacity needed.
# This step introduces the import-price threshold logic to the model,
# bridging market conditions with hydrogen system operation.


import pandas as pd
from extract_data import get_data, df_fuel_cells, df_storage_pressurisedTanks, df_storage_saltCaverns

def worst_H2_deficit_sequence(scenario, year, electricity_costThreshold):
    df = get_data(str(year), f"{scenario}.xlsx", "Index")

    eff_tanks = df_storage_pressurisedTanks.loc[year, "Efficiency (%)"]
    eff_caverns = df_storage_saltCaverns.loc[year, "Efficiency (%)"]
    eff_storage = (eff_tanks + eff_caverns) / 2

    # 2. Create new column: mark PT deficit hours without viable import (ES expensive)
    df["Use_H2"] = ((df["PT Balance [MW]"] < -1) & (df["ES Marginal Cost [€]"] >= electricity_costThreshold)).astype(int)

    # If there are no deficits to cover with H2
    if df["Use_H2"].sum() == 0:
        print(f"\n--- {scenario} {year} H2 Deficit Sequence ---")
        print("No deficits requiring H2 (all can be imported from ES).")
        summary = {
            "Scenario": scenario,
            "Year": year,
            "Threshold ES": electricity_costThreshold,
            "Worst H2 single-hour deficit (MW)": 0,
            "Worst H2 continous deficit (MW)": 0,
            "Estimated H2 required (kg))": 0,
            "Duration (hours)": 0
        }
        return df, summary

    # 3. Group continuous sequences of deficits to be covered with H2
    df["H2DeficitGroup"] = (df["Use_H2"] != df["Use_H2"].shift()).cumsum()
    h2_deficit_sequences = df[df["Use_H2"] == 1].groupby("H2DeficitGroup")

    # 4. Calculate sequence summary
    sequence_summary = h2_deficit_sequences["PT Balance [MW]"].agg(
        TotalDeficitMW=lambda x: -x.sum(),
        DurationHours="count",
        StartHour=lambda x: x.index[0],
        EndHour=lambda x: x.index[-1]
    )

    # 5. Choose the worst sequence (largest total deficit)
    worst_sequence = sequence_summary.sort_values("TotalDeficitMW", ascending=False).iloc[0]

    # 6. Conversion to kg H2 (using fuel cell efficiency)
    LHV_H2 = 33.33  # kWh/kg
    eff_fuel_cell = df_fuel_cells.loc[year, "Efficiency (%)"]
    total_deficit_kWh = worst_sequence["TotalDeficitMW"] * 1000
    h2_required_kg = total_deficit_kWh / (eff_fuel_cell * LHV_H2)
    worst_hourly_deficit = abs((df.loc[df['Use_H2'] == 1, 'PT Balance [MW]'].min()))
    worst_sequence_deficit = worst_sequence['TotalDeficitMW']

    duration = worst_sequence['DurationHours']
    fuel_cell_cap = abs(worst_hourly_deficit / eff_fuel_cell)
    storage_cap =  (worst_hourly_deficit * duration) / (eff_fuel_cell * eff_storage)
    storage_cap_inOut = worst_hourly_deficit / (eff_fuel_cell * eff_storage)
    

    print(f"\n--- {scenario} {year} H2 Deficit Sequence ---")
    print(f"Threshold ES: {electricity_costThreshold:.2f} €/MWh")
    print(f"Worst H2-required single-hour deficit: {worst_hourly_deficit:.2f} MW")
    print(f"Fuel Cells Capacity: {fuel_cell_cap:.2f} MW")
    print(f"Worst sequence (no import):")
    print(f"  • Total deficit: {worst_sequence_deficit:.2f} MWh")
    print(f"  • Estimated H2 required: {h2_required_kg:.2f} kg")
    print(f"  • Storage Capacity: {storage_cap:.2f} MWh")
    print(f"  • Storage Capacity In/Out: {storage_cap_inOut:.2f} MW")

    print(f"  • Duration: {duration} hours")
    print(f"  • From hour {worst_sequence['StartHour']} to {worst_sequence['EndHour']}")
    #print(f"Average Electricity Cost: {avg_threshold:.2f} MW")
    #print(f"Average Electricity Cost During Defecits: {avg_deficitThreshold:.2f} MW")

    summary = {
        "Scenario": scenario,
        "Year": year,
        "Threshold ES": electricity_costThreshold,
        "Worst H2 single-hour deficit (MW)": worst_hourly_deficit,
        "Worst H2 continous deficit (MWh)": worst_sequence_deficit,
        "Estimated H2 required (kg)": h2_required_kg,
        "Duration (hours)": worst_sequence['DurationHours'],
        "Fuel Cells Capacity (MW)": fuel_cell_cap,
        "Storage Capacity (MWh)": storage_cap,
        "Storage Capacity In/Out (MW)": storage_cap_inOut,
    }

    return df, summary

worst_H2_deficit_sequence("NT", 2030, 26)