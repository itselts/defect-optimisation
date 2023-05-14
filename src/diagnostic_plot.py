import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import numpy as np
import argparse
import mpld3
from tours import out, get_tours

##### DATA INPUT #####
def build_cmd_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--request_ID', action='store', type=str, required=True)
    parser.add_argument("--day", type=int, action="store", required=True, help="The day number within the horizon.")
    parser.add_argument('-n', action="store", type=int, required=True, help="Number of defects to optimis.")
    args = parser.parse_args()
    return args

args = build_cmd_args()
request_ID = args.request_ID
n = args.n
day = args.day

disp_bar = f"{'-'*40}"
print(disp_bar)
print(f"{'Getting diagnostic plots...' : ^40}")


plt.figure(num=1, figsize=[10,8]) # Figure that includes all defects
plt.figure(num=2, figsize=[10,8]) # Cleaned figure that only includes defects in tours


# Reading in depots (SHould be read in from a config file.)
depot_input = pd.read_parquet(f"../data/{request_ID}/v_DomainValueDepot.parquet")
depots = set()

depot_coords = {}
for i, row in depot_input.iterrows():
    depots.add(row["dv_code"])
    depot = row["dv_code"]
    depot_coords[f"{depot}"] = (float(row["Long"]), float(row["Lat"]))


# Reading in the crews. Enumerating each truck, along with its crew type and depot location.
crew_input = pd.read_excel(f'../outputs/day{day}/crew_input.xlsx', sheet_name="Sheet1")
vehicle_results = pd.read_excel(f'../results/day{day}/vehicle_results.xlsx', sheet_name="Sheet1")
m = sum(vehicle_results['tour'] != 0)

# Reading in visited points
visited = eval(pd.read_excel(f'../results/day{day}/visited_summary.xlsx', sheet_name="Sheet1")["visited"][0])
visited.remove(0)
visited = list(visited)


##### PLOTTING JOBS AND DEPOTS #####
coords = pd.read_excel(f"../outputs/day{day}/sample_data.xlsx")[["LatStart", "LongStart"]]
coords = coords.head(n)

plt.figure(1)
plt.scatter(coords["LongStart"], coords["LatStart"], color='b', s=10) 
fig1 = plt.figure(1)

plt.figure(2)
plt.scatter(coords["LongStart"][[x-1 for x in visited]], coords["LatStart"][[x-1 for x in visited]], color='b', s=10) 
fig2 = plt.figure(2)

# Plotting the depots in red
for fig in [1,2]:
    plt.figure(fig)
    for i, row in depot_input.iterrows():
        plt.scatter(float(row["Long"]), float(row["Lat"]), color='r')
        plt.text(float(row["Long"]), float(row["Lat"]), row["DepotName"])

# Annotating the defects
for i in range(1,n+1):
    plt.figure(1)
    plt.annotate(i, (coords['LongStart'][i-1], coords['LatStart'][i-1]))
    if i in visited:
        plt.figure(2)
        plt.annotate(i, (coords['LongStart'][i-1], coords['LatStart'][i-1]))


##### CREW TOURS #####
colours = cm.rainbow(np.linspace(0, 1, m))

for fig in [1,2]:
    plt.figure(fig)
    c=0
    for i, row in vehicle_results.iterrows():
        truck_number = row["vehicle_number"]

        if row['tour'] == 0:
            continue

        start_depot = row["start_depot"]
        end_depot = row["end_depot"]

        coords = pd.read_excel(f"../outputs/day{day}/sample_data.xlsx")[["LatStart", "LongStart"]]
        coords.loc[-1] = [depot_coords[start_depot][1], depot_coords[start_depot][0]] # adding a row on top for start depot 
        coords.index = coords.index + 1 # shifting index
        coords.loc[n+1] = [depot_coords[end_depot][1], depot_coords[end_depot][0]] # adding a row on the bottom for end depot
        coords.sort_index(inplace=True) # Index 0 is the start depot, index n+1 is the end depot. Required for out(X)

        X = pd.read_csv(f"../outputs/day{day}/X_matrices/X{truck_number}_matrix.csv", skiprows=1, header=None)

        pair_dict = out(X)

        for pair in pair_dict.values():
            p1 = pair[0] # origin node index
            p2 = pair[1] # destination node index

            x1 = coords.iloc[p1]["LongStart"]
            y1 = coords.iloc[p1]["LatStart"]
            
            x2 = coords.iloc[p2]["LongStart"]
            y2 = coords.iloc[p2]["LatStart"]

            plt.plot([x1, x2], [y1, y2], c=colours[c])

        c += 1


# Saving image to a html file
html_str1 = mpld3.fig_to_html(fig1)
Html_file1= open(f"../results/day{day}/results_plot.html","w")
Html_file1.write(html_str1)
Html_file1.close()

html_str2 = mpld3.fig_to_html(fig2)
Html_file2= open(f"../results/day{day}/results_plot_cleaned.html","w")
Html_file2.write(html_str2)
Html_file2.close()

print("Diagnostic plot produced and saved to local results folder.")
