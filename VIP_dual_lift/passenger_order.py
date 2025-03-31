import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import expon

class PassengerDataGenerator:
    """Class to generate passenger data for an elevator simulation using Poisson processes for each floor."""
    
    def __init__(self, number_of_floors, file_path, current_time, lambda_passenger_per_floor):
        self.number_of_floors = number_of_floors
        self.file_path = file_path
        self.df = self.load_data()
        self.index = self.get_start_index()
        self.current_time = current_time
        self.lambda_passenger_per_floor = lambda_passenger_per_floor  # List of lambda values for each floor
        self.next_arrival_time = [self.current_time] * (self.number_of_floors + 1)  # Initialize next arrival time for each floor

    def load_data(self):
        """Load passenger data from the CSV file or create an empty DataFrame if the file is not found."""
        try:
            return pd.read_csv(self.file_path)
        except FileNotFoundError:
            return pd.DataFrame()

    def get_start_index(self):
        """Get the starting index for new passengers based on the existing data."""
        return self.df['Index'].max() + 1 if not self.df.empty else 1

    def generate_passenger_data(self, duration):
        """Generate passenger data over a given duration using Poisson processes."""
        end_time = self.current_time + duration

        while self.current_time < end_time:
            for floor in range(self.number_of_floors + 1):  # Iterate over each floor
                if self.current_time >= self.next_arrival_time[floor]:
                    num_passengers = 1  # Single event in the time interval
                    destination_floors = np.random.choice(
                        [f for f in range(self.number_of_floors + 1) if f != floor],
                        size=num_passengers
                    )
                    new_data = {
                        'Index': [self.index],
                        'Passenger position': [floor],
                        'Passenger destination': [destination_floors[0]],
                        'Passenger arrival time': [self.current_time],  # Avoid rounding
                        'Lift arrival time': [0],
                        'Order completion time': [0],
                        'direction': [-1 if floor > destination_floors[0] else 1]
                    }

                    self.df = pd.concat([self.df, pd.DataFrame(new_data)], ignore_index=True)
                    self.index += num_passengers

                    inter_arrival_time = np.random.exponential(1 / self.lambda_passenger_per_floor[floor])
                    self.next_arrival_time[floor] = self.current_time + inter_arrival_time

            self.current_time += 0.1  # Smaller time step for finer simulation

    def save_data(self):
        """Save the generated passenger data to the CSV file, sorted by Passenger arrival time."""
        self.df = self.df.sort_values(by='Passenger arrival time').reset_index(drop=True)
        self.df.to_csv(self.file_path, index=False)
        print(f"The passenger data has been saved to {self.file_path} in ascending order of arrival time.")

def analyze_inter_arrival_times(df, floor):
    """Analyze and print inter-arrival times for a specific floor."""
    floor_data = df[df['Passenger position'] == floor]
    arrival_times = floor_data['Passenger arrival time'].sort_values().values

    if len(arrival_times) > 1:
        inter_arrival_times = np.diff(arrival_times)
        print(f"Inter-Arrival Times for Floor {floor}: {inter_arrival_times[:10]} (first 10 values)")
        print(f"Mean Inter-Arrival Time: {np.mean(inter_arrival_times)}")
        print(f"Estimated Lambda (1/mean): {1 / np.mean(inter_arrival_times):.4f}")

def plot_inter_arrival_times(df, floor, input_lambda):
    """Plot observed inter-arrival times against the expected exponential distribution."""
    floor_data = df[df['Passenger position'] == floor]
    arrival_times = floor_data['Passenger arrival time'].sort_values().values

    if len(arrival_times) < 2:
        print(f"Not enough data for floor {floor}.")
        return

    inter_arrival_times = np.diff(arrival_times)
    estimated_lambda = 1 / np.mean(inter_arrival_times)

    plt.hist(inter_arrival_times, bins=30, density=True, alpha=0.6, label='Observed')

    x = np.linspace(0, max(inter_arrival_times), 1000)
    plt.plot(x, expon.pdf(x, scale=1 / input_lambda), 'r-', label=f'Expected (λ={input_lambda})')
    plt.plot(x, expon.pdf(x, scale=1 / estimated_lambda), 'g--', label=f'Fitted (λ={estimated_lambda:.2f})')

    plt.title(f"Floor {floor}: Inter-Arrival Times")
    plt.xlabel("Inter-Arrival Time")
    plt.ylabel("Density")
    plt.legend()
    plt.show()

def verify_poisson_process(file_path, lambda_passenger_per_floor):
    """Verify the Poisson process by fitting exponential distribution to inter-arrival times."""
    df = pd.read_csv(file_path)
    for floor in range(len(lambda_passenger_per_floor)):
        analyze_inter_arrival_times(df, floor)
        plot_inter_arrival_times(df, floor, lambda_passenger_per_floor[floor])

# # Example usage
# file_path = "refined_passenger_data.csv"
# lambda_passenger_per_floor = [0.5] * 6  # Example input lambda values for each floor

# # Generate passenger data
# generator = PassengerDataGenerator(
#     number_of_floors=5,
#     file_path=file_path,
#     current_time=0,
#     lambda_passenger_per_floor=lambda_passenger_per_floor
# )
# generator.generate_passenger_data(duration=36000)  # Generate data for 10 hours
# generator.save_data()

# # Verify the generated data
# verify_poisson_process(file_path, lambda_passenger_per_floor)
