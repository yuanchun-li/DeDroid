import json
import os
import networkx as nx
from networkx.readwrite import json_graph


STATIC_NODE_TYPES = \
    [u'package_lib', u'class_lib', u'method_lib', u'field_lib',
     # u'package_3lib', u'class_3lib', u'method_3lib', u'field_3lib',
     # u'package', u'class', u'method', u'field',
     u'const',
     u'modifier', u'type']

METHOD_HASH_NODE_TYPES = \
    [u'package_lib', u'class_lib', u'method_lib', u'field_lib',
     # u'package_3lib', u'class_3lib', u'method_3lib', u'field_3lib',
     # u'package', u'class', u'method', u'field',
     u'const',
     u'type']


class DERG(object):
    def __init__(self, derg_path):
        self.derg_path = derg_path
        self.g = self.load_nx_graph(derg_path)

    @staticmethod
    def load_nx_graph(derg_path):
        g_data = json.load(open(derg_path))
        g = nx.DiGraph()
        for node in g_data['nodes']:
            g.add_node(node['id'], **node)
        for edge in g_data['edges']:
            g.add_edge(edge['source'], edge['target'], **edge)
        return g

    def nodes(self):
        for nid in self.g.nodes:
            yield self.g.nodes[nid]

    def edges(self):
        for eid in self.g.edges:
            yield self.g.edges[eid]

    def get_node_global_id(self, node):
        return '%s->node:%d' % (self.derg_path, node['id'])

    def export(self, output_path):
        g_data = json_graph.node_link_data(self.g)
        g_data['edges'] = g_data.pop('links')
        json.dump(g_data, open(output_path, 'w'))

    def get_packages(self):
        packages = set()
        for node in self.nodes():
            node_type = node['type']
            if node_type.startswith('class') and not node_type.endswith('_lib'):
                class_sig = node['sig']
                package = class_sig[:class_sig.rfind('.')]
                packages.add(package)

        sub_packages = set()
        for package in packages:
            for another_package in packages:
                if len(package) >= len(another_package):
                    continue
                if another_package.startswith(package):
                    sub_packages.add(another_package)

        return packages - sub_packages

    def get_package_subgraph(self, package):
        # TODO fix this
        included_node_ids = set()
        for node_id in self.g.nodes:
            node = self.g.nodes[node_id]
            node_type = node['type']
            if node_type in STATIC_NODE_TYPES:
                continue
            node_sig = node['sig']
            included = False
            if node_type.startswith('class'):
                included = node_sig.startswith(package)
            elif node_type.startswith('method') or node_type.startswith('field'):
                included = node_sig.startswith('<' + package)
            if not included:
                continue
            included_node_ids.add(node_id)
            for child_node_id in self.g[node_id]:
                child_node = self.g.nodes[child_node_id]
                if child_node['type'] in STATIC_NODE_TYPES:
                    included_node_ids.add(child_node_id)
        return self.g.subgraph(included_node_ids)

    def get_package_method_hashes(self, package):
        """
        method hashes can be used to identify 3-rd party library
        :param package:
        :return: a set of method hashes
        """
        import hashlib
        method_hashes = set()
        for node_id in self.g.nodes:
            node = self.g.nodes[node_id]
            node_type = node['type']
            if node_type in STATIC_NODE_TYPES:
                continue
            node_sig = node['sig']
            if not (node_type.startswith('method') and node_sig.startswith('<' + package)):
                continue
            static_child_node_names = []
            for child_node_id in self.g[node_id]:
                child_node = self.g.nodes[child_node_id]
                if child_node['type'] in METHOD_HASH_NODE_TYPES:
                    static_child_node_names.append(child_node['name'])
            # method_hash = hashlib.md5("\n".join(sorted(static_child_node_names))).hexdigest()
            method_hash = "\n".join(sorted(static_child_node_names))
            method_hashes.add(method_hash)
        return method_hashes

    @staticmethod
    def edge_match(e1, e2):
        return e1['relation'] == e2['relation']

    @staticmethod
    def node_match(n1, n2):
        n_type = n1['type']
        if not n2['type'].startswith(n_type):
            return False
        if n_type in STATIC_NODE_TYPES:
            return n1['sig'] == n2['sig']
        else:
            return True


