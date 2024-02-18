import json
import linecache
import os
import re

import networkx as nx

exp_type = "mine"
# exp_type = "hlmr"
# exp_type = "igmp"
# exp_type = "stp"
igmp = exp_type == "igmp"

with open(f'result/{exp_type}/ev_setting.json', 'r') as json_file:
    ev = json.load(json_file)
ev["group_to_src"] = {value: key for key, value in ev["src_to_group"].items()}
total_bw = ev["total_bw"]  # sum of all edge bw
routing_trees = {}
number_of_groups = len(ev["src_to_group"])

if not igmp:
    with open(f'result/{exp_type}/routing_trees.json', 'r') as json_file:
        routing_trees_json = json.load(json_file)
        for root, edges in routing_trees_json.items():
            routing_trees[root] = nx.Graph()
            for edge_str in edges:
                u, v = edge_str.split('-')[0], edge_str.split('-')[1]
                routing_trees[root].add_edge(u, v)

# jitter
iperf_path = f'result/{exp_type}/iperf'
libtins_path = f'result/{exp_type}/libtins'

# print("bw, jitter, lost rate >>>")
tot_avg_bw, tot_avg_jitter, tot_avg_lose = 0, 0, 0
for root, dirs, files in os.walk(iperf_path):
    group_to_file_names = {group: [] for group in ev["group_to_src"]}
    for file_name in files:
        group = int(file_name.split('-')[0].split('.')[-1])
        group_to_file_names[group].append(file_name)

    for group in group_to_file_names:
        # print(f"\tgroup {group}:")
        src = ev["group_to_src"][group]
        jitter_arr = []
        used_bw = 0
        lose_arr = []
        for file_name in group_to_file_names[group]:
            recv = file_name.split('-')[1][1:]
            file_path = os.path.join(root, file_name)
            file = open(file_path, 'r')
            lines = file.readlines()
            pos = 0
            for pos in range(len(lines)):
                if "[ ID] Interval" in lines[pos]:
                    break
            line = lines[pos + 1]
            match_bw = re.search(r'([1-9]\d*\.?\d*\s+[K,M])', line)
            match_ms = re.search(r'(\d+\.\d+\s+ms)', line)
            match_rate = re.search(r'(\d+/\d+)', line)
            bw_value, bw_unit = float(match_bw.group(1).split(" ")[0]), match_bw.group(1).split(" ")[1]
            bw = bw_value if bw_unit == 'M' else round(bw_value * 1e-3, 3)
            used_bw = bw * nx.shortest_path_length(routing_trees[src], src, recv)
            jitter = float(match_ms.group(1)[:-3])
            rate = int(match_rate.group(1).split('/')[0]) / int(match_rate.group(1).split('/')[1])
            # print(f"\t\tbw: {bw}, jitter: {jitter}, lost rate: {rate}")
            jitter_arr.append(jitter)
            lose_arr.append(rate)
        if not jitter_arr:
            continue
        # if not igmp:
        avg_lose = sum(lose_arr) / len(lose_arr)
        # print(f"\tlose rate: {avg_lose}")
        bw_use_rate = used_bw / total_bw
        # print(f"\tavg bw use rate: {bw_use_rate}")
        avg_jitter = round(sum(jitter_arr) / len(jitter_arr), 2)
        # print(f"\tavg jitter in this round: {avg_jitter}")
        tot_avg_lose += avg_lose
        tot_avg_bw += bw_use_rate
        tot_avg_jitter += avg_jitter
print(f"bw: {tot_avg_bw / number_of_groups}")
print(f"lose: {tot_avg_lose /  number_of_groups}")
print(f"jitter: {tot_avg_jitter / number_of_groups}")

# print("delay >>>")
tot_avg_delay = 0
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
        if not delay_arr:
            continue
        avg_delay = round(sum(delay_arr) / len(delay_arr), 2)
        # print(f"\tavg delay in this round: {avg_delay}")
        tot_avg_delay += avg_delay
print(f"delay: {tot_avg_delay / number_of_groups}")
