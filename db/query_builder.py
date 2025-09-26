class QueryBuilder:

    @staticmethod
    def build_where_clause(params_len=None, use_in=False):

        if use_in:
            placeholders = ', '.join(['%s'] * params_len)
            where_clause = f"IN ({placeholders})"
        else:
            where_clause = f"= %s"

        return where_clause

    @staticmethod
    def generate_query(query,params_len=None, use_in=False):
        where_clause = QueryBuilder.build_where_clause(params_len, use_in)
        query = query.format(where_clause)
        return query