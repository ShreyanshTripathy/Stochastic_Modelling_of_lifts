import random
import time
import numpy as np
# import pandas as pd
import csv
import sys
class DualLiftSystem:

    '''This elevator is trying to simulate the real life situation of passengers arriving at varied times'''
    
    '''This lift works when the current density is below a threshold density'''

    def __init__(self, current_floor_A,current_floor_B, num_floors,filepath, Passenger_limit,T_high_oscillation,T_low_oscillation,current_density,delta_time,T_high_VIP,T_low_VIP,current_time = 0):
        # Initialize the elevator state and load the passenger data from a CSV file
        self.num_floors = num_floors
        self.orders_in_opposite_direction = []
        self.already_picked = [] #list of passengers that have been picked
        self.orders_not_served = [] #these are the orders that were not done because there was some order to be completed right above it or below depending on the direction
        self.filepath = filepath
        # self.df_read = pd.read_csv(filepath)
        self.current_time = current_time
        self.orders_done = [] #list of passengers whose order is completed
        self.passenger_limit = Passenger_limit
        
        #adding variation in time
        self.floor_time = 1
        self.passenger_inout = 3
        
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

        # Switching Variables
        
        self.T_high_oscillation  = T_high_oscillation 
        self.T_low_oscillation  = T_low_oscillation
         
        self.T_high_VIP  = T_high_VIP 
        self.T_low_VIP  = T_low_VIP 

        self.density_snapshots = []  # To store densities over time
        self.floor_passenger_count = [0] * (self.num_floors + 1)
        
        current_density = [0]*(self.num_floors+1)
        
        self.current_density = current_density
        print(f"Initial mean density: {self.current_density}")
        
        self.picking = True
        
        self.time_elapsed = 0
        self.delta_time = delta_time
        self.t_persistence = 10  # Minimum time density must persist before switching (adjust as needed)
        self.time_above_threshold = 0  # Tracks time above a threshold
        self.time_below_threshold = 0  # Tracks time below a threshold
        
        self.current_mode = "normal"  # Tracks the current mode: "normal", "oscillation", "VIP"

        
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
        
        if lift_name=="A" :
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
                dont_pick = self.check_direction_conflict(order, copy_list, direction,lift_name,passenger_data)
                
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
                # self.df_read.loc[self.df_read["Index"] == Index, "Order completion time"] = self.current_time

                # # Extract the updated tuple
                # updated_tuple = self.df_read.loc[self.df_read["Index"] == Index].iloc[0]
                
                # updated_tuple = tuple(updated_tuple)
                
                # self.orders_done.append(updated_tuple)
                
                # print(f"update_line: {updated_tuple}")
                
                # Reload the DataFrame to reflect the changes
                
                # self.df_read = pd.read_csv(self.filepath)
            
                return 1
        except IndexError:
            pass

        return 0

    def check_direction_conflict(self, order, copy_list, direction,lift_name,passenger_data):
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

                self.floor_passenger_count[passenger_position] -= 1

                self.already_picked.append(order)
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
                        
                             
                if self.lift_B_population==self.passenger_limit:
                     for passenger in self.pending_orders_B[:]:
                        if passenger not in self.passengers_in_lift_B:
                            self.pending_orders_B.remove(passenger)
                            passenger_data.append(passenger)

        return passenger_data, number_people_picked                
    
    def add_stop(self, order, lift_name):
        '''
        Function to add stop to the lift queue if its efficient to do so.
        If the direction the passenger wants to go is opposite to the direction of the lift
        then the passenger will not be appended. Also, if the passenger is going in the same
        direction but his or her floor has already been crossed then he or she will not be
        added and will have to wait for the lift to change directions to come and get them later.
        '''
        
        current_floor = self.current_floor_A if lift_name=="A" else self.current_floor_B
        direction = self.direction_A if lift_name=="A" else self.direction_B
        
        if direction == 1 and order[-1] > 0 and current_floor <= order[1]:
            
            if lift_name == "A":
                if order not in self.pending_orders_A:
                
                    self.pending_orders_A.append(order)
                    self.status_A = True
            
            else:
                if order not in self.pending_orders_B:
                    
                    self.pending_orders_B.append(order)
                    self.status_B = True
                    
        elif direction == -1 and (order[-1]) < 0 and current_floor >= order[1]:
            if lift_name == "A":
                if order not in self.pending_orders_A:
                
                    self.pending_orders_A.append(order)
                    self.status_A = True
            
            else:
                if order not in self.pending_orders_B:
                    
                    self.pending_orders_B.append(order)
                    self.status_B = True

        else:

            if order not in self.orders_in_opposite_direction:

                self.orders_in_opposite_direction.append(order)
                
    def queue_maker(self, pending_orders, passenger_data, lift_name):
        going_up_to_come_down = False
        going_down_to_come_up = False
        
        if lift_name == "A":
            current_floor = self.current_floor_A
            lift_direction = self.direction_A
            started = self.status_A
        else:
            current_floor = self.current_floor_B
            lift_direction = self.direction_B
            started = self.status_B
        
        if pending_orders:
            for order in pending_orders:
                passenger_data.remove(order)
                '''the following helps to assign direction to the lift'''
                if order[1] > current_floor and not started:
                    lift_direction = 1
                    if lift_name=="A" and order not in self.pending_orders_A:
                        self.pending_orders_A.append(order)
                         
                    elif lift_name=="B" and order not in self.pending_orders_B:
                            self.pending_orders_B.append(order)
                             
                            
                elif order[1] < current_floor and not started:
                    lift_direction = -1
                    if lift_name=="A" and order not in self.pending_orders_A:
                        self.pending_orders_A.append(order)
                         
                    elif lift_name=="B" and order not in self.pending_orders_B:
                            self.pending_orders_B.append(order)
                             
                elif order[1] == current_floor and not started:
                    lift_direction = order[-1]
                    if lift_name=="A" and order not in self.pending_orders_A:
                        self.pending_orders_A.append(order)
                         
                    elif lift_name=="B" and order not in self.pending_orders_B:
                            self.pending_orders_B.append(order)
                             
                #checking if the person is calling the lift up to come down or calling it down to go up

                elif order[1] > current_floor and order[-1] < 0 and lift_direction == 1:
                    for j in pending_orders:
                        if j[-1] == -1 and j[1] > current_floor:
                        
                            if lift_name=="A":
                                if j not in self.pending_orders_A:
                                    self.pending_orders_A.append(j)
                                     
                            elif lift_name == "B" and j not in self.pending_orders_B:
                                    self.pending_orders_B.append(j)
                                     
                                
                                
                        elif j[-1] == 1 and j[1] == current_floor:
                            
                            if lift_name=="A":
                                if j not in self.pending_orders_A:
                                    self.pending_orders_A.append(j)
                                     
                            elif lift_name=="B" and j not in self.pending_orders_B:
                                    self.pending_orders_B.append(j)
                                     

                    going_up_to_come_down = True
                    
                elif order[1] < current_floor and order[-1] > 0 and lift_direction == -1:
                    for j in pending_orders:
                        if j[-1] == 1 and j[1] < current_floor:
                            if lift_name=="A":
                                if j not in self.pending_orders_A:
                                    self.pending_orders_A.append(j)
                                     
                            elif lift_name=="B" and j not in self.pending_orders_B:
                                    self.pending_orders_B.append(j)
                                     
                        elif j[-1] == 1 and j[1] == current_floor:
                            if lift_name=="A":
                                if j not in self.pending_orders_A:
                                    self.pending_orders_A.append(j)
                                     
                            elif lift_name=="B" and j not in self.pending_orders_B:
                                    self.pending_orders_B.append(j)
                                     
                    going_down_to_come_up = True
                    
                #All the pickup orders are over and the lift is moving up to drop someone but on the way some one wants to go down....so the lift goes up and comes down
                elif order[1] < current_floor and lift_direction > 0 and order[-1] < 0 and going_up_to_come_down:
                    if lift_name=="A" and order not in self.pending_orders_A:
                        self.pending_orders_A.append(order)
                         
                    elif lift_name=="B" and order not in self.pending_orders_B:
                            self.pending_orders_B.append(order)
                             

                elif order[1] > current_floor and lift_direction < 0 and order[-1] > 0 and going_down_to_come_up:
                    
                    if lift_name=="A" and order not in self.pending_orders_A:
                        self.pending_orders_A.append(order)
                         
                    elif lift_name=="B" and order not in self.pending_orders_B:
                            self.pending_orders_B.append(order)
                             
                            
                elif order[1] > current_floor and started and lift_direction==1:
                    if lift_name=="A" and order not in self.pending_orders_A:
                        self.pending_orders_A.append(order)
                         
                    elif lift_name=="B" and order not in self.pending_orders_B:
                            self.pending_orders_B.append(order)
                             
                            
                elif order[1] < current_floor and started and lift_direction==-1:
                    if lift_name=="A" and order not in self.pending_orders_A:
                        self.pending_orders_A.append(order)
                        
                    elif lift_name=="B" and order not in self.pending_orders_B:
                            self.pending_orders_B.append(order)
        
                elif order[1] == current_floor and started and lift_direction==order[-1]:
                    if lift_name=="A" and order not in self.pending_orders_A:
                        self.pending_orders_A.append(order)
                    elif lift_name=="B" and order not in self.pending_orders_B:
                            self.pending_orders_B.append(order)

                started = True

            going_up_to_come_down = False
            going_down_to_come_up = False
            
            for order in (self.pending_orders_A if lift_name=="A" else self.pending_orders_B):
                if order in passenger_data:
                    passenger_data.remove(order)
                if order in pending_orders:
                    pending_orders.remove(order)

            for order in pending_orders:
                self.add_stop(order=order,lift_name=lift_name)
                if self.orders_in_opposite_direction:
                    opp_order = self.orders_in_opposite_direction.pop(0)
                    if opp_order not in passenger_data:
                        passenger_data.append(opp_order)
        if lift_name=="A":
            self.direction_A=lift_direction
            self.status_A = started
        else:
            self.direction_B=lift_direction
            self.status_B = started
                            
        return passenger_data

    def assign_passengers(self, pending_orders):
        liftA_orders = []
        liftB_orders = []
        prospective_people_in_liftA = 0
        prospective_people_in_liftB = 0
        
        for passenger in pending_orders:
            Index, passenger_position, passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = passenger
                      
            distance_from_A = abs(self.current_floor_A - passenger_position)
            distance_from_B = abs(self.current_floor_B - passenger_position)
            
                        
            if distance_from_A<distance_from_B:
                if not self.status_A and (direction==self.direction_A or self.direction_A==0) and prospective_people_in_liftA==0:
                    if passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A):# making sure that the passenger has never entered the lift
                        
            
                        liftA_orders.append(passenger)
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
                # else:
                #     if ((self.direction_A>0 and direction>0 and passenger_position>self.current_floor_A) or (self.direction_A<0 and direction<0 and passenger_position<=self.current_floor_A)) and (passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A)):
                #         liftA_orders.append(passenger)
                #         print(f"\n {passenger} appended to lift A")
                #         prospective_people_in_liftA=1
            
            elif distance_from_B<distance_from_A:
                if not self.status_B  and (direction==self.direction_B or self.direction_B==0) and prospective_people_in_liftB==0:
                    if passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A):
                        liftB_orders.append(passenger)
                        print(f"\n {passenger} appended to lift B")
                        
                        if prospective_people_in_liftB==0 and not self.status_B:
                            if passenger_position>self.current_floor_B:
                                self.direction_B = 1
                            elif passenger_position<self.current_floor_B:
                                self.direction_B = -1
                            elif passenger_position==self.current_floor_B:
                                self.direction_B = direction
                        prospective_people_in_liftB = 1
                
            elif distance_from_A == distance_from_B:
                lift_name = random.choice(["A","B"])
                # lift_name = "B"
                if lift_name=="A":
                    if self.direction_A<=0 and direction<0 and passenger_position<=self.current_floor_A:
                        if passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A):
                            liftA_orders.append(passenger)
                            print(f"\n {passenger} appended to lift A")
                            prospective_people_in_liftA = 1
                            self.direction_A = direction
                            continue
                    if self.direction_A>=0 and direction>0 and passenger_position>=self.current_floor_A:
                        if passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A):
                            liftA_orders.append(passenger)
                            print(f"\n {passenger} appended to lift A")
                            prospective_people_in_liftA = 1
                            self.direction_A = direction
                            continue
                else:
                    if self.direction_B<=0 and direction<0 and passenger_position<=self.current_floor_B:
                        if passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A):
                            liftB_orders.append(passenger)
                            print(f"\n {passenger} appended to lift B")
                            prospective_people_in_liftB = 1
                            self.direction_B = direction
                            continue
                    if self.direction_B>=0 and direction>0 and passenger_position>=self.current_floor_B:
                        if passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A):
                            liftB_orders.append(passenger)
                            print(f"\n {passenger} appended to lift B")
                            prospective_people_in_liftB = 1
                            self.direction_B = direction
                            continue
            if self.status_B==False and prospective_people_in_liftB==0:
                if passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A):
                    liftB_orders.append(passenger)
                    print(f"\n {passenger} appended to lift B")
                    if prospective_people_in_liftB==0 and not self.status_B:
                        if passenger_position>self.current_floor_B:
                            self.direction_B = 1
                        elif passenger_position<self.current_floor_B:
                            self.direction_B = -1
                        elif passenger_position==self.current_floor_B:
                            self.direction_B = direction
                    prospective_people_in_liftB = 1
                    continue
            elif self.status_A == False and prospective_people_in_liftA==0:
                if passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A):
                    liftA_orders.append(passenger)
                    print(f"\n {passenger} appended to lift A")
                    if prospective_people_in_liftA==0 and not self.status_A:
                        if passenger_position>self.current_floor_A:
                            self.direction_A = 1
                        elif passenger_position<self.current_floor_B:
                            self.direction_A = -1
                        elif passenger_position==self.current_floor_B:
                            self.direction_A = direction
                    prospective_people_in_liftA = 1
                    continue
                
            elif passenger_position==self.current_floor_A and self.direction_A==direction and (passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A)):
                liftA_orders.append(passenger)
                print(f"\n {passenger} appended to lift A")
                prospective_people_in_liftA = 1
            elif passenger_position==self.current_floor_B and self.direction_B==direction and (passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A)):
                liftB_orders.append(passenger)
                print(f"\n {passenger} appended to lift B")
                prospective_people_in_liftB = 1
            

        return liftA_orders, liftB_orders
    
    def reassign_passenger(self, person, source_list, target_list, current_floor, direction):
        passengers_in_lift = self.passengers_in_lift_A+self.passengers_in_lift_B
        if source_list == self.pending_orders_B:
            name = "B"
            source_current_floor = self.current_floor_B
        elif source_list == self.pending_orders_A:
            name = "A"
            source_current_floor = self.current_floor_A
        else:
            name = "Not assigned list"
            source_current_floor = -1
        if target_list == self.pending_orders_B:
            name1 = "B"
        elif target_list == self.pending_orders_A:
            name1 = "A"
        
        if person[1] == current_floor and person[6] == direction and person[1] != source_current_floor:
            if person in source_list and person not in target_list and person not in passengers_in_lift:
                    source_list.remove(person)
                    target_list.append(person)
    
    def update_densities(self):
        densities = [count / self.delta_time for count in self.floor_passenger_count]
        self.density_snapshots.append({"time": self.current_time, "densities": densities})
        print(f"Density snapshot at time {self.current_time}: {densities}")
        
        mean_density = np.mean(densities)
        max_floor_density = max(densities)

        # Update persistence timers
        if mean_density > self.T_high_oscillation:
            self.time_above_threshold += self.delta_time
            self.time_below_threshold = 0
        elif mean_density < self.T_low_oscillation:
            self.time_below_threshold += self.delta_time
            self.time_above_threshold = 0
        
        if max_floor_density > self.T_high_VIP:
            self.time_above_threshold += self.delta_time
            self.time_below_threshold = 0
        elif max_floor_density < self.T_low_VIP:
            self.time_below_threshold += self.delta_time
            self.time_above_threshold = 0
        
        # self.floor_passenger_count = [0] * (self.num_floors + 1)
        return densities

    def switch_to_oscillation(self, passenger_data):
        if (self.lift_A_population == 0 and self.lift_B_population==0) and not self.picking:
            
            if self.pending_orders_A:
                for person in self.pending_orders_A:
                    if person not in passenger_data:
                        passenger_data.append(person)
                        self.pending_orders_A.remove(person)
            if self.pending_orders_B:
                for person in self.pending_orders_B:
                    if person not in passenger_data:
                        passenger_data.append(person)
                        self.pending_orders_B.remove(person)
                            
            print(f"Switching to oscillation at time {self.current_time}")
            
            metro = DualOscillation(current_floor_A=self.current_floor_A,current_floor_B=self.current_floor_B, num_floors=self.num_floors, Passenger_limit=self.passenger_limit, delta_time=self.delta_time, threshold_density_high=self.T_high_oscillation,threshold_density_low = self.T_low_oscillation , filepath = self.filepath, current_time=self.current_time, current_density=self.current_density)  
             
            updated_passenger_Data = metro.run_simulation(passenger_data)
            
            if metro.already_picked_A:
                for people in metro.already_picked_A:
                    if people not in self.pending_orders_A:
                        self.pending_orders_A.append(people)
                    if people not in self.passengers_in_lift_A:
                        self.passengers_in_lift_A.append(people)
                    if people not in self.already_picked:
                        self.already_picked.append(people)
            if metro.already_picked_B:
                for people in metro.already_picked_B:
                    if people not in self.pending_orders_B:
                        self.pending_orders_B.append(people)
                    if people not in self.passengers_in_lift_B:
                        self.passengers_in_lift_B.append(people)
                    if people not in self.already_picked:
                        self.already_picked.append(people)
                        
            if metro.orders_done:
                for people in metro.orders_done:
                    if people not in self.orders_done:
                        self.orders_done.append(people)
                    elif people in self.orders_done:
                        print("There was a problem...some one was processes twices")
                        sys.exit()
            
            self.direction_A = metro.direction_A
            self.direction_B = metro.direction_B
            self.current_floor_A = metro.current_floor_lift_A
            self.current_floor_B = metro.current_floor_lift_B
            self.current_time = metro.current_time
            
            self.lift_A_population = metro.lift_A_Population
            self.lift_B_population = metro.lift_B_Population
            
            for passenger in metro.pending_orders:
                if passenger in metro.already_picked_B:
                    pass
                if passenger in metro.already_picked_A:
                    pass
                if (passenger not in metro.already_picked_A) and (passenger not in metro.already_picked_B) and (passenger not in metro.orders_done):
                    updated_passenger_Data.append(passenger)
            
            
            if self.pending_orders_A:                    
                self.status_A = True
            else:
                self.status_A = False
                
            if self.pending_orders_B:
                self.status_B = True
            else:
                self.status_B = False 
            
            # print("We are out of the oscillation lift")
            # print(f"Passengers in lift A: {self.passengers_in_lift_A} Vs Passengers in lift A in metro system: {metro.already_picked_A}")
            # print(f"Passengers in lift B: {self.passengers_in_lift_B} Vs Passengers in lift B in metro system: {metro.already_picked_B}")
            # print(f"Pending_orders in dual lift: {updated_passenger_Data} Vs Pending_orders in metro system: {metro.pending_orders}")
            
            # # sys.exit()
            # 
            
            return updated_passenger_Data

    def switch_to_VIP(self, passenger_data):
        if self.pending_orders_A:
            for person in self.pending_orders_A:
                if person not in passenger_data:
                    passenger_data.append(person)
                    self.pending_orders_A.remove(person)
        if self.pending_orders_B:
            for person in self.pending_orders_B:
                if person not in passenger_data:
                    passenger_data.append(person)
                    self.pending_orders_B.remove(person)
        print(f"Switching to oscillation at time {self.current_time}")
        
        VIP = VIPDualSystem(current_floor_A = self.current_floor_A,current_floor_B = self.current_floor_B, num_floors=self.num_floors,filepath=self.filepath, Passenger_limit = self.passenger_limit,delta_time=self.delta_time,threshold_density_high=self.T_high_VIP,threshold_density_low=self.T_low_VIP,current_density=self.current_density, current_time = self.current_time)
        updated_passenger_Data = VIP.run_simulation(passenger_data)
        
        if VIP.passengers_in_lift_A:
            for people in VIP.passengers_in_lift_A:
                if people not in self.pending_orders_A:
                    self.pending_orders_A.append(people)
                if people not in self.passengers_in_lift_A:
                    self.passengers_in_lift_A.append(people)
                if people not in self.already_picked:
                    self.already_picked.append(people)
        if VIP.passengers_in_lift_B:
            for people in VIP.passengers_in_lift_B:
                if people not in self.pending_orders_B:
                    self.pending_orders_B.append(people)
                if people not in self.passengers_in_lift_B:
                    self.passengers_in_lift_B.append(people)
                if people not in self.already_picked:
                    self.already_picked.append(people)
        
        if VIP.orders_done:
            for people in VIP.orders_done:
                if people not in self.orders_done:
                    self.orders_done.append(people)
                elif people in self.orders_done:
                    print("There was a problem...some one was processes twices")
                    sys.exit()
                    
        total = VIP.pending_orders_A + VIP.pending_orders_B
        for passenger in total:
            if (passenger not in VIP.passengers_in_lift_A) and (passenger not in VIP.passengers_in_lift_B) and (passenger not in VIP.orders_done):
                updated_passenger_Data.append(passenger)
        
        if VIP.orders_in_opposite_direction:
            for passenger in VIP.orders_in_opposite_direction:
                if passenger not in self.orders_in_opposite_direction:
                    self.order_in_opposite_direction.append(passenger)
        if VIP.already_picked:
            for passenger in VIP.already_picked:
                if passenger not in self.already_picked:
                    self.already_picked.append(passenger)
        if VIP.orders_not_served:
            for passenger in VIP.orders_not_served:
                if passenger not in self.orders_not_served:
                    self.orders_not_served.append(passenger)
            
        
        self.direction_A = VIP.direction_A
        self.direction_B = VIP.direction_B
        self.current_floor_A = VIP.current_floor_A
        self.current_floor_B = VIP.current_floor_B
        self.current_time = VIP.current_time
        
        self.lift_A_population = VIP.lift_A_population
        self.lift_B_population = VIP.lift_B_population
        
        self.status_A = VIP.status_A
        self.status_B = VIP.status_B
        
        print("We are out of the oscillation lift")
        
        print(f"Updated passenger data: {updated_passenger_Data}")
        print(f"Lift_A_position: {VIP.current_floor_A}, Lift_B_position: {VIP.current_floor_B}")
        print(f"Lift_A_population: {VIP.lift_A_population}, Lift_B_population: {VIP.lift_B_population}")
        
        return updated_passenger_Data   
        
    def run_simulation(self, passenger_data):
        '''This simulates the lift'''       
        people_not_assigned = []
        number_lift_B_picked=0
        number_lift_A_picked=0
        dropped_by_B=0
        dropped_by_A=0
        while passenger_data or self.pending_orders_A or self.pending_orders_B:
            #first checking the status of the system
            print(f"Passenger in lift A: {self.passengers_in_lift_A}")
            print(f"Passenger in lift B: {self.passengers_in_lift_B}")
            print(f"pending orders in lift A: {self.pending_orders_A}")
            print(f"pending orders in lift B: {self.pending_orders_B}")
            
            print(f"already picked in total: {self.already_picked}")
            print(self.current_time)
            # input("continue?")
            
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
                
                for passenger in pending_orders:
                    floor = passenger[1]
                    self.floor_passenger_count[floor]+=1
            
                if self.time_elapsed>=self.delta_time:
                    self.current_density = self.update_densities()
                    self.time_elapsed=0
            
                pending_orders = sorted(pending_orders, key=lambda x: x[3])
                pending_orders_A, pending_orders_B = self.assign_passengers(pending_orders)
                
                pending_orders_A = self.data_sorter(pending_orders_A, self.current_floor_A)
                    
                pending_orders_A = sorted(pending_orders_A, key=lambda x: x[3])
                
                pending_orders_B = self.data_sorter(pending_orders_B, self.current_floor_B)
                
                pending_orders_B = sorted(pending_orders_B, key=lambda x: x[3])

                passenger_data= self.queue_maker(pending_orders=pending_orders_A, passenger_data=passenger_data,lift_name="A")
                
                passenger_data = self.queue_maker(pending_orders=pending_orders_B, passenger_data=passenger_data, lift_name="B")
            
                for person in passenger_data:
                    if person in pending_orders and person not in self.pending_orders_A and person not in self.pending_orders_B and person not in people_not_assigned:
                        people_not_assigned.append(person)
            
            for person in list(self.pending_orders_B).copy():
                self.reassign_passenger(person, self.pending_orders_B, self.pending_orders_A, self.current_floor_A, self.direction_A)
            for person in list(self.pending_orders_A).copy():
                self.reassign_passenger(person, self.pending_orders_A, self.pending_orders_B, self.current_floor_B, self.direction_B)
                
            for person in people_not_assigned[:]:
                if person in self.pending_orders_A or person in self.pending_orders_B:
                    people_not_assigned.remove(person)
            
            for person in list(people_not_assigned):
                self.reassign_passenger(person, people_not_assigned, self.pending_orders_A, self.current_floor_A, self.direction_A)
                self.reassign_passenger(person, people_not_assigned, self.pending_orders_B, self.current_floor_B, self.direction_B)
                
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
            
            count_greater_than_T_high_VIP = sum(1 for value in self.current_density if value > self.T_high_VIP)
            
            if np.mean(self.current_density) >= self.T_high_oscillation and self.time_above_threshold >= self.t_persistence and (self.current_mode=="normal" or self.current_mode == 'oscillation'):
                #the mean of the current densities is higher than the threshold given and time above this threshold is also more than the t_persistence this means that this change is not sudden. Now we need to switch to oscillation system, to do so we need to first empty the lifts by serving the passengers in the lifts and then stop picking passengers.
                print("Switching to Oscillation system")
                print("No more picking")
                print(self.lift_A_population)
                print(self.lift_B_population)
                
                self.picking = False
                
                for passenger in self.pending_orders_A:
                    if passenger not in self.passengers_in_lift_A:
                        self.pending_orders_A.remove(passenger)
                    if passenger not in passenger_data:
                        passenger_data.append(passenger)                
                for passenger in self.pending_orders_B:
                    if passenger not in self.passengers_in_lift_B:
                        self.pending_orders_B.remove(passenger)
                    if passenger not in passenger_data:
                        passenger_data.append(passenger)                
                
                self.current_mode = "oscillation"
                if not self.picking and (self.lift_A_population==0 and self.lift_B_population==0):
                    print("preparing to switch to oscillatin")
                    data = self.switch_to_oscillation(passenger_data)
                    for passenger in data:
                        if passenger not in passenger_data:
                            passenger_data.append(passenger)
                            print(passenger)
                            sys.exit()
                    print(f"Passengers in lift A: {self.passengers_in_lift_A}")
                    print(f"Passengers in lift B: {self.passengers_in_lift_B}")
                    # sys.exit()
                    self.current_mode = "normal"
                    self.picking = True
                    self.time_above_threshold = 0
                    print(self.passengers_in_lift_A)
                    print(self.passengers_in_lift_B)
                    
            elif max(self.current_density)>=self.T_high_VIP and self.time_above_threshold>=self.t_persistence and (self.current_mode=="normal" or self.current_mode == 'VIP') and count_greater_than_T_high_VIP==1:
                print("Switching to VIP system")
                #he max of the current densities is higher than the threshold given and ther is only one such floor and time above this threshold is also more than the t_persistence this means that this change is not sudden. Now we need to switch to oscillation system, to do so we need to first empty the lifts by serving the passengers in the lifts and then stop picking passengers.
                print("No more picking")
                self.picking = False
                self.current_mode = "VIP"
                if not self.picking and (self.lift_A_population==0 and self.lift_B_population==0):
                    print("Preparing to switch to VIP")
                    data = self.switch_to_VIP(passenger_data)
                    for passenger in data:
                        if passenger not in passenger_data:
                            passenger_data.append(passenger)
                    print(self.lift_A_population)
                    print(self.lift_B_population)
                    print(self.pending_orders_A)
                    print(self.pending_orders_B)
                    print(passenger_data)
                    self.current_mode = "normal"
                    self.picking = True
                    self.time_above_threshold = 0
            
            if self.lift_A_population==0 and self.pending_orders_A and not passenger_data:
                for order in self.pending_orders_A:
                    self.pending_orders_A.remove(order)
                    passenger_data.append(order)
            
            copy = []    
            if passenger_data:
                for passenger in passenger_data.copy():
                    if passenger not in copy:
                        copy.append(passenger)
                    passenger_data.remove(passenger)
                passenger_data = []
                for passenger in copy:
                    passenger_data.append(passenger)
        

            if self.lift_B_population==0 and self.pending_orders_B and not passenger_data:
                for order in self.pending_orders_B:
                    self.pending_orders_B.remove(order)
                    passenger_data.append(order)         
        return passenger_data

