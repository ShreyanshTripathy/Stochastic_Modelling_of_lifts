import logging
import gc
from datetime import datetime
from passenger_order import PassengerDataGenerator
from data_extracting_and_graphing import DataExtractingAndGraphing
import time
import sys
import random

from  single_lift_brain_with_limited_passengers import Elevator_varied_passenger_arrival_time
from Oscillation import DualOscillation
from Dual_system import DualLiftSystem
from Nliftsystem import NLiftSystem
from fourliftsystem import FourLiftSystem
from VIPdualsystemnotadaptive import VIPDualSystemNotAdaptive
from single_file_simulation import DualLiftSystemAdaptive

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

def generate_and_process_data(l, file_path,duration,current_floor_A_Oscillation,current_floor_A,current_floor_B,current_floor_B_Oscillation,passenger_limit,num_floors,system,T_high_oscillation,T_low_oscillation,current_density,delta_time,T_high_VIP,T_low_VIP,passenger_inout,floor_time,floor_time_oscillation,N_lift_floor,Quad_floors,VIP_floor,current_floor=0,current_timestamp=0):
    
    order_done_1=[]
    order_done_2=[]
    order_done_3=[]
    order_done_4=[]
    order_done_5=[]
    order_done_6=[]
    order_done_7=[]
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
        # print(data)
        
        if not data:
            logging.warning("No data read from file.")
        else:
            logging.debug(f"Data read from file: {data}")
        # sys.exit()
        # Initialize elevator simulation
        logging.debug("Initializing elevator simulation.")
        if system == "s":
            # input("YES")
            Single_lift = Elevator_varied_passenger_arrival_time(num_floors=num_floors, current_time=current_timestamp, current_floor=current_floor,filepath=file_path,Passenger_limit=passenger_limit, floor_time=floor_time,passenger_inout=passenger_inout)
            # Run the simulation for single lift
            logging.debug("Running simulation.")
            Single_lift.run_simulation(passenger_data=data)        
            current_timestamp = Single_lift.current_time
            order_done_1.append(Single_lift.orders_done)
            #print(order_done_1)
            del Single_lift
        if system == "o":
            Metro_lift = DualOscillation(current_floor_A=current_floor_A_Oscillation,current_floor_B=current_floor_B_Oscillation,num_floors=num_floors,filepath=file_path,Passenger_limit=passenger_limit,current_time=current_timestamp,floor_time=floor_time_oscillation)

            Metro_lift.run_simulation(passenger_data=data)
            current_timestamp = Metro_lift.current_time
            order_done_2.append(Metro_lift.orders_done)
            del Metro_lift

        if system == "d":
            Dual_lift = DualLiftSystem(current_floor_A=current_floor_A,current_floor_B=current_floor_B,num_floors=num_floors,filepath=file_path,Passenger_limit=passenger_limit,current_time=current_timestamp,floor_time = floor_time,passenger_inout=passenger_inout)
            Dual_lift.run_simulation(passenger_data=data)
            current_timestamp = Dual_lift.current_time
            order_done_3.append(Dual_lift.orders_done)
            del Dual_lift
        
        if system == "a":
            
            Adaptive_lift = DualLiftSystemAdaptive(
            current_floor_A, current_floor_B, num_floors, file_path,
            passenger_limit, floor_time, delta_time,
            T_high_oscillation=T_high_oscillation, T_low_oscillation=T_low_oscillation,
            T_high_VIP=T_high_VIP, T_low_VIP=T_low_VIP, floor_time_oscillation=floor_time_oscillation
            )
        
            Adaptive_lift.run_simulation(data)
            current_timestamp = Adaptive_lift.current_time
            order_done_4.append(Adaptive_lift.orders_done)
            del Adaptive_lift
            
        if system == "N":
            number_of_lifts = len(N_lift_floor)
            N_lift = NLiftSystem(
                current_floors=N_lift_floor,
                num_floors=num_floors,
                filepath=file_path,
                passenger_limit=passenger_limit,
                number_of_lifts=number_of_lifts,
                current_time=current_timestamp
            )
            N_lift.run_simulation(passenger_data=data)
            current_timestamp = N_lift.current_time
            order_done_5.append(N_lift.orders_done)
            del N_lift
            
        if system == "Q":
            Quad_lift = FourLiftSystem(
                current_floors=Quad_floors,
                num_floors=num_floors,
                filepath=file_path,
                passenger_limit=passenger_limit,
                current_time=current_timestamp
            )
            Quad_lift.run_simulation(passenger_data=data)
            current_timestamp = Quad_lift.current_time
            order_done_6.append(Quad_lift.orders_done)
            del Quad_lift
        if system == "V":
            VIP_lift = VIPDualSystemNotAdaptive(current_floor_A=current_floor_A,current_floor_B=current_floor_B,num_floors=num_floors,filepath=file_path,Passenger_limit=passenger_limit,floor_to_serve=VIP_floor ,current_time=current_timestamp)
            VIP_lift.run_simulation(passenger_data=data)
            current_timestamp = VIP_lift.current_time
            order_done_7.append(VIP_lift.orders_done)
            del VIP_lift
            
        
        
        data.clear()
        
        logging.debug("Simulation completed.")
        logging.info("Simulation completed successfully.")
        del data
        gc.collect()
        
    except Exception as e:
        logging.error(f"Error during simulation: {e}", exc_info=True)

    return order_done_1, order_done_2, order_done_3, order_done_4, order_done_5, order_done_6, order_done_7


