import random
import numpy as np
import pandas as pd
class DualLiftSystem:

    '''This elevator is trying to simulate the real life situation of passengers arriving at varied times'''

    def __init__(self, current_floor_A,current_floor_B, num_floors,filepath, Passenger_limit, current_time = 0):
        # Initialize the elevator state and load the passenger data from a CSV file
        self.num_floors = num_floors
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
                
    def assign_passengers(self, pending_orders):
        liftA_orders = []
        liftB_orders = []
        prospective_people_in_liftA = 0
        prospective_people_in_liftB = 0
        
        for passenger in pending_orders:
            _, passenger_position, _, _, _, _, direction = passenger
            total_list = liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A          
            distance_from_A = abs(self.current_floor_A - passenger_position)
            distance_from_B = abs(self.current_floor_B - passenger_position)
            
                        
            if distance_from_A<distance_from_B:
                if not self.status_A and (direction==self.direction_A or self.direction_A==0) and prospective_people_in_liftA==0:
                    if passenger not in (total_list):# making sure that the passenger has never entered the lift
                        
            
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
                elif (self.direction_A>0 and direction>0 and passenger_position>=self.current_floor_A) or (self.direction_A<0 and direction<0 and passenger_position<=self.current_floor_A) and (passenger not in (total_list)):
                    liftA_orders.append(passenger)
                    print(f"\n{passenger} appended to lift A")
                    prospective_people_in_liftA=1
                    continue
                    
     
            
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
                        continue
                # else:
                if ((self.direction_B>0 and direction>0 and passenger_position>self.current_floor_B) or (self.direction_B<0 and direction<0 and passenger_position<=self.current_floor_B)) and (passenger not in (liftA_orders + liftB_orders + self.pending_orders_B + self.pending_orders_A)):
                    liftB_orders.append(passenger)
                    print(f"\n {passenger} appended to lift B")
                    prospective_people_in_liftB=1
                    continue

            
            elif distance_from_A == distance_from_B:
                lift_name = random.choice(["A","B"])
                if lift_name=="A":
                    if self.direction_A<=0 and direction<0 and passenger_position<=self.current_floor_A:
                        if passenger not in (total_list):
                            liftA_orders.append(passenger)
                            print(f"\n {passenger} appended to lift A")
                            prospective_people_in_liftA = 1
                            self.direction_A = direction
                            continue
                    if self.direction_A>=0 and direction>0 and passenger_position>=self.current_floor_A:
                        if passenger not in (total_list):
                            liftA_orders.append(passenger)
                            print(f"\n {passenger} appended to lift A")
                            prospective_people_in_liftA = 1
                            self.direction_A = direction
                            continue
                else:
                    if self.direction_B<=0 and direction<0 and passenger_position<=self.current_floor_B:
                        if passenger not in (total_list):
                            liftB_orders.append(passenger)
                            print(f"\n {passenger} appended to lift B")
                            prospective_people_in_liftB = 1
                            self.direction_B = direction
                            continue
                    if self.direction_B>=0 and direction>0 and passenger_position>=self.current_floor_B:
                        if passenger not in (total_list):
                            liftB_orders.append(passenger)
                            print(f"\n {passenger} appended to lift B")
                            prospective_people_in_liftB = 1
                            self.direction_B = direction
                            continue
            if self.status_B==False and prospective_people_in_liftB==0:
                if passenger not in (total_list):
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
                if passenger not in (total_list):
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
            
            pending_orders_A, pending_orders_B = self.assign_passengers(pending_orders)

            # Ensure that the same pending_orders_A is passed to data_sorter
            pending_orders_A = self.data_sorter(pending_orders_A, self.current_floor_A)
            
            pending_orders_A = sorted(pending_orders_A, key=lambda x: x[3])
            
            pending_orders_B = self.data_sorter(pending_orders_B, self.current_floor_B)
            
            pending_orders_B = sorted(pending_orders_B, key=lambda x: x[3])

            for person in pending_orders_A:
                if person in passenger_data:
                    passenger_data.remove(person)
                if person in pending_orders:
                    pending_orders.remove(person)
                if person not in self.pending_orders_A:
                    self.pending_orders_A.append(person)

            for person in pending_orders_B:
                if person in passenger_data:
                    passenger_data.remove(person)
                if person in pending_orders:
                    pending_orders.remove(person)
                if person not in self.pending_orders_B:
                    self.pending_orders_B.append(person)
            
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
            

        
            #If the lifts are empty then giving the pending orders a secong chance to be reassigned                
            if self.lift_A_population==0 and self.pending_orders_A and not passenger_data:
                for order in self.pending_orders_A:
                    self.pending_orders_A.remove(order)# This part is for lets say there is A was sirving someone and B is empty so the new passenger gets assigned to B but then A gets empty and becomes the best option then the passenger should be going to A not to B even if it was assigned first. But lets say both are empty then wont it keep switching? no because of the movement of the lift now the lift is the closest to the passenger thus becomes the best option
                    passenger_data.append(order)

            if self.lift_B_population==0 and self.pending_orders_B and not passenger_data:
                for order in self.pending_orders_B:
                    self.pending_orders_B.remove(order)
                    passenger_data.append(order)

