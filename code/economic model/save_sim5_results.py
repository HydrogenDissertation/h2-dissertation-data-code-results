import pandas as pd
from sim5_ENTSOEValues import results_simulation

# List of all scenarios, years, and storage percentages to test
scenarios = ["NT", "GA", "DE"]
years = [2030, 2035, 2040, 2050]
storage_ratios = [100, 60, 50, 0]

summaries = []

for scenario in scenarios:
    for year in years:
        if scenario == "NT" and year == 2035:
            continue  # Skip NT in 2035 if you don't have it this year
        if scenario == "NT" and year == 2050:
            continue  # Skip NT in 2050 if you don't have it this year
        if scenario == "GA" and year == 2030:
            continue  # Skip GA in 2030 if you don't have it this year
        if scenario == "DE" and year == 2030:
            continue  # Skip DE in 2030 if you don't have it this year
        for ratio in storage_ratios:
            print(f"Running: {scenario} {year} ({ratio}% Salt Caverns)")
            df, summary = results_simulation(scenario, year, ratio)
            summaries.append(summary)


df_summary = pd.DataFrame(summaries)

df_summary.to_excel("sim5_results.xlsx", sheet_name = "Results", index=False)
print("\nResultados guardados em 'sim_results.xlsx'")
