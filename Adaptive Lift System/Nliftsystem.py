import pandas as pd  # Importing pandas library for data manipulation and CSV operations
import random         # Importing random library for random sampling
import csv
import logging
import numpy as np
class NLiftSystem:
    def __init__(self, current_floors, num_floors, filepath, Passenger_limit, number_of_lifts,delta_time,threshold_density,current_density, current_time=0):
        """
        Initialize the NLiftSystem class.

        Parameters:
        - current_floors: List of initial floor positions for the 4 lifts.
        - num_floors: Total number of floors in the building.
        - filepath: Path to the CSV file containing passenger data.
        - Passenger_limit: Maximum capacity of passengers for each lift.
        - current_time: Starting time for the simulation (default is 0).

        Creates the initial state for all lifts, including their current floor,
        direction, passengers, pending orders, and other attributes.
        """
        
        logging.basicConfig(level=logging.DEBUG, filename='Graphs/Lift_debug.log', filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s')
        
        logging.info("Initializing the FourLiftSystem class.")
        
        self.num_floors = num_floors  # Total number of floors in the building
        self.filepath = filepath      # Filepath for passenger data CSV
        
        logging.debug(f"Reading passenger data from: {filepath}")
        # self.df_read = pd.read_csv(filepath)  # Load passenger data from CSV file

        
        self.current_time = current_time # Current simulation time
        self.Passenger_limit = Passenger_limit # Maximum passengers per lift

        # Initialize lift states
        logging.debug("Initializing lift states.")
        self.lifts = {  
                f"Lift_{i+1}": {  # Create lift dictionaries for 4 lifts
                    "current_floor": current_floors[i],  # Set the initial floor for each lift
                    "direction": 0,  # 1 for up, -1 for down, 0 for idle
                    "passengers": [],  # List of passengers in the lift
                    "pending_orders": [],  # List of orders pending for this lift
                    "population": 0,  # Current number of passengers in the lift
                    "status": False  # False if idle, True if moving
                }
                for i in range(number_of_lifts)  # Repeat for each of the 4 lifts
            }
        logging.info(f"Lift states initialized: {self.lifts}")

        # Global state
        self.orders_in_opposite_direction = []
        self.already_picked = []
        self.orders_done = []
        self.orders_not_served = []
        
        self.passenger_inout = 3
        self.floor_time = 1
        
        self.threshold_density = threshold_density
        self.time_elapsed = 0
        self.density_snapshots = []  # To store densities over time
        self.floor_passenger_count = [0] * (self.num_floors + 1)
        self.current_density = np.mean(current_density)
        print(f"Initial mean density: {self.current_density}")
        self.delta_time = delta_time

    def move(self, lift_name): #i think this is good
        """
        Move the specified lift to the next floor based on its direction.

        Parameters:
        - lift_name: The name of the lift to move (e.g., "Lift_1").

        The lift's current floor is incremented or decremented based on its direction:
        - 1: Moves up
        - -1: Moves down
        - 0: Remains idle
        Also updates the direction to idle (0) if there are no pending orders.
        """
        logging.debug(f"Moving lift: {lift_name}")

        lift = self.lifts[lift_name] #fetching the lift
        
        if lift["pending_orders"]:
            if lift["current_floor"] == 0:
                lift["direction"] = 1
            elif lift["current_floor"] == self.num_floors:
                lift["direction"] = -1
            
            lift["current_floor"] += lift["direction"]
            
            logging.info(f"{lift_name} is moving to floor {lift['current_floor']}")
            print(f"{lift_name} position: {lift['current_floor']}")
        
        if lift["pending_orders"]==[]:
            lift["direction"] = 0
            logging.info(f"{lift_name} is idle at floor {lift['current_floor']}")
            print(f"{lift_name} is idle at floor {lift['current_floor']}")       

    def data_sorter(self, pending_order,lift_name):
        """
        Sort pending orders for a lift based on proximity to its current floor.

        Parameters:
        - pending_order: List of passenger orders to be sorted.
        - lift_name: The name of the lift processing these orders.

        The function groups orders by their arrival times and sorts them based on 
        their distance from the current floor of the lift. Returns the sorted order list.
        """

        logging.debug(f"Sorting pending orders for {lift_name}")
        
        lift = self.lifts[lift_name]
        # Initialize an empty dictionary to hold the grouped tuples
        grouped_by_index_3 = {}

        # Iterate over each tuple in the data
        for item in pending_order:
            # Get the value at the fourth index (index 3)
            key = item[3]

            # Add the item to the corresponding list in the dictionary
            grouped_by_index_3.setdefault(key, []).append(item)

        sorted_data = []

        # Iterate over the groups in the dictionary
        for group in grouped_by_index_3.values():
            # Sort each group based on the absolute difference between the second index value (index 1) and the given position
            sorted_group = sorted(group, key=lambda x: abs(x[1] - lift["current_floor"]))
            # Extend the sorted_data list with the sorted group
            sorted_data.extend(sorted_group)

        logging.info(f"Sorted data for {lift_name}: {sorted_data}")
        return sorted_data
    
    def drop_passenger(self,order,lift_name):
        """
        Drop a passenger at their destination floor if the lift is at the correct floor.

        Parameters:
        - order: The passenger order tuple.
        - lift_name: The name of the lift processing the order.

        If the current floor matches the passenger's destination:
        - Removes the passenger from the lift's pending orders and passenger list.
        - Updates the order's completion time in the dataset.
        - Moves the order to the 'orders_done' list.
        """
        
        (Index, passenger_position, passenger_destination, 
        Passenger_arrival_time, Lift_arrival_time, 
        Order_completion_time, direction) = order
        
        lift = self.lifts[lift_name]
        current_floor = lift["current_floor"]
        lift_direction = lift["direction"]
        
        try:
            logging.debug(f"Dropping passenger: {order}")
            if current_floor == passenger_destination and (order in self.already_picked):
                # print(f"going to remove {order} from {lift_name}")
                lift["pending_orders"].remove(order)
                
                if order in self.orders_not_served:
                    self.orders_not_served.remove(order)
                    
                Dropping_Passenger = {
                    "Lift ID": lift_name,
                    "Name": Index,
                    "Current Floor": passenger_position,
                    "Destination Floor": passenger_destination,
                    "Time": self.current_time,
                    "status": "Dropping"
                }
                
                print(f"Dropping a Passenger:\n\n{Dropping_Passenger}\n\n")
                
                logging.debug(f"Trying to drop passenger: {order} from lift: {lift_name}")
                
                lift["passengers"].remove(order)
                lift["population"]-=1
                # print(lift["pending_orders"])
                
                '''I had a doubt here which is should we update the time here or not then I remembered....the time at which the lift has come to this floor is the same for all so the time for them getting served is not the fault of the elevator but a thing of them not being able to get down quickly'''
                
                # self.df_read.loc[self.df_read["Index"]==Index, "Order completion time"] = self.current_time
                
                # updated_tuple = self.df_read.loc[self.df_read["Index"]==Index].iloc[0]
                
                # updated_tuple = tuple(updated_tuple)
                
                # self.orders_done.append(updated_tuple)
                # print(f"updated Line: {updated_tuple}")
                
                # self.df_read = pd.read_csv(self.filepath)
                
                logging.info(f"Passenger {order} dropped successfully.")
                return 1
        except IndexError:
            pass
        return 0
    
    def check_direction_conflict(self,order,copy_list,direction,lift_name):
        """
        Check for conflicts in direction between the lift and a pending order.

        Parameters:
        - order: The passenger order to evaluate.
        - copy_list: A copy of the current lift's pending orders.
        - direction: The direction of the passenger's order (1 for up, -1 for down).
        - lift_name: The name of the lift.

        Returns:
        - True if a direction conflict exists (e.g., lift is moving up but passenger wants to go down).
        - False otherwise.

        If a conflict is found, the order is added to the 'orders_not_served' list.
        """
        logging.debug(f"Checking direction conflict for {order}")
        dont_pick = False
        
        lift = self.lifts[lift_name]
        current_floor = lift["current_floor"]
        lift_direction = lift["direction"]
        
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
        logging.info(f"Direction conflict for {order}: {dont_pick} thus was not picked")
        return dont_pick
    
    def Passengers_on_same_floor(self, order, dont_pick, eligible_orders,lift_name):
        """
        Check if passengers on the same floor as the lift can be picked up.

        Parameters:
        - order: The passenger order to evaluate.
        - dont_pick: Boolean indicating if the lift should avoid picking up this order.
        - eligible_orders: List of orders eligible for pickup.
        - lift_name: The name of the lift.

        Adds eligible orders to the list if the passenger is on the current floor
        and the lift's direction matches the passenger's destination direction.
        """

        logging.debug(f"Checking for passengers on the same floor as {lift_name}")
        
        Index, passenger_position, passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = order

        lift = self.lifts[lift_name]
        current_floor = lift["current_floor"]
        lift_direction = lift["direction"]
        pending_orders = lift["pending_orders"]
        
        if current_floor == passenger_position and not dont_pick:
            if order not in self.already_picked and order not in eligible_orders:
                eligible_orders.append(order)
                

        # Additional condition to ensure Lift arrival time is updated correctly
        if current_floor == passenger_position and (((passenger_position == min(pending_orders, key=lambda x: x[1])[1]) and (lift_direction == direction)) or ((passenger_position == max(pending_orders, key=lambda x: x[1])[1]) and (lift_direction == direction))):
            if order not in self.already_picked and order not in eligible_orders:
                eligible_orders.append(order)
        
        logging.info(f"Eligible orders for {lift_name}: {eligible_orders}")
        return eligible_orders
                
    def pick_passenger(self, eligible_orders,lift_name, passenger_data):
        """
        Pick up passengers from the current floor if they meet eligibility criteria.

        Parameters:
        - eligible_orders: List of passenger orders eligible for pickup.
        - lift_name: The name of the lift picking up passengers.
        - passenger_data: List of all passenger data in the simulation.

        Updates the lift's passenger list, direction, and pending orders. Ensures
        that the lift does not exceed its passenger capacity. Returns updated
        passenger data and the number of passengers picked.
        """
        logging.debug(f"Picking up passengers for {lift_name}")
        number_people_picked = 0
        
        lift = self.lifts[lift_name]
        lift_population = lift["population"]
        current_floor = lift["current_floor"]
        lift_direction = lift["direction"]

        if eligible_orders:
            # Calculate available space in the lift
            once = False
            available_space = self.Passenger_limit - lift_population
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

                logging.info(f"Picking up passenger: {order}")
                lift["passengers"].append(order)
                lift["population"]+=1
                
            
                # Update the DataFrame with the new value
                # self.df_read.loc[self.df_read["Index"] == Index, "Lift arrival time"] = self.current_time
                # # Reload the DataFrame to reflect the changes
                # self.df_read.to_csv(self.filepath, index=False)  # Ensure you save the changes to the file

                self.already_picked.append(order)
                if not once:
                    lift["direction"]=direction
                    once = True  # Set once to True after updating the direction
                
                pending_orders = lift["pending_orders"]
                
                if current_floor == passenger_position and (((passenger_position == min(pending_orders, key=lambda x: x[1])[1]) and (lift_direction == direction)) or ((passenger_position == max(pending_orders, key=lambda x: x[1])[1]) and (lift_direction == direction))):
                    
                    lift["direction"]=direction
                
                if lift["population"] == self.Passenger_limit:
                    for passenger in lift["pending_orders"][:]:
                        if passenger not in lift["passengers"]:
                            lift["pending_orders"].remove(passenger)
                            passenger_data.append(passenger)
                            print("passenger not picked", passenger)
                            
            logging.info(f"Passengers picked for {lift_name}: {number_people_picked}")
        logging.info(f"Passenger data updated for {lift_name}")
        return passenger_data, number_people_picked
            
    def serve_stop(self, lift_name, passenger_data):
        """
        Process all actions for a lift at its current floor (pick up and drop passengers).

        Parameters:
        - lift_name: The name of the lift being served.
        - passenger_data: List of all passenger data in the simulation.

        Drops off passengers whose destination matches the current floor,
        then picks up eligible passengers. Returns updated passenger data,
        number of passengers picked, and number dropped at this stop.
        """
        
        logging.debug(f"Serving stop for {lift_name}")

        lift = self.lifts[lift_name]
        current_floor = lift["current_floor"]
        copy_list = lift["pending_orders"].copy()
        eligible_orders = []
        dropped = 0
        
        for order in copy_list:
            
            dont_pick = False
            direction = order[-1]
            logging.debug(f"Processing order: {order}")
            
            dropped += self.drop_passenger(order,lift_name)
            
            dont_pick = self.check_direction_conflict(order,copy_list,direction,lift_name)
            
            eligible_orders = self.Passengers_on_same_floor(order,dont_pick,eligible_orders,lift_name)
        
        passenger_data,number_picked = self.pick_passenger(eligible_orders,lift_name,passenger_data)
        logging.info(f"Stop served for {lift_name}: {number_picked} picked, {dropped} dropped")
        return passenger_data, number_picked, dropped

    def add_stop(self,order,lift_name):
        """
        Add a passenger order to a lift's queue if it aligns with the lift's current direction.

        Parameters:
        - order: The passenger order to be added.
        - lift_name: The name of the lift to process the order.

        Adds the order to the lift's pending orders if the passenger's direction
        matches the lift's current direction. If there is a conflict, the order
        is added to the 'orders_in_opposite_direction' list.
        """
        logging.debug(f"Adding stop for {lift_name}")
        lift = self.lifts[lift_name]
        current_floor = lift["current_floor"]
        direction = lift["direction"]
        
        if direction == 1 and order[-1] > 0 and current_floor <= order[1]:
            if order not in lift["pending_orders"]:
                lift["pending_orders"].append(order)
                lift["status"] = True
                    
        elif direction == -1 and (order[-1]) < 0 and current_floor >= order[1]:
            if order not in lift["pending_orders"]:
                lift["pending_orders"].append(order)
                lift["status"] = True

        else:
            if order not in self.orders_in_opposite_direction:

                self.orders_in_opposite_direction.append(order)
        logging.info(f"Stop added for {lift_name}")

    def queue_maker(self, pending_orders, passenger_data, lift_name):
        """
        Assign passenger orders to a lift's queue based on their floor and direction.

        Parameters:
        - pending_orders: List of passenger orders awaiting processing.
        - passenger_data: List of all passenger data in the simulation.
        - lift_name: The name of the lift to process the queue.

        Updates the lift's pending orders and direction, and removes processed orders
        from the passenger data. Handles cases where passengers need to travel
        in the opposite direction first (e.g., going up to come down).
        """
        logging.debug(f"Making queue for {lift_name}")
        going_up_to_come_down = False
        going_down_to_come_up = False
        
        lift = self.lifts[lift_name]
        current_floor = lift["current_floor"]
        lift_direction = lift["direction"]
        started = lift["status"]
        
        if pending_orders:
            for order in pending_orders:
                logging.debug(f"Processing order: {order}")
                logging.debug(f"removing orders: {order}")
                passenger_data.remove(order)
                '''the following helps to assign direction to the lift'''
                if order[1] > current_floor and not started:
                    lift_direction = 1
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
     
                elif order[1] < current_floor and not started:
                    lift_direction = -1
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
                             
                elif order[1] == current_floor and not started:
                    lift_direction = order[-1]
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
                             
                #checking if the person is calling the lift up to come down or calling it down to go up

                elif order[1] > current_floor and order[-1] < 0 and lift_direction == 1:
                    for j in pending_orders:
                        if j[-1] == -1 and j[1] > current_floor:
                        
                            if order not in lift["pending_orders"]:
                                lift["pending_orders"].append(order)
                    
                        elif j[-1] == 1 and j[1] == current_floor:
                            
                            if order not in lift["pending_orders"]:
                                lift["pending_orders"].append(order)
                            
                    going_up_to_come_down = True
                    
                elif order[1] < current_floor and order[-1] > 0 and lift_direction == -1:
                    for j in pending_orders:
                        if j[-1] == 1 and j[1] < current_floor:
                            if order not in lift["pending_orders"]:
                                lift["pending_orders"].append(order)
                            
                                     
                        elif j[-1] == 1 and j[1] == current_floor:
                            if order not in lift["pending_orders"]:
                                lift["pending_orders"].append(order)
                            
                                     
                    going_down_to_come_up = True
                    
                #All the pickup orders are over and the lift is moving up to drop someone but on the way some one wants to go down....so the lift goes up and comes down
                elif order[1] < current_floor and lift_direction > 0 and order[-1] < 0 and going_up_to_come_down:
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
                            
                             

                elif order[1] > current_floor and lift_direction < 0 and order[-1] > 0 and going_down_to_come_up:
                    
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
                            
                             
                            
                elif order[1] > current_floor and started and lift_direction==1:
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
                            
                elif order[1] < current_floor and started and lift_direction==-1:
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
                            
        
                elif order[1] == current_floor and started and lift_direction==order[-1]:
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
                            
                started = True

            going_up_to_come_down = False
            going_down_to_come_up = False
            
            for order in lift["pending_orders"]:
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
                        
        lift["direction"] = lift_direction
        lift["status"] = started
        logging.info(f"Queue made for {lift_name}")
        return passenger_data

    def calculate_lift_distances(self,passenger_floor):
        """
        Calculate the distance between each lift and a passenger's current floor.

        Parameters:
        - passenger_floor: The floor where the passenger is located.

        Returns:
        - A dictionary mapping lift names to their respective distances from the passenger.
        """
        logging.debug(f"Calculating lift distances for passenger at floor {passenger_floor}")
        return {
            lift_name: abs(lift["current_floor"] - passenger_floor)
            for lift_name, lift in self.lifts.items()
        }

    def get_nearest_lifts(self,distances):
        """
        Find the lifts closest to a given floor.

        Parameters:
        - distances: Dictionary of lifts and their distances to a floor.

        Returns:
        - A list of lifts that are at the minimum distance from the floor.
        """
        logging.debug(f"Finding nearest lifts.")
        min_distance = min(distances.values())
        return [lift for lift, distance in distances.items() if distance == min_distance]

    def is_lift_available(self,lift, direction, passenger_floor):
        """
        Check if a lift is available to serve a passenger.

        Parameters:
        - lift: The lift being evaluated.
        - direction: The direction the passenger wants to travel (1 for up, -1 for down).
        - passenger_floor: The floor where the passenger is located.

        Returns:
        - True if the lift is idle or moving in the passenger's direction.
        - False otherwise.
        """
        logging.debug(f"Checking lift availability for passenger at floor {passenger_floor}")
        return (
            not lift["status"] or
            (lift["direction"] == 0 or
            (lift["direction"] == direction and
            ((direction == 1 and passenger_floor >= lift["current_floor"]) or
            (direction == -1 and passenger_floor <= lift["current_floor"]))))
        )

    def assign_passenger_to_lift(self,lift_name, passenger):
        """
        Assign a passenger to a specific lift.

        Parameters:
        - lift_name: The name of the lift to assign the passenger.
        - passenger: The passenger order to assign.

        Updates the lift's pending orders and direction based on the passenger's
        destination. Ensures that the lift becomes active (status=True).
        """
        logging.debug(f"Assigning passenger {passenger} to {lift_name}")
        lift = self.lifts[lift_name]
        lift["pending_orders"].append(passenger)
        lift["status"] = True

        _, passenger_floor, _, _, _, _, direction = passenger
        if lift["direction"] == 0:
            lift["direction"] = (
                1 if passenger_floor > lift["current_floor"] else
                -1 if passenger_floor < lift["current_floor"] else
                direction
            )

    def handle_idle_lift(self,lift_name, passenger):
        """
        Assign a passenger to an idle lift and set its direction.

        Parameters:
        - lift_name: The name of the idle lift.
        - passenger: The passenger order to assign.

        Updates the lift's pending orders and direction based on the passenger's
        floor and destination.
        """
        logging.debug(f"Handling idle lift {lift_name}")
        lift = self.lifts[lift_name]
        _, passenger_floor, _, _, _, _, direction = passenger
        self.assign_passenger_to_lift(lift_name, passenger)
        lift["direction"] = (
            1 if passenger_floor > lift["current_floor"] else
            -1 if passenger_floor < lift["current_floor"] else
            direction
        )
    
    def handle_same_floor_passenger(self,passenger):
        """
        Assign a passenger to a lift if the lift is already on the passenger's floor 
        and moving in the desired direction.

        Parameters:
        - passenger: The passenger order to evaluate.

        Returns:
        - The name of the lift assigned to the passenger, or None if no suitable lift is found.

        Optimizes passenger pickup by utilizing lifts already in the correct position and direction.
        """
        logging.debug(f"Handling same-floor passenger: {passenger}")
        _, passenger_floor, _, _, _, _, direction = passenger

        for lift_name, lift in self.lifts.items():
            if (
                lift["current_floor"] == passenger_floor and  # Same floor
                lift["direction"] == direction and  # Same direction
                passenger not in lift["pending_orders"]  # Avoid duplicate assignment
            ):
                self.assign_passenger_to_lift(lift_name, passenger)
                return lift_name  # Return the lift assigned
        return None  # No same-floor lift available

    def assign_passengers(self, pending_orders):
        """
        Assign pending passenger orders to the most suitable lifts.

        Parameters:
        - pending_orders: List of all passenger orders waiting to be assigned.

        Attempts to assign passengers to the closest available lifts. If no lift
        is available, passengers remain unassigned. Returns a dictionary mapping
        lifts to their assigned orders.
        """
        logging.debug("Assigning passengers to lifts.")
        assignments = {lift_name: [] for lift_name in self.lifts}

        for passenger in pending_orders:
            _, passenger_floor, _, _, _, _, direction = passenger

            # Ensure passenger is not already assigned
            if passenger not in (
                sum(assignments.values(), []) + 
                [p for l in self.lifts.values() for p in l["pending_orders"]]
            ):
                # Step 1: Same-Floor Optimization
                same_floor_lift = self.handle_same_floor_passenger(passenger)
                if same_floor_lift:
                    assignments[same_floor_lift].append(passenger)
                    continue

                # Step 2: Find nearest lifts
                distances = self.calculate_lift_distances(passenger_floor)
                nearest_lifts = self.get_nearest_lifts(distances)

                # Step 3: Assign to the most suitable lift
                for lift_name in nearest_lifts:
                    if self.is_lift_available(self.lifts[lift_name], direction, passenger_floor):
                        self.assign_passenger_to_lift(lift_name, passenger)
                        assignments[lift_name].append(passenger)
                        break
                else:
                    # Step 4: Assign to an idle lift if no suitable lift found
                    idle_lifts = [lift_name for lift_name, lift in self.lifts.items() if not lift["status"]]
                    if idle_lifts:
                        self.handle_idle_lift(idle_lifts[0], passenger)
                        assignments[idle_lifts[0]].append(passenger)
                    # else:
                        # Step 5: Do not assign, leave in not_assigned list
                        # print(f"Passenger {passenger} not assigned to any lift.")
        '''There is another better way just remember'''

        return assignments
    
    def reassign_passenger(self, source_list):
        """
        Reassign passengers from one list (e.g., lift's pending orders or unassigned list) 
        to another lift based on proximity and direction.

        Parameters:
        - source_list: The list of passengers to reassign (can be a lift's pending orders 
        or the unassigned list).
        """

        logging.debug("Reassigning passengers to lifts.")
        passengers_in_lifts = [p for lift in self.lifts.values() for p in lift["passengers"]]
         
        # Step 1: Check if the source list is a lift's pending orders or the people_not_assigned list
        source_lift_name = None
        if any(source_list == lift["pending_orders"] for lift in self.lifts.values()):
            for lift_name, lift in self.lifts.items():
                if source_list == lift["pending_orders"]:
                    source_lift_name = lift_name
                    source_lift = self.lifts[source_lift_name]
                    break
        else:
            source_lift_name = "Not assigned list"

        
        # Step 2: Iterate over each passenger in the source list
        for person in source_list[:]:  # Use a copy of the list to avoid modification issues
            # Extract passenger details
            passenger_position = person[1]  # Current floor of the passenger
            passenger_direction = person[6]  # Desired direction of the passenger

            # Step 3: Search for a suitable target lift
            for target_lift_name, target_lift_data in self.lifts.items():
                # Check if the lift is at the passenger's floor and going in the same direction
                if (
                    target_lift_data["current_floor"] == passenger_position
                    and target_lift_data["direction"] == passenger_direction
                ):
                    # Move the passenger to the target lift's pending orders
                    if person not in target_lift_data["pending_orders"] and person not in passengers_in_lifts:
                        source_list.remove(person)
                        target_lift_data["pending_orders"].append(person)
                        print(
                            f"\n{person} reassigned from {source_lift_name} to {target_lift_name}\n"
                        )
                    break  # Stop searching once a suitable target lift is found
                elif source_lift_name != "Not assigned list":
                    # Check if the source lift has too many pending orders
                    if (
                        target_lift_data["status"] == False
                        and target_lift_data["direction"] == 0
                        and len(source_lift["pending_orders"]) >= 4
                    ):
                        for person in source_list[len(source_list) // 2 :]:
                            if person not in target_lift_data["pending_orders"] and person not in passengers_in_lifts:
                                source_list.remove(person)
                                target_lift_data["pending_orders"].append(person)
                                print(
                                    f"\n{person} reassigned from {source_lift_name} to {target_lift_name}\n"
                                )
                        break
                elif source_lift_name == "Not assigned list":
                    if (
                        target_lift_data["status"] == False
                        and target_lift_data["direction"] == 0
                    ):
                        for person in source_list[:]:
                            if person not in target_lift_data["pending_orders"] and person not in passengers_in_lifts:
                                source_list.remove(person)
                                target_lift_data["pending_orders"].append(person)
                                print(
                                    f"\n{person} reassigned from {source_lift_name} to {target_lift_name}\n"
                                )
                        break
                logging.info(f"Reassigned passengers from {source_lift_name} to {target_lift_name}.")
    
    def remove_duplicates(self, not_assigned):
        """
        Simulate the operation of the four-lift system.

        Parameters:
        - passenger_data: List of all passenger data in the simulation.

        The simulation progresses in time steps, processing actions for each lift:
        - Assigning passengers to lifts.
        - Picking up and dropping off passengers.
        - Moving lifts to the next floor.
        Handles unassigned passengers and prevents lift boundary errors.
        """
        logging.debug("Removing duplicates from lifts and unassigned list.")
        seen_passengers = set()
        
        # Remove duplicates from lifts' pending_orders
        for lift_name, lift in self.lifts.items():
            unique_orders = []
            for passenger in lift["pending_orders"]:
                if passenger not in seen_passengers:
                    seen_passengers.add(passenger)
                    unique_orders.append(passenger)
            lift["pending_orders"] = unique_orders
        
        # Remove duplicates from not_assigned
        unique_not_assigned = []
        for passenger in not_assigned:
            if passenger not in seen_passengers:
                seen_passengers.add(passenger)
                unique_not_assigned.append(passenger)
        logging.info("Duplicates removed.")
        return unique_not_assigned

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
    
    def run_simulation(self, passenger_data,output_filepath):
        """Simulate the operation of the four-lift system."""
        people_not_assigned = []
        dropped_by_lifts = {lift_name: 0 for lift_name in self.lifts}
        picked_by_lifts = {lift_name: 0 for lift_name in self.lifts}

        while self.threshold_density < self.current_density:
            logging.info(f"Running simulation at time: {self.current_time}")
            # Step 1: Update lift status
            for lift_name, lift in self.lifts.items():
                lift["status"] = bool(lift["pending_orders"])
                if not lift["status"]:
                    lift["direction"] = 0

            # Step 2: Filter passengers ready to be assigned
            logging.info("Filtering passengers ready to be assigned.")
            pending_orders = []
            pending_orders = [p for p in passenger_data if p[3] <= self.current_time]
            pending_orders = sorted(pending_orders, key=lambda x: x[3])

            
            # Step 3: Assign passengers to lifts
            logging.info("Assigning passengers to lifts.")
            lift_orders = self.assign_passengers(pending_orders)
            
            for lift_name, orders in lift_orders.items():
                sorted_orders = self.data_sorter(orders, lift_name)
                passenger_data = self.queue_maker(
                    pending_orders=sorted_orders, 
                    passenger_data=passenger_data, 
                    lift_name=lift_name
                )

            # Step 4: Collect unassigned passengers
            logging.info("Collecting unassigned passengers.")
            for person in passenger_data:
                if person in pending_orders and all(
                    person not in lift["pending_orders"] for lift in self.lifts.values()
                ) and person not in people_not_assigned:
                    people_not_assigned.append(person)

        
            
            # Step 5: Remove duplicates from lifts and unassigned list
            people_not_assigned = self.remove_duplicates(people_not_assigned)

            # Step 6: Reassign unassigned passengers
            for lift_name, lift in self.lifts.items():
                self.reassign_passenger(lift["pending_orders"])  # Check better lift assignment
            
            self.reassign_passenger(people_not_assigned)  # Try assigning unassigned passengers again
            
        
            # Step 7: Process lift actions (pick/drop passengers and move lifts)
            logging.info("Processing lift actions.")
            for lift_name, lift in self.lifts.items():
                if lift["pending_orders"]:
                    # Remove duplicates again as a safeguard
                    lift["pending_orders"] = list(dict.fromkeys(lift["pending_orders"]))
                    passenger_data = list(dict.fromkeys(passenger_data))

                    # Sort pending orders
                    lift["pending_orders"] = sorted(
                        lift["pending_orders"],
                        key=lambda x: abs(x[1] - lift["current_floor"]),
                        reverse=False if lift["direction"] < 0 else True,
                    )

                    # Serve passengers
                    passenger_data, picked_by_lifts[lift_name], dropped_by_lifts[lift_name] = self.serve_stop(
                        lift_name, passenger_data=passenger_data
                    )
                    print(f"{lift_name} pending order: {lift['pending_orders']}")
                    self.move(lift_name)
                    
            
            # Step 8: Update time based on actions
            logging.info("Updating simulation time.")
            self.current_time += (self.floor_time +sum(
                picked_by_lifts[lift_name] + dropped_by_lifts[lift_name] 
                for lift_name in self.lifts
            ) * self.passenger_inout)
            
            self.time_elapsed += self.floor_time
            if self.time_elapsed >= self.delta_time:
                desities = self.update_densities()
                self.current_density = np.mean(desities)
                self.time_elapsed = 0
                
            # Step 9: Error check for lift boundaries
            logging.info("Checking for lift boundaries")
            for lift_name, lift in self.lifts.items():
                if lift["current_floor"] > self.num_floors or lift["current_floor"] < 0:
                    print(f"Error in {lift_name}")
                    raise Exception("Lift out of bounds")
            
            print(f"Current time: {self.current_time}")

            for lift_name, lift in self.lifts.items():
                self.reassign_passenger(lift["pending_orders"])
                
            for person in people_not_assigned:
                if person not in [p for l in self.lifts.values() for p in l["pending_orders"]]:
                    people_not_assigned.remove(person)
                    
            self.reassign_passenger(people_not_assigned)
            
            people_not_assigned = self.remove_duplicates(people_not_assigned)
            
            for lift_name, lift in self.lifts.items():
                if lift["pending_orders"]:
                    # Remove duplicates again as a safeguard
                    lift["pending_orders"] = list(dict.fromkeys(lift["pending_orders"]))
                    passenger_data = list(dict.fromkeys(passenger_data))

                    # Sort pending orders
                    lift["pending_orders"] = sorted(
                        lift["pending_orders"],
                        key=lambda x: abs(x[1] - lift["current_floor"]),
                        reverse=False if lift["direction"] < 0 else True,
                    )

                    # Serve passengers
                    passenger_data, picked_by_lifts[lift_name], dropped_by_lifts[lift_name] = self.serve_stop(
                        lift_name, passenger_data=passenger_data
                    )
                    print(f"{lift_name} pending order: {lift['pending_orders']}")
        
                else:
                    lift["status"] = False
                    lift["direction"] = 0
            #giving second chance to the orders to be reassigned
            for lift_name, lift in self.lifts.items():
                if lift["population"]==0 and lift["pending_orders"] and not passenger_data:
                    for order in lift["pending_orders"][:]:
                        lift["pending_orders"].remove(order)
                        passenger_data.append(order)
            
            self.current_time += (+sum(
                picked_by_lifts[lift_name] + dropped_by_lifts[lift_name] 
                for lift_name in self.lifts
            ) * self.passenger_inout)
            print(f"current time 2: {self.current_time}")
            
            self.time_elapsed += self.floor_time
            if self.time_elapsed >= self.delta_time:
                desities = self.update_densities()
                self.current_density = np.mean(desities)
                self.time_elapsed = 0
        self.save_densities_to_file(output_filepath)
        return passenger_data

passenger_data = [(1, 0, 4, 0, 0, 0, 1), (2, 1, 0, 0, 0, 0, -1), (3, 2, 3, 0, 0, 0, 1), (4, 3, 1, 0, 0, 0, -1), (5, 4, 0, 0, 0, 0, -1), (6, 5, 2, 0, 0, 0, -1), (7, 3, 0, 4, 0, 0, -1), (8, 1, 2, 16, 0, 0, 1), (9, 5, 3, 21, 0, 0, -1)]
print(passenger_data)
# Simulation
dual_oscillation = NLiftSystem(
    current_floors=[0,0], 
    num_floors=5, 
    Passenger_limit=8,
    number_of_lifts=2,
    filepath="file_path", 
    threshold_density=0.01, 
    current_time=0.0, 
    current_density=[0.1]*6,
    delta_time=5
)

output_file = "density_snapshots.csv"
# output_file = "density_snapshots.csv"
remaining_passenger_data = dual_oscillation.run_simulation(passenger_data, output_filepath=output_file)

print("Simulation complete. Remaining passengers:")
print(remaining_passenger_data)

'''No errors as of now'''
