#!/usr/bin/env python3
"""
Combined Elevator Simulation (Refactored without Simplifying Order Handling)

This version groups common functionality in a base class (such as CSV handling,
density updates, and timing) while preserving separate, mode-specific implementations 
for order handling (e.g. serve_stop and assign_passengers) so that the individual 
logic for each mode remains unchanged.
"""

import numpy as np
import pandas as pd
import random
import sys
# ---------------------- Base Class ----------------------
class BaseElevatorSystem:
    def __init__(self, current_floor_A, current_floor_B, num_floors, filepath,passenger_limit, floor_time, delta_time):
        self.current_floor_A = current_floor_A
        self.current_floor_B = current_floor_B
        self.num_floors = num_floors
        self.filepath = filepath
        self.passenger_limit = passenger_limit
        self.floor_time = floor_time  # time per move
        self.delta_time = delta_time  # time period for density snapshots
        self.current_time = 0
        self.floor_passenger_count = [0] * (num_floors + 1)
        self.density_snapshots = []
        self.df = pd.read_csv(filepath)
        self.passenger_arrived = []
        self.passengers_in_lift_A = []
        self.passengers_in_lift_B = []
        self.direction_A = 0
        self.direction_B = 0
        self.orders_done = []
        self.t_persistence = 10
        self.lift_A_population = 0
        self.lift_B_population = 0
        self.status_A = False
        self.status_B = False
        self.picking = True
        self.time_elapsed = 0
        self.time_above_threshold = 0  # Tracks time above a threshold
        self.time_below_threshold = 0

    def update_densities(self):
        """Calculates and stores the density on each floor."""
        densities = [count / self.delta_time for count in self.floor_passenger_count]
        self.density_snapshots.append({"time": self.current_time, "densities": densities})
        return densities

    def compute_dwell_time(self, num_boarding, num_alighting,
                           door_overhead=2.0, min_time=0.8, max_time=2.0, max_parallel=2):
        """Computes dwell time considering parallel processing."""
        if num_boarding + num_alighting == 0:
            return 0.0
        boarding_times = [random.uniform(min_time, max_time) for _ in range(num_boarding)]
        alighting_times = [random.uniform(min_time, max_time) for _ in range(num_alighting)]

        def process_batches(times, max_parallel):
            total = 0.0
            for i in range(0, len(times), max_parallel):
                batch = times[i:i + max_parallel]
                total += max(batch)
            return total

        total_time = door_overhead + max(process_batches(boarding_times, max_parallel),
                                         process_batches(alighting_times, max_parallel))
        return total_time

    
    def data_sorter(self, passenger_data, lift_position):
        grouped = {}
        for item in passenger_data:
            key = item[3]  # Arrival time field
            grouped.setdefault(key, []).append(item)
        sorted_data = []
        for group in grouped.values():
            sorted_group = sorted(group, key=lambda x: abs(x[1] - lift_position))
            sorted_data.extend(sorted_group)
        return sorted_data
