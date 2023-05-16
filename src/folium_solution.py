import pandas as pd
import folium
from tours import out, get_tours
from matplotlib.pyplot import cm
import numpy as np

##### DATA INPUT #####
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

map_solution = folium.Map()
map_solution.fit_bounds([[min(coords["LatStart"]), min(coords["LongStart"])], [max(coords["LatStart"]), max(coords["LongStart"])]])


# Plotting the depots in red
for depot, c in depot_coords.items():
    folium.CircleMarker(location=[c[1], c[0]], color="#FF0000", radius=5, tooltip=depot).add_to(map_solution)

# Annotating the defects
for i in range(1,n+1):
    if i in visited:
        sy, sx = coords['LatStart'][i-1], coords['LongStart'][i-1]
        folium.CircleMarker(location=[sy, sx], color="#000000", radius=3, popup=i).add_to(map_solution)

##### CREW TOURS #####
colours = [tuple(rgb)[:3] for rgb in cm.rainbow(np.linspace(0, 1, m))]
colours = ['#{:02x}{:02x}{:02x}'.format(round(rgb[0]*255), round(rgb[1]*255), round(rgb[2]*255)) for rgb in colours] # In hex colours

c = 0
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

        x1, y1 = coords.iloc[p1]["LongStart"], coords.iloc[p1]["LatStart"]
        x2, y2 = coords.iloc[p2]["LongStart"], coords.iloc[p2]["LatStart"]

        folium.PolyLine(locations=[(y1, x1), (y2, x2)], color=colours[c]).add_to(map_solution)
   
    c += 1

map_solution.save(f"../outputs/folium_solution.html")