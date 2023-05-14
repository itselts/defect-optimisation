import argparse
import pandas as pd
import numpy as np
import datetime
import re
from argparse_formatters import date_formatter, time_formatter

def build_cmd_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--day", type=int, action="store", required=True, help="The day number within the horizon.")
    parser.add_argument('--s_date', action='store', type=date_formatter, required=True, help='Starting date of the horizon in iso format (yyyy-mm-dd)')
    parser.add_argument('--s_time', action='store', type=time_formatter, default='07:00', help='Shift start time in %H:%M format (e.g 07:00)')

    args = parser.parse_args()
    return args

# Parameterscrew_type
args = build_cmd_args()
day = args.day
start_datetime = datetime.datetime(args.s_date.year, args.s_date.month, args.s_date.day, args.s_time.hour, args.s_time.minute) + datetime.timedelta(days=day-1)

print("Processing optrunoutput...", end="")

# Reading in item and vehicle results
item_results = pd.read_excel(f"../results/day{day}/item_results.xlsx", index_col=0)
vehicle_results = pd.read_excel(f"../results/day{day}/vehicle_results.xlsx") 


# Getting which crew does each job, as well as the sequence for that vehicle.
job_allocation = {'index': [], 'crew_type_ID': [], 'crew_type': [], 'crew_num': [], 'sequence': []} # The dataframe to be joined to item_results. Index = Job index.
for _, row in vehicle_results.iterrows(): # For each vehicle (Row in vehicle results)
    seq = 1 # Initialise the job order index for that vehicles tour
    if row['tour'] == 0: # If the vehicle isn't used
        continue
    tour = eval(row["tour"]) # Getting the tour as a list. Use eval
    for job in tour:
        if job != 0:
            job_allocation['index'].append(job) # Job index based on ingested data
            job_allocation['crew_type_ID'].append(row['crew_type_ID'])
            job_allocation['crew_type'].append(row['crew_type'])
            job_allocation['crew_num'].append(int(row['crew_num']))
            job_allocation['sequence'].append(seq) # Job order index
            seq += 1


job_allocation = pd.DataFrame.from_dict(job_allocation).set_index('index') # Converting to a dataframe. Setting the index of the dataframe as the index of the job
item_results = item_results.join(job_allocation) # Left joining item_results to job_allocation on the index (Column types become float rather than int due to NaN values)

# Getting the start time of each job
start_time = []
for i, row in item_results.iterrows():
    if pd.isnull(row["OptShift"]): # If the optimisation does not assign a shift to the job
        start_time.append(None)
    else:
        start_time.append(row['Estimated Completion Time'] - datetime.timedelta(minutes=row['EstDuration']))

# Getting the distance travelled for each job (That is, going from the previous defect to the current defect)
travel_dist = {'index': [], 'DistanceTravelForJob': []} # The dataframe to be joined to item_results
depot_return = {'vehicle_num': [], 'Sequence': [], 'TimeForReturn': [], 'DistanceTravelForReturn': [], 'ReturnTime': []} # Separate dataframe that stores the return trip
n = len(item_results)

for i, row in vehicle_results.iterrows(): # For each vehicle
    tour = row["tour"] # Tour for that vehicle

    if tour == 0: # If vehicle is not used
        continue

    tour = eval(tour) 

    vehicle_num = row["vehicle_number"] # The depot for that vehicle
    dist_matrix = np.array(pd.read_excel(f"../outputs/day{day}/dist_matrices/{vehicle_num}_dist_matrix.xlsx", header=None)) 
    time_matrix = np.array(pd.read_excel(f"../outputs/day{day}/time_matrices/{vehicle_num}_time_matrix.xlsx", header=None))

    for i in range(1,len(tour)): # For each defect that the vehicle completes
        src = tour[i-1] # From previous position index
        dst = tour[i] # To current position index

        travel_dist['index'].append(dst)
        travel_dist['DistanceTravelForJob'].append(dist_matrix[src][dst-1]) # Python matrix indexing. Rows start at location 0, matching the Python index.

    # Returning to the depot
    last_job = tour[-1]
    depot = 0
    depot_return['vehicle_num'].append(row['vehicle_number'])
    depot_return['Sequence'].append(len(tour))
    depot_return['DistanceTravelForReturn'].append(dist_matrix[last_job][n])
    depot_return['TimeForReturn'].append(time_matrix[last_job][n])
    depot_return['ReturnTime'].append(item_results.loc[last_job, 'Estimated Completion Time'] + datetime.timedelta(minutes=time_matrix[last_job][n]))



