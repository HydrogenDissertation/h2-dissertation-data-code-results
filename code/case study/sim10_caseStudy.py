# SIMULATION 10 - CASE STUDY
#
# This final case study evaluates large-scale salt cavern storage.
# It integrates production, storage, reconversion, and H2 selling,
# calculating profitability, payback periods, and system flexibility.

import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extract_data import get_data, df_electrolyzers, df_fuel_cells, df_compressors_saltCaverns  

def results_simulation(scenario, year, storage_cap, threshold_selling):

    #################################################################################
    # DATAFRAMES INITIALIZATION

    # HOURLY DATA DF
    year_string = str(year)
    df = get_data(year_string, f"{scenario}.xlsx", "Index")

    # H2 SELLING PRICES DF
    h2_prices_df = get_data("Prices", "H2_prices.xlsx", "Year")

    # CAPACITY DF
    if scenario == "NT":
        installed_cap_df = get_data(scenario, "data_caseStudy.xlsx", "Years")
        exchange_cap_df = get_data(scenario, "Exchange_Capacity.xlsx", "Years")
    elif scenario == "DE":
        installed_cap_df = get_data(scenario, "data_caseStudy.xlsx", "Years")
        exchange_cap_df = get_data(scenario, "Exchange_Capacity.xlsx", "Years")
    elif scenario == "GA":
        installed_cap_df = get_data(scenario, "data_caseStudy.xlsx", "Years")
        exchange_cap_df = get_data(scenario, "Exchange_Capacity.xlsx", "Years")
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    df["Date/Hour"] = pd.to_datetime(
        df["Date/Hour"].str[:5] + str(year) + " " + df["Date/Hour"].str[5:], 
        format="%d%b%Y %H:%M"
    )

    df["Hour"] = df["Date/Hour"].dt.hour
    df["In_Selling_Window"] = df["Hour"].between(8, 17) # 10 hours working

    df["Is_Sunday"] = df["Date/Hour"].dt.weekday == 6  # 6 = Sunday


    # STORAGE DF
    if storage_cap <= 3000:
        df_storage = get_data("Salt Caverns 123", "data_caseStudy.xlsx", "Years")
    elif storage_cap > 3000:
        df_storage = get_data("Salt Caverns 456", "data_caseStudy.xlsx", "Years")
    else:
        raise ValueError("Could not find dataframe")
    
    # COMPRESSORS DF    
    #################################################################################

    h2_sellingPrice = h2_prices_df.loc[year, "H2 Cost [€/kg]"]

    #################################################################################
    # TECHNICAL PARAMETERS
    
    # Electrolyzers
    eff_electrolyzer = df_electrolyzers.loc[year, "Efficiency (kWh/kgH2)"]
    capex_electrolyzer = df_electrolyzers.loc[year, "CAPEX (€/kW)"]
    opex_electrolyzer = df_electrolyzers.loc[year, "OPEX yearly (€/kW/year)"]
    lifetime_electrolyzer = df_electrolyzers.loc[year, "Lifetime (hours)"]
    capex_anual_electrolyzer = capex_electrolyzer / lifetime_electrolyzer

    cap_electrolyzer = installed_cap_df.loc[year, "Electrolyzers (MW)"]

    # Compressors
    eff_compressors = df_compressors_saltCaverns.loc[year, "Efficiency (%)"]
    capex_compressors = df_compressors_saltCaverns.loc[year, "CAPEX (€/kW)"]
    opex_compressors = df_compressors_saltCaverns.loc[year, "OPEX yearly (€/kW/year)"]
    lifetime_compressors = df_compressors_saltCaverns.loc[year, "Lifetime (hours)"]
    comsumption_compressors = df_compressors_saltCaverns.loc[year, "Consumption (kWh/kgH2)"]
    capex_anual_compressors = capex_compressors / lifetime_compressors

    cap_compressors = (cap_electrolyzer * 1000) / eff_electrolyzer * comsumption_compressors


    # Salt Caverns
    eff_storage = df_storage.loc[year, "Efficiency (%)"]
    capex_storage = df_storage.loc[year, "CAPEX (€/kgH2)"]
    opex_storage = df_storage.loc[year, "OPEX yearly (€/kW/year)"]
    lifetime_storage = df_storage.loc[year, "Lifetime (hours)"]
    capex_anual_storage = capex_storage / lifetime_storage

    # Fuel Cells

    cap_fuel_cell = installed_cap_df.loc[year, "Fuel Cells (MW)"]

    eff_fuel_cell = df_fuel_cells.loc[year, "Efficiency (%)"]
    capex_fuel_cell = df_fuel_cells.loc[year, "CAPEX (€/kW)"]
    opex_fuel_cell = df_fuel_cells.loc[year, "OPEX yearly (€/kW/year)"]
    lifetime_fuel_cell = df_fuel_cells.loc[year, "Lifetime (hours)"]
    capex_anual_fuel_cell = capex_fuel_cell / lifetime_fuel_cell

    # Exchange

    cap_exchange = exchange_cap_df.loc[year, "Capacity (MWH2)"]
    max_export_cap = cap_exchange * 0.7
    cost_export = 0.2 # 0.2€/kg
    export_loss_rate = 0.05  # 5% de perdas


    #################################################################################
    # INITIALIZATION OF VARIABLES
    
    cap_storage_kg = storage_cap * 1000 # storage_cap is in tons, 1 ton = 1 000 kg 
    current_storage = 0  # H2 in storage at each hour (kg)
    storage_list = []  # to track storage levels hour by hour

    current_H2stored = 0

    h2_total_production = 0
    h2_total_conversion = 0
    electricity_used = 0
    total_deficits = 0

    total_revenue = 0
    revenue = 0

    flag_sell_H2 = False
    start_selling = 0.8 * cap_storage_kg
    stop_selling = 0.2 * cap_storage_kg
    total_h2_sold = 0.0

    capex_total = ( 
        capex_anual_electrolyzer * cap_electrolyzer * 1000 + 
        capex_anual_compressors * cap_compressors + 
        capex_anual_storage * cap_storage_kg +
        capex_anual_fuel_cell * cap_fuel_cell * 1000 
    )
    
    opex_total = ( 
        opex_electrolyzer * cap_electrolyzer * 1000 + 
        opex_compressors * cap_compressors + 
        opex_storage * cap_storage_kg +
        opex_fuel_cell * cap_fuel_cell * 1000 
    )
    
    eff_total_equipments = ( 
        eff_fuel_cell * 
        eff_storage * 
        eff_compressors * 
        ( 
            33.33 /
            eff_electrolyzer 
        )
    )

    threshold_buying = threshold_selling * eff_total_equipments

    #################################################################################
    # COLUMNS FOR OUTPUTS

    df["H2_produced [kg]"] = 0.0
    df["H2_converted [kg]"] = 0.0
    df["Storage H2 [kg]"] = 0.0
    df["Elec_used_for_H2 [kWh]"] = 0.0
    df["Elec_from_H2 [kWh]"] = 0.0
    df["Elec_recovered [kWh]"] = 0.0
    df["Cost_H2_production [€]"] = 0.0
    df["Cost_H2_conversion [€]"] = 0.0

    df["H2_sold [kg]"] = 0.0
    df["Cost_H2_export [€]"] = 0.0

    df["Elec_used_for_H2_sold [kWh]"] = 0.0
    df["Revenue_H2_sold [€]"] = 0.0

    df["Elec_used_total [kWh]"] = 0.0
    df["Cost_H2_production_with_selling [€]"] = 0.0
    df["H2_produced_P2G2P [kg]"] = 0.0

    #################################################################################


    for i, row in df.iterrows(): # Iterates each row of the df, i is the index, the row contains the info about balance, cost, etc

        balance_pt = row["PT Balance [MW]"] * 1000 # Stores the current balance value
        balance_es = row["ES Balance [MW]"] * 1000

        es_electricityCost = row["ES Marginal Cost [€]"]
        pt_electricityCost = row["PT Marginal Cost [€]"]

        # Checks the difference between the Portuguese electricity cost and the Spanish electricity cost
        if pt_electricityCost > 0:
            price_diff = abs(pt_electricityCost - es_electricityCost) / pt_electricityCost 
        elif es_electricityCost > 0:
            price_diff = abs( es_electricityCost - pt_electricityCost ) / es_electricityCost 
        else:
            price_diff = 0

        # Is exchange of electricity allowed?
        if price_diff > 0.2:
            can_exchange = False
        else:
            can_exchange = True

        ###########
        # SURPLUS #
        ###########
        if balance_pt >= 1: # Surplus of electricity → produce and store H2

            if pt_electricityCost <= threshold_buying: # If the price of electricity is lower then the buying threshold we can produce H2

                if balance_es < -1 and can_exchange: # ES is in deficit, export electricity
                    max_export = min(balance_pt, abs(balance_es))  
                    balance_pt -= max_export  # Updates the current balance after export
                    balance_es += max_export  # Updates ES value

                if balance_pt >= 1: # There is still a surplus of electricity after exportation
                    electricity_available = balance_pt
                    electricity_used = 0
                    electricity_toSellH2 = 0
                    h2_produced = 0
                    h2_toSell = 0
                        
                    if current_storage < cap_storage_kg: # There is storage place available

                        eff_total = eff_electrolyzer + comsumption_compressors
                        
                        h2_produced = electricity_available / eff_total # em kg

                        if current_storage + h2_produced > cap_storage_kg:
                            h2_produced = cap_storage_kg - current_storage
                            electricity_used = ( h2_produced / eff_compressors ) * eff_total
                        else:
                            electricity_used = electricity_available

                
                        current_storage += h2_produced # Updates the current stored H2 value
                        df.at[i, "H2_produced_P2G2P [kg]"] = h2_produced # Stores the value of H2 produced in the df
                        df.at[i, "Elec_used_for_H2 [kWh]"] = electricity_used
                    

                    df.at[i, "Elec_used_total [kWh]"] = electricity_toSellH2 + electricity_used
                    df.at[i, "H2_produced [kg]"] = h2_produced

            if current_storage >= start_selling and flag_sell_H2 == False:
                flag_sell_H2 = True
            


        ###########
        # DEFICIT #
        ###########
        else: # Deficit → convert H2 to electricity

            if pt_electricityCost >= threshold_selling: #  If the price of electricity is higher then the seeling threshold we use H2

                deficit_energy = abs(balance_pt)  # turns the negative value into positive in kW
                total_deficits += deficit_energy # kW
                energy_imported = 0
                energy_recovered = 0

                # Choose if there is going to be an import or H2 reconversion
                if es_electricityCost < threshold_buying:
                    if balance_es <= 0 or not can_exchange:
                        energy_imported = 0
                    else:
                        energy_imported = min(balance_es, deficit_energy)
                        if deficit_energy - energy_imported > 0:
                            deficit_energy = deficit_energy - energy_imported
                        else:
                            deficit_energy = 0
                
                energy_imported = max(0, energy_imported)
                
                if deficit_energy > 0: # If either the import was not enough to cover the deficit or there was no import, use H2

                    if current_storage > 0: # If there is H2 stored to cover the deficit

                        h2_needed_fuelCell = (deficit_energy) / (eff_fuel_cell * 33.33)  # Calculates how much H2 is need to cover the deficit using LHV conversion
                                        
                        
                        h2_needed_storage = h2_needed_fuelCell / eff_storage

                        h2_converted = min(current_storage, h2_needed_storage)

                        energy_recovered = min((h2_converted * eff_storage * eff_fuel_cell * 33.33), deficit_energy)# em kW
                            
                        
                        current_storage -= h2_converted # Updates the stored value
                        

                        h2_total_conversion += h2_converted # Updates the value of the total of H2 converted
                        df.at[i, "H2_converted [kg]"] = h2_converted # Stores the value of H2 converted in the df
                        df.at[i, "Elec_from_H2 [kWh]"] = energy_recovered
                    
                    if (deficit_energy - energy_recovered) > 0 and energy_imported == 0 and balance_es > 0 and can_exchange:   
                            remaining_deficit = deficit_energy - energy_recovered
                            energy_imported_2 = min(balance_es, remaining_deficit)

                            deficit_energy = max(0, remaining_deficit - energy_imported_2)
                            energy_imported += energy_imported_2


                if (current_storage <= stop_selling) and (flag_sell_H2 is True) : # Limit was reached, no more selling until 80% full
                    flag_sell_H2 = False
                df.at[i, "Elec_recovered [kWh]"] = energy_recovered + energy_imported

        ##############
        # SELLING H2 #
        ##############
        if ((current_storage >= stop_selling) and (flag_sell_H2 == True)  and (not df.at[i, "Is_Sunday"]) ):

            if df.at[i, "In_Selling_Window"]: # Can we sell H2 at this hour?
                h2_available_for_sale  = min(((max_export_cap * 1000) /33.3), (current_storage - stop_selling)) # Either sell the max of exchange capacity or until it reaches the minimum selling point
                
                h2_toSell = h2_available_for_sale * (1 - export_loss_rate)
                cost_H2_toSell = h2_toSell * cost_export
                
                revenue = h2_toSell * h2_sellingPrice - cost_H2_toSell
                total_revenue += revenue

                current_storage -= h2_available_for_sale 
                total_h2_sold += h2_toSell
                df.at[i, "H2_sold [kg]"] = h2_toSell
                df.at[i, "Cost_H2_export [€]"] = cost_H2_toSell
                df.at[i, "Revenue_H2_sold [€]"] = revenue

            if current_storage <= stop_selling: # Limit was reached, no more selling until 80% full
                flag_sell_H2 = False
        
        storage_list.append(current_storage)  
        df.at[i, "Storage H2 [kg]"] = current_storage 

    # Final results
    df["Cost_H2_production [€]"] = df["Elec_used_for_H2 [kWh]"] * df["PT Marginal Cost [€]"] / 1000

    df["Cost_H2_production_with_selling [€]"] = df["Elec_used_total [kWh]"] * df["PT Marginal Cost [€]"] / 1000

    total_recovered = df["Elec_recovered [kWh]"].sum()
    total_cost_electricity_used = df["Cost_H2_production [€]"].sum()

    electricity_cost_total = df["Cost_H2_production_with_selling [€]"].sum()

    h2_total_production = df["H2_produced [kg]"].sum()
    h2_total_production_P2G2P = df["H2_produced_P2G2P [kg]"].sum()

    flex_index = (total_recovered / total_deficits) * 100 if total_deficits > 0 else 0
    flex_index_H2 = (df["Elec_from_H2 [kWh]"].sum() / total_deficits) * 100

    total_export_cost = df["Cost_H2_export [€]"].sum()
    profit = total_revenue - (capex_total + opex_total + total_cost_electricity_used + total_export_cost)

    lcoh_P2G2P = (capex_total + opex_total + total_cost_electricity_used ) / h2_total_production_P2G2P if h2_total_production_P2G2P > 0 else 0

    lcoh_standard = (capex_total + opex_total + total_cost_electricity_used ) / h2_total_production if h2_total_production > 0 else 0

    lcoh_net = (capex_total + opex_total + total_cost_electricity_used - total_revenue) / h2_total_production if h2_total_production > 0 else 0

    payback_years = (capex_storage * cap_storage_kg) / total_revenue if total_revenue > 0 else float('inf')
    
    total_costs = capex_total + opex_total + electricity_cost_total
    payback_system = total_costs / total_revenue if total_revenue > 0 else float("inf")

    storage_utilization = sum(storage_list) / (cap_storage_kg * len(storage_list)) * 100

    cave_cost = capex_storage * cap_storage_kg

    if lcoh_net < 0: lcoh_net = 0

    print(f"\n--- Simulation Results for {scenario} {year} ---")
    print("\n")
    print(f"Total H2 produced: {h2_total_production:.2f} kg")
    print(f"Total H2 converted: {h2_total_conversion:.2f} kg")
    print(f"Total H2 sold: {total_h2_sold:.2f} kg")
    print("\n")
    #print(f"Total Deficits: {h2_total_conversion:.2f} kg")
    #print(f"Deficits Covered: {h2_total_conversion:.2f} kg")
    print(f"Buying Threshold: {threshold_buying:.2f} €/MW")
    print(f"Selling Threshold: {threshold_selling:.2f} €/MW")
    #print(f"CAPEX total {capex_total:.2f} €/year")
    #print(f"Total efficiency {eff_total_equipments*100:.2f} %")
    print(f"Grid Flexibility Index with imports and H2: {flex_index:.2f} %")
    print(f"Grid Flexibility Index with H2: {flex_index_H2:.2f} %")
    print("\n")

    print(f"LCOH P2G2P: {lcoh_P2G2P:.2f} €/kg")
    print(f"LCOH Standard: {lcoh_standard:.2f} €/kg")
    print(f"LCOH Adjusted: {lcoh_net:.2f} €/kg")
    print("\n")

    print(f"H2 Selling Price: {h2_sellingPrice:.2f}€")
    print(f"Cave Cost: {cave_cost:.2f}€")
    print(f"Revenue H2 Sold: {total_revenue:.2f}€")
    print(f"Profit: {profit:.2f}€")
    print("\n")

    print(f"Payback Years Salt Cavern: {payback_years:.2f} years")
    print(f"Payback Years Full System: {payback_system:.2f} years")
    print(f"Storage Utilization: {storage_utilization:.2f} %")



    summary = {
        "Scenario": scenario,
        "Year": year,

        "Buying Threshold": threshold_buying,
        "Selling Threshold": threshold_selling,
        "Cave Capacity (ton)": storage_cap,

        "H2 Produced (kg)": h2_total_production,
        "H2 Converted (kg)": h2_total_conversion,
        "H2 Sold (kg)": total_h2_sold,

        "Energy Recovered (kWh)": total_recovered,
        "Electricity Cost [€]": total_cost_electricity_used,

        "Revenue H2 Sold [€]": total_revenue,
        "Profit [€]": profit,

        "Cave Cost [€]": cave_cost,
        "H2 Selling Price [€/kg]": h2_sellingPrice,
        "Payback Salt Cavern (years)": payback_years,
        "Payback Full System (years)": payback_system,
        "Storage Utilization (%)": storage_utilization,

        "Flexibility Index (%)": flex_index,
        "Flexibility Index H2(%)": flex_index_H2,

        "LCOH P2G2P (€/kg)": lcoh_P2G2P,
        "LCOH Standard (€/kg)": lcoh_standard,
        "LCOH Adjusted (€/kg)": lcoh_net

    }

    return df, summary

#results_simulation("DE", 2050, 1000, 55)