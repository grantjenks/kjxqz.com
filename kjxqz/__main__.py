from __future__ import annotations

import argparse
from typing import Sequence

from . import DAWG_JS, build, load, search


def parse_args(argv: Sequence[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Search words or build kjxqz website assets.'
    )
    parser.add_argument(
        '--dawg',
        default=None,
        help='Path to DAWG JavaScript data.',
    )
    parser.add_argument(
        '--service-worker',
        default='www/service-worker.js',
        help='Output path for generated service worker JavaScript.',
    )
    parser.add_argument('args', nargs='*', help='Command and command arguments.')
    namespace = parser.parse_args(argv)

    args = namespace.args
    if not args:
        namespace.command = 'build'
        namespace.letters = ''
        namespace.contains = ''
        return namespace

    head = args[0]
    if head == 'build':
        if len(args) != 1:
            parser.error('build takes no positional arguments')
        namespace.command = 'build'
        namespace.letters = ''
        namespace.contains = ''
        return namespace

    if head == 'search':
        if len(args) not in (2, 3):
            parser.error('search requires letters and optional contains')
        namespace.command = 'search'
        namespace.letters = args[1]
        namespace.contains = args[2] if len(args) == 3 else ''
        return namespace

    if len(args) not in (1, 2):
        parser.error('search shorthand requires letters and optional contains')
    namespace.command = 'search'
    namespace.letters = args[0]
    namespace.contains = args[1] if len(args) == 2 else ''
    return namespace


def main(argv: Sequence[str] | None = None):
    args = parse_args(argv)
    if args.command == 'build':
        dawg = args.dawg or 'www/dawg.js'
        build(dawg=dawg, service_worker=args.service_worker)
        return 0

    load(filename=args.dawg or DAWG_JS)
    for word in search(letters=args.letters, contains=args.contains):
        print(word)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
