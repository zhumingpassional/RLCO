import copy
from torch.autograd import Variable
import os
import functools
import torch.nn as nn
import numpy as np
from typing import List, Union, Tuple
import networkx as nx
import torch as th
from torch import Tensor
from os import system
from config import Config
import math
try:
    import matplotlib as mpl
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

TEN = th.Tensor
INT = th.IntTensor
TEN = th.Tensor
GraphList = List[Tuple[int, int, int]]
IndexList = List[List[int]]
DataDir = './data/gset'

class MyGraph:
    def __init__(self):
        num_nodes = 0
        num_edges = 0
        graph = List[int]
def plot_nxgraph(g: nx.Graph()):
    import matplotlib.pyplot as plt
    nx.draw_networkx(g)
    fig_filename = '.result/fig.png'
    plt.savefig(fig_filename)
    plt.show()

# read graph file, e.g., gset_14.txt, as networkx.Graph
# The nodes in file start from 1, but the nodes start from 0 in our codes.
def read_nxgraph(filename: str) -> nx.Graph():
    g = nx.Graph()
    with open(filename, 'r') as file:
        # lines = []
        line = file.readline()
        is_first_line = True
        while line is not None and line != '':
            if '//' not in line:
                if is_first_line:
                    strings = line.split(" ")
                    num_nodes = int(strings[0])
                    num_edges = int(strings[1])
                    nodes = list(range(num_nodes))
                    g.add_nodes_from(nodes)
                    is_first_line = False
                else:
                    node1, node2, weight = line.split(" ")
                    g.add_edge(int(node1) - 1, int(node2) - 1, weight=weight)
            line = file.readline()
    return g

#
def transfer_nxgraph_to_adjacencymatrix(graph: nx.Graph):
    return nx.to_numpy_matrix(graph)

# the returned weightmatrix has the following format： node1 node2 weight
# 1 2 1 // the weight of node1 and node2 is 1
def transfer_nxgraph_to_weightmatrix(graph: nx.Graph):
    # edges = nx.edges(graph)
    res = np.array([])
    edges = graph.edges()
    for u, v in edges:
        u = int(u)
        v = int(v)
        # weight = graph[u][v]["weight"]
        weight = float(graph.get_edge_data(u, v)["weight"])
        vec = np.array([u, v, weight])
        if len(res) == 0:
            res = vec
        else:
            res = np.vstack((res, vec))
    return res

# weightmatrix: format of each vector: node1 node2 weight
# num_nodes: num of nodes
def transfer_weightmatrix_to_nxgraph(edges: List[List[int]], num_nodes: int) -> nx.Graph():
    graph = nx.Graph()
    nodes = list(range(num_nodes))
    graph.add_nodes_from(nodes)
    for i, j, weight in edges:
        graph.add_edge(i, j, weight=weight)
    return graph

def obj_maxcut(result: Union[Tensor, List[int], np.array], graph: nx.Graph):
    num_nodes = len(result)
    cut = 0
    adj_matrix = nx.to_numpy_matrix(graph)
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if result[i] != result[j]:
                cut += adj_matrix[(i, j)]
    return cut


# write a tensor/list/np.array (dim: 1) to a txt file.
# The nodes start from 0, and the label of classified set is 0 or 1 in our codes, but the nodes written to file start from 1, and the label is 1 or 2
def write_result(result: Union[Tensor, List, np.array], filename: str = 'result/result.txt', obj: Union[int, float] = None, running_duration: Union[int, float] = None):
    # assert len(result.shape) == 1
    # N = result.shape[0]
    num_nodes = len(result)
    directory = filename.split('/')[0]
    if not os.path.exists(directory):
        os.mkdir(directory)
    with open(filename, 'w', encoding="UTF-8") as file:
        if obj is not None:
            file.write(f'// obj: {obj}\n')
        if running_duration is not None:
            file.write(f'// running_duration: {running_duration}\n')
        for node in range(num_nodes):
            file.write(f'{node + 1} {int(result[node] + 1)}\n')


