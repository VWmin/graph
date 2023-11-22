import copy

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
    print(mine_instance.routing_trees)

    hlmr_instance = hlmr.HLMR(copy.deepcopy(g), D, B, S2R)
    print(hlmr_instance.routing_trees)


if __name__ == '__main__':
    test_ts_example()
