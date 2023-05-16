import pandas as pd
import os
import re
import numpy as np
import datetime
from tours import out, get_tours


# Reading in the jobs, depots and crews
sample_data = pd.read_csv("../data/sample_data.csv")
depot_input = pd.read_csv(f"../data/depot_input.csv")
crew_input = pd.read_csv(f'../data/crew_input.csv')

time_matrix_dict = {}
dist_matrix_dict = {}
depots = set()

for depot in depot_input["DepotName"]:
    depots.add(depot)

for truck_num in crew_input["truck_num"]:
    time_matrix_dict[truck_num] = pd.read_excel(f"../data/time_matrices/{truck_num}_time_matrix.xlsx", header=None).to_numpy()
    dist_matrix_dict[truck_num] = pd.read_excel(f"../data/dist_matrices/{truck_num}_dist_matrix.xlsx", header=None).to_numpy()

m = len(crew_input) # total number of trucks


##### VEHICLE RESULTS #####
visited = set() # Getting the list of visited points by iterating through all vehicle tours
vehicles = [] # The results summary for each vehicle. Each element is a row in the resulting data frame

# Processing X matrices to get vehicle resutls
for file in os.listdir(f"../results/X_matrices"):
    vehicle_number = int(re.findall('\d+', file)[0])
    start_depot = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'start_depot'].to_string(index=False)
    end_depot = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'end_depot'].to_string(index=False)
    crew_type_ID = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'crew_type_ID'].to_string(index=False)
    crew_type = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'crew_type'].to_string(index=False)
    shift_code = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'shift_code'].to_string(index=False)
    crew_num = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'crew_num'].to_string(index=False)
    start_time = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'start_time'].to_string(index=False)
    end_time = crew_input.loc[crew_input['truck_num'] == vehicle_number, 'end_time'].to_string(index=False)

    X_df = pd.read_csv(f"../results/X_matrices/{file}")
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
vehicles.to_csv(f"../results/vehicle_results.csv")


##### VISITED SUMMARY #####
count = len(visited)-1 # -1 because it includes index 0 (Start depot)
if count == -1:
    count = 0
pd.DataFrame([{'count': count, 'visited': visited}]).to_csv(f"../results/visited_summary.csv")

print(f"Results processed. Item results, vehicle results, and item summary saved to local results folder.")