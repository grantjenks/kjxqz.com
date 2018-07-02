"""Scrabble Solver

- TODO: Max blanks is 2!

"""

# Slow, brute-force solution.

from itertools import count, permutations
from collections import Counter
import wordsegment

wordsegment.load()
words = sorted(set(wordsegment.WORDS))

def matches_simple(letters):
    for count in range(2, len(letters) + 1):
        for perm in permutations(letters, count):
            word = ''.join(perm)
            if word in words:
                yield word

# Faster, brute-force solution.

from string import ascii_lowercase

prefixes = set(word[:num] for word in words for num in range(1, len(word)))

def matches(letters, value=''):
    for index in range(len(letters)):
        letter = letters.pop(index)
        if letter == '?':
            options = ascii_lowercase
        else:
            options = [letter]
        for option in options:
            value += option
            if value in words:
                yield value
            if value in prefixes:
                yield from matches(letters, value)
            value = value[:-1]
        letters.insert(index, letter)

# Maybe even faster solution?

from collections import defaultdict, deque
from itertools import count

def make_tree(words):
    # TODO: Make the end state "1". Then optimize the tree by merging
    # redundant branches.
    tree = defaultdict(dict)  # tree[state][letter] = state
    goals = set()  # states
    states = count(start=1)

    for word in words:
        state = 0
        for letter in word:
            branch = tree[state]
            if letter in branch:
                state = branch[letter]
            else:
                state = next(states)
                branch[letter] = state
        goals.add(state)

    return tree, goals

tree, goals = make_tree(words)

def matches_tree(letters):
    letters = deque(letters)
    value = []

    def helper(state=0):
        branch = tree[state]

        for index in range(len(letters)):
            letter = letters.pop()

            if letter == '?':
                options = ascii_lowercase
            else:
                options = [letter]

            for option in options:
                if option in branch:
                    value.append(option)
                    state = branch[option]

                    if state in goals:
                        yield ''.join(value)

                    yield from helper(state)
                    value.pop()

            letters.appendleft(letter)

    yield from helper()

# In [26]: %timeit sum(1 for word in matches_tree('etaoinsrhlndc??'))
# 8.55 s ± 68.4 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

# How to merge tree branches into dag?
# Replace terminal goal states with same num.
# Build tree where id() of dict in goals?
#   * Use tree() instead of defaultdict(dict).
# Merge equal branches repeatedly.

# Idea: Build Directed-Acyclic-Word-Graph in Python and then serialize as JSON
# to run in the browser! Super fast!
#
# Need to convert to {num: {letters: nums}} mapping for JSON.
#
# The result is big (megabytes) but not huge. In Python, it takes ~143ms to
# load the JSON data.

def tree_dict():
    return defaultdict(tree_dict)

def make_dawg(words):
    root = tree_dict()  # Root of nodes.

    for word in words:
        node = root
        for letter in word:
            node = node[letter]
        node['$'] = None

    # Watch out! Relies on insertion order for dicts!

    def convert(value):
        if value is None:
            return None
        return {key: convert(val) for key, val in sorted(value.items())}

    root = convert(root)
    hashes = {}

    def simplify(node):
        if node is None:
            return None, repr(None)
        triples = []
        for key, value in sorted(node.items()):
            new_value, repr_value = simplify(value)
            new_value = hashes.setdefault(repr_value, new_value)
            triples.append((key, new_value, repr_value))
        new_node = {key: new_value for key, new_value, _ in triples}
        items = []
        for key, _, repr_value in triples:
            items.append('{}: {}'.format(key, repr_value))
        repr_inner = ', '.join(items)
        repr_node = '{%s}' % repr_inner
        return new_node, repr_node

    root, _ = simplify(root)

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

    # Start by converting the "root" so that id()s are used instead
    # of direct dictionary references.

    def traverse(node):
        if node is None:
            return
        for value in node.values():
            traverse(value)
        value = {key: id(value) for key, value in node.items()}
        num = id(node)
        if num in idtree:
            assert idtree[num] == value
            return
        idtree[num] = value

    idtree = {}
    traverse(root)

    # Then convert the ids so that smaller numbers are used.

    counts = Counter(idtree.keys())
    counts.update(num for value in idtree.values() for num in value.values())
    num_map = {}
    num_map[id(root)] = '0'
    num_map[id(None)] = '0'
    del counts[id(root)]
    del counts[id(None)]
    counter = count(start=1)
    for key, _ in counts.most_common():
        num_map[key] = str(next(counter))

    result = {}
    for num, branches in idtree.items():
        sub = {key: num_map[value] for key, value in branches.items()}
        result[num_map[num]] = sub

    return result
