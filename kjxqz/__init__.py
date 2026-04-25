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
    contains_starts = contains.startswith('.')
    contains_ends = len(contains) > 1 and contains.endswith('.')
    contains_pattern = contains

    if contains_starts:
        contains_pattern = contains_pattern[1:]

    if contains_ends:
        contains_pattern = contains_pattern[:-1]

    if contains_pattern:
        contains = contains_pattern
    else:
        contains_starts = False
        contains_ends = False

    dawg = _get_dawg()
    value: list[str] = []
    letter_counts = Counter(letters)
    blanks = letter_counts.pop('?', 0)
    contains_list = list(contains)
    seen: set[str] = set()

    def consume(letter: str) -> Iterator[None]:
        nonlocal blanks

        count = letter_counts[letter]

        if count > 0:
            letter_counts[letter] = count - 1
            yield
            letter_counts[letter] = count
        elif blanks > 0:
            blanks -= 1
            yield
            blanks += 1

    def helper(state: str, contained: bool) -> Iterator[str]:
        branches = dawg.get(state, {})

        if contained:
            if '$' in branches:
                result = ''.join(value)
                if result not in seen:
                    seen.add(result)
                    yield result
            if not contains_ends:
                yield from traverse(state, True)
            return

        if not contains_starts:
            yield from traverse(state, False)
        yield from match_contains(state, 0)

    def traverse(state: str, contained: bool) -> Iterator[str]:
        branches = dawg.get(state, {})

        for letter, next_state in branches.items():
            if letter == '$':
                continue

            for _ in consume(letter):
                value.append(letter)
                yield from helper(next_state, contained)
                value.pop()

    def match_contains(state: str, offset: int) -> Iterator[str]:
        if offset == len(contains_list):
            yield from helper(state, True)
            return

        branches = dawg.get(state, {})
        letter = contains_list[offset]

        if letter == '_':
            for choice, next_state in branches.items():
                if choice == '$':
                    continue

                for _ in consume(choice):
                    value.append(choice)
                    yield from match_contains(next_state, offset + 1)
                    value.pop()
        elif letter in branches:
            value.append(letter)
            yield from match_contains(branches[letter], offset + 1)
            value.pop()

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
__version__ = '1.2.0'
__build__ = 0x000001
__author__ = 'Grant Jenks'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2018-2026 Grant Jenks'
