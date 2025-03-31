import logging
import gc
from datetime import datetime
from passenger_order import PassengerDataGenerator
from data_extracting_and_graphing_new import DataExtractingAndGraphing
import time
import sys
import random

from fourliftsystem import FourLiftSystem

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

def generate_and_process_data(l, file_path, duration, current_floors, passenger_limit, num_floors, current_timestamp=0):

    order_done = []

    logging.basicConfig(level=logging.DEBUG, filename='simulation_debug.log', filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        logging.info("Simulation started.")

        # Generate passenger data
        generator = PassengerDataGenerator(
            number_of_floors=num_floors,
            file_path=file_path,
            current_time=current_timestamp,
            lambda_passenger_per_floor=l
        )
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
        permission = input("Do you want to continue for four lifts?\n")
        if permission.lower() == "yes":
            elevator = FourLiftSystem(
                current_floors=current_floors,
                num_floors=num_floors,
                filepath=file_path,
                passenger_limit=passenger_limit,
                current_time=current_timestamp
            )
        else:
            print("Program terminated. Exiting...")
            sys.exit()

        # Run the simulation for four lifts
        logging.debug("Running simulation.")
        elevator.run_simulation(passenger_data=data)
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

def run_multiple_scenarios():
    # Scenarios for different traffic levels and number of floors
    traffic_levels = {
        # "low_traffic": {20: [0.000001] + [0.000005] * 20},
        # "moderate_traffic": {20: [0.005] + [0.002] * 20},
        "high_traffic": {  20: [0.01] + [0.005
                                         ] * 20 }
    }

    durations = {
        20: 7200  # 2 hours
    }

    passenger_limits = {
        20: 8
    }

    # Iterate over each traffic level
    for traffic_level, floor_configs in traffic_levels.items():
        time.sleep(1)
        for num_floors, l in floor_configs.items():
            time.sleep(1)
            scenario_name = f"{traffic_level}_{num_floors}"
            duration = durations[num_floors]
            passenger_limit = passenger_limits[num_floors]

            file_path = f"Graphs/{scenario_name}_passenger_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

            current_floors = [random.randint(0, num_floors) for _ in range(4)]  # Initial positions of four lifts
            print(current_floors)
            # Run the simulation
            order_done = generate_and_process_data(
                l=l,
                file_path=file_path,
                duration=duration,
                current_floors=current_floors,
                passenger_limit=passenger_limit,
                num_floors=num_floors,
                current_timestamp=0
            )

            # Save and visualize data
            csv_file_name = f"Graphs/FourLift_{scenario_name}_updated_passenger_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            data_visualizer = DataExtractingAndGraphing(
                csv_file_name=csv_file_name,
                completed_data=order_done,
                num_of_floors=len(l) - 1
            )
            data_visualizer.extract_and_save_data()
            data_visualizer.plot_data()

# Main execution
run_multiple_scenarios()
