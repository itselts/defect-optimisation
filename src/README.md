The execute.py script runs the follow sequence of scripts:

1) `preprocessing.py`
- Loads in the required input data (Defects, depots and crews).
- Calculates the priority score for each job.
- Takes the top n subset of jobs to optimise on.

2) `get_dist_matrix.py`
- For that subset of jobs, get the time matrix.
- A different time matrix for each depot.

3) `optimise.jl`
- Optimise and outputs the X matrix for each vehicle.

4) `plot.py`
- Plots the vehicle tours.

5) `results_summary.py`
- Summarises the optimisation results, providing metrics and output results.

6) `get_remaining.py`
- If the horizon is more than 1 day, we take out the subset of points that was visited on the prior day, producing a reduced dataset to optimise on for future days.