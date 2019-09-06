from read_raw_data import get_plotly_dfs
from pymongo import MongoClient
def get_axis(name):
    return [name + ', x', name + ', y']
def get_category(table):
    categories = []
    for col in table['chart_data']:
        category = None
        if 'type' in col:
            category = col['type']
        elif 'mode' in col:
            category = col['mode']
        if category:
            if category not in types:
                categories.append(category)
    return categories


def get_col_type(col):
    if 'type' in col.keys():
        if col['type'] == 'scatter':
            if 'mode' in col.keys():
                return col['mode']
            return 'scatter'
        else:
            return col['type']
    if 'mode' in col.keys():
        return col['mode']
    return "other"


def get_uid(str_uid):
    splits = str_uid.split(':')
    assert len(splits) == 3
    src_id = splits[0] + ':' + splits[1]
    return src_id, splits[2]




def process_col(col, uid_map, df):
    inline = False
    has_y = False
    if 'x' in col.keys():
        inline = True
        if 'y' in col.keys():
            has_y = False
    else:
        if 'ysrc' in col.keys():
            has_y = False

    if inline:
        xsrc = 'inline'
        column_x = 'inline'
        x_data = col['x']
        pass
    else:
        x_src_id, column_x_uid = get_uid(col['xsrc'])
        column_x = table['uid_map'][x_src_id][column_x_uid]
        xsrc = col['xsrc']
        x_data = list(df[column_x])


    vis_type = get_col_type(col)
    name = "y"
    if 'name' in col.keys():
        name = col['name']
    document = {
        'vis_type': vis_type,
        'name': name,
        'column_x': column_x,
        'x': x_data,
        'col': col,
        'xsrc': xsrc,
        'data_type': 'x',
        'inline': 'inline'
    }
    if has_y:
        if inline:
            document['ysrc'] = 'inline'
            document['y'] = col['y'],
            document['column_y'] = 'inline',
            document['data_type'] = "y-x"
        else:
            y_src_id, column_y_uid = get_uid(col['ysrc'])
            column_y = table['uid_map'][y_src_id][column_y_uid]
            document['ysrc'] = col['ysrc']
            document['y'] = list(df[column_x]),
            document['column_y'] = column_y,
            document['data_type'] = "y-x"
    return document

def process_chart(table):
    vis_types = set()
    vis_style = "not_set"
    axises = {}

    if 'yaxis' not in table['chart_data'][0].keys():
        axises['y'] = list(range(len(table['chart_data'])))
    else:
        for i, col in enumerate(table['chart_data']):
            if col['yaxis'] in axises.keys():
                axises[col['yaxis']].append(i)
            else:
                axises[col['yaxis']] = [i]
    documents = []
    vis_type = get_col_type(table['chart_data'][0])
    if vis_type == 'table':
        return {},{}, None

    for yaxis, ids in axises.items():
        if len(ids) == 1:
            i = ids[0]
            col = table['chart_data'][i]
            data_document = process_col(col, table['uid_map'], table['df'])
            document = {
                'dataset_id': table['dataset_id'],
                'order': i,
                'locator': table['locator'],
                'vis_type': data_document['vis_type'],
                'data_type': 'monoseq',
                'data': [data_document],
            }
            documents.append(document)
        else:
            min_value = ids[0]
            for i in ids:
                if min_value > i:
                    min_value = i
            vis_type = get_col_type(table['chart_data'][min_value])
            document = {
                'dataset_id': table['dataset_id'],
                'order': min_value,
                'orders': ids,
                'data_type': "multiseq",
                'vis_type': vis_type,
                'locator': table['locator']
            }

            data_docs = []
            for i in ids:
                i_doc = process_col(table['chart_data'][i], table['uid_map'], table['df'])
                data_docs.append(i_doc)
            document['data'] = data_docs
            documents.append(document)
        vis_types.add(vis_type)
    plot = {
        'dataset_id': table['dataset_id'],
        'locator': table['locator']
    }
    return plot, documents, vis_types





tables = get_plotly_dfs(limit=1)
line_count = 0
count = 0
types = []
client = MongoClient()
collection = client['vis_data'].data
plots = client['vis_data'].plots
# for i, table in enumerate(tables):
#     print(i)
vis_types = set()
for table in tables:
    plot, documents, table_types = process_chart(table)
    # collection.insert_many(tables)
    if not table_types:

        continue
    if len(table_types) > 1:
        print(table_types)
    vis_types = vis_types.union(table_types)
    collection.insert_many(documents)
    plots.insert(plot)
    count += 1
    
    if count % 100 == 0:
        print("finished: ", count)
print(vis_types)
# try:
#     for table in tables:
#         documents, table_types = process_chart(table)
#         vis_types.union(vis_types)
#         # categories = get_category(table)
#         # for col in table['chart_data']:
#         #     category = None
#         #     if 'type' in col:
#         #         category = col['type']
#         #     elif 'mode' in col:
#         #         category = col['mode']
#         # if 'line' in categories:
#         #     line_count += 1
#         count += 1
#         if count == 100:
#             break
#         if count % 1000 == 0:
#             print("finished: ", count)
#         # table['df'][]
#         # try:
#         #     if table['chart_data'][0]['type'] == "line":
#         #         count += 1
#         # except:
#         #     if table['chart_data'][0]['mode'] == "line":
#         #         count += 1
#         # print(table['chart_data'])
# except Exception as e:
#     print(e)
# print(vis_types)
# # print(count)
# # print(types)