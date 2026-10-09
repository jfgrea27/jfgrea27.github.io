import matplotlib.pyplot as plt
import pandas as pd

# Read the salary dataset
df = pd.read_csv("path/to/06-ml-math/01-linear-regression/salary.csv")

# Create scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(df["YearsExperience"], df["Salary"], color="blue", alpha=0.7)
plt.xlabel("Years of Experience")
plt.ylabel("Salary ($)")
plt.title("Salary vs Years of Experience")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("salary_plot.png")
plt.show()
