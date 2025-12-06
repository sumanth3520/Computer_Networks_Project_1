#trstats
import argparse
import subprocess
import os
import time
import re
import statistics
import json
import matplotlib.pyplot as plt

# Function to run traceroute command
def run_traceroute(target, max_hops):
    result = subprocess.run(['traceroute', '-m', str(max_hops), target], capture_output=True, text=True)
    return result.stdout

# Function to parse traceroute output and extract latency info
def parse_traceroute_output(output):
    hop_info = []
    for line in output.splitlines():
        match = re.match(r"^\s*(\d+)\s+([\S]+)\s+\(([\d.]+)\)\s+([\d.]+)\sms\s+([\d.]+)\sms\s+([\d.]+)\sms", line)
        if match:
            hop = int(match.group(1))
            host = match.group(2)
            ip = match.group(3)
            latencies = [float(match.group(4)), float(match.group(5)), float(match.group(6))]
            hop_info.append({'hop': hop, 'host': host, 'ip': ip, 'latencies': latencies})
    return hop_info

# Function to calculate statistics from latency data
def calculate_statistics(traceroute_runs):
    hop_stats = {}
    
    for run in traceroute_runs:
        for hop in run:
            hop_num = hop['hop']
            if hop_num not in hop_stats:
                hop_stats[hop_num] = {
                    'hosts': [[hop['host'], hop['ip']]],
                    'latencies': hop['latencies']
                }
            else:
                hop_stats[hop_num]['latencies'].extend(hop['latencies'])
    
    results = []
    for hop_num, stats in hop_stats.items():
        latencies = stats['latencies']
        results.append({
            'hop': hop_num,
            'hosts': stats['hosts'],
            'avg': statistics.mean(latencies),
            'med': statistics.median(latencies),
            'min': min(latencies),
            'max': max(latencies)
        })
    
    return results

# Function to save results as JSON
def save_as_json(results, output_file):
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)

# Function to create a boxplot of latencies
def create_boxplot(traceroute_runs, graph_file):
    hop_latencies = {}
    
    for run in traceroute_runs:
        for hop in run:
            hop_num = hop['hop']
            if hop_num not in hop_latencies:
                hop_latencies[hop_num] = []
            hop_latencies[hop_num].extend(hop['latencies'])
    
    data = [hop_latencies[hop_num] for hop_num in sorted(hop_latencies)]
    
    plt.boxplot(data)
    plt.xlabel("Hops")
    plt.ylabel("Latency (ms)")
    plt.title("Latency Distribution per Hop")
    plt.savefig(graph_file)
    plt.close()

# Function to read traceroute outputs from test files
def read_test_files(test_dir):
    traceroute_runs = []
    for file_name in sorted(os.listdir(test_dir)):
        if file_name.endswith('.out'):
            with open(os.path.join(test_dir, file_name), 'r') as file:
                traceroute_runs.append(parse_traceroute_output(file.read()))
    return traceroute_runs

# Main function
def main():
    parser = argparse.ArgumentParser(description='Run traceroute multiple times towards a given target host')
    parser.add_argument('-n', '--num_runs', type=int, default=1, help='Number of times traceroute will run')
    parser.add_argument('-d', '--run_delay', type=int, default=1, help='Number of seconds to wait between two consecutive runs')
    parser.add_argument('-m', '--max_hops', type=int, default=30, help='Number of max hops per traceroute run')
    parser.add_argument('-o', '--output', required=True, help='Path and name of output JSON file containing the stats')
    parser.add_argument('-g', '--graph', required=True, help='Path and name of output PDF file containing stats graph')
    parser.add_argument('-t', '--target', help='A target domain name or IP address (required if --test is absent)')
    parser.add_argument('--test', help='Directory containing traceroute output text files')
    
    args = parser.parse_args()

    traceroute_runs = []

    # If test mode is enabled, read from the test files
    if args.test:
        traceroute_runs = read_test_files(args.test)
    else:
        if not args.target:
            print("Error: target must be provided if --test is not specified.")
            exit(1)
        
        # Run traceroute multiple times and collect data
        for _ in range(args.num_runs):
            output = run_traceroute(args.target, args.max_hops)
            traceroute_runs.append(parse_traceroute_output(output))
            time.sleep(args.run_delay)
    
    # Calculate statistics
    results = calculate_statistics(traceroute_runs)
    
    # Save results as JSON
    save_as_json(results, args.output)
    
    # Generate boxplot graph
    create_boxplot(traceroute_runs, args.graph)

if __name__ == "__main__":
    main()