class DualOscillation:
    '''This lift will be used when the density on each floor is high and similar.'''
    def __init__(self, current_floor_A, current_floor_B, num_floors, Passenger_limit, filepath, threshold_density_high,threshold_density_low ,current_time, current_density, directionA=0, directionB=0, lowest_floor=0, delta_time=5):
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
        self.threshold_density_high = threshold_density_high
        self.threshold_density_low = threshold_density_low

        # Take the mean of current_density (which is now a list)
        self.current_density = current_density
        print(f"Initial mean density: {self.current_density}")

        self.delta_time = delta_time
        
        # self.df = pd.read_csv(filepath)

        # New variables for tracking densities
        self.time_elapsed = 0
        self.density_snapshots = []  # To store densities over time
        self.floor_passenger_count = [0] * (self.num_floors + 1)  # Tracks passengers on each floor
        
        self.t_persistence = 10  # Minimum time density must persist before switching (adjust as needed)
        self.time_above_threshold = 0  # Tracks time above a threshold
        self.time_below_threshold = 0  # Tracks time below a threshold
        
        # self.pick_passenger = True
        '''What if we stop picking and the last person of the lift gets down on a floor and there is a person that is on the same floor do we serve them or not if we dont want to pick them then we wont pick them'''

    def move(self):
        self.current_floor_lift_A += self.direction_A
        print(f"Lift position A: {self.current_floor_lift_A}")
        self.current_floor_lift_B += self.direction_B
        print(f"Lift position B: {self.current_floor_lift_B}")

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
                # self.df.loc[self.df["Index"] == Index, "Order completion time"] = self.current_time
                # updated_tuple = self.df.loc[self.df["Index"] == Index].iloc[0]
                # updated_tuple = tuple(updated_tuple)
                # self.orders_done.append(updated_tuple)
                self.lift_A_Population-=1


            if (self.current_floor_lift_A == Passenger_position and order not in already_picked and self.direction_A == direction):
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
                    
                    # self.df.loc[self.df["Index"] == Index, "Lift arrival time"] = self.current_time
                
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

                # self.df.loc[self.df["Index"] == Index, "Order completion time"] = self.current_time
                # updated_tuple = self.df.loc[self.df["Index"] == Index].iloc[0]
                # updated_tuple = tuple(updated_tuple)
                # self.orders_done.append(updated_tuple)
                # self.df.to_csv(self.filepath, index=False)

            if (self.current_floor_lift_B == Passenger_position and order not in already_picked and self.direction_B == direction):
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
                    
                    # self.df.loc[self.df["Index"] == Index, "Lift arrival time"] = self.current_time

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

        # Update persistence timers
        if mean_density > self.threshold_density_high:
            self.time_above_threshold += self.delta_time
            self.time_below_threshold = 0
        elif mean_density < self.threshold_density_low:
            self.time_below_threshold += self.delta_time
            self.time_above_threshold = 0
        
        # self.floor_passenger_count = [0] * (self.num_floors + 1)
        return densities

    def run_simulation(self, passenger_data):
        passenger_data = sorted(passenger_data, key=lambda x: x[3])
        not_done = True
        print("We are in oscillation")
        dont_pick = False
        print(self.threshold_density_low)
        print(np.mean(self.current_density))
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
                
            while ((self.current_floor_lift_A != 0 and self.current_floor_lift_B != self.num_floors) or (self.current_floor_lift_A != self.num_floors and self.current_floor_lift_B != 0) or (self.current_floor_lift_A==self.current_floor_lift_B)) and (not_done):
                
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
                    
                if not dont_pick:
                    for p in passenger_data:
                        if p[3] <= self.current_time:
                            self.pending_orders.append(p)
                            passenger_data.remove(p)
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
                    not_done=False
                    
                if self.threshold_density_low > np.mean(self.current_density) and self.time_below_threshold >= self.t_persistence:
                    dont_pick = True
                    print("fhgj")
                
                                
       
            #The lifts are at either ends now...there are tww possibilities they have served enough to get the density down or they have not if they have then we just need to make the population 0 if not then we move to serving
            picking = True
            if np.mean(self.current_density) <= self.threshold_density_low:
                picking = False

            print(self.current_floor_lift_A)
            print(self.current_floor_lift_B) 
            returning = False
            # while self.threshold_density_low < np.mean(self.current_density) and self.time_below_threshold <= self.t_persistence or (self.lift_A_Population!=0 and self.lift_B_Population!=0):
            while not returning:
                self.direction_decider()
                print(self.direction_A)
                print(self.direction_B)
                print(self.current_floor_lift_A)
                print(self.current_floor_lift_B)
                if picking:
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
                
                if np.mean(self.current_density) <= self.threshold_density_low:
                    print(f"Current density = {self.current_density}. Switching to Oscillation")
                    print("We are here")
                    
                    print("Turning off picking...")
                    picking = False
                                          
                    
                    if self.time_below_threshold >= self.t_persistence and self.lift_A_Population==0 and self.lift_B_Population==0:
                        returning = False
                        self.time_below_threshold = 0                    

                self.move()
                self.direction_decider()
                self.current_time += self.floor_time
                self.time_elapsed += self.floor_time
                
                

                if (self.current_floor_lift_A > self.num_floors or self.current_floor_lift_A < self.lowest_floor or 
                    self.current_floor_lift_B > self.num_floors or self.current_floor_lift_B < self.lowest_floor):
                    print("There has been an error in the Oscillation code")
                    break
                print(f"Current Time: {self.current_time}")

        print(self.already_picked_A)
        print(self.already_picked_B)
        print(self.lift_A_Population)
        print(self.lift_B_Population)
        print(self.orders_done)
        print(self.pending_orders)
        sys.exit()
        return passenger_data    

