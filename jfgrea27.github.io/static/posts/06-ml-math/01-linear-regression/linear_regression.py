import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Read the salary dataset
df = pd.read_csv("path/to/06-ml-math/01-linear-regression/salary.csv")

X = df["YearsExperience"].to_numpy()
y = df["Salary"].to_numpy()

# Initialize parameters
theta_0 = 0.0  # y-intercept
theta_1 = 0.0  # gradient
alpha = 0.0001  # learning rate (small due to large salary values)
n_iterations = 1000
m = len(X)

# Store loss history
losses = []

# Gradient descent
for i in range(n_iterations):
    # Predictions
    y_pred = theta_0 + theta_1 * X

    # Calculate MSE loss
    loss = (1 / m) * np.sum((y - y_pred) ** 2)
    losses.append(loss)

    # Calculate gradients
    d_theta_0 = (-2 / m) * np.sum(y - y_pred)
    d_theta_1 = (-2 / m) * np.sum((y - y_pred) * X)

    # Update parameters
    theta_0 = theta_0 - alpha * d_theta_0
    theta_1 = theta_1 - alpha * d_theta_1

print(f"Final parameters:")
print(f"  theta_0 (y-intercept): {theta_0:.2f}")
print(f"  theta_1 (gradient): {theta_1:.2f}")
print(f"  Equation: Salary = {theta_0:.2f} + {theta_1:.2f} * YearsExperience")

# Create two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Data points and line of best fit
ax1.scatter(X, y, color="blue", alpha=0.7, label="Data points")
X_line = np.linspace(X.min(), X.max(), 100)
y_line = theta_0 + theta_1 * X_line
ax1.plot(X_line, y_line, color="red", linewidth=2, label="Line of best fit")
ax1.set_xlabel("Years of Experience")
ax1.set_ylabel("Salary ($)")
ax1.set_title("Linear Regression: Salary vs Experience")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Loss over iterations
ax2.plot(range(n_iterations), losses, color="green", linewidth=2)
ax2.set_xlabel("Iteration")
ax2.set_ylabel("MSE Loss")
ax2.set_title("Loss over Training Iterations")
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("linear_regression_results.png")
plt.show()
