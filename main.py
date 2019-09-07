from read_raw_data import get_plotly_dfs
from pymongo import MongoClient
import random
import re
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


def clip_seq(seq, limit=1000):
    if len(seq) > limit:
        start = random.randint(0, len(seq) - 1000)
        return seq[start: start + limit]
    else:
        return seq

def clip_too_long(data_doc):
    if len(data_doc['x']) > 1000:
        start = random.randint(0, len(data_doc['x']) - 1000)
        data_doc['x'] = data_doc['x'][start: start + 1000]
        if 'y' in data_doc.keys():
            data_doc['y'] = data_doc['y'][start: start + 1000]
        return data_doc
    else:
        return data_doc

def process_pie_col(col, uid_map, df):
    value_scr_id, value_uid = get_uid(col['valuessrc'])
    label_src_id, label_uid = get_uid(col['labelssrc'])
    vis_type = "pie"
    name = "pie"
    column_value = uid_map[value_scr_id][value_uid]
    value_data = list(df[column_value])

    column_label = uid_map[label_src_id][label_uid]
    label_data = list(df[column_label])
    document = {
        'vis_type': vis_type,
        'name': name,
        'label': label_data,
        'value': value_data,
        # 'col': col,
        'data_type': 'label-value',
        'inline': 'inline'
    }
    return document

def split_uid(uid):
    if uid[0] == '-':
        uid = uid[1:]
    uids = uid.split(',')
    return uids


def process_heatmap_z(z_data, x=None, y=None):
    data_ready = []
    for key, value in z_data.items():
        s = re.search('z\[(.*)\]', key, re.IGNORECASE)
        if not s:
            return None, None, None
        index = s.group(1)
        data_ready.append((index, value))
    data_ready.sort(key = lambda val: val[0])
    processed_z = list(map(lambda v: v[1], data_ready))
    processed_x = x
    processed_y = y
    if len(processed_z) > 100:
        start = random.randint(0, len(processed_z) - 100)
        processed_z = processed_z[start: start + 100]
        if x:
            processed_x = processed_x[start: start + 100]
    if len(processed_z[0]) > 100:
        start = random.randint(0, len(processed_z[0]) - 100)
        processed_z = list(map(lambda column: column[start: start + 100], processed_z))
        if y:
            processed_y = processed_y[start: start + 100]
    return processed_z, processed_x, processed_y

def process_heatmap_col(col, uid_map, df):
    if 'zsrc' not in col.keys():
        return {"vis_type": None}
    z_scr_id, z_uid = get_uid(col['zsrc'])
    vis_type = "heatmap"
    name = "heatmp"
    if 'xsrc' in col.keys():
        z_data = {}
        zr_uids = split_uid(z_uid)
        x_scr_id, x_uid = get_uid(col['xsrc'])
        if x_uid not in uid_map[x_scr_id].keys():
            return {"vis_type": None}
        column_x = uid_map[x_scr_id][x_uid]
        x_data = list(df[column_x])
        if 'ysrc' not in col.keys():
            return {"vis_type": None}
        y_scr_id, y_uid = get_uid(col['ysrc'])
        column_y = uid_map[y_scr_id][y_uid]
        y_data = list(df[column_y])
        if x_uid in zr_uids:
            return {"vis_type": None}
        for zr_uid in zr_uids:
            column = uid_map[z_scr_id][zr_uid]
            column_data = list(df[column])
            z_data[column] = column_data

        z_data, x_data, y_data = process_heatmap_z(z_data, x_data, y_data)
        if not z_data:
            return {'vis_type': None}
        document = {
            'vis_type': vis_type,
            'name': name,
            'x': x_data,
            'y': y_data,
            'z': z_data,
            # 'col': col,
            'data_type': 'z-x-y',
            'inline': 'inline'
        }
    else:
        z_data = {}
        for column in df.columns:
            z_data[column] = list(df[column])
        z_data, _x, _y = process_heatmap_z(z_data)
        if not z_data:
            return {'vis_type': None}
        document = {
            'vis_type': vis_type,
            'name': name,
            'z': z_data,
            'data_type': 'z',
        }
    return document


def process_seq_col(col, uid_map, df):
    inline = False
    has_y = False
    has_x = False
    missing_x = False
    x_src = "xsrc"
    y_src = "ysrc"
    if 'x' in col.keys():
        inline = True
        if 'y' in col.keys():
            has_y = True
    else:
        if 'tsrc' in col.keys():
            x_src = 'tsrc'
            y_src = 'rsrc'
            if 'rsrc' in col.keys():
                has_y = True
        else:
            if 'xsrc' not in col.keys():
                missing_x = True
        if 'ysrc' in col.keys():
            has_y = True

    if inline:
        xsrc = 'inline'
        column_x = 'inline'
        x_data = col['x']
        pass
    elif missing_x:
        column_x = "missing"
        y_src_id, column_y_uid = get_uid(col[y_src])
        column_y = uid_map[y_src_id][column_y_uid]
        x_data = [i for i in range(len(list(df[column_y])))]
        xsrc = 'missing'
    else:
        x_src_id, column_x_uid = get_uid(col[x_src])
        column_x = uid_map[x_src_id][column_x_uid]
        xsrc = col[x_src]
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
        # 'col': col,
        'xsrc': xsrc,
        'data_type': 'x',
        'inline': 'inline'
    }
    if not has_y:
        print("not")
    if has_y:
        if inline:
            document['ysrc'] = 'inline'
            document['y'] = col['y'],
            document['column_y'] = 'inline',
            document['data_type'] = "y-x"
        else:
            y_src_id, column_y_uid = get_uid(col[y_src])
            column_y = uid_map[y_src_id][column_y_uid]
            document['ysrc'] = col[y_src]
            document['y'] = list(df[column_y]),
            document['column_y'] = column_y,
            document['data_type'] = "y-x"
    return clip_too_long(document)


def process_col(col, uid_map, df):
    vis_type = get_col_type(col)
    if vis_type == "pie":
        return process_pie_col(col, uid_map, df)
    elif vis_type == "heatmap":
        return process_heatmap_col(col, uid_map, df)
    else:
        return process_seq_col(col, uid_map, df)


def process_chart(table):
    vis_types = set()
    vis_style = "not_set"
    axises = {}
    vis_type = get_col_type(table['chart_data'][0])
    if vis_type == 'table' or vis_type == "box" or vis_type == "markers" or vis_type == "surface":
        return {}, {}, None
    if vis_type != 'bar' and vis_type != 'lines' and vis_type != 'line' and vis_type != 'heatmap' and vis_type != 'pie':
        return {}, {}, None
    if 'yaxis' not in table['chart_data'][0].keys():
        axises['y'] = list(range(len(table['chart_data'])))
    else:
        for i, col in enumerate(table['chart_data']):
            if col['yaxis'] in axises.keys():
                axises[col['yaxis']].append(i)
            else:
                axises[col['yaxis']] = [i]
    documents = []

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





tables = get_plotly_dfs()
line_count = 0
count = 0
types = []
client = MongoClient()
db = client['viznet']
collection = db.data
plots = db.plots
# for i, table in enumerate(tables):
#     print(i)
vis_types = set()
start = 5000
limit = 100000
for table in tables:
    try:
        if count < start:
            count += 1
            continue
        if count > start + limit:
            print("done: ", count)
            break
        plot, documents, table_types = process_chart(table)
        # collection.insert_many(tables)
        if not table_types:
            continue
        if len(table_types) > 1:
            print(table_types)
        vis_types = vis_types.union(table_types)
        collection.insert_many(documents)
        plots.insert(plot)
    except:
        print("error")


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
