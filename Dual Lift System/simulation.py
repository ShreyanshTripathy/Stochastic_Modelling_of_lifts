import logging
import gc
from datetime import datetime
# from Dual_system import DualLiftSystem
from trial import DualLiftSystem
from passenger_order import PassengerDataGenerator
from data_extracting_and_graphing import DataExtractingAndGraphing
import sys
import time

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

def generate_and_process_data(l, file_path,duration,current_floor_A, current_floor_B, passenger_limit,num_floors,current_timestamp=0,order_done=[]):
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
        
        if not data:
            logging.warning("No data read from file.")
        else:
            logging.debug(f"Data read from file: {data}")
        
        # Initialize elevator simulation
        logging.debug("Initializing elevator simulation.")
        permission = "yes"
        if permission == "yes":
            # elevator = DualLiftSystem(passenger_data=data,current_floor_A=current_floor_A,current_floor_B=current_floor_B,num_floors=num_floors,filepath=file_path,Passenger_limit=passenger_limit,current_time=current_timestamp)
            elevator = DualLiftSystem(current_floor_A=current_floor_A,current_floor_B=current_floor_B,num_floors=num_floors,filepath=file_path,Passenger_limit=passenger_limit,current_time=current_timestamp)
        else:
            print("Program terminated. Exiting...")
            sys.exit()
            
          
        # Run the simulation
        logging.debug("Running simulation.")
        elevator.run_simulation(passenger_data=data)
        # elevator.run_simulation()
        current_timestamp = elevator.current_time
        order_done.append(elevator.orders_done)
        data.clear()
        
        logging.debug("Simulation completed.")
        logging.info("Simulation completed successfully.")
        
        # Explicit resource cleanup
        del elevator
        del data
        gc.collect()
        
    except Exception as e:
        logging.error(f"Error during simulation: {e}", exc_info=True)

    return order_done


# Main execution
def run_multiple_scenarios():
    # Scenarios for different traffic levels and number of floors
    '''
    traffic_levels = {
        "low_traffic": {
            5: [0.01] + [0.002] * 5,   # Ground floor higher than others
            # 20: [0.005] + [0.001] * 20,
            # 40: [0.0025] + [0.0005] * 40
        },
        "moderate_traffic": {
            5: [0.02] + [0.005, 0.007, 0.005, 0.003, 0.004],
            # 20: [0.015] + [0.008] * 20,
            # 40: [0.01] + [0.004] * 40
        },
        "high_traffic": {
            5: [0.05] + [0.03, 0.02, 0.015, 0.02, 0.01],
            # 20: [0.03] + [0.02] * 20,
            # 40: [0.02] + [0.01] * 40
        }
    }
    '''
    traffic_levels = {
        "low_traffic": {
            # 5: [0.005] + [0.0002] * 5,   # Ground floor higher than others
            20: [0.00001] + [0.00005] * 20,
            # 40: [0.002] + [0.0004] * 40
        },
        "moderate_traffic": {
            # 5: [0.01] + [0.005]*5,
            # 20: [0.001] + [0.0007] * 20,
            # 40: [0.004] + [0.0009] * 40
        },
        "high_traffic": {
            # 5: [0.03] + [0.008]*5,
            # 20: [0.008] + [0.003] * 20,
            # 40: [0.01] + [0.003] * 40
        }
    }
    
    durations = {
        # 5: 3600,   # 1 hour
        # 20: 7200,  # 2 hours
        # 40: 14400  # 4 hours
        20:30
    }
    
    passenger_limits = {
        # 5: 8,
        20: 8,
        # 40: 8
    }

    # Iterate over each traffic level
    for traffic_level, floor_configs in traffic_levels.items():
        time.sleep(3)
        for num_floors, l in floor_configs.items():
            time.sleep(3)
            scenario_name = f"{traffic_level}_{num_floors}"
            duration = durations[num_floors]
            passenger_limit = passenger_limits[num_floors]
            
            file_path = f"{scenario_name}passenger_data{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

            
            print(l)
            print(num_floors)
            print(duration)
            # Run the simulation
            order_done = generate_and_process_data(current_floor_A=0,current_floor_B=0, num_floors=num_floors, passenger_limit=passenger_limit, duration=duration, file_path = file_path,l=l)
            
            # Save and visualize data
            csv_file_name = f"Graphs/{scenario_name}updated_passenger_data{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            data_visualizer = DataExtractingAndGraphing(csv_file_name=csv_file_name, completed_data=order_done, num_of_floors=len(l) - 1)
            data_visualizer.extract_and_save_data()
            data_visualizer.plot_data()


# Main execution
run_multiple_scenarios()
