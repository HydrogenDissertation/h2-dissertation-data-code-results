# SIMULATION 9 - CASE STUDY
#
# This case study simulation estimates electrolyzer and fuel cell
# capacity requirements based on Portugal’s net balance after exchanges,
# using both maximum and average deficit conditions.

import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    
    eff_fuel_cell = df_fuel_cells.loc[year, "Efficiency (%)"]

    df["Final Balance [MW]"] = 0.0
    df["Deficits [MW]"] = 0.0

    for i, row in df.iterrows():
        balance_pt = row["PT Balance [MW]"]
        balance_es = row["ES Balance [MW]"]

        pt_cost = row["PT Marginal Cost [€]"]
        es_cost = row["ES Marginal Cost [€]"]

        if pt_cost > 0:
            price_diff = abs(pt_cost - es_cost) / pt_cost
        elif es_cost > 0:
            price_diff = abs(es_cost - pt_cost) / es_cost
        else:
            price_diff = 0

        can_exchange = price_diff <= 0.2

        final_balance = 0.0
        deficit = 0.0

        if balance_pt >= 1:
            if balance_es < -1 and can_exchange:
                max_export = min(balance_pt, abs(balance_es))
                final_balance = balance_pt - max_export
            else:
                final_balance = balance_pt
        if balance_pt < 0:
            deficit = balance_pt

        df.at[i, "Final Balance [MW]"] = final_balance
        df.at[i, "Deficits [MW]"] = deficit


    # Final results
    df["Final Balance [MW]"] = df["Final Balance [MW]"].apply(lambda x: x if x >= 1 else 0)

    max_balance = df["Final Balance [MW]"].max()
    row_max = df.loc[df["Final Balance [MW]"].idxmax()]

    min_deficit = abs(df["Deficits [MW]"].min())
    row_min = df.loc[df["Deficits [MW]"].idxmin()]
    fuel_cells_min = min_deficit / eff_fuel_cell

    positive_balances = df[df["Final Balance [MW]"] > 0]["Final Balance [MW]"]
    average_balance = positive_balances.mean()
    average_deficit = abs(df["Deficits [MW]"].mean())
    fuel_cells_average = average_deficit / eff_fuel_cell



    print(f"\n--- Storage Simulation Results for {scenario} {year} ---")
    print(f"Maximum Balance: {max_balance:.2f} MW")
    print(f"Mean positive balances: {average_balance:.2f} MW")
    print(f"Minimum Deficit: {min_deficit:.2f} MW")
    print(f"Fuel Cells Min Cap: {fuel_cells_min:.2f} MW")
    print(f"Mean deficit: {average_deficit:.2f} MW")
    print(f"Fuel Cells Mean Cap: {fuel_cells_average:.2f} MW")
    #print(df["Final Balance [MW]"].describe())
    #print(f"Row id: {row_min}")


    return df


storage_simulation("GA", 2050)