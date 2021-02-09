import os
import pandas as pd
import json
from zipfile import ZipFile, ZIP_DEFLATED
from recommend import recommender
from tempfile import TemporaryFile
from tornado.template import Template


UI = """
import:
  ui:
    path: $GRAMEXAPPS/ui/gramex.yaml
    YAMLURL: /$YAMLURL/ui/
"""


def charts(choice):
    fpath = os.path.join('assets', 'data', choice)
    df = pd.read_csv(fpath, encoding='utf8')
    results = recommender(df)
    return {'charts': results['chart_list'], 'data': df}


def render_template(fpath, **args):
    with open(fpath, 'r') as fout:
        return Template(fout.read()).generate(**args)


def export(handler):
    # args = {k: json.loads(v[0]) for k, v in handler.args.items()}
    args = {k: v for k, v in handler.args.items()}
    args['charts_data'] = charts(handler.get_argument('data_choice'))['data']
    with open('download.html') as fout:
        tmpl = Template(fout.read()).generate(**args)
    with TemporaryFile() as tf:
        with ZipFile(tf, 'w', ZIP_DEFLATED) as arch:
            # Write the template
            arch.writestr('index.html', tmpl.decode('utf8'))
            # Write gramex.yaml
            arch.writestr('gramex.yaml', UI)
        tf.seek(0)
        return tf.read()
