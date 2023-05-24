# Overview
A cost-constrained multi-depot vehicle routing model for scheduling and routing of technicians. This is an advanced decision making tool that will determine what is the optimal choice of jobs to do, the allocation of which crew to do them, and how to traverse them, all the while satisfying complex constraints detailed in model features. That is, it makes three decisions simultaneously and optimally:
- what jobs to do 
- who does them  
- how to do them

Automate workforce planning, reduce travel time and increase productivity all in one.

**Thought experiment 1**: *Try manually determining just one of these decisions optimally. For example, given 15 jobs, what is the fastest way to traverse all of them with just 1 vehicle?*

**Thought experiment 2**: *If we can't do all the jobs, is it better to attend to a cluster of low priority jobs close by, or travel further out to an urgent one?*

### Sample problem and solution
![alt text](https://github.com/big-thugga/defect-optimisation/blob/main/outputs/folium_plot.png)

Solution on a blank canvas. Further geographic plot results in the outputs folder.
![alt text](https://github.com/big-thugga/defect-optimisation/blob/main/outputs/results_plot.png)

Mathematical formulation is in the docs folder. Formulation is then coded up and solved in Julia using Gurobi (License required). Post-processing and plotting done in Python. Not the cleanest of code as it was originally part of a much larger workflow. This is a focus on the mathematical model and its solution, rather than operational usage. The model can be solved for hundreds of jobs, dozens of crews and dozens of depots.

## Model features
- Maximise the job score (Unique score for each job to indicate priority level)
- Truck capabilities (Some jobs can't be done by some trucks)
- Due dates (Time windows of jobs)
- Penalties for going overdue
- Different start and end depots for each truck
- Different start and end shift times for each truck

## Sample data
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
