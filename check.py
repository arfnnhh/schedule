import pandas as pd
from pulp import *
from tabulate import tabulate

# Load data from CSV
data = pd.read_csv('mapel.csv')

# Parameters
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
periods_per_day = {"Monday": 9, "Tuesday": 10, "Wednesday": 10, "Thursday": 10, "Friday": 9}
classes = data['jumlah_rombel'].iloc[0]  # Number of classes
total_periods_per_class = 48  # Each class needs exactly 48 periods
total_periods = total_periods_per_class * classes  # Total periods needed

# Teacher and period setup
teachers = data['guru'].unique()
teacher_periods = data.groupby('guru')['mapel'].sum()
max_teacher = teacher_periods.idxmax()  # Teacher with the highest periods

# Initialize the LP problem
prob = LpProblem("Teacher_Scheduling_Problem", LpMinimize)

# Decision variables
assign = LpVariable.dicts("assign", [(t, c, d) for t in teachers for c in range(1, classes + 1) for d in days], 0, 1, LpBinary)

# Objective function: minimize the total number of assignments
prob += lpSum(assign[t, c, d] for t in teachers for c in range(1, classes + 1) for d in days)

# Constraints

# 1. Each class should have exactly 48 periods across the week
for c in range(1, classes + 1):
    prob += lpSum(assign[t, c, d] for t in teachers for d in days) == total_periods_per_class

# 2. Each teacher must have at least 2 periods per day, except the teacher with the highest periods
for t in teachers:
    for d in days:
        if t != max_teacher:
            prob += lpSum(assign[t, c, d] for c in range(1, classes + 1)) >= 2
        else:
            prob += lpSum(assign[t, c, d] for c in range(1, classes + 1)) >= 0  # No restriction for the max_teacher

# 3. A teacher can only be assigned to a single class per period (but can be assigned to multiple periods in the same class)
for d in days:
    for t in teachers:
        prob += lpSum(assign[t, c, d] for c in range(1, classes + 1)) <= 1

# 4. Total periods per day must match the allowed periods (9 on Monday and Friday, 10 on others)
for d in days:
    prob += lpSum(assign[t, c, d] for t in teachers for c in range(1, classes + 1)) == periods_per_day[d]

# Debugging step: Relax or comment constraints to identify issues
# Temporarily disable or relax constraints
# prob += lpSum(assign[t, c, d] for t in teachers for c in range(1, classes + 1) for d in days) >= total_periods  # Ensure all periods are covered

# Solve the problem
prob.solve()

# Print problem status and check for infeasibility
print(f"Status: {LpStatus[prob.status]}")
if LpStatus[prob.status] != "Optimal":
    print("Problem status:", LpStatus[prob.status])
    print("Objective value:", value(prob.objective))
    for name, constraint in prob.constraints.items():
        print(f"{name}: {constraint}")
    raise ValueError("No optimal solution found. Check the constraints or model.")

# Extract the schedule
schedule = []
for d in days:
    for t in teachers:
        for c in range(1, classes + 1):
            if assign[t, c, d].varValue == 1:
                schedule.append([d, t, c])

# Convert to DataFrame
schedule_df = pd.DataFrame(schedule, columns=["Day", "Teacher", "Class"])

# Sort schedule by Day and then by Class
schedule_df['Day'] = pd.Categorical(schedule_df['Day'], categories=days, ordered=True)
schedule_df = schedule_df.sort_values(by=["Day", "Class"]).reset_index(drop=True)

# Display in the console
print(tabulate(schedule_df, headers="keys", tablefmt="grid"))

# Save to CSV and Excel

