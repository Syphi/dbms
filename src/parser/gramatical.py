from lark import Lark, Transformer, LarkError
from src.parser import ast_schema as schema


sql_grammar = r"""
?start: create_table_stmt ";" | insert_stmt ";" | select_stmt ";"

// ---------- CREATE TABLE ----------
create_table_stmt: "CREATE" "TABLE" table_name "(" column_def_list ")"
table_name: CNAME
column_def_list: column_def ("," column_def)*
column_def: column_name type_name
column_name: CNAME
type_name: TYPE_INT | TYPE_TEXT

// ---------- INSERT ----------
insert_stmt: "INSERT" "INTO" table_name "(" column_list ")" "VALUES" "(" value_list ")"
column_list: column_name ("," column_name)*
value_list: value ("," value)*
?value: INT -> int_value | STRING -> string_value

// ---------- SELECT ----------
select_stmt: "SELECT" select_list "FROM" table_name where_clause? limit_clause?
?select_list: "*" -> select_all | select_items
select_items: column_name ("," column_name)*
where_clause: "WHERE" condition
?condition: or_expr
?or_expr: and_expr | or_expr "OR" and_expr -> or_op
?and_expr: comparison | and_expr "AND" comparison -> and_op
?comparison: operand comparator operand
operand: column_name | value
comparator: COMP_EQ | COMP_NEQ | COMP_LT | COMP_LTE | COMP_GT | COMP_GTE
limit_clause: "LIMIT" INT

TYPE_INT: "INT"
TYPE_TEXT: "TEXT"

COMP_EQ: "="
COMP_NEQ: "!="
COMP_LT: "<"
COMP_LTE: "<="
COMP_GT: ">"
COMP_GTE: ">="

STRING: /'[^']*'/

%import common.CNAME
%import common.INT
%import common.WS
%ignore WS
"""


class SQLTransformer(Transformer):
    def create_table_stmt(self, items):
        table_name = items[0]
        columns = items[1]
        return schema.CreateTableExp(table_name=table_name, table_columns=columns)

    def table_name(self, items):
        return str(items[0])

    def column_def_list(self, items):
        return list(items)

    def column_def(self, items):
        name = items[0]
        type_token = items[1]

        dtype = schema.DataTypes.INT
        if type_token.type == "TYPE_TEXT":
            dtype = schema.DataTypes.STR

        return schema.CreateTableColumExp(
            column_name=name, column_type=dtype, column_default_value=None
        )

    def column_name(self, items):
        return str(items[0])

    def type_name(self, items):
        return items[0]

    # ---------- INSERT ----------
    def insert_stmt(self, items):
        table_name = items[0]
        columns = items[1]
        values = items[2]

        if len(columns) != len(values):
            raise ValueError(
                f"Column count {len(columns)} does not match value count {len(values)}"
            )

        values_map = []
        for i, col in enumerate(columns):
            values_map.append(
                schema.InsertValueExp(column_name=col, column_value=values[i])
            )

        return schema.InsertExp(table_name=table_name, values_map=values_map)

    def column_list(self, items):
        return list(items)

    def value_list(self, items):
        return list(items)

    def int_value(self, items):
        return int(items[0])

    def string_value(self, items):
        # Remove single quotes
        return str(items[0])[1:-1]

    # ---------- SELECT ----------
    def select_stmt(self, items):
        select_items_list = items[0]
        table_name = items[1]

        where_condition = None
        limit = None

        # Check remaining items for where_clause and limit_clause
        idx = 2
        if idx < len(items) and isinstance(items[idx], schema.SelectWhereExp):
            where_condition = items[idx]
            idx += 1

        if idx < len(items) and isinstance(items[idx], int):  # limit returns int
            limit = items[idx]

        return schema.SelectExp(
            column_names=select_items_list,
            table_name=table_name,
            where_conditions=where_condition,
            limit=limit,
        )

    def select_all(self, items):
        return ["*"]

    def select_items(self, items):
        return list(items)

    def where_clause(self, items):
        return items[0]

    def or_op(self, items):
        left = items[0]
        right = items[1]

        # Traverse to the end of left's linked list
        current = left
        while current.next is not None:
            current = current.next

        current.next_value = schema.Choose.OR
        current.next = right
        return left

    def and_op(self, items):
        left = items[0]
        right = items[1]

        # Traverse to the end of left's linked list
        current = left
        while current.next is not None:
            current = current.next

        current.next_value = schema.Choose.AND
        current.next = right
        return left

    def comparison(self, items):
        col_name = items[0]
        op_token = items[1]
        val = items[2]

        op_map = {
            "COMP_EQ": schema.Comparator.EQUAL,
            "COMP_NEQ": schema.Comparator.NOT_EQUAL,
            "COMP_LT": schema.Comparator.LEFT_MORE,
            "COMP_LTE": schema.Comparator.LEFT_MORE_EQUAL,
            "COMP_GT": schema.Comparator.RIGHT_MORE,
            "COMP_GTE": schema.Comparator.RIGHT_MORE_EQUAL,
        }

        return schema.SelectWhereExp(
            column_name=str(col_name),
            compare=op_map[op_token.type],
            value=val,
            next=None,
            next_value=None,
        )

    def operand(self, items):
        return items[0]

    def comparator(self, items):
        return items[0]

    def limit_clause(self, items):
        return int(items[0])


_parser = Lark(sql_grammar, start="start", parser="lalr")


def parse_sql(sql_query: str) -> schema.ParserResponse:
    try:
        tree = _parser.parse(sql_query)
        return schema.ParserResponse(
            error=None, result=SQLTransformer().transform(tree)
        )
    except (LarkError, Exception) as e:
        return schema.ParserResponse(error=schema.ParseError(msg=str(e)), result=None)
