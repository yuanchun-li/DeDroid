import json
import os
import hashlib
import networkx as nx
from networkx.readwrite import json_graph
from networkx.algorithms import isomorphism


STATIC_NODE_TYPES = \
    [u'package_lib', u'class_lib', u'method_lib', u'field_lib',
     # u'package_3lib', u'class_3lib', u'method_3lib', u'field_3lib',
     # u'package', u'class', u'method', u'field',
     u'const',
     u'modifier', u'type']

THIRD_PARTY_LIB_NODE_TYPES = \
    [u'package_lib', u'class_lib', u'method_lib', u'field_lib',
     # u'package_3lib', u'class_3lib', u'method_3lib', u'field_3lib',
     # u'package', u'class', u'method', u'field',
     u'const',
     # u'modifier',
     u'type']

THIRD_PARTY_LIB_EDGE_TYPES = \
    [u'C_F_contains', u'C_M_contains', u'P_C_contains', u'P_P_contains',
     u'C_M_modifier', u'F_M_modifier', u'M_M_modifier',
     u'F_C_instance', u'F_T_instance', u'F_[C_instance', u'F_[T_instance',
     u'M_C_parameter', u'M_C_refer', u'M_C_return', u'M_F_DU', u'M_F_refer', u'M_M_override', u'M_M_refer',
     u'M_T_parameter', u'M_T_return', u'M_[C_parameter', u'M_[C_return', u'M_[T_parameter', u'M_[T_return']
    # [u'C_C_implement', u'C_C_inherit', u'C_F_contains', u'C_M_contains', u'C_M_modifier', u'F_C_instance', u'F_F_DU',
    #  u'F_M_DU', u'F_M_modifier', u'F_T_instance', u'F_[C_instance', u'F_[T_instance', u'M_C_parameter', u'M_C_refer',
    #  u'M_C_return', u'M_F_DU', u'M_F_refer', u'M_M_modifier', u'M_M_override', u'M_M_refer', u'M_T_parameter',
    #  u'M_T_return', u'M_[C_parameter', u'M_[C_return', u'M_[T_parameter', u'M_[T_return', u'P_C_contains',
    #  u'P_P_contains']


class DERG(object):
    def __init__(self, derg_path=None, derg_dict=None):
        self.derg_path = None
        self.g = None
        if derg_path:
            self.derg_path = derg_path
            derg_dict = json.load(open(derg_path))
            self.g = self.load_nx_graph(derg_dict)
        elif derg_dict:
            self.derg_path = derg_dict['derg_path']
            self.g = self.load_nx_graph(derg_dict)

        self.method_hashes = None

    @staticmethod
    def load_nx_graph(derg_dict):
        g = nx.DiGraph()
        for node in derg_dict['nodes']:
            g.add_node(node['id'], **node)
        for edge in derg_dict['edges']:
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

    def to_dict(self):
        g_dict = json_graph.node_link_data(self.g)
        g_dict['edges'] = g_dict.pop('links')
        g_dict['derg_path'] = self.derg_path

    def export(self, output_path):
        json.dump(self.to_dict(), open(output_path, 'w'))

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

    def get_package_derg(self, package):
        subgraph = nx.DiGraph()

        for node_id in self.g.nodes:
            node = self.g.nodes[node_id]
            node_type = node['type']
            if node_type in STATIC_NODE_TYPES:
                continue
            node_sig = node['sig']
            included = False
            if node_type.startswith('package') or node_type.startswith('class'):
                included = node_sig.startswith(package)
            elif node_type.startswith('method') or node_type.startswith('field'):
                included = node_sig.startswith('<' + package)
            if not included:
                continue
            if node_type.startswith('method'):
                node = node.copy()
                node['hash'] = self.get_method_hash(node_id)
            subgraph.add_node(node_id, **node)
            for child_node_id in self.g[node_id]:
                child_node = self.g.nodes[child_node_id]
                edge = self.g[node_id][child_node_id]
                if child_node['type'] in THIRD_PARTY_LIB_NODE_TYPES and edge['relation'] in THIRD_PARTY_LIB_EDGE_TYPES:
                    subgraph.add_node(child_node_id, **child_node)
                    subgraph.add_edge(node_id, child_node_id, **edge)

        package_derg = DERG()
        package_derg.derg_path = "%s->package:%s" % (self.derg_path, package)
        package_derg.g = subgraph.copy()
        return package_derg

    def get_method_hash(self, method_node_id):
        """
        method hashes can be used to identify 3-rd party library
        :param method_node_id:
        :return:
        """
        static_child_node_names = []
        for child_node_id in self.g[method_node_id]:
            child_node = self.g.nodes[child_node_id]
            if child_node['type'] in THIRD_PARTY_LIB_NODE_TYPES:
                static_child_node_names.append(child_node['name'])
        method_hash = hashlib.md5("\n".join(sorted(static_child_node_names))).hexdigest()
        # method_hash = "\n".join(sorted(static_child_node_names))
        return method_hash

    def get_method_hashes(self):
        """
        get a set of method hashes of all methods in the derg
        :return: a set of method hashes
        """
        if not self.method_hashes:
            self.method_hashes = set()
            for node_id in self.g.nodes:
                node = self.g.nodes[node_id]
                node_type = node['type']
                if node_type in STATIC_NODE_TYPES:
                    continue
                if node_type.startswith('method'):
                    self.method_hashes.add(self.get_method_hash(node_id))
        return self.method_hashes

    def get_kg_mappings(self):
        # get name mappings in knowledge graph
        return KnowledgeGraph.get_unknown_node_name_mappings(self)


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


