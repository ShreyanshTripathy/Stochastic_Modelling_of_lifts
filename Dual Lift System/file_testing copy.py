import random
import numpy as np
import pandas as pd
class DualLiftSystem:

    '''This elevator is trying to simulate the real life situation of passengers arriving at varied times'''

    def __init__(self, current_floor_A,current_floor_B, num_floors,filepath, Passenger_limit, current_time = 0):
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
                
                # # Update the DataFrame
                # self.df_read.loc[self.df_read["Index"] == Index, "Order completion time"] = self.current_time

                # # Extract the updated tuple
                # updated_tuple = self.df_read.loc[self.df_read["Index"] == Index].iloc[0]
                
                # updated_tuple = tuple(updated_tuple)
                
                # self.orders_done.append(updated_tuple)
                
                # print(f"update_line: {updated_tuple}")
                
                # # Reload the DataFrame to reflect the changes
                
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

                # # Update the DataFrame with the new value
                # self.df_read.loc[self.df_read["Index"] == Index, "Lift arrival time"] = self.current_time
                # # Reload the DataFrame to reflect the changes
                # self.df_read.to_csv(self.filepath, index=False)  # Ensure you save the changes to the file

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
                # else:
                #     if ((self.direction_B>0 and direction>0 and passenger_position>self.current_floor_B) or (self.direction_B<0 and direction<0 and passenger_position<=self.current_floor_B)) and (passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A)):
                #         liftB_orders.append(passenger)
                #         print(f"\n {passenger} appended to lift B")
                #         prospective_people_in_liftB=1
            
            # # '''If someone has been added to a lift and they are going in the same direction as the lift then i would like them to be added to the lift'''
            # elif distance_from_A==distance_from_B and (prospective_people_in_liftB!=0 or prospective_people_in_liftA!=0):
            #     if passenger[1]<self.current_floor_B and self.direction_B==-1 and passenger[-1]==-1:
            #         if passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A):
            #                 liftB_orders.append(passenger)
            #                 print(f"\n {passenger} appended to lift B")
            #     elif passenger[1]>self.current_floor_B and self.direction_B==1 and passenger[-1]==1:
            #         if passenger not in (liftA_orders+liftB_orders+self.pending_orders_A+self.pending_orders_B):
            #             liftB_orders.append(passenger)
            #             print(f"\n{passenger} appeded to lift B")
            #     elif passenger[1]<self.current_floor_A and self.direction_A==-1 and passenger[-1]==-1:
            #         if passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A):
            #                 liftA_orders.append(passenger)
            #                 print(f"\n {passenger} appended to lift A")
            #     elif passenger[1]>self.current_floor_A and self.direction_A==1 and passenger[-1]==1:
            #         if passenger not in (liftA_orders+liftB_orders+self.pending_orders_A+self.pending_orders_B):
            #             liftA_orders.append(passenger)
            #             print(f"\n{passenger} appeded to lift A")
            
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
                    print(f"\n{person} removed from {name} to {name1}\n")
                 
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
            for person in list(self.pending_orders_B):
                self.reassign_passenger(person, self.pending_orders_B, self.pending_orders_A, self.current_floor_A, self.direction_A)
            for person in list(self.pending_orders_A):
                self.reassign_passenger(person, self.pending_orders_A, self.pending_orders_B, self.current_floor_B, self.direction_B)

            print(f"Pending_order_B  = {self.pending_orders_B}")
            print(f"Pending_order_A  = {self.pending_orders_A}")
            
            for person in people_not_assigned[:]:
                if person in self.pending_orders_A or person in self.pending_orders_B:
                    people_not_assigned.remove(person)
                    print(person)

            # Using a copy of the list to avoid modification issues during iteration
            for person in list(people_not_assigned):
                self.reassign_passenger(person, people_not_assigned, self.pending_orders_A, self.current_floor_A, self.direction_A)
                self.reassign_passenger(person, people_not_assigned, self.pending_orders_B, self.current_floor_B, self.direction_B)
                     
            
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
            print(self.current_time)
            
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
            # input("continue")
            '''
            self.current_time += (number_lift_B_picked + number_lift_A_picked + dropped_by_B + dropped_by_A)*self.passenger_inout
            print(self.current_time)
            input("continue")
            '''
