from humps import decamelize
from sqlalchemy import and_, or_

from core import schema
from core.database.database import Base
from core.database.model import MAPPING, Order

# All columns that supports fuzzy search box in front-end
FUZZY_COLS = [Order.barcode, Order.bsn, Order.library_note, Order.title, Order.order_number]


def compile_filters(query, filters, table_mapping):
    """
    Combine all the filters from the user request.
    :param query: The SQLAlchemy Query object.
    :param filters: The filters from user request
    :param table_mapping: The table-to-column name mapping
    :return: SQLAlchemy Query Object with the filters added.
    """
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
                    and_flags.append(target_table.tags.like("%[" + t + "]%"))
                sql_filters.append(and_(*and_flags))
            else:
                in_filters = [getattr(target_table, decamelize(f.col)).in_(f.val)]
                if None in f.val:
                    in_filters.append((getattr(target_table, decamelize(f.col)) == None))
                    sql_filters.append(or_(*in_filters))
                else:
                    sql_filters.append(*in_filters)

        elif f.op == schema.FilterOperators.LIKE:
            if f.val is None:
                sql_filters.append(getattr(target_table, decamelize(f.col)) == None)
            else:
                sql_filters.append(getattr(target_table, decamelize(f.col)).like("%" + f.val + "%"))

        elif f.op == schema.FilterOperators.BETWEEN:
            sql_filters.append(getattr(target_table, decamelize(f.col)).between(*f.val))

    for f in sql_filters:
        query = query.filter(f)

    return query


def compile_sorters(query, sorter, table_mapping, backup_sort_key=None):
    """
    Combine the query with sorter options from user request.
    :param query: SQLAlchemy Query Object.
    :param sorter: Sorter from user request.
    :param table_mapping: The table-to-column mapping.
    :param backup_sort_key: Backup key in case of draw.
    :return: SQLAlchemy Query Object with sorting added.
    """
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
    """
    Compile the search for fuzzy searching feature.
    :param query: SQLAlchemy Query Object.
    :param fuzzy: The fuzzy search content.
    :param fuzzy_cols: The columns that supports fuzzy_search.
    :return: SQLAlchemy Query Object, with fuzzy search added.
    """
    fuzzy_filters = []
    for col in fuzzy_cols:
        fuzzy_filters.append(col.like("%" + fuzzy + "%"))
    query = query.filter(or_(*fuzzy_filters))
    return query


def compile_query(
    query,
    filters=None,
    table_mapping=None,
    sorter=None,
    default_key=None,
    start_idx=None,
    limit=None,
    suffix=None,
    fuzzy=None,
    fuzzy_cols=None,
):
    """
    Combine all the query params and return the result.
    :param query: Original SQLAlchemy Query Object.
    :param filters: The filters from user input.
    :param table_mapping: The table-column mapping.
    :param sorter: The sorters from user input.
    :param default_key: Default key in sorting in case of draw.
    :param start_idx: Pagination: Start query from this index.
    :param limit: Pagination: The number of records to be returned.
    :param suffix: Any RAW SQL suffix for the query.
    :param fuzzy: Fuzzy search contents.
    :param fuzzy_cols: Fuzzy search target columns.
    :return: Query result.
    """
    if fuzzy_cols is None:
        fuzzy_cols = FUZZY_COLS
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


def convert_sqlalchemy_objs_to_dict(*args):
    """
    Convert SQLAlchemy Query Result to native Python Dicts.
    """
    d = {}
    for i in args:
        if isinstance(i, Base):
            d.update(i.__dict__)
    return d
