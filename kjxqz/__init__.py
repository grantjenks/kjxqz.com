"Tools for creating directed acyclic word graphs."

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Iterator
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
DAWG_JS = PACKAGE_DIR / 'dawg.js'
WEBSITE_DAWG_JS = PROJECT_DIR / 'www' / 'dawg.js'
SERVICE_WORKER_JS = PACKAGE_DIR / 'service-worker.js'
INDEX_HTML = PROJECT_DIR / 'www' / 'index.html'
MAIN_JS = PROJECT_DIR / 'www' / 'main.js'
STYLES_CSS = PROJECT_DIR / 'www' / 'styles.css'
ALPHABET = tuple('abcdefghijklmnopqrstuvwxyz')

_DAWG: dict[str, dict[str, str]] | None = None


def load_words(words_filename: str | Path = WORDS_TXT) -> list[str]:
    path = Path(words_filename)
    return sorted(set(path.read_text(encoding='utf-8').splitlines()))


def _to_dawg_js(data: dict[str, dict[str, str]]) -> str:
    text = 'var dawg = '
    text += json.dumps(data, indent=4, sort_keys=True)
    text += ';\n'
    return text


def _write_dawg(data: dict[str, dict[str, str]], filename: str | Path) -> None:
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_to_dawg_js(data), encoding='utf-8')


def load(filename: str | Path = DAWG_JS) -> dict[str, dict[str, str]]:
    text = Path(filename).read_text(encoding='utf-8').strip()
    if text.startswith('var dawg ='):
        payload = text[len('var dawg =') :].strip()
        if payload.endswith(';'):
            payload = payload[:-1].strip()
    else:
        payload = text

    data = json.loads(payload)

    global _DAWG
    _DAWG = data
    return data


def _get_dawg() -> dict[str, dict[str, str]]:
    if _DAWG is None:
        raise RuntimeError('DAWG is not loaded. Call kjxqz.load() first.')
    return _DAWG


def isearch(letters: str, contains: str = '') -> Iterator[str]:
    letters = letters.lower()
    contains = contains.lower()

    dawg = _get_dawg()
    value: list[str] = []
    letters_list = list(letters)
    contains_list = list(contains)
    seen: set[str] = set()

    def helper(state: str, contained: bool) -> Iterator[str]:
        branches = dawg.get(state, {})

        if contained:
            if '$' in branches:
                result = ''.join(value)
                if result not in seen:
                    seen.add(result)
                    yield result
            yield from traverse(state, True)
            return

        yield from traverse(state, False)

        contains_length = len(contains_list)
        for index in range(contains_length):
            letter = contains_list[index]
            if letter in branches:
                value.append(letter)
                state = branches[letter]
                branches = dawg.get(state, {})
            else:
                for _ in range(index):
                    value.pop()
                return

        yield from helper(state, True)

        for _ in range(contains_length):
            value.pop()

    def traverse(state: str, contained: bool) -> Iterator[str]:
        branches = dawg.get(state, {})
        letters_length = len(letters_list)

        for _ in range(letters_length):
            letter = letters_list.pop(0)
            choices = ALPHABET if letter == '?' else (letter,)

            for choice in choices:
                if choice in branches:
                    value.append(choice)
                    yield from helper(branches[choice], contained)
                    value.pop()

            letters_list.append(letter)

    yield from helper('0', not contains_list)


def search(letters: str, contains: str = '') -> list[str]:
    results = list(isearch(letters, contains))
    results.sort(key=lambda word: (-len(word), word))
    return results


def make_dawg(
    filename: str | Path = WEBSITE_DAWG_JS, words_filename: str | Path = WORDS_TXT
):
    words = load_words(words_filename=words_filename)
    data = build_dawg(words)
    _write_dawg(data, filename=filename)
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


def build(
    dawg: str | Path = WEBSITE_DAWG_JS,
    package_dawg: str | Path = DAWG_JS,
    service_worker: str | Path = 'www/service-worker.js',
    words_filename: str | Path = WORDS_TXT,
    template_filename: str | Path = SERVICE_WORKER_JS,
    hash_filenames: Iterable[str | Path] | None = None,
) -> tuple[dict[str, dict[str, str]], str]:
    data = make_dawg(filename=dawg, words_filename=words_filename)
    if Path(package_dawg) != Path(dawg):
        _write_dawg(data, filename=package_dawg)
    code = make_service_worker(
        filename=service_worker,
        template_filename=template_filename,
        hash_filenames=hash_filenames,
    )
    return data, code


__title__ = 'kjxqz'
__version__ = '1.1.0'
__build__ = 0x000001
__author__ = 'Grant Jenks'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2018-2026 Grant Jenks'
