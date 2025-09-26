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
        """
}
# endregion

def get_update_query(query):
    return RFL_PJ_UPDATE_QUERIES[query]