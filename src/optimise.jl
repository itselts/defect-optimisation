using CSV
using DataFrames
using JuMP
using Pipe
using Dates
using Gurobi


##### INPUT DATA ####
sample_data = @pipe CSV.File("./data/sample_data.csv") |> DataFrame(_)
depot_input = @pipe CSV.File("./data/depot_input.csv") |> DataFrame(_)
crew_input = @pipe CSV.File("./data/crew_input.csv") |> DataFrame(_)

select!(sample_data, Not(:Column1))
n = size(sample_data)[1]

# Job data
scores = Dict{Int64, Float64}() # Job scores
due_times = Dict{Int64, Float64}() # Due times
job_times = Dict{Int64, Int64}() # Job times
shifts = Dict{Int64, String}() # Shift codes for each job
for (i,row) in enumerate(eachrow(sample_data))
    scores[i]=row["Score"]
    due_times[i] = row["Minutes until due"]
    shifts[i] = row["ShiftCode"]
    if row["EstDuration"] === nothing
        job_times[i] = 15
    else
       
        job_times[i] = row["EstDuration"]
    end
end

# Dummy job score and job times for the start and end depots
scores[0] = 0
scores[n+1] = 0
job_times[0] = 0 
job_times[n+1] = 0
due_times[0] = 0 
due_times[n+1] = 0


##### CREW INPUT DATA #####
trucks = 1:nrow(crew_input) # Indexing each truck
crew_types = Set(crew_input[!,"crew_type"]) # All possible crew types
depots = Set(depot_input[!, "dv_code"]) # All depots
shift_codes = Set(sample_data[!, "ShiftCode"])

# For crew type constraints
type_job_dict = Dict(name => Array{Int}(undef,0) for name in crew_types) # For each crew type, which jobs they can do.
type_truck_dict = Dict(name => Array{Int}(undef,0) for name in crew_types) # For each crew type, which truck numbers are associated with it.

for crew_type in crew_types
    # Populating type_job_dict
    for (i, row) in enumerate(eachrow(sample_data))
        if occursin(crew_type, row["CrewType_FKs"])
            append!(type_job_dict[crew_type], i) # That is because depot is location 1. So the i-th entry is position i+1
        end
    end

    # Populating type_truck_dict
    for row in eachrow(crew_input)
        if  crew_type == row["crew_type"]
            append!(type_truck_dict[crew_type], row["truck_num"])
        end
    end
end

# For shift code constraints
shift_job_dict = Dict(shift_code => Array{Int}(undef,0) for shift_code in shift_codes)
shift_truck_dict = Dict(shift_code => Array{Int}(undef,0) for shift_code in shift_codes)

for shift_code in shift_codes
    # Populating shift_job_dict
    for (i, row) in enumerate(eachrow(sample_data))
        if occursin(shift_code, row["ShiftCode"])
            append!(shift_job_dict[shift_code], i)
        end
    end

    # Populating shift_truck_dict
    for (i, row) in enumerate(eachrow(crew_input))
        if shift_code == row["shift_code"]
            append!(shift_truck_dict[shift_code], i)
        end
    end
end

# Time matrices for each crew
time_matrix_dict = Dict{Int64, DataFrame}()
for truck in trucks
    time_matrix_dict[truck] = CSV.File(string("./data/time_matrices/", string(truck),"_time_matrix.csv"), header=false) |> DataFrame
end

# Getting thes start and end times of each crew into an int, as well as time capacities of each crew
shift_end = Dict{}()
shift_start = Dict{}()

for row in eachrow(crew_input)
    truck_num = row["truck_num"]
    shift_start[truck_num] = Dates.Minute(row["start_time"].instant).value
    shift_end[truck_num] = Dates.Minute(row["end_time"].instant).value
end


##### OTHER INPUT DATA #####
# Getting the max times in minutes for each crew
max_time = []
for row in eachrow(crew_input)
    truck_num = row["truck_num"]
    delta_t = shift_end[truck_num] - shift_start[truck_num]
    append!(max_time, [delta_t])
end



# Job penalties
penalties = sample_data[!, "Penalty"]

# Due today
due_today = []
for i in 1:n
    if penalties[i] != 0
        append!(due_today, i)
    end
end


##### MODEL PARAMETERS #####
println('-'^40)
println(string("        Optimising for ", n, " jobs        "))

locations = 0:(n+1) # Location 0 is start depot, location n+1 is end depot
jobs = 1:n

###### Determine which is the global big M, and which is crew dependent #####
M1 = maximum(values(shift_end)) + maximum(values(job_times)) + 5000 # Big M1 for temporal/tours constraint
M2 = maximum(values(shift_end)) + 5000 # Big M2 for shift time constraints

