import os
import pandas as pd
from pathlib import Path

DATA_DIR = str(Path(__file__).parent.parent.parent/'data')


def load_raw_data():
    files = os.listdir(f'{DATA_DIR}/raw')
    df = pd.concat([pd.read_csv(f'{DATA_DIR}/raw/{f}') for f in files])
    return df.reset_index()