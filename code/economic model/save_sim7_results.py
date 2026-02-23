import pandas as pd
from sim7_ProductionAndDeficitCoverageThresholds import results_simulation  

scenarios = ["NT", "GA", "DE"]
years = [2030, 2035, 2040, 2050]
storage_ratios = [100, 60, 50, 0]
threshold_sheet_name = "Sim7 Thresholds"

summaries = []

for scenario in scenarios:
    print(f"\n--- Processing scenario: {scenario} ---")

    df_thresholds = pd.read_excel(f"{scenario}.xlsx", threshold_sheet_name)

    for _, row in df_thresholds.iterrows():
        year = int(row["Years"])

        thresholds = [
            row["Avg Electricity Cost [€/MWh]"],
            row["Avg Electricity Cost During Deficits [€/MWh]"],
            row["Manual Threshold [€/MWh]"]
        ]
        threshold_labels = ["Average Cost", "Deficit Cost", "Manual Threshold"]

        for threshold, label in zip(thresholds, threshold_labels):
            for ratio in storage_ratios:
                print(f"Running: {scenario} {year} | Threshold: {label} ({threshold:.2f}) | Storage: {ratio}% Salt Caverns")

                try:
                    df, summary = results_simulation(scenario, year, ratio, threshold)
                    summary["Scenario"] = scenario
                    summary["Year"] = year
                    summary["Storage in Salt Caverns (%)"] = ratio
                    summary["Storage in Pressurized Tanks (%)"] = 100 - ratio
                    summary["Threshold Type"] = label
                    summary["Threshold Value"] = threshold
                    summaries.append(summary)
                except Exception as e:
                    print(f"Erro em {scenario}-{year}-{threshold} ({ratio}%): {e}")

df_summary = pd.DataFrame(summaries)
df_summary.to_excel("sim7_results.xlsx", sheet_name="Results", index=False)
print("\nResultados guardados em 'sim7_results.xlsx'")