# genete a graph, and output a symmetric_adjacency_matrix and networkx_graph. The graph will be written to a file.
# weight_low (inclusive) and weight_high (exclusive) are the low and high int values for weight, and should be int.
# If writing the graph to file, the node starts from 1, not 0. The first node index < the second node index. Only the non-zero weight will be written.
# If writing the graph, the file name will be revised, e.g., syn.txt will be revised to syn_n_m.txt, where n is num_nodes, and m is num_edges.
def generate_write_adjacencymatrix_and_nxgraph(num_nodes: int,
                                               num_edges: int,
                                               filename: str = 'data/syn.txt',
                                               weight_low=0,
                                               weight_high=2) -> (List[List[int]], nx.Graph):
    if weight_low == 0:
        weight_low += 1
    adjacency_matrix = []
    # generate adjacency_matrix where each row has num_edges_per_row edges
    num_edges_per_row = int(np.ceil(2 * num_edges / num_nodes))
    for i in range(num_nodes):
        indices = []
        while True:
            all_indices = list(range(0, num_nodes))
            np.random.shuffle(all_indices)
            indices = all_indices[: num_edges_per_row]
            if i not in indices:
                break
        row = [0] * num_nodes
        weights = np.random.randint(weight_low, weight_high, size=num_edges_per_row)
        for k in range(len(indices)):
            row[indices[k]] = weights[k]
        adjacency_matrix.append(row)
    # the num of edges of the generated adjacency_matrix may not be the specified, so we revise it.
    indices1 = []  # num of non-zero weights for i < j
    indices2 = []  # num of non-zero weights for i > j
    for i in range(num_nodes):
        for j in range(num_nodes):
            if adjacency_matrix[i][j] != 0:
                if i < j:
                    indices1.append((i, j))
                else:
                    indices2.append((i, j))
    # if |indices1| > |indices2|, we get the new adjacency_matrix by swapping symmetric elements
    # based on adjacency_matrix so that |indices1| < |indices2|
    if len(indices1) > len(indices2):
        indices1 = []
        indices2 = []
        new_adjacency_matrix = copy.deepcopy(adjacency_matrix)
        for i in range(num_nodes):
            for j in range(num_nodes):
                new_adjacency_matrix[i][j] = adjacency_matrix[j][i]
                if new_adjacency_matrix[i][j] != 0:
                    if i < j:
                        indices1.append((i, j))
                    else:
                        indices2.append((i, j))
        adjacency_matrix = new_adjacency_matrix
    # We first set some elements of indices2 0 so that |indices2| = num_edges,
    # then, fill the adjacency_matrix so that the symmetric elements along diagonal are the same
    if len(indices1) <= len(indices2):
        num_set_0 = len(indices2) - num_edges
        if num_set_0 < 0:
            raise ValueError("wrong num_set_0")
        while True:
            all_ind_set_0 = list(range(0, len(indices2)))
            np.random.shuffle(all_ind_set_0)
            ind_set_0 = all_ind_set_0[: num_set_0]
            indices2_set_0 = [indices2[k] for k in ind_set_0]
            new_indices2 = set([indices2[k] for k in range(len(indices2)) if k not in ind_set_0])
            my_list = list(range(num_nodes))
            my_set: set = set()
            satisfy = True
            # check if all nodes exist in new_indices2. If yes, the condition is satisfied, and iterate again otherwise.
            for i, j in new_indices2:
                my_set.add(i)
                my_set.add(j)
            for item in my_list:
                if item not in my_set:
                    satisfy = False
                    break
            if satisfy:
                break
        for (i, j) in indices2_set_0:
            adjacency_matrix[i][j] = 0
        if len(new_indices2) != num_edges:
            raise ValueError("wrong new_indices2")
        # fill elements of adjacency_matrix based on new_indices2
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if (j, i) in new_indices2:
                    adjacency_matrix[i][j] = adjacency_matrix[j][i]
                else:
                    adjacency_matrix[i][j] = 0
    # create a networkx graph
    graph = nx.Graph()
    nodes = list(range(num_nodes))
    graph.add_nodes_from(nodes)
    num_edges = len(new_indices2)
    # create a new filename, and write the graph to the file.
    new_filename = filename.split('.')[0] + '_' + str(num_nodes) + '_' + str(num_edges) + '.txt'
    with open(new_filename, 'w', encoding="UTF-8") as file:
        file.write(f'{num_nodes} {num_edges} \n')
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                weight = int(adjacency_matrix[i][j])
                graph.add_edge(i, j, weight=weight)
                if weight != 0:
                    file.write(f'{i + 1} {j + 1} {weight}\n')
    return adjacency_matrix, graph

