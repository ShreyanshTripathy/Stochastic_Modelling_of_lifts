import random         # Importing random library for random sampling
import sys
import logging

class FourLiftSystem:
    def __init__(self, current_floors, num_floors, filepath, passenger_limit, current_time=0):
        """
        Initialize the FourLiftSystem class.

        Parameters:
        - current_floors: List of initial floor positions for the 4 lifts.
        - num_floors: Total number of floors in the building.
        - filepath: Path to the CSV file containing passenger data.
        - passenger_limit: Maximum capacity of passengers for each lift.
        - current_time: Starting time for the simulation (default is 0).

        Creates the initial state for all lifts, including their current floor,
        direction, passengers, pending orders, and other attributes.
        """
        
        logging.basicConfig(level=logging.DEBUG, filename='Lift_debug.log', filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s')
        
        logging.info("Initializing the FourLiftSystem class.")
        
        self.num_floors = num_floors  # Total number of floors in the building
        self.filepath = filepath      # Filepath for passenger data CSV
        
        logging.debug(f"Reading passenger data from: {filepath}")
        # self.df_read = pd.read_csv(filepath)  # Load passenger data from CSV file

        
        self.current_time = current_time # Current simulation time
        self.passenger_limit = passenger_limit # Maximum passengers per lift

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
                for i in range(4)  # Repeat for each of the 4 lifts
            }
        logging.info(f"Lift states initialized: {self.lifts}")

        # Global state
        self.already_picked = []
        self.orders_done = []
        self.orders_not_served = []
        
        self.passenger_inout = 3
        self.floor_time = 1

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
        
        Index, passenger_position, passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = order
        
        lift = self.lifts[lift_name]
        current_floor = lift["current_floor"]
        lift_direction = lift["direction"]
        passengers = lift["passengers"]
        try:            
            # input("Co")
            logging.debug(f"Dropping passenger: {order}")
            if current_floor == passenger_destination and (order in self.already_picked) and order in passengers:
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
                # input("continue")
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
            sys.exit()
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
        logging.info(f"Direction conflict for {order}: {dont_pick} thus was not picked...the lift position is {current_floor} going {"up" if lift_direction==1 else "down"}.....its pending orders are {lift["pending_orders"]}")
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
            available_space = self.passenger_limit - lift_population
            # print(lift["passengers"])
            print(f"passenger limit: {self.passenger_limit}, lift population: {lift_population}")
            Orders_tobe_picked = []
            
            if len(eligible_orders) > available_space:
                # Pick only the number of passengers that can be accommodated
                print(f"available space: {available_space}")
                Orders_tobe_picked = random.sample(eligible_orders, available_space)
                for orders in eligible_orders:
                    if orders not in Orders_tobe_picked:#do something about the ordersnot picked
                        # Orders_not_picked.append(orders)#even if not picked the the passenger is in the pending_orders I dont need this i can just remove them from pewnding orders and put them back in the passenge data this means that then I need to change the passeger data
                        lift["pending_orders"].remove(orders)
                        passenger_data.append(orders)
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
                
                if lift["population"] == self.passenger_limit:
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
            if order[1]==current_floor:
                dont_pick = self.check_direction_conflict(order,copy_list,direction,lift_name)
                
                eligible_orders = self.Passengers_on_same_floor(order,dont_pick,eligible_orders,lift_name)
        
        passenger_data,number_picked = self.pick_passenger(eligible_orders,lift_name,passenger_data)
        logging.info(f"Stop served for {lift_name}: {number_picked} picked, {dropped} dropped")
        return passenger_data, number_picked, dropped

    
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
                Index, passenger_position, passenger_destination, Passenger_arrival_time, Lift_arrival_time, Order_completion_time, direction = order

                logging.debug(f"Processing order: {order}")
                logging.debug(f"removing orders: {order}")
                passenger_data.remove(order)
                '''the following helps to assign direction to the lift'''
                if passenger_position > current_floor and not started:
                    lift_direction = 1
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
     
                elif passenger_position < current_floor and not started:
                    lift_direction = -1
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
                             
                elif passenger_position == current_floor and not started:
                    lift_direction = direction
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
                             
                #checking if the person is calling the lift up to come down or calling it down to go up

                elif passenger_position > current_floor and direction < 0 and lift_direction == 1:
                    for j in pending_orders:
                        if j[-1] == -1 and j[1] > current_floor:
                        
                            if order not in lift["pending_orders"]:
                                lift["pending_orders"].append(order)
                    
                        elif j[-1] == 1 and j[1] == current_floor:
                            
                            if order not in lift["pending_orders"]:
                                lift["pending_orders"].append(order)
                            
                    going_up_to_come_down = True
                    
                elif passenger_position < current_floor and direction > 0 and lift_direction == -1:
                    for j in pending_orders:
                        if j[-1] == 1 and j[1] < current_floor:
                            if order not in lift["pending_orders"]:
                                lift["pending_orders"].append(order)
                            
                                     
                        elif j[-1] == 1 and j[1] == current_floor:
                            if order not in lift["pending_orders"]:
                                lift["pending_orders"].append(order)
                            
                                     
                    going_down_to_come_up = True
                    
                #All the pickup orders are over and the lift is moving up to drop someone but on the way some one wants to go down....so the lift goes up and comes down
                elif passenger_position < current_floor and lift_direction > 0 and direction < 0 and going_up_to_come_down:
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)

                elif passenger_position > current_floor and lift_direction < 0 and direction > 0 and going_down_to_come_up:
                    
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
                            
                             
                            
                elif passenger_position > current_floor and started and lift_direction==1:
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
                            
                elif passenger_position < current_floor and started and lift_direction==-1:
                    if order not in lift["pending_orders"]:
                        lift["pending_orders"].append(order)
                            
        
                elif passenger_position == current_floor and started and lift_direction==order[-1]:
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

    def is_lift_available(self, lift, direction, passenger_floor):
        logging.debug(f"Checking lift availability for passenger at floor {passenger_floor}")

        # Ensure there are pending orders before accessing the first element
        first_order_direction = lift["pending_orders"][0][-1] if lift["pending_orders"] else None
        
        return ((not lift["status"] or
                (lift["direction"] == direction and
                ((direction == 1 and passenger_floor >= lift["current_floor"]) or
                (direction == -1 and passenger_floor <= lift["current_floor"])) and 
                (first_order_direction == direction if first_order_direction is not None else True)#this part is for efficiency
                ))) and (len(lift["pending_orders"]) < self.passenger_limit)


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
        # input("sdfdg")
        
        if not lift["pending_orders"]:
            self.assign_passenger_to_lift(lift_name, passenger)
            
    
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
                (lift["direction"] == direction or lift["direction"]==0)and  # Same direction
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
            _, passenger_floor, passenger_destination, _, _, _, direction = passenger

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
        print("passengers in lift",passengers_in_lifts)
        
        # Identify if the source list belongs to a specific lift
        source_lift_name = None
        for lift_name, lift in self.lifts.items():
            if source_list == lift["pending_orders"]:
                source_lift_name = lift_name
                source_lift = lift
                break

        if source_lift_name is None:
            source_lift_name = "Not assigned list"

        # Create a copy of the source list to iterate
        to_remove = []
        for person in source_list:
            passenger_position = person[1]  # Current floor of the passenger
            passenger_direction = person[6]  # Desired direction of the passenger

            # Look for a suitable target lift
            for target_lift_name, target_lift_data in self.lifts.items():
                if (
                    target_lift_data["current_floor"] == passenger_position
                    and target_lift_data["direction"] == passenger_direction
                    and person not in target_lift_data["pending_orders"]
                    and person not in passengers_in_lifts
                ):
                    # Add to target lift
                    target_lift_data["pending_orders"].append(person)
                    to_remove.append(person)
                    print(f"\n{person} reassigned from {source_lift_name} to {target_lift_name}\n")
                    break
                elif source_lift_name != "Not assigned list":
                    if (
                        target_lift_data["status"] == False
                        and target_lift_data["direction"] == 0
                        and len(source_lift["pending_orders"]) >= 4
                    ):
                        # Handle load balancing
                        for p in source_list[len(source_list) // 2:]:
                            if p not in target_lift_data["pending_orders"] and p not in passengers_in_lifts:
                                target_lift_data["pending_orders"].append(p)
                                to_remove.append(p)
                        break
                elif source_lift_name == "Not assigned list":
                    if (
                        target_lift_data["status"] == False
                        and target_lift_data["direction"] == 0
                    ):
                        for p in source_list:
                            if p not in target_lift_data["pending_orders"] and p not in passengers_in_lifts:
                                target_lift_data["pending_orders"].append(p)
                                to_remove.append(p)
                        break

        # Remove all reassigned passengers from the source list in a separate step
        for person in to_remove:
            if person in source_list:
                source_list.remove(person)
        logging.info(f"Reassigned passengers from {source_lift_name}.")

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

    def run_simulation(self, passenger_data):
        """Simulate the operation of the four-lift system."""
        people_not_assigned = []
        dropped_by_lifts = {lift_name: 0 for lift_name in self.lifts}
        picked_by_lifts = {lift_name: 0 for lift_name in self.lifts}

        while passenger_data or any(lift["pending_orders"] for lift in self.lifts.values()):
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
            print(lift_orders)
            print(self.lifts)
            
            for lift_name, orders in lift_orders.items():
                sorted_orders = self.data_sorter(orders, lift_name)
                passenger_data = self.queue_maker(
                    pending_orders=sorted_orders, 
                    passenger_data=passenger_data, 
                    lift_name=lift_name
                )
            print(self.lifts)
            
            # Step 4: Collect unassigned passengers
            logging.info("Collecting unassigned passengers.")
            for person in pending_orders:
                if person in pending_orders and all(
                    person not in lift["pending_orders"] for lift in self.lifts.values()
                ) and person not in people_not_assigned:
                    people_not_assigned.append(person)
                    print("not assigned",people_not_assigned)

        
            
            # Step 5: Remove duplicates from lifts and unassigned list
            people_not_assigned = self.remove_duplicates(people_not_assigned)

            # Step 6: Reassign unassigned passengers
            for lift_name, lift in self.lifts.items():
                self.reassign_passenger(lift["pending_orders"])  # Check better lift assignment
            
            self.reassign_passenger(people_not_assigned)  # Try assigning unassigned passengers again
            
            pending_orders_update = [p for lift in self.lifts.values() for p in lift["pending_orders"]]
            
            for passenger in passenger_data:
                if passenger in pending_orders_update:
                    passenger_data.remove(passenger)
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
                else:
                    lift["status"] = False
                    lift["direction"] = 0
            
            # Step 8: Update time based on actions
            logging.info("Updating simulation time.")
            self.current_time += (self.floor_time +sum(
                picked_by_lifts[lift_name] + dropped_by_lifts[lift_name] 
                for lift_name in self.lifts
            ) * self.passenger_inout)
            

            # Step 9: Error check for lift boundaries
            logging.info("Checking for lift boundaries")
            for lift_name, lift in self.lifts.items():
                if lift["current_floor"] > self.num_floors or lift["current_floor"] < 0:
                    print(f"Error in {lift_name}")
                    raise Exception("Lift out of bounds")
            
            print(f"Current time: {self.current_time}")
            
            #giving second chance to the orders to be reassigned
            for lift_name, lift in self.lifts.items():
                if lift["population"]==0 and lift["pending_orders"] and not passenger_data:
                    for order in lift["pending_orders"][:]:
                        lift["pending_orders"].remove(order)
                        passenger_data.append(order)
            
            # self.current_time += (+sum(picked_by_lifts[lift_name] + dropped_by_lifts[lift_name] for lift_name in self.lifts) * self.passenger_inout)
            print(f"current time 2: {self.current_time}")
            if current_timestamp>=8000:
                input("continue")
    
   
# data = [(1, 0, 11, 0, 0, 0, 1), (2, 1, 20, 0, 0, 0, 1), (3, 2, 20, 0, 0, 0, 1), (4, 3, 0, 0, 0, 0, -1), (5, 4, 0, 0, 0, 0, -1), (6, 5, 19, 0, 0, 0, 1), (7, 6, 20, 0, 0, 0, 1), (8, 7, 0, 0, 0, 0, -1), (9, 8, 18, 0, 0, 0, 1), (10, 9, 10, 0, 0, 0, 1), (11, 10, 1, 0, 0, 0, -1), (12, 11, 20, 0, 0, 0, 1), (13, 12, 7, 0, 0, 0, -1), (14, 13, 11, 0, 0, 0, -1), (15, 14, 17, 0, 0, 0, 1), (16, 15, 10, 0, 0, 0, -1), (17, 16, 9, 0, 0, 0, -1), (18, 17, 12, 0, 0, 0, -1), (19, 18, 2, 0, 0, 0, -1), (20, 19, 6, 0, 0, 0, -1), (21, 20, 1, 0, 0, 0, -1), (22, 8, 7, 4087, 0, 0, -1)]
data = [(1, 0, 3, 0, 0, 0, 1), (2, 1, 22, 0, 0, 0, 1), (3, 2, 14, 0, 0, 0, 1), (4, 3, 17, 0, 0, 0, 1), (5, 4, 21, 0, 0, 0, 1), (6, 5, 14, 0, 0, 0, 1), (7, 6, 14, 0, 0, 0, 1), (8, 7, 36, 0, 0, 0, 1), (9, 8, 11, 0, 0, 0, 1), (10, 9, 39, 0, 0, 0, 1), (11, 10, 31, 0, 0, 0, 1), (12, 11, 28, 0, 0, 0, 1), (13, 12, 1, 0, 0, 0, -1), (14, 13, 14, 0, 0, 0, 1), (15, 14, 37, 0, 0, 0, 1), (16, 15, 40, 0, 0, 0, 1), (17, 16, 19, 0, 0, 0, 1), (18, 17, 35, 0, 0, 0, 1), (19, 18, 36, 0, 0, 0, 1), (30, 29, 13, 0, 0, 0, -1), (31, 30, 26, 0, 0, 0, -1), (32, 31, 6, 0, 0, 0, -1), (33, 32, 28, 0, 0, 0, -1), (34, 33, 38, 0, 0, 0, 1), (35, 34, 5, 0, 0, 0, -1), (20, 19, 30, 0, 0, 0, 1), (22, 21, 10, 0, 0, 0, -1), (21, 20, 8, 0, 0, 0, -1), (25, 24, 15, 0, 0, 0, -1), (24, 23, 31, 0, 0, 0, 1), (26, 25, 1, 0, 0, 0, -1), (23, 22, 12, 0, 0, 0, -1), (27, 26, 32, 0, 0, 0, 1), (28, 27, 6, 0, 0, 0, -1), (29, 28, 34, 0, 0, 0, 1), (41, 40, 27, 0, 0, 0, -1), (38, 37, 20, 0, 0, 0, -1), (37, 36, 3, 0, 0, 0, -1), (36, 35, 24, 0, 0, 0, -1), (39, 38, 16, 0, 0, 0, -1), (40, 39, 40, 0, 0, 0, 1), (42, 35, 27, 1, 0, 0, -1), (43, 39, 29, 14, 0, 0, -1), (44, 19, 2, 28, 0, 0, -1), (45, 39, 38, 37, 0, 0, -1), (46, 2, 6, 38, 0, 0, 1), (47, 12, 34, 40, 0, 0, 1), (48, 31, 22, 42, 0, 0, -1), (49, 9, 22, 45, 0, 0, 1), (50, 19, 33, 45, 0, 0, 1), (51, 34, 27, 48, 0, 0, -1), (52, 3, 15, 66, 0, 0, 1), (53, 27, 31, 67, 0, 0, 1), (54, 10, 23, 75, 0, 0, 1), (55, 37, 35, 79, 0, 0, -1), (56, 2, 37, 81, 0, 0, 1), (57, 33, 2, 82, 0, 0, -1), (58, 22, 18, 91, 0, 0, -1), (59, 21, 11, 93, 0, 0, -1), (60, 35, 21, 97, 0, 0, -1), (61, 13, 31, 99, 0, 0, 1), (62, 25, 4, 102, 0, 0, -1), (63, 32, 8, 104, 0, 0, -1), (64, 31, 37, 106, 0, 0, 1), (65, 3, 17, 111, 0, 0, 1), (66, 10, 6, 116, 0, 0, -1), (67, 12, 2, 118, 0, 0, -1), (68, 2, 16, 124, 0, 0, 1), (69, 23, 19, 124, 0, 0, -1), (70, 34, 15, 125, 0, 0, -1), (71, 6, 26, 131, 0, 0, 1), (72, 25, 20, 140, 0, 0, -1), (73, 36, 3, 142, 0, 0, -1), (74, 21, 39, 145, 0, 0, 1), (75, 34, 30, 146, 0, 0, -1), (76, 0, 34, 156, 0, 0, 1), (77, 16, 24, 175, 0, 0, 1), (78, 16, 8, 176, 0, 0, -1), (79, 22, 5, 195, 0, 0, -1), (80, 36, 24, 198, 0, 0, -1), (81, 29, 37, 201, 0, 0, 1), (82, 12, 4, 202, 0, 0, -1), (83, 8, 34, 208, 0, 0, 1), (84, 40, 27, 213, 0, 0, -1), (85, 26, 36, 214, 0, 0, 1), (86, 11, 25, 219, 0, 0, 1), (87, 23, 4, 219, 0, 0, -1), (88, 24, 39, 222, 0, 0, 1), (89, 28, 13, 228, 0, 0, -1), (90, 12, 13, 231, 0, 0, 1), (92, 37, 28, 232, 0, 0, -1), (91, 14, 18, 232, 0, 0, 1), (93, 19, 8, 235, 0, 0, -1), (94, 2, 36, 244, 0, 0, 1), (95, 40, 19, 253, 0, 0, -1), (96, 15, 17, 258, 0, 0, 1), (97, 22, 40, 261, 0, 0, 1), (98, 18, 35, 263, 0, 0, 1), (99, 25, 23, 264, 0, 0, -1), (100, 30, 6, 269, 0, 0, -1), (101, 26, 27, 273, 0, 0, 1), (102, 19, 8, 279, 0, 0, -1), (103, 30, 29, 283, 0, 0, -1), (104, 21, 24, 288, 0, 0, 1), (105, 8, 4, 291, 0, 0, -1), (106, 25, 24, 296, 0, 0, -1), (107, 13, 17, 307, 0, 0, 1), (108, 2, 16, 312, 0, 0, 1), (109, 32, 31, 315, 0, 0, -1), (110, 3, 38, 329, 0, 0, 1), (111, 27, 38, 330, 0, 0, 1), (112, 31, 28, 336, 0, 0, -1), (113, 15, 22, 338, 0, 0, 1), (114, 10, 32, 342, 0, 0, 1), (115, 9, 16, 347, 0, 0, 1), (116, 17, 37, 382, 0, 0, 1), (117, 7, 13, 383, 0, 0, 1), (118, 7, 37, 389, 0, 0, 1), (119, 23, 29, 390, 0, 0, 1), (120, 14, 15, 394, 0, 0, 1), (121, 3, 8, 396, 0, 0, 1), (122, 25, 20, 403, 0, 0, -1), (123, 7, 3, 412, 0, 0, -1), (124, 33, 14, 421, 0, 0, -1), (125, 3, 8, 427, 0, 0, 1), (126, 10, 1, 428, 0, 0, -1), (127, 11, 22, 428, 0, 0, 1), (128, 37, 18, 438, 0, 0, -1), (129, 13, 32, 447, 0, 0, 1), (130, 20, 39, 447, 0, 0, 1), (131, 37, 21, 449, 0, 0, -1), (132, 33, 40, 451, 0, 0, 1), (133, 31, 28, 456, 0, 0, -1), (134, 22, 11, 457, 0, 0, -1), (135, 37, 5, 460, 0, 0, -1), (136, 36, 15, 463, 0, 0, -1), (137, 7, 8, 467, 0, 0, 1), (138, 36, 5, 467, 0, 0, -1), (139, 35, 7, 470, 0, 0, -1), (140, 34, 0, 471, 0, 0, -1), (141, 28, 31, 473, 0, 0, 1), (142, 5, 34, 474, 0, 0, 1), (143, 39, 24, 477, 0, 0, -1), (144, 31, 23, 481, 0, 0, -1), (145, 37, 16, 481, 0, 0, -1), (146, 36, 35, 483, 0, 0, -1), (147, 10, 11, 487, 0, 0, 1), (148, 39, 25, 488, 0, 0, -1), (149, 1, 28, 502, 0, 0, 1), (150, 25, 6, 502, 0, 0, -1), (151, 23, 0, 507, 0, 0, -1), (152, 8, 37, 508, 0, 0, 1), (153, 23, 35, 512, 0, 0, 1), (154, 28, 19, 520, 0, 0, -1), (155, 19, 31, 521, 0, 0, 1), (156, 39, 20, 521, 0, 0, -1), (157, 10, 15, 527, 0, 0, 1), (158, 25, 11, 530, 0, 0, -1), (159, 21, 19, 533, 0, 0, -1), (160, 40, 38, 536, 0, 0, -1), (161, 6, 38, 540, 0, 0, 1), (162, 1, 23, 546, 0, 0, 1), (163, 37, 40, 549, 0, 0, 1), (164, 29, 23, 558, 0, 0, -1), (165, 20, 40, 563, 0, 0, 1), (166, 31, 29, 573, 0, 0, -1), (167, 25, 38, 579, 0, 0, 1), (168, 34, 38, 580, 0, 0, 1), (169, 22, 21, 584, 0, 0, -1), (170, 23, 8, 595, 0, 0, -1), (171, 0, 37, 596, 0, 0, 1), (172, 4, 2, 602, 0, 0, -1), (173, 27, 7, 603, 0, 0, -1), (174, 32, 6, 624, 0, 0, -1), (176, 38, 25, 626, 0, 0, -1), (175, 7, 11, 626, 0, 0, 1), (177, 20, 10, 634, 0, 0, -1), (178, 10, 17, 635, 0, 0, 1), (179, 39, 12, 656, 0, 0, -1), (180, 0, 9, 657, 0, 0, 1), (181, 1, 20, 664, 0, 0, 1), (182, 26, 7, 674, 0, 0, -1), (183, 34, 23, 678, 0, 0, -1), (184, 19, 8, 685, 0, 0, -1), (185, 17, 9, 687, 0, 0, -1), (186, 32, 40, 689, 0, 0, 1), (187, 5, 8, 694, 0, 0, 1), (188, 37, 4, 695, 0, 0, -1), (189, 28, 29, 700, 0, 0, 1), (190, 21, 23, 703, 0, 0, 1), (191, 36, 11, 711, 0, 0, -1), (192, 30, 37, 713, 0, 0, 1), (193, 24, 4, 714, 0, 0, -1), (194, 38, 14, 722, 0, 0, -1), (195, 5, 28, 726, 0, 0, 1), (196, 35, 17, 731, 0, 0, -1), (197, 12, 31, 733, 0, 0, 1), (198, 25, 21, 738, 0, 0, -1), (199, 9, 23, 742, 0, 0, 1), (200, 0, 4, 744, 0, 0, 1), (201, 25, 0, 746, 0, 0, -1), (202, 30, 4, 751, 0, 0, -1), (203, 11, 13, 763, 0, 0, 1), (204, 35, 30, 764, 0, 0, -1), (205, 12, 23, 776, 0, 0, 1), (206, 22, 40, 778, 0, 0, 1), (207, 27, 39, 780, 0, 0, 1), (208, 39, 17, 783, 0, 0, -1), (209, 20, 29, 784, 0, 0, 1), (211, 38, 2, 785, 0, 0, -1), (210, 1, 35, 785, 0, 0, 1), (212, 17, 3, 786, 0, 0, -1), (213, 14, 17, 789, 0, 0, 1), (214, 38, 3, 789, 0, 0, -1), (215, 27, 26, 790, 0, 0, -1), (216, 27, 12, 792, 0, 0, -1), (217, 34, 24, 796, 0, 0, -1), (218, 10, 14, 802, 0, 0, 1), (219, 10, 32, 806, 0, 0, 1), (220, 11, 4, 806, 0, 0, -1), (221, 0, 40, 809, 0, 0, 1), (222, 0, 26, 811, 0, 0, 1), (223, 5, 17, 816, 0, 0, 1), (224, 3, 36, 821, 0, 0, 1), (225, 39, 31, 832, 0, 0, -1), (226, 13, 39, 838, 0, 0, 1), (227, 38, 7, 842, 0, 0, -1), (228, 25, 37, 844, 0, 0, 1), (229, 26, 0, 853, 0, 0, -1), (230, 24, 3, 855, 0, 0, -1), (231, 18, 5, 856, 0, 0, -1), (232, 19, 15, 857, 0, 0, -1), (233, 37, 0, 860, 0, 0, -1), (234, 31, 38, 863, 0, 0, 1), (235, 15, 34, 879, 0, 0, 1), (236, 18, 12, 886, 0, 0, -1), (237, 15, 17, 887, 0, 0, 1), (238, 37, 33, 891, 0, 0, -1), (239, 34, 9, 896, 0, 0, -1), (240, 37, 15, 898, 0, 0, -1), (241, 40, 15, 900, 0, 0, -1), (242, 34, 37, 903, 0, 0, 1), (243, 39, 14, 903, 0, 0, -1), (244, 17, 27, 909, 0, 0, 1), (245, 27, 25, 923, 0, 0, -1), (246, 19, 12, 942, 0, 0, -1), (247, 23, 3, 942, 0, 0, -1), (248, 20, 11, 952, 0, 0, -1), (249, 10, 1, 953, 0, 0, -1), (250, 4, 5, 954, 0, 0, 1), (251, 13, 19, 958, 0, 0, 1), (252, 4, 21, 963, 0, 0, 1), (253, 12, 15, 963, 0, 0, 1), (254, 11, 35, 977, 0, 0, 1), (256, 38, 3, 977, 0, 0, -1), (255, 16, 14, 977, 0, 0, -1), (257, 9, 17, 978, 0, 0, 1), (258, 5, 35, 980, 0, 0, 1), (259, 2, 36, 982, 0, 0, 1), (260, 30, 18, 989, 0, 0, -1), (261, 4, 1, 997, 0, 0, -1), (262, 16, 11, 998, 0, 0, -1), (263, 20, 27, 1010, 0, 0, 1), (264, 21, 3, 1012, 0, 0, -1), (265, 30, 18, 1020, 0, 0, -1), (266, 25, 36, 1023, 0, 0, 1), (267, 36, 37, 1034, 0, 0, 1), (268, 20, 25, 1059, 0, 0, 1), (269, 15, 8, 1066, 0, 0, -1), (270, 29, 21, 1084, 0, 0, -1), (271, 38, 3, 1084, 0, 0, -1), (272, 1, 12, 1088, 0, 0, 1), (273, 22, 19, 1112, 0, 0, -1), (274, 24, 11, 1115, 0, 0, -1), (275, 37, 29, 1116, 0, 0, -1), (277, 39, 24, 1128, 0, 0, -1), (276, 25, 17, 1128, 0, 0, -1), (278, 29, 8, 1132, 0, 0, -1), (279, 5, 10, 1135, 0, 0, 1), (280, 40, 5, 1136, 0, 0, -1), (281, 15, 0, 1143, 0, 0, -1), (282, 9, 2, 1145, 0, 0, -1), (283, 34, 39, 1157, 0, 0, 1), (284, 29, 15, 1158, 0, 0, -1), (285, 34, 23, 1159, 0, 0, -1), (286, 33, 11, 1161, 0, 0, -1), (287, 31, 3, 1162, 0, 0, -1), (288, 32, 34, 1167, 0, 0, 1), (289, 24, 36, 1168, 0, 0, 1), (290, 16, 23, 1169, 0, 0, 1), (291, 0, 18, 1170, 0, 0, 1), (292, 25, 1, 1172, 0, 0, -1), (293, 0, 12, 1173, 0, 0, 1), (294, 31, 29, 1179, 0, 0, -1), (295, 24, 18, 1183, 0, 0, -1), (296, 13, 33, 1185, 0, 0, 1), (297, 30, 1, 1192, 0, 0, -1), (298, 4, 32, 1193, 0, 0, 1), (299, 26, 13, 1203, 0, 0, -1), (300, 3, 12, 1206, 0, 0, 1), (301, 22, 40, 1206, 0, 0, 1), (302, 23, 4, 1208, 0, 0, -1), (303, 9, 27, 1211, 0, 0, 1), (304, 35, 30, 1212, 0, 0, -1), (305, 8, 20, 1214, 0, 0, 1), (306, 15, 4, 1215, 0, 0, -1), (307, 25, 13, 1220, 0, 0, -1), (308, 27, 1, 1224, 0, 0, -1), (309, 13, 10, 1227, 0, 0, -1), (310, 39, 20, 1235, 0, 0, -1), (311, 28, 0, 1238, 0, 0, -1), (312, 37, 15, 1238, 0, 0, -1), (313, 0, 34, 1248, 0, 0, 1), (314, 31, 10, 1248, 0, 0, -1), (315, 31, 16, 1252, 0, 0, -1), (316, 38, 15, 1257, 0, 0, -1), (317, 10, 27, 1258, 0, 0, 1), (318, 16, 6, 1258, 0, 0, -1), (319, 5, 34, 1270, 0, 0, 1), (320, 0, 22, 1276, 0, 0, 1), (321, 26, 4, 1279, 0, 0, -1), (322, 0, 13, 1281, 0, 0, 1), (323, 12, 33, 1292, 0, 0, 1), (325, 23, 14, 1294, 0, 0, -1), (326, 40, 8, 1294, 0, 0, -1), (324, 5, 36, 1294, 0, 0, 1), (327, 37, 35, 1298, 0, 0, -1), (328, 6, 0, 1307, 0, 0, -1), (329, 1, 9, 1308, 0, 0, 1), (330, 6, 18, 1308, 0, 0, 1), (331, 18, 28, 1310, 0, 0, 1), (332, 32, 40, 1310, 0, 0, 1), (333, 26, 9, 1321, 0, 0, -1), (335, 35, 28, 1328, 0, 0, -1), (334, 13, 14, 1328, 0, 0, 1), (336, 2, 3, 1336, 0, 0, 1), (337, 3, 1, 1338, 0, 0, -1), (338, 7, 11, 1338, 0, 0, 1), (339, 28, 25, 1340, 0, 0, -1), (340, 12, 21, 1345, 0, 0, 1), (341, 26, 33, 1345, 0, 0, 1), (342, 25, 34, 1347, 0, 0, 1), (343, 21, 40, 1349, 0, 0, 1), (344, 35, 29, 1352, 0, 0, -1), (347, 14, 15, 1363, 0, 0, 1), (346, 12, 37, 1363, 0, 0, 1), (345, 3, 14, 1363, 0, 0, 1), (348, 23, 31, 1365, 0, 0, 1), (349, 4, 1, 1374, 0, 0, -1), (350, 8, 24, 1375, 0, 0, 1), (351, 28, 37, 1378, 0, 0, 1), (352, 33, 18, 1390, 0, 0, -1), (353, 8, 3, 1396, 0, 0, -1), (354, 26, 11, 1400, 0, 0, -1), (355, 35, 14, 1404, 0, 0, -1), (356, 32, 3, 1407, 0, 0, -1), (357, 4, 0, 1418, 0, 0, -1), (358, 32, 28, 1418, 0, 0, -1), (359, 31, 17, 1422, 0, 0, -1), (360, 2, 38, 1444, 0, 0, 1), (361, 4, 31, 1452, 0, 0, 1), (362, 11, 4, 1453, 0, 0, -1), (363, 13, 30, 1459, 0, 0, 1), (364, 15, 6, 1466, 0, 0, -1), (365, 13, 23, 1477, 0, 0, 1), (367, 27, 31, 1510, 0, 0, 1), (366, 18, 7, 1510, 0, 0, -1), (368, 20, 5, 1511, 0, 0, -1), (369, 40, 35, 1511, 0, 0, -1), (370, 21, 30, 1514, 0, 0, 1), (371, 34, 8, 1519, 0, 0, -1), (372, 12, 34, 1525, 0, 0, 1), (373, 35, 2, 1527, 0, 0, -1), (374, 9, 14, 1529, 0, 0, 1), (375, 33, 13, 1536, 0, 0, -1), (376, 6, 18, 1542, 0, 0, 1), (377, 25, 36, 1543, 0, 0, 1), (378, 7, 15, 1558, 0, 0, 1), (379, 3, 26, 1559, 0, 0, 1), (380, 8, 18, 1559, 0, 0, 1), (381, 10, 24, 1560, 0, 0, 1), (382, 7, 20, 1563, 0, 0, 1), (383, 27, 8, 1563, 0, 0, -1), (384, 13, 14, 1569, 0, 0, 1), (385, 14, 36, 1569, 0, 0, 1), (386, 13, 0, 1574, 0, 0, -1), (387, 34, 37, 1582, 0, 0, 1), (388, 10, 16, 1586, 0, 0, 1), (389, 13, 0, 1589, 0, 0, -1), (390, 21, 13, 1592, 0, 0, -1), (391, 15, 33, 1593, 0, 0, 1), (392, 9, 15, 1594, 0, 0, 1), (393, 29, 3, 1599, 0, 0, -1), (394, 31, 40, 1600, 0, 0, 1), (395, 22, 28, 1604, 0, 0, 1), (396, 20, 27, 1605, 0, 0, 1), (397, 5, 40, 1606, 0, 0, 1), (398, 14, 28, 1609, 0, 0, 1), (399, 24, 10, 1613, 0, 0, -1), (400, 12, 19, 1616, 0, 0, 1), (401, 14, 34, 1619, 0, 0, 1), (402, 39, 5, 1629, 0, 0, -1), (403, 31, 6, 1636, 0, 0, -1), (404, 19, 3, 1644, 0, 0, -1), (405, 38, 34, 1653, 0, 0, -1), (406, 24, 16, 1662, 0, 0, -1), (407, 12, 25, 1664, 0, 0, 1), (408, 38, 40, 1668, 0, 0, 1), (409, 37, 14, 1675, 0, 0, -1), (410, 36, 15, 1677, 0, 0, -1), (411, 10, 30, 1684, 0, 0, 1), (412, 12, 9, 1684, 0, 0, -1), (413, 14, 39, 1686, 0, 0, 1), (414, 2, 6, 1689, 0, 0, 1), (415, 6, 31, 1691, 0, 0, 1), (416, 16, 35, 1691, 0, 0, 1), (417, 20, 1, 1697, 0, 0, -1), (418, 32, 11, 1700, 0, 0, -1), (419, 16, 11, 1702, 0, 0, -1), (420, 0, 30, 1707, 0, 0, 1), (421, 15, 12, 1714, 0, 0, -1), (423, 35, 11, 1717, 0, 0, -1), (422, 1, 13, 1717, 0, 0, 1), (424, 11, 40, 1720, 0, 0, 1), (425, 29, 15, 1729, 0, 0, -1), (426, 38, 17, 1731, 0, 0, -1), (427, 34, 24, 1742, 0, 0, -1), (428, 31, 30, 1744, 0, 0, -1), (429, 16, 27, 1746, 0, 0, 1), (430, 21, 27, 1748, 0, 0, 1), (431, 2, 5, 1749, 0, 0, 1), (432, 15, 34, 1749, 0, 0, 1), (433, 25, 23, 1755, 0, 0, -1), (434, 38, 12, 1767, 0, 0, -1), (435, 4, 20, 1773, 0, 0, 1), (436, 18, 29, 1775, 0, 0, 1), (437, 38, 5, 1785, 0, 0, -1), (438, 28, 8, 1789, 0, 0, -1), (439, 15, 21, 1795, 0, 0, 1), (440, 23, 5, 1797, 0, 0, -1), (441, 11, 27, 1818, 0, 0, 1), (442, 8, 13, 1825, 0, 0, 1), (443, 36, 23, 1832, 0, 0, -1), (444, 12, 29, 1842, 0, 0, 1), (445, 17, 40, 1854, 0, 0, 1), (446, 10, 20, 1860, 0, 0, 1), (447, 7, 34, 1862, 0, 0, 1), (448, 22, 12, 1869, 0, 0, -1), (449, 28, 29, 1870, 0, 0, 1), (450, 32, 15, 1879, 0, 0, -1), (451, 32, 8, 1880, 0, 0, -1), (452, 1, 10, 1886, 0, 0, 1), (453, 0, 12, 1902, 0, 0, 1), (454, 32, 27, 1904, 0, 0, -1), (455, 30, 3, 1906, 0, 0, -1), (456, 39, 3, 1906, 0, 0, -1), (457, 6, 8, 1913, 0, 0, 1), (458, 20, 36, 1917, 0, 0, 1), (459, 16, 27, 1919, 0, 0, 1), (460, 37, 25, 1919, 0, 0, -1), (461, 4, 12, 1924, 0, 0, 1), (463, 36, 32, 1926, 0, 0, -1), (462, 7, 9, 1926, 0, 0, 1), (464, 8, 14, 1933, 0, 0, 1), (465, 1, 40, 1938, 0, 0, 1), (466, 5, 17, 1938, 0, 0, 1), (467, 26, 27, 1940, 0, 0, 1), (468, 36, 28, 1943, 0, 0, -1), (469, 13, 2, 1947, 0, 0, -1), (470, 40, 7, 1947, 0, 0, -1), (471, 24, 35, 1952, 0, 0, 1), (472, 28, 22, 1952, 0, 0, -1), (473, 1, 31, 1955, 0, 0, 1), (474, 21, 20, 1957, 0, 0, -1), (475, 32, 15, 1965, 0, 0, -1), (476, 18, 37, 1970, 0, 0, 1), (477, 5, 0, 1973, 0, 0, -1), (478, 1, 38, 1976, 0, 0, 1), (479, 36, 37, 1980, 0, 0, 1), (480, 20, 24, 1981, 0, 0, 1), (481, 33, 35, 1984, 0, 0, 1), (482, 30, 40, 1985, 0, 0, 1), (485, 23, 35, 1987, 0, 0, 1), (483, 5, 6, 1987, 0, 0, 1), (484, 11, 7, 1987, 0, 0, -1), (486, 22, 5, 1989, 0, 0, -1), (487, 25, 27, 1993, 0, 0, 1), (488, 0, 28, 1997, 0, 0, 1), (489, 32, 40, 2003, 0, 0, 1), (490, 4, 8, 2021, 0, 0, 1), (491, 32, 22, 2022, 0, 0, -1), (492, 15, 33, 2031, 0, 0, 1), (493, 29, 26, 2037, 0, 0, -1), (494, 1, 6, 2042, 0, 0, 1), (495, 11, 30, 2050, 0, 0, 1), (496, 29, 39, 2051, 0, 0, 1), (497, 24, 15, 2069, 0, 0, -1), (498, 20, 30, 2070, 0, 0, 1), (499, 22, 6, 2071, 0, 0, -1), (500, 28, 1, 2071, 0, 0, -1), (501, 22, 32, 2080, 0, 0, 1), (502, 22, 16, 2089, 0, 0, -1), (503, 40, 3, 2092, 0, 0, -1), (504, 39, 1, 2106, 0, 0, -1), (505, 6, 22, 2109, 0, 0, 1), (506, 22, 14, 2115, 0, 0, -1), (507, 31, 16, 2127, 0, 0, -1), (508, 0, 13, 2136, 0, 0, 1), (509, 40, 29, 2155, 0, 0, -1), (510, 19, 8, 2159, 0, 0, -1), (511, 24, 29, 2171, 0, 0, 1), (512, 22, 27, 2174, 0, 0, 1), (513, 36, 23, 2181, 0, 0, -1), (514, 12, 13, 2182, 0, 0, 1), (515, 9, 40, 2188, 0, 0, 1), (516, 20, 23, 2188, 0, 0, 1), (517, 19, 32, 2194, 0, 0, 1), (518, 3, 39, 2198, 0, 0, 1), (519, 35, 23, 2199, 0, 0, -1), (520, 13, 11, 2204, 0, 0, -1), (521, 0, 33, 2207, 0, 0, 1), (522, 35, 14, 2213, 0, 0, -1), (523, 4, 38, 2215, 0, 0, 1), (524, 28, 29, 2224, 0, 0, 1), (525, 10, 13, 2228, 0, 0, 1), (526, 39, 33, 2229, 0, 0, -1), (527, 31, 28, 2237, 0, 0, -1), (528, 14, 0, 2238, 0, 0, -1), (529, 22, 13, 2239, 0, 0, -1), (530, 38, 5, 2247, 0, 0, -1), (531, 3, 20, 2251, 0, 0, 1), (532, 16, 9, 2252, 0, 0, -1), (533, 10, 29, 2253, 0, 0, 1), (534, 28, 22, 2258, 0, 0, -1), (535, 35, 33, 2259, 0, 0, -1), (536, 34, 16, 2264, 0, 0, -1), (537, 30, 5, 2266, 0, 0, -1), (538, 40, 23, 2269, 0, 0, -1), (539, 34, 36, 2276, 0, 0, 1), (540, 37, 5, 2276, 0, 0, -1), (541, 14, 17, 2280, 0, 0, 1), (542, 1, 38, 2282, 0, 0, 1), (543, 10, 39, 2283, 0, 0, 1), (544, 17, 1, 2291, 0, 0, -1), (546, 35, 10, 2292, 0, 0, -1), (545, 27, 2, 2292, 0, 0, -1), (548, 33, 21, 2297, 0, 0, -1), (547, 13, 28, 2297, 0, 0, 1), (549, 23, 4, 2313, 0, 0, -1), (550, 39, 5, 2324, 0, 0, -1), (551, 35, 10, 2341, 0, 0, -1), (552, 18, 30, 2342, 0, 0, 1), (553, 37, 6, 2344, 0, 0, -1), (554, 17, 1, 2349, 0, 0, -1), (555, 40, 6, 2361, 0, 0, -1), (556, 21, 7, 2366, 0, 0, -1), (557, 1, 26, 2367, 0, 0, 1), (558, 33, 26, 2371, 0, 0, -1), (559, 24, 40, 2373, 0, 0, 1), (560, 23, 31, 2374, 0, 0, 1), (561, 38, 28, 2375, 0, 0, -1), (562, 32, 11, 2383, 0, 0, -1), (563, 26, 16, 2384, 0, 0, -1), (564, 40, 31, 2386, 0, 0, -1), (566, 28, 14, 2388, 0, 0, -1), (565, 14, 27, 2388, 0, 0, 1), (567, 20, 3, 2394, 0, 0, -1), (568, 15, 28, 2396, 0, 0, 1), (570, 28, 4, 2399, 0, 0, -1), (569, 5, 38, 2399, 0, 0, 1), (571, 35, 21, 2401, 0, 0, -1), (572, 1, 6, 2402, 0, 0, 1), (573, 40, 17, 2404, 0, 0, -1), (574, 21, 23, 2407, 0, 0, 1), (575, 4, 34, 2410, 0, 0, 1), (576, 15, 4, 2410, 0, 0, -1), (577, 0, 23, 2421, 0, 0, 1), (578, 1, 30, 2422, 0, 0, 1), (579, 14, 5, 2423, 0, 0, -1), (580, 27, 22, 2456, 0, 0, -1), (581, 21, 30, 2469, 0, 0, 1), (582, 17, 39, 2471, 0, 0, 1), (583, 12, 21, 2476, 0, 0, 1), (584, 27, 15, 2476, 0, 0, -1), (585, 11, 38, 2479, 0, 0, 1), (586, 33, 14, 2482, 0, 0, -1), (587, 14, 21, 2489, 0, 0, 1), (588, 16, 5, 2494, 0, 0, -1), (589, 7, 24, 2502, 0, 0, 1), (590, 35, 34, 2506, 0, 0, -1), (591, 19, 22, 2512, 0, 0, 1), (592, 29, 30, 2512, 0, 0, 1), (593, 34, 31, 2526, 0, 0, -1), (594, 12, 7, 2530, 0, 0, -1), (595, 18, 38, 2534, 0, 0, 1), (596, 11, 14, 2549, 0, 0, 1), (597, 27, 3, 2559, 0, 0, -1), (598, 32, 20, 2560, 0, 0, -1), (599, 24, 37, 2563, 0, 0, 1), (600, 3, 13, 2565, 0, 0, 1), (601, 14, 34, 2569, 0, 0, 1), (602, 6, 31, 2577, 0, 0, 1), (603, 15, 23, 2577, 0, 0, 1), (604, 26, 33, 2593, 0, 0, 1), (605, 3, 9, 2598, 0, 0, 1), (606, 5, 28, 2599, 0, 0, 1), (607, 18, 8, 2601, 0, 0, -1), (608, 39, 17, 2605, 0, 0, -1), (609, 3, 15, 2611, 0, 0, 1), (610, 4, 26, 2612, 0, 0, 1), (611, 26, 2, 2617, 0, 0, -1), (612, 26, 5, 2620, 0, 0, -1), (613, 28, 1, 2629, 0, 0, -1), (614, 16, 24, 2637, 0, 0, 1), (615, 4, 35, 2639, 0, 0, 1), (616, 3, 16, 2641, 0, 0, 1), (617, 30, 4, 2642, 0, 0, -1), (618, 15, 3, 2643, 0, 0, -1), (619, 15, 19, 2651, 0, 0, 1), (620, 11, 27, 2652, 0, 0, 1), (621, 32, 16, 2652, 0, 0, -1), (622, 22, 30, 2654, 0, 0, 1), (623, 38, 21, 2657, 0, 0, -1), (624, 39, 13, 2664, 0, 0, -1), (625, 16, 29, 2672, 0, 0, 1), (626, 22, 31, 2672, 0, 0, 1), (627, 35, 27, 2688, 0, 0, -1), (628, 22, 0, 2692, 0, 0, -1), (629, 15, 10, 2694, 0, 0, -1), (630, 8, 12, 2695, 0, 0, 1), (631, 7, 21, 2696, 0, 0, 1), (632, 20, 4, 2698, 0, 0, -1), (633, 35, 9, 2700, 0, 0, -1), (634, 30, 27, 2703, 0, 0, -1), (635, 5, 7, 2715, 0, 0, 1), (636, 25, 29, 2716, 0, 0, 1), (637, 30, 15, 2722, 0, 0, -1), (638, 9, 0, 2735, 0, 0, -1), (639, 27, 1, 2735, 0, 0, -1), (640, 21, 19, 2739, 0, 0, -1), (641, 40, 36, 2758, 0, 0, -1), (642, 2, 8, 2763, 0, 0, 1), (643, 14, 23, 2777, 0, 0, 1), (646, 40, 2, 2777, 0, 0, -1), (644, 26, 18, 2777, 0, 0, -1), (645, 39, 23, 2777, 0, 0, -1), (647, 26, 37, 2785, 0, 0, 1), (648, 37, 3, 2786, 0, 0, -1), (650, 17, 25, 2790, 0, 0, 1), (649, 3, 5, 2790, 0, 0, 1), (651, 2, 35, 2793, 0, 0, 1), (652, 10, 9, 2793, 0, 0, -1), (653, 30, 14, 2796, 0, 0, -1), (654, 2, 6, 2800, 0, 0, 1), (655, 30, 10, 2805, 0, 0, -1), (656, 23, 36, 2807, 0, 0, 1), (657, 14, 7, 2810, 0, 0, -1), (658, 13, 8, 2811, 0, 0, -1), (659, 0, 15, 2814, 0, 0, 1), (660, 31, 22, 2818, 0, 0, -1), (661, 22, 15, 2841, 0, 0, -1), (662, 30, 26, 2865, 0, 0, -1), (663, 10, 34, 2870, 0, 0, 1), (664, 33, 5, 2882, 0, 0, -1), (665, 13, 3, 2887, 0, 0, -1), (666, 38, 28, 2887, 0, 0, -1), (667, 27, 29, 2889, 0, 0, 1), (668, 12, 38, 2896, 0, 0, 1), (669, 26, 3, 2897, 0, 0, -1), (670, 39, 2, 2901, 0, 0, -1), (671, 11, 7, 2907, 0, 0, -1), (672, 14, 28, 2915, 0, 0, 1), (673, 37, 28, 2918, 0, 0, -1), (674, 26, 1, 2922, 0, 0, -1), (675, 18, 1, 2924, 0, 0, -1), (676, 25, 26, 2929, 0, 0, 1), (677, 33, 19, 2938, 0, 0, -1), (678, 3, 18, 2943, 0, 0, 1), (679, 8, 11, 2951, 0, 0, 1), (680, 29, 3, 2952, 0, 0, -1), (681, 13, 12, 2963, 0, 0, -1), (682, 40, 14, 2968, 0, 0, -1), (683, 0, 11, 2971, 0, 0, 1), (684, 34, 20, 2974, 0, 0, -1), (685, 28, 39, 2975, 0, 0, 1), (686, 26, 0, 2980, 0, 0, -1), (687, 35, 36, 2983, 0, 0, 1), (688, 1, 21, 2985, 0, 0, 1), (689, 6, 8, 3008, 0, 0, 1), (690, 3, 5, 3015, 0, 0, 1), (691, 28, 37, 3024, 0, 0, 1), (692, 27, 33, 3027, 0, 0, 1), (693, 19, 13, 3042, 0, 0, -1), (694, 34, 5, 3044, 0, 0, -1), (695, 24, 4, 3054, 0, 0, -1), (696, 15, 17, 3055, 0, 0, 1), (697, 13, 3, 3056, 0, 0, -1), (698, 19, 29, 3058, 0, 0, 1), (699, 27, 9, 3058, 0, 0, -1), (700, 12, 35, 3060, 0, 0, 1), (702, 23, 20, 3070, 0, 0, -1), (701, 19, 36, 3070, 0, 0, 1), (703, 28, 1, 3070, 0, 0, -1), (704, 21, 35, 3071, 0, 0, 1), (705, 8, 18, 3075, 0, 0, 1), (706, 31, 2, 3076, 0, 0, -1), (707, 28, 4, 3091, 0, 0, -1), (708, 13, 15, 3092, 0, 0, 1), (710, 37, 16, 3103, 0, 0, -1), (709, 11, 27, 3103, 0, 0, 1), (711, 29, 1, 3104, 0, 0, -1), (712, 27, 35, 3113, 0, 0, 1), (713, 23, 19, 3115, 0, 0, -1), (714, 25, 27, 3121, 0, 0, 1), (715, 1, 40, 3122, 0, 0, 1), (716, 37, 3, 3134, 0, 0, -1), (717, 4, 12, 3146, 0, 0, 1), (718, 20, 40, 3153, 0, 0, 1), (719, 34, 6, 3154, 0, 0, -1), (720, 2, 39, 3158, 0, 0, 1), (721, 29, 16, 3160, 0, 0, -1), (722, 12, 37, 3163, 0, 0, 1), (723, 30, 28, 3165, 0, 0, -1), (724, 21, 36, 3168, 0, 0, 1), (725, 38, 36, 3171, 0, 0, -1), (726, 3, 17, 3176, 0, 0, 1), (727, 32, 12, 3176, 0, 0, -1), (728, 24, 5, 3177, 0, 0, -1), (729, 17, 25, 3179, 0, 0, 1), (730, 18, 40, 3180, 0, 0, 1), (731, 24, 10, 3182, 0, 0, -1), (732, 28, 25, 3185, 0, 0, -1), (733, 8, 7, 3186, 0, 0, -1), (734, 5, 21, 3188, 0, 0, 1), (735, 3, 7, 3191, 0, 0, 1), (736, 17, 23, 3192, 0, 0, 1), (737, 24, 11, 3194, 0, 0, -1), (738, 22, 25, 3195, 0, 0, 1), (739, 17, 5, 3205, 0, 0, -1), (740, 9, 28, 3211, 0, 0, 1), (741, 30, 35, 3213, 0, 0, 1), (742, 35, 22, 3218, 0, 0, -1), (743, 2, 11, 3229, 0, 0, 1), (744, 21, 35, 3232, 0, 0, 1), (745, 31, 28, 3233, 0, 0, -1), (746, 10, 3, 3247, 0, 0, -1), (747, 17, 31, 3249, 0, 0, 1), (748, 5, 18, 3251, 0, 0, 1), (749, 31, 5, 3252, 0, 0, -1), (750, 8, 36, 3257, 0, 0, 1), (751, 6, 11, 3262, 0, 0, 1), (752, 40, 24, 3272, 0, 0, -1), (753, 38, 1, 3282, 0, 0, -1), (754, 20, 3, 3283, 0, 0, -1), (755, 37, 36, 3288, 0, 0, -1), (756, 37, 13, 3293, 0, 0, -1), (757, 18, 27, 3299, 0, 0, 1), (758, 17, 6, 3307, 0, 0, -1), (759, 26, 23, 3321, 0, 0, -1), (760, 3, 15, 3327, 0, 0, 1), (761, 16, 22, 3346, 0, 0, 1), (762, 23, 24, 3346, 0, 0, 1), (763, 12, 11, 3347, 0, 0, -1), (764, 39, 14, 3351, 0, 0, -1), (765, 21, 31, 3369, 0, 0, 1), (766, 28, 3, 3371, 0, 0, -1), (767, 25, 31, 3377, 0, 0, 1), (768, 33, 15, 3381, 0, 0, -1), (769, 10, 8, 3384, 0, 0, -1), (770, 16, 19, 3391, 0, 0, 1), (771, 31, 16, 3392, 0, 0, -1), (772, 4, 39, 3397, 0, 0, 1), (773, 5, 12, 3399, 0, 0, 1), (774, 22, 40, 3412, 0, 0, 1), (776, 25, 14, 3419, 0, 0, -1), (775, 17, 4, 3419, 0, 0, -1), (777, 18, 26, 3420, 0, 0, 1), (779, 25, 24, 3422, 0, 0, -1), (778, 24, 6, 3422, 0, 0, -1), (781, 22, 7, 3428, 0, 0, -1), (780, 17, 28, 3428, 0, 0, 1), (782, 6, 23, 3435, 0, 0, 1), (783, 4, 33, 3451, 0, 0, 1), (784, 9, 1, 3451, 0, 0, -1), (785, 8, 20, 3454, 0, 0, 1), (786, 17, 39, 3459, 0, 0, 1), (787, 6, 13, 3465, 0, 0, 1), (788, 14, 21, 3466, 0, 0, 1), (789, 30, 29, 3467, 0, 0, -1), (790, 0, 15, 3469, 0, 0, 1), (791, 25, 22, 3473, 0, 0, -1), (792, 30, 23, 3480, 0, 0, -1), (793, 1, 31, 3481, 0, 0, 1), (794, 23, 16, 3483, 0, 0, -1), (795, 27, 5, 3491, 0, 0, -1), (796, 0, 6, 3493, 0, 0, 1), (797, 13, 5, 3500, 0, 0, -1), (798, 35, 4, 3501, 0, 0, -1), (799, 26, 18, 3503, 0, 0, -1), (800, 22, 11, 3505, 0, 0, -1), (801, 37, 32, 3506, 0, 0, -1), (802, 15, 19, 3507, 0, 0, 1), (803, 0, 37, 3515, 0, 0, 1), (804, 38, 9, 3517, 0, 0, -1), (805, 1, 6, 3529, 0, 0, 1), (806, 34, 13, 3538, 0, 0, -1), (807, 14, 18, 3547, 0, 0, 1), (808, 0, 29, 3550, 0, 0, 1), (809, 4, 20, 3551, 0, 0, 1), (811, 14, 20, 3555, 0, 0, 1), (810, 5, 3, 3555, 0, 0, -1), (812, 38, 15, 3561, 0, 0, -1), (813, 37, 12, 3568, 0, 0, -1), (815, 37, 5, 3586, 0, 0, -1), (814, 10, 31, 3586, 0, 0, 1), (816, 21, 5, 3591, 0, 0, -1), (817, 36, 23, 3592, 0, 0, -1), (818, 23, 18, 3595, 0, 0, -1), (819, 24, 32, 3596, 0, 0, 1)]
# data = [(1, 0, 18, 0, 0, 0, 1), (2, 1, 15, 0, 0, 0, 1), (3, 2, 5, 0, 0, 0, 1), (4, 3, 11, 0, 0, 0, 1), (5, 4, 18, 0, 0, 0, 1), (6, 5, 12, 0, 0, 0, 1), (7, 6, 8, 0, 0, 0, 1), (8, 7, 12, 0, 0, 0, 1), (9, 8, 3, 0, 0, 0, -1), (10, 9, 13, 0, 0, 0, 1), (11, 10, 14, 0, 0, 0, 1), (12, 11, 13, 0, 0, 0, 1), (13, 12, 15, 0, 0, 0, 1), (14, 13, 3, 0, 0, 0, -1), (15, 14, 3, 0, 0, 0, -1), (16, 15, 4, 0, 0, 0, -1), (17, 16, 6, 0, 0, 0, -1), (18, 17, 4, 0, 0, 0, -1), (19, 18, 14, 0, 0, 0, -1), (20, 19, 8, 0, 0, 0, -1), (21, 20, 2, 0, 0, 0, -1), (22, 3, 20, 29, 0, 0, 1), (23, 5, 13, 35, 0, 0, 1), (24, 3, 7, 40, 0, 0, 1)]

# data = [(1, 0, 10, 0, 0, 0, 1), (2, 1, 18, 0, 0, 0, 1), (3, 2, 4, 0, 0, 0, 1), (4, 3, 13, 0, 0, 0, 1), (5, 4, 13, 0, 0, 0, 1), (6, 5, 1, 0, 0, 0, -1), (7, 6, 20, 0, 0, 0, 1), (8, 7, 19, 0, 0, 0, 1), (9, 8, 5, 0, 0, 0, -1), (10, 9, 7, 0, 0, 0, -1), (11, 10, 8, 0, 0, 0, -1), (12, 11, 1, 0, 0, 0, -1), (13, 12, 3, 0, 0, 0, -1), (14, 13, 0, 0, 0, 0, -1), (15, 14, 5, 0, 0, 0, -1), (16, 15, 16, 0, 0, 0, 1), (17, 16, 17, 0, 0, 0, 1), (18, 17, 1, 0, 0, 0, -1), (19, 18, 16, 0, 0, 0, -1), (20, 19, 3, 0, 0, 0, -1), (21, 20, 17, 0, 0, 0, -1), (22, 3, 1, 2, 0, 0, -1), (23, 8, 5, 22, 0, 0, -1), (24, 4, 2, 24, 0, 0, -1), (25, 5, 16, 37, 0, 0, 1), (26, 0, 13, 88, 0, 0, 1), (27, 9, 17, 93, 0, 0, 1), (28, 6, 20, 103, 0, 0, 1), (29, 8, 10, 106, 0, 0, 1), (30, 0, 5, 118, 0, 0, 1), (31, 16, 0, 119, 0, 0, -1), (32, 11, 0, 125, 0, 0, -1), (33, 12, 20, 126, 0, 0, 1), (34, 8, 16, 131, 0, 0, 1), (35, 4, 18, 134, 0, 0, 1), (36, 20, 7, 156, 0, 0, -1), (37, 18, 12, 159, 0, 0, -1), (38, 12, 9, 170, 0, 0, -1), (39, 5, 20, 187, 0, 0, 1), (40, 19, 7, 191, 0, 0, -1), (41, 6, 3, 192, 0, 0, -1), (42, 3, 17, 193, 0, 0, 1), (43, 8, 7, 199, 0, 0, -1), (44, 3, 6, 200, 0, 0, 1), (45, 16, 0, 214, 0, 0, -1), (46, 2, 18, 240, 0, 0, 1), (47, 4, 17, 241, 0, 0, 1), (48, 18, 14, 245, 0, 0, -1), (49, 8, 19, 274, 0, 0, 1), (50, 19, 9, 280, 0, 0, -1), (51, 3, 5, 302, 0, 0, 1), (52, 10, 12, 310, 0, 0, 1), (53, 16, 3, 317, 0, 0, -1), (54, 2, 5, 322, 0, 0, 1), (55, 13, 15, 325, 0, 0, 1), (56, 10, 17, 332, 0, 0, 1), (57, 5, 4, 332, 0, 0, -1), (58, 17, 7, 336, 0, 0, -1), (59, 1, 5, 342, 0, 0, 1), (60, 10, 0, 357, 0, 0, -1), (61, 18, 15, 384, 0, 0, -1), (62, 10, 3, 413, 0, 0, -1), (63, 4, 13, 416, 0, 0, 1), (64, 1, 10, 438, 0, 0, 1), (65, 18, 12, 444, 0, 0, -1), (66, 1, 4, 452, 0, 0, 1), (67, 19, 8, 460, 0, 0, -1), (68, 19, 7, 464, 0, 0, -1), (69, 16, 18, 466, 0, 0, 1), (70, 8, 5, 471, 0, 0, -1), (71, 9, 11, 474, 0, 0, 1), (72, 13, 10, 484, 0, 0, -1), (73, 13, 7, 512, 0, 0, -1), (74, 2, 20, 516, 0, 0, 1), (75, 10, 12, 545, 0, 0, 1), (76, 19, 13, 556, 0, 0, -1), (77, 7, 13, 561, 0, 0, 1), (78, 14, 10, 566, 0, 0, -1), (79, 17, 5, 567, 0, 0, -1), (80, 7, 15, 575, 0, 0, 1), (81, 5, 3, 581, 0, 0, -1), (82, 12, 2, 586, 0, 0, -1), (83, 14, 18, 597, 0, 0, 1), (84, 6, 3, 603, 0, 0, -1), (85, 20, 12, 617, 0, 0, -1), (86, 14, 0, 642, 0, 0, -1), (87, 19, 14, 645, 0, 0, -1), (88, 3, 0, 662, 0, 0, -1), (89, 0, 8, 664, 0, 0, 1), (90, 15, 3, 670, 0, 0, -1), (91, 9, 13, 680, 0, 0, 1), (92, 9, 20, 704, 0, 0, 1), (93, 17, 0, 715, 0, 0, -1), (94, 7, 12, 717, 0, 0, 1), (95, 1, 19, 720, 0, 0, 1), (96, 14, 8, 745, 0, 0, -1), (97, 4, 2, 754, 0, 0, -1), (98, 20, 3, 755, 0, 0, -1), (99, 3, 7, 761, 0, 0, 1), (100, 0, 17, 781, 0, 0, 1), (101, 14, 15, 781, 0, 0, 1), (102, 18, 2, 781, 0, 0, -1), (103, 8, 10, 785, 0, 0, 1), (104, 9, 4, 801, 0, 0, -1), (105, 0, 10, 813, 0, 0, 1), (106, 5, 20, 815, 0, 0, 1), (107, 1, 13, 818, 0, 0, 1), (108, 17, 8, 822, 0, 0, -1), (109, 5, 8, 827, 0, 0, 1), (110, 16, 12, 830, 0, 0, -1), (111, 8, 10, 837, 0, 0, 1), (112, 7, 6, 839, 0, 0, -1), (113, 18, 5, 854, 0, 0, -1), (114, 1, 20, 866, 0, 0, 1), (115, 2, 15, 867, 0, 0, 1), (116, 15, 14, 870, 0, 0, -1), (117, 14, 11, 872, 0, 0, -1), (118, 5, 4, 904, 0, 0, -1), (119, 9, 17, 904, 0, 0, 1), (120, 17, 13, 905, 0, 0, -1), (121, 0, 7, 911, 0, 0, 1), (122, 10, 0, 924, 0, 0, -1), (123, 4, 7, 927, 0, 0, 1), (124, 6, 5, 934, 0, 0, -1), (125, 5, 12, 938, 0, 0, 1), (126, 16, 11, 960, 0, 0, -1), (127, 4, 17, 966, 0, 0, 1), (128, 4, 3, 968, 0, 0, -1), (129, 16, 9, 983, 0, 0, -1), (130, 0, 7, 988, 0, 0, 1), (131, 4, 19, 996, 0, 0, 1), (132, 8, 12, 1026, 0, 0, 1), (133, 4, 13, 1037, 0, 0, 1), (134, 11, 1, 1037, 0, 0, -1), (135, 11, 6, 1043, 0, 0, -1), (136, 8, 2, 1062, 0, 0, -1), (137, 4, 19, 1069, 0, 0, 1), (138, 7, 10, 1085, 0, 0, 1), (139, 20, 10, 1127, 0, 0, -1), (140, 12, 13, 1134, 0, 0, 1), (141, 2, 14, 1137, 0, 0, 1), (142, 14, 4, 1145, 0, 0, -1), (143, 12, 16, 1152, 0, 0, 1), (144, 18, 11, 1160, 0, 0, -1), (145, 3, 0, 1165, 0, 0, -1), (146, 9, 6, 1165, 0, 0, -1), (147, 3, 14, 1169, 0, 0, 1), (148, 3, 0, 1176, 0, 0, -1), (149, 8, 12, 1178, 0, 0, 1), (150, 19, 2, 1183, 0, 0, -1), (151, 5, 1, 1185, 0, 0, -1), (152, 9, 0, 1189, 0, 0, -1), (153, 16, 1, 1189, 0, 0, -1), (154, 10, 14, 1196, 0, 0, 1), (155, 18, 13, 1196, 0, 0, -1), (156, 14, 8, 1227, 0, 0, -1), (157, 4, 6, 1233, 0, 0, 1), (158, 4, 1, 1261, 0, 0, -1), (159, 14, 11, 1274, 0, 0, -1), (160, 15, 1, 1281, 0, 0, -1), (161, 2, 16, 1283, 0, 0, 1), (162, 18, 12, 1286, 0, 0, -1), (163, 5, 20, 1287, 0, 0, 1), (164, 2, 17, 1297, 0, 0, 1), (165, 14, 2, 1315, 0, 0, -1), (166, 5, 0, 1330, 0, 0, -1), (167, 9, 1, 1345, 0, 0, -1), (168, 5, 4, 1347, 0, 0, -1), (169, 16, 18, 1347, 0, 0, 1), (170, 15, 5, 1358, 0, 0, -1), (171, 2, 20, 1361, 0, 0, 1), (172, 16, 19, 1375, 0, 0, 1), (173, 7, 9, 1385, 0, 0, 1), (174, 8, 15, 1402, 0, 0, 1), (175, 20, 3, 1411, 0, 0, -1), (176, 14, 6, 1420, 0, 0, -1), (178, 16, 10, 1463, 0, 0, -1), (177, 10, 16, 1463, 0, 0, 1), (179, 13, 15, 1469, 0, 0, 1), (180, 4, 20, 1470, 0, 0, 1), (181, 0, 4, 1470, 0, 0, 1), (182, 0, 3, 1471, 0, 0, 1), (183, 7, 20, 1483, 0, 0, 1), (184, 1, 6, 1484, 0, 0, 1), (185, 4, 16, 1496, 0, 0, 1), (186, 1, 20, 1501, 0, 0, 1), (187, 12, 0, 1505, 0, 0, -1), (188, 17, 16, 1518, 0, 0, -1), (189, 8, 20, 1536, 0, 0, 1), (190, 3, 6, 1558, 0, 0, 1), (191, 1, 7, 1569, 0, 0, 1), (192, 3, 17, 1583, 0, 0, 1), (193, 20, 19, 1595, 0, 0, -1), (194, 1, 13, 1611, 0, 0, 1), (195, 11, 6, 1614, 0, 0, -1), (196, 18, 17, 1614, 0, 0, -1), (197, 0, 13, 1619, 0, 0, 1), (198, 10, 16, 1620, 0, 0, 1), (199, 0, 9, 1621, 0, 0, 1), (200, 18, 16, 1627, 0, 0, -1), (201, 17, 2, 1645, 0, 0, -1), (202, 20, 1, 1645, 0, 0, -1), (203, 14, 16, 1669, 0, 0, 1), (204, 18, 10, 1691, 0, 0, -1), (205, 15, 0, 1701, 0, 0, -1), (206, 11, 9, 1709, 0, 0, -1), (207, 1, 15, 1717, 0, 0, 1), (208, 6, 17, 1718, 0, 0, 1), (209, 4, 17, 1727, 0, 0, 1), (210, 7, 9, 1731, 0, 0, 1), (211, 9, 16, 1741, 0, 0, 1), (212, 9, 1, 1747, 0, 0, -1), (213, 6, 15, 1755, 0, 0, 1), (214, 5, 12, 1758, 0, 0, 1), (215, 12, 20, 1762, 0, 0, 1), (216, 12, 19, 1768, 0, 0, 1), (217, 16, 1, 1770, 0, 0, -1), (218, 8, 10, 1777, 0, 0, 1), (219, 1, 10, 1790, 0, 0, 1), (220, 20, 1, 1803, 0, 0, -1), (221, 2, 7, 1811, 0, 0, 1), (222, 7, 16, 1836, 0, 0, 1), (223, 11, 17, 1838, 0, 0, 1), (224, 3, 8, 1844, 0, 0, 1), (225, 17, 5, 1853, 0, 0, -1), (226, 5, 6, 1858, 0, 0, 1), (227, 7, 5, 1885, 0, 0, -1), (228, 10, 16, 1891, 0, 0, 1), (229, 16, 10, 1903, 0, 0, -1), (230, 15, 19, 1910, 0, 0, 1), (231, 9, 20, 1931, 0, 0, 1), (232, 16, 8, 1931, 0, 0, -1), (233, 12, 13, 1932, 0, 0, 1), (234, 14, 0, 1932, 0, 0, -1), (235, 10, 5, 1933, 0, 0, -1), (236, 13, 14, 1934, 0, 0, 1), (237, 0, 4, 1939, 0, 0, 1), (238, 18, 19, 1954, 0, 0, 1), (239, 15, 4, 1958, 0, 0, -1), (240, 9, 16, 1978, 0, 0, 1), (241, 1, 8, 1988, 0, 0, 1), (242, 19, 1, 2000, 0, 0, -1), (243, 8, 11, 2001, 0, 0, 1), (244, 4, 14, 2048, 0, 0, 1), (245, 1, 0, 2054, 0, 0, -1), (246, 7, 12, 2058, 0, 0, 1), (247, 4, 2, 2058, 0, 0, -1), (248, 8, 6, 2069, 0, 0, -1), (249, 6, 9, 2073, 0, 0, 1), (250, 20, 17, 2086, 0, 0, -1), (251, 0, 5, 2088, 0, 0, 1), (252, 0, 2, 2106, 0, 0, 1), (253, 9, 17, 2106, 0, 0, 1), (254, 9, 4, 2109, 0, 0, -1), (255, 6, 5, 2111, 0, 0, -1), (256, 0, 10, 2117, 0, 0, 1), (257, 3, 17, 2135, 0, 0, 1), (258, 7, 19, 2141, 0, 0, 1), (259, 14, 16, 2145, 0, 0, 1), (260, 8, 12, 2147, 0, 0, 1), (261, 17, 0, 2156, 0, 0, -1), (262, 8, 20, 2164, 0, 0, 1), (263, 1, 9, 2187, 0, 0, 1), (264, 3, 13, 2191, 0, 0, 1), (265, 6, 8, 2199, 0, 0, 1), (266, 12, 8, 2210, 0, 0, -1), (267, 15, 17, 2210, 0, 0, 1), (268, 10, 18, 2212, 0, 0, 1), (269, 12, 0, 2217, 0, 0, -1), (270, 3, 6, 2217, 0, 0, 1), (271, 16, 11, 2234, 0, 0, -1), (272, 12, 13, 2238, 0, 0, 1), (273, 2, 1, 2243, 0, 0, -1), (274, 9, 20, 2246, 0, 0, 1), (275, 6, 19, 2246, 0, 0, 1), (276, 9, 5, 2254, 0, 0, -1), (277, 8, 5, 2258, 0, 0, -1), (278, 17, 14, 2271, 0, 0, -1), (279, 16, 4, 2296, 0, 0, -1), (280, 14, 16, 2299, 0, 0, 1), (281, 6, 9, 2303, 0, 0, 1), (282, 9, 5, 2346, 0, 0, -1), (283, 14, 4, 2359, 0, 0, -1), (284, 12, 14, 2378, 0, 0, 1), (285, 18, 15, 2382, 0, 0, -1), (286, 19, 5, 2400, 0, 0, -1), (287, 20, 4, 2403, 0, 0, -1), (288, 19, 17, 2413, 0, 0, -1), (289, 10, 13, 2414, 0, 0, 1), (290, 5, 1, 2428, 0, 0, -1), (291, 17, 0, 2440, 0, 0, -1), (292, 19, 13, 2466, 0, 0, -1), (293, 15, 0, 2472, 0, 0, -1), (294, 12, 11, 2489, 0, 0, -1), (295, 2, 18, 2490, 0, 0, 1), (296, 9, 15, 2528, 0, 0, 1), (297, 7, 9, 2537, 0, 0, 1), (298, 1, 4, 2567, 0, 0, 1), (299, 2, 4, 2584, 0, 0, 1), (300, 17, 15, 2596, 0, 0, -1), (301, 3, 15, 2606, 0, 0, 1), (302, 3, 9, 2610, 0, 0, 1), (303, 19, 15, 2612, 0, 0, -1), (304, 20, 15, 2623, 0, 0, -1), (305, 3, 12, 2624, 0, 0, 1), (306, 6, 16, 2635, 0, 0, 1), (307, 16, 2, 2639, 0, 0, -1), (308, 12, 4, 2658, 0, 0, -1), (309, 14, 2, 2667, 0, 0, -1), (310, 9, 2, 2672, 0, 0, -1), (311, 7, 16, 2676, 0, 0, 1), (312, 5, 14, 2683, 0, 0, 1), (313, 18, 17, 2710, 0, 0, -1), (314, 10, 6, 2719, 0, 0, -1), (315, 3, 20, 2740, 0, 0, 1), (316, 10, 6, 2740, 0, 0, -1), (317, 0, 10, 2748, 0, 0, 1), (318, 9, 15, 2753, 0, 0, 1), (319, 5, 9, 2759, 0, 0, 1), (320, 16, 2, 2762, 0, 0, -1), (321, 1, 19, 2772, 0, 0, 1), (322, 0, 3, 2778, 0, 0, 1), (323, 4, 20, 2781, 0, 0, 1), (324, 3, 14, 2793, 0, 0, 1), (325, 1, 18, 2798, 0, 0, 1), (326, 8, 13, 2799, 0, 0, 1), (327, 13, 3, 2811, 0, 0, -1), (328, 0, 16, 2844, 0, 0, 1), (329, 9, 16, 2848, 0, 0, 1), (330, 12, 19, 2850, 0, 0, 1), (331, 19, 13, 2851, 0, 0, -1), (332, 0, 4, 2865, 0, 0, 1), (333, 17, 10, 2869, 0, 0, -1), (334, 9, 11, 2870, 0, 0, 1), (335, 20, 3, 2873, 0, 0, -1), (336, 7, 20, 2875, 0, 0, 1), (337, 6, 5, 2911, 0, 0, -1), (338, 0, 1, 2930, 0, 0, 1), (339, 6, 20, 2935, 0, 0, 1), (340, 7, 10, 2935, 0, 0, 1), (341, 9, 15, 2944, 0, 0, 1), (342, 12, 1, 2945, 0, 0, -1), (343, 14, 4, 2945, 0, 0, -1), (344, 16, 15, 2950, 0, 0, -1), (345, 1, 18, 2972, 0, 0, 1), (346, 19, 14, 2975, 0, 0, -1), (347, 6, 3, 2977, 0, 0, -1), (348, 5, 6, 2977, 0, 0, 1), (349, 20, 0, 2981, 0, 0, -1), (350, 12, 11, 2991, 0, 0, -1), (351, 10, 5, 3004, 0, 0, -1), (352, 11, 14, 3005, 0, 0, 1), (353, 1, 3, 3009, 0, 0, 1), (354, 5, 16, 3024, 0, 0, 1), (355, 2, 14, 3033, 0, 0, 1), (356, 0, 3, 3050, 0, 0, 1), (357, 9, 13, 3054, 0, 0, 1), (358, 9, 11, 3070, 0, 0, 1), (359, 2, 12, 3080, 0, 0, 1), (360, 0, 18, 3082, 0, 0, 1), (361, 7, 16, 3093, 0, 0, 1), (362, 10, 16, 3098, 0, 0, 1), (363, 0, 1, 3126, 0, 0, 1), (364, 0, 4, 3131, 0, 0, 1), (365, 1, 2, 3137, 0, 0, 1), (366, 0, 2, 3139, 0, 0, 1), (367, 7, 2, 3142, 0, 0, -1), (368, 20, 11, 3148, 0, 0, -1), (369, 1, 11, 3152, 0, 0, 1), (370, 5, 0, 3170, 0, 0, -1), (371, 12, 4, 3178, 0, 0, -1), (372, 20, 14, 3181, 0, 0, -1), (373, 12, 7, 3199, 0, 0, -1), (374, 16, 1, 3201, 0, 0, -1), (375, 4, 0, 3204, 0, 0, -1), (376, 14, 7, 3204, 0, 0, -1), (377, 14, 5, 3222, 0, 0, -1), (378, 4, 13, 3226, 0, 0, 1), (379, 19, 8, 3226, 0, 0, -1), (380, 17, 14, 3227, 0, 0, -1), (381, 9, 16, 3228, 0, 0, 1), (382, 5, 20, 3228, 0, 0, 1), (383, 18, 16, 3248, 0, 0, -1), (384, 15, 0, 3252, 0, 0, -1), (385, 1, 19, 3254, 0, 0, 1), (386, 17, 9, 3257, 0, 0, -1), (387, 6, 10, 3279, 0, 0, 1), (388, 6, 19, 3281, 0, 0, 1), (389, 5, 4, 3293, 0, 0, -1), (390, 14, 3, 3333, 0, 0, -1), (391, 5, 9, 3346, 0, 0, 1), (392, 4, 15, 3350, 0, 0, 1), (393, 7, 3, 3369, 0, 0, -1), (394, 0, 13, 3370, 0, 0, 1), (395, 17, 10, 3371, 0, 0, -1), (396, 14, 4, 3377, 0, 0, -1), (397, 1, 5, 3384, 0, 0, 1), (398, 16, 3, 3423, 0, 0, -1), (399, 10, 15, 3429, 0, 0, 1), (400, 13, 11, 3442, 0, 0, -1), (401, 0, 11, 3452, 0, 0, 1), (402, 20, 2, 3459, 0, 0, -1), (403, 8, 16, 3462, 0, 0, 1), (404, 8, 15, 3462, 0, 0, 1), (405, 1, 3, 3497, 0, 0, 1), (406, 15, 12, 3498, 0, 0, -1), (407, 12, 14, 3500, 0, 0, 1), (408, 0, 3, 3509, 0, 0, 1), (409, 6, 1, 3512, 0, 0, -1), (410, 0, 11, 3514, 0, 0, 1), (411, 11, 8, 3516, 0, 0, -1), (412, 3, 16, 3556, 0, 0, 1), (413, 6, 17, 3557, 0, 0, 1), (414, 0, 3, 3560, 0, 0, 1), (415, 16, 7, 3583, 0, 0, -1), (416, 19, 20, 3597, 0, 0, 1), (417, 4, 13, 3608, 0, 0, 1), (418, 13, 7, 3617, 0, 0, -1), (419, 5, 19, 3627, 0, 0, 1), (420, 11, 12, 3640, 0, 0, 1), (421, 6, 18, 3644, 0, 0, 1), (422, 10, 6, 3659, 0, 0, -1), (423, 14, 1, 3669, 0, 0, -1), (424, 11, 7, 3683, 0, 0, -1), (425, 11, 4, 3684, 0, 0, -1), (426, 20, 7, 3687, 0, 0, -1), (427, 17, 2, 3694, 0, 0, -1), (428, 12, 3, 3697, 0, 0, -1), (429, 10, 8, 3704, 0, 0, -1), (430, 18, 12, 3727, 0, 0, -1), (431, 1, 10, 3730, 0, 0, 1), (432, 1, 2, 3732, 0, 0, 1), (433, 3, 18, 3733, 0, 0, 1), (434, 9, 14, 3756, 0, 0, 1), (435, 0, 14, 3763, 0, 0, 1), (436, 20, 7, 3764, 0, 0, -1), (437, 4, 18, 3764, 0, 0, 1), (438, 17, 15, 3778, 0, 0, -1), (439, 12, 16, 3781, 0, 0, 1), (440, 6, 5, 3783, 0, 0, -1), (441, 11, 1, 3788, 0, 0, -1), (442, 4, 13, 3791, 0, 0, 1), (443, 11, 14, 3791, 0, 0, 1), (444, 18, 8, 3809, 0, 0, -1), (445, 17, 16, 3822, 0, 0, -1), (446, 1, 9, 3823, 0, 0, 1), (447, 2, 5, 3845, 0, 0, 1), (448, 12, 18, 3858, 0, 0, 1), (449, 19, 6, 3862, 0, 0, -1), (450, 11, 1, 3862, 0, 0, -1), (451, 11, 16, 3881, 0, 0, 1), (452, 3, 15, 3906, 0, 0, 1), (453, 9, 18, 3937, 0, 0, 1), (454, 7, 6, 3945, 0, 0, -1), (455, 3, 14, 3969, 0, 0, 1), (456, 2, 15, 3983, 0, 0, 1), (457, 0, 11, 3988, 0, 0, 1), (458, 16, 6, 4007, 0, 0, -1), (459, 5, 18, 4016, 0, 0, 1), (460, 3, 0, 4023, 0, 0, -1), (461, 16, 13, 4031, 0, 0, -1), (462, 6, 15, 4056, 0, 0, 1), (463, 5, 20, 4063, 0, 0, 1), (464, 0, 15, 4078, 0, 0, 1), (465, 20, 1, 4081, 0, 0, -1), (466, 11, 3, 4102, 0, 0, -1), (467, 5, 3, 4105, 0, 0, -1), (468, 14, 4, 4125, 0, 0, -1), (469, 12, 5, 4129, 0, 0, -1), (470, 3, 17, 4134, 0, 0, 1), (471, 7, 0, 4146, 0, 0, -1), (472, 13, 15, 4148, 0, 0, 1), (473, 19, 2, 4165, 0, 0, -1), (474, 5, 4, 4176, 0, 0, -1), (475, 17, 0, 4204, 0, 0, -1), (476, 11, 5, 4207, 0, 0, -1), (477, 14, 7, 4222, 0, 0, -1), (478, 19, 16, 4223, 0, 0, -1), (479, 14, 5, 4224, 0, 0, -1), (480, 7, 3, 4242, 0, 0, -1), (481, 13, 12, 4246, 0, 0, -1), (482, 15, 13, 4287, 0, 0, -1), (483, 1, 11, 4339, 0, 0, 1), (484, 5, 20, 4344, 0, 0, 1), (485, 0, 8, 4356, 0, 0, 1), (486, 14, 3, 4357, 0, 0, -1), (487, 9, 7, 4359, 0, 0, -1), (488, 10, 8, 4362, 0, 0, -1), (489, 18, 4, 4365, 0, 0, -1), (490, 14, 13, 4367, 0, 0, -1), (491, 6, 11, 4368, 0, 0, 1), (492, 8, 3, 4376, 0, 0, -1), (493, 16, 18, 4384, 0, 0, 1), (494, 12, 14, 4401, 0, 0, 1), (495, 2, 1, 4404, 0, 0, -1), (496, 2, 6, 4420, 0, 0, 1), (497, 3, 5, 4451, 0, 0, 1), (498, 0, 13, 4452, 0, 0, 1), (499, 9, 2, 4465, 0, 0, -1), (500, 0, 16, 4466, 0, 0, 1), (501, 19, 15, 4472, 0, 0, -1), (502, 12, 19, 4472, 0, 0, 1), (503, 14, 15, 4505, 0, 0, 1), (504, 6, 2, 4507, 0, 0, -1), (505, 11, 18, 4509, 0, 0, 1), (506, 0, 10, 4520, 0, 0, 1), (507, 16, 4, 4521, 0, 0, -1), (508, 14, 16, 4521, 0, 0, 1), (509, 20, 12, 4542, 0, 0, -1), (510, 19, 8, 4547, 0, 0, -1), (511, 10, 14, 4552, 0, 0, 1), (512, 5, 14, 4573, 0, 0, 1), (513, 1, 18, 4575, 0, 0, 1), (514, 9, 12, 4575, 0, 0, 1), (515, 20, 4, 4583, 0, 0, -1), (516, 11, 2, 4588, 0, 0, -1), (517, 0, 6, 4627, 0, 0, 1), (518, 3, 8, 4630, 0, 0, 1), (519, 18, 2, 4637, 0, 0, -1), (520, 16, 19, 4642, 0, 0, 1), (521, 20, 2, 4653, 0, 0, -1), (522, 12, 3, 4669, 0, 0, -1), (523, 13, 20, 4674, 0, 0, 1), (524, 0, 7, 4684, 0, 0, 1), (525, 16, 10, 4701, 0, 0, -1), (526, 13, 2, 4706, 0, 0, -1), (527, 1, 9, 4711, 0, 0, 1), (528, 12, 15, 4713, 0, 0, 1), (529, 19, 4, 4729, 0, 0, -1), (530, 3, 16, 4783, 0, 0, 1), (531, 11, 19, 4783, 0, 0, 1), (532, 16, 8, 4795, 0, 0, -1), (533, 11, 6, 4798, 0, 0, -1), (534, 15, 18, 4811, 0, 0, 1), (535, 11, 1, 4819, 0, 0, -1), (536, 8, 16, 4821, 0, 0, 1), (537, 7, 10, 4826, 0, 0, 1), (538, 15, 10, 4848, 0, 0, -1), (539, 0, 11, 4848, 0, 0, 1), (540, 8, 5, 4864, 0, 0, -1), (541, 0, 17, 4874, 0, 0, 1), (542, 0, 18, 4882, 0, 0, 1), (543, 10, 14, 4886, 0, 0, 1), (544, 12, 4, 4891, 0, 0, -1), (545, 19, 11, 4907, 0, 0, -1), (546, 3, 19, 4911, 0, 0, 1), (547, 11, 14, 4917, 0, 0, 1), (548, 1, 6, 4917, 0, 0, 1), (549, 7, 10, 4921, 0, 0, 1), (550, 14, 6, 4927, 0, 0, -1), (551, 17, 6, 4932, 0, 0, -1), (552, 1, 20, 4933, 0, 0, 1), (553, 15, 3, 4944, 0, 0, -1), (554, 16, 1, 4949, 0, 0, -1), (555, 2, 9, 4969, 0, 0, 1), (556, 20, 15, 4985, 0, 0, -1), (557, 7, 8, 4987, 0, 0, 1), (558, 0, 11, 4991, 0, 0, 1), (559, 1, 7, 5005, 0, 0, 1), (560, 7, 13, 5010, 0, 0, 1), (561, 15, 12, 5021, 0, 0, -1), (562, 1, 15, 5036, 0, 0, 1), (563, 12, 9, 5040, 0, 0, -1), (564, 10, 16, 5042, 0, 0, 1), (565, 16, 18, 5051, 0, 0, 1), (566, 9, 11, 5056, 0, 0, 1), (567, 19, 20, 5061, 0, 0, 1), (568, 7, 10, 5063, 0, 0, 1), (569, 0, 20, 5093, 0, 0, 1), (570, 18, 19, 5117, 0, 0, 1), (571, 7, 10, 5123, 0, 0, 1), (572, 1, 4, 5132, 0, 0, 1), (573, 10, 6, 5146, 0, 0, -1), (574, 10, 9, 5160, 0, 0, -1), (575, 8, 1, 5172, 0, 0, -1), (576, 16, 5, 5189, 0, 0, -1), (577, 2, 17, 5195, 0, 0, 1), (578, 18, 3, 5202, 0, 0, -1), (579, 3, 16, 5205, 0, 0, 1), (580, 14, 17, 5210, 0, 0, 1), (581, 9, 8, 5214, 0, 0, -1), (582, 18, 1, 5216, 0, 0, -1), (583, 8, 18, 5228, 0, 0, 1), (584, 7, 5, 5245, 0, 0, -1), (585, 19, 10, 5249, 0, 0, -1), (586, 14, 5, 5259, 0, 0, -1), (587, 8, 1, 5262, 0, 0, -1), (588, 14, 20, 5277, 0, 0, 1), (589, 17, 15, 5292, 0, 0, -1), (590, 20, 11, 5320, 0, 0, -1), (591, 4, 7, 5326, 0, 0, 1), (592, 5, 15, 5329, 0, 0, 1), (593, 14, 2, 5331, 0, 0, -1), (594, 17, 11, 5341, 0, 0, -1), (595, 0, 3, 5345, 0, 0, 1), (596, 10, 5, 5356, 0, 0, -1), (597, 8, 3, 5358, 0, 0, -1), (598, 14, 18, 5372, 0, 0, 1), (600, 17, 18, 5387, 0, 0, 1), (599, 7, 2, 5387, 0, 0, -1), (601, 4, 0, 5389, 0, 0, -1), (602, 17, 6, 5391, 0, 0, -1), (603, 18, 8, 5400, 0, 0, -1), (604, 17, 18, 5405, 0, 0, 1), (605, 18, 11, 5406, 0, 0, -1), (606, 1, 13, 5410, 0, 0, 1), (607, 12, 7, 5423, 0, 0, -1), (608, 17, 15, 5452, 0, 0, -1), (609, 4, 2, 5459, 0, 0, -1), (610, 9, 0, 5463, 0, 0, -1), (611, 0, 11, 5481, 0, 0, 1), (612, 10, 20, 5486, 0, 0, 1), (613, 10, 16, 5496, 0, 0, 1), (614, 1, 20, 5505, 0, 0, 1), (615, 1, 3, 5508, 0, 0, 1), (616, 0, 15, 5533, 0, 0, 1), (617, 0, 14, 5539, 0, 0, 1), (618, 4, 3, 5544, 0, 0, -1), (619, 13, 7, 5545, 0, 0, -1), (620, 6, 12, 5562, 0, 0, 1), (621, 8, 13, 5575, 0, 0, 1), (622, 18, 11, 5587, 0, 0, -1), (623, 13, 9, 5593, 0, 0, -1), (624, 14, 18, 5618, 0, 0, 1), (625, 4, 11, 5634, 0, 0, 1), (626, 9, 7, 5638, 0, 0, -1), (627, 18, 7, 5638, 0, 0, -1), (628, 4, 5, 5655, 0, 0, 1), (629, 7, 6, 5662, 0, 0, -1), (630, 4, 8, 5673, 0, 0, 1), (631, 8, 17, 5683, 0, 0, 1), (632, 7, 10, 5684, 0, 0, 1), (633, 10, 4, 5693, 0, 0, -1), (634, 2, 3, 5693, 0, 0, 1), (635, 6, 3, 5693, 0, 0, -1), (636, 4, 0, 5706, 0, 0, -1), (637, 6, 4, 5714, 0, 0, -1), (638, 20, 16, 5719, 0, 0, -1), (639, 14, 3, 5725, 0, 0, -1), (640, 11, 15, 5727, 0, 0, 1), (641, 10, 17, 5730, 0, 0, 1), (642, 4, 10, 5731, 0, 0, 1), (643, 3, 14, 5739, 0, 0, 1), (644, 14, 0, 5743, 0, 0, -1), (645, 5, 6, 5747, 0, 0, 1), (646, 14, 20, 5752, 0, 0, 1), (647, 19, 9, 5759, 0, 0, -1), (648, 9, 11, 5764, 0, 0, 1), (649, 16, 13, 5767, 0, 0, -1), (650, 11, 17, 5775, 0, 0, 1), (651, 13, 3, 5801, 0, 0, -1), (652, 15, 7, 5805, 0, 0, -1), (653, 16, 15, 5809, 0, 0, -1), (654, 20, 19, 5835, 0, 0, -1), (655, 10, 6, 5838, 0, 0, -1), (656, 4, 2, 5899, 0, 0, -1), (657, 2, 4, 5909, 0, 0, 1), (658, 6, 12, 5924, 0, 0, 1), (659, 17, 13, 5926, 0, 0, -1), (660, 12, 6, 5931, 0, 0, -1), (661, 9, 10, 5951, 0, 0, 1), (662, 5, 8, 5954, 0, 0, 1), (663, 2, 14, 5966, 0, 0, 1), (664, 20, 14, 5982, 0, 0, -1), (665, 6, 7, 6003, 0, 0, 1), (666, 4, 12, 6018, 0, 0, 1), (667, 0, 9, 6019, 0, 0, 1), (668, 17, 7, 6031, 0, 0, -1), (669, 18, 4, 6034, 0, 0, -1), (670, 12, 2, 6041, 0, 0, -1), (671, 8, 14, 6051, 0, 0, 1), (672, 11, 9, 6053, 0, 0, -1), (673, 16, 4, 6053, 0, 0, -1), (674, 0, 9, 6056, 0, 0, 1), (675, 7, 12, 6056, 0, 0, 1), (676, 0, 19, 6082, 0, 0, 1), (677, 0, 6, 6084, 0, 0, 1), (678, 14, 15, 6084, 0, 0, 1), (679, 14, 19, 6089, 0, 0, 1), (680, 12, 9, 6100, 0, 0, -1), (681, 15, 12, 6116, 0, 0, -1), (682, 3, 8, 6127, 0, 0, 1), (683, 4, 16, 6130, 0, 0, 1), (684, 2, 14, 6140, 0, 0, 1), (685, 10, 17, 6173, 0, 0, 1), (686, 15, 1, 6186, 0, 0, -1), (687, 20, 9, 6201, 0, 0, -1), (688, 6, 8, 6202, 0, 0, 1), (689, 6, 18, 6212, 0, 0, 1), (690, 5, 8, 6228, 0, 0, 1), (691, 7, 9, 6237, 0, 0, 1), (692, 4, 17, 6243, 0, 0, 1), (693, 9, 17, 6244, 0, 0, 1), (694, 7, 11, 6246, 0, 0, 1), (695, 12, 18, 6256, 0, 0, 1), (696, 6, 15, 6271, 0, 0, 1), (697, 5, 16, 6273, 0, 0, 1), (698, 4, 16, 6280, 0, 0, 1), (699, 1, 16, 6297, 0, 0, 1), (700, 8, 11, 6301, 0, 0, 1), (701, 8, 3, 6311, 0, 0, -1), (702, 17, 8, 6318, 0, 0, -1), (703, 0, 12, 6318, 0, 0, 1), (704, 13, 7, 6318, 0, 0, -1), (705, 0, 6, 6326, 0, 0, 1), (706, 1, 19, 6327, 0, 0, 1), (707, 5, 18, 6328, 0, 0, 1), (708, 12, 11, 6340, 0, 0, -1), (709, 2, 8, 6344, 0, 0, 1), (710, 0, 9, 6351, 0, 0, 1), (711, 5, 0, 6362, 0, 0, -1), (712, 13, 12, 6371, 0, 0, -1), (713, 10, 4, 6375, 0, 0, -1), (714, 3, 16, 6378, 0, 0, 1), (715, 3, 12, 6378, 0, 0, 1), (716, 13, 16, 6389, 0, 0, 1), (717, 12, 7, 6392, 0, 0, -1), (718, 18, 20, 6409, 0, 0, 1), (719, 8, 7, 6413, 0, 0, -1), (720, 3, 13, 6424, 0, 0, 1), (721, 20, 10, 6434, 0, 0, -1), (722, 0, 18, 6440, 0, 0, 1), (723, 4, 6, 6444, 0, 0, 1), (724, 14, 20, 6449, 0, 0, 1), (725, 1, 0, 6450, 0, 0, -1), (726, 5, 19, 6453, 0, 0, 1), (727, 16, 4, 6455, 0, 0, -1), (728, 5, 4, 6459, 0, 0, -1), (729, 5, 10, 6461, 0, 0, 1), (730, 1, 4, 6462, 0, 0, 1), (731, 16, 15, 6479, 0, 0, -1), (732, 14, 2, 6495, 0, 0, -1), (733, 0, 9, 6507, 0, 0, 1), (734, 4, 17, 6522, 0, 0, 1), (735, 11, 2, 6523, 0, 0, -1), (736, 8, 16, 6527, 0, 0, 1), (737, 1, 16, 6527, 0, 0, 1), (738, 0, 2, 6544, 0, 0, 1), (739, 10, 1, 6545, 0, 0, -1), (740, 1, 12, 6574, 0, 0, 1), (741, 8, 11, 6583, 0, 0, 1), (742, 4, 14, 6584, 0, 0, 1), (743, 13, 11, 6587, 0, 0, -1), (744, 13, 2, 6592, 0, 0, -1), (745, 1, 20, 6593, 0, 0, 1), (746, 20, 0, 6594, 0, 0, -1), (747, 13, 5, 6616, 0, 0, -1), (748, 17, 20, 6630, 0, 0, 1), (749, 9, 11, 6633, 0, 0, 1), (750, 10, 3, 6649, 0, 0, -1), (751, 8, 3, 6649, 0, 0, -1), (752, 0, 10, 6652, 0, 0, 1), (753, 15, 4, 6657, 0, 0, -1), (754, 8, 13, 6664, 0, 0, 1), (755, 7, 3, 6667, 0, 0, -1), (756, 0, 8, 6680, 0, 0, 1), (757, 17, 13, 6691, 0, 0, -1), (758, 20, 12, 6693, 0, 0, -1), (759, 19, 5, 6712, 0, 0, -1), (760, 7, 19, 6716, 0, 0, 1), (761, 2, 3, 6717, 0, 0, 1), (762, 17, 13, 6728, 0, 0, -1), (763, 11, 3, 6746, 0, 0, -1), (764, 10, 0, 6751, 0, 0, -1), (765, 4, 1, 6759, 0, 0, -1), (766, 1, 7, 6771, 0, 0, 1), (767, 20, 10, 6780, 0, 0, -1), (768, 8, 19, 6781, 0, 0, 1), (769, 2, 11, 6781, 0, 0, 1), (770, 13, 8, 6787, 0, 0, -1), (771, 12, 2, 6801, 0, 0, -1), (772, 4, 14, 6806, 0, 0, 1), (773, 12, 9, 6818, 0, 0, -1), (774, 8, 16, 6843, 0, 0, 1), (775, 0, 14, 6845, 0, 0, 1), (776, 5, 0, 6849, 0, 0, -1), (777, 20, 3, 6853, 0, 0, -1), (778, 7, 4, 6873, 0, 0, -1), (779, 2, 11, 6878, 0, 0, 1), (780, 10, 4, 6882, 0, 0, -1), (781, 7, 8, 6889, 0, 0, 1), (782, 0, 14, 6899, 0, 0, 1), (783, 15, 0, 6904, 0, 0, -1), (784, 7, 0, 6913, 0, 0, -1), (785, 1, 11, 6925, 0, 0, 1), (786, 4, 5, 6929, 0, 0, 1), (787, 1, 0, 6945, 0, 0, -1), (788, 2, 19, 6945, 0, 0, 1), (789, 12, 17, 6958, 0, 0, 1), (790, 7, 9, 6968, 0, 0, 1), (791, 12, 16, 6969, 0, 0, 1), (792, 14, 18, 6970, 0, 0, 1), (793, 19, 17, 6971, 0, 0, -1), (794, 0, 17, 6977, 0, 0, 1), (795, 4, 18, 6979, 0, 0, 1), (796, 9, 2, 6981, 0, 0, -1), (797, 6, 5, 6985, 0, 0, -1), (798, 19, 1, 6987, 0, 0, -1), (799, 17, 18, 6992, 0, 0, 1), (800, 4, 19, 7015, 0, 0, 1), (801, 2, 17, 7027, 0, 0, 1), (802, 13, 0, 7047, 0, 0, -1), (803, 0, 5, 7049, 0, 0, 1), (804, 13, 0, 7062, 0, 0, -1), (805, 17, 2, 7071, 0, 0, -1), (806, 11, 7, 7084, 0, 0, -1), (807, 18, 10, 7111, 0, 0, -1), (808, 3, 5, 7115, 0, 0, 1), (809, 7, 15, 7116, 0, 0, 1), (810, 0, 17, 7120, 0, 0, 1), (811, 8, 11, 7129, 0, 0, 1), (812, 12, 0, 7129, 0, 0, -1), (813, 7, 3, 7145, 0, 0, -1), (814, 3, 4, 7155, 0, 0, 1), (815, 0, 4, 7176, 0, 0, 1), (816, 13, 9, 7177, 0, 0, -1), (817, 19, 5, 7181, 0, 0, -1), (818, 14, 12, 7185, 0, 0, -1), (819, 12, 3, 7189, 0, 0, -1), (820, 10, 20, 7192, 0, 0, 1), (821, 3, 2, 7194, 0, 0, -1)]
time = []
for i in range(1):
    num_floors = 40
    current_floors = [16, 4, 10, 6]
    passenger_limit = 8
    current_timestamp = 0
    elevator = FourLiftSystem(
                    current_floors=current_floors,
                    num_floors=num_floors,
                    filepath="dummy",
                    passenger_limit=passenger_limit,
                    current_time=current_timestamp
                )

    elevator.run_simulation(passenger_data=data)
    time.append(elevator.current_time)
    
print(sum(time)/20)
print(elevator.orders_done)