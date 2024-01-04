import json
import linecache
import os
import re

exp_type = "mine"

with open(f'result/{exp_type}/ev_setting.json', 'r') as json_file:
    ev = json.load(json_file)
ev["group_to_src"] = {value: key for key, value in ev["src_to_group"].items()}

with open(f'result/{exp_type}/routing_trees.json', 'r') as json_file:
    routing_trees = json.load(json_file)

# jitter
iperf_path = f'result/{exp_type}/iperf'
libtins_path = f'result/{exp_type}/libtins'

print("bw, jitter, lost rate >>>")
for root, dirs, files in os.walk(iperf_path):
    group_to_file_names = {group: [] for group in ev["group_to_src"]}
    for file_name in files:
        group = int(file_name[8])
        group_to_file_names[group].append(file_name)

    for group in group_to_file_names:
        print(f"\tgroup {group}:")
        for file_name in group_to_file_names[group]:
            file_path = os.path.join(root, file_name)
            line = linecache.getline(file_path, 9)
            match_bw = re.search(r'(\d+\s+[K,M]bits/sec)', line)
            match_ms = re.search(r'(\d+\.\d+\s+ms)', line)
            match_rate = re.search(r'(\d+/\d+)', line)
            bw, jitter, rate = match_bw.group(1), match_ms.group(1), match_rate.group(1)
            print(f"\t\tbw: {bw}, jitter: {jitter}, lost rate: {rate}")

print("delay >>>")
for root, dirs, files in os.walk(libtins_path):
    group_to_file_names = {group: [] for group in ev["group_to_src"]}
    for file_name in files:
        group = int(file_name[1])
        group_to_file_names[group].append(file_name)

    for group in group_to_file_names:
        print(f"\tgroup {group}:")
        for file_name in group_to_file_names[group]:
            file_path = os.path.join(root, file_name)
            with open(file_path, 'r') as file:
                cost_arr = [float(line.split(" ")[-1]) for line in file]
                print(f"\t\tdelay: {round(sum(cost_arr) / len(cost_arr), 2)} ms")
