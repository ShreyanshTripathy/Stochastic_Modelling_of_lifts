import random
import numpy as np
import pandas as pd
import sys
class VIPDualSystem:

    '''This elevator is trying to simulate the real life situation of passengers arriving at varied times'''

    def __init__(self, current_floor_A,current_floor_B, num_floors,filepath, Passenger_limit,delta_time,threshold_density_high,threshold_density_low,current_density,floor_time,passenger_inout, current_time = 0):
        # Initialize the elevator state and load the passenger data from a CSV file
        self.num_floors = num_floors
        self.orders_in_opposite_direction = []
        self.already_picked = [] #list of passengers that have been picked
        self.orders_not_served = [] #these are the orders that were not done because there was some order to be completed right above it or below depending on the direction
        self.filepath = filepath
        self.df_read = pd.read_csv(filepath)
        self.current_time = current_time
        self.orders_done = [] #list of passengers whose order is completed
        self.passenger_limit = Passenger_limit
        
        #adding variation in time
        self.floor_time = floor_time
        self.passenger_inout = passenger_inout
        
        #Lift A
        self.current_floor_A = current_floor_A
        self.direction_A = 0  # 1 for up, -1 for down
        self.passengers_in_lift_A = []#list of passengers in the lift A
        self.lift_A_population = 0
        self.pending_orders_A = [] #list of passengers whose orders are still incomplete
        self.status_A = False #false for not moving and true for moving
        
        #Lift B
        self.current_floor_B = current_floor_B
        self.direction_B = 0  # 1 for up, -1 for down
        self.passengers_in_lift_B = []#list of passengers in the lift A
        self.lift_B_population = 0
        self.pending_orders_B = [] #list of passengers whose orders are still incomplete
        self.status_B = False #false for not moving and true for moving
        
        self.floor_to_serve = max(enumerate(current_density), key=lambda x: x[1])[0]
        self.threshold_density_high = threshold_density_high
        self.threshold_density_low = threshold_density_low

        self.time_elapsed = 0
        self.density_snapshots = []  # To store densities over time
        self.floor_passenger_count = [0] * (self.num_floors + 1)
        self.current_density = current_density
        print(f"Initial  density of floor {self.floor_to_serve}: {self.current_density}")
        self.delta_time = delta_time
        
        self.t_persistence = 10  # Minimum time density must persist before switching (adjust as needed)
        self.time_above_threshold = 0  # Tracks time above a threshold
        self.time_below_threshold = 0  # Tracks time below a threshold
        
        self.picking = True
        

    def move(self, lift_name):
        '''Function to move the elevator'''
        if self.pending_orders_A:
            if self.current_floor_A==0:
                self.direction_A=1
            elif self.current_floor_A==self.num_floors:
                self.direction_A=-1
                
        if self.pending_orders_B:
            if self.current_floor_B==0:
                self.direction_B=1
            elif self.current_floor_B==self.num_floors:
                self.direction_B=-1
        
        if lift_name=="A" and self.pending_orders_A==[]:
            self.direction_A=0
        if lift_name=="B" and self.pending_orders_B==[]:
            self.direction_B=0
        
        if lift_name=="A":
            self.current_floor_A += self.direction_A
            
            print(f"Lift position A: {self.current_floor_A}")
            
        else:
            self.current_floor_B += self.direction_B
            
            print(f"Lift position B: {self.current_floor_B}")

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

    def serve_stop(self,lift_name, passenger_data):
        '''This function picks and drops the passenger based on the pending order list'''
        if lift_name=="A":
            copy_list = self.pending_orders_A.copy()
        else:
            copy_list = self.pending_orders_B.copy()
        eligible_orders = []
        dropped = 0
        for order in copy_list:
            dont_pick = False
            direction = order[-1]

            dropped += self.drop_passenger(order,lift_name)
            
            if self.picking:
                dont_pick = self.check_direction_conflict(order, copy_list, direction,lift_name)

                eligible_orders= self.Passengers_on_same_floor(order, dont_pick,eligible_orders,lift_name)
        if self.picking:
            passenger_data, number_picked = self.pick_passenger(eligible_orders,lift_name, passenger_data)
        else:
            number_picked = 0
        return passenger_data, number_picked, dropped
    
    def drop_passenger(self, order, lift_name):
        """Drop passengers if the current floor matches their destination"""
        (Index, passenger_position, passenger_destination, 
        Passenger_arrival_time, Lift_arrival_time, 
        Order_completion_time, direction) = order

        current_floor = self.current_floor_A if lift_name == "A" else self.current_floor_B
        lift_direction = self.direction_A if lift_name == "A" else self.direction_B

        try:
            if current_floor == passenger_destination and (order in self.already_picked):
                self.already_picked.remove(order)
                # Remove order from pending orders based on the lift name
                if lift_name == "A":
                    self.pending_orders_A.remove(order)
                else:
                    self.pending_orders_B.remove(order)

                # Remove order from unserved orders
                if order in self.orders_not_served:
                    self.orders_not_served.remove(order)

                # Log the dropping passenger details
                Dropping_Passenger = {
                    "Lift ID": lift_name,
                    "Name": Index,
                    "Current floor": passenger_position,
                    "Destination_floor": passenger_destination,
                    "Time": self.current_time,
                    "Status": "Dropping"
                }

                print(f"DROPPING:\n\n{Dropping_Passenger}\n")

                # Update lift population and remove passenger from the lift
                if lift_name == "A":
                    self.passengers_in_lift_A.remove(order)
                    self.lift_A_population -= 1
                else:
                    self.passengers_in_lift_B.remove(order)
                    self.lift_B_population -= 1
                
                # Update the DataFrame
                self.df_read.loc[self.df_read["Index"] == Index, "Order completion time"] = self.current_time

                # Extract the updated tuple
                updated_tuple = self.df_read.loc[self.df_read["Index"] == Index].iloc[0]
                
                updated_tuple = tuple(updated_tuple)
                
                self.orders_done.append(updated_tuple)
                
                print(f"update_line: {updated_tuple}")
                
                # Reload the DataFrame to reflect the changes
                
                self.df_read = pd.read_csv(self.filepath)
            
                '''for orders in self.orders_not_served:
                    passengers_in_lift = self.passengers_in_lift_A if lift_name=="A" else self.passengers_in_lift_B
                    
                    if ((min(self.orders_not_served, key=lambda x: x[1])[1] <= current_floor and lift_direction > 0) or (max(self.orders_not_served, key=lambda x: x[1])[1] >= current_floor and lift_direction < 0)) and not ((any(tup[-1]==-1 for tup in passengers_in_lift) and lift_direction==-1) or (any(tup[-1]==1 for tup in passengers_in_lift) and lift_direction==1)):
                        
                        if lift_name == "A":
                            self.direction_A = orders[-1]
                        else:
                            self.direction_B = order[-1]'''

                return 1
        except IndexError:
            pass

        return 0

    def check_direction_conflict(self, order, copy_list, direction,lift_name):
        '''Check if there is a conflict in the direction and decide not to pick up the passenger'''
        dont_pick = False
        
        current_floor = self.current_floor_A if lift_name=="A" else self.current_floor_B
        lift_direction = self.direction_A if lift_name =="A" else self.direction_B
        
        if (min(copy_list, key=lambda x: x[1])[1] < current_floor and lift_direction < 0 and direction > 0) or (max(copy_list, key=lambda x: x[1])[1] > current_floor and lift_direction > 0 and direction < 0):
            dont_pick = True
            if order not in self.orders_not_served and order not in self.already_picked:
                self.orders_not_served.append(order)

        if lift_direction > 0 and direction < 0:
            if any(tup[2] > current_floor for tup in copy_list):
                dont_pick = True
        elif lift_direction < 0 and direction > 0:
            if any(tup[2] < current_floor for tup in copy_list):
                dont_pick = True
                
        
                

        return dont_pick

    def Passengers_on_same_floor(self, order, dont_pick, eligible_orders,lift_name):
        '''Pick up the passenger if conditions are met'''
        Index, passenger_position, passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = order

        current_floor = self.current_floor_A if lift_name=="A" else self.current_floor_B
        lift_direction = self.direction_A if lift_name=="A" else self.direction_B
        pending_orders = self.pending_orders_A if lift_name=="A" else self.pending_orders_B
        
        if current_floor == passenger_position and not dont_pick:
            if order not in self.already_picked and order not in eligible_orders:
                eligible_orders.append(order)
                

        # Additional condition to ensure Lift arrival time is updated correctly
        if current_floor == passenger_position and (((passenger_position == min(pending_orders, key=lambda x: x[1])[1]) and (lift_direction == direction)) or ((passenger_position == max(pending_orders, key=lambda x: x[1])[1]) and (lift_direction == direction))):
            if order not in self.already_picked and order not in eligible_orders:
                eligible_orders.append(order)
        
        return eligible_orders
                
    def pick_passenger(self, eligible_orders,lift_name, passenger_data):
        number_people_picked = 0
        if lift_name=="A":
            lift_population = self.lift_A_population
            current_floor = self.current_floor_A
            lift_direction = self.direction_A
        else:
            lift_population = self.lift_B_population
            current_floor =  self.current_floor_B
            lift_direction =  self.direction_B

        if eligible_orders:
            # Calculate available space in the lift
            once = False
            available_space = self.passenger_limit - lift_population
            Orders_tobe_picked = []
            Orders_not_picked = []
            
            if len(eligible_orders) > available_space:
                # Pick only the number of passengers that can be accommodated
                Orders_tobe_picked = random.sample(eligible_orders, available_space)
                for orders in eligible_orders:
                    if orders not in Orders_tobe_picked:#do something about the ordersnot picked
                        Orders_not_picked.append(orders)
                
            else:
                Orders_tobe_picked = eligible_orders[:]

            for order in Orders_tobe_picked:
                Index, passenger_position, passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = order


                picking_passenger = {
                    "Lift ID": lift_name,
                    "Name": Index,
                    "Current floor": passenger_position,
                    "Destination_floor": passenger_destination,
                    "Time": self.current_time,
                    "Status": "Picking"
                }
                print(f"PICKING:\n\n{picking_passenger}\n")
                
                # self.current_time+=self.passenger_inout
                number_people_picked+=1
                
                if lift_name == "A":
                    self.passengers_in_lift_A.append(order)
                    self.lift_A_population += 1
                    
                else:
                    self.passengers_in_lift_B.append(order)
                    self.lift_B_population += 1

                # Update the DataFrame with the new value
                self.df_read.loc[self.df_read["Index"] == Index, "Lift arrival time"] = self.current_time
                # Reload the DataFrame to reflect the changes
                self.df_read.to_csv(self.filepath, index=False)  # Ensure you save the changes to the file

                self.already_picked.append(order)
                self.floor_passenger_count[passenger_position] -= 1
                if not once:
                    if lift_name=="A":
                        self.direction_A = direction
                    else:
                        self.direction_B = direction
                    once = True  # Set once to True after updating the direction
                
                pending_orders = self.pending_orders_A if lift_name=="A" else self.pending_orders_B
                
                if current_floor == passenger_position and (((passenger_position == min(pending_orders, key=lambda x: x[1])[1]) and (lift_direction == direction)) or ((passenger_position == max(pending_orders, key=lambda x: x[1])[1]) and (lift_direction == direction))):
                    
                    if lift_name=="A":
                        self.direction_A=direction
                    
                    else:
                        self.direction_B=direction
                
                if self.lift_A_population == self.passenger_limit:
                    for passenger in self.pending_orders_A[:]:
                        if passenger not in self.passengers_in_lift_A:
                            self.pending_orders_A.remove(passenger)
                            passenger_data.append(passenger)
                            print("passenger not picked", passenger)
                        
                             
                if self.lift_B_population==self.passenger_limit:
                     for passenger in self.pending_orders_B[:]:
                        if passenger not in self.passengers_in_lift_B:
                            self.pending_orders_B.remove(passenger)
                            passenger_data.append(passenger)
                            print("passenger not picked", passenger)

        return passenger_data, number_people_picked                
 
    def assign_passengers(self, pending_orders):
        liftA_orders = []
        liftB_orders = []
        prospective_people_in_liftA = 0
        prospective_people_in_liftB = 0
        
        for passenger in pending_orders:
            Index, passenger_position, passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = passenger
                            
            if passenger_position == self.floor_to_serve:
                
                if passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A):
                    self.pending_orders_B.append(passenger)
                    print(f"\n {passenger} appended to lift B")
                    
                    if prospective_people_in_liftB==0 and not self.status_B:
                        if passenger_position>self.current_floor_B:
                            self.direction_B = 1
                        elif passenger_position<self.current_floor_B:
                            self.direction_B = -1
                        elif passenger_position==self.current_floor_B:
                            self.direction_B = direction
                    prospective_people_in_liftB = 1
            else:
            
                if passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A):# making sure that the passenger has never entered the lift
                                  
                    self.pending_orders_A.append(passenger)
                    print(f"\n {passenger} appended to lift A")
                    
                    if prospective_people_in_liftA==0 and not self.status_A:
                        if passenger_position>self.current_floor_A:
                            self.direction_A = 1
                        elif passenger_position<self.current_floor_A:
                            self.direction_A = -1
                        elif passenger_position==self.current_floor_A:
                            self.direction_A = direction
                    prospective_people_in_liftA = 1
                                            
                    continue

    def update_densities(self):
        densities = [count / self.delta_time for count in self.floor_passenger_count]
        self.density_snapshots.append({"time": self.current_time, "densities": densities})
        print(f"Density snapshot at time {self.current_time}: {densities}")
        
        # self.floor_passenger_count = [0] * (self.num_floors + 1)
        return densities

    def run_simulation(self, passenger_data):
        '''This simulates the lift'''
        passenger_data = sorted(passenger_data, key=lambda x: x[3])
        passenger_arrived = []     
        number_lift_B_picked=0
        number_lift_A_picked=0
        dropped_by_B=0
        dropped_by_A=0
        print("We are in VIP")
        returning = False
        while not returning:
            # Add pending stops for new passengers
            '''method to decide there the passengers will go
            1. the one which is closer (this can be used when both the lifts are idle)
            2. The one which is going to come in the path of one and is going in the same direction as the lift while there is someone in the lift
            3. If the lift get empty then the order which is in the same direction as the lift just before dropping the passenger will be the next order'''
            
            if self.pending_orders_A:
                self.status_A=True
            else:
                self.status_A=False
                self.direction_A = 0
            
            if self.pending_orders_B:
                self.status_B = True
            else:
                self.status_B=False
                self.direction_B = 0
            if self.picking:
                pending_orders = []
                pending_orders_A = []
                pending_orders_B = []
                pending_orders = [p for p in passenger_data if p[3] <= self.current_time]
                
                for p in pending_orders:
                    if p not in passenger_arrived:
                        passenger_arrived.append(p)
                        floor = p[1]
                        self.floor_passenger_count[floor] += 1
                
                pending_orders = sorted(pending_orders, key=lambda x: x[3])
                print("pending_orders",pending_orders)
                
                if self.time_elapsed >= self.delta_time:
                    densities = self.update_densities()
                    self.current_density = densities
                    self.time_elapsed = 0
                
                if pending_orders:
                    self.assign_passengers(pending_orders)

                # Print the current state of pending_orders_A
                print(f"pending_orders_A: {pending_orders_A}")

                # Ensure that the same pending_orders_A is passed to data_sorter
                self.pending_orders_A = self.data_sorter(self.pending_orders_A, self.current_floor_A)
                
                self.pending_orders_A = sorted(self.pending_orders_A, key=lambda x: x[3])
                
                self.pending_orders_B = self.data_sorter(self.pending_orders_B, self.current_floor_B)
                
                self.pending_orders_B = sorted(self.pending_orders_B, key=lambda x: x[3])

                print(f"\nPending orders A: {pending_orders_A}\nPending orders B: {pending_orders_B}\n")
                
            #checking on each floor to see if there is a passenger going in the same direction as the lift even if he or she was not the closest to the lift and would be efficient
            print(f"Pending_order_B  = {self.pending_orders_B}")
            print(f"Pending_order_A  = {self.pending_orders_A}")
            
            for person in passenger_data[:]:
                if person in self.pending_orders_A or person in self.pending_orders_B:
                    passenger_data.remove(person)
            
            print(f"\npending orders A: {self.pending_orders_A}\npending orders B: {self.pending_orders_B}\n")
            
            
            # Remove duplicates from pending orders and passenger data           
            if self.pending_orders_A:
                seen = set()
                self.pending_orders_A = [x for x in self.pending_orders_A if not (x in seen or seen.add(x))]
                passenger_data = [x for x in passenger_data if not (x in seen or seen.add(x))]
                self.pending_orders_A = sorted(self.pending_orders_A, key=lambda x: abs(x[1] - self.current_floor_A), reverse=False if self.direction_A < 0 else True)
           
            if self.pending_orders_B:
                seen = set()
                self.pending_orders_B = [x for x in self.pending_orders_B if not (x in seen or seen.add(x))]
                passenger_data = [x for x in passenger_data if not (x in seen or seen.add(x))]
                self.pending_orders_B = sorted(self.pending_orders_B, key=lambda x: abs(x[1] - self.current_floor_B), reverse=False if self.direction_B < 0 else True)
            
            self.pending_orders_A = list(dict.fromkeys(self.pending_orders_A) )
            self.pending_orders_B = list(dict.fromkeys(self.pending_orders_B) )

            if self.pending_orders_A:
                self.status_A=True
                passenger_data, number_lift_A_picked, dropped_by_A = self.serve_stop("A", passenger_data=passenger_data)
                self.move("A")
            else:
                self.status_A=False
                self.direction_A = 0
            
                
            if self.pending_orders_B:
                self.status_B = True
                passenger_data, number_lift_B_picked, dropped_by_B = self.serve_stop("B", passenger_data=passenger_data)
                self.move("B")
            else:
                self.status_B=False
                self.direction_B = 0


            # Stop simulation if lift goes out of bounds
            if self.current_floor_A > self.num_floors or self.current_floor_A < 0 or self.current_floor_B>self.num_floors or self.current_floor_B<0:
                print("There was an error")
                raise Exception("There is an Error")

            self.current_time += self.floor_time + (number_lift_B_picked + number_lift_A_picked + dropped_by_B + dropped_by_A)*self.passenger_inout
            self.time_elapsed += self.floor_time + (number_lift_B_picked + number_lift_A_picked + dropped_by_B + dropped_by_A)*self.passenger_inout
                    
            print(f"Pending_order_B  = {self.pending_orders_B}")
            print(f"Pending_order_A  = {self.pending_orders_A}")
            print(max(self.current_density))
            print(self.floor_to_serve)
            print(self.threshold_density_low)
            print(self.floor_passenger_count)
            # input("con")
            if max(self.current_density)<=self.threshold_density_low:
                self.picking = False
                # sys.exit()
                self.time_below_threshold += self.floor_time + (number_lift_B_picked + number_lift_A_picked + dropped_by_B + dropped_by_A)*self.passenger_inout
                if self.time_below_threshold>=self.t_persistence and self.lift_A_population==0 and self.lift_B_population==0:
                    returning = True
                    self.time_below_threshold = 0
            
            for person in passenger_data[:]:
                if person in self.pending_orders_A or person in self.pending_orders_B:
                    passenger_data.remove(person)
                    print(person)
            print(self.current_time)
        return passenger_data
  