import logging
import csv
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import seaborn as sns
import numpy as np
from scipy.interpolate import griddata
import shutil

class DataExtractingAndGraphing:
    def __init__(self, completed_data, csv_file_name, traffic_level, floor_directory, system_type,num_of_floors,iteration):
        self.completed_data = completed_data
        self.csv_file_name = csv_file_name
        self.number_of_floors = num_of_floors
        self.traffic_level = traffic_level
        self.floor_directory = floor_directory
        self.system_type = system_type
        self.iteration = iteration
    def extract_and_save_data(self):
        # Extract tuples from the nested list structure in self.completed_data
        extracted_tuples = []
        for item in self.completed_data:
            if isinstance(item, list):
                extracted_tuples.extend(item)
        # Sort the extracted tuples by the 'Index' field
        extracted_tuples = sorted(extracted_tuples, key=lambda x: x[1])
        csv_file_name = self.csv_file_name
        headers = ["Index", "Passenger position", "Passenger destination", "Passenger arrival time", 
                   "Lift arrival time", "Order completion time", "Direction"]

        with open(csv_file_name, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)  # Write the headers
            writer.writerows(extracted_tuples)  # Write the data rows

        logging.info(f"Data has been written to {csv_file_name}")
        print(f"Data has been written to {csv_file_name}")

        return csv_file_name

    def plot_data(self):
        # Load the data from the new CSV file for analysis
        data = pd.read_csv(self.csv_file_name)
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

        # Print statistics as plain numbers
        print("Waiting Time Statistics:")
        for key, value in waiting_time_stats.items():
            print(f"{key.capitalize()}: {value}")

        print("Total Service Time Statistics:")
        for key, value in total_service_time_stats.items():
            print(f"{key.capitalize()}: {value}")

        # Save statistics to a text file
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        stats_file_name = f"notepads/{timestamp}_{number_passengers}passengers_{self.number_of_floors}floors.txt"
        with open(stats_file_name, 'w') as f:
            # iteration
            f.write(f"iteration: {self.iteration}\n")
            f.write(f"System used: {self.system_type}\n")
            f.write(f"Number of floors: {self.number_of_floors}\n")
            f.write(f"Number of passengers: {number_passengers}\n")
            f.write(f"traffic: {self.traffic_level}\n")
            f.write("Waiting Time Statistics:\n")
            for key, value in waiting_time_stats.items():
                f.write(f"{key.capitalize()}: {value}\n")
            f.write("\nTotal Service Time Statistics:\n")
            for key, value in total_service_time_stats.items():
                f.write(f"{key.capitalize()}: {value}\n")

        destination_path = f"Graphs/{self.floor_directory}/{self.traffic_level}/{self.system_type}/{timestamp}_{number_passengers}passengers_{self.number_of_floors}floors.txt"

        # Copy the file to the new location
        shutil.copy(stats_file_name, destination_path)
        
        # Create unique file identifiers
        graph_directory = f"Graphs/{self.floor_directory}/{self.traffic_level}/{self.system_type}"
        graph_file_prefix = f"{graph_directory}/{self.system_type}_{timestamp}_np{number_passengers}_nf{self.number_of_floors}"
        
        # Create normalized histogram of Waiting Times
        plt.figure()
        plt.hist(non_negative_waiting_times, bins='auto', density=True,color='orange', edgecolor='black', alpha=0.8)
        plt.title('Normalized Histogram of Waiting Times')
        plt.xlabel('Waiting Time (units)')
        plt.ylabel('Density (Probability per unit time)')
        plt.grid(True)
        plt.savefig(f'{graph_file_prefix}_normalized_histogram_waiting_times.png')

        bin_width = 5
        max_waiting_time = int(data['Waiting Time'].max())  # Convert to integer for range
        bins = range(0, max_waiting_time + bin_width, bin_width)
        data['Waiting Time Binned'] = pd.cut(data['Waiting Time'], bins=bins)

        # Count occurrences for each bin
        waiting_time_counts = data['Waiting Time Binned'].value_counts().sort_index()

        # Plot the data
        plt.figure(figsize=(12, 6))
        plt.bar(
            waiting_time_counts.index.astype(str),  # Convert bins to strings for better x-axis labeling
            waiting_time_counts.values,
            color="skyblue",
            edgecolor="black"
        )
        plt.title('Waiting Time vs. Number of People')
        plt.xlabel('Waiting Time (units)')
        plt.ylabel('Number of People')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)

        # Save the graph with tight layout
        plt.savefig(f'{graph_file_prefix}_waiting_time_vs_number_of_people_ranged.png', bbox_inches='tight')

        
        waiting_time_counts = data['Waiting Time'].value_counts().sort_index()
        plt.figure(figsize=(12, 6))
        plt.bar(waiting_time_counts.index, waiting_time_counts.values, color="skyblue", edgecolor="black")
        plt.title('Waiting Time vs. Number of People')
        plt.xlabel('Waiting Time (units)' )
        plt.ylabel('Number of People')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.savefig(f'{graph_file_prefix}_waiting_time_vs_number_of_people.png')

        # Create normalized histogram of Total Service Times
        plt.figure()
        plt.hist(data['Total Service Time'], bins="auto", density=True,color='orange', edgecolor='black', alpha=0.8)
        plt.title('Normalized Histogram of Total Service Times')
        plt.xlabel('Total Service Time (units)')
        plt.ylabel('Density (Probability per unit time)')
        plt.grid(True)
        plt.savefig(f'{graph_file_prefix}_normalized_histogram_total_service_times.png')

        heatmap_data = data.pivot_table(index='Passenger position', 
                                    columns='Passenger arrival time', 
                                    aggfunc='size', fill_value=0)
        plt.figure(figsize=(16, self.number_of_floors / 2))  # Dynamically adjust size based on number of floors
        sns.heatmap(heatmap_data, cmap='cividis', linewidths=0.5, linecolor='black', cbar_kws={'label': 'Number of Passengers'})
        plt.title('Heatmap of Passenger Arrivals', fontsize=16)
        plt.xlabel('Time (discrete units)', fontsize=14)
        plt.ylabel('Floors', fontsize=14)
        plt.tight_layout()
        # plt.show()
        plt.savefig(f'{graph_file_prefix}_heatmap_passenger_arrivals.png')

        # Scatter graph of Waiting Time for Each Passenger
        plt.figure()
        plt.scatter(data['Index'], non_negative_waiting_times,alpha=0.6, color="purple", edgecolor='black')
        plt.title('Waiting Time for Each Passenger')
        plt.xlabel('Passenger Index')
        plt.ylabel('Waiting Time (units)')
        plt.grid(True)
        plt.savefig(f'{graph_file_prefix}_waiting_time_each_passenger.png')
        
        # KDE plot of Waiting Times
        plt.figure()
        sns.kdeplot(non_negative_waiting_times, fill=True, color="blue")
        plt.title('KDE Plot of Waiting Times')
        plt.xlabel('Waiting Time (units)')
        plt.ylabel('Density (Probability per unit time)')
        plt.xlim(0,None)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f'{graph_file_prefix}_waiting_time_kde.png')
        
        
        heatmap_data = data.pivot_table(index='Passenger position', columns='Passenger arrival time', aggfunc='size', fill_value=0)
        plt.figure()
        plt.imshow(heatmap_data, aspect='auto', cmap='viridis', origin='lower')
        plt.colorbar(label='Number of Passengers')
        plt.title('Heatmap of Passenger Arrivals')
        plt.xlabel('Time (discrete units)')
        plt.ylabel('Floors')
        plt.grid(True)
        plt.savefig(f'{graph_file_prefix}_heatmap_passenger_arrivals_2.png')
        
        
        # Create normalized histogram of Waiting Times
        plt.figure()
        plt.hist(non_negative_waiting_times, bins='auto', density=True)
        plt.title('Normalized Histogram of Waiting Times')
        plt.xlabel('Waiting Time (units)')
        plt.ylabel('Density (Probability per unit time)')
        plt.grid(True)
        plt.savefig(f'{graph_file_prefix}_normalized_histogram_waiting_times_2.png')
        
        plt.figure()
        plt.hist(data['Total Service Time'], bins="auto", density=True)
        plt.title('Normalized Histogram of Total Service Times')
        plt.xlabel('Total Service Time (units)')
        plt.ylabel('Density (Probability per unit time)')
        plt.grid(True)
        plt.savefig(f'{graph_file_prefix}_normalized_histogram_total_service_times_2.png')

        plt.close("all")