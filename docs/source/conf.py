# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- REQUIREMENTS -----------------------------------------------------
# pip install sphinx-material
# pip install sphinxemoji

import datetime
import os
import re
import sys
import asyncio
import platform

sys.path.insert(0, os.path.abspath("../"))
# -- Project information

project = 'PyUMLS-Similarity'
copyright = '2023, Victor M. Murcia'
author = 'Victor M. Murcia'

release = '0.1'
version = '0.1.0'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.viewcode",
    "IPython.sphinxext.ipython_console_highlighting",
    "IPython.sphinxext.ipython_directive",
    "sphinxemoji.sphinxemoji",
    "sphinx_copybutton",
    "myst_nb",
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# Ignore duplicated sections warning
suppress_warnings = ["epub.duplicated_toc_entry"]
nitpicky = False  # Set to True to get all warnings about crosslinks

# Prefix document path to section labels, to use:
# `path/to/file:heading` instead of just `heading`
autosectionlabel_prefix_document = True

# -- Options for autodoc -------------------------------------------------
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = False
napoleon_use_ivar = False
napoleon_use_rtype = False
add_module_names = False  # If true, the current module name will be prepended to all description

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'
