# encoding=utf8

import json, argparse, os, operator, logging
from pymongo import MongoClient

METHOD_PROFILE_DB = "liycdata"
METHOD_PROFILE_COLLECTION = "lib_method_profiles"

LOG_FORMAT = "%(asctime)-15s %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger("recover_derg")
logger.setLevel(logging.INFO)


def parse_args():
    """
    parse command line input
    generate options including host name, port number
    """
    parser = argparse.ArgumentParser(description="recover identifiers in derg")
    parser.add_argument("-method_profile", action="store", dest="method_profile", required=True,
                        help="file path of method_profile.json")
    parser.add_argument("-derg", action="store", dest="derg", required=True,
                        help="file path of derg.json")
    parser.add_argument("-o", action="store", dest="output_dir", default=".",
                        help="file path to output dir")

    options = parser.parse_args()
    logger.info(options)
    return options


def main():
    """
    the main function
    it starts a droidbot according to the arguments given in cmd line
    """
    opts = parse_args()

    if not os.path.exists(opts.derg):
        logger.warning("derg not exist")
        return

    if not os.path.exists(opts.method_profile):
        logger.warning("method profile not exist")
        return

    recover_derg = RecoverDERG(opts.derg, opts.method_profile, opts.output_dir)
    recover_derg.recover()
    recover_derg.export()
    recover_derg.close()

    return


