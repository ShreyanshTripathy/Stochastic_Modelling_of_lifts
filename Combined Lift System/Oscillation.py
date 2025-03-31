import pandas as pd
'''Trialed and tested it is working perfectly'''
class DualOscillation:
    def __init__(self, current_floor_A, current_floor_B, num_floors, Passenger_limit, filepath,floor_time, current_time=0, directionA=0, directionB=0, lowest_floor=0, lift_speed=0.89408, building_height=20):

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
        
        self.lift_speed = lift_speed  # m/s
        self.building_height = building_height  # m
        
        # Calculate the height of each floor
        self.floor_height = self.building_height / self.num_floors
        
        # Calculate the time taken to move between floors
        self.floor_time = float(self.floor_height / self.lift_speed)
        # print(self.floor_time)
        self.floor_time = floor_time
        self.df = pd.read_csv(filepath)
        
    
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
    
    def serve_floor(self,passenger_data):
        copied_list = self.pending_orders.copy()
        already_picked = self.already_picked_A + self.already_picked_B
    
        for order in copied_list:
            Index, Passenger_position, Passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = order
            
            # Check for Lift A
            if (self.current_floor_lift_A == Passenger_destination and order in self.already_picked_A):
                print(f"Lift A is on floor {self.current_floor_lift_A} and dropped passenger {Index} at time {self.current_time}")
                self.pending_orders.remove(order)
                self.already_picked_A.remove(order)
                # time.sleep(1)
                self.df.loc[self.df["Index"] == Index, "Order completion time"] = self.current_time
                updated_tuple = self.df.loc[self.df["Index"] == Index].iloc[0]
                updated_tuple = tuple(updated_tuple)
                self.orders_done.append(updated_tuple)
                self.lift_A_Population-=1


            if (self.current_floor_lift_A == Passenger_position and order not in already_picked and self.direction_A == direction):
                if self.lift_A_Population<self.Passenger_limit:
                    print(f"Lift A is on floor {self.current_floor_lift_A} to pick passenger {Index} at time {self.current_time}")
                    # time.sleep(1)
                    self.df.loc[self.df["Index"] == Index, "Lift arrival time"] = self.current_time
                    # print(self.df)
                    # time.sleep(1)
                    self.already_picked_A.append(order)
                    self.lift_A_Population+=1
                else:
                    self.pending_orders.remove(order)
                    passenger_data.append(order)
                    
                
            # Check for Lift B
            if (self.current_floor_lift_B == Passenger_destination and order in self.already_picked_B):
                print(f"Lift B is on floor {self.current_floor_lift_B} and dropped passenger {Index} at time {self.current_time}")
                self.pending_orders.remove(order)
                self.already_picked_B.remove(order)
                self.lift_B_Population-=1
                # time.sleep(1)
                self.df.loc[self.df["Index"] == Index, "Order completion time"] = self.current_time
                updated_tuple = self.df.loc[self.df["Index"] == Index].iloc[0]
                updated_tuple = tuple(updated_tuple)
                self.orders_done.append(updated_tuple)
                self.df.to_csv(self.filepath, index=False)
                # time.sleep(1)

            if (self.current_floor_lift_B == Passenger_position and order not in already_picked and self.direction_B == direction):
                if self.lift_B_Population<self.Passenger_limit:
                    print(f"Lift B is on floor {self.current_floor_lift_B} to pick passenger {Index} at time {self.current_time}")
                    # time.sleep(1)
                    self.df.loc[self.df["Index"] == Index, "Lift arrival time"] = self.current_time
                    # print(self.df)
                    # time.sleep(1)
                    self.already_picked_B.append(order)
                    self.lift_B_Population+=1
                else:
                    self.pending_orders.remove(order)
                    passenger_data.append(order)
        return passenger_data
    def run_simulation(self, passenger_data):
        passenger_data = sorted(passenger_data, key=lambda x: x[3])
        
        while passenger_data or self.pending_orders:
            self.direction_decider()
            
            for p in passenger_data.copy():
                if p[3] <= self.current_time:
                    self.pending_orders.append(p)
                    passenger_data.remove(p)
            
            print(f"Current Time: {self.current_time}")
            # print(f"Pending Orders: {self.pending_orders}")
            
            if self.pending_orders:
                passenger_data = self.serve_floor(passenger_data)
            
            self.move()
            self.direction_decider()
            self.current_time += self.floor_time
            
            if (self.current_floor_lift_A > self.num_floors or self.current_floor_lift_A < self.lowest_floor or 
                self.current_floor_lift_B > self.num_floors or self.current_floor_lift_B < self.lowest_floor):
                break           
        print("Simulation complete")
