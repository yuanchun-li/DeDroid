# encoding=utf-8
from pymongo import MongoClient
import re


def main():
    mongo_client = MongoClient()
    col = mongo_client['liycdata']['method_profiles']
    cur = col.find()

    profiles_to_drop = []

    p = 0
    count = cur.count()
    for profile in cur:
        p += 1
        if p % 100 == 0:
            print "finding minified id: %.0f%%" % (p * 100.0 / count)

        method_id = profile['id']
        if is_method_obfuscated(method_id):
            profiles_to_drop.append(profile)

    p = 0
    count = len(profiles_to_drop)
    for profile in profiles_to_drop:
        p += 1
        if p % 100 == 0:
            print "dropping minified id %s: %.0f%%" % (profile['id'], p * 100.0 / count)

        col.delete_one(profile)


def is_method_obfuscated(name):
    segs = name.split('.')
    if len(segs) < 2:
        return False

    method_seg = segs[-1].split('$')[0]
    class_seg = segs[-2].split('$')[0]

    if len(method_seg) == 1 or len(class_seg) == 1:
        # print name
        return True

    # print name
    return False


if __name__ == "__main__":
    main()
