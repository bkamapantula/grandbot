import operator
import logging
import numpy as np
from functools import reduce  # forward compatibility for Python 3
import gramex.cache

root = logging.getLogger()
root.setLevel(logging.DEBUG)
DATA_LENGTH = 2000

chart_possible = {
    'coltype_combination':
    {
        'num_and_cat': {
            'one_num_one_cat': {
                'one_obs_per_group': ['lollipop', 'barchart', 'circularbar', 'treemap', 'circlepacking'],
                'several_obs_per_group': ['boxplot', 'violin-plot']
            },
            'one_cat_several_num': {  # NOTE: Could not understand rationale behind no_order, a_num_is_ordered in data-to-viz.com
                'one_value_per_group': ['multiline', 'parallelcoordinates', 'stacked-column', 'groupbar'],
                'multiple_values_per_group': ['groupscatterplot']
            },
            'several_cat_one_num': {
                'subgroup': {
                    'one_obs_per_group': ['multiline', 'parallelcoordinates', 'stacked-column', 'groupbar'],
                    'several_obs_per_group': ['boxplot', 'violin-plot']
                },
                'nested': {
                    'one_obs_per_group': ['lollipop', 'barchart', 'circularbar', 'treemap', 'circlepacking'],
                    'several_obs_per_group': ['boxplot', 'violin-plot']
                },
                'adjacency': ['network', 'sankey', 'chord', 'arc']
            }
        },
        'numerical': {
            'one_num': ['histogram', 'density_plot'],
            'two_num': {
                'not_ordered': {
                    'few_points': ['facet_box_plot', 'scatterplot'],
                    'many_points': ['facet_violin_plot', 'facet_densityplot']
                },
                'ordered': ['linechart', 'area-chart', 'connected_scatterplot']
            },
            'three_num': {
                'not_ordered': ['boxplot', 'violin-plot', 'bubblechartlegend'],
                'ordered': ['area-chart', 'multiline']
            },
            'several_num': {
                'not_ordered': ['boxplot', 'violin-plot', 'heatmap', 'correlogram'],
                'ordered': ['area-chart', 'multiline']
            }
        },
        'categorical': {
            'one_cat': ['barchart', 'lollipop', 'donut', 'treemap', 'circlepacking'],
            'several_cat': {
                'nested': ['treemap', 'sunburst'],
                'subgroup': ['groupscatterplot', 'parallelcoordinates', 'stacked-column', 'groupbar'],
                'adjacency': ['network', 'sankey', 'heatmap']
            }
        }
    }
}


def get_from_dict(data_dict, map_list):
    return reduce(operator.getitem, map_list, data_dict)


def initiate(handler):
    """Setup chart recommendation workflow

    Args:
        handler (object): tornado request object

    Returns:
        charts_recommended (json): list of recommended charts against `chart_list` key
    """
    # TODO: write a null check on dataframe. It should have at least one column.
    df = gramex.cache.open('data.xlsx')

    pivot_df = None
    # if len(df.select_dtypes(include=['number']).columns) > 4 or handler.args.pivot == True:
    #     pivot_df = df.pivot()
    df = df[['ID', 'c1']]

    charts_recommended = recommender(pivot_df or df)
    return charts_recommended


def recommender(df):
    """Recommend charts for a given pandas dataframe

    Args:
        df (pandas dataframe): pandas dataframe for the given data file

    Returns:
        (json): list of charts recommended mapped against `chart_list` key
    """
    # BFS but will go further down only if certain condition is possible
    # So, a node is pushed to the BFS
    queue = []
    charts_recommended = []
    visited_nodes_path = []
    node_path = []

    for key in chart_possible:
        queue.append(key)
        visited_nodes_path.append(key)

    while len(queue) > 0:
        node_visited = queue.pop(0)
        if isinstance(get_from_dict(chart_possible, visited_nodes_path), list):   # headsup: you are at leaf node
            charts_recommended.extend(get_from_dict(chart_possible, visited_nodes_path))
            # break
        else:
            loc = {}
            exec('loc["next_node"] = ' + node_visited + '(df)', globals(), locals())
            queue.append(loc['next_node'])
        visited_nodes_path.append(loc['next_node'])
        node_path.append(node_visited)

    return {'chart_list': charts_recommended, 'path': node_path}


