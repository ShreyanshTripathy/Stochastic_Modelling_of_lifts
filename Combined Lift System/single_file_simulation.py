import logging
import gc
from datetime import datetime
from data_extracting_and_graphing import DataExtractingAndGraphing
import time
import sys
import random

from  single_lift_brain_with_limited_passengers import Elevator_varied_passenger_arrival_time
from Oscillation import DualOscillation
from Dual_system import DualLiftSystem

from Dual_system_adaptive import DualLiftSystemAdaptive

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

def generate_and_process_data(l, file_path,duration,current_floor_A_Oscillation,current_floor_A,current_floor_B,current_floor_B_Oscillation,passenger_limit,num_floors,system,T_high_oscillation,T_low_oscillation,current_density,delta_time,T_high_VIP,T_low_VIP,current_floor=0,current_timestamp=0):
    
    order_done_1=[]
    order_done_2=[]
    order_done_3=[]
    order_done_4=[]
    
    logging.basicConfig(level=logging.DEBUG, filename='simulation_debug.log', filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        logging.info("Simulation started.")
        
        # Read passenger data
        logging.debug("Reading passenger data.")
        data = read_passenger_data(file_path)
        # print(data)
        
        if not data:
            logging.warning("No data read from file.")
        else:
            logging.debug(f"Data read from file: {data}")
        
        # Initialize elevator simulation
        logging.debug("Initializing elevator simulation.")
        if system == "s":
            # input("YES")
            elevator_1 = Elevator_varied_passenger_arrival_time(num_floors=num_floors, current_time=current_timestamp, current_floor=current_floor,filepath=file_path,Passenger_limit=passenger_limit)

                
            # Run the simulation for single lift
            logging.debug("Running simulation.")
            elevator_1.run_simulation(passenger_data=data)        
            current_timestamp = elevator_1.current_time
            order_done_1.append(elevator_1.orders_done)
            print(order_done_1)
            del elevator_1
        if system == "o":
            elevator_2 = DualOscillation(current_floor_A=current_floor_A_Oscillation,current_floor_B=current_floor_B_Oscillation,num_floors=num_floors,filepath=file_path,Passenger_limit=passenger_limit,current_time=current_timestamp)

            elevator_2.run_simulation(passenger_data=data)
            current_timestamp = elevator_2.current_time
            order_done_2.append(elevator_2.orders_done)
            del elevator_2

        if system == "d":
            elevator_3 = DualLiftSystem(current_floor_A=current_floor_A,current_floor_B=current_floor_B,num_floors=num_floors,filepath=file_path,Passenger_limit=passenger_limit,current_time=current_timestamp)
            elevator_3.run_simulation(passenger_data=data)
            current_timestamp = elevator_3.current_time
            order_done_3.append(elevator_3.orders_done)
            del elevator_3
        
        if system == "a":
            elevator_4 = DualLiftSystemAdaptive(
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
            current_time=0
        )
            elevator_4.run_simulation(passenger_data=data)
            current_timestamp = elevator_4.current_time
            order_done_4.append(elevator_4.orders_done)
            del elevator_4
            
        
        
        data.clear()
        
        logging.debug("Simulation completed.")
        logging.info("Simulation completed successfully.")
        del data
        gc.collect()
        
    except Exception as e:
        logging.error(f"Error during simulation: {e}", exc_info=True)

    return order_done_1, order_done_2, order_done_3, order_done_4


def run_multiple_scenarios(system):
    # Scenarios for different traffic levels and number of floors
    traffic_levels = {
        # "low_traffic": {
        #     # 5: [0.001] + [0.0001] * 5,   # Ground floor higher than others
        #     # 20: [0.0003] + [0.00015] * 20,
        #     # 40: [0.002] + [0.0004] * 40
        # },
        # "moderate_traffic": {
        #     # 5: [0.01] + [0.005]*5,
        #     # 20: [0.05] + [0.0001] * 20,
        #     # 40: [0.004] + [0.0009] * 40
        # },
        "high_traffic": {
            # 5: [0.03] + [0.008]*5,
            # 20: [0.008] + [0.004] * 20,
            40: [0.03] + [0.0001] * 40
        }
    }
    
    durations = {
        # 5: 3600,   # 1 hour
        # 20: 7200,  # 2 hours
        40: 14400  # 4 hours
        # 40:36000
    }
    
    passenger_limits = {
        # 5: 8,
        # 20: 8,
        40: 8
    }

    # Iterate over each traffic level
    for traffic_level, floor_configs in traffic_levels.items():
        time.sleep(1)
        for num_floors, l in floor_configs.items():
            time.sleep(1)
            scenario_name = f"{traffic_level}_{num_floors}"
            duration = durations[num_floors]
            passenger_limit = passenger_limits[num_floors]
                      
            if num_floors == 5:
                first_directory = "5_floor"
            elif num_floors == 20:
                first_directory = "20_floor"
            elif num_floors == 40:
                first_directory = "40_floor"
                
            if traffic_level == "low_traffic":
                second_directory = "low"
            elif traffic_level == "moderate_traffic":
                second_directory = "moderate"
            elif traffic_level == "high_traffic":
                second_directory = "high"
            
            if system == "d":
                third_directory = "dual"
            elif system == "o":
                third_directory = "oscillation"
            elif system == "s":
                third_directory = "single"
            elif system == "a":
                third_directory = "Adaptive"
            
           
            current_density = [0]*(num_floors+1)
            delta_time = 10
            
            if num_floors==5:
                T_high_oscillation = 0.8
                T_low_oscillation = 0
                T_high_VIP = 2
                T_low_VIP = 1.25
            elif num_floors==20:
                T_high_VIP = 0.5
                T_low_VIP = 0.25
            elif num_floors==40:
                T_high_VIP = 0.25
                T_low_VIP = 0.1
            
            file_path = f"Graphs/{first_directory}/{second_directory}/{third_directory}/{scenario_name}passenger_data{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"


            current_floor_A = random.randint(0,num_floors)
            current_floor_B = random.randint(0,num_floors)
            
            # Run the simulation
            order_done_1, order_done_2,order_done_3, order_done_4= generate_and_process_data(l=l,file_path=file_path,duration=duration,current_floor_A_Oscillation=0,current_floor_B_Oscillation=num_floors,current_floor_A=current_floor_A,current_floor_B=current_floor_B,current_floor=random.randint(0,num_floors),passenger_limit=passenger_limit,num_floors=num_floors,system=system, current_timestamp=0, T_high_oscillation=T_high_oscillation,T_low_oscillation=T_low_oscillation, current_density=current_density,delta_time=delta_time,T_high_VIP=T_high_VIP,T_low_VIP=T_low_VIP)
            
            # print(order_done_1)
            # Save and visualize data
            order = None
        
            if order_done_1:
                order = order_done_1
            elif order_done_2:
                order = order_done_2
            elif order_done_3:
                order = order_done_3
            elif order_done_4:
                order = order_done_4
            else:
                sys.exit()
            csv_file_name = f"Graphs/{first_directory}/{second_directory}/{third_directory}/{third_directory}_{scenario_name}updated_passenger_data{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            data_visualizer = DataExtractingAndGraphing(csv_file_name=csv_file_name, completed_data=order, num_of_floors=len(l) - 1,traffic_level=second_directory, floor_directory=first_directory,system_type=third_directory)
            data_visualizer.extract_and_save_data()
            data_visualizer.plot_data()
            time.sleep(3)

# Main execution
run_multiple_scenarios(system = "s")
time.sleep(1)
run_multiple_scenarios(system = "d")
time.sleep(1)
run_multiple_scenarios(system = "o")
time.sleep(1)
run_multiple_scenarios(system = "a")