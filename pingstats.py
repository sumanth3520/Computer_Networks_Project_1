import argparse
import subprocess
import time
import re
import statistics
import json
import matplotlib.pyplot as plt

# Function to run ping command
def run_ping(target, count):
    result = subprocess.run(['ping', '-c', str(count), target], capture_output=True, text=True)
    return result.stdout

# Function to parse ping output and extract latency info
def parse_ping_output(output):
    latencies = []
    for line in output.splitlines():
        match = re.search(r'time=([\d.]+)\s+ms', line)
        if match:
            latencies.append(float(match.group(1)))  # Ensure only numeric values are added
    return latencies

# Function to calculate statistics from latency data
def calculate_statistics(ping_runs):
    all_latencies = [lat for run in ping_runs for lat in run]
    
    if not all_latencies:
        return {"avg": None, "med": None, "min": None, "max": None}
    
    return {
        'avg': statistics.mean(all_latencies),
        'med': statistics.median(all_latencies),
        'min': min(all_latencies),
        'max': max(all_latencies)
    }

# Function to save results as JSON
def save_as_json(results, output_file):
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)

# Function to create a boxplot of latencies
def create_boxplot(ping_runs, graph_file):
    # Filter out empty ping runs and ensure all data is numeric
    ping_runs = [run for run in ping_runs if run]
    
    if not ping_runs:
        print("No data to plot.")
        return
    
    plt.boxplot(ping_runs, showmeans=True, meanprops={"marker": "o", "markerfacecolor": "black"})
    plt.xlabel("Runs")
    plt.ylabel("Latency (ms)")
    plt.title("Ping Latency Distribution")
    plt.savefig(graph_file)
    plt.close()

# Function to read ping outputs from test files
def read_test_files(test_dir):
    ping_runs = []
    for file_name in sorted(os.listdir(test_dir)):
        if file_name.endswith('.out'):
            with open(os.path.join(test_dir, file_name), 'r') as file:
                ping_runs.append(parse_ping_output(file.read()))
    return ping_runs

# Main function
def main():
    parser = argparse.ArgumentParser(description='Run ping multiple times towards a given target host')
    parser.add_argument('-n', '--num_runs', type=int, default=1, help='Number of times ping will run')
    parser.add_argument('-d', '--run_delay', type=int, default=1, help='Number of seconds to wait between two consecutive runs')
    parser.add_argument('-c', '--count', type=int, default=4, help='Number of ping requests per run')
    parser.add_argument('-o', '--output', required=True, help='Path and name of output JSON file containing the stats')
    parser.add_argument('-g', '--graph', required=True, help='Path and name of output PDF file containing stats graph')
    parser.add_argument('-t', '--target', help='A target domain name or IP address (required if --test is absent)')
    parser.add_argument('--test', help='Directory containing ping output text files')
    
    args = parser.parse_args()

    ping_runs = []

    # If test mode is enabled, read from the test files
    if args.test:
        ping_runs = read_test_files(args.test)
    else:
        if not args.target:
            print("Error: target must be provided if --test is not specified.")
            exit(1)
        
        # Run ping multiple times and collect data
        for _ in range(args.num_runs):
            output = run_ping(args.target, args.count)
            parsed_output = parse_ping_output(output)
            print(f"Run data: {parsed_output}")  # Debug print to ensure correct parsing
            ping_runs.append(parsed_output)
            time.sleep(args.run_delay)
    
    # Calculate statistics
    results = calculate_statistics(ping_runs)
    
    # Save results as JSON
    save_as_json(results, args.output)
    
    # Generate boxplot graph
    create_boxplot(ping_runs, args.graph)

if __name__ == "__main__":
    main()
