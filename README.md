# Overview
A cost-constrained multi-depot vehicle routing model used to optimise work packaging. Makes three decisions simultaneously:
- what jobs to do 
- who does them  
- how to do them

Model formulation is in docs. Formulation is then coded up and solved in Julia using Gurobi (License required). Post-processing and plotting done in Python. Not the cleanest of code as it was part of a much larger workflow. This is a focus on the mathematical model and solving, rather than operational usage.

![alt text](https://github.com/big-thugga/defect-optimisation/blob/main/outputs/folium_plot.png)

Solution on a blank canvas. Further geographic plot results in the outputs folder.

![alt text](https://github.com/big-thugga/defect-optimisation/blob/main/outputs/results_plot.png)

## Model features
- Maximise the job score (Score function, balanced by travel time and job time)
- Crew constraints
- Due dates
- Different start and end depots
- Different start and end shift times

## Data input
The data used to create and test the model is from NEMA. 
- 9 depots (Wangaratta, Shepparton, Wodonga, Seymour, Mansfield, Broadford...)
- 44 defects

## How to run
Download the repository. Environment requirements are all contained in requirements.txt for Python, and Manifest.toml/Project.toml for Julia.

### Python steps
pip install -r requirements.txt

### Julia steps
] activate .

Pkg.instantiate()
