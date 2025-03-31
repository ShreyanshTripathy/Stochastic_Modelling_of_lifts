import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_and_plot_data(csv_file_name, num_floors):
    # Load the CSV file
    data = pd.read_csv(csv_file_name)
    
    # Calculate metrics
    data['Waiting Time'] = data['Lift arrival time'] - data['Passenger arrival time']
    data['Travel Time'] = data['Order completion time'] - data['Lift arrival time']
    data['Total Service Time'] = data['Order completion time'] - data['Passenger arrival time']
    
    # Ensure non-negative times
    data['Waiting Time'] = data['Waiting Time'].clip(lower=0)
    data['Total Service Time'] = data['Total Service Time'].clip(lower=0)

    # 1. Bar Plot: Waiting Time vs. Number of People
    waiting_time_counts = data['Waiting Time'].value_counts().sort_index()
    plt.figure(figsize=(12, 6))
    plt.bar(waiting_time_counts.index, waiting_time_counts.values, color="skyblue", edgecolor="black")
    plt.title('Waiting Time vs. Number of People')
    plt.xlabel('Waiting Time (units)' )
    plt.ylabel('Number of People')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.show()

    # 2. KDE Plot: Waiting Times
    plt.figure(figsize=(12, 6))
    sns.kdeplot(data['Waiting Time'], fill=True, color="blue", bw_adjust=1.5)
    plt.title('KDE Plot of Waiting Times', fontsize=16)
    plt.xlabel('Waiting Time (units)', fontsize=14)
    plt.ylabel('Density', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

    # 3. Histogram: Total Service Times
    plt.figure(figsize=(12, 6))
    plt.hist(data['Total Service Time'], bins='auto', density=True, color='orange', edgecolor='black', alpha=0.8)
    plt.title('Histogram of Total Service Times', fontsize=16)
    plt.xlabel('Total Service Time (units)', fontsize=14)
    plt.ylabel('Density (Probability per unit time)', fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()
    
    # 4. Histogram: Total Service Times
    plt.figure(figsize=(12, 6))
    plt.hist(data['Waiting Time'], bins='auto', density=True, color='orange', edgecolor='black', alpha=0.8)
    plt.title('Histogram of Waiting Time', fontsize=16)
    plt.xlabel('Total Service Time (units)', fontsize=14)
    plt.ylabel('Density (Probability per unit time)', fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

    # 4. Heatmap: Passenger Arrivals
    heatmap_data = data.pivot_table(index='Passenger position', 
                                    columns='Passenger arrival time', 
                                    aggfunc='size', fill_value=0)
    plt.figure(figsize=(16, num_floors / 2))  # Dynamically adjust size based on number of floors
    sns.heatmap(heatmap_data, cmap='cividis', linewidths=0.5, linecolor='black', cbar_kws={'label': 'Number of Passengers'})
    plt.title('Heatmap of Passenger Arrivals', fontsize=16)
    plt.xlabel('Time (discrete units)', fontsize=14)
    plt.ylabel('Floors', fontsize=14)
    plt.tight_layout()
    plt.show()

    # 5. Scatter Plot: Waiting Time for Each Passenger
    plt.figure(figsize=(12, 6))
    plt.scatter(data['Index'], data['Waiting Time'], alpha=0.6, color="purple", edgecolor='black')
    plt.title('Waiting Time for Each Passenger', fontsize=16)
    plt.xlabel('Passenger Index', fontsize=14)
    plt.ylabel('Waiting Time (units)', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

# Example usage
csv_file = "Graphs/4th december 2024 1725/20 floors/Low Traffic/low_traffic_20updated_passenger_data20241204173106.csv"  # Replace with your CSV file path
num_floors = 20  # Set this based on your dataset
analyze_and_plot_data(csv_file, num_floors)
