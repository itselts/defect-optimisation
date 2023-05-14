import pandas as pd
import os
import re
import numpy as np
import datetime
import argparse
from argparse_formatters import date_formatter, time_formatter
from tours import out, get_tours

def build_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request_ID', action='store', type=str, required=True)
    parser.add_argument("--day", type=int, action="store", required=True, help="The day number within the horizon.")
    parser.add_argument('--s_date', action='store', type=date_formatter, required=True, help='Starting date of the horizon in iso format (yyyy-mm-dd)')
    parser.add_argument('--s_time', action='store', type=time_formatter, default='00:00', help='Shift start time in %H:%M format (e.g 07:00)')

    args = parser.parse_args()
    return args


args = build_cmd_args()
request_ID = args.request_ID
day = args.day

start_datetime = datetime.datetime(args.s_date.year, args.s_date.month, args.s_date.day, args.s_time.hour, args.s_time.minute) 

disp_bar = f"{'-'*40}"
print(disp_bar)
print(f"{'Postprocessing...' : ^40}")

# Reading in the jobs, depots and crews
sample_data = pd.read_excel(f"../outputs/day{day}/sample_data.xlsx")
depot_input = pd.read_parquet(f"../data/{request_ID}/v_DomainValueDepot.parquet")
crew_input = pd.read_excel(f'../outputs/day{day}/crew_input.xlsx', sheet_name="Sheet1")

time_matrix_dict = {}
dist_matrix_dict = {}
depots = set()

for depot in depot_input["DepotName"]:
    depots.add(depot)

for truck_num in crew_input["truck_num"]:
    time_matrix_dict[truck_num] = pd.read_excel(f"../outputs/day{day}/time_matrices/{truck_num}_time_matrix.xlsx", header=None).to_numpy()
    dist_matrix_dict[truck_num] = pd.read_excel(f"../outputs/day{day}/dist_matrices/{truck_num}_dist_matrix.xlsx", header=None).to_numpy()

m = len(crew_input) # total number of trucks


##### VEHICLE RESULTS #####
visited = set() # Getting the list of visited points by iterating through all vehicle tours
vehicles = [] # The results summary for each vehicle. Each element is a row in the resulting data frame

# Processing X matrices to get vehicle resutls
for file in os.listdir(f"../outputs/day{day}/X_matrices"):
    vehicle_number = int(re.findall('\d+', file)[0])
    start_depot = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'start_depot'].to_string(index=False)
    end_depot = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'end_depot'].to_string(index=False)
    crew_type_ID = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'crew_type_ID'].to_string(index=False)
    crew_type = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'crew_type'].to_string(index=False)
    shift_code = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'shift_code'].to_string(index=False)
    crew_num = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'crew_num'].to_string(index=False)
    start_time = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'start_time'].to_string(index=False)
    end_time = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'end_time'].to_string(index=False)

    X_df = pd.read_csv(f"../outputs/day{day}/X_matrices/{file}")
    X_matrix = X_df.to_numpy()

    # Check if the vehicle is used
    if round(np.sum(X_matrix)) == 0:
        vehicles.append({'vehicle_number': vehicle_number, 'crew_type_ID': crew_type_ID, 'crew_type': crew_type, 'shift_code': shift_code, 
                         'crew_num': crew_num, 'start_depot': start_depot, 'end_depot': end_depot, 'start_time': start_time, 'end_time': end_time, 
                         'number_of_jobs': 0, 'tour': 0, 'distance_travelled': 0, 'total_time': 0, 'total_travel_time': 0, 'total_job_time': 0})
        continue

    tour = get_tours(X_df) # Get the tours (Based on the ordering of sample_data)
    visited.update(tour)

    # Getting the travel time and travel distance for each truck
    time_matrix = time_matrix_dict[vehicle_number]
    dist_matrix = dist_matrix_dict[vehicle_number]
    travel_time = np.sum(np.multiply(X_matrix, time_matrix))
    travel_dist = np.sum(np.multiply(X_matrix, dist_matrix))


    # Getting the job time for each truck
    tmp = tour.copy()
    del tmp[0]
    job_time = sum(sample_data.loc[[x-1 for x in tmp], "EstDuration"])

    vehicles.append({'vehicle_number': vehicle_number, 'crew_type_ID': crew_type_ID, 'crew_type': crew_type, 'shift_code': shift_code,
                    'crew_num': crew_num, 'start_depot': start_depot, 'end_depot': end_depot, 'start_time': start_time, 'end_time': end_time, 
                     'number_of_jobs': len(tour)-1, 'tour': tour, 'distance_travelled': travel_dist, 'total_time': travel_time+job_time, 
                     'total_travel_time': travel_time, 'total_job_time': job_time})

