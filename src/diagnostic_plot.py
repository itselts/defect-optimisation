import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import numpy as np
import argparse
import mpld3
from tours import out

##### DATA INPUT #####
plt.figure(num=1, figsize=[10,8]) # Figure that includes all defects
plt.figure(num=2, figsize=[10,8]) # Cleaned figure that only includes defects in tours


# Reading in depots (SHould be read in from a config file.)
depot_input = pd.read_csv(f"../data/depot_input.csv")
depots = set()

depot_coords = {}
for i, row in depot_input.iterrows():
    depots.add(row["dv_code"])
    depot = row["dv_code"]
    depot_coords[f"{depot}"] = (float(row["Long"]), float(row["Lat"]))


# Reading in the crews. Enumerating each truck, along with its crew type and depot location.
crew_input = pd.read_csv('../data/crew_input.csv')
vehicle_results = pd.read_csv('../results/vehicle_results.csv')
m = sum(vehicle_results['tour'] != 0)

# Reading in visited points
visited = eval(pd.read_csv(f'../results//visited_summary.csv')["visited"][0])
visited.remove(0)
visited = list(visited)


##### PLOTTING JOBS AND DEPOTS #####
coords = pd.read_csv(f"../data/sample_data.csv")[["LatStart", "LongStart"]]
n = len(coords)

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

        coords = pd.read_csv(f"../data/sample_data.csv")[["LatStart", "LongStart"]]
        coords.loc[-1] = [depot_coords[start_depot][1], depot_coords[start_depot][0]] # adding a row on top for start depot 
        coords.index = coords.index + 1 # shifting index
        coords.loc[n+1] = [depot_coords[end_depot][1], depot_coords[end_depot][0]] # adding a row on the bottom for end depot
        coords.sort_index(inplace=True) # Index 0 is the start depot, index n+1 is the end depot. Required for out(X)

        X = pd.read_csv(f"../results/X_matrices/X{truck_number}_matrix.csv", skiprows=1, header=None)

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
Html_file1= open(f"../outputs/results_plot.html","w")
Html_file1.write(html_str1)
Html_file1.close()

html_str2 = mpld3.fig_to_html(fig2)
Html_file2= open(f"../outputs/results_plot_cleaned.html","w")
Html_file2.write(html_str2)
Html_file2.close()

print("Diagnostic plot produced and saved to local results folder.")
