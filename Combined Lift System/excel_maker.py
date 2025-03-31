import os
import re
import openpyxl

def extract_data_from_txt(file_path):
    """Extract specific data fields from a given text file."""
    data = {
        "System used": None,
        "Number of floors": None,
        "Traffic": None,
        "Mean Waiting Time": None,
        "Mean Service Time": None,
        "Number of passengers": None
    }

    try:
        with open(file_path, 'r') as file:
            waiting_time_section = False
            service_time_section = False

            for line in file:
                # Extract 'System used'
                if line.startswith("System used:"):
                    data["System used"] = line.split(":", 1)[1].strip()

                # Extract 'Number of floors'
                elif line.startswith("Number of floors:"):
                    data["Number of floors"] = int(line.split(":", 1)[1].strip())
                elif line.startswith("Number of passengers:"):
                    data["Number of passengers"] = int(line.split(":", 1)[1].strip())

                # Extract 'Traffic'
                elif line.startswith("traffic:"):
                    data["Traffic"] = line.split(":", 1)[1].strip()

                # Detect context for stats sections
                elif "Waiting Time Statistics:" in line:
                    waiting_time_section = True
                    service_time_section = False

                elif "Total Service Time Statistics:" in line:
                    waiting_time_section = False
                    service_time_section = True

                # Extract 'Mean Waiting Time' and 'Mean Service Time'
                elif line.startswith("Mean:"):
                    mean_value = float(line.split(":", 1)[1].strip())
                    mean_value = round(mean_value, 2)  # Limit to two decimal places
                    if waiting_time_section:
                        data["Mean Waiting Time"] = mean_value
                    elif service_time_section:
                        data["Mean Service Time"] = mean_value

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")

    return data

def process_folder(folder_path, output_excel):
    """Process all text files in the folder and save extracted data to an Excel file."""
    results = []

    # Loop through each file in the folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".txt"):
            file_path = os.path.join(folder_path, file_name)
            data = extract_data_from_txt(file_path)
            results.append(data)

    # Write results to an Excel file
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Extracted Data"

    # Write header row
    headers = ["System used", "Number of floors", "Traffic", "Mean Waiting Time", "Mean Service Time", "Number of people"]
    sheet.append(headers)

    # Write data rows
    for result in results:
        row = [
            result["System used"],
            result["Number of floors"],
            result["Traffic"],
            result["Mean Waiting Time"],
            result["Mean Service Time"],
            result["Number of passengers"]
        ]
        sheet.append(row)

    workbook.save(output_excel)
    print(f"Data extraction completed. Results saved to {output_excel}.")

# Example usage
folder_path = "notepads\Single lift mod traffic"
output_excel = f"{folder_path}\output.xlsx"
process_folder(folder_path, output_excel)
