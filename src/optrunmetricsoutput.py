import pandas as pd
import datetime
import argparse
from argparse_formatters import date_formatter, time_formatter

def build_cmd_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--request_ID', action='store', type=str, required=True)
    parser.add_argument("--day", type=int, action="store", required=True, help="The day number within the horizon.")
    parser.add_argument('--s_date', action='store', type=date_formatter, required=True, help='Starting date of the horizon in iso format (yyyy-mm-dd)')

    args = parser.parse_args()
    return args

# Parameters
args = build_cmd_args()
request_ID = args.request_ID
day = args.day
start_date = datetime.datetime(args.s_date.year, args.s_date.month, args.s_date.day) + datetime.timedelta(days=day - 1)

print("Processing optrunmetricsoutput...", end="")

# Reading in the full dataset
if day == 1:
    all_tasks = pd.read_parquet(f"../data/{request_ID}/v_GetOptimiseInputItems.parquet")
else:
    all_tasks = pd.read_parquet(f"../data/{request_ID}/v_GetOptimiseInputItems_day{day}.parquet")

n = len(all_tasks)
completed_count = int(pd.read_excel(f"../results/day{day}/visited_summary.xlsx")["count"].to_string(index=False))

# Reading in optimisation results
item_results = pd.read_excel(f"../results/day{day}/item_results.xlsx", index_col=0)

# Processing which jobs are missed/gone overdue
missed = set() # This is the set of jobs that aren't done.
overdue = set() # This is the set of jobs that go overdue, but are still completed on the day.

for i, row in item_results.iterrows():
    if pd.isnull(row["OptShift"]):
        missed.add(i)
    elif row['DueDate'].day == start_date.day and row['Estimated Completion Time'] > row['DueDate']:
        overdue.add(i)


# Objective & Gap results 
obj_gap = pd.read_csv(f"../results/day{day}/objective_gap.csv")

# Total distance travelled for the day
vehicle_results = pd.read_excel(f"../results/day{day}/vehicle_results.xlsx")
total_dist = sum(vehicle_results["distance_travelled"])

# OptRunMetricsOutput table
df = {}

df['ModelIdentifier'] = ['v1.1.0']
df['ResultStatusCode'] = [obj_gap.loc[0,"Column1"]]

if [obj_gap.loc[0,"Column1"]] == ["FEASIBLE_POINT"]:
    df['SolutionFound'] = True
else:
    df['SolutionFound'] = False

df['TotalJobsCompleted'] = [completed_count]
df['TotalMissedJobs'] = [n-completed_count]
df['TotalPointsScore'] = [obj_gap.loc[1,"Column1"]]
df['TotalDistanceDriven'] = [total_dist]
df['RunTime'] = [obj_gap.loc[3,"Column1"]]
df['Gap'] = [obj_gap.loc[2,"Column1"]]

df = pd.DataFrame.from_dict(df)
df.to_excel(f"../results/day{day}/optrunmetricsoutput.xlsx", index=False)
df.to_parquet(f"../results/day{day}/optrunmetricsoutput.parquet", index=False)

print("ok")