# returning to depot rows for item_results 
return_rows = {'ItemType': [], 'ItemIdentifier': [], 'OptShift': [], 'CrewTypeID': [], 'CrewTypeCode': [], 'CrewNum': [], 'Sequence': [], 
'DistanceTravelForJob': [], 'PointsCalculatedForJob': [], 'PlanStartDate': [], 'PlanEndDate': []} # The rows which indicate returning back to the depot

for i, vehicle_num in enumerate(depot_return['vehicle_num']):
    return_rows['ItemType'].append("Return")
    return_rows['ItemIdentifier'].append(0)
    return_rows['OptShift'].append(None)
    return_rows['CrewTypeID'].append(vehicle_results.loc[vehicle_results["vehicle_number"] == vehicle_num, "crew_type_ID"].iloc[0])
    return_rows['CrewTypeCode'].append(vehicle_results.loc[vehicle_results["vehicle_number"] == vehicle_num, "crew_type"].iloc[0])
    return_rows['CrewNum'].append(vehicle_results.loc[vehicle_results["vehicle_number"] == vehicle_num, "crew_num"].iloc[0])
    return_rows['Sequence'].append(depot_return['Sequence'][i])
    return_rows['DistanceTravelForJob'].append(depot_return['DistanceTravelForReturn'][i])
    return_rows['PointsCalculatedForJob'].append(0)
    return_rows['PlanStartDate'].append(depot_return['ReturnTime'][i])
    return_rows['PlanEndDate'].append(depot_return['ReturnTime'][i])


travel_dist = pd.DataFrame.from_dict(travel_dist).set_index('index') # Converting to a dataframe. Setting the index of the dataframe as the index of the job
item_results = item_results.join(travel_dist) # Left joining item_results to travel_dist on the index

# OptRunOutput table
df = {}

df['ItemType'] = list(item_results['ItemType'])
df['ItemIdentifier'] = list(item_results['ItemIdentifier'])
df['OptShift'] = list(item_results['OptShift'])
df['CrewTypeID'] = [None if pd.isnull(x) else x for x in item_results['crew_type_ID']]
df['CrewTypeCode'] = [None if pd.isnull(x) else x for x in item_results['crew_type']]
df['CrewNum'] = [None if np.isnan(x) else int(x) for x in item_results['crew_num']]
df['Sequence'] = [None if np.isnan(x) else int(x) for x in item_results['sequence']]
df['DistanceTravelForJob'] = [None if np.isnan(x) else x for x in item_results['DistanceTravelForJob']]
df['PointsCalculatedForJob'] = list(item_results['Score'])
df['PlanStartDate'] = [None if x == None else x.to_pydatetime() for x in start_time] # Converting Timestamp object to datetime (Parquet files store Timestamp as int)
df['PlanEndDate'] = [None if type(x) != pd.Timestamp else x.to_pydatetime() for x in item_results['Estimated Completion Time']]

df = pd.DataFrame.from_dict(df)
df = df[df.OptShift.notnull()] # Drops jobs that aren't assigned

# Adding in the depot return trip as rows
return_rows = pd.DataFrame.from_dict(return_rows)
df = pd.concat([df, return_rows])

df.to_excel(f"../results/day{day}/optrunoutput.xlsx", index=False)
df.to_parquet(f"../results/day{day}/optrunoutput.parquet", coerce_timestamps="ms", allow_truncated_timestamps=True, engine='pyarrow')

print("ok")