def write_nxgraph(g: nx.Graph(), new_filename: str):
    num_nodes = nx.number_of_nodes(g)
    num_edges = nx.number_of_edges(g)
    adjacency_matrix = nx.to_numpy_array(g)
    with open(new_filename, 'w', encoding="UTF-8") as file:
        file.write(f'{num_nodes} {num_edges} \n')
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                weight = int(adjacency_matrix[i][j])
                g.add_edge(i, j, weight=weight)
                if weight != 0:
                    file.write(f'{i + 1} {j + 1} {weight}\n')



def calc_file_name(front: str, id2: int, val: int, end: str):
    return front + "_" + str(id2) + "_" + str(val) + end + "pkl"


def detach_var(v, device):
    var = Variable(v.data, requires_grad=True).to(device)
    var.retain_grad()
    return var


def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split('.'))


class Opt_net(nn.Module):
    def __init__(self, N, hidden_layers):
        super(Opt_net, self).__init__()
        self.N = N
        self.hidden_layers = hidden_layers
        self.lstm = nn.LSTM(self.N, self.hidden_layers, 1, batch_first=True)
        self.output = nn.Linear(hidden_layers, self.N)

    def forward(self, configuration, hidden_state, cell_state):
        x, (h, c) = self.lstm(configuration, (hidden_state, cell_state))
        return self.output(x).sigmoid(), h, c


# def plot_figs(scoress: List[List[int]], num_steps: int, labels: List[str]):
#     num = len(scoress)
#     x = list(range(num_steps))
#     dic = {'0': 'ro', '1': 'gs', '2': 'b^', '3': 'c>', '4': 'm<', '5': 'yp'}
#     for i in range(num):
#         plt(x, scoress[i], dic[str(i)], labels[i])
#     plt.legend(labels, loc=0)
#     plt.show()

def plot_fig(scores: List[int], label: str):
    import matplotlib.pyplot as plt
    plt.figure()
    x = list(range(len(scores)))
    dic = {'0': 'ro-', '1': 'gs', '2': 'b^', '3': 'c>', '4': 'm<', '5': 'yp'}
    plt.plot(x, scores, dic['0'])
    plt.legend([label], loc=0)
    plt.savefig('../result/' + label + '.png')
    plt.show()

def calc_txt_files_with_prefix(directory: str, prefix: str):
    res = []
    files = os.listdir(directory)
    for file in files:
        if prefix in file and '.txt' in file:
            res.append(directory + '/' + file)
    return res

def calc_files_with_prefix_suffix(directory: str, prefix: str, suffix: str, extension: str = '.txt'):
    res = []
    files = os.listdir(directory)
    new_suffix = '_' + suffix + extension
    for file in files:
        if prefix in file and new_suffix in file:
            res.append(directory + '/' + file)
    return res

# if the file name is 'data/syn_10_27.txt', the return is 'result/syn_10_27'
# if the file name is '../data/syn/syn_10_27.txt', the return is '../result/syn_10_27'
def calc_result_file_name(file: str):
    new_file = copy.deepcopy(file)
    if 'data' in new_file:
        new_file = new_file.replace('data', 'result')
    if file[0: 2] == '..':
        new_file = new_file.split('.txt')[0]
        new_file = new_file.split('/')[0] + '/' + new_file.split('/')[1] + '/' + new_file.split('/')[-1]
    else:
        new_file = new_file.split('.')[0]
        new_file = new_file.split('/')[0] + '/' + new_file.split('/')[-1]
    return new_file

