"""
Summary:
    Select For RFLTreeView
Attributes:
    F_TREE : RFL_SELECT文
Author:
    Telema Tanaka
Created:
    2025-07-24
"""

# region SQL Queries
RFL_SELECT_QUERIES = {
    'get_secondary_function_from_hr1':"""
        WITH hr1 AS(
            SELECT
                wp.wp AS hr1_wp,
                rfl.requirement_s_id AS hr1_req,
                rfl.logic_s_id AS hr1_logic,
                hr1_f.design_item AS hr1_func,
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
            INNER JOIN
                f_parameter AS hr1_f
            ON
                hr1_f.id = rfl.function_id
            WHERE
                wp.wp = %s
                AND prji.project_code = %s
                AND r.hierarchy_id = 1
        ),
        hr2 AS(
            SELECT
                hr1_wp AS hr1_wp,
                hr2_wp.wp AS hr2_wp,
                hr2_rfl.logic_s_id AS hr2_logic,
                hr2_srr.id AS hr2_req,
                hr1_func,
                hr2_f.design_item AS hr2_func,
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
                f_parameter AS hr2_f
            ON
                hr2_f.id = hr2_rfl.function_id
            INNER JOIN
                prj_rfl
            ON
                prj_rfl.rfl_id = hr2_rfl.id
            WHERE
                hr2_r.hierarchy_id = 2
                AND prj_rfl.project_info_id = criterion_pj
        ),
        hr3 AS(
            SELECT
                hr1_wp AS hr1_wp,
                hr2_wp AS hr2_wp,
                hr3_wp.wp AS hr3_wp,
                hr2_req,
                hr2_logic,
                hr1_func,
                hr2_func,
                hr3_func.design_item AS hr3_func,
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
                hr3_rfl.requirement_s_id = hr3_srr.id
            INNER JOIN
                f_parameter AS hr3_func
            ON
                hr3_rfl.function_id = hr3_func.id
            INNER JOIN
                prj_rfl
            ON
                hr3_rfl.id = prj_rfl.rfl_id
            WHERE
                hr3_r.hierarchy_id = 3
                AND prj_rfl.project_info_id = criterion_pj
        ),
        hr1_2ry AS(
            SELECT
                hr1_wp,
                hr2_wp,
                hr3_wp,
                hr2_req,
                hr1_2ry_wp.wp AS hr1_2ry_wp,
                hr1_func,
                hr2_func,
                hr3_func,
                hr1_2ry_func.design_item AS hr1_2ry_func,
                criterion_pj
            FROM hr3

            INNER JOIN
                l_r_relation AS hr1_2ry_lrr
            ON
                hr2_req = hr1_2ry_lrr.r_s_id
            INNER JOIN
                setup_l_relation AS hr1_2ry_slr
            ON
                hr1_2ry_slr.id = hr1_2ry_lrr.l_s_id
            INNER JOIN
                rfl AS hr1_2ry_rfl
            ON
                 hr1_2ry_slr.id = hr1_2ry_rfl.logic_s_id
            INNER JOIN
                setup_r_relation AS hr1_2ry_srr
            ON
                hr1_2ry_rfl.requirement_s_id = hr1_2ry_srr.id
            INNER JOIN
                r_parameter AS hr1_2ry_r
            ON
                hr1_2ry_srr.r_parameter_id = hr1_2ry_r.id
            INNER JOIN
                wp AS hr1_2ry_wp
            ON
                hr1_2ry_r.wp_id = hr1_2ry_wp.id
            INNER JOIN
                f_parameter AS hr1_2ry_func
            ON
                hr1_2ry_rfl.function_id = hr1_2ry_func.id
            INNER JOIN
                prj_rfl
            ON
                hr1_2ry_rfl.id = prj_rfl.rfl_id
            WHERE
                hr1_2ry_r.hierarchy_id = 1
                AND prj_rfl.project_info_id = criterion_pj
        )SELECT DISTINCT ON (
            hr1_func,
            hr2_func,
            hr3_func,
            hr1_2ry_func
            )
            hr1_wp,
            hr2_wp,
            hr3_wp,
            hr1_2ry_wp,
            hr1_func,
            hr2_func,
            hr3_func,
            hr1_2ry_func
        FROM
            hr1_2ry
    """,
    'get_secondary_function_from_hr2':"""
        WITH hr2 AS(
        SELECT
            wp.wp AS hr2_wp,
            rfl.requirement_s_id AS hr2_req,
            rfl.logic_s_id AS hr2_logic,
            hr2_func.design_item AS hr2_func,
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
        INNER JOIN
            f_parameter AS hr2_func
        ON
            rfl.function_id = hr2_func.id
        WHERE
            wp.wp = %s
            AND prji.project_code = %s
            AND r.hierarchy_id = 2
        ),hr1 AS(
        SELECT
            hr1_wp.wp AS hr1_wp,
            hr1_rfl.requirement_s_id AS hr1_req,
            hr1_rfl.logic_s_id AS hr1_logic,
            hr1_lrr.l_s_id AS hr1_l_s_id,
            hr2_req,
            hr2_logic,
            hr2_wp,
            hr1_func.design_item AS hr1_func,
            hr2_func,
            criterion_pj
        FROM
            hr2
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
            wp AS hr1_wp
        ON
            hr1_wp.id = hr1_r.wp_id
        INNER JOIN
            f_parameter AS hr1_func
        ON
            hr1_rfl.function_id = hr1_func.id
        INNER JOIN
            prj_rfl
        ON
            hr1_rfl.id = prj_rfl.rfl_id
        WHERE
            hr1_r.hierarchy_id = 1
            AND prj_rfl.project_info_id = criterion_pj
        ),hr3 AS(
        SELECT
            hr3_lrr.l_s_id AS hr3_l_s_id,
            hr1_logic,
            hr2_logic,
            hr2_req,
            hr3_srr.id AS hr3_req,
            hr1_wp,
            hr2_wp,
            hr3_wp.wp AS hr3_wp,
            hr1_func,
            hr2_func,
            hr3_func.design_item AS hr3_func,
            criterion_pj
        FROM
            hr1
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
            hr3_wp.id = hr3_r.wp_id
        INNER JOIN
            rfl AS hr3_rfl
        ON
            hr3_srr.id = hr3_rfl.requirement_s_id
        INNER JOIN
            f_parameter AS hr3_func
        ON
            hr3_rfl.function_id = hr3_func.id
        INNER JOIN
            prj_rfl
        ON
            hr3_rfl.id = prj_rfl.rfl_id
        WHERE
            hr3_r.hierarchy_id = 3
            AND prj_rfl.project_info_id = criterion_pj
        ),hr2_2ry_from_hr3 AS(
        SELECT
            hr3_l_s_id,
            hr1_logic,
            hr2_logic,
            hr2_req,
            hr3_req,
            hr1_wp,
            hr2_wp,
            hr3_wp,
            hr2_2ry_wp.wp AS hr2_2ry_wp_from_hr3,
            hr1_func,
            hr2_func,
            hr3_func,
            hr2_2ry_func.design_item AS hr2_2ry_from_hr3_func,
            criterion_pj
        FROM
            hr3
        INNER JOIN
            l_r_relation AS hr2_2ry_lrr
        ON
            hr3_req = hr2_2ry_lrr.r_s_id
        INNER JOIN
            setup_l_relation AS hr2_2ry_slr
        ON
            hr2_2ry_lrr.l_s_id = hr2_2ry_slr.id
        INNER JOIN
            rfl AS hr2_2ry_rfl
        ON
            hr2_2ry_slr.id = hr2_2ry_rfl.logic_s_id
        INNER JOIN
            setup_r_relation AS hr2_2ry_srr
        ON
            hr2_2ry_srr.id = hr2_2ry_rfl.requirement_s_id
        INNER JOIN
            r_parameter AS hr2_2ry_r
        ON
            hr2_2ry_srr.r_parameter_id = hr2_2ry_r.id
        INNER JOIN
            wp AS hr2_2ry_wp
        ON
            hr2_2ry_r.wp_id = hr2_2ry_wp.id
        INNER JOIN
            f_parameter AS hr2_2ry_func
        ON
            hr2_2ry_rfl.function_id = hr2_2ry_func.id
        INNER JOIN
            prj_rfl
        ON
            hr2_2ry_rfl.id = prj_rfl.rfl_id
        WHERE
            hr2_2ry_r.hierarchy_id = 2
            AND prj_rfl.project_info_id = criterion_pj
        ),hr2_2ry_from_hr1 AS(
        SELECT
            hr3_l_s_id,
            hr1_logic,
            hr2_logic,
            hr3_req,
            hr1_wp,
            hr2_wp,
            hr3_wp,
            hr2_2ry_wp_from_hr3,
            hr2_2ry_wp_from_hr1.wp AS hr2_2ry_wp_from_hr1,
            hr1_func,
            hr2_func,
            hr3_func,
            hr2_2ry_from_hr3_func,
            hr2_2ry_func.design_item AS hr2_2ry_from_hr1_func,
            criterion_pj
        FROM
            hr2_2ry_from_hr3
        INNER JOIN
            l_r_relation AS hr2_2ry_lrr
        ON
            hr1_logic = hr2_2ry_lrr.l_s_id
        INNER JOIN
            setup_r_relation AS hr2_2ry_srr
        ON
            hr2_2ry_lrr.r_s_id = hr2_2ry_srr.id
        INNER JOIN
            r_parameter AS hr2_2ry_r
        ON
            hr2_2ry_srr.r_parameter_id = hr2_2ry_r.id
        INNER JOIN
            wp AS hr2_2ry_wp_from_hr1
        ON
            hr2_2ry_r.wp_id = hr2_2ry_wp_from_hr1.id
        INNER JOIN
            rfl AS hr2_2ry_rfl
        ON
            hr2_2ry_srr.id = hr2_2ry_rfl.requirement_s_id
        INNER JOIN
            f_parameter AS hr2_2ry_func
        ON
            hr2_2ry_rfl.function_id = hr2_2ry_func.id
        INNER JOIN
            prj_rfl
        ON
            hr2_2ry_rfl.id = prj_rfl.rfl_id
        WHERE
            hr2_2ry_r.hierarchy_id = 2
            AND prj_rfl.project_info_id = criterion_pj
        )
        SELECT DISTINCT ON (
                hr1_func,
                hr2_func,
                hr2_2ry_from_hr1_func,
                hr2_2ry_from_hr3_func,
                hr3_func
            )
            hr1_wp,
            hr2_2ry_wp_from_hr1,
            hr2_2ry_wp_from_hr3,
            hr3_wp,
            hr1_func,
            hr2_2ry_from_hr1_func,
            hr2_2ry_from_hr3_func,
            hr3_func
        FROM hr2_2ry_from_hr1;
    """,
    'get_secondary_function_from_hr3':"""
        WITH hr3 AS(
            SELECT
                wp.wp AS hr3_wp,
                hr3_lrr.r_s_id AS hr3_req,
                hr3_func.design_item AS hr3_func,
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
                l_r_relation as hr3_lrr
            ON
                srr.id = hr3_lrr.r_s_id
            INNER JOIN
                rfl
            ON
                rfl.requirement_s_id = hr3_lrr.r_s_id
            INNER JOIN
                prj_rfl AS prfl
            ON
                prfl.rfl_id = rfl.id
            INNER JOIN
                project_info AS prji
            ON
                prji.id = prfl.project_info_id
            INNER JOIN
                f_parameter AS hr3_func
            ON
                rfl.function_id = hr3_func.id
            WHERE
                wp.wp = %s
                AND prji.project_code = %s
                AND r.hierarchy_id = 3
        ),
        hr2 AS(
            SELECT
                hr2_wp.wp AS hr2_wp,
                hr2_rfl.requirement_s_id AS hr2_req,
                hr2_rfl.logic_s_id AS hr2_logic,
                hr3_wp,
                hr2_func.design_item AS hr2_func,
                hr3_func,
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
                hr2_lrr.l_s_id  = hr2_rfl.logic_s_id
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
                f_parameter hr2_func
            ON
                hr2_rfl.function_id = hr2_func.id
            INNER JOIN
                prj_rfl
            ON
                hr2_rfl.id = prj_rfl.rfl_id
            WHERE
                hr2_r.hierarchy_id = 2
                AND prj_rfl.project_info_id = criterion_pj

        ),hr1 AS(
            SELECT
                hr1_wp.wp AS hr1_wp,
                hr2_req,
                hr2_logic,
                hr2_wp,
                hr3_wp,
                hr1_func.design_item AS hr1_func,
                hr2_func,
                hr3_func,
                criterion_pj
            FROM
                hr2
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
                f_parameter AS hr1_func
            ON
                hr1_rfl.function_id = hr1_func.id
            INNER JOIN
                prj_rfl
            ON
                hr1_rfl.id = prj_rfl.rfl_id
            WHERE
                hr1_r.hierarchy_id = 1
                AND prj_rfl.project_info_id = criterion_pj
        ),hr3_2ry AS(
            SELECT
                hr1_wp,
                hr2_logic,
                hr2_wp,
                hr3_2ry_wp.wp AS hr3_2ry_wp,
                hr3_wp,
                hr1_func,
                hr2_func,
                hr3_func,
                hr3_2ry_func.design_item AS hr3_2ry_func,
                criterion_pj
            FROM
                hr1
            INNER JOIN
                l_r_relation AS hr3_2ry_lrr
            ON
                hr2_logic = hr3_2ry_lrr.l_s_id
            INNER JOIN
                setup_r_relation AS hr3_2ry_srr
            ON
                hr3_2ry_lrr.r_s_id  = hr3_2ry_srr.id
            INNER JOIN
                r_parameter AS hr3_2ry_r
            ON
                hr3_2ry_srr.r_parameter_id = hr3_2ry_r.id
            INNER JOIN
                wp AS hr3_2ry_wp
            ON
                hr3_2ry_r.wp_id = hr3_2ry_wp.id
            INNER JOIN
                rfl AS hr3_2ry_rfl
            ON
                hr3_2ry_srr.id = hr3_2ry_rfl.requirement_s_id
            INNER JOIN
                f_parameter AS hr3_2ry_func
            ON
                hr3_2ry_rfl.function_id = hr3_2ry_func.id
            INNER JOIN
                prj_rfl
            ON
                hr3_2ry_rfl.id = prj_rfl.rfl_id
            WHERE
                hr3_2ry_r.hierarchy_id = 3
                AND prj_rfl.project_info_id = criterion_pj
        )
        SELECT DISTINCT ON (
                hr1_func,
                hr2_func,
                hr3_func,
                hr3_2ry_func
            )
            hr1_wp,
            hr2_wp,
            hr3_wp,
            hr3_2ry_wp,
            hr1_func,
            hr2_func,
            hr3_func,
            hr3_2ry_func
        FROM
            hr3_2ry;
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

