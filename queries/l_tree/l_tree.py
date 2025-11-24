"""
Summary:
    L-TREE
Attributes:
    RFL_SELECT_QUERIES : RFL_SELECT文
Author:
    Telema Tanaka
Created:
    2025-07-25
"""

# region SQL Queries
RFL_SELECT_QUERIES = {
    'get_l_tree_in_pj':"""
        WITH hr1 AS(
            SELECT
                wp.wp AS hr1_wp,
                rfl.requirement_s_id AS hr1_req,
                rfl.logic_s_id AS hr1_logic,
                prj_rfl.project_info_id AS pj_id
            FROM wp
            INNER JOIN
                r_parameter AS r
            ON
                wp.id = r.wp_id
            INNER JOIN
                setup_r_relation AS srr
            ON
                r.id = srr.r_parameter_id
            INNER JOIN
                rfl
            ON
                srr.id = rfl.requirement_s_id
            INNER JOIN
                prj_rfl
            ON
                rfl.id = prj_rfl.rfl_id
            INNER JOIN
                project_info AS pi
            ON
                prj_rfl.project_info_id = pi.id
            WHERE
                pi.project_code = %s
                AND r.hierarchy_id = 1
        ),
        hr2 AS(
            SELECT
                hr1_wp AS hr1_wp,
                hr2_wp.wp AS hr2_wp,
                hr2_rfl.logic_s_id AS hr2_logic,
                pj_id
            FROM
                hr1
            INNER JOIN
                l_r_relation AS hr2_lrr
            ON
                hr1_logic = hr2_lrr.l_s_id
            INNER JOIN
                setup_r_relation AS hr2_srr
            ON
                hr2_lrr.r_s_id  = hr2_srr.id
            INNER JOIN
                r_parameter AS hr2_r
            ON
                hr2_srr.r_parameter_id = hr2_r.id
            INNER JOIN
                rfl AS hr2_rfl
            ON
                hr2_lrr.r_s_id = hr2_rfl.requirement_s_id
            INNER JOIN
                wp AS hr2_wp
            ON
                hr2_r.wp_id = hr2_wp.id
            INNER JOIN
                prj_rfl
            ON
                hr2_rfl.id = prj_rfl.rfl_id
            WHERE
                hr2_r.hierarchy_id = 2
                AND prj_rfl.project_info_id = pj_id
        ),
        hr3 AS(
            SELECT DISTINCT ON (hr1_wp,hr2_wp,hr3_wp)
                hr1_wp AS hr1_wp,
                hr2_wp AS hr2_wp,
                hr3_wp.wp AS hr3_wp,
                pj_id
            FROM
                hr2
            INNER JOIN
                l_r_relation AS hr3_lrr
            ON
                hr2_logic = hr3_lrr.l_s_id
            INNER JOIN
                setup_r_relation AS hr3_srr
            ON
                hr3_lrr.r_s_id  = hr3_srr.id
            INNER JOIN
                r_parameter AS hr3_r
            ON
                hr3_srr.r_parameter_id = hr3_r.id
            INNER JOIN
                wp AS hr3_wp
            ON
                hr3_r.wp_id = hr3_wp.id
            INNER JOIN
                rfl AS hr3_rfl
            ON
                hr3_srr.id = hr3_rfl.requirement_s_id
            INNER JOIN
                prj_rfl
            ON
                hr3_rfl.id = prj_rfl.rfl_id
            WHERE
                hr3_r.hierarchy_id = 3
                AND prj_rfl.project_info_id = pj_id
        )
        SELECT
            hr1_wp,
            hr2_wp,
            hr3_wp
        FROM hr3;
    """,
}
# endregion

def get_select_query(query):
    """SELECT文取得

    Args:
        query (string): QUERY(key)を指定

    Returns:
        _type_: string(QUERY)
    """
    return RFL_SELECT_QUERIES[query]