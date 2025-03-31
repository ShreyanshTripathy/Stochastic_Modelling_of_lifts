import random
import numpy as np
import pandas as pd
'''Working Perfectly'''
class DualLiftSystem:

    '''This elevator is trying to simulate the real life situation of passengers arriving at varied times'''

    def __init__(self, current_floor_A,current_floor_B, num_floors,filepath, Passenger_limit, current_time = 0):
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
            current_floor = self.current_floor_A
        else:
            copy_list = self.pending_orders_B.copy()
            current_floor = self.current_floor_B
        eligible_orders = []
        dropped = 0
        for order in copy_list:
            dont_pick = False
            direction = order[-1]

            dropped += self.drop_passenger(order,lift_name)
            
            if order[1] == current_floor:
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
                self.df_read.loc[self.df_read["Index"] == Index, "Order completion time"] = self.current_time

                # Extract the updated tuple
                updated_tuple = self.df_read.loc[self.df_read["Index"] == Index].iloc[0]
                
                updated_tuple = tuple(updated_tuple)
                
                self.orders_done.append(updated_tuple)
                
                print(f"update_line: {updated_tuple}")
                
                # Reload the DataFrame to reflect the changes
                
                self.df_read = pd.read_csv(self.filepath)
            
                

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
            
            if len(eligible_orders) > available_space:
                # Pick only the number of passengers that can be accommodated
                Orders_tobe_picked = random.sample(eligible_orders, available_space)
                for orders in eligible_orders:
                    if orders not in Orders_tobe_picked:#do something about the ordersnot picked
                        passenger_data.append(orders)
                        if lift_name=="A":
                            self.pending_orders_A.remove(orders)
                        if lift_name=="B":
                            self.pending_orders_B.remove(orders)  
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
                
        if lift_name=="A":
            self.direction_A=lift_direction
            self.status_A = started
        else:
            self.direction_B=lift_direction
            self.status_B = started
                            
        return passenger_data, pending_orders
        
    
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
                else:
                    if ((self.direction_A>0 and direction>0 and passenger_position>self.current_floor_A) or (self.direction_A<0 and direction<0 and passenger_position<=self.current_floor_A)) and (passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A)):
                        liftA_orders.append(passenger)
                        print(f"\n {passenger} appended to lift A")
                        prospective_people_in_liftA=1
            
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
                else:
                    if ((self.direction_B>0 and direction>0 and passenger_position>self.current_floor_B) or (self.direction_B<0 and direction<0 and passenger_position<=self.current_floor_B)) and (passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A)):
                        liftB_orders.append(passenger)
                        print(f"\n {passenger} appended to lift B")
                        prospective_people_in_liftB=1
            

            elif distance_from_A == distance_from_B:
                lift_name = random.choice(["A","B"])
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
                    print(f"{person} removed from {name} to {name1}")
        return source_list, target_list
                  
    def run_simulation(self, passenger_data):
        '''This simulates the lift'''       
        people_not_assigned = []
        number_lift_B_picked=0
        number_lift_A_picked=0
        dropped_by_B=0
        dropped_by_A=0
        while passenger_data or self.pending_orders_A or self.pending_orders_B:
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
            
            print(self.current_floor_B)
            print(self.current_floor_A)
            pending_orders = []
            pending_orders_A = []
            pending_orders_B = []
            pending_orders = [p for p in passenger_data if p[3] <= self.current_time]
            pending_orders = sorted(pending_orders, key=lambda x: x[3])
            print("pending_orders",pending_orders)
            
            pending_orders_A, pending_orders_B = self.assign_passengers(pending_orders)

            # Ensure that the same pending_orders_A is passed to data_sorter
            pending_orders_A = self.data_sorter(pending_orders_A, self.current_floor_A)
            
            pending_orders_A = sorted(pending_orders_A, key=lambda x: x[3])
            
            pending_orders_B = self.data_sorter(pending_orders_B, self.current_floor_B)
            
            pending_orders_B = sorted(pending_orders_B, key=lambda x: x[3])
            
            passenger_data,pending_orders= self.queue_maker(pending_orders=pending_orders_A, passenger_data=passenger_data,lift_name="A")
            
            passenger_data,pending_orders = self.queue_maker(pending_orders=pending_orders_B, passenger_data=passenger_data, lift_name="B")
            
            for person in passenger_data:
                if person in pending_orders and person not in self.pending_orders_A and person not in self.pending_orders_B and person not in people_not_assigned:
                    people_not_assigned.append(person)
            
            #checking on each floor to see if there is a passenger going in the same direction as the lift even if he or she was not the closest to the lift and would be efficient
            for person in list(self.pending_orders_B).copy():
                self.pending_orders_B, self.pending_orders_A = self.reassign_passenger(person, self.pending_orders_B, self.pending_orders_A, self.current_floor_A, self.direction_A)
            for person in list(self.pending_orders_A).copy():
                self.pending_orders_A, self.pending_orders_B = self.reassign_passenger(person, self.pending_orders_A, self.pending_orders_B, self.current_floor_B, self.direction_B)
            print(f"Pending_order_B  = {self.pending_orders_B}")
            print(f"Pending_order_A  = {self.pending_orders_A}")
            
            for person in people_not_assigned[:]:
                if person in self.pending_orders_A or person in self.pending_orders_B:
                    people_not_assigned.remove(person)
                    print(person)

            # Using a copy of the list to avoid modification issues during iteration
            for person in list(people_not_assigned):
                people_not_assigned, self.pending_orders_A = self.reassign_passenger(person, people_not_assigned, self.pending_orders_A, self.current_floor_A, self.direction_A)
                people_not_assigned, self.pending_orders_B = self.reassign_passenger(person, people_not_assigned, self.pending_orders_B, self.current_floor_B, self.direction_B)
                     
            
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
            
            # Move the lift if there are still pending orders
            lift_A_position = self.current_floor_A
            lift_B_position = self.current_floor_B
            
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
            
            '''                  
             #checking on each floor to see if there is a passenger going in the same direction as the lift even if he or she was not the closest to the lift and would be efficient
            for person in list(self.pending_orders_B):
                self.reassign_passenger(person, self.pending_orders_B, self.pending_orders_A, self.current_floor_A, self.direction_A)
            for person in list(self.pending_orders_A):
                self.reassign_passenger(person, self.pending_orders_A, self.pending_orders_B, self.current_floor_B, self.direction_B)
            
            print(f"Pending_order_B  = {self.pending_orders_B}")
            print(f"Pending_order_A  = {self.pending_orders_A}")
            
            for person in people_not_assigned[:]:
                if person in self.pending_orders_A or person in self.pending_orders_B:
                    people_not_assigned.remove(person)
                                  
            for person in list(people_not_assigned):
                self.reassign_passenger(person,people_not_assigned, self.pending_orders_A, self.current_floor_A, self.direction_A)                     
                self.reassign_passenger(person,people_not_assigned, self.pending_orders_B, self.current_floor_B, self.direction_B)
                
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
            
            print(f"\npending orders A: {self.pending_orders_A}\npending orders B: {self.pending_orders_B}")
            
            if self.pending_orders_A:
                self.status_A=True
                passenger_data,number_lift_A_picked, dropped_by_A = self.serve_stop("A", passenger_data=passenger_data)
            else:
                self.status_A=False
                self.direction = 0
            
            if self.pending_orders_B:
                self.status_B = True
                passenger_data, number_lift_B_picked, dropped_by_B = self.serve_stop("B", passenger_data=passenger_data)
            else:
                self.status_B=False
                self.direction = 0
            '''
            #If the lifts are empty then giving the pending orders a secong chance to be reassigned                
            if self.lift_A_population==0 and self.pending_orders_A and not passenger_data:
                for order in self.pending_orders_A:
                    self.pending_orders_A.remove(order)# This part is for lets say there is A was sirving someone and B is empty so the new passenger gets assigned to B but then A gets empty and becomes the best option then the passenger should be going to A not to B even if it was assigned first. But lets say both are empty then wont it keep switching? no because of the movement of the lift now the lift is the closest to the passenger thus becomes the best option
                    passenger_data.append(order)

            if self.lift_B_population==0 and self.pending_orders_B and not passenger_data:
                for order in self.pending_orders_B:
                    self.pending_orders_B.remove(order)
                    passenger_data.append(order)
            '''
            self.current_time += (number_lift_B_picked + number_lift_A_picked + dropped_by_B + dropped_by_A)*self.passenger_inout
            print(self.current_time)
            # input("continue")
            '''
