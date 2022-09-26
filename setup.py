"""
Copyright 2022 Ovizro

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import re
import warnings
from setuptools import setup, Extension

try:
    with open("README.md", encoding='utf-8') as f:
        description = f.read()
except OSError:
    warnings.warn("Miss file 'README.md', using default description.", ResourceWarning)
    description = "simple python module for KoiLang parsing"

try:
    with open("kola/version.py") as f:
        version = re.search(r"__version__\s*=\s*\"(.*)\"\n", f.read()).group(1) # type: ignore
except Exception as e:
    raise ValueError("fail to read kola version") from e


USE_CYTHON = "USE_CYTHON" in os.environ
FILE_SUFFIX = ".pyx" if USE_CYTHON else ".c"

extensions = [
    Extension("kola.lexer", ["kola/lexer" + FILE_SUFFIX, "kola/lex.yy.c"]),
    Extension("kola.parser", ["kola/parser" + FILE_SUFFIX])
]
if USE_CYTHON:
    from Cython.Build import cythonize
    extensions = cythonize(extensions, annotate=True, compiler_directives={"language_level": "3"})


setup(
    name="KoiLang",
    version=version,
    description="simple python module for KoiLang parsing",
    long_description=description,
    long_description_content_type='text/markdown',

    author="Ovizro",
    author_email="Ovizro@hypercol.com",
    maintainer="Ovizro",
    maintainer_email="Ovizro@hypercol.com",
    license="Apache 2.0",

    url="https://github.com/Ovizro/Kola",
    packages=["kola"],
    python_requires=">=3.6",
    package_data={'':["*.pyi", "*.pxd", "*.h"]},
    install_requires=["typing_extensions"],
    ext_modules=extensions,

    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: C",
        "Programming Language :: Cython",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup"
    ]
)