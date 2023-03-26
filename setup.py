# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

import opf

# The directory containing this file
HERE = path.abspath(path.dirname(__file__))

EMOJIES = [':zap:', ':o:', ':x:']

def load_description(path_dir=HERE, filename='README.md'):
    with open(path.join(HERE, filename), 'r', encoding='utf-8') as f:
        desc = f.read().split(' ')
        return ' '.join([d for d in desc if d not in EMOJIES])

def load_requirements(path_dir=HERE, filename='requirements.txt', comment_char='#'):
    reqs = []
    with open(path.join(path_dir, filename), "r") as f:
        lines = [ln.strip() for ln in f.readlines()]
    
    for ln in lines:
        # filer all comments
        if comment_char in ln:
            ln = ln[: ln.index(comment_char)].strip()
        # skip directly installed dependencies
        if ln.startswith("http"):
            continue
        if ln:  # if requirement is not empty
            reqs.append(ln)
    return reqs

packages = [
    'opf',
    'opf.io',
    'opf.core'
]
# This call to setup() does all the work
setup(
    name="opf",
    version=opf.__version__,
    description="PyOPF: Optimal Power Flow Modeling in Python",
    long_description=load_description(),
    long_description_content_type="text/markdown",
    author="Seonho Park",
    author_email="park.seonho@gmail.com",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent"
    ],
    packages=packages,
    include_package_data=True,
    install_requires=load_requirements(),
    project_urls={
        'Github': 'https://github.com/seonho-park/PyOPF'
    },
    python_requires='>=3.8'
)
