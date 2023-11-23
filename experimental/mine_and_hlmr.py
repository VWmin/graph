import copy
import random

import hlmr
import heat_degree_matrix
import random_graph
import util


def test_ts_example():
    g = random_graph.gt_itm_example()
    number_of_nodes = g.number_of_nodes()
    b_lo, b_hi = 5e6 / 2, 10e6 / 2  # use half of the bandwidth for multicast
    b_req_lo, b_req_hi = 512 * 1e3, 1e6  # per multicast required
    d_lo, d_hi = 1, 10
    d_req_lo, d_req_hi = 50, 100

    random_graph.add_attr_with_random_value(g, "bandwidth", int(b_lo), int(b_hi))
    random_graph.add_attr_with_random_value(g, "weight", d_lo, d_hi)
    S = util.random_s_with_number(number_of_nodes, 10)
    S2R = util.random_s2r_with_number(number_of_nodes, 10, S)
    B = util.random_d_with_range(S, int(b_req_lo), int(b_req_hi))
    D = util.random_d_with_range(S, d_req_lo, d_req_hi)

    print(S2R)

    mine_instance = heat_degree_matrix.HeatDegreeModel(g, D, B, S2R)
    mine_instance.statistic()

    hlmr_instance = hlmr.HLMR(copy.deepcopy(g), D, B, S2R)
    hlmr_instance.statistic()


def test_ts_example_with_random_op():
    g = random_graph.gt_itm_example()
    number_of_nodes = g.number_of_nodes()
    b_lo, b_hi = 5e6 / 2, 10e6 / 2  # use half of the bandwidth for multicast
    b_req_lo, b_req_hi = 512 * 1e3, 1e6  # per multicast required
    d_lo, d_hi = 1, 10
    d_req_lo, d_req_hi = 50, 100

    random_graph.add_attr_with_random_value(g, "bandwidth", int(b_lo), int(b_hi))
    random_graph.add_attr_with_random_value(g, "weight", d_lo, d_hi)
    S = util.random_s_with_number(number_of_nodes, 10)
    S2R = util.random_s2r_with_number(number_of_nodes, 10, S)
    B = util.random_d_with_range(S, int(b_req_lo), int(b_req_hi))
    D = util.random_d_with_range(S, d_req_lo, d_req_hi)

    print(S2R)

    mine_instance = heat_degree_matrix.HeatDegreeModel(g, D, B, copy.deepcopy(S2R))
    mine_instance.statistic()

    g_copy = copy.deepcopy(g)
    hlmr_instance = hlmr.HLMR(g_copy, D, B, S2R)
    hlmr_instance.statistic()

    cnt = 10
    for i in range(cnt):
        print()
        op_type = random.randint(0, 1)
        if op_type == 1:
            s = random.choice(S)
            new_r = util.random_number_but_not_in(0, number_of_nodes - 1, S2R[s] | {s})
            S2R[s].add(new_r)
            print(f"turn {i+1}, add new recv {new_r} to src {s}")

            mine_instance.add_recv(s, new_r)
            mine_instance.statistic()

            hlmr_instance = hlmr.HLMR(g_copy, D, B, S2R)
            hlmr_instance.statistic()
        else:
            s = random.choice(S)
            while len(S2R[s]) == 0:
                s = random.choice(S)
            remove_r = random.choice(list(S2R[s]))
            S2R[s].remove(remove_r)
            print(f"turn {i+1}, remove recv {remove_r} from src {s}")

            mine_instance.remove_recv(s, remove_r)
            mine_instance.statistic()

            hlmr_instance = hlmr.HLMR(g_copy, D, B, S2R)
            hlmr_instance.statistic()



def test_with_random_graph():
    number_of_nodes = 2000
    prob_of_edge = 0.1
    b_lo, b_hi = 5e6 / 2, 10e6 / 2  # use half of the bandwidth for multicast
    b_req_lo, b_req_hi = 512 * 1e3, 1e6  # per multicast required
    d_lo, d_hi = 1, 10
    d_req_lo, d_req_hi = 50, 100

    number_of_multicast_group = 10
    number_of_group_member = 10

    g = random_graph.random_graph(number_of_nodes, prob_of_edge, d_hi)
    random_graph.add_attr_with_random_value(g, "bandwidth", int(b_lo), int(b_hi))
    S = util.random_s_with_number(number_of_nodes, number_of_multicast_group)
    S2R = util.random_s2r_with_number(number_of_nodes, number_of_group_member, S)
    B = util.random_d_with_range(S, int(b_req_lo), int(b_req_hi))
    D = util.random_d_with_range(S, d_req_lo, d_req_hi)

    print(S2R)

    mine_instance = heat_degree_matrix.HeatDegreeModel(g, D, B, S2R)
    mine_instance.statistic()

    hlmr_instance = hlmr.HLMR(copy.deepcopy(g), D, B, S2R)
    hlmr_instance.statistic()


if __name__ == '__main__':
    # test_ts_example()
    # test_with_random_graph()
    test_ts_example_with_random_op()
