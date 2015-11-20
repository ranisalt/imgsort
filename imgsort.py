#!/usr/bin/env python3
import logging
import os
import shutil
from PIL import Image


WHITELIST = {
        (1366, 768),
        (1440, 900),
        (1600, 900),
        (1680, 1050),
        (1920, 1080),
        (1920, 1200),
        (2560, 1440),
        (2560, 1600),
        }


def split(directory, recursive=False):
    filemap = {dimensions: set() for dimensions in WHITELIST}
    filemap['others'] = set()

    makepath = lambda directory, filename: os.path.join(directory, filename)

    to_visit = set(makepath(directory, f) for f in os.listdir(directory))
    while to_visit:
        filename = to_visit.pop()

        if recursive and os.path.isdir(filename):
            logging.debug('Found directory at %s' % filename)
            to_visit.update(makepath(filename, f) for f in os.listdir(filename))
            continue

        try:
            image = Image.open(filename)
        except IOError:
            continue

        if image.size in WHITELIST:
            filemap[image.size].add(filename)

        else:
            filemap['others'].add(filename)

    logging.info('Found %d images with %d resolutions' % (sum(map(len, filemap)), len(filemap)))
    return filemap


def scatter(filemap, directory, fn, ignore=False):
    makepath = lambda resolution: os.path.join(directory, '%dx%d' % resolution)
    samepath = lambda filename, destdir: os.path.split(filename)[0] == destdir

    def try_move(filename, destiny):
        logging.debug('Moving %s to %s' % (filename, destiny))
        try:
            if not samepath(filename, destiny):
                fn(filename, destiny)
        except shutil.Error:
            logging.warn('Failed to move %s to %s' % (filename, destiny))

    for resolution in WHITELIST:
        if resolution not in filemap or not filemap[resolution]:
            continue

        abspath = makepath(resolution)
        os.makedirs(abspath, exist_ok=True)
        for filename in filemap[resolution]:
            try_move(filename, abspath)

        logging.info('Moved %d files to %dx%d' % (len(filemap[resolution]), resolution[0], resolution[1]))

    if not ignore:
        for filename in filemap['others']:
            try_move(filename, directory)

def main():
    import argparse

    parser = argparse.ArgumentParser(
            description='Automatic wallpaper sorter by image dimensions')
    parser.add_argument('origin', type=os.path.abspath)
    parser.add_argument('destiny', type=os.path.abspath)
    parser.add_argument('-i', '--ignore', action='store_true', help='ignore files not in resolution whitelist')
    parser.add_argument('-m', '--move', action='store_const', const=shutil.move, default=shutil.copy)
    parser.add_argument('-r', '--recursive', action='store_true')

    args = parser.parse_args()
    scatter(split(args.origin, args.recursive), args.destiny, args.move, args.ignore)


if __name__ == '__main__':
    main()
