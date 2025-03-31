import random
import numpy as np
import csv
import sys

class DualOscillation:
    '''This lift will be used when the density on each floor is high and similar.'''
    def __init__(self, current_floor_A, current_floor_B, num_floors, Passenger_limit, filepath, threshold_density, current_time, current_density, directionA=0, directionB=0, lowest_floor=0, delta_time=5):
        self.current_floor_A = current_floor_A
        self.current_floor_B = current_floor_B
        self.num_floors = num_floors
        self.direction_A = directionA
        self.direction_B = directionB
        self.lowest_floor = lowest_floor

        self.lift_A_Population = 0
        self.lift_B_Population = 0

        self.current_floor_lift_A = current_floor_A
        self.current_floor_lift_B = current_floor_B

        self.pending_orders = []
        self.already_picked_A = []
        self.already_picked_B = []
        self.orders_done = []

        self.current_time = current_time
        self.filepath = filepath
        self.Passenger_limit = Passenger_limit

        self.floor_time = 3
        self.threshold_density = threshold_density

        self.current_density = np.mean(current_density)
        print(f"Initial mean density: {self.current_density}")

        self.delta_time = delta_time

        self.time_elapsed = 0
        self.density_snapshots = []
        self.floor_passenger_count = [0] * (self.num_floors + 1)

    def move(self):
        self.current_floor_lift_A += self.direction_A
        print(f"Lift A is on floor {self.current_floor_lift_A}")
        self.current_floor_lift_B += self.direction_B
        print(f"Lift B is on floor {self.current_floor_lift_B}")

    def direction_decider(self):
        if self.current_floor_lift_A == self.lowest_floor:
            self.direction_A = 1
        elif self.current_floor_lift_A == self.num_floors:
            self.direction_A = -1

        if self.current_floor_lift_B == self.lowest_floor:
            self.direction_B = 1
        elif self.current_floor_lift_B == self.num_floors:
            self.direction_B = -1

    def serve_floor(self, passenger_data):
        copied_list = self.pending_orders.copy()
        already_picked = self.already_picked_A + self.already_picked_B
    
        for order in copied_list:
            Index, Passenger_position, Passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = order
            
            if (self.current_floor_lift_A == Passenger_destination and order in self.already_picked_A):
                print(f"Lift A is on floor {self.current_floor_lift_A} and dropped passenger {Index} at time {self.current_time}")
                self.pending_orders.remove(order)
                self.already_picked_A.remove(order)
                self.lift_A_Population -= 1

            if (self.current_floor_lift_A == Passenger_position and order not in already_picked and self.direction_A == direction):
                if self.lift_A_Population < self.Passenger_limit:
                    print(f"Lift A is on floor {self.current_floor_lift_A} to pick passenger {Index} at time {self.current_time}")
                    self.already_picked_A.append(order)
                    self.lift_A_Population += 1
                else:
                    self.pending_orders.remove(order)
                    passenger_data.append(order)
                    
            if (self.current_floor_lift_B == Passenger_destination and order in self.already_picked_B):
                print(f"Lift B is on floor {self.current_floor_lift_B} and dropped passenger {Index} at time {self.current_time}")
                self.pending_orders.remove(order)
                self.already_picked_B.remove(order)
                self.lift_B_Population -= 1

            if (self.current_floor_lift_B == Passenger_position and order not in already_picked and self.direction_B == direction):
                if self.lift_B_Population < self.Passenger_limit:
                    print(f"Lift B is on floor {self.current_floor_lift_B} to pick passenger {Index} at time {self.current_time}")
                    self.already_picked_B.append(order)
                    self.lift_B_Population += 1
                else:
                    self.pending_orders.remove(order)
                    passenger_data.append(order)
        return passenger_data

    def update_densities(self):
        densities = [count / self.delta_time for count in self.floor_passenger_count]
        self.density_snapshots.append({"time": self.current_time, "densities": densities})
        print(f"Density snapshot at time {self.current_time}: {densities}")
        self.floor_passenger_count = [0] * (self.num_floors + 1)
        return densities

    def save_densities_to_file(self, output_filepath):
        with open(output_filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            header = ["Time"] + [f"Floor_{i}" for i in range(self.num_floors + 1)]
            writer.writerow(header)

            for snapshot in self.density_snapshots:
                row = [snapshot["time"]] + snapshot["densities"]
                writer.writerow(row)
        print(f"Density snapshots saved to {output_filepath}")

    def run_simulation(self, passenger_data, output_filepath="density_snapshots.csv"):
        passenger_data = sorted(passenger_data, key=lambda x: x[3])

        while self.threshold_density < self.current_density:
            while (self.current_floor_A != 0 and self.current_floor_B != self.num_floors) or (self.current_floor_A != self.num_floors and self.current_floor_B != 0):
                if (self.num_floors - self.current_floor_A) < self.current_floor_B:
                    self.direction_A = 1 if self.current_floor_A != self.num_floors else 0
                    self.direction_B = -1 if self.current_floor_B != 0 else 0
                else:
                    self.direction_A = -1 if self.current_floor_A != 0 else 0
                    self.direction_B = 1 if self.current_floor_B != self.num_floors else 0

                for p in passenger_data:
                    if p[3] <= self.current_time:
                        self.pending_orders.append(p)
                        passenger_data.remove(p)
                        floor = p[1]
                        self.floor_passenger_count[floor] += 1

                if self.pending_orders:
                    passenger_data = self.serve_floor(passenger_data)

                self.time_elapsed += self.floor_time
                if self.time_elapsed >= self.delta_time:
                    densities = self.update_densities()
                    self.current_density = np.mean(densities)
                    self.time_elapsed = 0

                self.move()
                self.direction_decider()
                self.current_time += self.floor_time

            self.direction_decider()
            for p in passenger_data:
                if p[3] <= self.current_time:
                    self.pending_orders.append(p)
                    passenger_data.remove(p)
                    floor = p[1]
                    self.floor_passenger_count[floor] += 1

            print(f"Current Time: {self.current_time}")

            if self.pending_orders:
                passenger_data = self.serve_floor(passenger_data)

            self.time_elapsed += self.floor_time
            if self.time_elapsed >= self.delta_time:
                densities = self.update_densities()
                self.current_density = np.mean(densities)
                self.time_elapsed = 0

            self.move()
            self.direction_decider()
            self.current_time += self.floor_time

            if (self.current_floor_lift_A > self.num_floors or self.current_floor_lift_A < self.lowest_floor or 
                self.current_floor_lift_B > self.num_floors or self.current_floor_lift_B < self.lowest_floor):
                print("There has been an error in the Oscillation code")
                break

        self.save_densities_to_file(output_filepath)
        return passenger_data
    
    