def coltype_combination(df):
    """returns combination for column types
        https://stackoverflow.com/a/29803297

    Args:
        fields_names {list} -- Field names and
        type_map {dict} -- dictionary of field names and its corresponding dtypes

    Returns:
        [string] -- [categorical, numerical and num_and_cat]
    """
    number_df = df.select_dtypes(exclude=['number'])
    if len(number_df.columns) == 0:
        return 'numerical'
    elif len(number_df.columns) == len(df.columns):
        return 'categorical'
    else:
        return 'num_and_cat'


def num_and_cat(df):
    if len(df.columns) == 2 and len(df.select_dtypes(include=['number']).columns) == 1:
        return 'one_num_one_cat'
    elif len(df.select_dtypes(exclude=['number']).columns) == 1:
        return 'one_cat_several_num'
    else:
        return 'several_cat_one_num'


def numerical(df):
    if len(df.columns) == 1:
        return 'one_num'
    elif len(df.columns) == 2:
        return 'two_num'
    elif len(df.columns) == 3:
        return 'three_num'
    return 'several_num'


def categorical(df):
    """
    Args:
        df (dataframe): pandas dataframe

    Returns:
        (str): appropriate categorization for category columns
    """
    return 'one_cat' if len(df.columns) == 1 else 'several_cat'


def two_num(df):
    return 'ordered' if ordered(df) else 'not_ordered'


def three_num(df):
    return 'ordered' if ordered(df) else 'not_ordered'


def several_num(df):
    return 'ordered' if ordered(df) else 'not_ordered'


def one_num_one_cat(df):
    return 'one_obs_per_group' if one_obs_per_group(df) else 'several_obs_per_group'


def several_cat_one_num(df):
    cat_cols = df.select_dtypes(exclude=['number'])
    if len(cat_cols) == 2 and df[cat_cols[0]].unique().sort() == df[cat_cols[1]].unique().sort():
        return 'adjacency'
    return 'subgroup'


def several_cat(df):
    # print(df[df.columns[0]].unique(), df[df.columns[1]].unique())
    if len(df.columns) == 2 and df[df.columns[0]].unique().sort() == df[df.columns[1]].unique().sort():
        return 'adjacency'
    else:
        return 'subgroup'


def one_obs_per_group(df):
    return one_value_per_group(df)


def one_cat_several_num(df):
    return 'one_value_per_group' if one_value_per_group(df) else 'multiple_values_per_group'


def one_value_per_group(df):
    one_cat_df = df.select_dtypes(exclude=['number'])
    col_name = one_cat_df.columns[0]
    return one_cat_df[col_name].unique().size == one_cat_df[col_name].size


def multiple_values_per_group(df, one_cat):
    return not one_value_per_group


# A dataframe is ORDERED if one column is ordered
def ordered(df):
    """check if any column in dataframe is ordered

    # Alternate solution?: https://stackoverflow.com/a/17705498

    Args:
        df {dataframe} -- Expects a dataframe which contains **only numerical columns**

    Returns:
        [boolean] -- [description]
    """
    return any((np.diff(df[colname]) > 0).all() for colname in df.columns)


def not_ordered(df):
    if len(df.columns) == 2:
        return 'few_points' if len(df) < DATA_LENGTH else 'many_points'
    return not ordered(df)


def subgroup(df):
    return 'one_obs_per_group' if one_obs_per_group(df) else 'several_obs_per_group'


def nested(df):
    return 'one_obs_per_group' if one_obs_per_group(df) else 'several_obs_per_group'


def group_type(categorical_cols):
    """if multiple categorical cols chosen, this function is called.

    Args:
        categorical_cols {[type]} -- [description]
    """
    raise NotImplementedError


def group_item_type(categorical_col):
    """[summary]

    Args:
        categorical_col {[type]} -- [description]

    Returns:
        [type] -- [description]
    """
    raise NotImplementedError


if __name__ == "__main__":
    logging.debug(initiate(''))
