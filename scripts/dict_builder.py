from pymongo import MongoClient

client = MongoClient()
d = "liycdata"
c1_name = "code_dict"
c2_name = "element_names"

c1 = client[d][c1_name]
c2 = client[d][c2_name]


def safe_increase(data_dict, key1, key2):
    if key1 not in data_dict.keys():
        data_dict[key1] = {}
    if key2 not in data_dict[key1].keys():
        data_dict[key1][key2] = 0
    data_dict[key1][key2] += 1

names = {}
dicts = c1.find()
count = dicts.count()
i = 0
for dict_item in dicts:
    print "%d/%d" % (i, count)
    i += 1

    type = dict_item['type']
    words = dict_item['words']
    for word in words:
        if len(word) < 2:
            continue
        safe_increase(names, type, word)

for type in names.keys():
    for word in names[type].keys():
        item = {"word":word, "type":type, "count":names[type][word]}
        c2.insert(item)

client.close()