import random
import numpy as np
# import pandas as pd
import time
class VIPDualSystem:

    '''This elevator is trying to simulate the real life situation of passengers arriving at varied times'''

    def __init__(self, current_floor_A,current_floor_B, num_floors,filepath, Passenger_limit,delta_time,threshold_density_high,threshold_density_low,current_density, current_time = 0):
        # Initialize the elevator state and load the passenger data from a CSV file
        self.num_floors = num_floors
        self.orders_in_opposite_direction = []
        self.already_picked = [] #list of passengers that have been picked
        self.orders_not_served = [] #these are the orders that were not done because there was some order to be completed right above it or below depending on the direction
        self.filepath = filepath
        # self.df_read = pd.read_csv(filepath)
        self.current_time = current_time
        self.orders_done = [] #list of passengers whose order is completed
        self.passenger_limit = Passenger_limit
        
        #adding variation in time
        self.floor_time = 1
        self.passenger_inout = 3
        
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
        self.current_density = max(current_density)
        print(f"Initial  density of floor {self.floor_to_serve}: {self.current_density}")
        self.delta_time = delta_time
        
        self.t_persistence = 10  # Minimum time density must persist before switching (adjust as needed)
        self.time_above_threshold = 0  # Tracks time above a threshold
        self.time_below_threshold = 0  # Tracks time below a threshold
        
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
            

            dont_pick = self.check_direction_conflict(order, copy_list, direction,lift_name)

            eligible_orders= self.Passengers_on_same_floor(order, dont_pick,eligible_orders,lift_name)
        
        passenger_data, number_picked = self.pick_passenger(eligible_orders,lift_name, passenger_data)
        
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
                # self.df_read.loc[self.df_read["Index"] == Index, "Order completion time"] = self.current_time

                # # Extract the updated tuple
                # updated_tuple = self.df_read.loc[self.df_read["Index"] == Index].iloc[0]
                
                # updated_tuple = tuple(updated_tuple)
                
                # self.orders_done.append(updated_tuple)
                
                # print(f"update_line: {updated_tuple}")
                
                # Reload the DataFrame to reflect the changes
                
                # self.df_read = pd.read_csv(self.filepath)
            
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
                # self.df_read.loc[self.df_read["Index"] == Index, "Lift arrival time"] = self.current_time
                # # Reload the DataFrame to reflect the changes
                # self.df_read.to_csv(self.filepath, index=False)  # Ensure you save the changes to the file

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
        
        mean_density = np.mean(densities)
        max_floor_density = max(densities)

        # Update persistence timers
        if mean_density > self.T_high_oscillation:
            self.time_above_threshold += self.delta_time
            self.time_below_threshold = 0
        elif mean_density < self.T_low_oscillation:
            self.time_below_threshold += self.delta_time
            self.time_above_threshold = 0
        
        if max_floor_density > self.T_high_VIP:
            self.time_above_threshold += self.delta_time
            self.time_below_threshold = 0
        elif max_floor_density < self.T_low_VIP:
            self.time_below_threshold += self.delta_time
            self.time_above_threshold = 0
        
        # self.floor_passenger_count = [0] * (self.num_floors + 1)
        return densities

    def run_simulation(self, passenger_data):
        '''This simulates the lift'''       
        people_not_assigned = []
        number_lift_B_picked=0
        number_lift_A_picked=0
        dropped_by_B=0
        dropped_by_A=0
        print("We are in VIP")
        picking = True
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
            if picking:
                pending_orders = []
                pending_orders_A = []
                pending_orders_B = []
                pending_orders = [p for p in passenger_data if p[3] <= self.current_time]
                
                for p in pending_orders:
                    floor = p[1]
                    self.floor_passenger_count[floor] += 1
                
                pending_orders = sorted(pending_orders, key=lambda x: x[3])
                print("pending_orders",pending_orders)
                
                if self.time_elapsed >= self.delta_time:
                    desities = self.update_densities()
                    self.current_density = max(desities)
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
            
            if max(self.current_density)<=self.threshold_density_low:
                picking = False
                if self.time_below_threshold>=self.t_persistence and self.lift_A_population==0 and self.lift_B_population==0:
                    returning = True
            
            for person in passenger_data[:]:
                if person in self.pending_orders_A or person in self.pending_orders_B:
                    passenger_data.remove(person)
                    print(person)
                                  
            print(self.current_time)
        return passenger_data
    

