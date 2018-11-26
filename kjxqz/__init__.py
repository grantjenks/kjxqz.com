"Tools for creating directed acyclic word graphs."

import hashlib
import io
from itertools import count, permutations
from collections import Counter, defaultdict
import os.path as op
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

DIR_PATH = op.dirname(op.realpath(__file__))
WORDS_TXT = op.join(DIR_PATH, 'words.txt')
INDEX_HTML = op.join(DIR_PATH, 'index.html')
SERVICE_WORKER_JS = op.join(DIR_PATH, 'service-worker.js')

def make_index(filename='index.html'):
    with open(INDEX_HTML, 'rb') as reader:
        with open(filename, 'wb') as writer:
            writer.write(reader.read())

def make_json(filename='dawg.js'):
    with io.open(WORDS_TXT, encoding='utf-8') as reader:
        text = reader.read()
        words = sorted(set(text.splitlines()))
    data = make_dawg(words)
    with open(filename, 'w') as writer:
        writer.write('var dawg = ')
        json.dump(data, writer, indent=4, sort_keys=True)
        writer.write(';\n')

def make_service_worker(filename='service-worker.js'):
    sha2 = hashlib.sha256()
    for path in [INDEX_HTML, SERVICE_WORKER_JS, WORDS_TXT]:
        with open(path, 'rb') as reader:
            while True:
                chunk = reader.read(2 ** 16)
                if not chunk:
                    break
                sha2.update(chunk)
    code = sha2.hexdigest()[:16]
    with open(SERVICE_WORKER_JS) as reader:
        text = reader.read()
        text = text.replace('{HASH}', code)
    with open(filename, 'w') as writer:
        writer.write(text)

__title__ = 'kjxqz'
__version__ = '0.0.1'
__build__ = 0x000001
__author__ = 'Grant Jenks'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2018 Grant Jenks'