def run_multiple_scenarios(system, iteration):
    # Scenarios for different traffic levels and number of floors
    traffic_levels = {
        "low_traffic": {
            5: [0.002] + [0.002] * 5,  
            20: [0.0015] + [0.0015] * 20,
            40: [0.001] + [0.001] * 40
        },
        "moderate_traffic": {
            5: [0.006] + [0.006]*5,
            20: [0.0035] + [0.0035] * 20,
            40: [0.003] + [0.003] * 40 #500
        },
        "high_traffic": {
            5: [0.015] + [0.015]*5,
            20: [0.0080] + [0.0080] * 20, # 600
            40: [0.0062] + [0.0062] * 40 #1000
        }
    }
    
    durations = {
        5: 3600,   # 1 hour
        20: 3600,  # 1 hours
        40: 3600  # 1 hours
        
    }
    
    passenger_limits = {
        5: 8,
        20: 8,
        40: 8
    }
   
    # Iterate over each traffic level
    for traffic_level, floor_configs in traffic_levels.items():
        time.sleep(1)
        N_current_floors = []
        Quad_current_floors = []
        VIP_floor = None
        for num_floors, l in floor_configs.items():
            time.sleep(1)
            scenario_name = f"{traffic_level}_{num_floors}"
            duration = durations[num_floors]
            passenger_limit = passenger_limits[num_floors]\
            
                      
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
            elif system=="N":
                third_directory = "N_lift"
                number_of_lifts = 8
                N_current_floors = [random.randint(0, num_floors) for _ in range(number_of_lifts)]
            elif system =="Q":
                third_directory = "Quad_lift"
                Quad_current_floors = [random.randint(0,num_floors) for _ in range(4)]
            elif system =="V":
                third_directory = "VIP_lift"
                VIP_floor = 0
            
            # T_high_oscillation = 0.8
            # T_low_oscillation = 0.7 
            current_density = [0]*(num_floors+1)
            delta_time = 5
            
            if num_floors==5:
                T_high_oscillation = 0.06
                T_low_oscillation = 0.03
                T_high_VIP = 1
                T_low_VIP = 0.5
            elif num_floors==20:
                T_high_VIP = 1
                T_low_VIP = 0.5
                T_high_oscillation = 0.05
                T_low_oscillation = 0.04
            elif num_floors==40:
                T_high_VIP = 0.2
                T_low_VIP = 1.0
                T_high_oscillation = 0.06
                T_low_oscillation = 0.04
            passenger_inout = 3
            floor_time = 1
            floor_time_oscillation=4
            
            file_path = f"Graphs/{first_directory}/{second_directory}/{third_directory}/{scenario_name}passenger_data{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

            current_floor_A = random.randint(0,num_floors)
            current_floor_B = random.randint(0,num_floors)
            
            
            # Run the simulation
            order_done_1, order_done_2,order_done_3, order_done_4,order_done_5, order_done_6,order_done_7= generate_and_process_data(
                l=l,
                file_path=file_path,
                duration=duration,
                current_floor_A_Oscillation=0,
                current_floor_B_Oscillation=num_floors,
                current_floor_A=current_floor_A,
                current_floor_B=current_floor_B,
                current_floor=random.randint(0,num_floors),
                passenger_limit=passenger_limit,
                num_floors=num_floors,
                system=system,
                current_timestamp=0,
                T_high_oscillation=T_high_oscillation,
                T_low_oscillation=T_low_oscillation,
                current_density=current_density,
                delta_time=delta_time,
                T_high_VIP=T_high_VIP,
                T_low_VIP=T_low_VIP,
                passenger_inout=passenger_inout,
                floor_time=floor_time,
                floor_time_oscillation=floor_time_oscillation,
                N_lift_floor=N_current_floors,
                Quad_floors = Quad_current_floors,
                VIP_floor=VIP_floor)
            
            order = None
        
            if order_done_1:
                order = order_done_1
            elif order_done_2:
                order = order_done_2
            elif order_done_3:
                order = order_done_3
            elif order_done_4:
                order = order_done_4
            elif order_done_5:
                order = order_done_5
            elif order_done_6:
                order = order_done_6
            elif order_done_7:
                order = order_done_7
            else:
                print("You have not returned the completed orders")
                sys.exit()
            csv_file_name = f"Graphs/{first_directory}/{second_directory}/{third_directory}/{third_directory}_{scenario_name}updated_passenger_data{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            data_visualizer = DataExtractingAndGraphing(csv_file_name=csv_file_name,iteration=iteration, completed_data=order, num_of_floors=len(l) - 1,traffic_level=second_directory, floor_directory=first_directory,system_type=third_directory)
            data_visualizer.extract_and_save_data()
            data_visualizer.plot_data()
            time.sleep(1)

# Main execution
# single lift system
# for i in range(100):
#     run_multiple_scenarios(system = "s", iteration=i)

# dual lift system
# for i in range(100):
#     run_multiple_scenarios(system = "d", iteration=i)
#     print(i)
# time.sleep(1)

# # oscillation lift system
# for i in range(100):
#     run_multiple_scenarios(system = "o", iteration= i)
    # time.sleep(1)


# # adaptive lift system
# for i in range(60,100):
#     run_multiple_scenarios(system = "a", iteration=i)
#     time.sleep(1)

# #VIP lift system
# run_multiple_scenarios(system="V")

# Quad lift system
# for i in range(100):
#     run_multiple_scenarios(system="Q", iteration = i)
#     time.sleep(1)

# N lift system
for i in range(100):
    run_multiple_scenarios(system="N", iteration=i)
#     time.sleep(1)
print("Simulation done")