vehicles = pd.DataFrame(vehicles)
vehicles.to_excel(f"../results/day{day}/vehicle_results.xlsx", index=False)

##### ITEM RESULTS #####
items = sample_data[["ItemType", "ItemIdentifier", "LatStart", "LongStart", "Score", "ActivityNameCode",  "EstQty", "EstDuration", "CrewType_FKs", "ShiftCode", "DueDate"]]
items.index += 1 # Index 1 is job 1

# Which crew did which job
opt_shift = []
crew_type_completed = []
crew_num_completed = []
truck_num_completed = []
shift_code_completed = []

for i, row in items.iterrows():
    included = False
    for j, vehicle in vehicles.iterrows(): # Looking for which vehicle did that job
        if not vehicle["tour"]: # Vehicle is not used
            continue
        if i in vehicle["tour"]: # If that job index is in the tour of that vehicle
            opt_shift.append(datetime.datetime(start_datetime.year, start_datetime.month, start_datetime.day, int(vehicle["start_time"][:2]), int(vehicle["start_time"][3:5])) )
            truck_num_completed.append(vehicle["vehicle_number"])
            crew_type_completed.append(vehicle["crew_type"])
            crew_num_completed.append(vehicle["crew_num"])
            shift_code_completed.append(vehicle["shift_code"])
            included = True
            break
    if not included: # Job is not completed by any crew 
        opt_shift.append(None)
        truck_num_completed.append(None)
        crew_num_completed.append(None)
        crew_type_completed.append(None)
        shift_code_completed.append(None)

pd.options.mode.chained_assignment = None # Assigned new column to list induces warnings. Surpress them
items["OptShift"] = opt_shift
items["Assigned truck num"] = truck_num_completed
items["Assigned crew type"] = crew_type_completed
items["Assigned crew num"] = crew_num_completed
items["Assigned shift code"] = shift_code_completed

# Completion times
# Gurobi optimisation assigns not completed jobs a dummy value for its completion times. Therefore if it is not in visited, it is not completed, and time is set to 0.
times = list(pd.read_csv(f"../results/day{day}/job_completion_times.csv")["Column1"])
for job in range(1, len(times)+1): # Position 0 is the depot, so job indexes go from 1. 
    if job not in visited:
        times[job-1] = None # Times do not include the depot, so index is shifted back by 1.

items["Completion from start (min)"] = times

completion_time = []
for i, row in items.iterrows(): # Completion times depend on when the assigned crew started their shift
    if pd.isnull(row["OptShift"]):
        completion_time.append(None)
    else:
        completion_time.append(datetime.timedelta(minutes=row["Completion from start (min)"]) + start_datetime)
items["Estimated Completion Time"] = completion_time

items.to_excel(f"../results/day{day}/item_results.xlsx")


##### VISITED SUMMARY #####
count = len(visited)-1 # -1 because it includes index 0 (Start depot)
if count == -1:
    count = 0
pd.DataFrame([{'count': count, 'visited': visited}]).to_excel(f"../results/day{day}/visited_summary.xlsx", index=False)

print(f"Results processed. Item results, vehicle results, and item summary saved to local results folder.")