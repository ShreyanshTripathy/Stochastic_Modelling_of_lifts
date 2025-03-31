import pandas as pd
import numpy as np
import csv
import sys
import time

class DualOscillation:
    '''This lift will be used when the density on each floor is high and similar.'''
    def __init__(self, current_floor_A, current_floor_B, num_floors, Passenger_limit, filepath, threshold_density_high,threshold_density_low ,floor_time,current_time, current_density, directionA=0, directionB=0, lowest_floor=0, delta_time=5):
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

        self.floor_time = floor_time
        self.threshold_density_high = threshold_density_high
        self.threshold_density_low = threshold_density_low

        # Take the mean of current_density (which is now a list)
        self.current_density = current_density
        print(f"Initial mean density: {self.current_density}")

        self.delta_time = delta_time
        
        self.df = pd.read_csv(filepath)

        # New variables for tracking densities
        self.time_elapsed = 0
        self.density_snapshots = []  # To store densities over time
        self.floor_passenger_count = [0] * (self.num_floors + 1)  # Tracks passengers on each floor
        
        self.t_persistence = 10  # Minimum time density must persist before switching (adjust as needed)
        self.time_above_threshold = 0  # Tracks time above a threshold
        self.time_below_threshold = 0  # Tracks time below a threshold
        
        self.picking = True
        

    def move(self):
        self.current_floor_lift_A += self.direction_A
        print(f"Lift position A: {self.current_floor_lift_A}")
        self.current_floor_lift_B += self.direction_B
        print(f"Lift position B: {self.current_floor_lift_B}")
        print(np.mean(self.current_density))

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
            
            # Check for Lift A
            if (self.current_floor_lift_A == Passenger_destination and order in self.already_picked_A):
                
                Dropping_Passenger = {
                    "Lift ID": "Lift A",
                    "Name": Index,
                    "Current floor": Passenger_position,
                    "Destination_floor": Passenger_destination,
                    "Time": self.current_time,
                    "Status": "Dropping"
                }

                print(f"DROPPING:\n\n{Dropping_Passenger}\n")
                
                self.pending_orders.remove(order)
                self.already_picked_A.remove(order)
                self.df.loc[self.df["Index"] == Index, "Order completion time"] = self.current_time
                updated_tuple = self.df.loc[self.df["Index"] == Index].iloc[0]
                updated_tuple = tuple(updated_tuple)
                self.orders_done.append(updated_tuple)
                self.lift_A_Population-=1


            if (self.current_floor_lift_A == Passenger_position and order not in already_picked and self.direction_A == direction) and self.picking:
                if self.lift_A_Population<self.Passenger_limit:
                    
                    picking_passenger = {
                    "Lift ID": "Lift A",
                    "Name": Index,
                    "Current floor": Passenger_position,
                    "Destination_floor": Passenger_destination,
                    "Time": self.current_time,
                    "Status": "Picking"
                    }
                    print(f"PICKING:\n\n{picking_passenger}\n")
                    
                    self.df.loc[self.df["Index"] == Index, "Lift arrival time"] = self.current_time
                
                    self.already_picked_A.append(order)
                    self.lift_A_Population+=1
                    self.floor_passenger_count[Passenger_position] -= 1
                else:
                    self.pending_orders.remove(order)
                    passenger_data.append(order)
                    
                
            # Check for Lift B
            if (self.current_floor_lift_B == Passenger_destination and order in self.already_picked_B):
                
                Dropping_Passenger = {
                    "Lift ID": "Lift A",
                    "Name": Index,
                    "Current floor": Passenger_position,
                    "Destination_floor": Passenger_destination,
                    "Time": self.current_time,
                    "Status": "Dropping"
                }

                print(f"DROPPING:\n\n{Dropping_Passenger}\n")
                
                self.pending_orders.remove(order)
                self.already_picked_B.remove(order)
                self.lift_B_Population-=1

                self.df.loc[self.df["Index"] == Index, "Order completion time"] = self.current_time
                updated_tuple = self.df.loc[self.df["Index"] == Index].iloc[0]
                updated_tuple = tuple(updated_tuple)
                self.orders_done.append(updated_tuple)
                self.df.to_csv(self.filepath, index=False)

            if (self.current_floor_lift_B == Passenger_position and order not in already_picked and self.direction_B == direction) and self.picking:
                if self.lift_B_Population<self.Passenger_limit:
                    
                    picking_passenger = {
                    "Lift ID": "Lift B",
                    "Name": Index,
                    "Current floor": Passenger_position,
                    "Destination_floor": Passenger_destination,
                    "Time": self.current_time,
                    "Status": "Picking"
                    }
                    print(f"PICKING:\n\n{picking_passenger}\n")
                    
                    self.df.loc[self.df["Index"] == Index, "Lift arrival time"] = self.current_time

                    self.already_picked_B.append(order)
                    self.lift_B_Population+=1
                    self.floor_passenger_count[Passenger_position] -= 1
                else:
                    self.pending_orders.remove(order)
                    passenger_data.append(order)
        return passenger_data

    def update_densities(self):
        densities = [count / self.delta_time for count in self.floor_passenger_count]
        self.density_snapshots.append({"time": self.current_time, "densities": densities})
        print(f"Density snapshot at time {self.current_time}: {densities}")
        
        mean_density = np.mean(densities)
        
        # self.floor_passenger_count = [0] * (self.num_floors + 1)
        return densities

    def run_simulation(self, passenger_data):
        passenger_data = sorted(passenger_data, key=lambda x: x[3])
        print("We are in oscillation")
        passenger_arrived = []
        if self.threshold_density_low < np.mean(self.current_density) and self.time_below_threshold <= self.t_persistence:
            #deciding the direction for each lift
            if self.current_floor_lift_A > self.current_floor_lift_B:
                    self.direction_A = 1 if self.current_floor_lift_A != self.num_floors else 0
                    self.direction_B = -1 if self.current_floor_lift_B != 0 else 0
            elif self.current_floor_lift_A < self.current_floor_lift_B:
                self.direction_A = -1 if self.current_floor_lift_A != 0 else 0
                self.direction_B = 1 if self.current_floor_lift_B != self.num_floors else 0
            elif (self.current_floor_lift_A) == self.current_floor_lift_B:
                if self.current_floor_lift_A==0:
                    self.direction_A = 0
                    self.direction_B = 1
                elif self.current_floor_lift_A==self.num_floors:
                    self.direction_A = -1
                    self.direction_B = 0
                else:
                    self.direction_A = 1
                    self.direction_B = -1
                    
            # we get the lifts to the starting point while serving people
            returning = False
            while ((self.current_floor_lift_A != 0 and self.current_floor_lift_B != self.num_floors) or (self.current_floor_lift_A != self.num_floors and self.current_floor_lift_B != 0) or (self.current_floor_lift_A==self.current_floor_lift_B)) and (not returning):
                
                print(self.current_floor_lift_A)
                print(self.current_floor_lift_B) 
                if self.current_floor_lift_A==self.num_floors or self.current_floor_lift_A==0:
                    self.direction_A=0
                elif self.current_floor_lift_B==self.num_floors or self.current_floor_lift_B==0:
                    self.direction_B=0
                if (self.current_floor_lift_A) == self.current_floor_lift_B:
                    if self.current_floor_lift_A==0:
                        self.direction_A = 0
                        self.direction_B = 1
                    elif self.current_floor_lift_A==self.num_floors:
                        self.direction_A = -1
                        self.direction_B = 0
                    else:
                        self.direction_A = 1
                        self.direction_B = -1
                    
                if self.picking:
                    for p in passenger_data:
                        if p[3] <= self.current_time:
                            self.pending_orders.append(p)
                            passenger_data.remove(p)
                            if p not in passenger_arrived:
                                passenger_arrived.append(p)
                                floor = p[1]
                                self.floor_passenger_count[floor] += 1

                    if self.time_elapsed >= self.delta_time:
                        self.current_density = self.update_densities()
                        self.time_elapsed = 0              
                
                if self.pending_orders:
                    passenger_data = self.serve_floor(passenger_data)

                self.move()
                self.current_time += self.floor_time
                self.time_elapsed += self.floor_time
                
                if (self.current_floor_lift_A==self.num_floors and self.current_floor_lift_B==0) or (self.current_floor_lift_A==0 and self.current_floor_lift_B==self.num_floors):
                    print("They are at the two ends")
                    returning=True
                    
                if self.threshold_density_low >= np.mean(self.current_density):
                    self.picking = False
                    self.time_below_threshold += self.floor_time
                    if  self.time_below_threshold >= self.t_persistence:
                        returning = True
                        self.time_below_threshold = 0
            #The lifts are at either ends now...there are tww possibilities they have served enough to get the density down or they have not if they have then we just need to make the population 0 if not then we move to serving
            print(np.mean(self.current_density))
            print(self.picking)
            print(returning)
            
            if np.mean(self.current_density) <= self.threshold_density_low:
                self.picking = False
            else:
                self.picking = True
            if np.mean(self.current_density) <= self.threshold_density_low and self.time_below_threshold >= self.t_persistence and  self.lift_A_Population==0 and self.lift_B_Population==0:
                returning = True                
            else:
                returning = True                
            # while self.threshold_density_low < np.mean(self.current_density) and self.time_below_threshold <= self.t_persistence or (self.lift_A_Population!=0 and self.lift_B_Population!=0):
            while not returning:
                self.direction_decider()
                if self.picking:
                    for p in passenger_data:
                        if p[3] <= self.current_time:
                            self.pending_orders.append(p)
                            passenger_data.remove(p)
                            floor = p[1]
                            self.floor_passenger_count[floor] += 1

                
                    if self.time_elapsed >= self.delta_time:
                        densities = self.update_densities()
                        self.current_density = np.mean(densities)
                        self.time_elapsed = 0
                
                
                if self.pending_orders:
                    passenger_data = self.serve_floor(passenger_data)
                    

                self.move()
                self.direction_decider()
                self.current_time += self.floor_time
                self.time_elapsed += self.floor_time
                
                if np.mean(self.current_density) <= self.threshold_density_low:
                    print(f"Current density = {self.current_density}. Switching to Oscillation")
                    print("Turning off picking...")
                    self.picking = False
                    self.time_below_threshold += self.floor_time                                          
                    
                    if self.time_below_threshold >= self.t_persistence and self.lift_A_Population==0 and self.lift_B_Population==0:
                        returning = True
                        self.time_below_threshold = 0

                if (self.current_floor_lift_A > self.num_floors or self.current_floor_lift_A < self.lowest_floor or 
                    self.current_floor_lift_B > self.num_floors or self.current_floor_lift_B < self.lowest_floor):
                    print("There has been an error in the Oscillation code")
                    break
                print(f"Current Time: {self.current_time}")
        return passenger_data    