# For example, syn_10_21_3600.txt, the prefix is 'syn_10_', time_limit is 3600 (seconds).
# The gap and running_duration are also be calculated.
def calc_avg_std_of_obj(directory: str, prefix: str, time_limit: int):
    init_time_limit = copy.deepcopy(time_limit)
    objs = []
    gaps = []
    obj_bounds = []
    running_durations = []
    suffix = str(time_limit)
    files = calc_files_with_prefix_suffix(directory, prefix, suffix)
    for i in range(len(files)):
        with open(files[i], 'r') as file:
            line = file.readline()
            assert 'obj' in line
            obj = float(line.split('obj:')[1].split('\n')[0])
            objs.append(obj)

            line2 = file.readline()
            running_duration_ = line2.split('running_duration:')
            running_duration = float(running_duration_[1]) if len(running_duration_) >= 2 else None
            running_durations.append(running_duration)

            line3 = file.readline()
            gap_ = line3.split('gap:')
            gap = float(gap_[1]) if len(gap_) >= 2 else None
            gaps.append(gap)

            line4 = file.readline()
            obj_bound_ = line4.split('obj_bound:')
            obj_bound = float(obj_bound_[1]) if len(obj_bound_) >= 2 else None
            obj_bounds.append(obj_bound)

    avg_obj = np.average(objs)
    std_obj = np.std(objs)
    avg_running_duration = np.average(running_durations)
    avg_gap = np.average(gaps)
    avg_obj_bound = np.average(obj_bounds)
    print(f'{directory} prefix {prefix}, suffix {suffix}: avg_obj {avg_obj}, std_obj {std_obj}, avg_running_duration {avg_running_duration}, avg_gap {avg_gap}, avg_obj_bound {avg_obj_bound}')
    if time_limit != init_time_limit:
        print()
    return {(prefix, time_limit): (avg_obj, std_obj, avg_running_duration, avg_gap, avg_obj_bound)}

def calc_avg_std_of_objs(directory: str, prefixes: List[str], time_limits: List[int]):
    res = []
    for i in range(len(prefixes)):
        for k in range(len(time_limits)):
            avg_std = calc_avg_std_of_obj(directory, prefixes[i], int(time_limits[k]))
            res.append(avg_std)
    return res

# transfer flot to binary. For example, 1e-7 -> 0, 1 + 1e-8 -> 1
def float_to_binary(value: float) -> int:
    if abs(value) < 1e-4:
        value = 0
    elif abs(value - 1) < 1e-4:
        value = 1
    else:
        raise ValueError('wrong value')
    return value

def fetch_node(line: str):
    if 'x[' in line:
        node = int(line.split('x[')[1].split(']')[0])
    else:
        node = None
    return node

# transfer result file,
# e.g.,
# x[0]: 1.0
# x[1]: 0.0
# x[2]: 1.0
# to
# 1 2
# 2 1
# 3 2
def transfer_write_solver_result(filename: str, new_filename: str):
    # assert '.txt' in filename
    nodes = []
    values = []
    with open(filename, 'r') as file:
        find_x = False
        while True:
            line = file.readline()
            if 'x[' in line:
                find_x = True
                node = int(line.split('x[')[1].split(']')[0])
                value = float(line.split(':')[1].split('\n')[0])
                value = float_to_binary(value)
                nodes.append(node)
                values.append(value)
            if find_x and 'x[' not in line:
                break
    with open(new_filename, 'w', encoding="UTF-8") as file:
        for i in range(len(nodes)):
            file.write(f'{nodes[i] + 1} {values[i] + 1}\n')

# For example, syn_10_21_3600.sov, the prefix is 'syn_10_', time_limit is 3600 (seconds).
# extension is '.txt' or '.sta'
def transfer_write_solver_results(directory: str, prefixes: List[str], time_limits: List[int], from_extension: str, to_extension: str):
    for i in range(len(prefixes)):
        for k in range(len(time_limits)):
            suffix = str(int(time_limits[k]))
            files = calc_files_with_prefix_suffix(directory, prefixes[i], suffix, from_extension)
            for filename in files:
                new_filename = filename.split('.')[0] + to_extension
                transfer_write_solver_result(filename, new_filename)

# e.g., rename 'txt' files in directory to 'sta'
def rename_files(directory: str, orig: str, dest: str):
    files = os.listdir(directory)
    for file in files:
        filename = directory + '/' + file
        if orig in filename:
            new_filename = filename.replace(orig, dest)
            os.rename(filename, new_filename)

