import pandas as pd
import random
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns

'''This code is for generating a general poisson process '''
class PassengerDataGenerator:
    '''Class to generate passenger data for an elevator simulation using a Poisson process for arrival times'''
    
    def __init__(self, number_of_floors, file_path, current_time, time_interval, lambda_passenger):
        self.number_of_floors = number_of_floors
        self.file_path = file_path
        self.df = self.load_data()
        self.index = self.get_start_index()
        self.current_time = current_time
        self.time_interval = time_interval
        self.lambda_passenger = lambda_passenger  # Rate parameter for the Poisson process

    def load_data(self):
        '''Load passenger data from the CSV file or create an empty DataFrame if the file is not found'''
        try:
            return pd.read_csv(self.file_path)
        except FileNotFoundError:
            return pd.DataFrame()

    def get_start_index(self):
        '''Get the starting index for new passengers based on the existing data'''
        try:
            return self.df.iloc[-1]["Index"] + 1
        except IndexError:
            return 1

    def generate_passenger_data(self, duration):
        '''Generate passenger data using a Poisson process over a given duration'''
        current_time = self.current_time

        while current_time < self.current_time + duration:
            # Generate the number of passengers arriving in the current time unit
            num_passengers = np.random.poisson(self.lambda_passenger)

            for _ in range(num_passengers):
                # Randomly generate passenger's starting position and destination floor
                passenger_position, passenger_destination = random.sample(range(0, self.number_of_floors + 1), 2)

                # Create a dictionary for the new passenger data
                new_data = {
                    'Index': [self.index],
                    'Passenger position': [passenger_position],
                    'Passenger destination': [passenger_destination],
                    'Passenger arrival time': [round(current_time)],  # Round to the nearest integer
                    'Lift arrival time': [0],
                    'Order completion time': [0],
                    'direction': [-1 if passenger_position > passenger_destination else 1]
                }

                # Convert the dictionary to a DataFrame and concatenate with the existing data
                new_df = pd.DataFrame(new_data)
                self.df = pd.concat([self.df, new_df], ignore_index=True)

                # Increment the index for the next passenger
                self.index += 1

            # Move to the next time step using exponential inter-arrival time
            current_time += np.random.exponential(1 / self.lambda_passenger)

    def save_data(self):
        '''Save the generated passenger data to the CSV file'''
        self.df.to_csv(self.file_path, index=False)
        print(f"The Passenger data has been saved to {self.file_path}")

    def append_data(self):
        '''Append new passenger data to the existing CSV file'''
        self.df.to_csv(self.file_path, index=False, mode='a')


# # Example usage
if __name__ == "__main__":
    # Parameters for passenger data generation
    number_of_floors = 5
    file_path = 'passenger_data_general.csv'
    current_time = 0
    time_interval = 100  # Total time duration for which to generate data
    lambda_passenger = 0.5  # Average number of passengers arriving per time unit

    # Initialize the data generator
    generator = PassengerDataGenerator(number_of_floors, file_path, current_time, time_interval, lambda_passenger)

    # Generate passenger data for the given duration
    generator.generate_passenger_data(time_interval)
    # Save the generated data to a file (optional)
    generator.save_data()
