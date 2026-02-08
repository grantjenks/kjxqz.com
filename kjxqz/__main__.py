from __future__ import annotations

import argparse

from . import make_dawg, make_service_worker


def parse_args():
    parser = argparse.ArgumentParser(description='Build kjxqz website assets.')
    parser.add_argument(
        '--dawg',
        default='www/dawg.js',
        help='Output path for DAWG JavaScript data.',
    )
    parser.add_argument(
        '--service-worker',
        default='www/service-worker.js',
        help='Output path for generated service worker JavaScript.',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    make_dawg(filename=args.dawg)
    make_service_worker(filename=args.service_worker)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
