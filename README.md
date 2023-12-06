## Overview

This package computes a variety of semantic similarity metrics between concepts present in the UMLS (Unified Medical Language System) database. It serves as a Python wrapper based off the Perl modules ([UMLS Interface](https://metacpan.org/dist/UMLS-Interface) and [UMLS Similarity](https://metacpan.org/dist/UMLS-Similarity)) developed by Bridget McInnes and Ted Pedersen, offering an accessible and user-friendly interface for Python users.

## Available Similarity Measures

    * The basic path measure --> path
    * The undirected path measure --> upath
    * Leacock and Chodorow (1998) --> lch
    * Wu and Palmer (1994) --> wup
    * Zhong, et al. (2002) --> zhong
    * Rada, et. al. (1989) --> cdist
    * Nguyan and Al-Mubaid (2006) --> nam
    * Resnik (1996) --> res
    * Lin (1988) --> lin
    * Jiang and Conrath (1997) --> jcn
    * The vector measure --> vector
    * Pekar and Staab (2002) --> pks
    * Pirro and Euzenat (2010) --> faith
    * Maedche and Staab (2001) --> cmatch
    * Batet, et al (2011) --> batet
    * Sanchez, et al. (2012) --> sanchez

## Installation

To install PyUMLS_Similarity, run the following command:

```
pip install PyUMLS-Similarity
```

## Prerequisites

Before using the PyUMLS_Similarity package, ensure that you have the following prerequisites installed and set up:

### Strawberry Perl

The package requires Strawberry Perl to run Perl scripts. Download and install it from [Strawberry Perl's official website](http://strawberryperl.com/).

### MySQL

A local MySQL database instance is required to store and access UMLS data. Download and install MySQL from [MySQL's official download page](https://dev.mysql.com/downloads/mysql/). This package was tested on MySQL 8.1.0.

In order to work efficiently with the UMLS, you'll want to configure MySQL. A good starting point is to use the parameters designated by the UMLS found [here](https://www.nlm.nih.gov/research/umls/implementation_resources/scripts/README_ORF_MySQL_Output_Stream.html).

### UMLS Data

You need to have a local instance of the UMLS installed in MySQL. This involves downloading UMLS data and importing it into your MySQL database. Follow the guidelines provided by the UMLS for [obtaining a license](https://uts.nlm.nih.gov/license.html) and [downloading the UMLS data](https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html).

### UMLS-Interface and UMLS-Similarity Perl Modules

The package depends on the UMLS-Interface and UMLS-Similarity Perl modules. If you are interested in using feature-based semantic similarity metrics you'll also want to download [WordNet](https://wordnet.princeton.edu/download/old-versions) and the associated Perl modules. After installing Strawberry Perl, install these modules using CPAN:

```
cpanm UMLS::Interface --force
cpanm UMLS::Similarity --force
cpanm WordNet::QueryData
cpanm WordNet::Similarity
```

## Usage

**IMPORTANT**: The first time you run a path based semantic similarity metric calculation, the UMLS Interface needs to create an index within MySQL of your UMLS instance for efficient pathing calculations in subsequent runs. This can be a long process depending on your machine hardware and your MySQL configuration. The default source vocabulary (SAB) is the UMLS Metathesaurus (MTH). Indexing this was relatively fast in my machine (a few minutes). It is possible to use/include other SABs as part of your UMLS Interface configuration like SNOMED, LOINC, CPT, etc. however, be warned that this will exponentially increase both the required memory for your process AND the time required for the indexing. For example, indexing SNOMED took about 2 days.   


Below are some examples of how to use the PyUMLS_Similarity package.

Start by initiating an instance of the PyUMLS_Similarity class:

```
from PyUMLS-Similarity import PyUMLS_Similarity

# define MySQL information that stores UMLS data in your computer
mysql_info = {}
mysql_info = {
    "username": "root",
    "password": "your_password",
    "hostname": "localhost",
    "socket": "MYSQL",
    "database": "umls"
}

umls_sim = PyUMLS_Similarity(mysql_info=mysql_info)

```

### Computing Multiple Similarity Metrics

You can compute similarity metrics between UMLS concepts as shown below. 

You can either provide a list of tuples contains the CUIs to be compared:

```
cui_pairs = [
    ('C0018563', 'C0037303'),
    ('C0035078', 'C0035078'),
    ('C0018787' ,'C0027061')
]
```
Or you can provide a list of tuples containing the medical terms you want to be compare:

```
cui_pairs = [
    ('hand', 'skull'),
    ('Renal failure', 'Kidney failure'),
    ('Heart' ,'Myocardium')
]
```

## Compute similarity using specific measures

```
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

PyUMLS_Similarity also supports running tasks concurrently for efficiency. Each time the Perl module is called it triggers a new connection to the database. This overhead is actually the most time consuming portion and running functions sequentially and/or separately adds up more and more overhead. To save time, I've made it so multiple functions can be run concurrently via Python's threading module. This essentially removes the overhead time of any additional function calls.

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

## Future Developments
Future developments of this package will 

* allow for calculations of standard similarity metrics like cosine similarity, sorensen-dice index, jaccard similarity, and others
* allow for modifications of the UMLS Interface Configuration file
