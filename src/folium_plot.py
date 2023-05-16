import pandas as pd
import folium

##### DATA INPUT #####
sample_data = pd.read_csv("../data/sample_data.csv")
depot_input = pd.read_csv("../data/depot_input.csv")

##### PLOTTING #####
map = folium.Map()
map.fit_bounds([[min(sample_data["LatStart"]), min(sample_data["LongStart"])], [max(sample_data["LatStart"]), max(sample_data["LongStart"])]])

# Plotting the depots in red
for i, row in depot_input.iterrows():
    folium.CircleMarker(location=[row["Lat"], row["Long"]], color="#FF0000", radius=5, tooltip=f'{row["dv_meaning"]} Depot').add_to(map)

# Plotting the defects in black
n = len(sample_data)
for i, row in sample_data.iterrows():
    sy, sx = row['LatStart'], row['LongStart']
    folium.CircleMarker(location=[sy, sx], color="#000000", radius=3, popup=f"Defect ID: {row['ItemIdentifier']}").add_to(map)

map.save(f"../outputs/folium_plot.html")