def load_graph_from_txt(txt_path: str = './data/gset_14.txt'):
    with open(txt_path, 'r') as file:
        lines = file.readlines()
        lines = [[int(i1) for i1 in i0.split()] for i0 in lines]
    num_nodes, num_edges = lines[0]
    graph = [(n0 - 1, n1 - 1, dt) for n0, n1, dt in lines[1:]]  # node_id “从1开始”改为“从0开始”
    return graph, num_nodes, num_edges

def get_adjacency_matrix(graph, num_nodes):
    adjacency_matrix = np.empty((num_nodes, num_nodes))
    adjacency_matrix[:] = -1  # 选用-1而非0表示表示两个node之间没有edge相连，避免两个节点的距离为0时出现冲突
    for n0, n1, dt in graph:
        adjacency_matrix[n0, n1] = dt
    return adjacency_matrix

def load_graph(graph_name: str):
    data_dir = './data/gset'
    graph_types = ['erdos_renyi', 'powerlaw', 'barabasi_albert']

    if os.path.exists(f"{data_dir}/{graph_name}.txt"):
        txt_path = f"{data_dir}/{graph_name}.txt"
        graph, num_nodes, num_edges = load_graph_from_txt(txt_path=txt_path)
    elif graph_name.split('_')[0] in graph_types:
        g_type, num_nodes = graph_name.split('_')
        num_nodes = int(num_nodes)
        graph, num_nodes, num_edges = generate_graph(num_nodes=num_nodes, g_type=g_type)
    else:
        raise ValueError(f"graph_name {graph_name}")
    return graph, num_nodes, num_edges

def load_graph_auto(graph_name: str):
    import random
    graph_types = ['erdos_renyi', 'powerlaw', 'barabasi_albert']

    if os.path.exists(f"{DataDir}/{graph_name}.txt"):
        txt_path = f"{DataDir}/{graph_name}.txt"
        graph = load_graph_from_txt(txt_path=txt_path)
    elif graph_name.split('_')[0] in graph_types and len(graph_name.split('_')) == 3:
        graph_type, num_nodes, valid_i = graph_name.split('_')
        num_nodes = int(num_nodes)
        valid_i = int(valid_i[len('ID'):])
        random.seed(valid_i)
        graph = generate_graph(num_nodes=num_nodes, graph_type=graph_type)
        random.seed()
    elif graph_name.split('_')[0] in graph_types and len(graph_name.split('_')) == 2:
        graph_type, num_nodes = graph_name.split('_')
        num_nodes = int(num_nodes)
        graph = generate_graph(num_nodes=num_nodes, graph_type=graph_type)
    else:
        raise ValueError(f"DataDir {DataDir} | graph_name {graph_name}")
    return graph

def save_graph_info_to_txt(txt_path, graph, num_nodes, num_edges):
    formatted_content = f"{num_nodes} {num_edges}\n"
    for node0, node1, distance in graph:
        row = [node0 + 1, node1 + 1, distance]  # node+1 is a bad design
        formatted_content += " ".join(str(item) for item in row) + "\n"
    with open(txt_path, "w") as file:
        file.write(formatted_content)


def generate_graph(num_nodes: int, g_type: str):
    graph_types = ['erdos_renyi', 'powerlaw', 'barabasi_albert']
    assert g_type in graph_types

    if g_type == 'erdos_renyi':
        g = nx.erdos_renyi_graph(n=num_nodes, p=0.15)
    elif g_type == 'powerlaw':
        g = nx.powerlaw_cluster_graph(n=num_nodes, m=4, p=0.05)
    elif g_type == 'barabasi_albert':
        g = nx.barabasi_albert_graph(n=num_nodes, m=4)
    else:
        raise ValueError(f"g_type {g_type} should in {graph_types}")

    graph = []
    for node0, node1 in g.edges:
        distance = 1
        graph.append((node0, node1, distance))
    num_nodes = num_nodes
    num_edges = len(graph)
    return graph, num_nodes, num_edges


