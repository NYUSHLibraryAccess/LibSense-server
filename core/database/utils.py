from core import schema
from core.database.model import *
from humps import decamelize


def compile_filters(query, filters, target_table):
    sql_filters = []
    for f in filters:
        if f.op == schema.FilterOperators.IN:
            if f.col == "tags":
                for t in f.val:
                    sql_filters.append(ExtraInfo.tags.like('%[' + t + ']%'))
            else:
                sql_filters.append(getattr(target_table, decamelize(f.col)).in_(f.val))

        elif f.op == schema.FilterOperators.LIKE:
            sql_filters.append(getattr(target_table, decamelize(f.col)).like('%' + f.val + '%'))

        elif f.op == schema.FilterOperators.BETWEEN:
            sql_filters.append(getattr(target_table, decamelize(f.col)).between(*f.val))

    for f in sql_filters:
        query = query.filter(f)

    return query


def compile_sorters(query, sorter, target_table, backup_sort_key=None):
    col = getattr(target_table, decamelize(sorter.col))
    if sorter.desc:
        col = col.desc()
        if backup_sort_key:
            backup_sort_key = backup_sort_key.desc()

    return query.order_by(col, backup_sort_key)


