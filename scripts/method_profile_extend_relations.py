import json, argparse, os, re
from pymongo import MongoClient


def parse_args():
    """
    parse command line input
    generate options including host name, port number
    """
    parser = argparse.ArgumentParser(description="import DERG method profiles to mongo db")
    parser.add_argument("-i", action="store", dest="method_profile", required=True,
                        help="file path of method profile")
    parser.add_argument("-db", action="store", dest="db", default="liycdata",
                        help="target database")
    parser.add_argument("-collection", action="store", dest="collection", default="method_profiles",
                        help="target collection")

    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    it starts a droidbot according to the arguments given in cmd line
    """
    opts = parse_args()

    if not os.path.exists(opts.method_profile):
        print "method profile not exist"
        return

    extend_method_profile(opts.method_profile, opts.db, opts.collection)

    return


def extend_method_profile(method_profile_path, mongo_db, mongo_collection):
    mongo_client = MongoClient()
    col = mongo_client[mongo_db][mongo_collection]
    method_profile_file = open(method_profile_path, "r")
    method_profiles = json.load(method_profile_file)

    count = len(method_profiles)
    p = 0
    for method_profile in method_profiles:
        p += 1
        if p % 100 == 0:
            print "%.0f%%" % (p * 100.0 / count)

        sig = method_profile['sig']
        method_id = method_profile['id']
        relation = method_profile['relation']

        if is_method_obfuscated(method_id):
            continue

        cur = col.find({"sig":sig, "id":method_id})
        if cur.count() != 1:
            continue

        profile = cur.next()
        old_relation = profile['relation'] if 'relation' in profile else ""
        if old_relation == relation:
            continue

        new_relation = merge_relation(old_relation, relation)

        col.update({"sig":sig, "id":method_id}, {'$set': {'relation': new_relation}}, upsert=False)
    mongo_client.close()


def merge_relation(relation1, relation2):
    relation1_segs = relation1.split("\n")
    relation2_segs = relation2.split("\n")
    relation_segs = sorted(set(relation1_segs + relation2_segs))
    return "\n".join(relation_segs)


def is_method_obfuscated(name):
    segs = name.split('.')
    if len(segs) < 2:
        return False

    method_seg = segs[-1].split('$')[0]
    class_seg = segs[-2].split('$')[0]

    if len(method_seg) == 1 or len(class_seg) == 1:
        return True

    return False


if __name__ == "__main__":
    main()
