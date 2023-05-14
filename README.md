# Cost-constrained multi-depot vehicle routing model
A cost-constrained multi-depot vehicle routing model used to optimise work packaging and crew/inspector utilisation by firstly deciding on work allocation, and then the efficient traversely of those jobs for each crew. Model formulated via Julia, workflow with Python. Solved using a Gurobi license. 

## Model features
- Maximise the job score (Score function, balanced by travel time and job time)
- Crew constraints
- Due dates
- Can handle 150+ defects with an approximate 12 minute solve time.

## Data input
The data used to create and test the model is from NEMA. 
- 5 depots (Wangaratta, Shepparton, Wodonga, Seymour, Mansfield)

## How to run
Clone the repository and download the required Python and Julia libraries from requirements.txt.

To run an optimisation for a specified dataset, number of points, start date and horizon, run the execute.py script in src via the command line.
An example of a command to optimise for 99 defects over a 3 day horizon from 2022/12/3:

python execute.py --contract_ID VRMC_OPS --request_ID AE49344C-D100-420E-A5AC-87B0053D4DE3

Test cases: 
7299E896-F776-4F5C-A5A7-1312569DB94D
- 35 defects
- 5 crews O,I,H,G,P
- All jobs can be done
- 2 crews not used, I and H

B82CFB29-87FA-4AF7-BC2E-F05D0576C2F8
- 6 F,G defects
- s_date = 25/01/2023
- 8 crews (Mix of O, P, G crews)
- 2 of the same crews from entry from PowerApp, but different end depots. Can use to test same start depot. (Trucks 1/2 and 4/5)

B65EC52F-FE1C-4012-94D6-3C3531ECB994
- 1 A crew
- 1 F,G job

0F26E014-F9DF-4D88-AB7B-744E3B75FAEC
- 34 defects that cannot be all done due to crew constraints

664BAB95-7ACB-4496-9BB5-829FD995D99A
- 100 F,G defects
- 21 crews, 4 F,G crews

B4725161-9A9E-4D9A-BA4D-B1274600C387
- 22 defects
- Real run by Madi (With real crew type codes)

F80C245A-962A-492A-8925-0CD463C677D4
- 6 defects, 7 crews
- Different crew start times. Bleeding over the next day. All jobs can be done. Different shift codes as well

2780ADD4-1A20-4B32-BAAF-D40061C8C147
- 44 defects
- Different start and end depots for 6 vehicles
- 9 depot locations

9F9D1574-0B27-4A8A-8138-3523AF95454C

B4B0FA55-44FE-43F2-999F-9103442E4BBB
- 371 jobs, real scenario observed 3 weeks after VRMC go-live

AE49344C-D100-420E-A5AC-87B0053D4DE3
- 690 jobs, 2 depots, 2 crews
- Real scenario by Molly

538EDA64-5DCC-4633-B2B5-DE16373001CF
- 104 jobs, 1 crew
- Real scenario by Molly
- Sparse jobs around the depot


## Future features
- Dynamic optimisation
- Work balancing
- Two-shift day 
- Different start and end location for trucks
- Long job durations
- Multi-day jobs