# ---------------------- VIP Mode (Detailed Order Handling) ----------------------
class VIPDualSystem(BaseElevatorSystem):
    def __init__(self, current_floor_A, current_floor_B, num_floors,
                filepath, passenger_limit, floor_time, delta_time,
                threshold_density_high, threshold_density_low, current_density, passenger_inout):
        super().__init__(current_floor_A, current_floor_B, num_floors,
                        filepath, passenger_limit, floor_time, delta_time)
        self.threshold_density_high = threshold_density_high
        self.threshold_density_low = threshold_density_low
        self.current_density = current_density
        self.passenger_inout = passenger_inout
        self.pending_orders_A = []
        self.pending_orders_B = []
        self.already_picked = []
        self.orders_not_served = []
        self.floor_to_serve = max(enumerate(current_density), key=lambda x: x[1])[0]

    # Mode-specific movement method for VIP mode
    def move(self, lift_name):
        if lift_name == "A":
            if self.pending_orders_A:
                if self.current_floor_A == 0:
                    self.direction_A = 1
                elif self.current_floor_A == self.num_floors:
                    self.direction_A = -1
            else:
                self.direction_A = 0
            self.current_floor_A += self.direction_A
            print(f"[VIP] Lift A at floor: {self.current_floor_A}")
        elif lift_name == "B":
            if self.pending_orders_B:
                if self.current_floor_B == 0:
                    self.direction_B = 1
                elif self.current_floor_B == self.num_floors:
                    self.direction_B = -1
            else:
                self.direction_B = 0
            self.current_floor_B += self.direction_B
            print(f"[VIP] Lift B at floor: {self.current_floor_B}")

    def serve_stop(self, lift_name, passenger_data):
        if lift_name == "A":
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
            # Attempt drop-off if destination is reached
            dropped += self.drop_passenger(order, lift_name)
            if self.picking():
                dont_pick = self.check_direction_conflict(order, copy_list, direction, lift_name)
                eligible_orders = self.passengers_on_same_floor(order, dont_pick, eligible_orders, lift_name)
        if self.picking():
            passenger_data, number_picked = self.pick_passenger(eligible_orders, lift_name, passenger_data)
        else:
            number_picked = 0
        return passenger_data, number_picked, dropped

    def drop_passenger(self, order, lift_name):
        (Index, passenger_position, passenger_destination,
         Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction) = order
        current_floor = self.current_floor_A if lift_name == "A" else self.current_floor_B
        try:
            if current_floor == passenger_destination and (order in self.already_picked):
                self.already_picked.remove(order)
                if lift_name == "A":
                    self.pending_orders_A.remove(order)
                else:
                    self.pending_orders_B.remove(order)
                if order in self.orders_not_served:
                    self.orders_not_served.remove(order)
                
                Dropping_Passenger = {
                    "Lift ID": lift_name,
                    "Name": Index,
                    "Current floor": passenger_position,
                    "Destination_floor": passenger_destination,
                    "Time": self.current_time,
                    "Status": "Dropping"
                }
                if lift_name=="A":
                    self.lift_A_population-=1
                else:
                    self.lift_B_population-=1
                    
                print(f"[VIP] Dropping passenger {Dropping_Passenger}")
                if lift_name == "A":
                    self.passengers_in_lift_A.remove(order)
                else:
                    self.passengers_in_lift_B.remove(order)
                    
                # Update CSV if available
                self.df["Order completion time"] = self.df["Order completion time"].astype(float)
                self.df.loc[self.df["Index"] == Index, "Order completion time"] = self.current_time
                updated_tuple = self.df.loc[self.df["Index"] == Index].iloc[0]
                
                updated_tuple = tuple(updated_tuple)
                
                self.orders_done.append(updated_tuple)
                self.orders_done.append(order)
                self.df = pd.read_csv(self.filepath)
                if order in self.passenger_arrived:
                    self.passenger_arrived.remove(order)
                
                
                return 1
        except IndexError:
            pass
        return 0

    def check_direction_conflict(self, order, copy_list, direction, lift_name):
        dont_pick = False
        current_floor = self.current_floor_A if lift_name == "A" else self.current_floor_B
        lift_direction = self.direction_A if lift_name == "A" else self.direction_B
        # Retain original conflict-check logic
        if ((min(copy_list, key=lambda x: x[1])[1] < current_floor and lift_direction < 0 and direction > 0) or
            (max(copy_list, key=lambda x: x[1])[1] > current_floor and lift_direction > 0 and direction < 0)):
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

    def passengers_on_same_floor(self, order, dont_pick, eligible_orders, lift_name):
        Index, passenger_position, passenger_destination, _, _, _, direction = order
        current_floor = self.current_floor_A if lift_name == "A" else self.current_floor_B
        pending_orders = self.pending_orders_A if lift_name == "A" else self.pending_orders_B
        if current_floor == passenger_position and not dont_pick:
            if order not in self.already_picked and order not in eligible_orders:
                eligible_orders.append(order)
        if (current_floor == passenger_position and 
            (((passenger_position == min(pending_orders, key=lambda x: x[1])[1]) and (self.get_direction(lift_name) == direction)) or 
             ((passenger_position == max(pending_orders, key=lambda x: x[1])[1]) and (self.get_direction(lift_name) == direction)))):
            if order not in self.already_picked and order not in eligible_orders:
                eligible_orders.append(order)
        return eligible_orders

    def pick_passenger(self, eligible_orders, lift_name, passenger_data):
        number_picked = 0
        if lift_name == "A":
            lift_population = len(self.passengers_in_lift_A)
            current_floor = self.current_floor_A
            pending_orders = self.pending_orders_A
        else:
            lift_population = len(self.passengers_in_lift_B)
            current_floor = self.current_floor_B
            pending_orders = self.pending_orders_B

        if eligible_orders:
            available_space = self.passenger_limit - lift_population
            if len(eligible_orders) > available_space:
                orders_to_pick = random.sample(eligible_orders, available_space)
            else:
                orders_to_pick = eligible_orders[:]
                
            for order in orders_to_pick:
                Index, passenger_position, passenger_destination, _, _, _, direction = order
                
                picking_passenger = {
                    "Lift ID": lift_name,
                    "Name": Index,
                    "Current floor": passenger_position,
                    "Destination_floor": passenger_destination,
                    "Time": self.current_time,
                    "Status": "Picking"
                }
                print(f"[VIP] Picking passenger {picking_passenger}")
                number_picked += 1
                if lift_name=="A":
                    self.lift_A_population+=1
                if lift_name=="B":
                    self.lift_B_population+=1
                if lift_name == "A":
                    self.passengers_in_lift_A.append(order)
                else:
                    self.passengers_in_lift_B.append(order)
                # Update CSV if available
                
                self.df["Lift arrival time"] = self.df["Lift arrival time"].astype(float)
                self.df.loc[self.df["Index"] == Index, "Lift arrival time"] = self.current_time
                self.df.to_csv(self.filepath, index=False)
                
                self.already_picked.append(order)
                self.floor_passenger_count[passenger_position] -= 1
                if self.get_direction(lift_name) == 0:
                    self.set_direction(lift_name, direction)
                    
                if current_floor == passenger_position and (((passenger_position == min(pending_orders, key=lambda x: x[1])[1]) and (self.get_direction(lift_name) == direction)) or ((passenger_position == max(pending_orders, key=lambda x: x[1])[1]) and (self.get_direction(lift_name) == direction))):
                    self.set_direction(lift_name, direction)
                    
            # If the lift is full, remove extra orders
            if lift_name == "A" and len(self.passengers_in_lift_A) == self.passenger_limit:
                for order in self.pending_orders_A[:]:
                    if order not in self.passengers_in_lift_A:
                        self.pending_orders_A.remove(order)
                        passenger_data.append(order)
            if lift_name == "B" and len(self.passengers_in_lift_B) == self.passenger_limit:
                for order in self.pending_orders_B[:]:
                    if order not in self.passengers_in_lift_B:
                        self.pending_orders_B.remove(order)
                        passenger_data.append(order)
        return passenger_data, number_picked

    def get_direction(self, lift_name):
        return self.direction_A if lift_name == "A" else self.direction_B

    def set_direction(self, lift_name, direction):
        if lift_name == "A":
            self.direction_A = direction
        else:
            self.direction_B = direction

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

    def run_simulation(self, passenger_data):
        """Run the VIP simulation over a fixed time period."""
        passenger_data = sorted(passenger_data, key=lambda x: x[3])
        returning = False
        while not returning:
            # Process pending orders with arrival time ≤ current time.
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
                pending_orders = [p for p in passenger_data if p[3] <= self.current_time]
                
                for p in pending_orders:
                    if p not in self.passenger_arrived:
                        self.passenger_arrived.append(p)
                        floor = p[1]
                        self.floor_passenger_count[floor] += 1
                pending_orders = sorted(pending_orders, key=lambda x: x[3])
                print("pending_orders",pending_orders)
                if self.current_time % self.delta_time == 0:
                    dens = self.update_densities()
                    print(f"[VIP] Density at time {self.current_time}: {dens}")
                    self.current_density = dens
                    self.time_elapsed = 0
                if pending_orders:
                    self.assign_passengers(pending_orders)
            
                self.pending_orders_A = self.data_sorter(self.pending_orders_A, self.current_floor_A)
                self.pending_orders_B = self.data_sorter(self.pending_orders_B, self.current_floor_B)
                
                for person in passenger_data[:]:
                    if person in self.pending_orders_A or person in self.pending_orders_B:
                        passenger_data.remove(person)
                        
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
                if self.current_floor_A > self.num_floors or self.current_floor_A < 0 or self.current_floor_B>self.num_floors or self.current_floor_B<0:
                    print("There was an error")
                    raise Exception("There is an Error")
                dwell_time_B = self.compute_dwell_time(num_boarding=number_lift_B_picked, num_alighting=dropped_by_B)
                dwell_time_A = self.compute_dwell_time(num_boarding=number_lift_A_picked, num_alighting=dropped_by_A)
                self.current_time += self.floor_time + dwell_time_B + dwell_time_A
                self.time_elapsed += self.floor_time + dwell_time_B + dwell_time_A
                
                if max(self.current_density)<=self.threshold_density_low:
                    self.picking = False
                    # sys.exit()
                    self.time_below_threshold += self.floor_time + dwell_time_B + dwell_time_A
                    if self.time_below_threshold>=self.t_persistence and self.lift_A_population==0 and self.lift_B_population==0:
                        returning = True
                        self.time_below_threshold = 0
                for person in passenger_data[:]:
                    if person in self.pending_orders_A or person in self.pending_orders_B:
                        passenger_data.remove(person)
            
            
        print("VIP simulation complete.")
        return passenger_data

