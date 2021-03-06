import logging
import math
import os
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from image_match.goldberg import ImageSignature
from PIL import Image

# Setup logging facility
logger = logging.getLogger('walsort')

# Typing aliases
Resolution = Tuple[int, int]


@dataclass
class Metadata:
    filename: os.PathLike
    resolution: Resolution
    signature: float


# Signature generator
gis = ImageSignature()


def get_metadata(image: Image) -> Metadata:
    return Metadata(
            filename=image.filename,
            resolution=image.size,
            signature=gis.generate_signature(
                np.asarray(image.convert('RGB'), dtype=np.uint8)
                )
            )


def ratio(resolution: Resolution) -> float:
    width, height = resolution
    return width / height


def isclose(a: Resolution, b: Resolution) -> bool:
    return math.isclose(ratio(a), ratio(b), rel_tol=1e-03)


def is_duplicate(a: Metadata, b: Metadata, threshold: float):
    # skip if images have different ratio
    if not isclose(a.resolution, b.resolution):
        return False

    # skip if images do not match
    dist = gis.normalized_distance(a.signature, b.signature)
    return dist < threshold


def find_dups(paths: List[os.PathLike], threshold: float) -> List[os.PathLike]:
    dups = []
    images = []

    for filename in paths:
        logger.debug(f'Processing {filename}...')
        try:
            meta = get_metadata(Image.open(filename))
        except (IOError, OSError) as e:
            logger.warn(f'Error opening {filename}: {e}')
            continue

        # detect duplicates
        for i, orig in enumerate(images):
            if not is_duplicate(meta, orig, threshold):
                continue

            if meta.resolution > orig.resolution:
                dups.append(orig.filename)
                images[i] = meta
            else:
                dups.append(meta.filename)
            logger.info(f'{dups[-1]} is duplicate of {images[i].filename}')
            break

        # if loop doesn't break, a duplicate is found
        else:
            images.append(meta)

    return dups


def clean(filenames: List[os.PathLike], dry_run: bool):
    for filename in filenames:
        logger.debug(f'Removing {filename}')
        if not dry_run:
            os.remove(filename)


def main(args):
    dups = find_dups(args.images, args.threshold)
    clean(dups, args.dry_run)
