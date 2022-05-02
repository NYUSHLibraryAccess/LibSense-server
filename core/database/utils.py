from core import schema
from core.database.model import MAPPING
from humps import decamelize
from sqlalchemy import or_


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
                or_flags = []
                for t in f.val:
                    or_flags.append(target_table.tags.like('%[' + t + ']%'))
                sql_filters.append(or_(*or_flags))
            else:
                sql_filters.append(getattr(target_table, decamelize(f.col)).in_(f.val))

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


def compile(query, filters, table_mapping, sorter, default_key, start_idx, limit):
    if filters:
        query = compile_filters(query, filters, table_mapping)
    if sorter:
        query = compile_sorters(query, sorter, table_mapping, default_key)
    if start_idx:
        query = query.offset(start_idx * limit)
    total_records = query.count()
    if limit:
        query = query.limit(limit)
    return query, total_records


