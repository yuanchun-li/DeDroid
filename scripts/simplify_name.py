__author__ = 'ziyue'


def simplify_label(origin_pattern, item_to_pattern_index, pattern_list):
    intersect_results = []
    candidate_pattern_ids = set()
    
    for item in origin_pattern:
        for pattern_id in item_to_pattern_index[item]:
            candidate_pattern_ids.add(pattern_id)
    
    for pattern_id in candidate_pattern_ids:
        intersect_results.append((set(origin_pattern) & set(pattern_list[pattern_id]), pattern_id))
    
    return intersect_results
    
def test_simplify_label():
    origin_pattern = [0, 1, 2]
    item_to_pattern_index = [[0, 1, 2], [0], [1], [0, 1, 2], [2]]
    pattern_list = [[0, 1, 3], [0, 2, 3], [0, 3, 4]]

    print simplify_label(origin_pattern, item_to_pattern_index, pattern_list)
    
    return


if __name__ == "__main__":
    test_simplify_label()