time = []
for i in range(1):
    number_of_floors = 20
    passenger_limit = 8
    current_floor_A = 0
    current_floor_B = 0
    file_path = "Dummy"
    Dual_lift = DualLiftSystem(num_floors=number_of_floors, Passenger_limit=passenger_limit, current_floor_A=current_floor_A, current_floor_B=current_floor_B, filepath=file_path) 
    data = [(1, 0, 18, 0, 0, 0, 1), (2, 1, 15, 0, 0, 0, 1), (3, 2, 5, 0, 0, 0, 1), (4, 3, 11, 0, 0, 0, 1), (5, 4, 18, 0, 0, 0, 1), (6, 5, 12, 0, 0, 0, 1), (7, 6, 8, 0, 0, 0, 1), (8, 7, 12, 0, 0, 0, 1), (9, 8, 3, 0, 0, 0, -1), (10, 9, 13, 0, 0, 0, 1), (11, 10, 14, 0, 0, 0, 1), (12, 11, 13, 0, 0, 0, 1), (13, 12, 15, 0, 0, 0, 1), (14, 13, 3, 0, 0, 0, -1), (15, 14, 3, 0, 0, 0, -1), (16, 15, 4, 0, 0, 0, -1), (17, 16, 6, 0, 0, 0, -1), (18, 17, 4, 0, 0, 0, -1), (19, 18, 14, 0, 0, 0, -1), (20, 19, 8, 0, 0, 0, -1), (21, 20, 2, 0, 0, 0, -1), (22, 3, 20, 29, 0, 0, 1), (23, 5, 13, 35, 0, 0, 1), (24, 3, 7, 40, 0, 0, 1)]
    # data = [(1, 0, 2, 0, 0, 0, 1), (21, 20, 0, 0, 0, 0, -1), (20, 19, 0, 0, 0, 0, -1), (19, 18, 9, 0, 0, 0, -1), (18, 17, 5, 0, 0, 0, -1), (17, 16, 13, 0, 0, 0, -1), (15, 14, 1, 0, 0, 0, -1), (14, 13, 0, 0, 0, 0, -1), (13, 12, 18, 0, 0, 0, 1), (12, 11, 14, 0, 0, 0, 1), (16, 15, 16, 0, 0, 0, 1), (10, 9, 2, 0, 0, 0, -1), (11, 10, 16, 0, 0, 0, 1), (3, 2, 18, 0, 0, 0, 1), (4, 3, 7, 0, 0, 0, 1), (5, 4, 5, 0, 0, 0, 1), (2, 1, 4, 0, 0, 0, 1), (7, 6, 17, 0, 0, 0, 1), (8, 7, 11, 0, 0, 0, 1), (9, 8, 5, 0, 0, 0, -1), (6, 5, 4, 0, 0, 0, -1), (22, 20, 3, 51, 0, 0, -1), (23, 18, 3, 182, 0, 0, -1), (24, 18, 0, 185, 0, 0, -1), (25, 15, 17, 246, 0, 0, 1), (26, 0, 4, 259, 0, 0, 1), (27, 7, 8, 294, 0, 0, 1), (28, 19, 10, 373, 0, 0, -1), (29, 3, 10, 382, 0, 0, 1), (30, 18, 8, 387, 0, 0, -1), (31, 17, 12, 416, 0, 0, -1), (32, 12, 1, 485, 0, 0, -1), (33, 7, 19, 535, 0, 0, 1), (34, 3, 6, 608, 0, 0, 1), (35, 13, 19, 609, 0, 0, 1), (36, 19, 16, 627, 0, 0, -1), (37, 15, 8, 651, 0, 0, -1), (38, 17, 4, 665, 0, 0, -1), (39, 10, 12, 697, 0, 0, 1), (40, 5, 7, 711, 0, 0, 1), (41, 9, 15, 747, 0, 0, 1), (42, 9, 0, 761, 0, 0, -1), (43, 6, 14, 784, 0, 0, 1), (44, 17, 12, 789, 0, 0, -1), (45, 15, 20, 827, 0, 0, 1), (46, 14, 16, 846, 0, 0, 1), (47, 15, 4, 860, 0, 0, -1), (48, 9, 7, 888, 0, 0, -1), (49, 8, 15, 903, 0, 0, 1), (50, 9, 17, 912, 0, 0, 1), (51, 11, 15, 968, 0, 0, 1), (52, 12, 18, 979, 0, 0, 1), (53, 12, 7, 988, 0, 0, -1), (54, 18, 13, 997, 0, 0, -1), (55, 1, 5, 1024, 0, 0, 1), (56, 13, 20, 1093, 0, 0, 1), (57, 5, 18, 1134, 0, 0, 1), (58, 7, 3, 1151, 0, 0, -1), (59, 3, 14, 1212, 0, 0, 1), (60, 10, 7, 1269, 0, 0, -1), (61, 10, 15, 1311, 0, 0, 1), (62, 6, 4, 1312, 0, 0, -1), (63, 7, 4, 1313, 0, 0, -1), (64, 15, 14, 1365, 0, 0, -1), (65, 5, 9, 1379, 0, 0, 1), (66, 6, 18, 1412, 0, 0, 1), (67, 3, 12, 1424, 0, 0, 1), (68, 9, 14, 1443, 0, 0, 1), (69, 19, 9, 1450, 0, 0, -1), (70, 7, 2, 1460, 0, 0, -1), (71, 11, 2, 1520, 0, 0, -1), (72, 20, 2, 1523, 0, 0, -1), (73, 7, 15, 1607, 0, 0, 1), (74, 19, 4, 1613, 0, 0, -1), (75, 1, 5, 1652, 0, 0, 1), (76, 12, 10, 1655, 0, 0, -1), (77, 15, 2, 1687, 0, 0, -1), (78, 17, 14, 1699, 0, 0, -1), (79, 3, 0, 1718, 0, 0, -1), (80, 0, 19, 1858, 0, 0, 1), (81, 14, 7, 1868, 0, 0, -1), (82, 9, 6, 1918, 0, 0, -1), (83, 6, 7, 1927, 0, 0, 1), (84, 16, 14, 1963, 0, 0, -1), (85, 18, 14, 2003, 0, 0, -1), (86, 20, 17, 2022, 0, 0, -1), (87, 10, 2, 2052, 0, 0, -1), (88, 3, 18, 2075, 0, 0, 1), (89, 18, 13, 2082, 0, 0, -1), (90, 10, 20, 2087, 0, 0, 1), (91, 14, 9, 2090, 0, 0, -1), (92, 6, 20, 2115, 0, 0, 1), (93, 5, 8, 2184, 0, 0, 1), (94, 15, 13, 2185, 0, 0, -1), (95, 0, 3, 2192, 0, 0, 1), (96, 4, 2, 2231, 0, 0, -1), (97, 9, 16, 2244, 0, 0, 1), (98, 10, 20, 2283, 0, 0, 1), (99, 5, 8, 2375, 0, 0, 1), (100, 12, 0, 2443, 0, 0, -1), (101, 5, 15, 2461, 0, 0, 1), (102, 11, 10, 2486, 0, 0, -1), (103, 8, 7, 2493, 0, 0, -1), (104, 20, 0, 2509, 0, 0, -1), (105, 2, 10, 2518, 0, 0, 1), (106, 20, 14, 2591, 0, 0, -1), (107, 5, 15, 2614, 0, 0, 1), (108, 18, 17, 2676, 0, 0, -1), (109, 10, 5, 2720, 0, 0, -1), (110, 11, 7, 2761, 0, 0, -1), (111, 2, 9, 2845, 0, 0, 1), (112, 17, 10, 2863, 0, 0, -1), (113, 6, 1, 2882, 0, 0, -1), (114, 12, 11, 2897, 0, 0, -1), (115, 8, 18, 2905, 0, 0, 1), (116, 9, 11, 2922, 0, 0, 1), (117, 0, 1, 2994, 0, 0, 1), (118, 11, 2, 3003, 0, 0, -1), (119, 9, 3, 3096, 0, 0, -1), (120, 5, 12, 3114, 0, 0, 1), (121, 2, 13, 3126, 0, 0, 1), (122, 1, 12, 3168, 0, 0, 1), (123, 19, 6, 3175, 0, 0, -1), (124, 0, 10, 3210, 0, 0, 1), (125, 14, 3, 3338, 0, 0, -1), (126, 14, 9, 3369, 0, 0, -1), (127, 17, 8, 3518, 0, 0, -1), (128, 2, 7, 3556, 0, 0, 1), (129, 12, 0, 3597, 0, 0, -1)]
    Dual_lift.run_simulation(data)
    time.append(Dual_lift.current_time)
# print(np.max(time))
print(time)