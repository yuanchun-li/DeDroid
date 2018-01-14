#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import argparse

KNOWN_RELATION_NAMES = \
    ['CC_implement', 'CC_inherit', 'CC_outer',
     'FT_instance',
     'MC_exception', 'MM_override', 'MT_parameter', 'MT_return', 'MX_refer',
     'XS_modifier', 'XX_DU', 'XX_contains']

KNOWN_NODE_TYPES = \
    ['package_LIB', 'method_LIB', 'field_LIB', 'class_LIB',
     'type', 'modifier']

PRIMITIVE_TYPES = \
    ['int', 'long', 'float', 'double', 'boolean', 'byte', 'java.lang.String']

INCLUDED_NODE_TYPES = \
    ['package', 'class', 'method', 'field',
     'package_3LIB', 'method_3LIB', 'field_3LIB', 'class_3LIB',
     'package_LIB', 'method_LIB', 'field_LIB', 'class_LIB',
     'type', 'modifier']

INCLUDED_RELATION_NAMES = \
    ['CC_implement', 'CC_inherit', 'CC_outer',
     'FT_instance',
     'MC_exception', 'MM_override', 'MT_parameter', 'MT_return', 'MX_refer',
     'XS_modifier', 'XX_DU', 'XX_contains']


class DERG(object):
    def __init__(self, derg_path):
        self.derg_path = derg_path
        self.derg = json.load(open(derg_path))

    def get_known_node_names(self):
        known_node_names = set()
        for node in self.derg['nodes']:
            if self.is_known(node):
                known_node_names.add(self.get_node_name(node))
        return known_node_names

    @staticmethod
    def is_known(node):
        return node['type'] in KNOWN_NODE_TYPES

    @staticmethod
    def get_node_name(node):
        name = node['name']
        if node['type'] == 'modifier':
            name = 'modifier:' + name
        elif node['type'] == 'type':
            if name.endswith('[]') and name[:name.rfind('[')] not in PRIMITIVE_TYPES:
                name = '*[]'
            name = 'type:' + name
        elif node['type'].endswith('_LIB'):
            name = 'lib:' + name.replace(' ', '~')
        # elif node['type'].endswith('_3LIB'):
        #     name = '3lib:' + name.replace(' ', '~')
        return name


def get_dergs(dergs_dir, derg_name):
    dergs = []
    for path, dir_names, file_names in os.walk(dergs_dir):
        for file_name in file_names:
            if file_name == derg_name:
                derg_path = os.path.join(path, file_name)
                dergs.append(DERG(derg_path))
    return dergs