# ---------------------- Oscillation Mode (Detailed Order Handling) ----------------------
class DualOscillation(BaseElevatorSystem):
    def __init__(self, current_floor_A, current_floor_B, num_floors, filepath, passenger_limit,
                 floor_time, delta_time, threshold_density_high, threshold_density_low, current_density, lowest_floor):
        super().__init__(current_floor_A, current_floor_B, num_floors,
                         filepath, passenger_limit, floor_time, delta_time)
        self.threshold_density_high = threshold_density_high
        self.threshold_density_low = threshold_density_low
        self.current_density = current_density
        self.pending_orders = []
        self.lowest_floor = lowest_floor

    def move(self):
        self.current_floor_A += self.direction_A
        self.current_floor_B += self.direction_B
        print(f"[Oscillation] Lift A: {self.current_floor_A}, Lift B: {self.current_floor_B}")
    def direction_decider(self):
        if self.current_floor_A == self.lowest_floor:
            self.direction_A = 1
        elif self.current_floor_A == self.num_floors:
            self.direction_A = -1

        if self.current_floor_B == self.lowest_floor:
            self.direction_B = 1
        elif self.current_floor_B == self.num_floors:
            self.direction_B = -1
            
    def serve_floor(self, passenger_data):
        for order in self.pending_orders.copy():
            Index, Passenger_position, Passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = order
            if self.current_floor_A == Passenger_destination and order in self.passengers_in_lift_A:
                self.pending_orders.remove(order)
                self.passengers_in_lift_A.remove(order)
                self.lift_A_population -= 1
                Dropping_Passenger = {
                    "Lift ID": "Lift A",
                    "Name": Index,
                    "Current floor": Passenger_position,
                    "Destination_floor": Passenger_destination,
                    "Time": self.current_time,
                    "Status": "Dropping"
                }
                print(f"[Oscillation] Dropped passenger {Dropping_Passenger}")
                
                self.df["Order completion time"] = self.df["Order completion time"].astype(float)
                self.df.loc[self.df["Index"] == Index, "Order completion time"] = self.current_time
                updated_tuple = self.df.loc[self.df["Index"] == Index].iloc[0]
                updated_tuple = tuple(updated_tuple)
                self.orders_done.append(updated_tuple)
                self.df.to_csv(self.filepath, index=False)
                if order in self.passenger_arrived:
                    self.passenger_arrived.remove(order)
            if self.current_floor_B == Passenger_destination and order in self.passengers_in_lift_B:
                self.pending_orders.remove(order)
                self.passengers_in_lift_B.remove(order)
                self.lift_B_population -= 1
                Dropping_Passenger = {
                    "Lift ID": "Lift B",
                    "Name": Index,
                    "Current floor": Passenger_position,
                    "Destination_floor": Passenger_destination,
                    "Time": self.current_time,
                    "Status": "Dropping"
                }
                print(f"[Oscillation] Dropped passenger: {Dropping_Passenger}")
                self.df["Order completion time"] = self.df["Order completion time"].astype(float)
                self.df.loc[self.df["Index"] == Index, "Order completion time"] = self.current_time
                updated_tuple = self.df.loc[self.df["Index"] == Index].iloc[0]
                updated_tuple = tuple(updated_tuple)
                self.orders_done.append(updated_tuple)
                self.df.to_csv(self.filepath, index=False)
                if order in self.passenger_arrived:
                    self.passenger_arrived.remove(order)
            
            #Picking    
            if self.current_floor_A == Passenger_position and order not in self.passengers_in_lift_A:
                if self.lift_A_population < self.passenger_limit:
                    
                    picking_passenger = {
                    "Lift ID": "Lift A",
                    "Name": Index,
                    "Current floor": Passenger_position,
                    "Destination_floor": Passenger_destination,
                    "Time": self.current_time,
                    "Status": "Picking"
                    }
                    
                    print(f"[Oscillation] Picked up passenger:{picking_passenger}")
                    
                    self.df["Lift arrival time"] = self.df["Lift arrival time"].astype(float)
                    self.df.loc[self.df["Index"] == Index, "Lift arrival time"] = self.current_time
                    
                    self.passengers_in_lift_A.append(order)
                    self.lift_A_population += 1
                    self.floor_passenger_count[Passenger_position] -= 1
                else:
                    self.pending_orders.remove(order)
                    passenger_data.append(order)
                    
            if self.current_floor_B == Passenger_position and order not in self.passengers_in_lift_B:
                if self.lift_B_population < self.passenger_limit:
                    
                    picking_passenger = {
                    "Lift ID": "Lift B",
                    "Name": Index,
                    "Current floor": Passenger_position,
                    "Destination_floor": Passenger_destination,
                    "Time": self.current_time,
                    "Status": "Picking"
                    }
                    
                    print(f"[Oscillation] Picked up passenger:{picking_passenger}")
                    
                    self.df["Lift arrival time"] = self.df["Lift arrival time"].astype(float)
                    self.df.loc[self.df["Index"] == Index, "Lift arrival time"] = self.current_time
                    
                    self.passengers_in_lift_B.append(order)
                    self.lift_B_population += 1
                    self.floor_passenger_count[Passenger_position] -= 1
                else:
                    self.pending_orders.remove(order)
                    passenger_data.append(order)
                    
            
        return passenger_data

    def run_simulation(self, passenger_data):
        passenger_data = sorted(passenger_data, key=lambda x: x[3])
        if self.threshold_density_low < np.mean(self.current_density) and self.time_below_threshold <= self.t_persistence:
            #deciding the direction for each lift
            if self.current_floor_A > self.current_floor_B:
                    self.direction_A = 1 if self.current_floor_A != self.num_floors else 0
                    self.direction_B = -1 if self.current_floor_B != 0 else 0
            elif self.current_floor_A < self.current_floor_B:
                self.direction_A = -1 if self.current_floor_A != 0 else 0
                self.direction_B = 1 if self.current_floor_B != self.num_floors else 0
            elif (self.current_floor_A) == self.current_floor_B:
                if self.current_floor_A==0:
                    self.direction_A = 0
                    self.direction_B = 1
                elif self.current_floor_A==self.num_floors:
                    self.direction_A = -1
                    self.direction_B = 0
                else:
                    self.direction_A = 1
                    self.direction_B = -1
            returning = False
            while ((self.current_floor_A != 0 and self.current_floor_B != self.num_floors) or (self.current_floor_A != self.num_floors and self.current_floor_B != 0) or (self.current_floor_A==self.current_floor_B)) and (not returning):
                if self.current_floor_A==self.num_floors or self.current_floor_A==0:
                    self.direction_A=0
                elif self.current_floor_B==self.num_floors or self.current_floor_B==0:
                    self.direction_B=0
                if (self.current_floor_A) == self.current_floor_B:
                    if self.current_floor_A==0:
                        self.direction_A = 0
                        self.direction_B = 1
                    elif self.current_floor_A==self.num_floors:
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
                            if p not in self.passenger_arrived:
                                self.passenger_arrived.append(p)
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
                
                if (self.current_floor_A==self.num_floors and self.current_floor_B==0) or (self.current_floor_A==0 and self.current_floor_B==self.num_floors):
                    print("They are at the two ends")
                    returning=True
                    
                if self.threshold_density_low >= np.mean(self.current_density):
                    self.picking = False
                    self.time_below_threshold += self.floor_time
                    if  self.time_below_threshold >= self.t_persistence:
                        returning = True
                        self.time_below_threshold = 0
            #The lifts are at either ends now...there are tww possibilities they have served enough to get the density down or they have not if they have then we just need to make the population 0 if not then we move to serving
            
            if np.mean(self.current_density) <= self.threshold_density_low:
                self.picking = False
            else:
                self.picking = True
            if np.mean(self.current_density) <= self.threshold_density_low and self.time_below_threshold >= self.t_persistence and  self.lift_A_Population==0 and self.lift_B_Population==0:
                returning = True                
            else:
                returning = True                
            
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

                if (self.current_floor_A > self.num_floors or self.current_floor_A < self.lowest_floor or 
                    self.current_floor_B > self.num_floors or self.current_floor_B < self.lowest_floor):
                    print("There has been an error in the Oscillation code")
                    break
                print(f"Current Time: {self.current_time}")
        return passenger_data

