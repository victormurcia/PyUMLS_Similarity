## Overview

This package computes a variety of similarity metrics between concepts present in the UMLS (Unified Medical Language System) database. It serves as a Python wrapper based off the Perl module developed by Bridget McInnes and Ted Pedersen, offering an accessible and user-friendly interface for Python users.

## Installation

To install PyUMLS_Similarity, run the following command:

```
pip install pyumls_similarity
```

## Prerequisites

Before using the PyUMLS_Similarity package, ensure that you have the following prerequisites installed and set up:

### Strawberry Perl

The package requires Strawberry Perl to run Perl scripts. Download and install it from [Strawberry Perl's official website](http://strawberryperl.com/).

### MySQL

A local MySQL database instance is required to store and access UMLS data. Download and install MySQL from [MySQL's official download page](https://dev.mysql.com/downloads/mysql/).

### UMLS Data

You need to have a local instance of the UMLS installed in MySQL. This involves downloading UMLS data and importing it into your MySQL database. Follow the guidelines provided by the UMLS for [obtaining a license](https://uts.nlm.nih.gov/license.html) and [downloading the UMLS data](https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html).

### UMLS-Interface and UMLS-Similarity Perl Modules

The package depends on the UMLS-Interface and UMLS-Similarity Perl modules. After installing Strawberry Perl, install these modules using CPAN:

```
cpanm UMLS::Interface
cpanm UMLS::Similarity
```


## Usage

Below are some examples of how to use the PyUMLS_Similarity package.

Start by initiating an instance of the PyUMLS_Similarity class:

```
from pyumls_similarity import PyUMLS_Similarity

mysql_info = {
    "username": "your_username",
    "password": "your_password",
    "hostname": "localhost",
    "socket": "your_socket",
    "database": "umls"
}

umls_sim = PyUMLS_Similarity(mysql_info=mysql_info)

```

### Computing Multiple Similarity Metrics

You can compute similarity metrics between UMLS concepts as shown below:

```
cui_pairs = [
    ('C0018563', 'C0037303'),
    ('C0035078', 'C0035078'),
]

# Compute similarity using specific measures
measures = ['lch', 'wup']
similarity_df = umls_sim.similarity(cui_pairs, measures)

```

An example output would look something like this:
|    | Term 1        | Term 2        | CUI 1    | CUI 2    | lch   | wup   |
|----|---------------|---------------|----------|----------|-------|-------|
| 0  | hand          | skull         | C0018563 | C0037303 | 0.500 | 0.700 |
| 1  | Renal failure | Kidney failure| C0035078 | C0035078 | 1.000 | 1.000 |
| 2  | Heart         | Myocardium    | C0018787 | C0027061 | 0.823 | 0.875 |


### Finding Shortest Path

To find the shortest path between concepts:

```
shortest_path_df = umls_sim.find_shortest_path(cui_pairs)
```

### Finding Least Common Subsumer

To find the least common subsumer (LCS) of concepts:

```
lcs_df = umls_sim.find_least_common_subsumer(cui_pairs)
```

### Concurrency

PyUMLS_Similarity also supports running tasks concurrently for efficiency:

```
tasks = [
    {'function': 'similarity', 'arguments': (cui_pairs, measures)},
    {'function': 'shortest_path', 'arguments': (cui_pairs)},
    {'function': 'lcs', 'arguments': (cui_pairs)}
]

results = umls_sim.run_concurrently(tasks)
```

## Acknowledgements

This package is based on the Perl module developed by Bridget McInnes and Ted Pedersen.
