# SIMULATION 7
#
# This simulation applies separate price thresholds for hydrogen production
# and deficit coverage, integrating both imports and storage use. It refines
# the model by combining market conditions with operational constraints.

import pandas as pd
from extract_data import get_data, df_electrolyzers, df_fuel_cells, df_storage_saltCaverns, df_storage_pressurisedTanks, df_compressors_saltCaverns, df_compressors_pressurisedTanks, df_NT_installed_cap, df_GA_installed_cap, df_DE_installed_cap

def results_simulation(scenario, year, storage_ratio, threshold_selling):

    # Load hourly energy data for the selected scenario and year
    year_string = str(year)
    df = get_data(year_string, f"{scenario}.xlsx", "Index")
    thresholds_df = pd.read_excel("sim7_thresholdValues.xlsx", "Thresholds")

    # Select correct installed capacity dataframe
    if scenario == "NT":
        installed_cap_df = df_NT_installed_cap
    elif scenario == "DE":
        installed_cap_df = df_DE_installed_cap
    elif scenario == "GA":
        installed_cap_df = df_GA_installed_cap
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    
    if storage_ratio == 100:
        storage_saltCaverns_percentage = 1.0
        storage_pressurisedTanks_percentage = 0.0
    elif storage_ratio == 0:
        storage_saltCaverns_percentage = 0.0
        storage_pressurisedTanks_percentage = 1.0
    else:
        storage_saltCaverns_percentage = storage_ratio/100
        storage_pressurisedTanks_percentage = 1.0 - storage_saltCaverns_percentage

    row_match = thresholds_df[
        (thresholds_df["Scenario"] == scenario) &
        (thresholds_df["Year"] == year) &
        (thresholds_df["Threshold Value"].round(2) == round(threshold_selling, 2))
    ]

    if len(row_match) != 1:
        raise ValueError(f"Configuração não encontrada para {scenario} {year} com threshold {threshold_selling}")

    # Extrair valores da linha correspondente
    cap_fuel_cell = row_match["Fuel Cells Capacity (MW)"].values[0]
    cap_storage = row_match["Storage Capacity (MWh)"].values[0]

    # Technical parameters
    ####################################################################################################################
    # Electrolyzers
    eff_electrolyzer = df_electrolyzers.loc[year, "Efficiency (kWh/kgH2)"]
    capex_electrolyzer = df_electrolyzers.loc[year, "CAPEX (€/kW)"]
    opex_electrolyzer = df_electrolyzers.loc[year, "OPEX yearly (€/kW/year)"]
    lifetime_electrolyzer = df_electrolyzers.loc[year, "Lifetime (hours)"]
    capex_anual_electrolyzer = capex_electrolyzer / lifetime_electrolyzer

    cap_electrolyzer = installed_cap_df.loc[year, "Electrolyzers (MW)"]

    # Compressors
    # For Salt Caverns
    eff_compressors_saltCaverns = df_compressors_saltCaverns.loc[year, "Efficiency (%)"]
    capex_compressors_saltCaverns = df_compressors_saltCaverns.loc[year, "CAPEX (€/kW)"]
    opex_compressors_saltCaverns = df_compressors_saltCaverns.loc[year, "OPEX yearly (€/kW/year)"]
    lifetime_compressors_saltCaverns = df_compressors_saltCaverns.loc[year, "Lifetime (hours)"]
    comsumption_compressors_saltCaverns = df_compressors_saltCaverns.loc[year, "Consumption (kWh/kgH2)"]
    capex_anual_compressors_saltCaverns = capex_compressors_saltCaverns / lifetime_compressors_saltCaverns

    cap_compressors_saltCaverns = (cap_electrolyzer * 1000) / eff_electrolyzer * comsumption_compressors_saltCaverns * storage_saltCaverns_percentage

    # Salt Caverns
    eff_storage_saltCaverns = df_storage_saltCaverns.loc[year, "Efficiency (%)"]
    capex_storage_saltCaverns = df_storage_saltCaverns.loc[year, "CAPEX (€/kgH2)"]
    opex_storage_saltCaverns = df_storage_saltCaverns.loc[year, "OPEX yearly (€/kW/year)"]
    lifetime_storage_saltCaverns = df_storage_saltCaverns.loc[year, "Lifetime (hours)"]
    capex_anual_storage_saltCaverns = capex_storage_saltCaverns / lifetime_storage_saltCaverns

    # Pressurized Tanks
    eff_storage_pressurisedTanks = df_storage_pressurisedTanks.loc[year, "Efficiency (%)"]
    capex_storage_pressurisedTanks = df_storage_pressurisedTanks.loc[year, "CAPEX (€/kgH2)"]
    opex_storage_pressurisedTanks = df_storage_pressurisedTanks.loc[year, "OPEX yearly (€/kW/year)"]
    lifetime_storage_pressurisedTanks = df_storage_pressurisedTanks.loc[year, "Lifetime (hours)"]
    capex_anual_storage_pressurisedTanks = capex_storage_pressurisedTanks / lifetime_storage_pressurisedTanks

    # Fuel Cells

    eff_fuel_cell = df_fuel_cells.loc[year, "Efficiency (%)"]
    capex_fuel_cell = df_fuel_cells.loc[year, "CAPEX (€/kW)"]
    opex_fuel_cell = df_fuel_cells.loc[year, "OPEX yearly (€/kW/year)"]
    lifetime_fuel_cell = df_fuel_cells.loc[year, "Lifetime (hours)"]
    capex_anual_fuel_cell = capex_fuel_cell / lifetime_fuel_cell

    ####################################################################################################################

    # Initialization of variables
    cap_storage_kg = cap_storage * 1000 / 33.33
    storage = 0  # H2 in storage at each hour (kg)
    storage_list = []  # to track storage levels hour by hour

    cap_storage_caverns = cap_storage_kg * storage_saltCaverns_percentage
    cap_storage_tanks = cap_storage_kg * storage_pressurisedTanks_percentage

    avg_compression_consumption = storage_saltCaverns_percentage * comsumption_compressors_saltCaverns 

    storage_tanks = 0
    storage_caverns = 0

    h2_total_production = 0
    h2_total_conversion = 0
    electricity_used = 0
    total_deficits = 0

    capex_total = ( 
        capex_anual_electrolyzer * cap_electrolyzer * 1000 + 
        capex_anual_compressors_saltCaverns * cap_compressors_saltCaverns + 
        capex_anual_storage_pressurisedTanks * cap_storage_kg * storage_pressurisedTanks_percentage +
        capex_anual_storage_saltCaverns * cap_storage_kg * storage_saltCaverns_percentage + 
        capex_anual_fuel_cell * cap_fuel_cell * 1000 
    )
    
    opex_total = ( 
        opex_electrolyzer * cap_electrolyzer * 1000 + 
        opex_compressors_saltCaverns * cap_compressors_saltCaverns + 
        opex_storage_pressurisedTanks * cap_storage_kg * storage_pressurisedTanks_percentage + 
        opex_storage_saltCaverns * cap_storage_kg * storage_saltCaverns_percentage + 
        opex_fuel_cell * cap_fuel_cell * 1000 
    )
    
    eff_total_equipments = ( 
        eff_fuel_cell * 
        ( 
            eff_storage_saltCaverns * storage_saltCaverns_percentage + 
            eff_storage_pressurisedTanks * storage_pressurisedTanks_percentage
        ) * 
        ( 
            eff_compressors_saltCaverns * storage_saltCaverns_percentage #+ 
        ) * 
        ( 
            33.33 /
            eff_electrolyzer 
        )
    )

    threshold_buying = threshold_selling * eff_total_equipments


    # Create columns for outputs
    df["H2_produced [kg]"] = 0.0
    df["H2_converted [kg]"] = 0.0
    df["Storage H2 [kg]"] = 0.0
    df["Elec_used_for_H2 [kWh]"] = 0.0
    df["Elec_from_H2 [kWh]"] = 0.0
    df["Elec_recovered [kWh]"] = 0.0
    df["Cost_H2_production [€]"] = 0.0
    df["Cost_H2_conversion [€]"] = 0.0


    for i, row in df.iterrows(): # Iterates each row of the df, i is the index, the row contains the info about balance, cost, etc

        balance_pt = row["PT Balance [MW]"] * 1000 # Stores the current balance value
        balance_es = row["ES Balance [MW]"] * 1000

        es_electricityCost = row["ES Marginal Cost [€]"]
        pt_electricityCost = row["PT Marginal Cost [€]"]

        if pt_electricityCost > 0:
            price_diff = abs(pt_electricityCost - es_electricityCost) / pt_electricityCost 
        elif es_electricityCost > 0:
            price_diff = abs( es_electricityCost - pt_electricityCost ) / es_electricityCost 
        else:
            price_diff = 0
        
        if price_diff > 0.2:
            can_exchange = False
        else:
            can_exchange = True

        ###########
        # SURPLUS #
        ###########
        if balance_pt >= 1: # Surplus of electricity → produce and store H2
            if pt_electricityCost <= threshold_buying:
                if balance_es < -1 and can_exchange:
                    max_export = min(balance_pt, abs(balance_es)) 
                    balance_pt -= max_export  
                    balance_es += max_export  

                if balance_pt >= 1: # Se ainda houver excedente
                    energy_available = balance_pt
                    
                    if storage < cap_storage_kg: # There is storage place available

                        # Where do we store?
                        if storage_ratio == 100: # Storage 100% in Salt Caverns

                            eff_total = eff_electrolyzer + comsumption_compressors_saltCaverns
                            
                            h2_produced = energy_available / eff_total # em kg

                            if storage + h2_produced > cap_storage_kg:
                                h2_produced = cap_storage_kg - storage
                                electricity_used = ( h2_produced / eff_compressors_saltCaverns ) * eff_total
                            else:
                                electricity_used = energy_available

                        elif storage_ratio == 0: # Storage 100% in Pressurized Tanks

                            eff_total = eff_electrolyzer
                            
                            h2_produced = energy_available / eff_total 

                            if storage + h2_produced > cap_storage_kg:
                                h2_produced = cap_storage_kg - storage
                                electricity_used = ( h2_produced * eff_total )
                            else:
                                electricity_used = energy_available

                        else: # Storage in Pressurized Tanks and Salt Caverns

                            if storage_tanks == cap_storage_tanks: # Tanks are full store only in Caverns
                                
                                eff_total = eff_electrolyzer + comsumption_compressors_saltCaverns
                                
                                h2_produced = energy_available / eff_total * eff_compressors_saltCaverns 

                                if storage_caverns + h2_produced > cap_storage_caverns:
                                    h2_produced = cap_storage_caverns - storage_caverns
                                    electricity_used = ( h2_produced / eff_compressors_saltCaverns ) * eff_total 
                                else:
                                    electricity_used = energy_available

                            elif storage_caverns == cap_storage_caverns: # Caverns are full store only in Tanks

                                eff_total = eff_electrolyzer 
                                
                                h2_produced = energy_available / eff_total 

                                if storage_tanks + h2_produced > cap_storage_tanks:
                                    h2_produced = cap_storage_tanks - storage_tanks
                                    electricity_used =  h2_produced * eff_total
                                else:
                                    electricity_used = energy_available

                            else: # Both Tanks and Caverns are available
                                
                                elec_per_kg_caverns = eff_electrolyzer + comsumption_compressors_saltCaverns
                                elec_per_kg_tanks = eff_electrolyzer

                                available_caverns = cap_storage_caverns - storage_caverns
                                available_tanks = cap_storage_tanks - storage_tanks

                                target_energy_caverns = energy_available * storage_saltCaverns_percentage
                                target_energy_tanks = energy_available * storage_pressurisedTanks_percentage

                                h2_target_caverns = target_energy_caverns / elec_per_kg_caverns
                                h2_target_tanks = target_energy_tanks / elec_per_kg_tanks

                                h2_caverns_stored = min(h2_target_caverns, available_caverns)
                                h2_tanks_stored = min(h2_target_tanks, available_tanks)

                                remaining_caverns_elec = max(0, target_energy_caverns - (h2_caverns_stored * elec_per_kg_caverns))
                                remaining_tanks_elec = max(0, target_energy_tanks - (h2_tanks_stored * elec_per_kg_tanks))

                                available_tanks -= h2_tanks_stored
                                available_caverns -= h2_caverns_stored

                                if available_tanks > 0:
                                    remaining_to_tanks = remaining_caverns_elec / elec_per_kg_tanks
                                    h2_remaning_tanks = min (remaining_to_tanks, available_tanks)
                                    h2_tanks_stored += h2_remaning_tanks

                                if available_caverns > 0:
                                    remaining_to_caverns = remaining_tanks_elec / elec_per_kg_caverns
                                    h2_remaning_caverns = min (remaining_to_caverns, available_caverns)
                                    h2_caverns_stored += h2_remaning_caverns


                                storage_caverns += h2_caverns_stored
                                storage_tanks += h2_tanks_stored
                                h2_produced = h2_caverns_stored + h2_tanks_stored

                                elec_used_caverns = h2_caverns_stored * elec_per_kg_caverns
                                elec_used_tanks = h2_tanks_stored * elec_per_kg_tanks

                                electricity_used = elec_used_caverns + elec_used_tanks
                
                        storage += h2_produced # Updates the current stored H2 value
                        df.at[i, "H2_produced [kg]"] = h2_produced # Stores the value of H2 produced in the df
                        df.at[i, "Elec_used_for_H2 [kWh]"] = electricity_used

        ###########
        # DEFICIT #
        ###########
        else: # Deficit → convert H2 to electricity
            
            deficit_energy = abs(balance_pt)
            total_deficits += deficit_energy
            energy_imported = 0
            energy_recovered = 0

            if es_electricityCost < threshold_buying and can_exchange and balance_es > 0:
                energy_imported = min(balance_es, deficit_energy)
                deficit_energy -= energy_imported

            if deficit_energy > 0 and pt_electricityCost >= threshold_selling:
                
                if storage > 0: # If there is H2 stored to cover the deficit

                    h2_needed_fuelCell = (deficit_energy) / (eff_fuel_cell * 33.33)  # Calculates how much H2 is need to cover the deficit using LHV conversion
                                    
                    if storage_ratio == 100: # Storage only in Salt Caverns
                        h2_needed_storage = h2_needed_fuelCell / eff_storage_saltCaverns

                        h2_converted = min(storage, h2_needed_storage)

                        energy_recovered = min((h2_converted * eff_storage_saltCaverns * eff_fuel_cell * 33.33), deficit_energy)

                        storage -= h2_converted
                        

                    elif storage_ratio == 0:
                        h2_needed_storage = h2_needed_fuelCell / eff_storage_pressurisedTanks

                        h2_converted = min(storage, h2_needed_storage)

                        energy_recovered = min((h2_converted * eff_storage_pressurisedTanks * eff_fuel_cell * 33.33), deficit_energy) 
                        storage -= h2_converted

                    else:

                        available_caverns = storage_caverns
                        available_tanks = storage_tanks

                        h2_to_convert = min(h2_needed_fuelCell, 
                            available_caverns * eff_storage_saltCaverns +
                            available_tanks * eff_storage_pressurisedTanks)
                        
                        proportion_caverns = available_caverns / storage if storage > 0 else 0
                        proportion_tanks = available_tanks / storage if storage > 0 else 0

                        h2_from_caverns = h2_to_convert * proportion_caverns / eff_storage_saltCaverns
                        h2_from_caverns = min(h2_from_caverns, available_caverns) 

                        h2_from_tanks = h2_to_convert * proportion_tanks / eff_storage_pressurisedTanks
                        h2_from_tanks = min(h2_from_tanks, available_tanks)

                        usable_caverns = h2_from_caverns * eff_storage_saltCaverns
                        usable_tanks = h2_from_tanks * eff_storage_pressurisedTanks
                        h2_converted = usable_caverns + usable_tanks

                        energy_recovered = min((h2_converted * eff_fuel_cell * 33.33), deficit_energy) 

                        storage_caverns -= h2_from_caverns
                        storage_tanks -= h2_from_tanks
                        h2_needed_storage = h2_from_caverns + h2_from_tanks

                        storage = storage_caverns + storage_tanks

                            

                    h2_total_conversion += h2_converted # Updates the value of the total of H2 converted
                    df.at[i, "H2_converted [kg]"] = h2_converted # Stores the value of H2 converted in the df
                    df.at[i, "Elec_from_H2 [kWh]"] = energy_recovered
                
                if (deficit_energy - energy_recovered) > 0 and energy_imported == 0 and balance_es > 0 and can_exchange: 
                        remaining_deficit = deficit_energy - energy_recovered
                        energy_imported_2 = min(balance_es, remaining_deficit)

                        deficit_energy = max(0, remaining_deficit - energy_imported_2)
                        energy_imported += energy_imported_2

                        
                df.at[i, "Elec_recovered [kWh]"] = energy_recovered + energy_imported

            
        storage_list.append(storage)  
        df.at[i, "Storage H2 [kg]"] = storage 

    # Final results
    df["Cost_H2_production [€]"] = df["Elec_used_for_H2 [kWh]"] * df["PT Marginal Cost [€]"] / 1000

    total_recovered = df["Elec_recovered [kWh]"].sum()
    total_cost_electricity_used = df["Cost_H2_production [€]"].sum()
    h2_total_production = df["H2_produced [kg]"].sum()

    flex_index = (total_recovered / total_deficits) * 100 if total_deficits > 0 else 0
    flex_index_H2 = (df["Elec_from_H2 [kWh]"].sum() / total_deficits) * 100

    lcoh = (capex_total + opex_total + total_cost_electricity_used ) / h2_total_production if h2_total_production > 0 else 0



    print(f"\n--- Simulation Results for {scenario} {year} ---")
    print(f"Total H2 produced: {h2_total_production:.2f} kg")
    print(f"Total H2 converted: {h2_total_conversion:.2f} kg")

    #print(f"Total Deficits: {h2_total_conversion:.2f} kg")
    #print(f"Deficits Covered: {h2_total_conversion:.2f} kg")
    print(f"Buying Threshold: {threshold_buying:.2f} €/MW")
    print(f"Selling Threshold: {threshold_selling:.2f} €/MW")
    print(f"CAPEX total {capex_total:.2f} €/MW")
    print(f"Total efficiency {eff_total_equipments*100:.2f} %")


    print(f"Grid Flexibility Index with imports and H2: {flex_index:.2f} %")
    print(f"Grid Flexibility Index with H2: {flex_index_H2:.2f} %")
    print(f"LCOH: {lcoh:.2f} €/kg")
    print(f"Capacity Fuel Cells: {cap_fuel_cell:.2f} MW")
    print(f"Capacity Storage: {cap_storage:.2f} MW")


    summary = {
        "Scenario": scenario,
        "Year": year,
        "Storage in Salt Caverns (%)": storage_ratio,
        "Storage in Pressurized Tanks (%)": (100-storage_ratio),
        "Buying Threshold": threshold_buying,
        "Selling Threshold": threshold_selling,
        "H2 Produced (kg)": h2_total_production,
        "H2 Converted (kg)": h2_total_conversion,
        "Energy Recovered (kWh)": total_recovered,
        "Electricity Cost [€]": total_cost_electricity_used,
        "Yearly CAPEX [€]": capex_total,
        "Yearly OPEX [€]": opex_total,
        "Flexibility Index (%)": flex_index,
        "Flexibility Index H2(%)": flex_index_H2,
        "LCOH (€/kg)": lcoh
    }

    return df, summary

results_simulation("DE", 2035, 100, 94)