# ---------------------- Adaptive System (Detailed Order Handling) ----------------------
class DualLiftSystemAdaptive(BaseElevatorSystem):
    def __init__(self, current_floor_A, current_floor_B, num_floors, filepath, passenger_limit,
                 floor_time, delta_time, T_high_oscillation, T_low_oscillation,
                 T_high_VIP, T_low_VIP, floor_time_oscillation, current_time=0):
        super().__init__(current_floor_A, current_floor_B, num_floors, filepath,
                         passenger_limit, floor_time, delta_time)
        self.T_high_oscillation = T_high_oscillation
        self.T_low_oscillation = T_low_oscillation
        self.T_high_VIP = T_high_VIP
        self.T_low_VIP = T_low_VIP
        self.floor_time_oscillation = floor_time_oscillation
        self.pending_orders_A = []
        self.pending_orders_B = []
        self.current_density = [0] * (self.num_floors + 1)
        self.current_mode = "normal"
        self.time_below_threshold = 0
        self.time_above_threshold = 0
        self.already_picked = []
        self.orders_not_served = []
        self.orders_in_opposite_direction = []

    def move(self, lift="A"):
        if lift == "A":
            if self.pending_orders_A:
                if self.current_floor_A == 0:
                    self.direction_A = 1
                elif self.current_floor_A == self.num_floors:
                    self.direction_A = -1
            else:
                self.direction_A = 0
            self.current_floor_A += self.direction_A
            print(f"[Adaptive] Lift A: {self.current_floor_A}")
        else:
            if self.pending_orders_B:
                if self.current_floor_B == 0:
                    self.direction_B = 1
                elif self.current_floor_B == self.num_floors:
                    self.direction_B = -1
            else:
                self.direction_B = 0
            self.current_floor_B += self.direction_B
            print(f"[Adaptive] Lift B: {self.current_floor_B}")

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
                
                if order in self.passenger_arrived:
                    self.passenger_arrived.remove(order)
                
                # Update the DataFrame
                self.df["Order completion time"] = self.df["Order completion time"].astype(float)
                self.df.loc[self.df["Index"] == Index, "Order completion time"] = self.current_time

                # Extract the updated tuple
                updated_tuple = self.df.loc[self.df["Index"] == Index].iloc[0]
                
                updated_tuple = tuple(updated_tuple)
                
                self.orders_done.append(updated_tuple)
                
                print(f"update_line: {updated_tuple}")
                
                # Reload the DataFrame to reflect the changes
                
                self.df = pd.read_csv(self.filepath)
            
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
                self.df["Lift arrival time"] = self.df["Lift arrival time"].astype(float)
                self.df.loc[self.df["Index"] == Index, "Lift arrival time"] = self.current_time
                # Reload the DataFrame to reflect the changes
                self.df.to_csv(self.filepath, index=False)  # Ensure you save the changes to the file

                self.already_picked.append(order)
    
                if all(passenger == 0 for passenger in self.floor_passenger_count):
                    print("No passengers on any floor:", self.floor_passenger_count)
                    sys.exit()
                
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
        if pending_orders:
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
                    print(f"{person} removed from {name} to {name1}")
        return source_list, target_list
    
    def switch_to_oscillation(self, passenger_data):
        if (self.lift_A_population == 0 and self.lift_B_population==0) and not self.picking:
            
            if self.pending_orders_A:
                for person in self.pending_orders_A.copy():
                    if person not in passenger_data:
                        passenger_data.append(person)
                    self.pending_orders_A.remove(person)
            if self.pending_orders_B:
                for person in self.pending_orders_B.copy():
                    if person not in passenger_data:
                        passenger_data.append(person)
                    self.pending_orders_B.remove(person)
                    
            print(f"Switching to oscillation at time {self.current_time}")
            metro = DualOscillation(current_floor_A=self.current_floor_A,current_floor_B=self.current_floor_B, num_floors=self.num_floors, delta_time=self.delta_time, threshold_density_high=self.T_high_oscillation,threshold_density_low = self.T_low_oscillation , filepath = self.filepath, current_density=self.current_density, floor_time = self.floor_time_oscillation, lowest_floor = 0, passenger_limit = self.passenger_limit)  
             
            updated_passenger_Data = metro.run_simulation(passenger_data)
            if self.passengers_in_lift_A:
                for people in self.passengers_in_lift_A:
                    if people not in self.pending_orders_A:
                        self.pending_orders_A.append(people)
                    if people not in self.already_picked:
                        self.already_picked.append(people)
            if self.passengers_in_lift_B:
                for people in self.passengers_in_lift_B:
                    if people not in self.pending_orders_B:
                        self.pending_orders_B.append(people)
                    if people not in self.already_picked:
                        self.already_picked.append(people)

            for passenger in metro.pending_orders:
                if (passenger not in self.passengers_in_lift_A) and (passenger not in self.passengers_in_lift_B) and (passenger not in metro.orders_done):
                    updated_passenger_Data.append(passenger)
                        
            if self.pending_orders_A:                    
                self.status_A = True
            else:
                self.status_A = False
                
            if self.pending_orders_B:
                self.status_B = True
            else:
                self.status_B = False 
            
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
        
        VIP = VIPDualSystem(threshold_density_high=self.T_high_VIP,threshold_density_low=self.T_low_VIP,current_density=self.current_density, current_time = self.current_time,floor_time = self.floor_time,passenger_inout = self.passenger_inout)
        updated_passenger_Data = VIP.run_simulation(passenger_data)
        
        if self.passengers_in_lift_A:
            for people in self.passengers_in_lift_A:
                if people not in self.pending_orders_A:
                    self.pending_orders_A.append(people)
                if people not in self.already_picked:
                    self.already_picked.append(people)
        if self.passengers_in_lift_A:
            for people in VIP.passengers_in_lift_B:
                if people not in self.pending_orders_B:
                    self.pending_orders_B.append(people)
                if people not in self.already_picked:
                    self.already_picked.append(people)
                
                    
        total = self.pending_orders_A + self.pending_orders_B
        for passenger in total:
            if (passenger not in VIP.passengers_in_lift_A) and (passenger not in VIP.passengers_in_lift_B) and (passenger not in VIP.orders_done):
                updated_passenger_Data.append(passenger)
        if self.already_picked:
            for passenger in VIP.already_picked:
                if passenger not in self.already_picked:
                    self.already_picked.append(passenger)
        if VIP.orders_not_served:
            for passenger in VIP.orders_not_served:
                if passenger not in self.orders_not_served:
                    self.orders_not_served.append(passenger)
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
                    if passenger not in self.passenger_arrived:
                        self.passenger_arrived.append(passenger)
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
                self.pending_orders_B, self.pending_orders_A = self.reassign_passenger(person, self.pending_orders_B, self.pending_orders_A, self.current_floor_A, self.direction_A)
            for person in list(self.pending_orders_A).copy():
                self.pending_orders_A, self.pending_orders_B = self.reassign_passenger(person, self.pending_orders_A, self.pending_orders_B, self.current_floor_B, self.direction_B)
                
            for person in people_not_assigned[:]:
                if person in self.pending_orders_A or person in self.pending_orders_B:
                    people_not_assigned.remove(person)
            
            for person in list(people_not_assigned):
                people_not_assigned, self.pending_orders_A = self.reassign_passenger(person, people_not_assigned, self.pending_orders_A, self.current_floor_A, self.direction_A)
                people_not_assigned, self.pending_orders_B = self.reassign_passenger(person, people_not_assigned, self.pending_orders_B, self.current_floor_B, self.direction_B)
            
            
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
            
            total = self.pending_orders_A + self.pending_orders_B
            for person in total:
                if person in passenger_data:
                    passenger_data.remove(person)
            
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

            # self.current_time += self.floor_time + (number_lift_B_picked + number_lift_A_picked + dropped_by_B + dropped_by_A)*self.passenger_inout
            
            # self.time_elapsed += self.floor_time + (number_lift_B_picked + number_lift_A_picked + dropped_by_B + dropped_by_A)*self.passenger_inout

            dwell_time_B = self.compute_dwell_time(num_boarding=number_lift_B_picked, num_alighting=dropped_by_B)
            dwell_time_A = self.compute_dwell_time(num_boarding=number_lift_A_picked, num_alighting=dropped_by_A)
            self.current_time += self.floor_time + dwell_time_B + dwell_time_A
            self.time_elapsed += self.floor_time + dwell_time_B + dwell_time_A

            
            count_greater_than_T_high_VIP = sum(1 for value in self.current_density if value > self.T_high_VIP)
            
            if (np.mean(self.current_density) > self.T_high_oscillation) or (max(self.current_density)>=self.T_high_VIP and count_greater_than_T_high_VIP==1):
                self.time_above_threshold += self.floor_time + dwell_time_B + dwell_time_A
            
            if np.mean(self.current_density) >= self.T_high_oscillation and self.time_above_threshold >= self.t_persistence and (self.current_mode=="normal"):
                #the mean of the current densities is higher than the threshold given and time above this threshold is also more than the t_persistence this means that this change is not sudden. Now we need to switch to oscillation system, to do so we need to first empty the lifts by serving the passengers in the lifts and then stop picking passengers.
                print("Switching to Oscillation system")
                print("No more picking")
                print(self.lift_A_population)
                print(self.lift_B_population)
                
                self.picking = False           
                
                self.current_mode = "oscillation"
                   
            elif max(self.current_density)>=self.T_high_VIP and self.time_above_threshold>=self.t_persistence and (self.current_mode=="normal") and count_greater_than_T_high_VIP==1:
                print("Switching to VIP system")
                #he max of the current densities is higher than the threshold given and ther is only one such floor and time above this threshold is also more than the t_persistence this means that this change is not sudden. Now we need to switch to oscillation system, to do so we need to first empty the lifts by serving the passengers in the lifts and then stop picking passengers.
                print("No more picking")
                self.picking = False
                self.current_mode = "VIP"
                
            
            if not self.picking and (self.lift_A_population==0 and self.lift_B_population==0) and self.current_mode=="oscillation":
                print("preparing to switch to oscillation")
                people_not_assigned = []
                self.passenger_arrived = []
                passenger_data = self.switch_to_oscillation(passenger_data)
                
                self.current_mode = "normal"
                self.picking = True
                
                # self.floor_passenger_count = [0] * (self.num_floors + 1)
                # temporary_pending_orders = self.pending_orders_A + self.pending_orders_B
                
                # for passenger in temporary_pending_orders:
                #     # input(f"passenger = {passenger}")
                #     if passenger not in self.passenger_arrived:
                #         self.passenger_arrived.append(passenger)
                #         floor = passenger[1]
                #         self.floor_passenger_count[floor]+=1
                
                self.time_above_threshold = 0
                
            elif not self.picking and (self.lift_A_population==0 and self.lift_B_population==0) and self.current_mode == "VIP":
                print("Preparing to switch to VIP")
                people_not_assigned = []
                self.passenger_arrived = []
                passenger_data = self.switch_to_VIP(passenger_data)
                self.current_mode = "normal"
                self.picking = True
                
                # self.floor_passenger_count = [0] * (self.num_floors + 1)
                # temporary_pending_orders = self.pending_orders_A + self.pending_orders_B
                self.time_above_threshold = 0

                # for passenger in temporary_pending_orders:
                #     input(f"passenger = {passenger}")
                #     if passenger not in self.passenger_arrived:
                #         self.passenger_arrived.append(passenger)
                #         floor = passenger[1]
                #         self.floor_passenger_count[floor]+=1
            
            if self.lift_A_population==0 and self.pending_orders_A and not passenger_data:
                for order in self.pending_orders_A:
                    self.pending_orders_A.remove(order)
                    passenger_data.append(order)

            if self.lift_B_population==0 and self.pending_orders_B and not passenger_data:
                for order in self.pending_orders_B:
                    self.pending_orders_B.remove(order)
                    passenger_data.append(order)     
            print(self.current_time)    
        return passenger_data