class RecoverDERG(object):
    def __init__(self, derg_file, method_profile_file, output_dir):
        self.g = DERG(derg_file)
        self.method_profile = json.load(open(method_profile_file, "r"))
        self.node_profile = self.get_node_profile_map(self.method_profile)
        self.output_dir = output_dir

        self.method_nodes_matched_profiles = {}
        self.nodes_matched_names = {}
        self.nodes_method_count = {}

        self.mongo_client = MongoClient()
        self.method_profile_col = self.mongo_client[METHOD_PROFILE_DB][METHOD_PROFILE_COLLECTION]

        self.third_party_packages = {}
        self.recovered_node_relations = {}

    def get_node_profile_map(self, method_profile):
        node_profile = {}
        for profile in method_profile:
            node_id = int(profile['DERG_id'])
            node_profile[node_id] = profile
        return node_profile

    def export(self):
        recovered_derg_file_path = os.path.join(self.output_dir, "recovered_derg.json")
        json.dump(self.g.derg, open(recovered_derg_file_path, 'w'), indent=2)

    def _match_method_node_profile(self):
        p = 0
        count = len(self.method_profile)
        for profile in self.method_profile:
            p += 1
            if p % 100 == 0 or p == count:
                log_msg = "matching method profile %s: %.0f%%" % (profile['id'], p * 100.0 / count)
                logger.debug(log_msg)

            sig = profile['sig']
            minified_id = profile['id']
            DERG_id = int(profile['DERG_id'])

            cur = self.method_profile_col.find({"sig": sig})
            # filter out large profiles to speed up
            if cur.count() > 10:
                continue

            method_ids = filter_methods(cur.distinct("id"), minified_id)
            self.method_nodes_matched_profiles[DERG_id] = method_ids

    def _down_top_propagation(self):
        p = 0
        count = len(self.method_profile)
        for profile in self.method_profile:
            p += 1
            if p % 100 == 0 or p == count:
                log_msg = "down-top propagation %s: %.0f%%" % (profile['id'], p * 100.0 / count)
                logger.debug(log_msg)

            DERG_id = int(profile['DERG_id'])
            if DERG_id not in self.method_nodes_matched_profiles:
                continue

            method_ids = self.method_nodes_matched_profiles[DERG_id]
            parent_nodes = self.g.get_parent_nodes(DERG_id)[::-1][1:]
            parent_nodes_choices = []
            for parent_node in parent_nodes:
                parent_nodes_choices.append(set())

            for method_id in method_ids:
                method_id_segs = method_id.split('.')
                for i in range(0, len(method_id_segs)):
                    parent_nodes_choices[i].add(".".join(method_id_segs[:i+1]))

            for i in range(0, len(parent_nodes)):
                parent_node = parent_nodes[i]
                parent_node_choices = parent_nodes_choices[i]

                safe_increase(self.nodes_method_count, parent_node)

                if parent_node not in self.nodes_matched_names:
                    self.nodes_matched_names[parent_node] = {}
                for parent_node_choice in parent_node_choices:
                    safe_increase(self.nodes_matched_names[parent_node], parent_node_choice)

    def _top_down_propagation(self):
        derg = self.g.derg
        p = 0
        count = len(derg['nodes'])
        for node in derg['nodes']:
            p += 1
            if p % 100 == 0 or p == count:
                log_msg = "top-down class recovering: %.0f%%" % (p * 100.0 / count)
                logger.debug(log_msg)

            # recover package nodes
            node_id = node['id']
            node_type = node['type']

            if node_type in ["package", "class"]:
                if node_id not in self.nodes_method_count or node_id not in self.nodes_matched_names:
                    continue

                method_count = self.nodes_method_count[node_id]
                if method_count == 0:
                    continue

                recover_choices = self.nodes_matched_names[node_id]
                if len(recover_choices) == 0:
                    continue

                best_choice_score = max(recover_choices.values())
                best_choice_confidence = best_choice_score * 1.0 / method_count

                if best_choice_confidence < 0.6:
                    continue

                best_choices = []
                for choice in recover_choices:
                    if recover_choices[choice] == best_choice_score:
                        best_choices.append(choice)
                if len(best_choices) > 1:
                    continue

                best_choice = best_choices[0]
                self.g.recover_node_with_sig(node_id, best_choice)

                if node_type == "package":
                    self.third_party_packages[node['sig']] = node['recovered_sig']

        # mark third party lib nodes
        self.g.mark_3lib_nodes(self.third_party_packages)

        p = 0
        count = len(self.method_profile)
        for profile in self.method_profile:
            p += 1
            if p % 100 == 0:
                log_msg = "top-down method recovering: %.0f%%" % (p * 100.0 / count)
                logger.debug(log_msg)

            # recover package nodes
            node_id = int(profile['DERG_id'])
            node = derg['nodes'][node_id]
            node_type = node['type']
            if node_type == "method_3LIB":
                class_node_id = self.g.belongto_map[node_id]
                class_node = derg['nodes'][class_node_id]
                cur = self.method_profile_col.find({"sig": profile['sig'], "id": {'$regex': '^%s' % class_node['recovered_sig']}})
                # print "matched %d methods" % cur,count()
                matched_profile_ids = cur.distinct('id')
                if len(matched_profile_ids) == 1:
                    matched_profile = cur.next()
                    matched_profile_id = matched_profile['id']
                    self.g.recover_node_with_sig(node_id, matched_profile_id)
                    continue
                package_node_id = self.g.belongto_map[class_node_id]
                package_node = derg['nodes'][package_node_id]
                cur = self.method_profile_col.find({"sig": profile['sig'], "id": {'$regex': '^%s' % package_node['recovered_sig']}})
                matched_profile_ids = cur.distinct('id')
                if len(matched_profile_ids) == 1:
                    matched_profile = cur.next()
                    matched_profile_id = matched_profile['id']
                    self.g.recover_node_with_sig(node_id, matched_profile_id)

    def _cross_propagation(self):
        match_sets = []
        for node in self.g.derg['nodes']:
            match_set = self.get_match_set_for_node(node['id'])
            if match_set is None:
                continue
            match_sets.append(match_set)
        logger.info("cross propagation ...")
        while True:
            match = self.__select_a_match(match_sets)
            if match is None:
                break
            self.__update_derg(match)
            self.__update_match_sets(match_sets, match)

        # print "following match_sets are ignored"
        # for match_set in match_sets:
        #     print match_set

    def __select_a_match(self, match_sets):
        for match_set in match_sets:
            # try to find a simple match
            match = self.__select_a_simple_match_by_type(match_set, "para")
            if match is not None:
                return match
            match = self.__select_a_simple_match_by_type(match_set, "ret")
            if match is not None:
                return match
            match = self.__select_a_simple_match_by_type(match_set, "refer")
            if match is not None:
                return match

            # look for intersections
            for node_id in match_set[1]:
                choices = set(match_set[0])
                for match_set_i in match_sets:
                    if node_id in match_set_i[1]:
                        choices.intersection_update(match_set_i[0])
                        if len(choices) == 1:
                            matched_relation = choices.pop()
                            matched_name = matched_relation[matched_relation.index(':')+1:]
                            match = (matched_name, node_id)
                            return match

        return None

    def __select_a_simple_match_by_type(self, match_set, type):
        relation_choices = self.__filter_relations(match_set[0], type)
        unknown_nodes = self.__filter_node_relation_mapping(match_set[1], type)
        if len(relation_choices) == len(unknown_nodes) == 1:
            matched_relation = relation_choices.pop()
            matched_node_id = unknown_nodes.popitem()[0]
            matched_name = matched_relation[matched_relation.index(':')+1:]
            match = (matched_name, matched_node_id)
            return match
        return None

    def __filter_relations(self, relations, prefix):
        filtered_relations = []
        for relation in relations:
            if relation.startswith(prefix):
                filtered_relations.append(relation)
        return filtered_relations

    def __filter_node_relation_mapping(self, node_relation_mapping, prefix):
        filtered_node_relation = {}
        for node_id in node_relation_mapping:
            relation = node_relation_mapping[node_id]
            if relation.startswith(prefix):
                filtered_node_relation[node_id] = relation
        return filtered_node_relation

    def __update_derg(self, match):
        matched_name = match[0]
        matched_node_id = match[1]
        if matched_node_id not in self.g.belongto_map:
            return
        class_node_id = self.g.belongto_map[matched_node_id]
        class_node = self.g.derg['nodes'][class_node_id]
        recovered_sig = "%s.%s" % (class_node['recovered_sig'], matched_name)
        self.g.recover_node_with_sig(matched_node_id, recovered_sig)

    def __update_match_sets(self, match_sets, match):
        matched_name = match[0]
        matched_node_id = match[1]

        match_sets_to_remove = []
        for match_set in match_sets:
            if matched_name in match_set[0]:
                match_set[0].remove(matched_name)
            if matched_node_id in match_set[1]:
                match_set[1].pop(matched_node_id)
            if len(match_set[0]) == 0 or len(match_set[1]) == 0:
                match_sets_to_remove.append(match_set)
        for match_set in match_sets_to_remove:
            match_sets.remove(match_set)

        match_set = self.get_match_set_for_node(matched_node_id)
        if match_set is not None:
            match_sets.append(match_set)

    def get_match_set_for_node(self, node_id):
        node = self.g.derg['nodes'][node_id]
        if node['type'] not in ['method', 'method_3LIB']:
            return None
        if is_method_minified(node['recovered_sig']):
            return None
        profile = self.node_profile[node_id]
        node = self.g.derg['nodes'][node_id]
        profile_id = node['recovered_sig']
        profile_sig = profile['sig']
        matched_profile = self.method_profile_col.find_one({'id':profile_id, 'sig':profile_sig})
        if matched_profile is None or 'relation' not in matched_profile:
            return None

        matched_relations = matched_profile['relation'].strip().split("\n")
        node_relation_map = self.g.get_node_relation_map(node_id)

        # remove constructors
        constructors = []
        for matched_relation in matched_relations:
            if matched_relation.endswith("init>"):
                constructors.append(matched_relation)
        for constructor in constructors:
            matched_relations.remove(constructor)
        constructor_nodes = []
        for node_id in node_relation_map:
            relation = node_relation_map[node_id]
            if relation.endswith("init>"):
                constructor_nodes.append(node_id)
        for node_id in constructor_nodes:
            node_relation_map.pop(node_id)

        # remove known nodes
        known_nodes = []
        for node_id in node_relation_map:
            relation = node_relation_map[node_id]
            if relation in matched_relations:
                matched_relations.remove(relation)
                known_nodes.append(node_id)
        for node_id in known_nodes:
            node_relation_map.pop(node_id)

        # if len(matched_relations) != len(node_relation_map):
        #     print "matched_relations count does not match node_relation_map"
        #     print matched_relations
        #     print node_relation_map

        if len(matched_relations) == 0 or len(node_relation_map) == 0:
            return None

        match_set = (matched_relations, node_relation_map)
        return match_set

    def recover(self):
        logger.info("start recovering")

        g = self.g
        derg = g.derg

        for node in derg['nodes']:
            node['recovered_name'] = node['name']
            node['recovered_sig'] = node['sig']

        self._match_method_node_profile()
        self._down_top_propagation()
        # print choices of node for debug
        self.print_choices_of_nodes()
        self._top_down_propagation()
        # cross propagation pass
        self._cross_propagation()

        # output
        logger.info("done recovering")

    def print_choices_of_nodes(self, node_types=None):
        if not node_types:
            node_types = ['package', 'class', 'method']
        derg_nodes = self.g.derg['nodes']
        for node in derg_nodes:
            if node['type'] in node_types:
                node_id = node['id']
                if node_id not in self.nodes_method_count or node_id not in self.nodes_matched_names:
                    continue
                node_name = node['name']
                node_seg = node['sig']

                print "---------------------"
                print "id:%d, name:%s, sig:%s" % (node_id, node_name, node_seg)
                print "method count: %d" % self.nodes_method_count[node_id]
                print "matched names:"

                sorted_choices = sorted(self.nodes_matched_names[node_id].items(), key=operator.itemgetter(1), reverse=True)
                print sorted_choices

    def close(self):
        self.mongo_client.close()


