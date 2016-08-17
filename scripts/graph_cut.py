__author__ = 'ziyue'

import os
import argparse
import re
import sys
import json


def run(input_graph_json_path, output_graph_dir, gpmetis_path, avg_volume):

    """

    :param input_graph_json_path:
    :param output_graph_dir:
    :param gpmetis_path:
    """
    input_graph_json_path = os.path.abspath(input_graph_json_path)
    output_graph_dir = os.path.abspath(output_graph_dir)
    gpmetis_path = os.path.abspath(gpmetis_path)

    '''
    r = os.system("rm -rf %s/output/" % output_graph_dir)
    if r != 0:
        print "rm failed"
        sys.exit(r)
    '''
    r = os.system("mkdir -p %s/output/" % output_graph_dir)
    if r != 0:
        print "rm failed"
        sys.exit(r)

    with open(input_graph_json_path, 'r') as input_graph_json_file:
        input_graph_json = json.load(input_graph_json_file)

    if input_graph_json == None:
        print "load %s failed" % input_graph_json_path
        sys.exit(-1)

    metis_fmt_graph = {}
    edge_num = 0
    vertex_num = 0

    origin_vertex_list = sorted([vertex["v"] for vertex in input_graph_json["assign"]])
    vertex_map = {}
    for origin_vertex_id in origin_vertex_list:
        vertex_map[origin_vertex_id] = vertex_num + 1
        vertex_num += 1


    for edge in input_graph_json["query"]:
        if edge.has_key("cn"):
            continue
        if not metis_fmt_graph.has_key(vertex_map[edge["a"]]):
            metis_fmt_graph[vertex_map[edge["a"]]] = list()
        if not metis_fmt_graph.has_key(vertex_map[edge["b"]]):
            metis_fmt_graph[vertex_map[edge["b"]]] = list()
        metis_fmt_graph[vertex_map[edge["a"]]].append(vertex_map[edge["b"]])
        metis_fmt_graph[vertex_map[edge["b"]]].append(vertex_map[edge["a"]])
        edge_num += 1

    metis_graph_str = ""
    # generate metis graph header
    metis_graph_str += "%s %s\n" % (str(vertex_num), str(edge_num))
    # generate vertex info
    for i in range(1, vertex_num + 1):
        if metis_fmt_graph.has_key(i):
            vertex_str = ""
            for vertex in metis_fmt_graph[i]:
                vertex_str += "%s " % str(vertex)
            metis_graph_str += "%s\n" % vertex_str[:-1]
        else:
            metis_graph_str += "\n"

    with open("%s/output/origin_graph_metis" % output_graph_dir, 'w') as origin_graph_metis_file:
        origin_graph_metis_file.write(metis_graph_str)

    # todo
    partition_num = vertex_num / int(avg_volume)

    r = os.system("%s %s/output/origin_graph_metis %s" % (gpmetis_path, output_graph_dir, str(partition_num)))
    if r != 0:
        print "gpmetis failed"
        sys.exit(r)
    r = os.system("rm %s/output/origin_graph_metis" % output_graph_dir)
    if r != 0:
        print "rm %s/output/origin_graph_metis failed" % output_graph_dir
        sys.exit(r)

    vertex_partition_dict = {}
    new_graphs = {}
    edge_lost = 0
    with open("%s/output/origin_graph_metis.part.%s" % (output_graph_dir, str(partition_num)), 'r') as partition_metis_file:
        vertex_partition_list = map(lambda x: int(x), partition_metis_file.read().split("\n")[:-1])
        for partition_id in range(partition_num):
            vertex_partition_dict[partition_id] = []

        for vertex_id in range(len(vertex_partition_list)):
            vertex_partition_dict[vertex_partition_list[vertex_id]].append(origin_vertex_list[vertex_id])

        # generate sub-graph using partitions
        # init
        for partition_id in range(partition_num):
            new_graphs[partition_id] = {"assign":[], "query":[]}
        # assign
        for assign_item in input_graph_json["assign"]:
            partition_id = vertex_partition_list[vertex_map[assign_item["v"]] - 1]
            new_graphs[partition_id]["assign"].append(assign_item)
        # query
        for query_item in input_graph_json["query"]:
            if query_item.has_key("a"):
                partition_ida = vertex_partition_list[vertex_map[query_item["a"]] - 1]
                partition_idb = vertex_partition_list[vertex_map[query_item["b"]] - 1]
                if partition_ida != partition_idb:
                    edge_lost += 1
                    continue
                new_graphs[partition_id]["query"].append(query_item)
            else:
                inequal_groups = {}
                for partition_id in range(partition_num):
                    inequal_groups[partition_id] = []
                for origin_vertex_id in query_item["n"]:
                    partition_id = vertex_partition_list[vertex_map[origin_vertex_id] - 1]
                    inequal_groups[partition_id].append(origin_vertex_id)
                for partition_id in range(partition_num):
                    if len(inequal_groups[partition_id]) > 1:
                        new_graphs[partition_id]["query"].append({"cn": "!=", "n": inequal_groups[partition_id]})


    r = os.system("rm %s/output/origin_graph_metis.part.%s" % (output_graph_dir, str(partition_num)))
    if r != 0:
        print "rm %s/output/origin_graph_metis.part.%s failed" % (output_graph_dir, str(partition_num))
        sys.exit(r)

    print "edge_lost: %s" % str(edge_lost)
    output_base_name = input_graph_json_path.split("/")[-1][:-len(".json")]
    for i in range(partition_num):
        with open("%s/output/%s_%s.json" % (output_graph_dir, output_base_name, str(i)), 'w') as outfile:
            json.dump(new_graphs[i], outfile)


def parse_args():
    """
    parse command line input
    """
    parser = argparse.ArgumentParser(description="cut the application graph")
    parser.add_argument("-i", action="store", dest="input_graph_json_path",
                        required=True, help="path to input graph json")
    parser.add_argument("-o", action="store", dest="output_graph_dir",
                        required=True, help="directory to contain output graph jsons")
    parser.add_argument("-m", action="store", dest="gpmetis_path",
                        required=True, help="path to gpmetis")
    parser.add_argument("-v", action="store", dest="avg_volume",
                        required=True, help="average volume of the subgraph")

    options = parser.parse_args()
    # print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.input_graph_json_path, opts.output_graph_dir, opts.gpmetis_path, opts.avg_volume)

    return


if __name__ == "__main__":
    main()
