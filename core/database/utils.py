from core import schema
from core.database.model import MAPPING
from humps import decamelize
from sqlalchemy import and_, or_


def compile_filters(query, filters, table_mapping):
    sql_filters = []
    for f in filters:
        target_table = None
        for table_name, columns in table_mapping.items():
            if decamelize(f.col) in columns:
                target_table = MAPPING[table_name]
        target_table = MAPPING[table_mapping["default"]] if target_table is None else target_table
        if f.op == schema.FilterOperators.IN:
            if f.col == "tags":
                and_flags = []
                for t in f.val:
                    and_flags.append(target_table.tags.like('%[' + t + ']%'))
                sql_filters.append(and_(*and_flags))
            else:
                in_filters = [getattr(target_table, decamelize(f.col)).in_(f.val)]
                if None in f.val:
                    in_filters.append((getattr(target_table, decamelize(f.col)) == None))
                    sql_filters.append(and_(*in_filters))
                else:
                    sql_filters.append(*in_filters)
                
        elif f.op == schema.FilterOperators.LIKE:
            sql_filters.append(getattr(target_table, decamelize(f.col)).like('%' + f.val + '%'))

        elif f.op == schema.FilterOperators.BETWEEN:
            sql_filters.append(getattr(target_table, decamelize(f.col)).between(*f.val))

    for f in sql_filters:
        query = query.filter(f)

    return query


def compile_sorters(query, sorter, table_mapping, backup_sort_key=None):
    target_table = None
    for table_name, columns in table_mapping.items():
        if decamelize(sorter.col) in columns:
            target_table = MAPPING[table_name]
    target_table = MAPPING[table_mapping["default"]] if target_table is None else target_table
    col = getattr(target_table, decamelize(sorter.col))
    if sorter.desc:
        col = col.desc()
        if backup_sort_key:
            backup_sort_key = backup_sort_key.desc()

    return query.order_by(col, backup_sort_key)


def compile_fuzzy(query, fuzzy, fuzzy_cols):
    fuzzy_filters = []
    for col in fuzzy_cols:
        fuzzy_filters.append(col.like('%' + fuzzy + '%'))
    query = query.filter(or_(*fuzzy_filters))
    return query

def compile(query, filters=None, table_mapping=None, sorter=None, default_key=None, start_idx=None, limit=None, suffix=None, fuzzy=None, fuzzy_cols=None):
    if filters and table_mapping:
        query = compile_filters(query, filters, table_mapping)
    if fuzzy and fuzzy_cols:
        query = compile_fuzzy(query, fuzzy, fuzzy_cols)
    if sorter and table_mapping:
        query = compile_sorters(query, sorter, table_mapping, default_key)
    if suffix is not None:
        query = query.filter(suffix)
    if start_idx:
        query = query.offset(start_idx * limit)
    total_records = query.count()
    if limit and limit != -1:
        query = query.limit(limit)
    return query, total_records


