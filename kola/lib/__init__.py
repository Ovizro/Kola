import os

KOLA_LIB_PATH = os.environ.get(
    "KOLA_LIB_PATH", os.path.basename(__file__)
)
