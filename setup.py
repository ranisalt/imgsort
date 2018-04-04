import setuptools

try:
    import imgsort
except ImportError:
    print('error: imgsort requires Python 3.5 or greater.')
    quit(1)

LONG_DESC = open('README.md').read()

VERSION = imgsort.__version__
DOWNLOAD = 'https://github.com/ranisalt/imgsort/archive/%s.tar.gz' % VERSION

setuptools.setup(
    name='imgsort',
    version=VERSION,
    author='Ranieri Althoff',
    author_email='ranisalt@protonmail.com',
    description='Sort images (wallpapers) based on resolution',
    long_description=LONG_DESC,
    license='MIT',
    url='https://github.com/ranisalt/imgsort',
    download_url=DOWNLOAD,
    classifiers=[
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={'console_scripts': ['imgsort=imgsort.__main__:main']},
    python_requires='>=3.5',
)
