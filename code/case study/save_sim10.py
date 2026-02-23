import pandas as pd

from sim10_caseStudy import results_simulation 

scenarios = ["NT", "GA", "DE"]
years = [2030, 2035, 2040, 2050]
storage_cap = [1000, 3500, 6000]
threshold_excel_name = "thresholds_sim11"

summaries = []

for scenario in scenarios:
    print(f"\n--- Processing scenario: {scenario} ---")

    df_thresholds = pd.read_excel(f"{threshold_excel_name}.xlsx", f"{scenario}")


    for _, row in df_thresholds.iterrows():
        year = int(row["Years"])

        thresholds = [
            row["Avg Electricity Cost [€/MWh]"],
            row["Avg Electricity Cost During Deficits [€/MWh]"],
            row["Manual Threshold [€/MWh]"]
        ]
        threshold_labels = ["Average Cost", "Deficit Cost", "Manual Threshold"]

        for threshold, label in zip(thresholds, threshold_labels):
            for cap in storage_cap:
                print(f"Running: {scenario} {year} | Threshold: {label} ({threshold:.2f}) | Capacity: {cap} tons")

                try:
                    df, summary = results_simulation(scenario, year, cap, threshold)
                    summary["Scenario"] = scenario
                    summary["Year"] = year
                    summary["Threshold Type"] = label
                    summary["Threshold Value [€/MWh]"] = threshold
                    summaries.append(summary)
                except Exception as e:
                    print(f"Erro em {scenario}-{year}-{threshold} ({cap}%): {e}")

df_summary = pd.DataFrame(summaries)
df_summary.to_excel("sim12_results2.xlsx", sheet_name="Case Study Results", index=False)
print("\nResultados guardados em 'sim12_results2.xlsx'")
