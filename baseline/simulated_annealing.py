import sys
sys.path.append('../')
import copy
import time
from typing import List, Union, Optional
import numpy as np
import random
import networkx as nx
from util import read_nxgraph, cover_all_edges
from util import (obj_maxcut,
                  obj_graph_partitioning,
                  obj_minimum_vertex_cover,
                  obj_maximum_independent_set,
                  obj_maximum_independent_set_SA,
                  )
from greedy import (greedy_maxcut,
    greedy_graph_partitioning,
    greedy_minimum_vertex_cover,
    greedy_maximum_independent_set)
from util import write_result
from util import plot_fig
from util import run_simulated_annealing_over_multiple_files
from config import *
def simulated_annealing(init_temperature: int, num_steps: Optional[int], graph: nx.Graph) -> (int, Union[List[int], np.array], List[int]):
    print('simulated_annealing')
    num_nodes = int(graph.number_of_nodes())
    if PROBLEM == Problem.maxcut:
        if num_steps is None:
            num_steps = num_nodes
        gr_score, gr_solution, gr_scores = greedy_maxcut(num_steps, graph)
    elif PROBLEM == Problem.graph_partitioning:
        num_steps = num_nodes
        gr_score, gr_solution, gr_scores = greedy_graph_partitioning(num_steps, graph)
    elif PROBLEM == Problem.minimum_vertex_cover:
        num_steps = num_nodes
        gr_score, gr_solution, gr_scores = greedy_minimum_vertex_cover(None, graph)
        assert cover_all_edges(gr_solution, graph)
    elif PROBLEM == Problem.maximum_independent_set:
        num_steps = 100 * num_nodes
        gr_score, gr_solution, gr_scores = greedy_maximum_independent_set(num_steps, graph)

    start_time = time.time()
    init_score = gr_score
    curr_solution = copy.deepcopy(gr_solution)
    curr_score = gr_score
    # if PROBLEM == Problem.maximum_independent_set:
    #     curr_score = gr_score / graph.number_of_edges()
    scores = []
    scores.append(init_score)

    for k in range(num_steps):
        # The temperature decreases
        temperature = init_temperature * (1 - (k + 1) / num_steps)
        new_solution = copy.deepcopy(curr_solution)
        if PROBLEM == Problem.maxcut:
            idx = np.random.randint(0, num_nodes)
            new_solution[idx] = (new_solution[idx] + 1) % 2
            new_score = obj_maxcut(new_solution, graph)
        elif PROBLEM == Problem.graph_partitioning:
            while True:
                idx = np.random.randint(0, num_nodes)
                node2 = np.random.randint(0, num_nodes)
                if new_solution[idx] != new_solution[node2]:
                    break
            print(f"new_solution[index]: {new_solution[idx]}, new_solution[index2]: {new_solution[node2]}")
            tmp = new_solution[idx]
            new_solution[idx] = new_solution[node2]
            new_solution[node2] = tmp
            new_score = obj_graph_partitioning(new_solution, graph)
        elif PROBLEM == Problem.minimum_vertex_cover:
            iter = 0
            index = None
            while True:
                iter += 1
                if iter >= num_steps:
                    break
                indices_eq_1 = []
                for i in range(len(new_solution)):
                    if new_solution[i] == 1:
                        indices_eq_1.append(i)
                idx = np.random.randint(0, len(indices_eq_1))
                new_solution2 = copy.deepcopy(new_solution)
                new_solution2[indices_eq_1[idx]] = 0
                if cover_all_edges(new_solution2, graph):
                    index = indices_eq_1[idx]
                    break
            if index is not None:
                new_solution[index] = 0
            new_score = obj_minimum_vertex_cover(new_solution, graph, False)
        elif PROBLEM == Problem.maximum_independent_set:
            selected_indices = []
            unselected_indices = []
            for i in range(len(new_solution)):
                if new_solution[i] == 1:
                    selected_indices.append(i)
                else:
                    unselected_indices.append(i)
            idx_out = np.random.randint(0, len(selected_indices))
            node_out = selected_indices[idx_out]
            new_solution[node_out] = (new_solution[node_out] + 1) % 2
            # if prob < prob_thresh, change one node; if prob > prob_thresh, change two nodes
            prob_thresh = 0.05
            prob = random.random()
            if prob < prob_thresh:
                idx_in = np.random.randint(0, len(unselected_indices))
                node_in = unselected_indices[idx_in]
                new_solution[node_in] = (new_solution[node_in] + 1) % 2
            else:
                while True:
                    idx_in1, idx_in2 = np.random.randint(0, len(unselected_indices), 2)
                    if idx_in1 != idx_in2:
                        break
                node_in1 = unselected_indices[idx_in1]
                node_in2 = unselected_indices[idx_in2]
                new_solution[node_in1] = (new_solution[node_in1] + 1) % 2
                new_solution[node_in2] = (new_solution[node_in2] + 1) % 2
            new_score = obj_maximum_independent_set(new_solution, graph)
        store = False
        delta_e = curr_score - new_score
        if delta_e < 0:
            curr_solution = new_solution
            curr_score = new_score
            store = True
        else:
            prob = np.exp(-delta_e / (temperature + 1e-6))
            if prob > random.random():
                curr_solution = new_solution
                curr_score = new_score
                store = True
        if store:
            scores.append(new_score)
            # if PROBLEM == Problem.maximum_independent_set:
            #     tmp_new_score = obj_maximum_independent_set(new_solution, graph)
            #     print(f"init_score: {init_score}, tmp_new_score: {tmp_new_score}")
            #     scores.append(tmp_new_score)
            # else:
            #     scores.append(new_score)
    print("init_score, final score of simulated_annealing", init_score, curr_score)
    print("scores: ", scores)
    print("solution: ", curr_solution)
    running_duration = time.time() - start_time
    print('running_duration: ', running_duration)
    return curr_score, curr_solution, scores

if __name__ == '__main__':
    print(f'problem: {PROBLEM}')

    # run alg
    # init_solution = list(np.random.randint(0, 2, graph.number_of_nodes()))

    if_run_one_case = False
    if if_run_one_case:
        # read data
        graph = read_nxgraph('../data/syn/syn_50_176.txt')
        init_temperature = 4
        num_steps = None
        sa_score, sa_solution, sa_scores = simulated_annealing(init_temperature, num_steps, graph)
        # write result
        write_result(sa_solution, '../result/result.txt')
        # plot fig
        alg_name = 'SA'
        plot_fig(sa_scores, alg_name)


    alg = simulated_annealing
    alg_name = 'simulated_annealing'
    init_temperature = 4
    num_steps = None
    directory_data = '../data/syn_ER'
    prefixes = ['erdos_renyi_100_']
    run_simulated_annealing_over_multiple_files(alg, alg_name, init_temperature, num_steps, directory_data, prefixes)





