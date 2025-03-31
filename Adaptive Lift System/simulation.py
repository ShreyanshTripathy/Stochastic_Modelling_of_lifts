import logging
import gc
from datetime import datetime
from passenger_order import PassengerDataGenerator
from data_extracting_and_graphing import DataExtractingAndGraphing
import time
import sys
import random
# from Dual_system_adaptive import DualLiftSystem
from adaptive_lift import DualLiftSystem

'''The plan:
1. Track the number of passenger arriving within a given time frame an identify which floor they are coming on
        This implies that i can use a dictionary which looks like the following:
            Floor = {Totatl number of people:,
                     time passed: ,
                     density: }
2. I need to have threshold density which is responsible for switching to different lift models
3. system and the situation 
Metro Lift System: If the Density on multiple exceeds the threshold and is similar across floor
VIP Lift System: If only one floor has high density while others remain at low density
Single Lift System: If the density on all the floors is very small then we can just use a normal single lift system and save on energy
'''

def read_passenger_data(file_path):
    """Helps to read the CSV file and create the passenger data list"""
    logging.debug(f"Attempting to read passenger data from {file_path}.")
    passenger_data = []
    try:
        with open(file_path, 'r') as file:
            next(file)  # Skip header
            for line in file:
                try:
                    # Parse the CSV line
                    (index, passenger_position, passenger_destination,
                     passenger_arrival_time, Lift_arrival_time,
                     Order_completion_time, direction) = line.strip().split(',')
                    
                    # Convert data types (adjust for possible floats)
                    passenger_data.append((
                        int(index),
                        int(float(passenger_position)),  # Use float() if needed
                        int(float(passenger_destination)),
                        int(float(passenger_arrival_time)),
                        int(float(Lift_arrival_time)),
                        int(float(Order_completion_time)),
                        int(float(direction))
                    ))
                except ValueError as ve:
                    logging.error(f"ValueError parsing line: {line.strip()} | Error: {ve}")
                except Exception as e:
                    logging.error(f"Unexpected error parsing line: {line.strip()} | Error: {e}")
        logging.debug(f"Passenger data read successfully from {file_path}.")
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    except Exception as e:
        logging.error(f"Error reading passenger data from {file_path}: {e}")
    return passenger_data

def generate_and_process_data(l, file_path,duration,current_floor_A,current_floor_B,passenger_limit,num_floors,T_high_oscillation,T_low_oscillation,current_density,delta_time,T_high_VIP,T_low_VIP,floor_time,passenger_inout,floor_time_oscillation,current_timestamp=0):
    
    order_done=[]

    logging.basicConfig(level=logging.DEBUG, filename='simulation_debug.log', filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        logging.info("Simulation started.")
        
        # Generate passenger data
        generator = PassengerDataGenerator(number_of_floors=num_floors,file_path=file_path,current_time=current_timestamp,lambda_passenger_per_floor=l)
        logging.debug("Generating passenger data.")
        generator.generate_passenger_data(duration=duration)
        logging.debug("Passenger data generated.")
        
        # Save passenger data
        
        logging.debug("Saving passenger data.")
        generator.save_data()
        logging.debug("Passenger data saved.")
        
        # Read passenger data
        logging.debug("Reading passenger data.")
        data = read_passenger_data(file_path)
        print(data)
        print(len(data))
        # input("continue")
        if not data:
            logging.warning("No data read from file.")
        else:
            logging.debug(f"Data read from file: {data}")
        
        # Initialize elevator simulation
        logging.debug("Initializing elevator simulation.")

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
            current_time=0,
            floor_time = floor_time,
            passenger_inout = passenger_inout,
            floor_time_oscillation = floor_time_oscillation
        )
                
        # Run the simulation for single lift
        logging.debug("Running simulation.")
        elevator.run_simulation(passenger_data=data)        
        current_timestamp = elevator.current_time
        order_done.append(elevator.orders_done)
        
        data.clear()
        
        logging.debug("Simulation completed.")
        logging.info("Simulation completed successfully.")
        
        # Explicit resource cleanup
        del elevator_3
        del data
        gc.collect()
        
    except Exception as e:
        logging.error(f"Error during simulation: {e}", exc_info=True)

    return order_done


def run_multiple_scenarios():
    # Scenarios for different traffic levels and number of floors
    traffic_levels = {
        "low_traffic": {
            # 5: [0.001] + [0.0001] * 5,   # Ground floor higher than others
            # 5: [0.01]*6
            # 20: [0.0003] + [0.00015] * 20,
            # 40: [0.001] + [0.0004] * 40
        },
        "moderate_traffic": {
            # 5: [0.01] + [0.005]*5,
            # 20: [0.05] + [0.0001] * 20,
            # 40: [0.004] + [0.0009] * 40
        },
        "high_traffic": {
            # 5: [0.03] + [0.008]*5,
            # 20: [0.008] + [0.004] * 20,
            40: [0.1] + [0.0008] * 40
        }
    }
    
    durations = {
        # 5: 36,   # 1 hour
        # 20: 7200,  # 2 hours
        40: 7200  # 4 hours
        # 40:36000
    }
    
    passenger_limits = {
        # 5: 8,
        # 20: 8,
        40: 8
    }

    # Iterate over each traffic level
    for traffic_level, floor_configs in traffic_levels.items():
        # time.sleep(1)
        for num_floors, l in floor_configs.items():
            # time.sleep(1)
            scenario_name = f"{traffic_level}_{num_floors}"
            duration = durations[num_floors]
            passenger_limit = passenger_limits[num_floors]
            
            file_path = f"Graphs/{scenario_name}passenger_data{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            # file_path = f"Graphs/moderate_traffic_20passenger_data20241214002823 copy.csv"

            current_floor_A = random.randint(0,num_floors)
            current_floor_B = random.randint(0,num_floors)
            
            T_high_oscillation = 0.8
            T_low_oscillation = 0.7
            current_density = [0]*(num_floors+1)
            delta_time = 5 
            T_high_VIP = 20
            T_low_VIP = 10
            
            floor_time = 1
            passenger_inout = 3
            floor_time_oscillation = 3
            
            # Run the simulation
            order_done = generate_and_process_data(
                            l=l,        
                            file_path=file_path,
                            duration=duration,
                            current_floor_A=current_floor_A,
                            current_floor_B=current_floor_B,
                            passenger_limit=passenger_limit,
                            num_floors=num_floors,
                            current_timestamp=0, 
                            T_high_oscillation=T_high_oscillation,
                            T_low_oscillation=T_low_oscillation,
                            current_density=current_density,
                            delta_time=delta_time,
                            T_high_VIP=T_high_VIP,
                            T_low_VIP=T_low_VIP,
                            floor_time = floor_time,
                            passenger_inout = passenger_inout,
                            floor_time_oscillation = floor_time_oscillation
                        )

            
            # Save and visualize data
            csv_file_name = f"Graphs/Single_{scenario_name}updated_passenger_data{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            data_visualizer = DataExtractingAndGraphing(csv_file_name=csv_file_name, completed_data=order_done, num_of_floors=len(l) - 1)
            data_visualizer.extract_and_save_data()
            data_visualizer.plot_data()
# Main execution
for i in range(1):
    run_multiple_scenarios()
    time.sleep(0.25)