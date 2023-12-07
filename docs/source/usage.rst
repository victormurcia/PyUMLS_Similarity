Usage
=====

.. _installation:

Installation
------------

To use PyUMLS-Similarity, first install it using pip:

.. code-block:: console

   (.venv) $ pip install PyUMLS-Similarity

Computing Semantic Similarity
-----------------------------

PyUMLS-Similarity allows you to compute the semantic similarity between medical concepts from the UMLS database. To start, import the package and initialize it with your UMLS MySQL database information:

.. code-block:: python

   from pyumls_similarity import PyUMLS_Similarity
   mysql_info = {
       "username": "your_username",
       "password": "your_password",
       "hostname": "localhost",
       "socket": "your_socket",
       "database": "umls"
   }
   umls_sim = PyUMLS_Similarity(mysql_info)

You can now use the ``umls_sim.similarity()`` function to compute similarity between pairs of concepts:

.. code-block:: python

   cui_pairs = [
       ('C0018563', 'C0037303'),  # Example CUI pairs
       ('C0035078', 'C0035078'),
       # ... more pairs
   ]
   measures = ['lch', 'wup']
   similarity_df = umls_sim.similarity(cui_pairs, measures)

Handling Exceptions
-------------------

The PyUMLS-Similarity package may raise exceptions if it encounters invalid input or other errors. For example, if an invalid CUI pair is provided, the package will raise a `InvalidCUIPairError`:

.. autoexception:: pyumls_similarity.InvalidCUIPairError

For example:

>>> umls_sim.similarity([('INVALID_CUI', 'C0037303')], measures)
Traceback (most recent call last):
  ...
pyumls_similarity.InvalidCUIPairError: Invalid CUI pair provided
