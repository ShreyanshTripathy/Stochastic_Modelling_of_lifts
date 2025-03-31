import pandas as pd
import numpy as np
import random
import csv
class VIPLiftSystem:
    '''This elevator is trying to simulate the real life situation of passengers arriving at varied times'''

    def __init__(self, current_floor, num_floors, current_time, filepath, Passenger_limit, floor_to_Serve,delta_time,threshold_density,current_density):
        # Initialize the elevator state and load the passenger data from a CSV file
        self.current_floor = current_floor
        self.direction = 0  # 1 for up, -1 for down
        self.num_floors = num_floors
        self.pending_orders = []
        self.orders_in_opposite_direction = []
        self.already_picked = []
        self.passengers_in_lift = []
        self.orders_not_served = []
        self.filepath = filepath
        # self.df_read = pd.read_csv(filepath)
        self.current_time = current_time
        self.orders_done = []
        self.passenger_limit = Passenger_limit
        self.lift_population = 0
        
        #adding variation in time
        self.floor_time = 1
        self.passenger_inout = 3
        
        self.floor_to_Serve = floor_to_Serve
        self.others = []
        
        self.threshold_density = threshold_density
        self.time_elapsed = 0
        self.density_snapshots = []  # To store densities over time
        self.floor_passenger_count = [0] * (self.num_floors + 1)
        self.current_density = np.mean(current_density)
        print(f"Initial mean density: {self.current_density}")
        self.delta_time = delta_time

    def move(self):
        '''Function to move the elevator'''
        if self.current_floor==self.num_floors:
            self.direction=-1
        elif self.current_floor==0:
            self.direction=1
        self.current_floor += self.direction
        # print(f"The lift is on floor {self.current_floor}")
        print(f"Lift position: {self.current_floor}")

    def add_stop(self, passenger_data):
        '''
        Function to add stop to the lift queue if its efficient to do so.
        If the direction the passenger wants to go is opposite to the direction of the lift
        then the passenger will not be appended. Also, if the passenger is going in the same
        direction but his or her floor has already been crossed then he or she will not be
        added and will have to wait for the lift to change directions to come and get them later.
        '''
        if self.direction == 1 and (passenger_data[2] - passenger_data[1]) > 0 and self.current_floor <= passenger_data[1]:
            if passenger_data not in self.pending_orders:
                self.pending_orders.append(passenger_data)
        elif self.direction == -1 and (passenger_data[2] - passenger_data[1]) < 0 and self.current_floor >= passenger_data[1]:
            if passenger_data not in self.pending_orders:
                self.pending_orders.append(passenger_data)
        else:
            if passenger_data not in self.orders_in_opposite_direction:
                self.orders_in_opposite_direction.append(passenger_data)

    def data_sorter(self, passenger_data, lift_postion):
        '''
        Function to sort passenger data based on their arrival time and the distance
        from the current lift position.
        '''
        # Initialize an empty dictionary to hold the grouped tuples
        grouped_by_index_3 = {}

        # Iterate over each tuple in the data
        for item in passenger_data:
            # Get the value at the fourth index (index 3)
            key = item[3]

            # Add the item to the corresponding list in the dictionary
            grouped_by_index_3.setdefault(key, []).append(item)

        sorted_data = []

        # Iterate over the groups in the dictionary
        for group in grouped_by_index_3.values():
            # Sort each group based on the absolute difference between the second index value (index 1) and the given position
            sorted_group = sorted(group, key=lambda x: abs(x[1] - lift_postion))
            # Extend the sorted_data list with the sorted group
            sorted_data.extend(sorted_group)

        return sorted_data

    def serve_stop(self):
        '''This function picks and drops the passenger based on the pending order list'''
        copy_list = self.pending_orders.copy()
        eligible_orders = []

        for order in copy_list:
            dont_pick = False
            Index, passenger_position, passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = order

            self.drop_passenger(order)

            dont_pick = self.check_direction_conflict(order, copy_list, direction)

            eligible_orders = self.Passengers_on_same_floor(order, dont_pick,eligible_orders)
        
        self.pick_passenger(eligible_orders)
    
    def drop_passenger(self, order):
        '''Drop passengers if the current floor matches their destination'''
        Index, passenger_position, passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = order

        try:
            if self.current_floor == passenger_destination and (order in self.already_picked):
                self.pending_orders.remove(order)
                if order in self.orders_not_served:
                    self.orders_not_served.remove(order)
                # print(f"The lift is on floor {self.current_floor} and a passenger ID {Index} is dropped at time {self.current_time}")
                Dropping_Passenger = {
                    "Name": Index,
                    "Current floor": passenger_position,
                    "Destination_floor": passenger_destination,
                    "Time": self.current_time,
                    "Status": "Dropping"
                }
                print(f"DROPPING:\n\n{Dropping_Passenger}\n")
                
                self.current_time+=self.passenger_inout
                self.passengers_in_lift.remove(order)
                self.lift_population-=1
    
                # 
                # Update the DataFrame
                # self.df_read.loc[self.df_read["Index"] == Index, "Order completion time"] = self.current_time

                # # Extract the updated tuple
                # updated_tuple = self.df_read.loc[self.df_read["Index"] == Index].iloc[0]
                # updated_tuple = tuple(updated_tuple)
                # self.orders_done.append(updated_tuple)
                # print(f"update_line: {updated_tuple}")
                # # Reload the DataFrame to reflect the changes
                # self.df_read = pd.read_csv(self.filepath)
                # 
                for orders in self.orders_not_served:
                    if ((min(self.orders_not_served, key=lambda x: x[1])[1] <= self.current_floor and self.direction > 0) or (max(self.orders_not_served, key=lambda x: x[1])[1] >= self.current_floor and self.direction < 0)) and not ((any(tup[-1]==-1 for tup in self.passengers_in_lift) and self.direction==-1) or (any(tup[-1]==1 for tup in self.passengers_in_lift) and self.direction==1)):
                        self.direction = orders[-1]

        except IndexError:
            pass

    def check_direction_conflict(self, order, copy_list, direction):
        '''Check if there is a conflict in the direction and decide not to pick up the passenger'''
        dont_pick = False

        if (min(copy_list, key=lambda x: x[1])[1] < self.current_floor and self.direction < 0 and direction > 0) or (max(copy_list, key=lambda x: x[1])[1] > self.current_floor and self.direction > 0 and direction < 0):
            dont_pick = True
            if order not in self.orders_not_served and order not in self.already_picked:
                self.orders_not_served.append(order)

        if self.direction > 0 and direction < 0:
            if any(tup[2] > self.current_floor for tup in copy_list):
                dont_pick = True
        elif self.direction < 0 and direction > 0:
            if any(tup[2] < self.current_floor for tup in copy_list):
                dont_pick = True
                
        
                

        return dont_pick

    def Passengers_on_same_floor(self, order, dont_pick, eligible_orders):
        '''Pick up the passenger if conditions are met'''
        Index, passenger_position, passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = order

        if self.current_floor == passenger_position and not dont_pick:
            if order not in self.already_picked and order not in eligible_orders:
                eligible_orders.append(order)
                

        # Additional condition to ensure Lift arrival time is updated correctly
        if self.current_floor == passenger_position and (((passenger_position == min(self.pending_orders, key=lambda x: x[1])[1]) and (self.direction == direction)) or ((passenger_position == max(self.pending_orders, key=lambda x: x[1])[1]) and (self.direction == direction))):
            if order not in self.already_picked and order not in eligible_orders:
                eligible_orders.append(order)
        
        return eligible_orders
                
    def pick_passenger(self, eligible_orders):
        if eligible_orders:
            # Calculate available space in the lift
            once = False
            available_space = self.passenger_limit - self.lift_population
            Orders_tobe_picked = []
            Orders_not_picked = []
            if len(eligible_orders) > available_space:
                # Pick only the number of passengers that can be accommodated
                Orders_tobe_picked = random.sample(eligible_orders, available_space)
                for orders in eligible_orders:
                    if orders not in Orders_tobe_picked:
                        Orders_not_picked.append(orders)
                
            else:
                Orders_tobe_picked = eligible_orders[:]

            for order in Orders_tobe_picked:
                Index, passenger_position, passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = order

                # print(f"The Lift is on floor {self.current_floor} to pick up passenger {Index} going to floor {passenger_destination} at time {self.current_time}")
                picking_passenger = {
                    "Name": Index,
                    "Current floor": passenger_position,
                    "Destination_floor": passenger_destination,
                    "Time": self.current_time,
                    "Status": "Picking"
                }
                print(f"PICKING:\n\n{picking_passenger}\n")
                
                self.current_time+=self.passenger_inout
                
                self.passengers_in_lift.append(order)
                self.lift_population += 1
                # 
                # Update the DataFrame with the new value
                # self.df_read.loc[self.df_read["Index"] == Index, "Lift arrival time"] = self.current_time
                # # Reload the DataFrame to reflect the changes
                # self.df_read.to_csv(self.filepath, index=False)  # Ensure you save the changes to the file
                # 
                self.already_picked.append(order)
                if not once:
                    self.direction = direction
                    once = True  # Set once to True after updating the direction
                
                if self.current_floor == passenger_position and (((passenger_position == min(self.pending_orders, key=lambda x: x[1])[1]) and (self.direction == direction)) or ((passenger_position == max(self.pending_orders, key=lambda x: x[1])[1]) and (self.direction == direction))):
                    
                    self.direction=direction    

    def update_densities(self):
        """Update densities on each floor every delta_time seconds."""
        densities = [count / self.delta_time for count in self.floor_passenger_count]
        self.density_snapshots.append({"time": self.current_time, "densities": densities})
        print(f"Density snapshot at time {self.current_time}: {densities}")
        self.floor_passenger_count = [0] * (self.num_floors + 1)
        return densities# Reset for next interval

    def save_densities_to_file(self, output_filepath):
        """Save density snapshots to a CSV file."""
        with open(output_filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            header = ["Time"] + [f"Floor_{i}" for i in range(self.num_floors + 1)]
            writer.writerow(header)

            for snapshot in self.density_snapshots:
                row = [snapshot["time"]] + snapshot["densities"]
                writer.writerow(row)
        print(f"Density snapshots saved to {output_filepath}")
        
    def run_simulation(self, passenger_data,output_filepath="density_snapshots.csv"):
        '''This simulates the lift'''
        passenger_data = self.data_sorter(passenger_data, self.current_floor)
        started = False
        while self.threshold_density < self.current_density:
            # Add pending stops for new passengers
            pending_orders_1 = []
            pending_orders_1 = [p for p in passenger_data if p[3] <= self.current_time]
            pending_orders = []
            for orders in pending_orders_1.copy():
                if orders[1]==self.floor_to_Serve or orders[2]==self.floor_to_Serve:
                    pending_orders.append(orders)
                else:
                    self.others.append(orders)
                    passenger_data.remove(orders)
                     
            
            pending_orders = self.data_sorter(pending_orders, self.current_floor)
            pending_orders = sorted(pending_orders, key=lambda x: x[3])
            
                   
            
            if pending_orders:
                for order in pending_orders:
                    passenger_data.remove(order)
                    if order[1] > self.current_floor and not started:
                        self.direction = 1
                    elif order[1] < self.current_floor and not started:
                        self.direction = -1
                    elif order[1] == self.current_floor and not started:
                        self.direction = order[-1]

                    if order[1] > self.current_floor and order[-1] < 0 and self.direction == 1 and not started:
                        self.direction = 1
                        for j in pending_orders:
                            if j[-1] == -1 and j[1] > self.current_floor:
                                self.pending_orders.append(j)
                            elif j[-1] == 1 and j[1] == self.current_floor:
                                self.pending_orders.append(j)

                        going_up_to_come_down = True
                    elif order[1] < self.current_floor and order[-1] > 0 and self.direction == -1 and not started:
                        self.direction = -1
                        for j in pending_orders:
                            if j[-1] == 1 and j[1] < self.current_floor:
                                self.pending_orders.append(j)
                            elif j[-1] == 1 and j[1] == self.current_floor:
                                self.pending_orders.append(j)
                        going_down_to_come_up = True

                    if order[1] < self.current_floor and self.direction > 0 and order[-1] < 0 and going_up_to_come_down:
                        self.pending_orders.append(order)

                    elif order[1] > self.current_floor and self.direction < 0 and order[-1] > 0 and going_down_to_come_up:
                        self.pending_orders.append(order)

                    started = True

                going_up_to_come_down = False
                going_down_to_come_up = False
                for order in self.pending_orders:
                    if order in passenger_data:
                        passenger_data.remove(order)
                    if order in pending_orders:
                        pending_orders.remove(order)

                for order in pending_orders:
                    self.add_stop(passenger_data=order)
                    if self.orders_in_opposite_direction:
                        opp_order = self.orders_in_opposite_direction.pop(0)
                        if opp_order not in passenger_data:
                            passenger_data.append(opp_order)

            # Remove duplicates from pending orders and passenger data
            seen = set()
            self.pending_orders = [x for x in self.pending_orders if not (x in seen or seen.add(x))]
            passenger_data = [x for x in passenger_data if not (x in seen or seen.add(x))]
            self.pending_orders = sorted(self.pending_orders, key=lambda x: abs(x[1] - self.current_floor), reverse=False if self.direction < 0 else True)

            # Move the lift if there are still pending orders
            if self.pending_orders:
                self.serve_stop()

            if self.pending_orders:
                self.move()

            # Stop simulation if lift goes out of bounds
            if self.current_floor > self.num_floors or self.current_floor < 0:
                print("There was an error")
                raise Exception("There is an Error")

            self.current_time += self.floor_time
            
            self.time_elapsed += self.floor_time
            if self.time_elapsed >= self.delta_time:
                desities = self.update_densities()
                self.current_density = np.mean(desities)
                self.time_elapsed = 0
            
            if self.pending_orders:
                self.serve_stop()

            self.time_elapsed += self.floor_time
            if self.time_elapsed >= self.delta_time:
                desities = self.update_densities()
                self.current_density = np.mean(desities)
                self.time_elapsed = 0
                
            if (not self.pending_orders):
                started = False
                
            if self.lift_population==0 and self.pending_orders and not passenger_data:
                for order in self.pending_orders:
                    passenger_data.append(order)
                    
            print(len(self.passengers_in_lift))
        self.save_densities_to_file(output_filepath)
        return passenger_data
            
            
elevator = VIPLiftSystem(current_floor=0, num_floors=5, current_time=0, filepath="dummy", Passenger_limit=8, floor_to_Serve=3,threshold_density=0.01, current_density=[0.1]*6,delta_time=5)
passenger_data = [(1, 0, 4, 0, 0, 0, 1), (2, 1, 0, 0, 0, 0, -1), (3, 2, 3, 0, 0, 0, 1), (4, 3, 1, 0, 0, 0, -1), (5, 4, 0, 0, 0, 0, -1), (6, 5, 2, 0, 0, 0, -1), (7, 3, 0, 4, 0, 0, -1), (8, 1, 2, 16, 0, 0, 1), (9, 5, 3, 21, 0, 0, -1)]
remaining_passenger = elevator.run_simulation(passenger_data)
print(elevator.orders_done)
print(elevator.others)
print(remaining_passenger)