if due_today == Any[]
    M3 = 3000
else
    today_due_times = []
    for i in due_today
        append!(today_due_times, due_times[i])
    end
    M3 = maximum(today_due_times) # Big M3 constraint for due time tracking
end

##### MODELLING #####
# model = Model(SCIP.Optimizer)
model = Model(Gurobi.Optimizer)

# Decision variables scores
@variable(model, X[i in 0:n, j in 1:(n+1), k in trucks] >= 0, Bin) # 1 if go from location i to location j with truck k
@variable(model, t[i in jobs] >= 0) # Time tracking for jobs
@variable(model, z[i in due_today], Bin) # Penalty term for not doing a job on time

# expressions
# Penalty score and objective function expressions
@expression(model, penalty_score, sum(penalties[i]*z[i] for i in due_today))
@expression(model, job_score, sum((scores[j] - 1.5*time_matrix_dict[k][i+1,j] - 0.5*job_times[j]) * X[i,j,k] for i in 0:n for j in 1:(n+1) for k in trucks)) # BEWARE MATRIX INDEXING VS JOB INDEXING
@expression(model, obj, job_score - penalty_score )#- sum(t[i] for i in 2:n))
#println(obj)

# constraints
# (1) All jobs entered at most once (That is, excluding depot)
for j in jobs
    @constraint(model, sum(X[i,j,k] for i in 0:n for k in trucks) <= 1)
end

# (2) Vehicle leaving and returning
for k in trucks
    @constraint(model, sum(X[0,j,k] for j in jobs) == sum(X[j,n+1,k] for j in jobs))
    @constraint(model, sum(X[0,j,k] for j in jobs) == 1)
end

# (3) Conservation of flow
for j in jobs, k in trucks
    @constraint(model, sum(X[i,j,k] for i in 0:n) == sum(X[j,i,k] for i in 1:(n+1)))
end

# (4) Cannot visit itself (Might be covered by subtours constraints.)
for i in jobs, k in trucks
    @constraint(model, X[i,i,k] == 0)
end

# (5) Temporal constraints
for i in jobs
    for j in jobs
        @constraint(model, t[j] >= t[i] + job_times[j] + time_matrix_dict[1][i+1, j] - M1*(1 - sum(X[i,j,k] for k in trucks)))
    end
end

# (6) Shift time constraints
for j in jobs
    @constraint(model, t[j] >= sum(X[0,j,k]*(shift_start[k] + job_times[j] + time_matrix_dict[k][1, j]) for k in trucks))
    @constraint(model, t[j] <= sum(X[j,n+1,k]*(shift_end[k] - time_matrix_dict[k][j+1, n+1]) for k in trucks) + 5000*(1-sum(X[j,n+1,k] for k in trucks)))
end

# (7) Penalty constraints (t[i] >= due time + epsilon <=> penalty)
for i in due_today
    @constraint(model, t[i] >= due_times[i] + 1 - M3*(1-z[i]))
    @constraint(model, t[i] <= due_times[i] + M2*z[i])
end

# (8) Crew type constraints
for crew_type in crew_types
    for j in setdiff(collect(1:n), type_job_dict[crew_type])
        @constraint(model, sum(X[i,j,k] for i in 0:n for k in type_truck_dict[crew_type]) == 0) # These trucks cannot do those jobs
    end
end

# (9) Shift code constraints
for shift_code in shift_codes
    for j in setdiff(collect(1:n), shift_job_dict[shift_code])
        @constraint(model, sum(X[i,j,k] for i in 0:n for k in shift_truck_dict[shift_code]) == 0)
    end
end


##### Objective #####
@objective(model, Max, obj)


##### Solving model #####
SOLVER_GAP = 0.01
TIME_LIMIT = 120
NORELHEURTIME = TIME_LIMIT
#set_optimizer_attribute(model, "MIPGap", SOLVER_GAP)
set_optimizer_attribute(model, "TimeLimit", TIME_LIMIT)
set_optimizer_attribute(model, "NoRelHeurTime", NORELHEURTIME)
set_optimizer_attribute(model, "MIPFocus", 1)

show(model)
optimize!(model)
solution_summary(model)


# Job completion times
times = Tables.table(value.(t.data[:]))
CSV.write("./results/t.csv", times)

if !isdirpath("./results/X_matrices")
    mkpath("results/X_matrices")
end

for k in trucks
    path = string("./results/X_matrices/X", k, "_matrix.csv")
    CSV.write(path, Tables.table(value.(X.data[:, :, k])))
end

#=
# Warm start
x = all_variables(model)
x_solution = value.(x)
set_start_value.(x, x_solution)
optimize!(model)
=#