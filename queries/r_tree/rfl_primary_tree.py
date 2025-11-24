"""
Summary:
    R_TREE
Attributes:
    RFL_SELECT_QUERIES : RFL_SELECT文
Author:
    Telema Tanaka
Created:
    2025-07-20
"""

# region SQL Queries
RFL_SELECT_QUERIES = {
    'get_primary_wps_from_hr1':"""
        WITH hr1 AS(
            SELECT
                wp.wp AS hr1_wp,
                rfl.requirement_s_id AS hr1_req,
                rfl.logic_s_id AS hr1_logic,
                prji.id AS criterion_pj
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
                prj_rfl AS prfl
            ON
                prfl.rfl_id = rfl.id
            INNER JOIN
                project_info AS prji
            ON
                prji.id = prfl.project_info_id
            WHERE
                wp.wp = %s
                AND prji.project_code = %s
                AND r.hierarchy_id = 1
        ),
        hr2 AS(
            SELECT
                hr1_wp,
                hr2_wp.wp AS hr2_wp,
                criterion_pj
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
                AND prj_rfl.project_info_id = criterion_pj
        )
        SELECT DISTINCT ON (hr2_wp)
            hr1_wp,
            hr2_wp,
            NULL AS hr3_wp
        FROM hr2;
    """,
    'get_primary_wps_from_hr2':"""
        WITH hr2 AS(
            SELECT
                wp.wp AS hr2_wp,
                rfl.requirement_s_id AS hr2_req,
                rfl.logic_s_id AS hr2_logic,
                prji.id AS criterion_pj
            FROM
                wp
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
                prj_rfl AS prfl
            ON
                prfl.rfl_id = rfl.id
            INNER JOIN
                project_info AS prji
            ON
                prji.id = prfl.project_info_id
            WHERE
                wp.wp in %s
                AND prji.project_code = %s
                AND r.hierarchy_id = 2
        ),hr3 AS(
            SELECT
                hr2_wp AS hr2_wp,
                hr2_req AS hr2_req,
                hr3_wp.wp AS hr3_wp,
                criterion_pj
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
                AND prj_rfl.project_info_id = criterion_pj
        ),hr1 AS(
            SELECT
                hr1_wp.wp AS hr1_wp,
                hr2_wp AS hr2_wp,
                hr3_wp AS hr3_wp,
                criterion_pj
            FROM
                hr3
            INNER JOIN
                l_r_relation AS hr1_lrr
            ON
                hr2_req = hr1_lrr.r_s_id
            INNER JOIN
                rfl AS hr1_rfl
            ON
                hr1_lrr.l_s_id = hr1_rfl.logic_s_id
            INNER JOIN
                setup_r_relation AS hr1_srr
            ON
                hr1_rfl.requirement_s_id  = hr1_srr.id
            INNER JOIN
                r_parameter AS hr1_r
            ON
                hr1_srr.r_parameter_id = hr1_r.id
            INNER JOIN
                WP AS hr1_wp
            ON
                hr1_wp.id = hr1_r.wp_id
            INNER JOIN
                prj_rfl
            ON
                hr1_rfl.id = prj_rfl.rfl_id
            WHERE
                hr1_r.hierarchy_id = 1
                AND prj_rfl.project_info_id = criterion_pj
            )
        SELECT
            DISTINCT ON (hr1_wp,hr2_wp,hr3_wp)
            hr1_wp,
            hr2_wp,
            hr3_wp
        FROM
            hr1;
    """,
    'get_primary_wps_from_hr3':"""
        WITH hr3 AS(
            SELECT
                wp.wp AS hr3_wp,
                rfl.requirement_s_id AS hr3_req,
                rfl.logic_s_id AS hr3_logic,
                prji.id AS criterion_pj
            FROM
                wp
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
                prj_rfl AS prfl
            ON
                prfl.rfl_id = rfl.id
            INNER JOIN
                project_info AS prji
            ON
                prji.id = prfl.project_info_id
            WHERE
                wp.wp = %s
                AND prji.project_code = %s
                AND r.hierarchy_id = 3
        ),hr2 AS(
            SELECT
                hr3_wp AS hr3_wp,
                hr3_req AS hr3_req,
                hr2_wp.wp AS hr2_wp,
                criterion_pj
            FROM
                hr3
            INNER JOIN
                l_r_relation AS hr2_lrr
            ON
                hr3_req = hr2_lrr.r_s_id
            INNER JOIN
                rfl AS hr2_rfl
            ON
                hr2_rfl.logic_s_id = hr2_lrr.l_s_id
            INNER JOIN
                setup_r_relation AS hr2_srr
            ON
                hr2_rfl.requirement_s_id = hr2_srr.id
            INNER JOIN
                r_parameter AS hr2_r
            ON
                hr2_srr.r_parameter_id = hr2_r.id
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
            AND prj_rfl.project_info_id = criterion_pj
            )
        SELECT
            DISTINCT ON (hr2_wp)
            NULL AS hr1_wp,
            hr2_wp,
            hr3_wp
        FROM
            hr2;
    """
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