def generate_graph_for_validation():
    import random
    num_nodes_list = [20, 50, 100, 200, 300]
    g_type = 'powerlaw'
    num_valid = 6
    seed_num = 0
    data_dir = './data'
    os.makedirs(data_dir, exist_ok=True)

    '''generate'''
    for num_nodes in num_nodes_list:
        random.seed(seed_num)  # must write in the for loop
        for i in range(num_valid):
            txt_path = f"{data_dir}/graph_{g_type}_{num_nodes}_ID{i:03}.txt"

            graph, num_nodes, num_edges = generate_graph(num_nodes=num_nodes, g_type=g_type)
            save_graph_info_to_txt(txt_path, graph, num_nodes, num_edges)

    '''load'''
    for num_nodes in num_nodes_list:
        for i in range(num_valid):
            txt_path = f"{data_dir}/graph_{g_type}_{num_nodes}_ID{i:03}.txt"

            graph, num_nodes, num_edges = load_graph_from_txt(txt_path)
            adjacency_matrix = build_adjacency_matrix(graph, num_nodes)
            print(adjacency_matrix.shape)








'''simulator'''


def build_adjacency_matrix(graph, num_nodes):
    adjacency_matrix = np.empty((num_nodes, num_nodes))
    adjacency_matrix[:] = -1  # 选用-1而非0表示表示两个node之间没有edge相连，避免两个节点的距离为0时出现冲突
    for n0, n1, dt in graph:
        adjacency_matrix[n0, n1] = dt
    return adjacency_matrix

def build_adjacency_matrix_auto(graph: GraphList, if_bidirectional: bool = False):
    """例如，无向图里：
    - 节点0连接了节点1
    - 节点0连接了节点2
    - 节点2连接了节点3

    用邻接阶矩阵Ary的上三角表示这个无向图：
      0 1 2 3
    0 F T T F
    1 _ F F F
    2 _ _ F T
    3 _ _ _ F

    其中：
    - Ary[0,1]=True
    - Ary[0,2]=True
    - Ary[2,3]=True
    - 其余为False
    """
    not_connection = -1  # 选用-1去表示表示两个node之间没有edge相连，不选用0是为了避免两个节点的距离为0时出现冲突
    print(f"graph before enter: {graph}")
    num_nodes = obtain_num_nodes_auto(graph=graph)

    adjacency_matrix = th.zeros((num_nodes, num_nodes), dtype=th.float32)
    adjacency_matrix[:] = not_connection
    for n0, n1, distance in graph:
        adjacency_matrix[n0, n1] = distance
        if if_bidirectional:
            adjacency_matrix[n1, n0] = distance
    return adjacency_matrix

def build_adjacency_indies_auto(graph: MyGraph, if_bidirectional: bool = False) -> (IndexList, IndexList):
    """
    用二维列表list2d表示这个图：
    [
        [1, 2],
        [],
        [3],
        [],
    ]
    其中：
    - list2d[0] = [1, 2]
    - list2d[2] = [3]

    对于稀疏的矩阵，可以直接记录每条边两端节点的序号，用shape=(2,N)的二维列表 表示这个图：
    0, 1
    0, 2
    2, 3
    如果条边的长度为1，那么表示为shape=(2,N)的二维列表，并在第一行，写上 4个节点，3条边的信息，帮助重建这个图，然后保存在txt里：
    4, 3
    0, 1, 1
    0, 2, 1
    2, 3, 1
    """
    num_nodes = obtain_num_nodes_auto(graph=graph)

    n0_to_n1s = [[] for _ in range(num_nodes)]  # 将 node0_id 映射到 node1_id
    n0_to_dts = [[] for _ in range(num_nodes)]  # 将 mode0_id 映射到 node1_id 与 node0_id 的距离
    for n0, n1, distance in graph:
        n0_to_n1s[n0].append(n1)
        n0_to_dts[n0].append(distance)
        if if_bidirectional:
            n0_to_n1s[n1].append(n0)
            n0_to_dts[n1].append(distance)
    n0_to_n1s = [th.tensor(node1s) for node1s in n0_to_n1s]
    n0_to_dts = [th.tensor(node1s) for node1s in n0_to_dts]
    assert num_nodes == len(n0_to_n1s)
    assert num_nodes == len(n0_to_dts)

    '''sort'''
    for i, node1s in enumerate(n0_to_n1s):
        sort_ids = th.argsort(node1s)
        n0_to_n1s[i] = n0_to_n1s[i][sort_ids]
        n0_to_dts[i] = n0_to_dts[i][sort_ids]
    return n0_to_n1s, n0_to_dts

