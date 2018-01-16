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
    parser.add_argument("-allow_minify", action="store_true", dest="allow_minify", default=False,
                        help="allow minified class names and method names")

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

    import_method_profile(opts.method_profile, opts.db, opts.collection, opts.allow_minify)

    return


def import_method_profile(method_profile_path, mongo_db, mongo_collection, allow_minify):
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
        if not allow_minify and is_method_minified(method_id):
            continue
        col.update({"sig":sig, "id":method_id}, {"$inc": {"count":1}}, upsert=True)
    mongo_client.close()


def is_method_minified(name):
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
