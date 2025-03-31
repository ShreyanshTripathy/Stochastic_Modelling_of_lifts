import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

csv_file_name = "Graphs/Updated_passenger_data_20241201003209.csv"
data = pd.read_csv(csv_file_name)
number_passengers = data.Index.count()
# Calculate key metrics for analysis
data['Waiting Time'] = data['Lift arrival time'] - data['Passenger arrival time']
data['Travel Time'] = data['Order completion time'] - data['Lift arrival time']
data['Total Service Time'] = data['Order completion time'] - data['Passenger arrival time']

# Ensure no negative time values
data['Waiting Time'] = data['Waiting Time'].clip(lower=0)
data['Total Service Time'] = data['Total Service Time'].clip(lower=0)

# Filter for non-negative values for plotting KDE
non_negative_waiting_times = data['Waiting Time'][data['Waiting Time'] >= 0]

# Calculate and print essential statistics
waiting_time_stats = {
    'min': non_negative_waiting_times.min(),
    'max': non_negative_waiting_times.max(),
    'mean': non_negative_waiting_times.mean(),
    'std': non_negative_waiting_times.std()
}

total_service_time_stats = {
    'min': data['Total Service Time'].min(),
    'max': data['Total Service Time'].max(),
    'mean': data['Total Service Time'].mean(),
    'std': data['Total Service Time'].std()
}


# Create normalized histogram of Waiting Times
plt.figure()
plt.hist(non_negative_waiting_times, bins='auto', density=True)
plt.title('Normalized Histogram of Waiting Times')
plt.xlabel('Waiting Time (units)')
plt.ylabel('Density (Probability per unit time)')
plt.grid(True)

# Bar graph of Waiting Time vs. Number of People with the Same Waiting Time
waiting_time_counts = non_negative_waiting_times.value_counts().sort_index()
plt.figure()
plt.bar(waiting_time_counts.index, waiting_time_counts.values)
plt.title('Waiting Time vs. Number of People')
plt.xlabel('Waiting Time (units)')
plt.ylabel('Number of People')
plt.grid(True)
plt.show()

# Create normalized histogram of Total Service Times
plt.figure()
plt.hist(data['Total Service Time'], bins="auto", density=True)
plt.title('Normalized Histogram of Total Service Times')
plt.xlabel('Total Service Time (units)')
plt.ylabel('Density (Probability per unit time)')
plt.grid(True)
plt.show()

# Heatmap of Passenger Arrivals
heatmap_data = data.pivot_table(index='Passenger position', columns='Passenger arrival time', aggfunc='size', fill_value=0)
plt.figure()
plt.imshow(heatmap_data, aspect='auto', cmap='viridis', origin='lower')
plt.colorbar(label='Number of Passengers')
plt.title('Heatmap of Passenger Arrivals')
plt.xlabel('Time (discrete units)')
plt.ylabel('Floors')
plt.grid(True)
plt.show()

# Scatter graph of Waiting Time for Each Passenger
plt.figure()
plt.scatter(data['Index'], non_negative_waiting_times)
plt.title('Waiting Time for Each Passenger')
plt.xlabel('Passenger Index')
plt.ylabel('Waiting Time (units)')
plt.grid(True)
plt.show()

# KDE plot of Waiting Times
plt.figure()
sns.kdeplot(non_negative_waiting_times, fill=True, color="blue")
plt.title('KDE Plot of Waiting Times')
plt.xlabel('Waiting Time (units)')
plt.ylabel('Density (Probability per unit time)')
plt.grid(True)
plt.tight_layout()
plt.show()

# KDE plot of Waiting Times
plt.figure()
sns.kdeplot(data['Waiting Time'], fill=True, color="blue", bw_adjust=1)  # Adjust bw_adjust to control smoothing
plt.title('KDE Plot of Waiting Times')
plt.xlabel('Waiting Time (units)')
plt.ylabel('Density (Probability per unit time)')
plt.xlim(0, None)  # Set x-axis limit to start from 0
plt.grid(True)
plt.tight_layout()
plt.show()