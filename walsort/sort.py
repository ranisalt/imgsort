import logging
import os
import shutil
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Callable, Dict, FrozenSet, List, Tuple

from PIL import Image

# Setup logging facility
logger = logging.getLogger('walsort')

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


def prepare(paths: List[os.PathLike]) \
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
    return images, frozenset({res for res in whitelist if whitelist[res] >= 10})


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


def main(args):
    images, whitelist = prepare(args.images)

    needed_dirs, mapping = scatter(images, whitelist, args.output)
    create_dirs(needed_dirs, args.dry_run)
    copy_or_move(mapping, args.move, args.dry_run)
