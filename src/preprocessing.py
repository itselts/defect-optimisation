import pandas as pd
import matplotlib.pyplot as plt
import math
import datetime
from pathlib import Path
import os
import shutil
import argparse
from argparse_formatters import date_formatter, time_formatter
from points_curve import combined, plot_curve
from penalty import penalty
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient
import geopy.distance
import numpy as np

def build_cmd_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--request_ID', action='store', type=str, required=True)
    parser.add_argument('-n', action="store", type=int, required=True, help="Number of defects to optimise.")
    parser.add_argument("--day", type=int, action="store", required=True, help="The day number within the horizon.")
    parser.add_argument('--s_date', action='store', type=date_formatter, required=True, help='Starting date of the horizon in iso format (yyyy-mm-dd)')
    parser.add_argument('--s_time', action='store', type=time_formatter, default='00:00', help='Optimisation start time in %H:%M format (e.g 07:00)')

    args = parser.parse_args()

    return args


args = build_cmd_args()
request_ID = args.request_ID
n = args.n
day = args.day
start_datetime = datetime.datetime(args.s_date.year, args.s_date.month, args.s_date.day, args.s_time.hour, args.s_time.minute) + datetime.timedelta(days=day-1)
dow = start_datetime.strftime('%A')

path = "../data/"

files = ["v_GetOptimiseInputItems.parquet", "v_DomainValueDepot.parquet", "v_GetOptimiseInputCrews.parquet"] # Job list, depot list, crew list
dst_directory = path + request_ID # Local location for where ADLS files are saved to

disp_bar = f"{'-'*40}"
print(disp_bar)
print(f"{'Preprocessing...' : ^40}")

# CREATING THE NECESSARY FOLDER STRUCTURE 
outputs_dir = Path("../outputs")
results_dir = Path("../results")

# Remove any previous runs
if day == 1:
    if os.path.exists(outputs_dir):
        shutil.rmtree(outputs_dir) 
        shutil.rmtree(results_dir)
else:
    if os.path.exists("../outputs" + f"/day{day}"):
        shutil.rmtree(Path("../outputs" + f"/day{day}"))
        shutil.rmtree(Path("../results" + f"/day{day}"))

Path.mkdir(outputs_dir / f"day{day}" / "time_matrices", parents=True)
Path.mkdir(outputs_dir / f"day{day}" / "dist_matrices")
Path.mkdir(outputs_dir / f"day{day}" / "X_matrices")
Path.mkdir(results_dir / f"day{day}", parents=True)

# Reading in the jobs
if day == 1:
    all_tasks = pd.read_parquet(dst_directory + "/" + files[0]) # Reading in the extracted files from ADLS by extract.py
else:
    all_tasks = pd.read_parquet(dst_directory + "/" + f'{files[0].replace(".parquet", "")}_day{day}.parquet') # Reading in the new sample input by get_remaining.py

# Reading in depots 
depot_input = pd.read_parquet(dst_directory + "/" + files[1])
depot_input.to_excel(f'../outputs/day{day}/depot_input.xlsx', index=False)

# Reading in the crews and outputting a crew_input file for that day. Enumerating each truck, along with its crew type, depot location and start/end times.
crew_input = pd.read_parquet(dst_directory + "/" + files[2])
total_crews = 0
crew_dict = {'truck_num': [], 'crew_type': [], 'shift_code': [], 'start_depot': [], 'end_depot': [], 'crew_type_ID': [], 'crew_num': [], 'shift': [], 'start_time': [], 'end_time': []}

for i, row in crew_input.iterrows():
    for k in range(row[f'{dow}NumCrew']): # Number of crews depends on the day of week
        total_crews += 1
        crew_dict['truck_num'].append(total_crews)
        crew_dict['crew_type'].append(row['CrewTypeCode'])
        crew_dict['shift_code'].append(row["ShiftCode"])
        crew_dict['start_depot'].append(row['StartDepotCode'])
        crew_dict['end_depot'].append(row['EndDepotCode'])
        crew_dict['crew_type_ID'].append(row['CrewTypeID'])
        crew_dict['crew_num'].append(k+1)
        crew_dict['shift'].append(row['ShiftCode'])
        crew_dict['start_time'].append(row[f'{dow}StartTime'].time())
        crew_dict['end_time'].append(row[f'{dow}EndTime'].time())