num_floors = 40
file_path = "dummy"
passenger_limit = 8

current_floor_A = random.randint(0,num_floors)
current_floor_B = random.randint(0,num_floors)

T_high_oscillation = 0.8
T_low_oscillation = 0.7
current_density = [0]*(num_floors+1)
delta_time = 5 
T_high_VIP = 0.5
T_low_VIP = 0.2 

data = [(1, 0, 34, 0, 0, 0, 1), (2, 1, 38, 0, 0, 0, 1), (3, 2, 0, 0, 0, 0, -1), (4, 3, 30, 0, 0, 0, 1), (5, 4, 40, 0, 0, 0, 1), (6, 5, 21, 0, 0, 0, 1), (7, 6, 20, 0, 0, 0, 1), (8, 7, 26, 0, 0, 0, 1), (9, 8, 5, 0, 0, 0, -1), (10, 9, 5, 0, 0, 0, -1), (11, 10, 29, 0, 0, 0, 1), (12, 11, 4, 0, 0, 0, -1), (13, 12, 22, 0, 0, 0, 1), (14, 13, 14, 0, 0, 0, 1), (15, 14, 19, 0, 0, 0, 1), (16, 15, 31, 0, 0, 0, 1), (17, 16, 12, 0, 0, 0, -1), (18, 17, 7, 0, 0, 0, -1), (19, 18, 27, 0, 0, 0, 1), (20, 19, 2, 0, 0, 0, -1), (21, 20, 3, 0, 0, 0, -1), (22, 21, 26, 0, 0, 0, 1), (23, 22, 13, 0, 0, 0, -1), (24, 23, 13, 0, 0, 0, -1), (25, 24, 35, 0, 0, 0, 1), (26, 25, 36, 0, 0, 0, 1), (27, 26, 15, 0, 0, 0, -1), (28, 27, 5, 0, 0, 0, -1), (41, 40, 39, 0, 0, 0, -1), (33, 32, 37, 0, 0, 0, 1), (35, 34, 15, 0, 0, 0, -1), (36, 35, 4, 0, 0, 0, -1), (40, 39, 36, 0, 0, 0, -1), (37, 36, 39, 0, 0, 0, 1), (38, 37, 27, 0, 0, 0, -1), (29, 28, 39, 0, 0, 0, 1), (34, 33, 7, 0, 0, 0, -1), (30, 29, 24, 0, 0, 0, -1), (31, 30, 39, 0, 0, 0, 1), (32, 31, 23, 0, 0, 0, -1), (39, 38, 39, 0, 0, 0, 1), (42, 0, 5, 24, 0, 0, 1), (43, 0, 39, 24, 0, 0, 1), (44, 0, 29, 54, 0, 0, 1), (45, 0, 26, 60, 0, 0, 1), (46, 0, 25, 62, 0, 0, 1), (47, 0, 15, 73, 0, 0, 1), (48, 0, 7, 76, 0, 0, 1), (49, 19, 15, 80, 0, 0, -1), (50, 0, 17, 87, 0, 0, 1), (51, 0, 12, 92, 0, 0, 1), (52, 0, 2, 118, 0, 0, 1), (53, 0, 38, 124, 0, 0, 1), (54, 0, 9, 128, 0, 0, 1), (55, 0, 20, 134, 0, 0, 1), (56, 0, 34, 144, 0, 0, 1), (57, 7, 14, 144, 0, 0, 1), (58, 0, 33, 162, 0, 0, 1), (59, 0, 33, 187, 0, 0, 1), (60, 0, 7, 202, 0, 0, 1), (61, 0, 17, 211, 0, 0, 1), (62, 0, 11, 214, 0, 0, 1), (63, 0, 12, 236, 0, 0, 1), (64, 33, 37, 236, 0, 0, 1), (65, 32, 36, 241, 0, 0, 1), (66, 0, 16, 256, 0, 0, 1), (67, 0, 37, 271, 0, 0, 1), (68, 0, 23, 272, 0, 0, 1), (69, 0, 29, 273, 0, 0, 1), (70, 0, 28, 280, 0, 0, 1), (71, 0, 1, 297, 0, 0, 1), (72, 0, 4, 299, 0, 0, 1), (73, 0, 28, 313, 0, 0, 1), (74, 0, 28, 318, 0, 0, 1), (75, 0, 34, 325, 0, 0, 1), (76, 0, 11, 342, 0, 0, 1), (77, 0, 21, 342, 0, 0, 1), (78, 0, 4, 344, 0, 0, 1), (79, 0, 37, 347, 0, 0, 1), (80, 0, 35, 348, 0, 0, 1), (81, 25, 22, 349, 0, 0, -1), (82, 0, 2, 360, 0, 0, 1), (83, 0, 8, 361, 0, 0, 1), (84, 0, 39, 365, 0, 0, 1), (85, 37, 17, 370, 0, 0, -1), (86, 20, 2, 371, 0, 0, -1), (87, 0, 17, 371, 0, 0, 1), (88, 0, 15, 393, 0, 0, 1), (89, 0, 20, 394, 0, 0, 1), (90, 4, 16, 397, 0, 0, 1), (91, 0, 16, 399, 0, 0, 1), (92, 5, 33, 404, 0, 0, 1), (93, 0, 30, 417, 0, 0, 1), (94, 0, 31, 439, 0, 0, 1), (95, 0, 32, 445, 0, 0, 1), (96, 15, 11, 455, 0, 0, -1), (97, 0, 39, 464, 0, 0, 1), (98, 3, 40, 467, 0, 0, 1), (99, 0, 2, 473, 0, 0, 1), (100, 0, 40, 482, 0, 0, 1), (101, 0, 39, 487, 0, 0, 1), (102, 0, 34, 487, 0, 0, 1), (103, 0, 6, 489, 0, 0, 1), (104, 22, 37, 492, 0, 0, 1), (105, 0, 28, 496, 0, 0, 1), (106, 0, 18, 500, 0, 0, 1), (107, 0, 36, 503, 0, 0, 1), (108, 36, 6, 506, 0, 0, -1), (109, 0, 12, 523, 0, 0, 1), (110, 0, 30, 529, 0, 0, 1), (111, 0, 29, 534, 0, 0, 1), (112, 0, 21, 542, 0, 0, 1), (113, 0, 29, 547, 0, 0, 1), (114, 0, 40, 570, 0, 0, 1), (115, 0, 12, 576, 0, 0, 1), (116, 0, 17, 579, 0, 0, 1), (117, 0, 34, 587, 0, 0, 1), (118, 0, 2, 587, 0, 0, 1), (119, 0, 17, 602, 0, 0, 1), (120, 0, 21, 606, 0, 0, 1), (121, 0, 36, 627, 0, 0, 1), (122, 13, 33, 628, 0, 0, 1), (123, 18, 27, 638, 0, 0, 1), (124, 0, 19, 641, 0, 0, 1), (125, 0, 13, 652, 0, 0, 1), (126, 0, 34, 666, 0, 0, 1), (127, 0, 35, 670, 0, 0, 1), (128, 0, 20, 673, 0, 0, 1), (129, 0, 24, 682, 0, 0, 1), (130, 0, 23, 701, 0, 0, 1), (131, 0, 19, 701, 0, 0, 1), (132, 0, 37, 708, 0, 0, 1), (133, 0, 33, 717, 0, 0, 1), (134, 0, 37, 718, 0, 0, 1), (135, 0, 16, 743, 0, 0, 1), (136, 0, 15, 763, 0, 0, 1), (137, 0, 38, 765, 0, 0, 1), (138, 25, 39, 773, 0, 0, 1), (139, 0, 5, 783, 0, 0, 1), (140, 0, 34, 784, 0, 0, 1), (141, 0, 35, 796, 0, 0, 1), (142, 24, 28, 798, 0, 0, 1), (143, 0, 18, 802, 0, 0, 1), (144, 0, 19, 804, 0, 0, 1), (145, 0, 35, 813, 0, 0, 1), (146, 0, 8, 815, 0, 0, 1), (147, 0, 24, 828, 0, 0, 1), (148, 33, 13, 829, 0, 0, -1), (149, 0, 36, 831, 0, 0, 1), (150, 0, 29, 832, 0, 0, 1), (151, 29, 1, 839, 0, 0, -1), (152, 0, 39, 852, 0, 0, 1), (153, 0, 15, 855, 0, 0, 1), (154, 0, 38, 857, 0, 0, 1), (155, 0, 35, 875, 0, 0, 1), (156, 24, 31, 884, 0, 0, 1), (157, 0, 39, 884, 0, 0, 1), (158, 0, 21, 901, 0, 0, 1), (159, 0, 37, 920, 0, 0, 1), (160, 0, 15, 923, 0, 0, 1), (161, 34, 10, 925, 0, 0, -1), (162, 9, 21, 928, 0, 0, 1), (163, 0, 22, 936, 0, 0, 1), (164, 0, 25, 938, 0, 0, 1), (165, 11, 19, 939, 0, 0, 1), (166, 0, 7, 956, 0, 0, 1), (167, 0, 15, 964, 0, 0, 1), (168, 20, 24, 965, 0, 0, 1), (169, 0, 9, 972, 0, 0, 1), (170, 0, 40, 992, 0, 0, 1), (171, 0, 15, 1013, 0, 0, 1), (172, 0, 11, 1021, 0, 0, 1), (173, 16, 34, 1024, 0, 0, 1), (174, 0, 8, 1025, 0, 0, 1), (175, 0, 36, 1057, 0, 0, 1), (176, 0, 30, 1071, 0, 0, 1), (177, 9, 15, 1076, 0, 0, 1), (178, 0, 17, 1082, 0, 0, 1), (179, 31, 20, 1083, 0, 0, -1), (180, 27, 3, 1094, 0, 0, -1), (181, 0, 21, 1098, 0, 0, 1), (182, 26, 33, 1102, 0, 0, 1), (183, 0, 5, 1103, 0, 0, 1), (184, 3, 6, 1105, 0, 0, 1), (185, 0, 14, 1111, 0, 0, 1), (186, 0, 10, 1114, 0, 0, 1), (187, 0, 25, 1120, 0, 0, 1), (188, 0, 13, 1127, 0, 0, 1), (189, 0, 10, 1137, 0, 0, 1), (190, 0, 37, 1146, 0, 0, 1), (191, 0, 28, 1152, 0, 0, 1), (192, 0, 1, 1153, 0, 0, 1), (193, 0, 27, 1159, 0, 0, 1), (194, 33, 5, 1198, 0, 0, -1), (195, 0, 35, 1198, 0, 0, 1), (196, 0, 6, 1201, 0, 0, 1), (197, 0, 8, 1210, 0, 0, 1), (198, 1, 30, 1215, 0, 0, 1), (199, 0, 33, 1218, 0, 0, 1), (200, 0, 23, 1227, 0, 0, 1), (201, 0, 17, 1228, 0, 0, 1), (202, 0, 29, 1239, 0, 0, 1), (203, 0, 38, 1242, 0, 0, 1), (204, 0, 9, 1243, 0, 0, 1), (205, 27, 16, 1255, 0, 0, -1), (206, 0, 20, 1258, 0, 0, 1), (207, 17, 8, 1258, 0, 0, -1), (208, 0, 3, 1267, 0, 0, 1), (209, 0, 32, 1269, 0, 0, 1), (210, 0, 36, 1270, 0, 0, 1), (211, 0, 1, 1272, 0, 0, 1), (212, 0, 28, 1277, 0, 0, 1), (213, 0, 21, 1280, 0, 0, 1), (214, 0, 4, 1283, 0, 0, 1), (215, 0, 6, 1284, 0, 0, 1), (216, 0, 13, 1291, 0, 0, 1), (217, 0, 16, 1292, 0, 0, 1), (218, 0, 3, 1308, 0, 0, 1), (219, 0, 24, 1321, 0, 0, 1), (220, 0, 27, 1322, 0, 0, 1), (221, 25, 37, 1325, 0, 0, 1), (222, 0, 2, 1343, 0, 0, 1), (223, 0, 37, 1346, 0, 0, 1), (224, 27, 5, 1364, 0, 0, -1), (225, 0, 35, 1364, 0, 0, 1), (226, 0, 34, 1368, 0, 0, 1), (227, 0, 14, 1373, 0, 0, 1), (228, 0, 40, 1375, 0, 0, 1), (229, 0, 2, 1384, 0, 0, 1), (230, 0, 30, 1386, 0, 0, 1), (231, 37, 4, 1392, 0, 0, -1), (232, 0, 28, 1392, 0, 0, 1), (233, 0, 8, 1402, 0, 0, 1), (234, 0, 28, 1404, 0, 0, 1), (235, 0, 13, 1406, 0, 0, 1), (236, 0, 17, 1414, 0, 0, 1), (237, 28, 34, 1418, 0, 0, 1), (238, 0, 31, 1418, 0, 0, 1), (239, 0, 2, 1419, 0, 0, 1), (240, 33, 14, 1420, 0, 0, -1), (241, 0, 12, 1429, 0, 0, 1), (242, 1, 28, 1454, 0, 0, 1), (243, 0, 26, 1471, 0, 0, 1), (244, 38, 28, 1476, 0, 0, -1), (245, 0, 5, 1480, 0, 0, 1), (246, 0, 32, 1496, 0, 0, 1), (247, 0, 36, 1509, 0, 0, 1), (248, 0, 5, 1527, 0, 0, 1), (249, 0, 14, 1536, 0, 0, 1), (250, 0, 22, 1541, 0, 0, 1), (251, 0, 32, 1546, 0, 0, 1), (252, 0, 15, 1556, 0, 0, 1), (253, 0, 3, 1558, 0, 0, 1), (254, 0, 24, 1561, 0, 0, 1), (255, 25, 7, 1568, 0, 0, -1), (256, 0, 31, 1574, 0, 0, 1), (257, 0, 7, 1574, 0, 0, 1), (258, 0, 10, 1577, 0, 0, 1), (259, 27, 31, 1579, 0, 0, 1), (260, 7, 20, 1579, 0, 0, 1), (261, 0, 3, 1581, 0, 0, 1), (262, 12, 28, 1635, 0, 0, 1), (263, 0, 19, 1668, 0, 0, 1), (264, 0, 1, 1677, 0, 0, 1), (265, 0, 35, 1678, 0, 0, 1), (266, 0, 9, 1679, 0, 0, 1), (267, 0, 16, 1687, 0, 0, 1), (268, 0, 33, 1708, 0, 0, 1), (269, 0, 21, 1712, 0, 0, 1), (270, 10, 35, 1713, 0, 0, 1), (271, 0, 34, 1726, 0, 0, 1), (272, 0, 16, 1738, 0, 0, 1), (273, 28, 16, 1748, 0, 0, -1), (274, 0, 23, 1758, 0, 0, 1), (275, 0, 31, 1762, 0, 0, 1), (276, 0, 23, 1763, 0, 0, 1), (277, 0, 6, 1765, 0, 0, 1), (278, 0, 38, 1782, 0, 0, 1), (279, 0, 8, 1791, 0, 0, 1), (280, 29, 37, 1794, 0, 0, 1), (281, 0, 16, 1799, 0, 0, 1), (282, 34, 4, 1802, 0, 0, -1), (283, 0, 27, 1805, 0, 0, 1), (284, 27, 32, 1814, 0, 0, 1), (285, 17, 3, 1831, 0, 0, -1), (286, 0, 34, 1835, 0, 0, 1), (287, 0, 39, 1875, 0, 0, 1), (288, 0, 12, 1880, 0, 0, 1), (289, 0, 38, 1883, 0, 0, 1), (290, 6, 38, 1884, 0, 0, 1), (291, 22, 13, 1892, 0, 0, -1), (292, 0, 11, 1902, 0, 0, 1), (293, 0, 38, 1906, 0, 0, 1), (294, 0, 26, 1931, 0, 0, 1), (295, 19, 29, 1948, 0, 0, 1), (296, 14, 27, 1956, 0, 0, 1), (297, 0, 8, 1958, 0, 0, 1), (298, 22, 17, 1962, 0, 0, -1), (299, 0, 21, 1966, 0, 0, 1), (300, 0, 1, 1968, 0, 0, 1), (301, 0, 19, 1975, 0, 0, 1), (302, 0, 1, 1982, 0, 0, 1), (303, 6, 9, 1987, 0, 0, 1), (304, 0, 8, 1997, 0, 0, 1), (305, 0, 26, 1997, 0, 0, 1), (306, 0, 6, 1999, 0, 0, 1), (307, 0, 26, 2017, 0, 0, 1), (308, 0, 1, 2029, 0, 0, 1), (309, 14, 4, 2030, 0, 0, -1), (310, 0, 29, 2030, 0, 0, 1), (311, 0, 16, 2036, 0, 0, 1), (312, 0, 1, 2037, 0, 0, 1), (313, 0, 22, 2046, 0, 0, 1), (314, 0, 19, 2058, 0, 0, 1), (315, 7, 9, 2059, 0, 0, 1), (316, 0, 36, 2059, 0, 0, 1), (317, 0, 9, 2064, 0, 0, 1), (318, 0, 7, 2065, 0, 0, 1), (319, 25, 7, 2068, 0, 0, -1), (320, 0, 21, 2075, 0, 0, 1), (321, 28, 24, 2088, 0, 0, -1), (322, 21, 14, 2091, 0, 0, -1), (323, 0, 17, 2094, 0, 0, 1), (324, 0, 28, 2119, 0, 0, 1), (325, 0, 23, 2127, 0, 0, 1), (326, 22, 24, 2131, 0, 0, 1), (327, 0, 25, 2136, 0, 0, 1), (328, 0, 14, 2149, 0, 0, 1), (329, 0, 8, 2150, 0, 0, 1), (330, 0, 40, 2156, 0, 0, 1), (331, 0, 38, 2158, 0, 0, 1), (332, 0, 31, 2159, 0, 0, 1), (333, 33, 6, 2192, 0, 0, -1), (334, 0, 27, 2192, 0, 0, 1), (335, 0, 16, 2193, 0, 0, 1), (336, 0, 11, 2196, 0, 0, 1), (337, 0, 27, 2217, 0, 0, 1), (338, 0, 4, 2220, 0, 0, 1), (339, 19, 18, 2233, 0, 0, -1), (340, 0, 40, 2240, 0, 0, 1), (341, 0, 20, 2247, 0, 0, 1), (342, 0, 4, 2250, 0, 0, 1), (343, 0, 20, 2255, 0, 0, 1), (344, 20, 10, 2257, 0, 0, -1), (345, 14, 30, 2257, 0, 0, 1), (346, 0, 4, 2265, 0, 0, 1), (347, 0, 13, 2282, 0, 0, 1), (348, 0, 27, 2287, 0, 0, 1), (349, 0, 34, 2298, 0, 0, 1), (350, 0, 26, 2299, 0, 0, 1), (351, 0, 15, 2319, 0, 0, 1), (352, 0, 19, 2321, 0, 0, 1), (353, 0, 15, 2333, 0, 0, 1), (354, 0, 40, 2342, 0, 0, 1), (355, 0, 24, 2371, 0, 0, 1), (356, 0, 30, 2373, 0, 0, 1), (357, 0, 12, 2375, 0, 0, 1), (358, 27, 14, 2381, 0, 0, -1), (359, 17, 20, 2384, 0, 0, 1), (360, 0, 22, 2386, 0, 0, 1), (361, 23, 8, 2419, 0, 0, -1), (362, 0, 2, 2435, 0, 0, 1), (363, 0, 21, 2439, 0, 0, 1), (364, 0, 27, 2446, 0, 0, 1), (365, 0, 15, 2450, 0, 0, 1), (366, 0, 6, 2463, 0, 0, 1), (367, 0, 1, 2466, 0, 0, 1), (368, 0, 37, 2468, 0, 0, 1), (369, 35, 37, 2483, 0, 0, 1), (370, 0, 20, 2487, 0, 0, 1), (371, 0, 21, 2494, 0, 0, 1), (372, 0, 27, 2504, 0, 0, 1), (373, 0, 29, 2506, 0, 0, 1), (374, 0, 40, 2512, 0, 0, 1), (375, 18, 4, 2531, 0, 0, -1), (376, 0, 27, 2536, 0, 0, 1), (377, 0, 27, 2537, 0, 0, 1), (378, 0, 40, 2560, 0, 0, 1), (379, 37, 13, 2590, 0, 0, -1), (380, 0, 26, 2613, 0, 0, 1), (381, 0, 4, 2623, 0, 0, 1), (382, 32, 11, 2639, 0, 0, -1), (383, 0, 18, 2640, 0, 0, 1), (384, 0, 9, 2646, 0, 0, 1), (385, 0, 28, 2649, 0, 0, 1), (386, 0, 27, 2660, 0, 0, 1), (387, 0, 14, 2665, 0, 0, 1), (388, 0, 32, 2670, 0, 0, 1), (389, 0, 22, 2679, 0, 0, 1), (390, 21, 34, 2690, 0, 0, 1), (391, 0, 1, 2698, 0, 0, 1), (392, 14, 5, 2717, 0, 0, -1), (393, 0, 16, 2719, 0, 0, 1), (394, 0, 9, 2737, 0, 0, 1), (395, 0, 8, 2747, 0, 0, 1), (396, 0, 13, 2748, 0, 0, 1), (397, 0, 10, 2760, 0, 0, 1), (398, 0, 15, 2763, 0, 0, 1), (399, 0, 27, 2780, 0, 0, 1), (400, 0, 30, 2781, 0, 0, 1), (401, 0, 9, 2787, 0, 0, 1), (402, 0, 18, 2796, 0, 0, 1), (403, 0, 30, 2796, 0, 0, 1), (404, 8, 23, 2802, 0, 0, 1), (405, 0, 31, 2809, 0, 0, 1), (406, 0, 35, 2814, 0, 0, 1), (407, 25, 28, 2827, 0, 0, 1), (408, 0, 26, 2831, 0, 0, 1), (409, 0, 20, 2833, 0, 0, 1), (410, 0, 40, 2835, 0, 0, 1), (411, 0, 25, 2843, 0, 0, 1), (412, 0, 9, 2853, 0, 0, 1), (413, 0, 11, 2856, 0, 0, 1), (414, 0, 16, 2860, 0, 0, 1), (415, 0, 33, 2872, 0, 0, 1), (416, 18, 4, 2882, 0, 0, -1), (417, 0, 28, 2888, 0, 0, 1), (418, 0, 13, 2892, 0, 0, 1), (419, 0, 39, 2895, 0, 0, 1), (420, 0, 9, 2895, 0, 0, 1), (421, 0, 18, 2905, 0, 0, 1), (422, 0, 2, 2917, 0, 0, 1), (423, 0, 32, 2922, 0, 0, 1), (424, 0, 34, 2928, 0, 0, 1), (425, 0, 27, 2930, 0, 0, 1), (426, 1, 18, 2934, 0, 0, 1), (427, 0, 40, 2952, 0, 0, 1), (428, 0, 17, 2954, 0, 0, 1), (429, 12, 26, 2959, 0, 0, 1), (430, 0, 15, 2963, 0, 0, 1), (431, 0, 19, 2965, 0, 0, 1), (432, 0, 30, 2968, 0, 0, 1), (433, 9, 15, 2989, 0, 0, 1), (434, 0, 34, 2994, 0, 0, 1), (435, 0, 29, 3021, 0, 0, 1), (436, 0, 29, 3023, 0, 0, 1), (437, 38, 2, 3034, 0, 0, -1), (438, 27, 28, 3045, 0, 0, 1), (439, 0, 18, 3051, 0, 0, 1), (440, 0, 32, 3067, 0, 0, 1), (441, 0, 32, 3069, 0, 0, 1), (442, 0, 39, 3079, 0, 0, 1), (443, 0, 18, 3089, 0, 0, 1), (444, 0, 34, 3091, 0, 0, 1), (445, 11, 32, 3103, 0, 0, 1), (446, 0, 1, 3115, 0, 0, 1), (447, 0, 7, 3121, 0, 0, 1), (448, 0, 28, 3153, 0, 0, 1), (449, 7, 10, 3169, 0, 0, 1), (450, 2, 21, 3172, 0, 0, 1), (451, 0, 9, 3176, 0, 0, 1), (452, 18, 23, 3184, 0, 0, 1), (453, 0, 29, 3186, 0, 0, 1), (454, 0, 23, 3197, 0, 0, 1), (455, 0, 40, 3200, 0, 0, 1), (456, 0, 31, 3220, 0, 0, 1), (457, 0, 35, 3222, 0, 0, 1), (458, 0, 3, 3232, 0, 0, 1), (459, 0, 28, 3240, 0, 0, 1), (460, 0, 31, 3259, 0, 0, 1), (461, 0, 19, 3261, 0, 0, 1), (462, 0, 29, 3275, 0, 0, 1), (463, 0, 33, 3276, 0, 0, 1), (464, 10, 27, 3279, 0, 0, 1), (465, 0, 27, 3298, 0, 0, 1), (466, 0, 33, 3305, 0, 0, 1), (467, 24, 10, 3306, 0, 0, -1), (468, 0, 22, 3310, 0, 0, 1), (469, 0, 5, 3312, 0, 0, 1), (470, 0, 24, 3313, 0, 0, 1), (471, 0, 15, 3313, 0, 0, 1), (472, 0, 16, 3325, 0, 0, 1), (473, 0, 6, 3340, 0, 0, 1), (474, 0, 12, 3341, 0, 0, 1), (475, 0, 20, 3342, 0, 0, 1), (476, 0, 5, 3343, 0, 0, 1), (477, 0, 17, 3345, 0, 0, 1), (478, 14, 23, 3355, 0, 0, 1), (479, 6, 13, 3371, 0, 0, 1), (480, 33, 11, 3372, 0, 0, -1), (481, 0, 23, 3386, 0, 0, 1), (482, 0, 34, 3388, 0, 0, 1), (483, 0, 21, 3388, 0, 0, 1), (484, 0, 12, 3391, 0, 0, 1), (485, 0, 25, 3393, 0, 0, 1), (486, 13, 26, 3395, 0, 0, 1), (487, 0, 15, 3398, 0, 0, 1), (488, 0, 6, 3402, 0, 0, 1), (489, 0, 25, 3408, 0, 0, 1), (490, 0, 4, 3412, 0, 0, 1), (491, 0, 36, 3422, 0, 0, 1), (492, 0, 21, 3422, 0, 0, 1), (493, 35, 20, 3428, 0, 0, -1), (494, 0, 26, 3428, 0, 0, 1), (495, 0, 22, 3432, 0, 0, 1), (496, 0, 19, 3435, 0, 0, 1), (497, 37, 0, 3442, 0, 0, -1), (498, 36, 18, 3445, 0, 0, -1), (499, 12, 38, 3448, 0, 0, 1), (500, 0, 31, 3472, 0, 0, 1), (501, 0, 7, 3473, 0, 0, 1), (502, 0, 32, 3477, 0, 0, 1), (503, 0, 14, 3479, 0, 0, 1), (504, 0, 20, 3482, 0, 0, 1), (505, 0, 14, 3483, 0, 0, 1), (506, 0, 19, 3487, 0, 0, 1), (507, 0, 9, 3495, 0, 0, 1), (508, 0, 19, 3499, 0, 0, 1), (509, 0, 35, 3499, 0, 0, 1), (510, 17, 23, 3510, 0, 0, 1), (511, 0, 34, 3543, 0, 0, 1), (512, 0, 9, 3544, 0, 0, 1), (513, 0, 24, 3551, 0, 0, 1), (514, 0, 25, 3556, 0, 0, 1), (515, 0, 23, 3576, 0, 0, 1), (516, 4, 27, 3579, 0, 0, 1), (517, 0, 37, 3581, 0, 0, 1), (518, 0, 23, 3595, 0, 0, 1), (519, 34, 4, 3607, 0, 0, -1), (520, 20, 30, 3617, 0, 0, 1), (521, 0, 27, 3621, 0, 0, 1), (522, 9, 38, 3640, 0, 0, 1), (523, 2, 3, 3650, 0, 0, 1), (524, 0, 37, 3652, 0, 0, 1), (525, 0, 20, 3654, 0, 0, 1), (526, 1, 38, 3661, 0, 0, 1), (527, 0, 9, 3666, 0, 0, 1), (528, 0, 7, 3669, 0, 0, 1), (529, 3, 8, 3675, 0, 0, 1), (530, 0, 34, 3676, 0, 0, 1), (531, 0, 4, 3683, 0, 0, 1), (532, 40, 15, 3684, 0, 0, -1), (533, 0, 24, 3704, 0, 0, 1), (534, 0, 23, 3718, 0, 0, 1), (535, 0, 19, 3743, 0, 0, 1), (536, 0, 3, 3747, 0, 0, 1), (537, 0, 37, 3750, 0, 0, 1), (538, 8, 12, 3770, 0, 0, 1), (539, 0, 34, 3772, 0, 0, 1), (540, 0, 24, 3781, 0, 0, 1), (541, 34, 24, 3785, 0, 0, -1), (542, 0, 18, 3789, 0, 0, 1), (543, 27, 2, 3798, 0, 0, -1), (544, 0, 38, 3803, 0, 0, 1), (545, 0, 14, 3812, 0, 0, 1), (546, 0, 31, 3820, 0, 0, 1), (547, 0, 16, 3820, 0, 0, 1), (548, 0, 36, 3834, 0, 0, 1), (549, 0, 19, 3845, 0, 0, 1), (550, 21, 39, 3851, 0, 0, 1), (551, 38, 7, 3866, 0, 0, -1), (552, 0, 32, 3890, 0, 0, 1), (553, 0, 25, 3901, 0, 0, 1), (554, 0, 15, 3904, 0, 0, 1), (555, 20, 7, 3906, 0, 0, -1), (556, 35, 16, 3909, 0, 0, -1), (557, 0, 38, 3916, 0, 0, 1), (558, 8, 40, 3916, 0, 0, 1), (559, 0, 37, 3923, 0, 0, 1), (560, 0, 8, 3927, 0, 0, 1), (561, 3, 30, 3929, 0, 0, 1), (562, 0, 33, 3951, 0, 0, 1), (563, 0, 33, 3954, 0, 0, 1), (564, 0, 21, 3957, 0, 0, 1), (565, 16, 19, 3961, 0, 0, 1), (566, 0, 7, 3964, 0, 0, 1), (567, 0, 27, 3966, 0, 0, 1), (568, 0, 21, 3969, 0, 0, 1), (569, 0, 31, 3971, 0, 0, 1), (570, 0, 30, 3982, 0, 0, 1), (571, 0, 33, 3987, 0, 0, 1), (572, 0, 31, 3992, 0, 0, 1), (573, 0, 38, 3993, 0, 0, 1), (574, 0, 17, 3995, 0, 0, 1), (575, 0, 34, 4001, 0, 0, 1), (576, 0, 22, 4003, 0, 0, 1), (577, 0, 25, 4012, 0, 0, 1), (578, 0, 8, 4022, 0, 0, 1), (579, 11, 37, 4029, 0, 0, 1), (580, 0, 10, 4030, 0, 0, 1), (581, 0, 37, 4057, 0, 0, 1), (582, 17, 35, 4064, 0, 0, 1), (583, 35, 5, 4076, 0, 0, -1), (584, 0, 9, 4078, 0, 0, 1), (585, 0, 30, 4083, 0, 0, 1), (586, 0, 3, 4086, 0, 0, 1), (587, 0, 11, 4092, 0, 0, 1), (588, 0, 39, 4095, 0, 0, 1), (589, 0, 7, 4103, 0, 0, 1), (590, 0, 30, 4117, 0, 0, 1), (591, 0, 3, 4123, 0, 0, 1), (592, 29, 8, 4127, 0, 0, -1), (593, 0, 19, 4135, 0, 0, 1), (594, 0, 14, 4146, 0, 0, 1), (595, 25, 21, 4150, 0, 0, -1), (596, 0, 17, 4158, 0, 0, 1), (597, 39, 3, 4174, 0, 0, -1), (598, 0, 21, 4178, 0, 0, 1), (599, 0, 32, 4203, 0, 0, 1), (600, 33, 23, 4206, 0, 0, -1), (601, 0, 26, 4208, 0, 0, 1), (602, 0, 7, 4215, 0, 0, 1), (603, 0, 25, 4220, 0, 0, 1), (604, 0, 27, 4224, 0, 0, 1), (605, 0, 8, 4231, 0, 0, 1), (606, 0, 1, 4234, 0, 0, 1), (607, 0, 37, 4254, 0, 0, 1), (608, 0, 9, 4261, 0, 0, 1), (609, 0, 21, 4305, 0, 0, 1), (610, 0, 22, 4325, 0, 0, 1), (611, 0, 1, 4345, 0, 0, 1), (612, 0, 22, 4349, 0, 0, 1), (613, 0, 21, 4356, 0, 0, 1), (614, 0, 30, 4357, 0, 0, 1), (615, 0, 39, 4357, 0, 0, 1), (616, 0, 15, 4366, 0, 0, 1), (617, 0, 11, 4367, 0, 0, 1), (618, 0, 1, 4374, 0, 0, 1), (619, 0, 13, 4377, 0, 0, 1), (620, 0, 22, 4379, 0, 0, 1), (621, 14, 7, 4388, 0, 0, -1), (622, 0, 17, 4406, 0, 0, 1), (623, 0, 23, 4432, 0, 0, 1), (624, 31, 30, 4436, 0, 0, -1), (625, 33, 22, 4445, 0, 0, -1), (626, 0, 18, 4446, 0, 0, 1), (627, 0, 28, 4449, 0, 0, 1), (628, 0, 11, 4455, 0, 0, 1), (629, 0, 1, 4458, 0, 0, 1), (630, 0, 33, 4463, 0, 0, 1), (631, 0, 19, 4469, 0, 0, 1), (632, 0, 8, 4471, 0, 0, 1), (633, 2, 22, 4483, 0, 0, 1), (634, 12, 33, 4501, 0, 0, 1), (635, 0, 24, 4504, 0, 0, 1), (636, 0, 35, 4508, 0, 0, 1), (637, 35, 18, 4513, 0, 0, -1), (638, 0, 30, 4527, 0, 0, 1), (639, 0, 16, 4536, 0, 0, 1), (640, 0, 12, 4555, 0, 0, 1), (641, 0, 32, 4560, 0, 0, 1), (642, 0, 19, 4568, 0, 0, 1), (643, 21, 3, 4599, 0, 0, -1), (644, 0, 9, 4600, 0, 0, 1), (645, 0, 26, 4600, 0, 0, 1), (646, 0, 24, 4603, 0, 0, 1), (647, 0, 18, 4616, 0, 0, 1), (648, 4, 25, 4627, 0, 0, 1), (649, 0, 31, 4633, 0, 0, 1), (650, 36, 16, 4634, 0, 0, -1), (651, 26, 25, 4635, 0, 0, -1), (652, 0, 37, 4635, 0, 0, 1), (653, 2, 17, 4639, 0, 0, 1), (654, 0, 17, 4645, 0, 0, 1), (655, 0, 30, 4649, 0, 0, 1), (656, 0, 40, 4651, 0, 0, 1), (657, 0, 1, 4653, 0, 0, 1), (658, 0, 1, 4658, 0, 0, 1), (659, 20, 12, 4658, 0, 0, -1), (660, 0, 25, 4660, 0, 0, 1), (661, 27, 28, 4671, 0, 0, 1), (662, 0, 14, 4672, 0, 0, 1), (663, 0, 39, 4673, 0, 0, 1), (664, 18, 21, 4690, 0, 0, 1), (665, 0, 28, 4696, 0, 0, 1), (666, 0, 18, 4698, 0, 0, 1), (667, 0, 30, 4699, 0, 0, 1), (668, 0, 31, 4706, 0, 0, 1), (669, 0, 30, 4707, 0, 0, 1), (670, 0, 8, 4708, 0, 0, 1), (671, 0, 38, 4709, 0, 0, 1), (672, 9, 0, 4711, 0, 0, -1), (673, 11, 33, 4720, 0, 0, 1), (674, 28, 37, 4729, 0, 0, 1), (675, 0, 18, 4730, 0, 0, 1), (676, 8, 24, 4735, 0, 0, 1), (677, 0, 20, 4738, 0, 0, 1), (678, 0, 22, 4739, 0, 0, 1), (679, 0, 24, 4747, 0, 0, 1), (680, 0, 21, 4749, 0, 0, 1), (681, 0, 17, 4750, 0, 0, 1), (682, 0, 2, 4750, 0, 0, 1), (683, 0, 39, 4751, 0, 0, 1), (684, 6, 39, 4751, 0, 0, 1), (685, 0, 6, 4759, 0, 0, 1), (686, 0, 7, 4761, 0, 0, 1), (687, 4, 7, 4769, 0, 0, 1), (688, 0, 31, 4769, 0, 0, 1), (689, 0, 35, 4771, 0, 0, 1), (690, 0, 9, 4796, 0, 0, 1), (691, 28, 40, 4798, 0, 0, 1), (692, 0, 8, 4803, 0, 0, 1), (693, 0, 26, 4805, 0, 0, 1), (694, 14, 24, 4845, 0, 0, 1), (695, 0, 35, 4845, 0, 0, 1), (696, 0, 17, 4862, 0, 0, 1), (697, 0, 21, 4864, 0, 0, 1), (698, 0, 24, 4869, 0, 0, 1), (699, 0, 1, 4871, 0, 0, 1), (700, 15, 21, 4878, 0, 0, 1), (701, 0, 35, 4882, 0, 0, 1), (702, 0, 23, 4899, 0, 0, 1), (703, 0, 14, 4900, 0, 0, 1), (704, 0, 37, 4907, 0, 0, 1), (705, 0, 6, 4921, 0, 0, 1), (706, 0, 1, 4922, 0, 0, 1), (707, 0, 21, 4928, 0, 0, 1), (708, 27, 10, 4959, 0, 0, -1), (709, 0, 23, 4968, 0, 0, 1), (710, 0, 26, 4996, 0, 0, 1), (711, 0, 24, 4999, 0, 0, 1), (712, 0, 23, 5004, 0, 0, 1), (713, 32, 16, 5004, 0, 0, -1), (714, 11, 13, 5008, 0, 0, 1), (715, 0, 30, 5012, 0, 0, 1), (716, 0, 2, 5016, 0, 0, 1), (717, 0, 20, 5027, 0, 0, 1), (718, 0, 27, 5032, 0, 0, 1), (719, 0, 9, 5034, 0, 0, 1), (720, 14, 40, 5050, 0, 0, 1), (721, 0, 12, 5053, 0, 0, 1), (722, 0, 28, 5061, 0, 0, 1), (723, 0, 3, 5063, 0, 0, 1), (724, 0, 14, 5064, 0, 0, 1), (725, 0, 26, 5070, 0, 0, 1), (726, 27, 0, 5076, 0, 0, -1), (727, 0, 14, 5082, 0, 0, 1), (728, 0, 38, 5084, 0, 0, 1), (729, 0, 40, 5085, 0, 0, 1), (730, 0, 10, 5093, 0, 0, 1), (731, 0, 36, 5094, 0, 0, 1), (732, 0, 31, 5100, 0, 0, 1), (733, 0, 4, 5115, 0, 0, 1), (734, 0, 27, 5120, 0, 0, 1), (735, 0, 40, 5123, 0, 0, 1), (736, 0, 34, 5127, 0, 0, 1), (737, 24, 15, 5135, 0, 0, -1), (738, 0, 37, 5144, 0, 0, 1), (739, 0, 17, 5150, 0, 0, 1), (740, 0, 21, 5156, 0, 0, 1), (741, 0, 16, 5158, 0, 0, 1), (742, 0, 15, 5173, 0, 0, 1), (743, 0, 14, 5184, 0, 0, 1), (744, 0, 21, 5188, 0, 0, 1), (745, 0, 19, 5189, 0, 0, 1), (746, 32, 15, 5195, 0, 0, -1), (747, 25, 34, 5198, 0, 0, 1), (748, 0, 20, 5211, 0, 0, 1), (749, 0, 37, 5218, 0, 0, 1), (750, 0, 18, 5221, 0, 0, 1), (751, 0, 33, 5245, 0, 0, 1), (752, 10, 14, 5253, 0, 0, 1), (753, 0, 40, 5258, 0, 0, 1), (754, 0, 32, 5268, 0, 0, 1), (755, 0, 1, 5268, 0, 0, 1), (756, 0, 13, 5275, 0, 0, 1), (757, 0, 25, 5279, 0, 0, 1), (758, 40, 22, 5279, 0, 0, -1), (759, 0, 1, 5287, 0, 0, 1), (760, 0, 31, 5293, 0, 0, 1), (761, 17, 28, 5294, 0, 0, 1), (762, 0, 15, 5299, 0, 0, 1), (763, 0, 12, 5343, 0, 0, 1), (764, 32, 3, 5344, 0, 0, -1), (765, 0, 20, 5344, 0, 0, 1), (766, 11, 10, 5360, 0, 0, -1), (767, 0, 28, 5363, 0, 0, 1), (768, 0, 17, 5376, 0, 0, 1), (769, 0, 15, 5377, 0, 0, 1), (770, 0, 2, 5378, 0, 0, 1), (771, 0, 5, 5380, 0, 0, 1), (772, 37, 7, 5380, 0, 0, -1), (773, 0, 6, 5385, 0, 0, 1), (774, 0, 8, 5386, 0, 0, 1), (775, 0, 9, 5390, 0, 0, 1), (776, 37, 23, 5393, 0, 0, -1), (777, 0, 12, 5400, 0, 0, 1), (778, 24, 8, 5409, 0, 0, -1), (779, 0, 15, 5410, 0, 0, 1), (780, 39, 13, 5414, 0, 0, -1), (781, 4, 39, 5416, 0, 0, 1), (782, 0, 40, 5427, 0, 0, 1), (783, 0, 16, 5428, 0, 0, 1), (784, 0, 30, 5432, 0, 0, 1), (785, 22, 37, 5432, 0, 0, 1), (786, 0, 34, 5443, 0, 0, 1), (787, 0, 1, 5455, 0, 0, 1), (788, 0, 1, 5455, 0, 0, 1), (789, 0, 29, 5455, 0, 0, 1), (790, 6, 14, 5455, 0, 0, 1), (791, 0, 15, 5458, 0, 0, 1), (792, 0, 9, 5461, 0, 0, 1), (793, 0, 6, 5462, 0, 0, 1), (794, 0, 21, 5468, 0, 0, 1), (795, 0, 27, 5477, 0, 0, 1), (796, 26, 25, 5477, 0, 0, -1), (797, 0, 15, 5511, 0, 0, 1), (798, 0, 36, 5520, 0, 0, 1), (799, 0, 8, 5523, 0, 0, 1), (800, 35, 20, 5527, 0, 0, -1), (801, 0, 13, 5545, 0, 0, 1), (802, 0, 10, 5547, 0, 0, 1), (803, 0, 6, 5552, 0, 0, 1), (804, 0, 28, 5566, 0, 0, 1), (805, 0, 9, 5575, 0, 0, 1), (806, 0, 12, 5581, 0, 0, 1), (807, 0, 40, 5596, 0, 0, 1), (808, 0, 17, 5596, 0, 0, 1), (809, 22, 13, 5601, 0, 0, -1), (810, 23, 7, 5601, 0, 0, -1), (811, 0, 13, 5602, 0, 0, 1), (812, 0, 29, 5605, 0, 0, 1), (813, 0, 16, 5611, 0, 0, 1), (814, 20, 5, 5622, 0, 0, -1), (815, 0, 40, 5626, 0, 0, 1), (816, 0, 20, 5628, 0, 0, 1), (817, 0, 35, 5635, 0, 0, 1), (818, 0, 19, 5635, 0, 0, 1), (819, 0, 16, 5635, 0, 0, 1), (820, 0, 4, 5636, 0, 0, 1), (821, 0, 9, 5638, 0, 0, 1), (822, 0, 37, 5639, 0, 0, 1), (823, 0, 35, 5649, 0, 0, 1), (824, 0, 6, 5662, 0, 0, 1), (825, 0, 1, 5665, 0, 0, 1), (826, 0, 40, 5671, 0, 0, 1), (827, 0, 8, 5684, 0, 0, 1), (828, 20, 39, 5685, 0, 0, 1), (829, 0, 32, 5698, 0, 0, 1), (830, 0, 11, 5702, 0, 0, 1), (831, 0, 16, 5704, 0, 0, 1), (832, 0, 16, 5710, 0, 0, 1), (833, 0, 4, 5714, 0, 0, 1), (834, 0, 25, 5720, 0, 0, 1), (835, 0, 14, 5727, 0, 0, 1), (836, 2, 24, 5727, 0, 0, 1), (837, 18, 37, 5744, 0, 0, 1), (838, 0, 38, 5745, 0, 0, 1), (839, 36, 2, 5754, 0, 0, -1), (840, 37, 12, 5760, 0, 0, -1), (841, 0, 11, 5764, 0, 0, 1), (842, 0, 38, 5780, 0, 0, 1), (843, 0, 4, 5795, 0, 0, 1), (844, 29, 1, 5797, 0, 0, -1), (845, 34, 0, 5803, 0, 0, -1), (846, 0, 9, 5816, 0, 0, 1), (847, 2, 12, 5819, 0, 0, 1), (848, 0, 31, 5843, 0, 0, 1), (849, 0, 10, 5843, 0, 0, 1), (850, 0, 30, 5845, 0, 0, 1), (851, 40, 19, 5853, 0, 0, -1), (852, 0, 24, 5854, 0, 0, 1), (853, 0, 3, 5862, 0, 0, 1), (854, 0, 5, 5869, 0, 0, 1), (855, 0, 19, 5889, 0, 0, 1), (856, 0, 11, 5900, 0, 0, 1), (857, 0, 17, 5921, 0, 0, 1), (858, 0, 13, 5926, 0, 0, 1), (859, 0, 37, 5927, 0, 0, 1), (860, 0, 27, 5932, 0, 0, 1), (861, 0, 2, 5940, 0, 0, 1), (862, 0, 37, 5963, 0, 0, 1), (863, 0, 13, 5966, 0, 0, 1), (864, 0, 37, 5967, 0, 0, 1), (865, 19, 30, 5984, 0, 0, 1), (866, 0, 40, 5986, 0, 0, 1), (867, 0, 36, 6016, 0, 0, 1), (868, 0, 19, 6032, 0, 0, 1), (869, 0, 21, 6034, 0, 0, 1), (870, 0, 16, 6041, 0, 0, 1), (871, 0, 34, 6045, 0, 0, 1), (872, 1, 6, 6046, 0, 0, 1), (873, 0, 13, 6049, 0, 0, 1), (874, 39, 36, 6058, 0, 0, -1), (875, 0, 11, 6066, 0, 0, 1), (876, 0, 7, 6067, 0, 0, 1), (877, 0, 30, 6074, 0, 0, 1), (878, 0, 17, 6088, 0, 0, 1), (879, 0, 20, 6097, 0, 0, 1), (880, 15, 12, 6098, 0, 0, -1), (881, 5, 16, 6100, 0, 0, 1), (882, 0, 5, 6100, 0, 0, 1), (883, 0, 1, 6123, 0, 0, 1), (884, 33, 18, 6134, 0, 0, -1), (885, 0, 11, 6138, 0, 0, 1), (886, 0, 31, 6143, 0, 0, 1), (887, 0, 3, 6145, 0, 0, 1), (888, 0, 40, 6145, 0, 0, 1), (889, 0, 20, 6149, 0, 0, 1), (890, 0, 29, 6158, 0, 0, 1), (891, 0, 16, 6159, 0, 0, 1), (892, 0, 15, 6163, 0, 0, 1), (893, 0, 31, 6174, 0, 0, 1), (894, 0, 39, 6187, 0, 0, 1), (895, 0, 31, 6207, 0, 0, 1), (896, 0, 23, 6213, 0, 0, 1), (897, 0, 16, 6218, 0, 0, 1), (898, 26, 40, 6230, 0, 0, 1), (899, 0, 27, 6241, 0, 0, 1), (900, 0, 29, 6241, 0, 0, 1), (901, 0, 31, 6244, 0, 0, 1), (902, 0, 26, 6248, 0, 0, 1), (903, 0, 12, 6257, 0, 0, 1), (904, 0, 8, 6262, 0, 0, 1), (905, 0, 19, 6274, 0, 0, 1), (906, 0, 24, 6301, 0, 0, 1), (907, 11, 13, 6302, 0, 0, 1), (908, 0, 4, 6324, 0, 0, 1), (909, 0, 27, 6326, 0, 0, 1), (910, 0, 32, 6329, 0, 0, 1), (911, 7, 24, 6336, 0, 0, 1), (912, 0, 9, 6349, 0, 0, 1), (913, 0, 22, 6364, 0, 0, 1), (914, 0, 19, 6375, 0, 0, 1), (915, 38, 29, 6378, 0, 0, -1), (916, 0, 30, 6378, 0, 0, 1), (917, 0, 22, 6382, 0, 0, 1), (918, 0, 18, 6399, 0, 0, 1), (919, 0, 11, 6417, 0, 0, 1), (920, 0, 38, 6428, 0, 0, 1), (921, 18, 37, 6441, 0, 0, 1), (922, 29, 1, 6445, 0, 0, -1), (923, 0, 26, 6450, 0, 0, 1), (924, 0, 29, 6453, 0, 0, 1), (925, 0, 16, 6462, 0, 0, 1), (926, 0, 18, 6462, 0, 0, 1), (927, 37, 12, 6465, 0, 0, -1), (928, 0, 2, 6471, 0, 0, 1), (929, 0, 14, 6476, 0, 0, 1), (930, 0, 8, 6481, 0, 0, 1), (931, 0, 28, 6488, 0, 0, 1), (932, 0, 26, 6507, 0, 0, 1), (933, 0, 6, 6514, 0, 0, 1), (934, 0, 33, 6518, 0, 0, 1), (935, 0, 10, 6538, 0, 0, 1), (936, 0, 11, 6543, 0, 0, 1), (937, 0, 13, 6548, 0, 0, 1), (938, 0, 1, 6555, 0, 0, 1), (939, 0, 20, 6580, 0, 0, 1), (940, 0, 2, 6601, 0, 0, 1), (941, 0, 34, 6605, 0, 0, 1), (942, 18, 13, 6608, 0, 0, -1), (943, 0, 25, 6611, 0, 0, 1), (944, 0, 15, 6612, 0, 0, 1), (945, 0, 1, 6617, 0, 0, 1), (946, 0, 30, 6620, 0, 0, 1), (947, 0, 19, 6624, 0, 0, 1), (948, 0, 19, 6628, 0, 0, 1), (949, 0, 2, 6630, 0, 0, 1), (950, 0, 17, 6653, 0, 0, 1), (951, 8, 10, 6663, 0, 0, 1), (952, 0, 32, 6666, 0, 0, 1), (953, 0, 12, 6672, 0, 0, 1), (954, 35, 17, 6674, 0, 0, -1), (955, 32, 13, 6684, 0, 0, -1), (956, 0, 1, 6684, 0, 0, 1), (957, 6, 12, 6703, 0, 0, 1), (958, 0, 38, 6720, 0, 0, 1), (959, 0, 29, 6721, 0, 0, 1), (960, 0, 28, 6747, 0, 0, 1), (961, 0, 6, 6752, 0, 0, 1), (962, 0, 35, 6753, 0, 0, 1), (963, 0, 35, 6755, 0, 0, 1), (964, 18, 14, 6756, 0, 0, -1), (965, 0, 5, 6759, 0, 0, 1), (966, 0, 24, 6778, 0, 0, 1), (967, 0, 40, 6781, 0, 0, 1), (968, 10, 20, 6793, 0, 0, 1), (969, 0, 15, 6795, 0, 0, 1), (970, 0, 37, 6797, 0, 0, 1), (971, 34, 9, 6805, 0, 0, -1), (972, 10, 39, 6805, 0, 0, 1), (973, 0, 6, 6809, 0, 0, 1), (974, 0, 11, 6813, 0, 0, 1), (975, 0, 36, 6820, 0, 0, 1), (976, 29, 2, 6826, 0, 0, -1), (977, 0, 34, 6838, 0, 0, 1), (978, 0, 4, 6852, 0, 0, 1), (979, 36, 11, 6857, 0, 0, -1), (980, 27, 1, 6859, 0, 0, -1), (981, 0, 16, 6861, 0, 0, 1), (982, 25, 39, 6889, 0, 0, 1), (983, 0, 35, 6897, 0, 0, 1), (984, 4, 7, 6898, 0, 0, 1), (985, 0, 3, 6901, 0, 0, 1), (986, 11, 36, 6909, 0, 0, 1), (987, 0, 33, 6915, 0, 0, 1), (988, 0, 16, 6918, 0, 0, 1), (989, 0, 16, 6920, 0, 0, 1), (990, 0, 19, 6927, 0, 0, 1), (991, 27, 14, 6928, 0, 0, -1), (992, 17, 1, 6931, 0, 0, -1), (993, 35, 30, 6949, 0, 0, -1), (994, 0, 32, 6952, 0, 0, 1), (995, 20, 27, 6955, 0, 0, 1), (996, 20, 17, 6969, 0, 0, -1), (997, 23, 1, 6971, 0, 0, -1), (998, 0, 21, 6973, 0, 0, 1), (999, 35, 26, 6974, 0, 0, -1), (1000, 0, 27, 6991, 0, 0, 1), (1001, 0, 31, 7001, 0, 0, 1), (1002, 0, 17, 7002, 0, 0, 1), (1003, 37, 21, 7002, 0, 0, -1), (1004, 0, 34, 7015, 0, 0, 1), (1005, 0, 20, 7055, 0, 0, 1), (1006, 0, 5, 7058, 0, 0, 1), (1007, 0, 22, 7084, 0, 0, 1), (1008, 0, 40, 7096, 0, 0, 1), (1009, 21, 15, 7113, 0, 0, -1), (1010, 0, 35, 7113, 0, 0, 1), (1011, 0, 21, 7125, 0, 0, 1), (1012, 0, 39, 7128, 0, 0, 1), (1013, 2, 9, 7141, 0, 0, 1), (1014, 0, 17, 7145, 0, 0, 1), (1015, 0, 39, 7146, 0, 0, 1), (1016, 40, 5, 7147, 0, 0, -1), (1017, 0, 8, 7160, 0, 0, 1), (1018, 0, 16, 7163, 0, 0, 1), (1019, 0, 9, 7165, 0, 0, 1), (1020, 0, 5, 7174, 0, 0, 1)]
elevator = DualLiftSystem(
            current_floor_A=current_floor_A,
            current_floor_B=current_floor_B,
            num_floors=num_floors,
            filepath=file_path,
            Passenger_limit=passenger_limit,
            T_high_oscillation=T_high_oscillation,
            T_low_oscillation=T_low_oscillation,
            current_density=current_density,
            delta_time=delta_time,
            T_high_VIP=T_high_VIP,
            T_low_VIP=T_low_VIP,
            current_time=0
        )

elevator.run_simulation(passenger_data=data)
print("We has seucs")