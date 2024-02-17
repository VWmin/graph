import json
import linecache
import os
import re

# exp_type = "mine"
# exp_type = "hlmr"
exp_type = "igmp"
# exp_type = "stp"
igmp = exp_type == "igmp"


with open(f'result/{exp_type}/ev_setting.json', 'r') as json_file:
    ev = json.load(json_file)
ev["group_to_src"] = {value: key for key, value in ev["src_to_group"].items()}


if not igmp:
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
        # print(f"\tgroup {group}:")
        jitter_arr = []
        bw = 0
        for file_name in group_to_file_names[group]:
            file_path = os.path.join(root, file_name)
            file = open(file_path, 'r')
            lines = file.readlines()
            pos = 0
            for pos in range(len(lines)):
                if "[ ID] Interval" in lines[pos]:
                    break
            line = lines[pos+1]
            match_bw = re.search(r'(\d+\s+[K,M]bits/sec)', line)
            match_ms = re.search(r'(\d+\.\d+\s+ms)', line)
            match_rate = re.search(r'(\d+/\d+)', line)
            bw, jitter, rate = (round(int(match_bw.group(1).split(" ")[0]) * 0.001, 3),
                                float(match_ms.group(1)[:-3]),
                                match_rate.group(1))
            print(f"\t\tbw: {bw}, jitter: {jitter}, lost rate: {rate}")
            jitter_arr.append(jitter)
        if not igmp:
            used_bw = bw * len(routing_trees[ev["group_to_src"][group]])
            bw_use_rate = round(used_bw / ev["total_bw"] * 100, 3)
        avg_jitter = round(sum(jitter_arr) / len(jitter_arr), 2)
        print(f"\tavg jitter in this round: {avg_jitter}")

print("delay >>>")
for root, dirs, files in os.walk(libtins_path):
    group_to_file_names = {group: [] for group in ev["group_to_src"]}
    for file_name in files:
        group = int(file_name[1])
        group_to_file_names[group].append(file_name)

    for group in group_to_file_names:
        # print(f"\tgroup {group}:")
        delay_arr = []
        for file_name in group_to_file_names[group]:
            file_path = os.path.join(root, file_name)
            with open(file_path, 'r') as file:
                cost_arr = [float(line.split(" ")[-1]) for line in file]
                delay = round(sum(cost_arr) / len(cost_arr), 2)
                delay_arr.append(delay)
        print(f"\tavg delay in this round: {round(sum(delay_arr) / len(delay_arr), 2)}")