class ThridPartyLibRepo(object):
    def __init__(self):
        self.lib_packages = []

    def load(self, repo_path):
        self.lib_packages = json.load(open(repo_path))
        for lib_package in self.lib_packages:
            lib_package['derg'] = DERG(derg_dict=lib_package['derg'])

    def export(self, output_path):
        for lib_package in self.lib_packages:
            lib_package['derg'] = lib_package['derg'].to_dict()
        json.dump(self.lib_packages, open(output_path, 'w'), indent=2)

    def collect_from_dergs(self, dergs):
        for derg in dergs:
            packages = derg.get_packages()
            for package in packages:
                sub_derg = derg.get_package_derg(package)
                self._update_lib_packages(sub_derg, package)
        print("Found %d unique packages in total." % len(self.lib_packages))
        self._clear_uncommon_lib_packages()

    def _update_lib_packages(self, new_derg, package):
        print("Processing %s" % new_derg.derg_path)
        for lib_package in self.lib_packages:
            lib_package_derg = lib_package['derg']
            lib_package_hashes = lib_package_derg.get_method_hashes()
            new_package_hashes = new_derg.get_method_hashes()
            if lib_package_hashes.issuperset(new_package_hashes):
                lib_package['paths'].append(new_derg.derg_path)
                lib_package['packages'].append(package)
                return
            elif lib_package_hashes.issubset(new_package_hashes):
                lib_package['paths'].append(new_derg.derg_path)
                lib_package['packages'].append(package)
                lib_package['derg'] = new_derg
                return
        self.lib_packages.append({
            'paths': [new_derg.derg_path],
            'packages': [package],
            'derg': new_derg
        })

    def _clear_uncommon_lib_packages(self, threshold=1):
        uncommon_lib_packages = []
        for lib_package in self.lib_packages:
            paths = lib_package['paths']
            if len(paths) <= threshold:
                uncommon_lib_packages.append(lib_package)
        for uncommon_lib_package in uncommon_lib_packages:
            self.lib_packages.remove(uncommon_lib_package)
        print("Found %d lib packages after clearing uncommon ones (threshold %d)."
              % (len(self.lib_packages), threshold))

    @staticmethod
    def is_same_derg(derg1, derg2):
        GM = isomorphism.DiGraphMatcher(derg1.g, derg2.g,
                                        node_match=ThridPartyLibRepo.node_match,
                                        edge_match=ThridPartyLibRepo.edge_match)
        return GM.is_isomorphic()

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
        elif n_type.startswith('method'):
            return n1['hash'] == n2['hash']
        else:
            return True

    def match_3lib_package(self, package_derg):
        for lib_package in self.lib_packages:
            lib_derg = lib_package['derg']
            if not lib_derg.get_method_hashes().issuperset(package_derg.get_method_hashes()):
                continue
            GM = isomorphism.DiGraphMatcher(lib_derg.g, package_derg.g,
                                            node_match=ThridPartyLibRepo.node_match,
                                            edge_match=ThridPartyLibRepo.edge_match)
            if GM.subgraph_is_isomorphic():
                return lib_package, GM.mapping
        return None, None
