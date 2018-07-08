"Tools for creating directed acyclic word graphs."

from itertools import count, permutations
from collections import Counter, defaultdict
import wordsegment
import json

def treedict():
    return defaultdict(treedict)

def make_tree(words):
    root = treedict()  # Root of nodes.

    for word in words:
        node = root
        for letter in word:
            node = node[letter]
        node['$'] = None

    return root

def convert(node):
    if node is None:
        return None
    return {key: convert(value) for key, value in sorted(node.items())}

def simplify(tree):
    hashes = {}

    def helper(node):
        if node is None:
            return None, repr(None)

        triples = []

        for key, value in sorted(node.items()):
            new_value, repr_value = helper(value)
            new_value = hashes.setdefault(repr_value, new_value)
            triples.append((key, new_value, repr_value))

        new_node = {key: new_value for key, new_value, _ in triples}
        items = []

        for key, _, repr_value in triples:
            items.append('{}: {}'.format(key, repr_value))

        repr_inner = ', '.join(items)
        repr_node = '{%s}' % repr_inner
        return new_node, repr_node

    root, _ = helper(tree)
    return root

def traverse(tree):
    # To serialize for JSON, convert the root to:
    # {
    #   0: {
    #     'a': 1,
    #     'b': 2,
    #     ...
    #   },
    #   1: {
    #     'a': 3,
    #     '$': 0,
    # The result has:
    # 1. A number for every state.
    # 2. The start state is 0.
    # 3. Any state that contains '$' is an end-state.
    matrix = {}

    def helper(node):
        if node is None:
            return

        for value in node.values():
            helper(value)

        value = {key: id(value) for key, value in node.items()}
        num = id(node)
        if num in matrix:
            assert matrix[num] == value
            return
        matrix[num] = value
        
    helper(tree)
    return matrix

def minimize(matrix, root):
    # Convert the ids so that smaller numbers (as strings) are used.
    # Count how often each number id occurs.
    counts = Counter(matrix.keys())
    counts.update(num for value in matrix.values() for num in value.values())

    # Build mapping from number id to smaller number (as string).

    num_map = {}
    num_map[id(root)] = '0'
    del counts[id(root)]
    num_map[id(None)] = '0'
    del counts[id(None)]
    counter = count(start=1)
    keys = (key for key, _ in counts.most_common())
    num_map.update({key: str(next(counter)) for key in keys})

    result = {
        num_map[num]: {key: num_map[val] for key, val in branches.items()}
        for num, branches in matrix.items()
    }

    return result

def make_dawg(words):
    tree = make_tree(words)
    trunk = convert(tree)
    root = simplify(trunk)
    matrix = traverse(root)
    result = minimize(matrix, root)
    return result

def make_json(filename='dawg.js'):
    wordsegment.load()
    words = sorted(set(wordsegment.WORDS))
    data = make_dawg(words)
    with open(filename, 'w') as writer:
        writer.write('var dawg = ')
        json.dump(data, writer, indent=4, sort_keys=True)
        writer.write(';')
