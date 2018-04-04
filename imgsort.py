#!/usr/bin/env python3
import logging
import os
import shutil
from functools import lru_cache
from typing import Any, Callable, Dict, List, Set, Tuple

from dataclasses import dataclass, field
from PIL import Image

__version__ = '0.1'

try:
    from image_match.goldberg import ImageSignature

    # Signature generator
    gis = ImageSignature()

    def distance(a: float, b: float) -> float:
        return gis.normalized_distance(a, b)

    def signature(image: 'ImageMetadata') -> float:
        return gis.generate_signature(image.filename)

    IMAGE_MATCH_ENABLED = True
except ImportError:
    IMAGE_MATCH_ENABLED = False

# Setup logging facility
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(fmt)
logger.addHandler(ch)


@dataclass
class ImageMetadata:
    image: Image
    _signature: float = field(init=False)

    @property
    def basename(self):
        return os.path.basename(self.image.filename)

    @property
    def dirname(self):
        return os.path.dirname(self.image.filename)

    @property
    def filename(self):
        return self.image.filename

    @property
    def resolution(self):
        return self.image.size

    @property
    def signature(self):
        if not self._signature:
            self._signature = signature(self)
        return self._signature


# Typing aliases
ImageMap = Dict[os.PathLike, ImageMetadata]
Resolution = Tuple[int, int]

WHITELIST: Set[Resolution] = {
    (1366, 768),
    (1440, 900),
    (1600, 900),
    (1680, 1050),
    (1920, 1080),
    (1920, 1200),
    (1920, 1280),
    (1920, 1440),
    (2560, 1440),
    (2560, 1600),
    (2880, 1800),
    (3840, 1080),
    (3840, 1200),
    (3840, 2160),
}


def prepare(paths: List[os.PathLike], similarity: bool) -> List[ImageMetadata]:
    images: List[ImageMetadata] = []

    for path in paths:
        try:
            image = Image.open(path)
        except IOError as e:
            logger.warn(f'Error opening {path}: {e}')
            continue

        logger.debug(f'Processing metadata for {path}')
        images.append(ImageMetadata(image=image))

    logger.info(f'Found {len(images)} images')
    return images


def trim_by_whitelist(images: List[ImageMetadata]) -> List[ImageMetadata]:
    return [image for image in images if image.resolution in WHITELIST]


# TODO
def trim_by_similarity(images: List[ImageMetadata]) -> List[ImageMetadata]:
    return []


@lru_cache()
def path_to_resolution(dirname: os.PathLike, resolution: Resolution) \
        -> os.PathLike:
    if resolution in WHITELIST:
        return os.path.join(dirname, '{}x{}'.format(*resolution))
    return dirname


def path_to_image(dirname: os.PathLike, image: ImageMetadata) -> os.PathLike:
    path = path_to_resolution(dirname, image.resolution)
    return os.path.join(path, image.basename)


def scatter(images: List[ImageMetadata], output: os.PathLike) \
        -> Tuple[List[os.PathLike], Dict[os.PathLike, os.PathLike]]:
    needed_dirs = set()
    if not os.path.isdir(output):
        needed_dirs.add(output)

    mapping = dict()
    for image in images:
        destdir = path_to_resolution(output, image.resolution)
        dest = os.path.join(destdir, image.basename)

        if os.path.isfile(dest) and os.path.samefile(image.filename, dest):
            continue

        needed_dirs.add(destdir)
        mapping[image.filename] = dest

    return needed_dirs, mapping


def create_dirs(dirs: List[os.PathLike], dry_run: bool):
    for dir_ in dirs:
        if not os.path.isdir(dir_):
            logger.info(f'mkdir {dir_}')
            if not dry_run:
                os.makedirs(dir_)


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

    parser.add_argument('-i', '--ignore', action='store_true',
                        help='ignore files not in resolution whitelist')
    parser.add_argument('-m', '--move', action='store_const',
                        const=shutil.move, default=shutil.copyfile)
    parser.add_argument('-n', '--dry-run', action='store_true')

    if IMAGE_MATCH_ENABLED:
        match = parser.add_argument_group('similarity detection')
        match.add_argument('-s', '--similar', action='store_true',
                           help='try and find similar images')
        match.add_argument('-t', '--threshold', type=float, default=0.4,
                           metavar='T', help='similarity threshold')

    # TODO: watch folder

    parser.add_argument('images', nargs='*', type=os.path.abspath)
    parser.add_argument('output', type=os.path.abspath)

    args = parser.parse_args()

    images = prepare(args.images, args.similar)

    if args.ignore:
        count = len(images)
        images = trim_by_whitelist(images)
        logger.debug(f'Trimmed {count - len(images)} images by whitelist')

    needed_dirs, mapping = scatter(images, args.output)
    create_dirs(needed_dirs, args.dry_run)
    copy_or_move(mapping, args.move, args.dry_run)


if __name__ == '__main__':
    main()
