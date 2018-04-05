#!/usr/bin/env python3
import logging
import os
import shutil
from collections import Counter
from functools import lru_cache
from typing import Any, Callable, Dict, FrozenSet, List, Tuple

from dataclasses import dataclass, field
from PIL import Image

__version__ = '0.1'

# Setup logging facility
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
fmt = logging.Formatter('[%(levelname)s - %(filename)s:%(lineno)d] - %(message)s')
ch.setFormatter(fmt)
logger.addHandler(ch)


# Typing aliases
Resolution = Tuple[int, int]


@dataclass
class ImageMetadata:
    filename: os.PathLike
    resolution: Resolution

    @property
    def basename(self):
        return os.path.basename(self.filename)

    @property
    def dirname(self):
        return os.path.dirname(self.filename)


def prepare(paths: List[os.PathLike], similarity: bool) \
        -> Tuple[List[ImageMetadata], FrozenSet[Resolution]]:
    images: List[ImageMetadata] = []
    whitelist = Counter()

    for path in paths:
        try:
            image = Image.open(path)
        except IOError as e:
            logger.warn(f'Error opening {path}: {e}')
            continue

        logger.debug(f'Processing metadata for {path}')
        images.append(ImageMetadata(filename=path, resolution=image.size))
        whitelist[image.size] += 1

    logger.info(f'Found {len(images)} images')
    return images, frozenset({res for res in whitelist if whitelist[res] > 4})


def scatter(images: List[ImageMetadata],
            whitelist: FrozenSet[Resolution],
            dirname: os.PathLike) \
        -> Tuple[List[os.PathLike], Dict[os.PathLike, os.PathLike]]:
    @lru_cache()
    def path_to_resolution(resolution: Resolution) -> os.PathLike:
        if resolution in whitelist:
            return os.path.join(dirname, '{}x{}'.format(*resolution))
        return dirname

    mapping = dict()
    needed_dirs = {dirname}
    for image in images:
        destdir = path_to_resolution(image.resolution)
        dest = os.path.join(destdir, image.basename)

        if os.path.isfile(dest) and os.path.samefile(image.filename, dest):
            continue

        needed_dirs.add(destdir)
        mapping[image.filename] = dest

    return needed_dirs, mapping


def create_dirs(dirnames: List[os.PathLike], dry_run: bool):
    for dirname in dirnames:
        if not os.path.isdir(dirname):
            logger.info(f'mkdir {dirname}')
            if not dry_run:
                os.makedirs(dirname)


def copy_or_move(mapping: Dict[os.PathLike, os.PathLike],
                 fn: Callable[[os.PathLike, os.PathLike], Any], dry_run: bool):
    for orig, dest in mapping.items():
        logger.info(f'{orig} -> {dest}')
        if not dry_run:
            fn(orig, dest)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Automatic wallpaper sorter by image dimensions')

    parser.add_argument('-m', '--move', action='store_const',
                        const=shutil.move, default=shutil.copyfile)
    parser.add_argument('-n', '--dry-run', action='store_true')

    # TODO: watch folder

    parser.add_argument('images', nargs='*', type=os.path.abspath)
    parser.add_argument('output', type=os.path.abspath)

    args = parser.parse_args()

    images, whitelist = prepare(args.images, args.similar)

    needed_dirs, mapping = scatter(images, whitelist, args.output)
    create_dirs(needed_dirs, args.dry_run)
    copy_or_move(mapping, args.move, args.dry_run)


if __name__ == '__main__':
    main()