def obtain_num_nodes_auto(graph: GraphList) -> int:
    # print(f"iter: {Config.iter}, graph: {graph}")
    # Config.iter += 1
    # num_nodes = 0
    # for vec in graph:
    #     print(f"vec: {vec}")
    #     assert len(vec) == 3
    #     n0, n1, distance = vec
    #     if max(n0, n1) > num_nodes:
    #         num_nodes = max(n0, n1)
    # return num_nodes
    return max([max(n0, n1) for n0, n1, distance in graph]) + 1


def convert_matrix_to_vector(matrix):
    vector = [row[i + 1:] for i, row in enumerate(matrix)]
    return th.hstack(vector)


def check_adjacency_matrix_vector():
    num_nodes = 32
    graph_types = ['erdos_renyi', 'powerlaw', 'barabasi_albert']

    for g_type in graph_types:
        print(f"g_type {g_type}")
        for i in range(8):
            graph, num_nodes, num_edges = generate_graph(num_nodes=num_nodes, g_type=g_type)
            print(i, num_nodes, num_edges, graph)

            adjacency_matrix = build_adjacency_matrix(graph, num_nodes)  # 邻接矩阵
            adjacency_vector = convert_matrix_to_vector(adjacency_matrix)  # 邻接矩阵的上三角拍平为矢量，传入神经网络
            print(adjacency_vector)




def draw_adjacency_matrix():
    from simulator import GraphMaxCutSimulator
    graph_name = 'powerlaw_48'
    env = GraphMaxCutSimulator(graph_name=graph_name)
    ary = (env.adjacency_matrix != -1).to(th.int).data.cpu().numpy()

    d0 = d1 = ary.shape[0]
    if plt:
        plt.imshow(1 - ary[:, ::-1], cmap='hot', interpolation='nearest', extent=[0, d1, 0, d0])
        plt.gca().set_xticks(np.arange(0, d1, 1))
        plt.gca().set_yticks(np.arange(0, d0, 1))
        plt.grid(True, color='grey', linewidth=1)
        plt.title('black denotes connect')
        plt.show()


def check_simulator_encoder():
    th.manual_seed(0)
    num_envs = 6
    graph_name = 'powerlaw_64'
    from simulator import GraphMaxCutSimulator
    sim = GraphMaxCutSimulator(graph_name=graph_name)
    enc = EncoderBase64(num_nodes=sim.num_nodes)

    probs = sim.get_rand_probs(num_envs=num_envs)
    print(sim.get_objectives(probs))

    best_score = -th.inf
    best_str_x = ''
    for _ in range(8):
        probs = sim.get_rand_probs(num_envs=num_envs)
        sln_xs = sim.prob_to_bool(probs)
        scores = sim.get_scores(sln_xs)

        max_score, max_id = th.max(scores, dim=0)
        if max_score > best_score:
            best_score = max_score
            best_sln_x = sln_xs[max_id]
            best_str_x = enc.bool_to_str(best_sln_x)
            print(f"best_score {best_score}  best_sln_x {best_str_x}")

    best_sln_x = enc.str_to_bool(best_str_x)
    best_score = sim.get_scores(best_sln_x.unsqueeze(0)).squeeze(0)
    print(f"NumNodes {sim.num_nodes}  NumEdges {sim.num_edges}")
    print(f"score {best_score}  sln_x \n{enc.bool_to_str(best_sln_x)}")


def check_convert_sln_x():
    gpu_id = 0
    num_envs = 1
    graph_name = 'powerlaw_64'
    from simulator import GraphMaxCutSimulator
    sim = GraphMaxCutSimulator(graph_name=graph_name, gpu_id=gpu_id)
    enc = EncoderBase64(num_nodes=sim.num_nodes)

    x_prob = sim.get_rand_probs(num_envs=num_envs)[0]
    x_bool = sim.prob_to_bool(x_prob)

    x_str = enc.bool_to_str(x_bool)
    print(x_str)
    x_bool = enc.str_to_bool(x_str)

    assert all(x_bool == sim.prob_to_bool(x_prob))