KNOWN_RELATION_NAMES = \
    [u'C_C_implement', u'C_C_inherit', u'C_F_contains', u'C_M_contains', u'C_M_modifier', u'F_C_instance', u'F_F_DU',
     u'F_M_DU', u'F_M_modifier', u'F_T_instance', u'F_[C_instance', u'F_[T_instance', u'M_C_parameter', u'M_C_refer',
     u'M_C_return', u'M_F_DU', u'M_F_refer', u'M_M_modifier', u'M_M_override', u'M_M_refer', u'M_T_parameter',
     u'M_T_return', u'M_[C_parameter', u'M_[C_return', u'M_[T_parameter', u'M_[T_return', u'P_C_contains',
     u'P_P_contains']

KNOWN_NODE_TYPES = \
    [u'package_lib', u'class_lib', u'method_lib', u'field_lib',
     # u'package_3lib', u'class_3lib', u'method_3lib', u'field_3lib',
     # u'package', u'class', u'method', u'field',
     # u'const',
     u'modifier', u'type']

INCLUDED_NODE_TYPES = \
    [u'package_lib', u'class_lib', u'method_lib', u'field_lib',
     u'package_3lib', u'class_3lib', u'method_3lib', u'field_3lib',
     u'package', u'class', u'method', u'field',
     # u'const',
     u'modifier', u'type']

INCLUDED_RELATION_NAMES = KNOWN_RELATION_NAMES


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

    @staticmethod
    def get_known_node_names(derg):
        known_node_names = set()
        for node in derg.nodes():
            if KnowledgeGraph.is_known(node):
                known_node_names.add(KnowledgeGraph.get_node_name(node))
        return known_node_names

    @staticmethod
    def is_known(node):
        return node['type'] in KNOWN_NODE_TYPES or (node['name'] == 'DERG_ROOT' and node['type'] == 'package')

    @staticmethod
    def get_node_name(node):
        if KnowledgeGraph.is_known(node):
            return '%s:%s' % (node['type'], node['sig'].replace(' ', ''))
        else:
            return node['name']

    @staticmethod
    def get_unknown_node_name_mappings(derg):
        name_mappings = []
        for node in derg.nodes():
            if KnowledgeGraph.is_known(node):
                continue
            if node['type'] not in INCLUDED_NODE_TYPES:
                continue
            original_name = node['original_name']
            global_id = derg.get_node_global_id(node)
            name_mappings.append((global_id, original_name))
        return name_mappings

    def get_known_nodes_and_relations(self):
        known_node_names = set()
        for derg in self.dergs:
            known_node_names = known_node_names.union(KnowledgeGraph.get_known_node_names(derg))

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
        for derg in self.dergs:
            self._gen_knowledge_graph_for_derg(derg)

    def _gen_knowledge_graph_for_derg(self, derg):
        node_id_to_kg_id = {}
        unknown_node_global_id_to_kg_id = {}
        kg_triples = []

        kg_id_i = self._kg_id_offset
        for node in derg.nodes():
            if node['type'] not in INCLUDED_NODE_TYPES:
                continue
            node_name = KnowledgeGraph.get_node_name(node)
            node_id = node['id']
            if node_name in self.known_entity_name_to_kg_id:
                kg_id = self.known_entity_name_to_kg_id[node_name]
            else:
                kg_id = kg_id_i
                node_global_id = derg.get_node_global_id(node)
                unknown_node_global_id_to_kg_id[node_global_id] = kg_id
                kg_id_i += 1
            node_id_to_kg_id[node_id] = kg_id
        self._kg_id_offset = kg_id_i

        for edge in derg.edges():
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
        self._kg_entity_name_to_id.extend(unknown_node_global_id_to_kg_id.items())

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
