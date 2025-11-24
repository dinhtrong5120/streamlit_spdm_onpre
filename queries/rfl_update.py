# region SQL Queries
RFL_PJ_UPDATE_QUERIES = {
    'update_edited_prj_rfl':
        """
            UPDATE
                prj_rfl
            SET
                {0} = %s
            WHERE
                project_info_id = %s
            AND
                rfl_id = %s
            AND
                phase_id = %s
        """,
    'bulk_update_edited_prj_rfl': #telema-kyaw rfl_update 8/22
        """
            WITH bulk_table AS(
                SELECT
                    *
                FROM
                    prj_rfl
                INNER JOIN
                    rfl
                ON
                    prj_rfl.rfl_id = rfl.id
                WHERE
                    rfl.{0} = %s
            )
            UPDATE
                prj_rfl
            SET
                {1} = %s
            FROM
                bulk_table
            WHERE prj_rfl.rfl_id = bulk_table.rfl_id;
        """
}
# endregion

def get_update_query(query):
    return RFL_PJ_UPDATE_QUERIES[query]