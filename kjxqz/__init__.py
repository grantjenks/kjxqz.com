"Tools for creating directed acyclic word graphs."

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from itertools import count
from pathlib import Path
from typing import Iterable


def treedict():
    return defaultdict(treedict)


def make_tree(words):
    root = treedict()

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
        repr_inner = ', '.join(f'{key}: {repr_value}' for key, _, repr_value in triples)
        repr_node = '{%s}' % repr_inner
        return new_node, repr_node

    root, _ = helper(tree)
    return root


def traverse(tree):
    matrix = {}

    def helper(node):
        if node is None:
            return

        for value in node.values():
            helper(value)

        branches = {key: id(value) for key, value in node.items()}
        num = id(node)
        if num in matrix:
            assert matrix[num] == branches
            return
        matrix[num] = branches

    helper(tree)
    return matrix


def minimize(matrix, root):
    counts = Counter(matrix.keys())
    counts.update(num for value in matrix.values() for num in value.values())

    num_map = {id(root): '0', id(None): '0'}
    counts.pop(id(root), None)
    counts.pop(id(None), None)

    counter = count(start=1)
    for key, _ in counts.most_common():
        num_map[key] = str(next(counter))

    return {
        num_map[num]: {key: num_map[val] for key, val in branches.items()}
        for num, branches in matrix.items()
    }


def build_dawg(words: Iterable[str]) -> dict[str, dict[str, str]]:
    tree = make_tree(words)
    trunk = convert(tree)
    root = simplify(trunk)
    matrix = traverse(root)
    return minimize(matrix, root)


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
WORDS_TXT = PACKAGE_DIR / 'words.txt'
SERVICE_WORKER_JS = PACKAGE_DIR / 'service-worker.js'
INDEX_HTML = PROJECT_DIR / 'www' / 'index.html'
MAIN_JS = PROJECT_DIR / 'www' / 'main.js'
STYLES_CSS = PROJECT_DIR / 'www' / 'styles.css'


def load_words(words_filename: str | Path = WORDS_TXT) -> list[str]:
    path = Path(words_filename)
    return sorted(set(path.read_text(encoding='utf-8').splitlines()))


def make_dawg(
    filename: str | Path = 'www/dawg.js', words_filename: str | Path = WORDS_TXT
):
    words = load_words(words_filename=words_filename)
    data = build_dawg(words)
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = 'var dawg = '
    text += json.dumps(data, indent=4, sort_keys=True)
    text += ';\n'
    path.write_text(text, encoding='utf-8')
    return data


def make_service_worker(
    filename: str | Path = 'www/service-worker.js',
    template_filename: str | Path = SERVICE_WORKER_JS,
    hash_filenames: Iterable[str | Path] | None = None,
) -> str:
    if hash_filenames is None:
        hash_filenames = [INDEX_HTML, MAIN_JS, STYLES_CSS, WORDS_TXT, template_filename]

    sha2 = hashlib.sha256()
    for hash_filename in hash_filenames:
        sha2.update(Path(hash_filename).read_bytes())

    code = sha2.hexdigest()[:16]
    text = Path(template_filename).read_text(encoding='utf-8')
    text = text.replace('{HASH}', code)

    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return code


__title__ = 'kjxqz'
__version__ = '0.1.0'
__build__ = 0x000001
__author__ = 'Grant Jenks'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2018-2026 Grant Jenks'
