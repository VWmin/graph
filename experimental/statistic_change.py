per_turn = []
for i in range(11):
    # dp(int) -> content(string)
    flow_table = {}
    group_table = {}

    filepath = f"change/mine-{i}.txt"
    with open(filepath, 'r') as file:
        lines = file.readlines()
        flow, group = False, False
        dpid = -1
        for line in lines:

            if "ovs-ofctl dump-flows" in line:
                flow, group = True, False
                dpid = int(line.split(' ')[-1][1:])
            elif "ovs-ofctl dump-groups" in line:
                flow, group = False, True
                dpid = int(line.split(' ')[-1][1:])
            elif line is '\n':
                continue
            elif flow:
                if "reply" in line or "CONTROLLER" in line:
                    continue
                line = line.strip()
                flow_table.setdefault(dpid, [])
                flow_table[dpid].append(line[line.find("nw_dst"):])
            elif group:
                if "reply" in line:
                    continue
                line = line.strip()
                group_table.setdefault(dpid, [])
                pos = line.find('output')
                msg = "output: "
                for pair in line.split(','):
                    if "actions" in pair:
                        msg += pair.split(':')[-1] + ", "
                group_table[dpid].append(msg[:-2])

        # print(f"file {i} >>> ")
        # print(flow_table)
        # print(group_table)
        # print("\n")
        per_turn.append((flow_table, group_table))

flow_table0, group_table0 = per_turn[0]
flow_table1, group_table1 = per_turn[-1]
pre, after = {}, {}
for dpid, flow in flow_table0.items():
    pre.setdefault(dpid, "")
    pre[dpid] += flow[0]
for dpid, group in group_table0.items():
    pre.setdefault(dpid, "")
    pre[dpid] += group[0]
for dpid, flow in flow_table1.items():
    after.setdefault(dpid, "")
    after[dpid] += flow[0]
for dpid, group in group_table1.items():
    after.setdefault(dpid, "")
    after[dpid] += group[0]
print(pre)
print(after)
