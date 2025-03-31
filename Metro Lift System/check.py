import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import expon, poisson, kstest, chisquare

file_name = "passenger_data.csv"  # Update this with the correct file name
df = pd.read_csv(file_name)

# Sort the data by passenger position and arrival time
df_sorted = df.sort_values(by=['Passenger position', 'Passenger arrival time'])

# Compute interarrival times for each floor
df_sorted['Interarrival Time'] = df_sorted.groupby('Passenger position')['Passenger arrival time'].diff()

# Drop rows with NaN (first arrival on each floor has no interarrival time)
df_interarrival = df_sorted.dropna()

# Function to plot interarrival time histogram and fit exponential distribution
def analyze_interarrival_times(data):
    interarrival_times = data['Interarrival Time']
    
    # Plot histogram
    plt.hist(interarrival_times, bins=20, density=True, alpha=0.7, color='blue', label='Data')
    
    # Fit exponential distribution
    lambda_est = 1 / interarrival_times.mean()
    x = np.linspace(0, interarrival_times.max(), 100)
    pdf = lambda_est * np.exp(-lambda_est * x)
    plt.plot(x, pdf, 'r-', label=f'Exp Fit (λ={lambda_est:.2f})')
    
    # Display plot
    plt.xlabel('Interarrival Time')
    plt.ylabel('Density')
    plt.title('Interarrival Times and Exponential Fit')
    plt.legend()
    plt.show()

    # Perform Kolmogorov-Smirnov test
    ks_stat, ks_p = kstest(interarrival_times, 'expon', args=(0, 1 / lambda_est))
    print(f"Kolmogorov-Smirnov Test for Exponential Fit:\nStat: {ks_stat:.4f}, p-value: {ks_p:.4f}")

# Analyze interarrival times for each floor
for floor in df_sorted['Passenger position'].unique():
    print(f"\n=== Analyzing Floor {floor} ===")
    floor_data = df_interarrival[df_interarrival['Passenger position'] == floor]
    if len(floor_data) > 1:
        analyze_interarrival_times(floor_data)
    else:
        print(f"Not enough data for floor {floor} to analyze interarrival times.")

# Analyze passenger counts in fixed time intervals
# Create time bins
time_bins = np.arange(df['Passenger arrival time'].min(), df['Passenger arrival time'].max() + 2, 1)
df['Time Bin'] = pd.cut(df['Passenger arrival time'], bins=time_bins, labels=time_bins[:-1])

# Count arrivals per time bin for each floor
arrival_counts = df.groupby(['Passenger position', 'Time Bin']).size().reset_index(name='Counts')

# Function to analyze and plot arrival counts
def analyze_arrival_counts(data, floor):
    counts = data['Counts']
    
    # Plot histogram of arrival counts
    plt.hist(counts, bins=range(0, counts.max() + 2), alpha=0.7, color='green', label='Data')
    
    # Fit Poisson distribution
    lambda_est = counts.mean()
    x = np.arange(0, counts.max() + 1)
    pmf = poisson.pmf(x, lambda_est)
    plt.plot(x, pmf * len(counts), 'r-', label=f'Poisson Fit (λ={lambda_est:.2f})')
    
    # Display plot
    plt.xlabel('Arrival Count')
    plt.ylabel('Frequency')
    plt.title(f'Arrival Counts on Floor {floor} and Poisson Fit')
    plt.legend()
    plt.show()

    # Perform Chi-Square goodness-of-fit test
    observed = np.histogram(counts, bins=range(0, counts.max() + 2))[0]
    expected = len(counts) * poisson.pmf(np.arange(len(observed)), lambda_est)
    chi_stat, chi_p = chisquare(f_obs=observed, f_exp=expected)
    print(f"Chi-Square Test for Poisson Fit:\nStat: {chi_stat:.4f}, p-value: {chi_p:.4f}")

# Analyze arrival counts for each floor
for floor in df['Passenger position'].unique():
    print(f"\n=== Analyzing Arrival Counts for Floor {floor} ===")
    floor_data = arrival_counts[arrival_counts['Passenger position'] == floor]
    if len(floor_data) > 1:
        analyze_arrival_counts(floor_data, floor)
    else:
        print(f"Not enough data for floor {floor} to analyze arrival counts.")