time = []
for i in range(20):
    number_of_floors = 20
    passenger_limit = 8
    current_floor_A = random.randint(0,20)
    current_floor_B = random.randint(0,20)
    file_path = "Dummy"
    Dual_lift = DualLiftSystem(num_floors=number_of_floors, Passenger_limit=passenger_limit, current_floor_A=current_floor_A, current_floor_B=current_floor_B, filepath=file_path) 
    # data = [(1, 0, 18, 0, 0, 0, 1), (2, 1, 15, 0, 0, 0, 1), (3, 2, 5, 0, 0, 0, 1), (4, 3, 11, 0, 0, 0, 1), (5, 4, 18, 0, 0, 0, 1), (6, 5, 12, 0, 0, 0, 1), (7, 6, 8, 0, 0, 0, 1), (8, 7, 12, 0, 0, 0, 1), (9, 8, 3, 0, 0, 0, -1), (10, 9, 13, 0, 0, 0, 1), (11, 10, 14, 0, 0, 0, 1), (12, 11, 13, 0, 0, 0, 1), (13, 12, 15, 0, 0, 0, 1), (14, 13, 3, 0, 0, 0, -1), (15, 14, 3, 0, 0, 0, -1), (16, 15, 4, 0, 0, 0, -1), (17, 16, 6, 0, 0, 0, -1), (18, 17, 4, 0, 0, 0, -1), (19, 18, 14, 0, 0, 0, -1), (20, 19, 8, 0, 0, 0, -1), (21, 20, 2, 0, 0, 0, -1), (22, 3, 20, 29, 0, 0, 1), (23, 5, 13, 35, 0, 0, 1), (24, 3, 7, 40, 0, 0, 1)]
    # data = [(1, 0, 2, 0, 0, 0, 1), (21, 20, 0, 0, 0, 0, -1), (20, 19, 0, 0, 0, 0, -1), (19, 18, 9, 0, 0, 0, -1), (18, 17, 5, 0, 0, 0, -1), (17, 16, 13, 0, 0, 0, -1), (15, 14, 1, 0, 0, 0, -1), (14, 13, 0, 0, 0, 0, -1), (13, 12, 18, 0, 0, 0, 1), (12, 11, 14, 0, 0, 0, 1), (16, 15, 16, 0, 0, 0, 1), (10, 9, 2, 0, 0, 0, -1), (11, 10, 16, 0, 0, 0, 1), (3, 2, 18, 0, 0, 0, 1), (4, 3, 7, 0, 0, 0, 1), (5, 4, 5, 0, 0, 0, 1), (2, 1, 4, 0, 0, 0, 1), (7, 6, 17, 0, 0, 0, 1), (8, 7, 11, 0, 0, 0, 1), (9, 8, 5, 0, 0, 0, -1), (6, 5, 4, 0, 0, 0, -1), (22, 20, 3, 51, 0, 0, -1), (23, 18, 3, 182, 0, 0, -1), (24, 18, 0, 185, 0, 0, -1), (25, 15, 17, 246, 0, 0, 1), (26, 0, 4, 259, 0, 0, 1), (27, 7, 8, 294, 0, 0, 1), (28, 19, 10, 373, 0, 0, -1), (29, 3, 10, 382, 0, 0, 1), (30, 18, 8, 387, 0, 0, -1), (31, 17, 12, 416, 0, 0, -1), (32, 12, 1, 485, 0, 0, -1), (33, 7, 19, 535, 0, 0, 1), (34, 3, 6, 608, 0, 0, 1), (35, 13, 19, 609, 0, 0, 1), (36, 19, 16, 627, 0, 0, -1), (37, 15, 8, 651, 0, 0, -1), (38, 17, 4, 665, 0, 0, -1), (39, 10, 12, 697, 0, 0, 1), (40, 5, 7, 711, 0, 0, 1), (41, 9, 15, 747, 0, 0, 1), (42, 9, 0, 761, 0, 0, -1), (43, 6, 14, 784, 0, 0, 1), (44, 17, 12, 789, 0, 0, -1), (45, 15, 20, 827, 0, 0, 1), (46, 14, 16, 846, 0, 0, 1), (47, 15, 4, 860, 0, 0, -1), (48, 9, 7, 888, 0, 0, -1), (49, 8, 15, 903, 0, 0, 1), (50, 9, 17, 912, 0, 0, 1), (51, 11, 15, 968, 0, 0, 1), (52, 12, 18, 979, 0, 0, 1), (53, 12, 7, 988, 0, 0, -1), (54, 18, 13, 997, 0, 0, -1), (55, 1, 5, 1024, 0, 0, 1), (56, 13, 20, 1093, 0, 0, 1), (57, 5, 18, 1134, 0, 0, 1), (58, 7, 3, 1151, 0, 0, -1), (59, 3, 14, 1212, 0, 0, 1), (60, 10, 7, 1269, 0, 0, -1), (61, 10, 15, 1311, 0, 0, 1), (62, 6, 4, 1312, 0, 0, -1), (63, 7, 4, 1313, 0, 0, -1), (64, 15, 14, 1365, 0, 0, -1), (65, 5, 9, 1379, 0, 0, 1), (66, 6, 18, 1412, 0, 0, 1), (67, 3, 12, 1424, 0, 0, 1), (68, 9, 14, 1443, 0, 0, 1), (69, 19, 9, 1450, 0, 0, -1), (70, 7, 2, 1460, 0, 0, -1), (71, 11, 2, 1520, 0, 0, -1), (72, 20, 2, 1523, 0, 0, -1), (73, 7, 15, 1607, 0, 0, 1), (74, 19, 4, 1613, 0, 0, -1), (75, 1, 5, 1652, 0, 0, 1), (76, 12, 10, 1655, 0, 0, -1), (77, 15, 2, 1687, 0, 0, -1), (78, 17, 14, 1699, 0, 0, -1), (79, 3, 0, 1718, 0, 0, -1), (80, 0, 19, 1858, 0, 0, 1), (81, 14, 7, 1868, 0, 0, -1), (82, 9, 6, 1918, 0, 0, -1), (83, 6, 7, 1927, 0, 0, 1), (84, 16, 14, 1963, 0, 0, -1), (85, 18, 14, 2003, 0, 0, -1), (86, 20, 17, 2022, 0, 0, -1), (87, 10, 2, 2052, 0, 0, -1), (88, 3, 18, 2075, 0, 0, 1), (89, 18, 13, 2082, 0, 0, -1), (90, 10, 20, 2087, 0, 0, 1), (91, 14, 9, 2090, 0, 0, -1), (92, 6, 20, 2115, 0, 0, 1), (93, 5, 8, 2184, 0, 0, 1), (94, 15, 13, 2185, 0, 0, -1), (95, 0, 3, 2192, 0, 0, 1), (96, 4, 2, 2231, 0, 0, -1), (97, 9, 16, 2244, 0, 0, 1), (98, 10, 20, 2283, 0, 0, 1), (99, 5, 8, 2375, 0, 0, 1), (100, 12, 0, 2443, 0, 0, -1), (101, 5, 15, 2461, 0, 0, 1), (102, 11, 10, 2486, 0, 0, -1), (103, 8, 7, 2493, 0, 0, -1), (104, 20, 0, 2509, 0, 0, -1), (105, 2, 10, 2518, 0, 0, 1), (106, 20, 14, 2591, 0, 0, -1), (107, 5, 15, 2614, 0, 0, 1), (108, 18, 17, 2676, 0, 0, -1), (109, 10, 5, 2720, 0, 0, -1), (110, 11, 7, 2761, 0, 0, -1), (111, 2, 9, 2845, 0, 0, 1), (112, 17, 10, 2863, 0, 0, -1), (113, 6, 1, 2882, 0, 0, -1), (114, 12, 11, 2897, 0, 0, -1), (115, 8, 18, 2905, 0, 0, 1), (116, 9, 11, 2922, 0, 0, 1), (117, 0, 1, 2994, 0, 0, 1), (118, 11, 2, 3003, 0, 0, -1), (119, 9, 3, 3096, 0, 0, -1), (120, 5, 12, 3114, 0, 0, 1), (121, 2, 13, 3126, 0, 0, 1), (122, 1, 12, 3168, 0, 0, 1), (123, 19, 6, 3175, 0, 0, -1), (124, 0, 10, 3210, 0, 0, 1), (125, 14, 3, 3338, 0, 0, -1), (126, 14, 9, 3369, 0, 0, -1), (127, 17, 8, 3518, 0, 0, -1), (128, 2, 7, 3556, 0, 0, 1), (129, 12, 0, 3597, 0, 0, -1)]
    data = [(1, 0, 10, 0, 0, 0, 1), (2, 1, 18, 0, 0, 0, 1), (3, 2, 4, 0, 0, 0, 1), (4, 3, 13, 0, 0, 0, 1), (5, 4, 13, 0, 0, 0, 1), (6, 5, 1, 0, 0, 0, -1), (7, 6, 20, 0, 0, 0, 1), (8, 7, 19, 0, 0, 0, 1), (9, 8, 5, 0, 0, 0, -1), (10, 9, 7, 0, 0, 0, -1), (11, 10, 8, 0, 0, 0, -1), (12, 11, 1, 0, 0, 0, -1), (13, 12, 3, 0, 0, 0, -1), (14, 13, 0, 0, 0, 0, -1), (15, 14, 5, 0, 0, 0, -1), (16, 15, 16, 0, 0, 0, 1), (17, 16, 17, 0, 0, 0, 1), (18, 17, 1, 0, 0, 0, -1), (19, 18, 16, 0, 0, 0, -1), (20, 19, 3, 0, 0, 0, -1), (21, 20, 17, 0, 0, 0, -1), (22, 3, 1, 2, 0, 0, -1), (23, 8, 5, 22, 0, 0, -1), (24, 4, 2, 24, 0, 0, -1), (25, 5, 16, 37, 0, 0, 1), (26, 0, 13, 88, 0, 0, 1), (27, 9, 17, 93, 0, 0, 1), (28, 6, 20, 103, 0, 0, 1), (29, 8, 10, 106, 0, 0, 1), (30, 0, 5, 118, 0, 0, 1), (31, 16, 0, 119, 0, 0, -1), (32, 11, 0, 125, 0, 0, -1), (33, 12, 20, 126, 0, 0, 1), (34, 8, 16, 131, 0, 0, 1), (35, 4, 18, 134, 0, 0, 1), (36, 20, 7, 156, 0, 0, -1), (37, 18, 12, 159, 0, 0, -1), (38, 12, 9, 170, 0, 0, -1), (39, 5, 20, 187, 0, 0, 1), (40, 19, 7, 191, 0, 0, -1), (41, 6, 3, 192, 0, 0, -1), (42, 3, 17, 193, 0, 0, 1), (43, 8, 7, 199, 0, 0, -1), (44, 3, 6, 200, 0, 0, 1), (45, 16, 0, 214, 0, 0, -1), (46, 2, 18, 240, 0, 0, 1), (47, 4, 17, 241, 0, 0, 1), (48, 18, 14, 245, 0, 0, -1), (49, 8, 19, 274, 0, 0, 1), (50, 19, 9, 280, 0, 0, -1), (51, 3, 5, 302, 0, 0, 1), (52, 10, 12, 310, 0, 0, 1), (53, 16, 3, 317, 0, 0, -1), (54, 2, 5, 322, 0, 0, 1), (55, 13, 15, 325, 0, 0, 1), (56, 10, 17, 332, 0, 0, 1), (57, 5, 4, 332, 0, 0, -1), (58, 17, 7, 336, 0, 0, -1), (59, 1, 5, 342, 0, 0, 1), (60, 10, 0, 357, 0, 0, -1), (61, 18, 15, 384, 0, 0, -1), (62, 10, 3, 413, 0, 0, -1), (63, 4, 13, 416, 0, 0, 1), (64, 1, 10, 438, 0, 0, 1), (65, 18, 12, 444, 0, 0, -1), (66, 1, 4, 452, 0, 0, 1), (67, 19, 8, 460, 0, 0, -1), (68, 19, 7, 464, 0, 0, -1), (69, 16, 18, 466, 0, 0, 1), (70, 8, 5, 471, 0, 0, -1), (71, 9, 11, 474, 0, 0, 1), (72, 13, 10, 484, 0, 0, -1), (73, 13, 7, 512, 0, 0, -1), (74, 2, 20, 516, 0, 0, 1), (75, 10, 12, 545, 0, 0, 1), (76, 19, 13, 556, 0, 0, -1), (77, 7, 13, 561, 0, 0, 1), (78, 14, 10, 566, 0, 0, -1), (79, 17, 5, 567, 0, 0, -1), (80, 7, 15, 575, 0, 0, 1), (81, 5, 3, 581, 0, 0, -1), (82, 12, 2, 586, 0, 0, -1), (83, 14, 18, 597, 0, 0, 1), (84, 6, 3, 603, 0, 0, -1), (85, 20, 12, 617, 0, 0, -1), (86, 14, 0, 642, 0, 0, -1), (87, 19, 14, 645, 0, 0, -1), (88, 3, 0, 662, 0, 0, -1), (89, 0, 8, 664, 0, 0, 1), (90, 15, 3, 670, 0, 0, -1), (91, 9, 13, 680, 0, 0, 1), (92, 9, 20, 704, 0, 0, 1), (93, 17, 0, 715, 0, 0, -1), (94, 7, 12, 717, 0, 0, 1), (95, 1, 19, 720, 0, 0, 1), (96, 14, 8, 745, 0, 0, -1), (97, 4, 2, 754, 0, 0, -1), (98, 20, 3, 755, 0, 0, -1), (99, 3, 7, 761, 0, 0, 1), (100, 0, 17, 781, 0, 0, 1), (101, 14, 15, 781, 0, 0, 1), (102, 18, 2, 781, 0, 0, -1), (103, 8, 10, 785, 0, 0, 1), (104, 9, 4, 801, 0, 0, -1), (105, 0, 10, 813, 0, 0, 1), (106, 5, 20, 815, 0, 0, 1), (107, 1, 13, 818, 0, 0, 1), (108, 17, 8, 822, 0, 0, -1), (109, 5, 8, 827, 0, 0, 1), (110, 16, 12, 830, 0, 0, -1), (111, 8, 10, 837, 0, 0, 1), (112, 7, 6, 839, 0, 0, -1), (113, 18, 5, 854, 0, 0, -1), (114, 1, 20, 866, 0, 0, 1), (115, 2, 15, 867, 0, 0, 1), (116, 15, 14, 870, 0, 0, -1), (117, 14, 11, 872, 0, 0, -1), (118, 5, 4, 904, 0, 0, -1), (119, 9, 17, 904, 0, 0, 1), (120, 17, 13, 905, 0, 0, -1), (121, 0, 7, 911, 0, 0, 1), (122, 10, 0, 924, 0, 0, -1), (123, 4, 7, 927, 0, 0, 1), (124, 6, 5, 934, 0, 0, -1), (125, 5, 12, 938, 0, 0, 1), (126, 16, 11, 960, 0, 0, -1), (127, 4, 17, 966, 0, 0, 1), (128, 4, 3, 968, 0, 0, -1), (129, 16, 9, 983, 0, 0, -1), (130, 0, 7, 988, 0, 0, 1), (131, 4, 19, 996, 0, 0, 1), (132, 8, 12, 1026, 0, 0, 1), (133, 4, 13, 1037, 0, 0, 1), (134, 11, 1, 1037, 0, 0, -1), (135, 11, 6, 1043, 0, 0, -1), (136, 8, 2, 1062, 0, 0, -1), (137, 4, 19, 1069, 0, 0, 1), (138, 7, 10, 1085, 0, 0, 1), (139, 20, 10, 1127, 0, 0, -1), (140, 12, 13, 1134, 0, 0, 1), (141, 2, 14, 1137, 0, 0, 1), (142, 14, 4, 1145, 0, 0, -1), (143, 12, 16, 1152, 0, 0, 1), (144, 18, 11, 1160, 0, 0, -1), (145, 3, 0, 1165, 0, 0, -1), (146, 9, 6, 1165, 0, 0, -1), (147, 3, 14, 1169, 0, 0, 1), (148, 3, 0, 1176, 0, 0, -1), (149, 8, 12, 1178, 0, 0, 1), (150, 19, 2, 1183, 0, 0, -1), (151, 5, 1, 1185, 0, 0, -1), (152, 9, 0, 1189, 0, 0, -1), (153, 16, 1, 1189, 0, 0, -1), (154, 10, 14, 1196, 0, 0, 1), (155, 18, 13, 1196, 0, 0, -1), (156, 14, 8, 1227, 0, 0, -1), (157, 4, 6, 1233, 0, 0, 1), (158, 4, 1, 1261, 0, 0, -1), (159, 14, 11, 1274, 0, 0, -1), (160, 15, 1, 1281, 0, 0, -1), (161, 2, 16, 1283, 0, 0, 1), (162, 18, 12, 1286, 0, 0, -1), (163, 5, 20, 1287, 0, 0, 1), (164, 2, 17, 1297, 0, 0, 1), (165, 14, 2, 1315, 0, 0, -1), (166, 5, 0, 1330, 0, 0, -1), (167, 9, 1, 1345, 0, 0, -1), (168, 5, 4, 1347, 0, 0, -1), (169, 16, 18, 1347, 0, 0, 1), (170, 15, 5, 1358, 0, 0, -1), (171, 2, 20, 1361, 0, 0, 1), (172, 16, 19, 1375, 0, 0, 1), (173, 7, 9, 1385, 0, 0, 1), (174, 8, 15, 1402, 0, 0, 1), (175, 20, 3, 1411, 0, 0, -1), (176, 14, 6, 1420, 0, 0, -1), (178, 16, 10, 1463, 0, 0, -1), (177, 10, 16, 1463, 0, 0, 1), (179, 13, 15, 1469, 0, 0, 1), (180, 4, 20, 1470, 0, 0, 1), (181, 0, 4, 1470, 0, 0, 1), (182, 0, 3, 1471, 0, 0, 1), (183, 7, 20, 1483, 0, 0, 1), (184, 1, 6, 1484, 0, 0, 1), (185, 4, 16, 1496, 0, 0, 1), (186, 1, 20, 1501, 0, 0, 1), (187, 12, 0, 1505, 0, 0, -1), (188, 17, 16, 1518, 0, 0, -1), (189, 8, 20, 1536, 0, 0, 1), (190, 3, 6, 1558, 0, 0, 1), (191, 1, 7, 1569, 0, 0, 1), (192, 3, 17, 1583, 0, 0, 1), (193, 20, 19, 1595, 0, 0, -1), (194, 1, 13, 1611, 0, 0, 1), (195, 11, 6, 1614, 0, 0, -1), (196, 18, 17, 1614, 0, 0, -1), (197, 0, 13, 1619, 0, 0, 1), (198, 10, 16, 1620, 0, 0, 1), (199, 0, 9, 1621, 0, 0, 1), (200, 18, 16, 1627, 0, 0, -1), (201, 17, 2, 1645, 0, 0, -1), (202, 20, 1, 1645, 0, 0, -1), (203, 14, 16, 1669, 0, 0, 1), (204, 18, 10, 1691, 0, 0, -1), (205, 15, 0, 1701, 0, 0, -1), (206, 11, 9, 1709, 0, 0, -1), (207, 1, 15, 1717, 0, 0, 1), (208, 6, 17, 1718, 0, 0, 1), (209, 4, 17, 1727, 0, 0, 1), (210, 7, 9, 1731, 0, 0, 1), (211, 9, 16, 1741, 0, 0, 1), (212, 9, 1, 1747, 0, 0, -1), (213, 6, 15, 1755, 0, 0, 1), (214, 5, 12, 1758, 0, 0, 1), (215, 12, 20, 1762, 0, 0, 1), (216, 12, 19, 1768, 0, 0, 1), (217, 16, 1, 1770, 0, 0, -1), (218, 8, 10, 1777, 0, 0, 1), (219, 1, 10, 1790, 0, 0, 1), (220, 20, 1, 1803, 0, 0, -1), (221, 2, 7, 1811, 0, 0, 1), (222, 7, 16, 1836, 0, 0, 1), (223, 11, 17, 1838, 0, 0, 1), (224, 3, 8, 1844, 0, 0, 1), (225, 17, 5, 1853, 0, 0, -1), (226, 5, 6, 1858, 0, 0, 1), (227, 7, 5, 1885, 0, 0, -1), (228, 10, 16, 1891, 0, 0, 1), (229, 16, 10, 1903, 0, 0, -1), (230, 15, 19, 1910, 0, 0, 1), (231, 9, 20, 1931, 0, 0, 1), (232, 16, 8, 1931, 0, 0, -1), (233, 12, 13, 1932, 0, 0, 1), (234, 14, 0, 1932, 0, 0, -1), (235, 10, 5, 1933, 0, 0, -1), (236, 13, 14, 1934, 0, 0, 1), (237, 0, 4, 1939, 0, 0, 1), (238, 18, 19, 1954, 0, 0, 1), (239, 15, 4, 1958, 0, 0, -1), (240, 9, 16, 1978, 0, 0, 1), (241, 1, 8, 1988, 0, 0, 1), (242, 19, 1, 2000, 0, 0, -1), (243, 8, 11, 2001, 0, 0, 1), (244, 4, 14, 2048, 0, 0, 1), (245, 1, 0, 2054, 0, 0, -1), (246, 7, 12, 2058, 0, 0, 1), (247, 4, 2, 2058, 0, 0, -1), (248, 8, 6, 2069, 0, 0, -1), (249, 6, 9, 2073, 0, 0, 1), (250, 20, 17, 2086, 0, 0, -1), (251, 0, 5, 2088, 0, 0, 1), (252, 0, 2, 2106, 0, 0, 1), (253, 9, 17, 2106, 0, 0, 1), (254, 9, 4, 2109, 0, 0, -1), (255, 6, 5, 2111, 0, 0, -1), (256, 0, 10, 2117, 0, 0, 1), (257, 3, 17, 2135, 0, 0, 1), (258, 7, 19, 2141, 0, 0, 1), (259, 14, 16, 2145, 0, 0, 1), (260, 8, 12, 2147, 0, 0, 1), (261, 17, 0, 2156, 0, 0, -1), (262, 8, 20, 2164, 0, 0, 1), (263, 1, 9, 2187, 0, 0, 1), (264, 3, 13, 2191, 0, 0, 1), (265, 6, 8, 2199, 0, 0, 1), (266, 12, 8, 2210, 0, 0, -1), (267, 15, 17, 2210, 0, 0, 1), (268, 10, 18, 2212, 0, 0, 1), (269, 12, 0, 2217, 0, 0, -1), (270, 3, 6, 2217, 0, 0, 1), (271, 16, 11, 2234, 0, 0, -1), (272, 12, 13, 2238, 0, 0, 1), (273, 2, 1, 2243, 0, 0, -1), (274, 9, 20, 2246, 0, 0, 1), (275, 6, 19, 2246, 0, 0, 1), (276, 9, 5, 2254, 0, 0, -1), (277, 8, 5, 2258, 0, 0, -1), (278, 17, 14, 2271, 0, 0, -1), (279, 16, 4, 2296, 0, 0, -1), (280, 14, 16, 2299, 0, 0, 1), (281, 6, 9, 2303, 0, 0, 1), (282, 9, 5, 2346, 0, 0, -1), (283, 14, 4, 2359, 0, 0, -1), (284, 12, 14, 2378, 0, 0, 1), (285, 18, 15, 2382, 0, 0, -1), (286, 19, 5, 2400, 0, 0, -1), (287, 20, 4, 2403, 0, 0, -1), (288, 19, 17, 2413, 0, 0, -1), (289, 10, 13, 2414, 0, 0, 1), (290, 5, 1, 2428, 0, 0, -1), (291, 17, 0, 2440, 0, 0, -1), (292, 19, 13, 2466, 0, 0, -1), (293, 15, 0, 2472, 0, 0, -1), (294, 12, 11, 2489, 0, 0, -1), (295, 2, 18, 2490, 0, 0, 1), (296, 9, 15, 2528, 0, 0, 1), (297, 7, 9, 2537, 0, 0, 1), (298, 1, 4, 2567, 0, 0, 1), (299, 2, 4, 2584, 0, 0, 1), (300, 17, 15, 2596, 0, 0, -1), (301, 3, 15, 2606, 0, 0, 1), (302, 3, 9, 2610, 0, 0, 1), (303, 19, 15, 2612, 0, 0, -1), (304, 20, 15, 2623, 0, 0, -1), (305, 3, 12, 2624, 0, 0, 1), (306, 6, 16, 2635, 0, 0, 1), (307, 16, 2, 2639, 0, 0, -1), (308, 12, 4, 2658, 0, 0, -1), (309, 14, 2, 2667, 0, 0, -1), (310, 9, 2, 2672, 0, 0, -1), (311, 7, 16, 2676, 0, 0, 1), (312, 5, 14, 2683, 0, 0, 1), (313, 18, 17, 2710, 0, 0, -1), (314, 10, 6, 2719, 0, 0, -1), (315, 3, 20, 2740, 0, 0, 1), (316, 10, 6, 2740, 0, 0, -1), (317, 0, 10, 2748, 0, 0, 1), (318, 9, 15, 2753, 0, 0, 1), (319, 5, 9, 2759, 0, 0, 1), (320, 16, 2, 2762, 0, 0, -1), (321, 1, 19, 2772, 0, 0, 1), (322, 0, 3, 2778, 0, 0, 1), (323, 4, 20, 2781, 0, 0, 1), (324, 3, 14, 2793, 0, 0, 1), (325, 1, 18, 2798, 0, 0, 1), (326, 8, 13, 2799, 0, 0, 1), (327, 13, 3, 2811, 0, 0, -1), (328, 0, 16, 2844, 0, 0, 1), (329, 9, 16, 2848, 0, 0, 1), (330, 12, 19, 2850, 0, 0, 1), (331, 19, 13, 2851, 0, 0, -1), (332, 0, 4, 2865, 0, 0, 1), (333, 17, 10, 2869, 0, 0, -1), (334, 9, 11, 2870, 0, 0, 1), (335, 20, 3, 2873, 0, 0, -1), (336, 7, 20, 2875, 0, 0, 1), (337, 6, 5, 2911, 0, 0, -1), (338, 0, 1, 2930, 0, 0, 1), (339, 6, 20, 2935, 0, 0, 1), (340, 7, 10, 2935, 0, 0, 1), (341, 9, 15, 2944, 0, 0, 1), (342, 12, 1, 2945, 0, 0, -1), (343, 14, 4, 2945, 0, 0, -1), (344, 16, 15, 2950, 0, 0, -1), (345, 1, 18, 2972, 0, 0, 1), (346, 19, 14, 2975, 0, 0, -1), (347, 6, 3, 2977, 0, 0, -1), (348, 5, 6, 2977, 0, 0, 1), (349, 20, 0, 2981, 0, 0, -1), (350, 12, 11, 2991, 0, 0, -1), (351, 10, 5, 3004, 0, 0, -1), (352, 11, 14, 3005, 0, 0, 1), (353, 1, 3, 3009, 0, 0, 1), (354, 5, 16, 3024, 0, 0, 1), (355, 2, 14, 3033, 0, 0, 1), (356, 0, 3, 3050, 0, 0, 1), (357, 9, 13, 3054, 0, 0, 1), (358, 9, 11, 3070, 0, 0, 1), (359, 2, 12, 3080, 0, 0, 1), (360, 0, 18, 3082, 0, 0, 1), (361, 7, 16, 3093, 0, 0, 1), (362, 10, 16, 3098, 0, 0, 1), (363, 0, 1, 3126, 0, 0, 1), (364, 0, 4, 3131, 0, 0, 1), (365, 1, 2, 3137, 0, 0, 1), (366, 0, 2, 3139, 0, 0, 1), (367, 7, 2, 3142, 0, 0, -1), (368, 20, 11, 3148, 0, 0, -1), (369, 1, 11, 3152, 0, 0, 1), (370, 5, 0, 3170, 0, 0, -1), (371, 12, 4, 3178, 0, 0, -1), (372, 20, 14, 3181, 0, 0, -1), (373, 12, 7, 3199, 0, 0, -1), (374, 16, 1, 3201, 0, 0, -1), (375, 4, 0, 3204, 0, 0, -1), (376, 14, 7, 3204, 0, 0, -1), (377, 14, 5, 3222, 0, 0, -1), (378, 4, 13, 3226, 0, 0, 1), (379, 19, 8, 3226, 0, 0, -1), (380, 17, 14, 3227, 0, 0, -1), (381, 9, 16, 3228, 0, 0, 1), (382, 5, 20, 3228, 0, 0, 1), (383, 18, 16, 3248, 0, 0, -1), (384, 15, 0, 3252, 0, 0, -1), (385, 1, 19, 3254, 0, 0, 1), (386, 17, 9, 3257, 0, 0, -1), (387, 6, 10, 3279, 0, 0, 1), (388, 6, 19, 3281, 0, 0, 1), (389, 5, 4, 3293, 0, 0, -1), (390, 14, 3, 3333, 0, 0, -1), (391, 5, 9, 3346, 0, 0, 1), (392, 4, 15, 3350, 0, 0, 1), (393, 7, 3, 3369, 0, 0, -1), (394, 0, 13, 3370, 0, 0, 1), (395, 17, 10, 3371, 0, 0, -1), (396, 14, 4, 3377, 0, 0, -1), (397, 1, 5, 3384, 0, 0, 1), (398, 16, 3, 3423, 0, 0, -1), (399, 10, 15, 3429, 0, 0, 1), (400, 13, 11, 3442, 0, 0, -1), (401, 0, 11, 3452, 0, 0, 1), (402, 20, 2, 3459, 0, 0, -1), (403, 8, 16, 3462, 0, 0, 1), (404, 8, 15, 3462, 0, 0, 1), (405, 1, 3, 3497, 0, 0, 1), (406, 15, 12, 3498, 0, 0, -1), (407, 12, 14, 3500, 0, 0, 1), (408, 0, 3, 3509, 0, 0, 1), (409, 6, 1, 3512, 0, 0, -1), (410, 0, 11, 3514, 0, 0, 1), (411, 11, 8, 3516, 0, 0, -1), (412, 3, 16, 3556, 0, 0, 1), (413, 6, 17, 3557, 0, 0, 1), (414, 0, 3, 3560, 0, 0, 1), (415, 16, 7, 3583, 0, 0, -1), (416, 19, 20, 3597, 0, 0, 1), (417, 4, 13, 3608, 0, 0, 1), (418, 13, 7, 3617, 0, 0, -1), (419, 5, 19, 3627, 0, 0, 1), (420, 11, 12, 3640, 0, 0, 1), (421, 6, 18, 3644, 0, 0, 1), (422, 10, 6, 3659, 0, 0, -1), (423, 14, 1, 3669, 0, 0, -1), (424, 11, 7, 3683, 0, 0, -1), (425, 11, 4, 3684, 0, 0, -1), (426, 20, 7, 3687, 0, 0, -1), (427, 17, 2, 3694, 0, 0, -1), (428, 12, 3, 3697, 0, 0, -1), (429, 10, 8, 3704, 0, 0, -1), (430, 18, 12, 3727, 0, 0, -1), (431, 1, 10, 3730, 0, 0, 1), (432, 1, 2, 3732, 0, 0, 1), (433, 3, 18, 3733, 0, 0, 1), (434, 9, 14, 3756, 0, 0, 1), (435, 0, 14, 3763, 0, 0, 1), (436, 20, 7, 3764, 0, 0, -1), (437, 4, 18, 3764, 0, 0, 1), (438, 17, 15, 3778, 0, 0, -1), (439, 12, 16, 3781, 0, 0, 1), (440, 6, 5, 3783, 0, 0, -1), (441, 11, 1, 3788, 0, 0, -1), (442, 4, 13, 3791, 0, 0, 1), (443, 11, 14, 3791, 0, 0, 1), (444, 18, 8, 3809, 0, 0, -1), (445, 17, 16, 3822, 0, 0, -1), (446, 1, 9, 3823, 0, 0, 1), (447, 2, 5, 3845, 0, 0, 1), (448, 12, 18, 3858, 0, 0, 1), (449, 19, 6, 3862, 0, 0, -1), (450, 11, 1, 3862, 0, 0, -1), (451, 11, 16, 3881, 0, 0, 1), (452, 3, 15, 3906, 0, 0, 1), (453, 9, 18, 3937, 0, 0, 1), (454, 7, 6, 3945, 0, 0, -1), (455, 3, 14, 3969, 0, 0, 1), (456, 2, 15, 3983, 0, 0, 1), (457, 0, 11, 3988, 0, 0, 1), (458, 16, 6, 4007, 0, 0, -1), (459, 5, 18, 4016, 0, 0, 1), (460, 3, 0, 4023, 0, 0, -1), (461, 16, 13, 4031, 0, 0, -1), (462, 6, 15, 4056, 0, 0, 1), (463, 5, 20, 4063, 0, 0, 1), (464, 0, 15, 4078, 0, 0, 1), (465, 20, 1, 4081, 0, 0, -1), (466, 11, 3, 4102, 0, 0, -1), (467, 5, 3, 4105, 0, 0, -1), (468, 14, 4, 4125, 0, 0, -1), (469, 12, 5, 4129, 0, 0, -1), (470, 3, 17, 4134, 0, 0, 1), (471, 7, 0, 4146, 0, 0, -1), (472, 13, 15, 4148, 0, 0, 1), (473, 19, 2, 4165, 0, 0, -1), (474, 5, 4, 4176, 0, 0, -1), (475, 17, 0, 4204, 0, 0, -1), (476, 11, 5, 4207, 0, 0, -1), (477, 14, 7, 4222, 0, 0, -1), (478, 19, 16, 4223, 0, 0, -1), (479, 14, 5, 4224, 0, 0, -1), (480, 7, 3, 4242, 0, 0, -1), (481, 13, 12, 4246, 0, 0, -1), (482, 15, 13, 4287, 0, 0, -1), (483, 1, 11, 4339, 0, 0, 1), (484, 5, 20, 4344, 0, 0, 1), (485, 0, 8, 4356, 0, 0, 1), (486, 14, 3, 4357, 0, 0, -1), (487, 9, 7, 4359, 0, 0, -1), (488, 10, 8, 4362, 0, 0, -1), (489, 18, 4, 4365, 0, 0, -1), (490, 14, 13, 4367, 0, 0, -1), (491, 6, 11, 4368, 0, 0, 1), (492, 8, 3, 4376, 0, 0, -1), (493, 16, 18, 4384, 0, 0, 1), (494, 12, 14, 4401, 0, 0, 1), (495, 2, 1, 4404, 0, 0, -1), (496, 2, 6, 4420, 0, 0, 1), (497, 3, 5, 4451, 0, 0, 1), (498, 0, 13, 4452, 0, 0, 1), (499, 9, 2, 4465, 0, 0, -1), (500, 0, 16, 4466, 0, 0, 1), (501, 19, 15, 4472, 0, 0, -1), (502, 12, 19, 4472, 0, 0, 1), (503, 14, 15, 4505, 0, 0, 1), (504, 6, 2, 4507, 0, 0, -1), (505, 11, 18, 4509, 0, 0, 1), (506, 0, 10, 4520, 0, 0, 1), (507, 16, 4, 4521, 0, 0, -1), (508, 14, 16, 4521, 0, 0, 1), (509, 20, 12, 4542, 0, 0, -1), (510, 19, 8, 4547, 0, 0, -1), (511, 10, 14, 4552, 0, 0, 1), (512, 5, 14, 4573, 0, 0, 1), (513, 1, 18, 4575, 0, 0, 1), (514, 9, 12, 4575, 0, 0, 1), (515, 20, 4, 4583, 0, 0, -1), (516, 11, 2, 4588, 0, 0, -1), (517, 0, 6, 4627, 0, 0, 1), (518, 3, 8, 4630, 0, 0, 1), (519, 18, 2, 4637, 0, 0, -1), (520, 16, 19, 4642, 0, 0, 1), (521, 20, 2, 4653, 0, 0, -1), (522, 12, 3, 4669, 0, 0, -1), (523, 13, 20, 4674, 0, 0, 1), (524, 0, 7, 4684, 0, 0, 1), (525, 16, 10, 4701, 0, 0, -1), (526, 13, 2, 4706, 0, 0, -1), (527, 1, 9, 4711, 0, 0, 1), (528, 12, 15, 4713, 0, 0, 1), (529, 19, 4, 4729, 0, 0, -1), (530, 3, 16, 4783, 0, 0, 1), (531, 11, 19, 4783, 0, 0, 1), (532, 16, 8, 4795, 0, 0, -1), (533, 11, 6, 4798, 0, 0, -1), (534, 15, 18, 4811, 0, 0, 1), (535, 11, 1, 4819, 0, 0, -1), (536, 8, 16, 4821, 0, 0, 1), (537, 7, 10, 4826, 0, 0, 1), (538, 15, 10, 4848, 0, 0, -1), (539, 0, 11, 4848, 0, 0, 1), (540, 8, 5, 4864, 0, 0, -1), (541, 0, 17, 4874, 0, 0, 1), (542, 0, 18, 4882, 0, 0, 1), (543, 10, 14, 4886, 0, 0, 1), (544, 12, 4, 4891, 0, 0, -1), (545, 19, 11, 4907, 0, 0, -1), (546, 3, 19, 4911, 0, 0, 1), (547, 11, 14, 4917, 0, 0, 1), (548, 1, 6, 4917, 0, 0, 1), (549, 7, 10, 4921, 0, 0, 1), (550, 14, 6, 4927, 0, 0, -1), (551, 17, 6, 4932, 0, 0, -1), (552, 1, 20, 4933, 0, 0, 1), (553, 15, 3, 4944, 0, 0, -1), (554, 16, 1, 4949, 0, 0, -1), (555, 2, 9, 4969, 0, 0, 1), (556, 20, 15, 4985, 0, 0, -1), (557, 7, 8, 4987, 0, 0, 1), (558, 0, 11, 4991, 0, 0, 1), (559, 1, 7, 5005, 0, 0, 1), (560, 7, 13, 5010, 0, 0, 1), (561, 15, 12, 5021, 0, 0, -1), (562, 1, 15, 5036, 0, 0, 1), (563, 12, 9, 5040, 0, 0, -1), (564, 10, 16, 5042, 0, 0, 1), (565, 16, 18, 5051, 0, 0, 1), (566, 9, 11, 5056, 0, 0, 1), (567, 19, 20, 5061, 0, 0, 1), (568, 7, 10, 5063, 0, 0, 1), (569, 0, 20, 5093, 0, 0, 1), (570, 18, 19, 5117, 0, 0, 1), (571, 7, 10, 5123, 0, 0, 1), (572, 1, 4, 5132, 0, 0, 1), (573, 10, 6, 5146, 0, 0, -1), (574, 10, 9, 5160, 0, 0, -1), (575, 8, 1, 5172, 0, 0, -1), (576, 16, 5, 5189, 0, 0, -1), (577, 2, 17, 5195, 0, 0, 1), (578, 18, 3, 5202, 0, 0, -1), (579, 3, 16, 5205, 0, 0, 1), (580, 14, 17, 5210, 0, 0, 1), (581, 9, 8, 5214, 0, 0, -1), (582, 18, 1, 5216, 0, 0, -1), (583, 8, 18, 5228, 0, 0, 1), (584, 7, 5, 5245, 0, 0, -1), (585, 19, 10, 5249, 0, 0, -1), (586, 14, 5, 5259, 0, 0, -1), (587, 8, 1, 5262, 0, 0, -1), (588, 14, 20, 5277, 0, 0, 1), (589, 17, 15, 5292, 0, 0, -1), (590, 20, 11, 5320, 0, 0, -1), (591, 4, 7, 5326, 0, 0, 1), (592, 5, 15, 5329, 0, 0, 1), (593, 14, 2, 5331, 0, 0, -1), (594, 17, 11, 5341, 0, 0, -1), (595, 0, 3, 5345, 0, 0, 1), (596, 10, 5, 5356, 0, 0, -1), (597, 8, 3, 5358, 0, 0, -1), (598, 14, 18, 5372, 0, 0, 1), (600, 17, 18, 5387, 0, 0, 1), (599, 7, 2, 5387, 0, 0, -1), (601, 4, 0, 5389, 0, 0, -1), (602, 17, 6, 5391, 0, 0, -1), (603, 18, 8, 5400, 0, 0, -1), (604, 17, 18, 5405, 0, 0, 1), (605, 18, 11, 5406, 0, 0, -1), (606, 1, 13, 5410, 0, 0, 1), (607, 12, 7, 5423, 0, 0, -1), (608, 17, 15, 5452, 0, 0, -1), (609, 4, 2, 5459, 0, 0, -1), (610, 9, 0, 5463, 0, 0, -1), (611, 0, 11, 5481, 0, 0, 1), (612, 10, 20, 5486, 0, 0, 1), (613, 10, 16, 5496, 0, 0, 1), (614, 1, 20, 5505, 0, 0, 1), (615, 1, 3, 5508, 0, 0, 1), (616, 0, 15, 5533, 0, 0, 1), (617, 0, 14, 5539, 0, 0, 1), (618, 4, 3, 5544, 0, 0, -1), (619, 13, 7, 5545, 0, 0, -1), (620, 6, 12, 5562, 0, 0, 1), (621, 8, 13, 5575, 0, 0, 1), (622, 18, 11, 5587, 0, 0, -1), (623, 13, 9, 5593, 0, 0, -1), (624, 14, 18, 5618, 0, 0, 1), (625, 4, 11, 5634, 0, 0, 1), (626, 9, 7, 5638, 0, 0, -1), (627, 18, 7, 5638, 0, 0, -1), (628, 4, 5, 5655, 0, 0, 1), (629, 7, 6, 5662, 0, 0, -1), (630, 4, 8, 5673, 0, 0, 1), (631, 8, 17, 5683, 0, 0, 1), (632, 7, 10, 5684, 0, 0, 1), (633, 10, 4, 5693, 0, 0, -1), (634, 2, 3, 5693, 0, 0, 1), (635, 6, 3, 5693, 0, 0, -1), (636, 4, 0, 5706, 0, 0, -1), (637, 6, 4, 5714, 0, 0, -1), (638, 20, 16, 5719, 0, 0, -1), (639, 14, 3, 5725, 0, 0, -1), (640, 11, 15, 5727, 0, 0, 1), (641, 10, 17, 5730, 0, 0, 1), (642, 4, 10, 5731, 0, 0, 1), (643, 3, 14, 5739, 0, 0, 1), (644, 14, 0, 5743, 0, 0, -1), (645, 5, 6, 5747, 0, 0, 1), (646, 14, 20, 5752, 0, 0, 1), (647, 19, 9, 5759, 0, 0, -1), (648, 9, 11, 5764, 0, 0, 1), (649, 16, 13, 5767, 0, 0, -1), (650, 11, 17, 5775, 0, 0, 1), (651, 13, 3, 5801, 0, 0, -1), (652, 15, 7, 5805, 0, 0, -1), (653, 16, 15, 5809, 0, 0, -1), (654, 20, 19, 5835, 0, 0, -1), (655, 10, 6, 5838, 0, 0, -1), (656, 4, 2, 5899, 0, 0, -1), (657, 2, 4, 5909, 0, 0, 1), (658, 6, 12, 5924, 0, 0, 1), (659, 17, 13, 5926, 0, 0, -1), (660, 12, 6, 5931, 0, 0, -1), (661, 9, 10, 5951, 0, 0, 1), (662, 5, 8, 5954, 0, 0, 1), (663, 2, 14, 5966, 0, 0, 1), (664, 20, 14, 5982, 0, 0, -1), (665, 6, 7, 6003, 0, 0, 1), (666, 4, 12, 6018, 0, 0, 1), (667, 0, 9, 6019, 0, 0, 1), (668, 17, 7, 6031, 0, 0, -1), (669, 18, 4, 6034, 0, 0, -1), (670, 12, 2, 6041, 0, 0, -1), (671, 8, 14, 6051, 0, 0, 1), (672, 11, 9, 6053, 0, 0, -1), (673, 16, 4, 6053, 0, 0, -1), (674, 0, 9, 6056, 0, 0, 1), (675, 7, 12, 6056, 0, 0, 1), (676, 0, 19, 6082, 0, 0, 1), (677, 0, 6, 6084, 0, 0, 1), (678, 14, 15, 6084, 0, 0, 1), (679, 14, 19, 6089, 0, 0, 1), (680, 12, 9, 6100, 0, 0, -1), (681, 15, 12, 6116, 0, 0, -1), (682, 3, 8, 6127, 0, 0, 1), (683, 4, 16, 6130, 0, 0, 1), (684, 2, 14, 6140, 0, 0, 1), (685, 10, 17, 6173, 0, 0, 1), (686, 15, 1, 6186, 0, 0, -1), (687, 20, 9, 6201, 0, 0, -1), (688, 6, 8, 6202, 0, 0, 1), (689, 6, 18, 6212, 0, 0, 1), (690, 5, 8, 6228, 0, 0, 1), (691, 7, 9, 6237, 0, 0, 1), (692, 4, 17, 6243, 0, 0, 1), (693, 9, 17, 6244, 0, 0, 1), (694, 7, 11, 6246, 0, 0, 1), (695, 12, 18, 6256, 0, 0, 1), (696, 6, 15, 6271, 0, 0, 1), (697, 5, 16, 6273, 0, 0, 1), (698, 4, 16, 6280, 0, 0, 1), (699, 1, 16, 6297, 0, 0, 1), (700, 8, 11, 6301, 0, 0, 1), (701, 8, 3, 6311, 0, 0, -1), (702, 17, 8, 6318, 0, 0, -1), (703, 0, 12, 6318, 0, 0, 1), (704, 13, 7, 6318, 0, 0, -1), (705, 0, 6, 6326, 0, 0, 1), (706, 1, 19, 6327, 0, 0, 1), (707, 5, 18, 6328, 0, 0, 1), (708, 12, 11, 6340, 0, 0, -1), (709, 2, 8, 6344, 0, 0, 1), (710, 0, 9, 6351, 0, 0, 1), (711, 5, 0, 6362, 0, 0, -1), (712, 13, 12, 6371, 0, 0, -1), (713, 10, 4, 6375, 0, 0, -1), (714, 3, 16, 6378, 0, 0, 1), (715, 3, 12, 6378, 0, 0, 1), (716, 13, 16, 6389, 0, 0, 1), (717, 12, 7, 6392, 0, 0, -1), (718, 18, 20, 6409, 0, 0, 1), (719, 8, 7, 6413, 0, 0, -1), (720, 3, 13, 6424, 0, 0, 1), (721, 20, 10, 6434, 0, 0, -1), (722, 0, 18, 6440, 0, 0, 1), (723, 4, 6, 6444, 0, 0, 1), (724, 14, 20, 6449, 0, 0, 1), (725, 1, 0, 6450, 0, 0, -1), (726, 5, 19, 6453, 0, 0, 1), (727, 16, 4, 6455, 0, 0, -1), (728, 5, 4, 6459, 0, 0, -1), (729, 5, 10, 6461, 0, 0, 1), (730, 1, 4, 6462, 0, 0, 1), (731, 16, 15, 6479, 0, 0, -1), (732, 14, 2, 6495, 0, 0, -1), (733, 0, 9, 6507, 0, 0, 1), (734, 4, 17, 6522, 0, 0, 1), (735, 11, 2, 6523, 0, 0, -1), (736, 8, 16, 6527, 0, 0, 1), (737, 1, 16, 6527, 0, 0, 1), (738, 0, 2, 6544, 0, 0, 1), (739, 10, 1, 6545, 0, 0, -1), (740, 1, 12, 6574, 0, 0, 1), (741, 8, 11, 6583, 0, 0, 1), (742, 4, 14, 6584, 0, 0, 1), (743, 13, 11, 6587, 0, 0, -1), (744, 13, 2, 6592, 0, 0, -1), (745, 1, 20, 6593, 0, 0, 1), (746, 20, 0, 6594, 0, 0, -1), (747, 13, 5, 6616, 0, 0, -1), (748, 17, 20, 6630, 0, 0, 1), (749, 9, 11, 6633, 0, 0, 1), (750, 10, 3, 6649, 0, 0, -1), (751, 8, 3, 6649, 0, 0, -1), (752, 0, 10, 6652, 0, 0, 1), (753, 15, 4, 6657, 0, 0, -1), (754, 8, 13, 6664, 0, 0, 1), (755, 7, 3, 6667, 0, 0, -1), (756, 0, 8, 6680, 0, 0, 1), (757, 17, 13, 6691, 0, 0, -1), (758, 20, 12, 6693, 0, 0, -1), (759, 19, 5, 6712, 0, 0, -1), (760, 7, 19, 6716, 0, 0, 1), (761, 2, 3, 6717, 0, 0, 1), (762, 17, 13, 6728, 0, 0, -1), (763, 11, 3, 6746, 0, 0, -1), (764, 10, 0, 6751, 0, 0, -1), (765, 4, 1, 6759, 0, 0, -1), (766, 1, 7, 6771, 0, 0, 1), (767, 20, 10, 6780, 0, 0, -1), (768, 8, 19, 6781, 0, 0, 1), (769, 2, 11, 6781, 0, 0, 1), (770, 13, 8, 6787, 0, 0, -1), (771, 12, 2, 6801, 0, 0, -1), (772, 4, 14, 6806, 0, 0, 1), (773, 12, 9, 6818, 0, 0, -1), (774, 8, 16, 6843, 0, 0, 1), (775, 0, 14, 6845, 0, 0, 1), (776, 5, 0, 6849, 0, 0, -1), (777, 20, 3, 6853, 0, 0, -1), (778, 7, 4, 6873, 0, 0, -1), (779, 2, 11, 6878, 0, 0, 1), (780, 10, 4, 6882, 0, 0, -1), (781, 7, 8, 6889, 0, 0, 1), (782, 0, 14, 6899, 0, 0, 1), (783, 15, 0, 6904, 0, 0, -1), (784, 7, 0, 6913, 0, 0, -1), (785, 1, 11, 6925, 0, 0, 1), (786, 4, 5, 6929, 0, 0, 1), (787, 1, 0, 6945, 0, 0, -1), (788, 2, 19, 6945, 0, 0, 1), (789, 12, 17, 6958, 0, 0, 1), (790, 7, 9, 6968, 0, 0, 1), (791, 12, 16, 6969, 0, 0, 1), (792, 14, 18, 6970, 0, 0, 1), (793, 19, 17, 6971, 0, 0, -1), (794, 0, 17, 6977, 0, 0, 1), (795, 4, 18, 6979, 0, 0, 1), (796, 9, 2, 6981, 0, 0, -1), (797, 6, 5, 6985, 0, 0, -1), (798, 19, 1, 6987, 0, 0, -1), (799, 17, 18, 6992, 0, 0, 1), (800, 4, 19, 7015, 0, 0, 1), (801, 2, 17, 7027, 0, 0, 1), (802, 13, 0, 7047, 0, 0, -1), (803, 0, 5, 7049, 0, 0, 1), (804, 13, 0, 7062, 0, 0, -1), (805, 17, 2, 7071, 0, 0, -1), (806, 11, 7, 7084, 0, 0, -1), (807, 18, 10, 7111, 0, 0, -1), (808, 3, 5, 7115, 0, 0, 1), (809, 7, 15, 7116, 0, 0, 1), (810, 0, 17, 7120, 0, 0, 1), (811, 8, 11, 7129, 0, 0, 1), (812, 12, 0, 7129, 0, 0, -1), (813, 7, 3, 7145, 0, 0, -1), (814, 3, 4, 7155, 0, 0, 1), (815, 0, 4, 7176, 0, 0, 1), (816, 13, 9, 7177, 0, 0, -1), (817, 19, 5, 7181, 0, 0, -1), (818, 14, 12, 7185, 0, 0, -1), (819, 12, 3, 7189, 0, 0, -1), (820, 10, 20, 7192, 0, 0, 1), (821, 3, 2, 7194, 0, 0, -1)]
    Dual_lift.run_simulation(data)
    time.append(Dual_lift.current_time)
print(np.mean(time))