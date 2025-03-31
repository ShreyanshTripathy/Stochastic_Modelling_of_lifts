 Four-Lift System Simulation

  Overview

The Four-Lift System Simulation is a Python-based elevator control system designed to optimize the assignment of passengers to lifts in a multi-floor building. The simulation ensures efficient passenger pick-up and drop-off while avoiding issues like duplicate assignments and direction conflicts.

  Key Features

- Passenger Assignment Passengers are assigned based on their current floor, destination, and lift availability.
- Lift Movement Optimization: Each lift operates based on direction, pending requests, and passenger destinations.
- Customizable Parameters: Number of floors, lift capacity, and passenger data can be adjusted.

Project Structure


- four_lift_system.py (Core logic of the simulation)
- passenger_order.py (responsible for Passenger generation)
- data_extraction_and_graphing (Program to visualise and graph the data given by the simulation)
- simulation.py (brings the abpve three codes together)
- README.md (This documentation)


  Usage Example

python
current_floors = [0, 1, 2, 3]
num_floors = 20
passenger_limit = 8
current_timestamp = 0

elevator = FourLiftSystem(
    current_floors=current_floors,
    num_floors=num_floors,
    filepath="dummy.csv",
    passenger_limit=passenger_limit,
    current_time=current_timestamp
)

data = [(1, 0, 18, 0, 0, 0, 1), (2, 1, 15, 0, 0, 0, 1)]

elevator.run_simulation(passenger_data=data)


  Key Functions

- __init__(self, current_floors, num_floors, filepath, passenger_limit, current_time=0): Initialize the lift system with configuration parameters.

- move(lift_name): Move a specific lift based on direction.

- remove_duplicates(not_assigned): Remove duplicates from pending_orders and not_assigned.

- assign_passenger_to_lift(lift_name, passenger): Assign a passenger to a specific lift.

- handle_idle_lift(lift_name, passenger): Assign a passenger to an idle lift.

- handle_same_floor_passenger(passenger): Check if a lift on the same floor can pick up a passenger.

- assign_passengers(pending_orders): Main function to assign passengers to lifts.

- reassign_passenger(source_list): Reassign passengers to suitable lifts.

- drop_passenger(order, lift_name): Drop passengers if their destination floor is reached.

- check_direction_conflict(order, copy_list, direction, lift_name): Check for direction conflicts during assignment.

- Passengers_on_same_floor(order, dont_pick, eligible_orders, lift_name): Handle passengers on the same floor.

- pick_passenger(eligible_orders, lift_name, passenger_data): Pick eligible passengers.

- serve_stop(lift_name, passenger_data): Handle passenger pick-up and drop-off at each stop.

- queue_maker(pending_orders, passenger_data, lift_name): Manage passenger queues efficiently.

- run_simulation(passenger_data): Start the lift simulation.