class DERG(object):
    def __init__(self, derg_file):
        self.derg = json.load(open(derg_file, "r"))
        self.contain_map, self.belongto_map, self.para_map, self.ret_map, self.refer_map = self.get_all_util_maps()
        self.fix_package_signature()

    def fix_package_signature(self):
        for node in self.derg['nodes']:
            if node['type'] == "package":
                node['sig'] = self.get_sig(node['id'])

    def mark_3lib_nodes(self, packages_3lib):
        derg = self.derg
        belongto_map = self.belongto_map
        for node_id in self.get_bfs_nodes():
            node = derg['nodes'][node_id]
            node_type = node['type']
            node_sig = node['sig']
            if node_type == "package":
                if node_sig in packages_3lib:
                    self.mark_node_as_3lib(node)
            elif node_type == "class":
                package_node = derg['nodes'][belongto_map[node_id]]
                if DERG.is_3lib_node(package_node):
                    DERG.mark_node_as_3lib(node)
            elif node_type in ["method", "field"]:
                class_node = derg['nodes'][belongto_map[node_id]]
                if DERG.is_3lib_node(class_node):
                    DERG.mark_node_as_3lib(node)

    def recover_node_with_sig(self, node_id, node_sig):
        node = self.derg['nodes'][node_id]
        if node_sig == node['sig'] or node_sig == node['recovered_sig']:
            return

        if node_id in self.belongto_map and (node['type'].startswith('field') or node['type'].startswith('method')):
            parent_id = self.belongto_map[node_id]
            parent_sig = node_sig[:node_sig.rindex('.')]
            self.recover_node_with_sig(parent_id, parent_sig)

        node['recovered_sig'] = node_sig
        node['recovered_name'] = node_sig.split(".")[-1]

        if node['recovered_name'] != node['name']:
            node_type = node['type']
            if node_type.startswith("package"):
                print "recover package: %s -> %s" % (node['sig'], node['recovered_sig'])
            elif node_type.startswith("class"):
                print "recover class: %s -> %s" % (node['sig'], node['recovered_sig'])
            elif node_type.startswith("method"):
                print "recover method: %s -> %s" % (node['sig'], node['recovered_sig'])
            elif node_type.startswith("field"):
                print "recover field: %s -> %s" % (node['sig'], node['recovered_sig'])

    def get_contain_map(self):
        contain_map = {}
        derg_edges = self.derg['edges']
        for edge in derg_edges:
            if edge['relation'] == "XX_contains":
                s = edge['source']
                t = edge['target']
                if s not in contain_map:
                    contain_map[s] = set()
                contain_map[s].add(t)
        return contain_map

    def get_belongto_map(self):
        belongto_map = {}
        derg_edges = self.derg['edges']
        for edge in derg_edges:
            if edge['relation'] == "XX_contains":
                s = edge['source']
                t = edge['target']
                belongto_map[t] = s
        return belongto_map

    def get_sig(self, node_id):
        return ".".join([self.derg['nodes'][i]['name'] for i in self.get_parent_nodes(node_id)[::-1][1:]])

    @staticmethod
    def mark_node_as_3lib(DERG_node):
        DERG_node['type'] += "_3LIB"

    @staticmethod
    def is_3lib_node(DERG_node):
        return DERG_node['type'].endswith("_3LIB")

    def get_parent_nodes(self, node_id):
        belongto_map = self.belongto_map
        parents = [node_id]

        while node_id in belongto_map:
            node_id = belongto_map[node_id]
            parents.append(node_id)
        return parents

    def get_bfs_nodes(self):
        contain_map = self.contain_map
        bfs_nodes = [0]
        i = 0
        while i < len(bfs_nodes):
            parent_node = bfs_nodes[i]
            if parent_node in contain_map:
                children_nodes = contain_map[parent_node]
                bfs_nodes += children_nodes
            i += 1
        return bfs_nodes

    def get_refer_map(self):
        refer_map = {}
        derg_edges = self.derg['edges']
        for edge in derg_edges:
            if edge['relation'] == "MX_refer":
                s = edge['source']
                t = edge['target']
                if s not in refer_map:
                    refer_map[s] = set()
                refer_map[s].add(t)
        return refer_map

    def get_para_map(self):
        para_map = {}
        derg_edges = self.derg['edges']
        for edge in derg_edges:
            if edge['relation'] == "MT_parameter":
                s = edge['source']
                t = edge['target']
                if s not in para_map:
                    para_map[s] = set()
                para_map[s].add(t)
        return para_map

    def get_ret_map(self):
        ret_map = {}
        derg_edges = self.derg['edges']
        for edge in derg_edges:
            if edge['relation'] == "MT_return":
                s = edge['source']
                t = edge['target']
                ret_map[s] = t
        return ret_map

    def get_all_util_maps(self):
        contain_map = {}
        belongto_map = {}
        para_map = {}
        ret_map = {}
        refer_map = {}
        derg_edges = self.derg['edges']
        for edge in derg_edges:
            if edge['relation'] == "XX_contains":
                s = edge['source']
                t = edge['target']
                belongto_map[t] = s
                if s not in contain_map:
                    contain_map[s] = []
                contain_map[s].append(t)
            elif edge['relation'] == "MX_refer":
                s = edge['source']
                t = edge['target']
                if s not in refer_map:
                    refer_map[s] = []
                refer_map[s].append(t)
            elif edge['relation'] == "MT_parameter":
                s = edge['source']
                t = edge['target']
                if s not in para_map:
                    para_map[s] = []
                para_map[s].append(t)
            elif edge['relation'] == "MT_return":
                s = edge['source']
                t = edge['target']
                ret_map[s] = t
        return contain_map, belongto_map, para_map, ret_map, refer_map

    def get_relation_of_node(self, node_id):
        segs = []
        nodes = self.derg['nodes']
        if node_id in self.para_map:
            para_nodes = self.para_map[node_id]
            for para_node_id in para_nodes:
                segs.append("para:%s" % nodes[para_node_id]['recovered_name'])

        if node_id in self.ret_map:
            ret_node_id = self.ret_map[node_id]
            segs.append("ret:%s" % nodes[ret_node_id]['recovered_name'])

        if node_id in self.refer_map:
            refer_nodes = self.refer_map[node_id]
            for refer_node_id in refer_nodes:
                segs.append("refer:%s" % nodes[refer_node_id]['recovered_name'])

        return "\n".join(sorted(segs))

    def get_node_relation_map(self, node_id):
        node_relation_map = {}
        nodes = self.derg['nodes']
        if node_id in self.para_map:
            para_nodes = self.para_map[node_id]
            for para_node_id in para_nodes:
                relation = "para:%s" % nodes[para_node_id]['recovered_name']
                node_relation_map[para_node_id] = relation

        if node_id in self.ret_map:
            ret_node_id = self.ret_map[node_id]
            relation = "ret:%s" % nodes[ret_node_id]['recovered_name']
            node_relation_map[ret_node_id] = relation

        if node_id in self.refer_map:
            refer_nodes = self.refer_map[node_id]
            for refer_node_id in refer_nodes:
                relation = "refer:%s" % nodes[refer_node_id]['recovered_name']
                node_relation_map[refer_node_id] = relation

        return node_relation_map


def is_method_minified(name):
    segs = name.split('.')
    if len(segs) < 2:
        return False

    method_seg = segs[-1].split('$')[0]
    class_seg = segs[-2].split('$')[0]

    if len(method_seg) == 1 or len(class_seg) == 1:
        return True

    return False


def is_not_match(method_id, minified_id):
    method_id_segs = method_id.split('.')
    minified_id_segs = minified_id.split('.')
    if len(method_id_segs) != len(minified_id_segs):
        return True
    for i in range(0, len(method_id_segs)):
        method_id_seg = method_id_segs[i]
        minified_id_seg = minified_id_segs[i]
        if len(minified_id_seg) > 3 and method_id_seg != minified_id_seg:
            return True
    return False


def filter_methods(raw_method_ids, minified_id):
    method_ids = []
    for method_id in raw_method_ids:
        if is_not_match(method_id, minified_id):
            continue
        method_ids.append(method_id)
    return method_ids


def safe_increase(data_dict, key):
    if key not in data_dict:
        data_dict[key] = 1
    else:
        data_dict[key] += 1


if __name__ == "__main__":
    main()
