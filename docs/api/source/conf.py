# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from pathlib import Path
sys.path.append(
    Path(__file__).parent.parent.parent.as_posix()
)

project = 'Kola'
copyright = '2023, Ovizro'
author = 'Ovizro'
release = '1.1.0b3'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'recommonmark',
    'sphinx_markdown_tables'
]

autodoc_default_options = {
    'member-order': 'bysource',
    'special-members': '__kola_command__, __kola_write__, __kola_caller__', 
    'undoc-members': True,
    'show-inheritance': True,
    'exclude-members': '__weakref__'
}

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

import sphinx_rtd_theme
html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ['_static']


templates_path = ['_templates']
exclude_patterns = []
