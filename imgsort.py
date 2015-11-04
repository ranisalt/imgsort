#!/usr/bin/env python3
import os
import shutil
from PIL import Image


whitelist = (
    (1366, 768),
    (1600, 900),
    (1680, 1050),
    (1920, 1080),
    (1920, 1200),
)


def split(directory):
    filemap = {dimensions: set() for dimensions in whitelist}
    filemap['others'] = set()

    makepath = lambda filename: os.path.join(directory, filename)
    for filename in os.listdir(directory):
        abspath = makepath(filename)
        if not os.path.isfile(abspath):
            continue

        image = Image.open(abspath)
        if image.size in whitelist:
            filemap[image.size].add(abspath)

        else:
            filemap['others'].add(abspath)

    return filemap


def scatter(filemap, directory, fn):
    makepath = lambda resolution: os.path.join(directory, '%dx%d' % resolution)

    for resolution in whitelist:
        if resolution not in filemap or len(filemap[resolution]) == 0:
            continue

        abspath = makepath(resolution)
        os.makedirs(abspath, exist_ok=True)
        for filename in filemap[resolution]:
            try:
                fn(filename, abspath)
            except shutil.Error:
                pass

    for filename in filemap['others']:
        try:
            fn(filename, directory)
        except shutil.Error:
            pass


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Automatic wallpaper sorter by image dimensions')
    parser.add_argument('origin', type=os.path.abspath)
    parser.add_argument('destiny', type=os.path.abspath)
    parser.add_argument('-m', '--mv', action='store_const', const=shutil.move, default=shutil.copy)

    args = parser.parse_args()
    scatter(split(args.origin), args.destiny, args.mv)


if __name__ == '__main__':
    main()