class KnowledgeGraph(object):
    def __init__(self, dergs):
        self.dergs = dergs
        self._kg_id_offset = 0
        self.known_entity_name_to_kg_id = {}
        self.known_relation_name_to_kg_id = {}
        self._kg_entity_name_to_id = []
        self._kg_relation_name_to_id = []
        self._kg_triples = []

        self.get_known_nodes_and_relations()
        self.gen_knowledge_graph()
        self._kg_entity_name_to_id.sort(key=lambda x: x[1])
        self._kg_relation_name_to_id.sort(key=lambda x: x[1])

    def get_known_nodes_and_relations(self):
        known_node_names = set()
        for g in self.dergs:
            known_node_names = known_node_names.union(g.get_known_node_names())

        kg_id_i = self._kg_id_offset
        for node_name in sorted(known_node_names):
            self.known_entity_name_to_kg_id[node_name] = kg_id_i
            kg_id_i += 1
        self._kg_id_offset = kg_id_i
        self._kg_entity_name_to_id.extend(self.known_entity_name_to_kg_id.items())

        i = 0
        for relation_name in sorted(KNOWN_RELATION_NAMES):
            self.known_relation_name_to_kg_id[relation_name] = i
            i += 1
        self._kg_relation_name_to_id.extend(self.known_relation_name_to_kg_id.items())

    def gen_knowledge_graph(self):
        for g in self.dergs:
            self._get_knowledge_graph_for_derg(g)

    def _get_knowledge_graph_for_derg(self, g):
        node_id_to_kg_id = {}
        unknown_node_name_to_kg_id = {}
        kg_triples = []

        kg_id_i = self._kg_id_offset
        for node in g.derg['nodes']:
            if node['type'] not in INCLUDED_NODE_TYPES:
                continue
            node_name = g.get_node_name(node)
            node_id = node['id']
            if node_name in self.known_entity_name_to_kg_id:
                kg_id = self.known_entity_name_to_kg_id[node_name]
            else:
                kg_id = kg_id_i
                node_global_name = "%s->node:%d" % (g.derg_path, node_id)
                unknown_node_name_to_kg_id[node_global_name] = kg_id
                kg_id_i += 1
            node_id_to_kg_id[node_id] = kg_id
        self._kg_id_offset = kg_id_i

        for edge in g.derg['edges']:
            s_id = edge['source']
            t_id = edge['target']
            relation_name = edge['relation']
            if relation_name not in INCLUDED_RELATION_NAMES \
                    or s_id not in node_id_to_kg_id \
                    or t_id not in node_id_to_kg_id:
                continue
            relation_id = self.known_relation_name_to_kg_id[relation_name]
            s_kg_id = node_id_to_kg_id[s_id]
            t_kg_id = node_id_to_kg_id[t_id]
            kg_triples.append((s_kg_id, t_kg_id, relation_id))

        self._kg_triples.extend(kg_triples)
        self._kg_entity_name_to_id.extend(unknown_node_name_to_kg_id.items())

    def output(self, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        triple2id_file = open(os.path.join(output_dir, "train2id.txt"), 'w')
        triple2id_lines = []
        triple2id_lines.append("%d\n" % len(self._kg_triples))
        for s_id, t_id, relation_id in self._kg_triples:
            line = "%d\t%d\t%d\n" % (s_id, t_id, relation_id)
            triple2id_lines.append(line.encode('utf-8'))
        triple2id_file.writelines(triple2id_lines)
        triple2id_file.close()

        entity2id_file = open(os.path.join(output_dir, "entity2id.txt"), 'w')
        entity2id_lines = []
        entity2id_lines.append("%d\n" % len(self._kg_entity_name_to_id))
        for entity_name, kg_id in self._kg_entity_name_to_id:
            line = "%s\t%d\n" % (entity_name, kg_id)
            entity2id_lines.append(line.encode('utf-8'))
        entity2id_file.writelines(entity2id_lines)
        entity2id_file.close()

        relation2id_file = open(os.path.join(output_dir, "relation2id.txt"), 'w')
        relation2id_lines = []
        relation2id_lines.append("%d\n" % len(self.known_relation_name_to_kg_id))
        for relation_name, kg_id in self._kg_relation_name_to_id:
            line = "%s\t%d\n" % (relation_name, kg_id)
            relation2id_lines.append(line.encode('utf-8'))
        relation2id_file.writelines(relation2id_lines)
        relation2id_file.close()


def run(dergs_dir, output_dir, derg_name):
    dergs = get_dergs(dergs_dir, derg_name)
    kg = KnowledgeGraph(dergs)
    kg.output(output_dir)


def parse_args():
    """
    parse command line input
    generate options including input proguard-generated mappings and predict mappings
    """
    parser = argparse.ArgumentParser(
        description="covert the dergs in a directory to a knowledge graph.")
    parser.add_argument("-dergs_dir", action="store", dest="dergs_dir",
                        required=True, help="path to the dir of dergs")
    parser.add_argument("-output_dir", action="store", dest="output_dir",
                        required=True, help="path to output dir")
    parser.add_argument("-derg_name", action="store", dest="derg_name", default="derg.json",
                        required=False, help="the name of derg")

    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.dergs_dir, opts.output_dir, opts.derg_name)

    return


if __name__ == "__main__":
    main()
