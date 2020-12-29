import os
import pandas as pd
from recommend import recommender


def charts(choice):
    fpath = os.path.join('assets', 'data', choice)
    df = pd.read_csv(fpath)
    results = recommender(df)
    return {'charts': results['chart_list'], 'data': df}
