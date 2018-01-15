import argparse
import os
import json

import utils


def run(derg_path, new_derg_path):
    """

    :param derg_path:
    :param new_derg_path
    """

    derg_path = os.path.abspath(derg_path)

    derg_file = open(derg_path, 'r')
    derg = json.load(derg_file)
    derg_file.close()

    new_derg_dir = os.path.dirname(new_derg_path)
    if not os.path.exists(new_derg_dir):
        os.makedirs(new_derg_dir)

    edge_names = set()
    included_node_ids = set()

    for edge in derg['edges']:
        edge_name = edge['relation']
        s_node = derg['nodes'][edge['source']]
        t_node = derg['nodes'][edge['target']]

        s_node_list_type = get_list_element_type(s_node)
        if s_node_list_type:
            s_node = get_type_node(derg, s_node_list_type)
            edge['source'] = s_node['id']
            s_node_t = '[' + s_node['type'][0].upper()
        else:
            s_node_t = s_node['type'][0].upper()

        t_node_list_type = get_list_element_type(t_node)
        if t_node_list_type:
            t_node = get_type_node(derg, t_node_list_type)
            edge['target'] = t_node['id']
            t_node_t = '[' + t_node['type'][0].upper()
        else:
            t_node_t = t_node['type'][0].upper()

        new_edge_name = s_node_t + '_' + t_node_t + edge_name[2:]
        edge['relation'] = new_edge_name
        edge_names.add(new_edge_name)
        included_node_ids.add(s_node['id'])
        included_node_ids.add(t_node['id'])
    print(sorted(edge_names))

    node_types = set()
    type_names = set()
    old_nodes = derg['nodes']
    new_nodes = []
    new_node_id = 0
    for node in old_nodes:
        node_id = node['id']
        if node_id not in included_node_ids:
            continue

        node['id'] = new_node_id
        new_node_id += 1
        new_nodes.append(node)

        node_type = node['type'].lower()
        node['type'] = node_type
        node_types.add(node_type)

        if node_type == 'type':
            type_names.add(node['name'])

        if node['sig'] == "":
            node['sig'] = node['name']
        if 'recovered_sig' in node:
            node.pop('recovered_sig')

    print(sorted(node_types))
    print(sorted(type_names))

    for edge in derg['edges']:
        s_node = derg['nodes'][edge['source']]
        t_node = derg['nodes'][edge['target']]
        edge['source'] = s_node['id']
        edge['target'] = t_node['id']
        included_node_ids.add(t_node['id'])

    derg['nodes'] = new_nodes

    new_derg_file = open(new_derg_path, 'w')
    json.dump(derg, new_derg_file, indent=2)
    new_derg_file.close()


def get_type_node(derg, type_name):
    for node in derg['nodes']:
        if (node['type'].startswith('class') or node['type'].startswith('type'))\
                and (node['name'] == type_name or node['sig'] == type_name):
            return node
    print("type node not found: %s" % type_name)
    new_node = {
      "name": type_name,
      "sig": "",
      "type": 'type' if type_name in utils.PRIMITIVE_TYPES else "class_lib",
      "id": len(derg['nodes'])
    }
    derg['nodes'].append(new_node)
    return new_node


def get_list_element_type(node):
    node_type = node['type']
    node_name = node['name']
    if node_type == 'type' and node_name.endswith('[]'):
        return node_name[:node_name.find('[')]


def parse_args():
    """
    parse command line input
    generate options including input proguard-generated mappings and predict mappings
    """
    parser = argparse.ArgumentParser(
        description="process the original derg")
    parser.add_argument("-derg", action="store", dest="derg_path",
                        required=True, help="path to the original derg")
    parser.add_argument("-new_derg", action="store", dest="new_derg_path",
                        required=True, help="path to the new derg with original names")

    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.derg_path, opts.new_derg_path)

    return


if __name__ == "__main__":
    main()