class EncoderBase64:
    def __init__(self, num_nodes: int):
        self.num_nodes = num_nodes

        self.base_digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"
        self.base_num = len(self.base_digits)

    def bool_to_str(self, x_bool: TEN) -> str:
        x_int = int(''.join([('1' if i else '0') for i in x_bool.tolist()]), 2)

        '''bin_int_to_str'''
        base_num = len(self.base_digits)
        x_str = ""
        while True:
            remainder = x_int % base_num
            x_str = self.base_digits[remainder] + x_str
            x_int //= base_num
            if x_int == 0:
                break

        x_str = '\n'.join([x_str[i:i + 120] for i in range(0, len(x_str), 120)])
        return x_str.zfill(math.ceil(self.num_nodes // 6 + 1))

    def str_to_bool(self, x_str: str) -> TEN:
        x_b64 = x_str.replace('\n', '')

        '''b64_str_to_int'''
        x_int = 0
        base_len = len(x_b64)
        for i in range(base_len):
            digit = self.base_digits.index(x_b64[i])
            power = base_len - 1 - i
            x_int += digit * (self.base_num ** power)

        return self.int_to_bool(x_int)

    def int_to_bool(self, x_int: int) -> TEN:
        x_bin: str = bin(x_int)[2:]
        x_bool = th.zeros(self.num_nodes, dtype=th.int8)
        x_bool[-len(x_bin):] = th.tensor([int(i) for i in x_bin], dtype=th.int8)
        return x_bool



if __name__ == '__main__':
    read_txt = True
    if read_txt:
        graph1 = read_nxgraph('data/gset/gset_14.txt')
        graph2 = read_nxgraph('data/syn_5_5.txt')

    # result = Tensor([0, 1, 0, 1, 0, 1, 1])
    # write_result(result)
    # result = [0, 1, 0, 1, 0, 1, 1]
    # write_result(result)
    write_result_ = False
    if write_result_:
        result = [1, 0, 1, 0, 1]
        write_result(result)

    generate_read = False
    if generate_read:
        adj_matrix, graph3 = generate_write_adjacencymatrix_and_nxgraph(6, 8)
        graph4 = read_nxgraph('data/syn_6_8.txt')
        obj_maxcut(result, graph4)

    # generate synthetic data
    generate_data = False
    if generate_data:
        # num_nodes_edges = [(20, 50), (30, 110), (50, 190), (100, 460), (200, 1004), (400, 1109), (800, 2078), (1000, 4368), (2000, 9386), (3000, 11695), (4000, 25654), (5000, 50543), (10000, 100457)]
        num_nodes_edges = [(3000, 25695), (4000, 38654), (5000, 50543),  (6000, 73251), (7000, 79325), (8000, 83647), (9000, 96324), (10000, 100457), (13000, 18634), (16000, 19687), (20000, 26358)]
        # num_nodes_edges = [(100, 460)]
        num_datasets = 1
        for num_nodes, num_edges in num_nodes_edges:
            for n in range(num_datasets):
                generate_write_adjacencymatrix_and_nxgraph(num_nodes, num_edges + n)
        print()


    # directory = 'result'
    # prefix = 'syn_10_'
    # time_limit = 3600
    # avg_std = calc_avg_std_of_obj(directory, prefix, time_limit)

    directory_result = 'result'
    prefixes = ['syn_10_', 'syn_50_', 'syn_100_', 'syn_300_', 'syn_500_', 'syn_700_', 'syn_900_', 'syn_1000_', 'syn_3000_', 'syn_5000_', 'syn_7000_', 'syn_9000_', 'syn_10000_']
    # prefixes = ['syn_10_', 'syn_50_', 'syn_100_']
    time_limits = [0.5 * 3600]
    avgs_stds = calc_avg_std_of_objs(directory_result, prefixes, time_limits)

    # filename = 'result/syn_10_21_1800.sta'
    # new_filename = 'result/syn_10_21_1800.txt'
    # transfer_write_solver_result(filename, new_filename)

    # from_extension = '.sov'
    # to_extension = '.txt'
    # transfer_write_solver_results(directory_result, prefixes, time_limits, from_extension, to_extension)

    print()