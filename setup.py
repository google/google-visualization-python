#!/usr/bin/python
#
# Copyright (C) 2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Setup module for Google Visualization Python API."""

import codecs
import os.path

import setuptools


here = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(here, "README.rst"), encoding="utf-8") as f:
  long_description = f.read()


setuptools.setup(
    name="gviz_api",
    version="1.9.0",
    description="Python API for Google Visualization",
    long_description=long_description,
    url="https://github.com/google/google-visualization-python",
    author="Amit Weinstein, Misha Seltzer, Jacob Baskin",
    license="Apache 2.0",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    keywords="gviz,google visualization",
    py_modules=["gviz_api"],
    install_requires=["six"],
    test_suite="gviz_api_test",
)