# # ---------------------- Main Execution ----------------------
# if __name__ == "__main__":

#     data = [(1, 0, 2, 0, 0, 0, 1), (2, 1, 3, 0, 0, 0, 1), (3, 2, 3, 0, 0, 0, 1), (4, 3, 1, 0, 0, 0, -1), (5, 4, 3, 0, 0, 0, -1), (6, 5, 4, 0, 0, 0, -1), (7, 3, 5, 394, 0, 0, 1), (8, 4, 2, 418, 0, 0, -1), (9, 3, 2, 522, 0, 0, -1), (10, 1, 0, 572, 0, 0, -1), (11, 0, 3, 690, 0, 0, 1), (12, 2, 1, 759, 0, 0, -1), (13, 2, 5, 878, 0, 0, 1), (14, 5, 1, 1045, 0, 0, -1), (15, 5, 1, 1346, 0, 0, -1), (16, 1, 5, 1436, 0, 0, 1), (17, 4, 5, 1664, 0, 0, 1), (18, 4, 1, 1726, 0, 0, -1), (19, 4, 1, 1822, 0, 0, -1), (20, 1, 2, 2032, 0, 0, 1), (21, 3, 4, 2068, 0, 0, 1), (22, 1, 3, 2083, 0, 0, 1), (23, 3, 0, 2150, 0, 0, -1), (24, 0, 3, 2186, 0, 0, 1), (25, 4, 2, 2200, 0, 0, -1), (26, 1, 4, 2290, 0, 0, 1), (27, 3, 0, 2389, 0, 0, -1), (28, 3, 4, 2433, 0, 0, 1), (29, 5, 1, 2510, 0, 0, -1), (30, 5, 4, 2582, 0, 0, -1), (31, 1, 2, 2998, 0, 0, 1), (32, 1, 3, 3043, 0, 0, 1), (33, 2, 0, 3127, 0, 0, -1), (34, 3, 5, 3198, 0, 0, 1), (35, 4, 3, 3263, 0, 0, -1), (36, 5, 2, 3426, 0, 0, -1), (37, 0, 1, 3438, 0, 0, 1), (38, 2, 1, 3461, 0, 0, -1), (39, 4, 0, 3590, 0, 0, -1), (40, 4, 2, 3596, 0, 0, -1)]
#     num_floors = 5
#     T_high_oscillation = 0.06
#     T_low_oscillation = 0.03
#     T_high_VIP = 1
#     T_low_VIP = 0.5
#     passenger_limit = 8
#     delta_time = 5
#     floor_time = 1
#     passenger_inout = 3
#     floor_time_oscillation = 4
#     current_floor_A = 0
#     current_floor_B = 5
#     file_path = "refined_passenger_data.csv"
#     current_density = [0]*(num_floors+1)

#     adaptive_system = DualLiftSystemAdaptive(
#             current_floor_A, current_floor_B, num_floors, file_path,
#             passenger_limit, floor_time, delta_time,
#             T_high_oscillation=0.06, T_low_oscillation=0.03,
#             T_high_VIP=1, T_low_VIP=0.5, floor_time_oscillation=floor_time_oscillation
#         )

#     adaptive_system.run_simulation(data)
#     print("done")