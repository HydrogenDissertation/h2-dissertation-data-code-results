import pandas as pd
from sim4_DeficitImportOrH2 import worst_H2_deficit_sequence

# Parameters you want to test
scenarios = ["NT", "GA", "DE"]
years = [2030, 2035, 2040, 2050]
#threshold_sheet_name = "Threshold"
threshold_sheet_name = "Sim8 Thresholds"

# List to save summaries
summaries = []

# Loop through all cases
for scenario in scenarios:
    print(f"\n--- Processing thresholds for scenario: {scenario} ---")
    
    # Load the 'Threshold' sheet from the file corresponding to the scenario
    df_thresholds = pd.read_excel(f"{scenario}.xlsx", threshold_sheet_name)
    #get_data(threshold_sheet_name, f"{scenario}.xlsx","Years")

    for _, row in df_thresholds.iterrows():
        year = int(row["Years"])

        # List of the three thresholds per year (you can add others if you want)
        thresholds = [
            row["Avg Electricity Cost [€/MWh]"],
            row["Avg Electricity Cost During Deficits [€/MWh]"],
            row["Manual Threshold [€/MWh]"]
        ]

        threshold_labels = ["Average Cost", "Deficit Cost", "Manual Threshold"]

        for threshold, label in zip(thresholds, threshold_labels):
            print(f"Running: {scenario} {year} | {label}: {threshold:.2f} €/MWh")
            df, summary = worst_H2_deficit_sequence(scenario, year, threshold)
            summary["Threshold Type"] = label
            summary["Threshold Value"] = threshold
            summaries.append(summary)




# Save the results in an Excel file
df_summary = pd.DataFrame(summaries)
df_summary.to_excel("sim4_results.xlsx", sheet_name="Thresholds", index=False)
#df_summary.to_excel("sim7_thresholds_results.xlsx", sheet_name="Thresholds", index=False)
print("\nResultados guardados em 'sim4_results.xlsx'")
