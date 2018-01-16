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
    parser.add_argument("-collection", action="store", dest="collection", default="lib_method_profiles",
                        help="target collection")
    parser.add_argument("-lib", action="store", dest="libname", required=True,
                        help="name of third party library")

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

    import_lib_method_profile(opts.method_profile, opts.libname, opts.db, opts.collection)

    return


def import_lib_method_profile(method_profile_path, libname, mongo_db, mongo_collection):
    mongo_client = MongoClient()
    col = mongo_client[mongo_db][mongo_collection]
    method_profile_file = open(method_profile_path, "r")
    method_profiles = json.load(method_profile_file)

    count = len(method_profiles)
    p = 0
    for method_profile in method_profiles:
        p += 1
        if p % 100 == 0:
            print "importing method profile of lib %s: %.0f%%" % (libname, p * 100.0 / count)

        sig = method_profile['sig']
        method_id = method_profile['id']

        col.insert({"sig":sig, "id":method_id, "libname":libname})

    mongo_client.close()


if __name__ == "__main__":
    main()