pd.DataFrame.from_dict(crew_dict).to_excel(f'../outputs/day{day}/crew_input.xlsx', index=False) # Outputting the crew input for that day
pd.DataFrame.from_dict(crew_dict).to_excel(f'../results/day{day}/crew_input.xlsx', index=False)

plot_curve(day)

# Transforming the data (Setting the start day and time)
all_tasks = all_tasks[all_tasks.LongStart != ''] # Removing entries with no coordinates
all_tasks['Start datetime'] = start_datetime
all_tasks['Days until due'] = (all_tasks['Start datetime'] - all_tasks['DueDate']).dt.total_seconds() / (60*60*24)
all_tasks.loc[all_tasks['Days until due'].isnull(), 'Days until due'] = -180 # For rows with no due date, set the score to 250 (In effect 6 months due in the future)
all_tasks['Minutes until due'] = -all_tasks['Days until due'] * 24 * 60

# Points curve for each job (Based on due date then scaled by activity multiplier)
all_tasks['Points curve'] = all_tasks.apply(lambda row: combined(
    x = row['Days until due'], 
    growth = 1.25,
    due_score = 1000,
    minimum_score = 250,
    cycle_height1 = 500, 
    cycle_maximum1 = 1000,
    width1 = 10,
    cycle_height2 = 250, 
    cycle_maximum2 = 1000,
    width2 = 5,
    act_multi = 1)/2, axis=1)


all_tasks['Score'] = all_tasks.apply(lambda row: row['Points curve'] * float(row['ActivityMultipler']), axis=1)

# Penalty for going overdue
p = 1000 # Penalty of 1000
#all_tasks.dropna(axis=0, how='any', subset=["Days until due"], inplace=True)
all_tasks["Penalty"] = all_tasks.apply(lambda row: penalty(math.floor(-row["Days until due"]), p), axis=1)


# PROXIMITY SCORE
proximity_score_1 = []
proximity_score_2 = []
depot_coords = []
for i, row in depot_input.iterrows():
    depot_coords.append((float(row["Lat"]), float(row["Long"])))

for i, row in all_tasks.iterrows():
    coord_1 = (float(row["LatStart"]), float(row["LongStart"]))
    proximity_score_1.append(sum([1/geopy.distance.geodesic(coord_1, coord_2).km for coord_2 in depot_coords]) * 1000)
    proximity_score_2.append(sum([math.e**(-geopy.distance.geodesic(coord_1, coord_2).km*0.015) for coord_2 in depot_coords]))

all_tasks["Proximity Score"] = 100 * (np.array(proximity_score_2)/max(proximity_score_2))
all_tasks["Total Score"] = all_tasks["Proximity Score"] + all_tasks["Score"]
#print(depot_input)

# Getting the top n most important jobs by Score to optimise
all_tasks.sort_values('Total Score', ascending=False, inplace=True)  
all_tasks = all_tasks.reset_index(drop=True)


sample_tasks = all_tasks.head(n)
sample_tasks.to_excel(f"../outputs/day{day}/sample_data.xlsx", index=True)


# Plot the subset. Depots in red, jobs in blue
plt.figure(1)
for i, row in depot_input.iterrows(): 
    plt.scatter(float(row["Long"]), float(row["Lat"]), color='r')
    plt.text(float(row["Long"]), float(row["Lat"]), row["DepotName"])

for i, row in sample_tasks.iterrows():
    plt.scatter(x=float(row['LongStart']), y=float(row['LatStart']), color='b')

plt.savefig(f'../outputs/day{day}/sample_plot.png')


plt.figure(2)
for i, row in depot_input.iterrows(): 
    plt.scatter(float(row["Long"]), float(row["Lat"]), color='r')
    plt.text(float(row["Long"]), float(row["Lat"]), row["DepotName"])

for i, row in all_tasks.iterrows():
    plt.scatter(x=float(row['LongStart']), y=float(row['LatStart']), color='b')

plt.savefig(f'../outputs/day{day}/all_plot.png')


print(f"Preprocessing for day {day}: {len(all_tasks)} total jobs and {len(depot_input)} depots. Top {n} jobs selected.")