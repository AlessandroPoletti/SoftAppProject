import os

# todo: add .css document
# todo: Finish documentation
# todo: write docs.json
# todo: update git
# todo: add color to documentation
# todo: add dropdown mennu to the documentation
# todo: organize python files in a folder, keep main out



# ---------- Settings ----------

# Base url for the publications on PubMed
BASE_PMID_URL = 'https://pubmed.ncbi.nlm.nih.gov/'


# ---------- Paths Settings ----------

# Location of the documentation json file. The default path is "\static\docs.json"
DOCS_PATH = os.path.join(os.getcwd(), r'static\docs.json')


# Locations of the two datasets. The default path is "\datasets"
DATASET_LOCATION = os.path.join(os.getcwd(), r'datasets')

# Datasets name
GENE_TABLE_NAME = 'gene_evidences.tsv'
DISEASE_TABLE_NAME = 'disease_evidences.tsv'


# ---------- Cache Settings ----------

# IF YOU DON'T KNOW WHAT YOU ARE DOING, DON'T DO IT

# cache settings
CACHE_CONFIG = {
    "DEBUG": True,  # some Flask specific configs
    "CACHE_TYPE": "simple",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 3600
}

# The cache stores the data as "Key: Value" pairs. This is the name of the Key which will contain
# the table (as list) computed when an operation on the datasets is called, to be later downloaded.
# If you haven't changed the code, any name is fine.
TABLE_CACHE_NAME = 'table_cache'
