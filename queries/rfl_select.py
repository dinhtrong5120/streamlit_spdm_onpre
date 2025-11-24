"""
Summary:
    RFL機能SELECT文外だしファイル
Attributes:
    RFL_SELECT_QUERIES : RFL_SELECT文
Author:
    Telema Tanaka
Created:
    2025-03-25
"""

# region SQL Queries
RFL_SELECT_QUERIES = {
    'get_rfl_view_tlm':"""
        WITH pj AS(
            SELECT
                pjf.id AS project_id,
                pjf.project_code AS project_code,
                lt.lot AS lot,
                archi.architecturename AS architecture_name,
                dest.destination AS destination, --#10/20 #Kyaw added
                dt.drivetrain AS drivetrain --#10/20 #Kyaw added
            FROM
                project_info AS pjf
                JOIN setup AS stp ON pjf.setup_id = stp.id
                JOIN architecture AS archi on stp.architecture_id = archi.id
                JOIN destination AS dest ON dest.id = stp.destination_id
                JOIN drivetrain AS dt ON stp.drivetrain_id = dt.id
                JOIN lot AS lt ON pjf.lot_id = lt.id
                WHERE pjf.project_code IN (%s)
                AND dest.destination IN (%s)
                AND dt.drivetrain IN (%s)
                AND lt.lot IN (%s)
        ),rfl_tbl AS(
            SELECT
                rfl_view_tlm.pj_id as {0}r_pj_id,
                rfl_view_tlm.rfl_id as {0}rfl_id,
                rfl_view_tlm.phase_id as {0}phase_id,
                phase.phase as {0}phase,
                rfl_view_tlm.r_wp as {0}r_wp,
                rfl_view_tlm.flag_to as {0}flag_to,
                rfl_view_tlm.to_solving_value as {0}to_solving_value,
                rfl_view_tlm.flag_display_on_summary_logic as {0}flag_display_on_summary_logic,
                rfl_view_tlm.r_wp_id as {0}r_wp_id,
                rfl_view_tlm.l_wp as {0}l_wp,
                r_s_id as {0}r_s_id,
                l_s_id as {0}l_s_id,
                r_item as {0}r_item,
                r_item_2 as {0}r_item_2,
                prfl_r as {0}req,
                r_unit as {0}r_unit,
                r_uc as {0}r_scene,
                f_id as {0}f_id,
                ddt.user_memo as {0}user_memo,
                f_item as {0}f_item,
                prfl_f as {0}func,
                f_unit as {0}f_unit,
                l_item as {0}l_item,
                prfl_l as {0}logic,
                l_unit as {0}l_unit,
                l_r_s_p_i as c_related_se_parameter_id,
                l_uc as {0}l_scene,
                prfl_note as {0}note,
                rfl_view_tlm.r_wp as wp,
                pj.project_code as project_code,
                pj.lot as lot,
                pj.architecture_name as archi,
                rfl_view_tlm.phase as phase,
                rfl_view_tlm.hierarchy as hierarchy,
                rfl_view_tlm.n_wp as {0}n_wp,                
                allocation as {0}allocation,
                sender_judge as {0}sender_judge,
                sender_name as {0}sender_name,
                DATE(sender_date) as {0}sender_date,
                sender_comment as {0}sender_comment,
                receiver_judge as {0}receiver_judge,
                receiver_name as {0}receiver_name,
                DATE(receiver_date) as {0}receiver_date,
                receiver_comment as {0}receiver_comment,
                rfl_view_tlm.index as {0}index,
                rfl_view_tlm.log_condition as {0}log_condition,
                rfl_view_tlm.rfl_id as rfl_id,
                rfl_view_tlm.phase_id as ph_id,
                pj.destination, --#10/20 #Kyaw added
                pj.drivetrain --#10/20 #Kyaw added

            FROM
                rfl_view_tlm
            INNER JOIN
                pj
            ON
                rfl_view_tlm.pj_id = pj.project_id
            INNER JOIN
                phase
            ON
                phase_id = phase.id
            FULL OUTER JOIN(
                SELECT DISTINCT ON (project_id, phase_id, rfl_id) *
                FROM detail_data_to
                ORDER BY project_id, phase_id, rfl_id, update_day DESC
            ) AS ddt
            ON
                rfl_view_tlm.pj_id = ddt.project_id
                AND rfl_view_tlm.rfl_id = ddt.rfl_id
                AND rfl_view_tlm.phase_id = ddt.phase_id
            WHERE
                phase.phase in (%s)
                and rfl_view_tlm.hierarchy in  (%s)
                and rfl_view_tlm.r_wp in (%s)
            )
            SELECT
                rfl_tbl.*
            FROM  rfl_tbl

            ORDER BY rfl_tbl.{0}r_wp_id;
    """,
    'get_hierarchy':"""
        SELECT DISTINCT hierarchy
        FROM
            rfl_view_tlm
        WHERE
            pj_code IN (%s)
            AND phase IN (%s);
    """,
    'get_r_wp':"""
        SELECT DISTINCT r_wp
        FROM
            rfl_view_tlm
        WHERE
            pj_code IN (%s)
            AND phase IN (%s)
            AND hierarchy IN (%s);
    """,
    'get_prj_rfl':"""
        WITH pj AS(
            SELECT
                pjf.id AS project_id,
                pjf.project_code AS project_code,
                lt.lot AS lot,
                archi.architecturename AS architecture_name
            FROM
                project_info AS pjf
                JOIN setup AS stp ON pjf.setup_id = stp.id
                JOIN architecture AS archi on stp.architecture_id = archi.id
                JOIN destination AS dest ON dest.id = stp.destination_id
                JOIN drivetrain AS dt ON stp.drivetrain_id = dt.id
                JOIN lot AS lt ON pjf.lot_id = lt.id
                WHERE pjf.project_code IN (%s)
                AND dest.destination IN (%s)
                AND dt.drivetrain IN (%s)
                AND lt.lot IN (%s)
        ),rfl_table AS(
            SELECT
                rfl_view_tlm.pj_id as {0}r_pj_id,
                rfl_view_tlm.rfl_id as rfl_id,
                rfl_view_tlm.ph_id as ph_id,
                r_s_id as {0}r_s_id,
                r_item as {0}r_item,
                prfl_r as {0}requirement,
                r_unit as {0}r_unit,
                r_uc   as {0}r_scene,
                f_item as {0}f_item,
                prfl_f as {0}function,
                f_unit as {0}f_unit,
                l_item as {0}l_item,
                prfl_l as {0}logic,
                l_unit as {0}l_unit,
                l_uc as {0}l_scene,
                prfl_note as {0}note,
                rfl_view_tlm.r_wp as wp,
                pj.project_code as project_code,
                pj.lot as lot,
                pj.architecture_name as archi,
                rfl_view_tlm.phase as phase,
                rfl_view_tlm.hierarchy as hierarchy,
                rfl_view_tlm.n_wp as {0}n_wp
            FROM
                rfl_view_tlm
            INNER JOIN
                pj
            ON
                rfl_view_tlm.pj_id = pj.project_id
            WHERE
                phase IN (%s)
            AND
                hierarchy IN (%s)
            AND
                r_wp IN (%s)
        )
        SELECT
            rfl_table.*
        FROM
        rfl_table;
    """,
    'get_rfl_view_tlm_from_f':"""
        WITH pj AS(
            SELECT
                pjf.id AS project_id,
                pjf.project_code AS project_code,
                lt.lot AS lot,
                archi.architecturename AS architecture_name
            FROM
                project_info AS pjf
                JOIN setup AS stp ON pjf.setup_id = stp.id
                JOIN architecture AS archi on stp.architecture_id = archi.id
                JOIN destination AS dest ON dest.id = stp.destination_id
                JOIN drivetrain AS dt ON stp.drivetrain_id = dt.id
                JOIN lot AS lt ON pjf.lot_id = lt.id
                WHERE pjf.project_code IN (%s)
                AND dest.destination IN (%s)
                AND dt.drivetrain IN (%s)
                AND lt.lot IN (%s)
        ),rfl_tbl AS(
            SELECT
                rfl_view_tlm.pj_id as {0}r_pj_id,
                rfl_view_tlm.rfl_id as {0}rfl_id,
                rfl_view_tlm.phase_id as {0}phase_id,
                phase.phase as {0}phase,
                rfl_view_tlm.r_wp as {0}r_wp,
                rfl_view_tlm.flag_to as {0}flag_to,
                rfl_view_tlm.to_solving_value as {0}to_solving_value,
                rfl_view_tlm.flag_display_on_summary_logic as {0}flag_display_on_summary_logic,
                rfl_view_tlm.r_wp_id as {0}r_wp_id,
                rfl_view_tlm.l_wp as {0}l_wp,
                r_s_id as {0}r_s_id,
                l_s_id as {0}l_s_id,
                r_item as {0}r_item,
                r_item_2 as {0}r_item_2,
                prfl_r as {0}req,
                r_unit as {0}r_unit,
                r_uc as {0}r_scene,
                f_id as {0}f_id,
                ddt.user_memo as {0}user_memo,
                f_item as {0}f_item,
                prfl_f as {0}func,
                f_unit as {0}f_unit,
                l_item as {0}l_item,
                prfl_l as {0}logic,
                l_unit as {0}l_unit,
                l_r_s_p_i as c_related_se_parameter_id,
                l_uc as {0}l_scene,
                prfl_note as {0}note,
                rfl_view_tlm.r_wp as wp,
                pj.project_code as project_code,
                pj.lot as lot,
                pj.architecture_name as archi,
                rfl_view_tlm.phase as phase,
                rfl_view_tlm.hierarchy as hierarchy,
                rfl_view_tlm.n_wp as {0}n_wp,                
                allocation as {0}allocation,
                sender_judge as {0}sender_judge,
                sender_name as {0}sender_name,
                DATE(sender_date) as {0}sender_date,
                sender_comment as {0}sender_comment,
                receiver_judge as {0}receiver_judge,
                receiver_name as {0}receiver_name,
                DATE(receiver_date) as {0}receiver_date,
                receiver_comment as {0}receiver_comment,
                rfl_view_tlm.index as {0}index,
                rfl_view_tlm.rfl_id as rfl_id,
                rfl_view_tlm.phase_id as ph_id

            FROM
                rfl_view_tlm
            INNER JOIN
                pj
            ON
                rfl_view_tlm.pj_id = pj.project_id
            INNER JOIN
                phase
            ON
                phase_id = phase.id
            FULL OUTER JOIN(
                SELECT DISTINCT ON (project_id, phase_id, rfl_id) *
                FROM detail_data_to
                ORDER BY project_id, phase_id, rfl_id, update_day DESC
            ) AS ddt
            ON
                rfl_view_tlm.pj_id = ddt.project_id
                AND rfl_view_tlm.rfl_id = ddt.rfl_id
                AND rfl_view_tlm.phase_id = ddt.phase_id
            WHERE
                phase.phase in (%s)
                and rfl_view_tlm.hierarchy in  (%s)
                and rfl_view_tlm.r_wp in (%s)
                and f_item in (%s)
            )
            SELECT
                rfl_tbl.*
            FROM  rfl_tbl

            ORDER BY rfl_tbl.{0}r_wp_id;
    """,
    'get_wps_related_to_hr_from_hr1':"""
        WITH hr1 AS(
            SELECT
                wp.wp AS hr1_wp,
                rfl.requirement_s_id AS hr1_req,
                rfl.logic_s_id AS hr1_logic
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
        ),
        hr2 AS(
            SELECT
                hr1_wp AS hr1_wp,
                hr2_wp.wp AS hr2_wp,
                hr2_rfl.logic_s_id AS hr2_logic
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
        ),
        hr3 AS(
            SELECT DISTINCT ON (hr1_wp,hr2_wp,hr3_wp)
                hr1_wp AS hr1_wp,
                hr2_wp AS hr2_wp,
                hr3_wp.wp AS hr3_wp
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
        )
        SELECT *
        FROM hr3;
    """,
    'get_wps_related_to_hr_from_hr2':"""
        WITH hr2 AS(
            SELECT
                wp.wp AS hr2_wp,
                rfl.requirement_s_id AS hr2_req,
                rfl.logic_s_id AS hr2_logic
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
        ),hr3 AS(
            SELECT
                hr2_wp AS hr2_wp,
                hr2_req AS hr2_req,
                hr3_wp.wp AS hr3_wp
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
        ),hr1 AS(
            SELECT
                hr1_wp.wp AS hr1_wp,
                hr2_wp AS hr2_wp,
                hr3_wp AS hr3_wp
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
            )
        SELECT
            DISTINCT ON (hr1_wp,hr2_wp,hr3_wp)
            hr1_wp,
            hr2_wp,
            hr3_wp
        FROM
            hr1;
    """,
    'get_wps_related_to_hr_from_hr3':"""
        WITH hr3 AS(
            SELECT
                wp.wp AS hr3_wp,
                hr3_lrr.r_s_id AS hr3_req
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
                prj_rfl AS prfl
            ON 
                prfl.rfl_id = rfl.id
            INNER JOIN
                project_info AS prji
            ON
                prji.id = prfl.project_info_id
            WHERE
                wp.wp = %s
                AND prji.project_code = %ss
        ),
        hr2 AS(
            SELECT
                hr2_wp.wp AS hr2_wp,
                hr2_rfl.requirement_s_id AS hr2_req,
                hr3_wp
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
        ),hr1 AS(
            SELECT
                hr1_wp.wp AS hr1_wp,
                hr2_req,
                hr2_wp,
                hr3_wp
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
        )
        SELECT
            DISTINCT ON (hr1_wp,hr2_wp,hr3_wp)
            hr1_wp,
            hr2_wp,
            hr3_wp
        FROM
            hr1;
    """,
    'lock_prj_rfl_for_update':"""
        SELECT
            requirement,function,logic,note
        FROM
            prj_rfl
        WHERE
            project_info_id = %s
        AND
            rfl_id = %s
        AND
            phase_id = %s
        FOR UPDATE
    """,
    'get_related_f_from_hr1':"""
        WITH hr1 AS(
            SELECT
                wp.wp AS hr1_wp,
                rfl.requirement_s_id AS hr1_req,
                rfl.logic_s_id AS hr1_logic,
                hr1_f.design_item as hr1_function
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
                f_parameter AS hr1_f
            ON
                rfl.function_id = hr1_f.id
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
        ),hr2 AS(
            SELECT
                hr1_wp AS hr1_wp,
                hr2_wp.wp AS hr2_wp,
                hr1_function,
                hr2_rfl.logic_s_id AS hr2_logic,
                hr2_f.design_item as hr2_function
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
                f_parameter AS hr2_f
            ON
                hr2_rfl.function_id = hr2_f.id
            INNER JOIN
                wp AS hr2_wp
            ON
                hr2_r.wp_id = hr2_wp.id
        ),hr3 AS(
            SELECT DISTINCT ON (hr1_function,hr2_function,hr3_function)
                hr1_wp,
                hr2_wp,
                hr3_wp.wp,
                hr1_function,
                hr2_function,
                hr3_f.design_item AS hr3_function
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
                rfl AS hr3_rfl
            ON
                hr3_lrr.r_s_id = hr3_rfl.requirement_s_id
            INNER JOIN
                f_parameter AS hr3_f
            ON
                hr3_rfl.function_id = hr3_f.id
            INNER JOIN
                wp AS hr3_wp
            ON
                hr3_r.wp_id = hr3_wp.id
        )
        SELECT *
        FROM hr3
    """,
    'get_related_f_from_hr2':"""
        WITH hr2 AS(
            SELECT
                wp.wp AS hr2_wp,
                rfl.requirement_s_id AS hr2_req,
                rfl.logic_s_id AS hr2_logic,
                hr2_f.design_item AS hr2_function
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
                f_parameter AS hr2_f
            ON
                rfl.function_id = hr2_f.id
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
        ),hr3 AS(
            SELECT
                hr2_wp,
                hr2_req,
                hr2_function,
                hr3_wp.wp AS hr3_wp,
                hr3_f.design_item AS hr3_function
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
                rfl AS hr3_rfl
            ON
                hr3_lrr.r_s_id = hr3_rfl.requirement_s_id
            INNER JOIN
                f_parameter AS hr3_f
            ON
                hr3_rfl.function_id = hr3_f.id
            INNER JOIN
                wp AS hr3_wp
            ON
                hr3_r.wp_id = hr3_wp.id
        ),hr1 AS(
            SELECT DISTINCT ON (hr1_function,hr2_function,hr3_function)
                hr1_wp.wp,
                hr2_wp,
                hr3_wp,
                hr1_f.design_item AS hr1_function,
                hr2_function,
                hr3_function
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
                f_parameter AS hr1_f
            ON
                hr1_rfl.function_id = hr1_f.id
            INNER JOIN
                WP AS hr1_wp
            ON
                hr1_wp.id = hr1_r.wp_id
            )
        SELECT
            *
        FROM
            hr1;
    """,
    'get_related_f_from_hr3':"""
        WITH hr3 AS(
            SELECT
                wp.wp AS hr3_wp,
                hr3_lrr.r_s_id AS hr3_req,
                hr3_f.design_item AS hr3_function
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
                rfl AS hr3_rfl
            ON
                srr.id = hr3_rfl.requirement_s_id
            INNER JOIN
                f_parameter AS hr3_f
            ON
                hr3_f.id = hr3_rfl.function_id
            INNER JOIN
                prj_rfl AS prfl
            ON 
                prfl.rfl_id = hr3_rfl.id
            INNER JOIN
                project_info AS prji
            ON
                prji.id = prfl.project_info_id                
            WHERE
            wp.wp = %s
            AND prji.project_code = %s           
        ),
        hr2 AS(
            SELECT
                hr2_wp.wp AS hr2_wp,
                hr2_rfl.requirement_s_id AS hr2_req,
                hr2_f.design_item AS hr2_function,
                hr3_function,
                hr3_wp
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
                f_parameter AS hr2_f
            ON
                hr2_rfl.function_id = hr2_f.id
            INNER JOIN
                wp AS hr2_wp
            ON
                hr2_r.wp_id = hr2_wp.id
        ),hr1 AS(
            SELECT DISTINCT ON (hr1_function,hr2_function,hr3_function)
                hr1_wp.wp,
                hr2_wp,
                hr3_wp,
                hr1_f.design_item AS hr1_function,
                hr2_function,
                hr3_function
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
                f_parameter AS hr1_f
            ON
                hr1_rfl.function_id = hr1_f.id
            INNER JOIN
                WP AS hr1_wp
            ON
                hr1_wp.id = hr1_r.wp_id
        )
        SELECT
            *
        FROM
        hr1;
    """,
    'get_wp_tree':"""
        WITH RECURSIVE r AS(
            SELECT
                wr.id AS id,
                wr.parent_id AS parent_id,
                wr.wp_id AS wp_id,
                0 AS hierarchy,
                wp.wp AS wp
            FROM wp_tree AS wr
            INNER JOIN
                wp
            ON
                wp_id = wp.id
            WHERE
                parent_id = %s
            UNION ALL
                SELECT
                    wr.id AS id,
                    wr.parent_id AS parent_id,
                    wr.wp_id AS wp_id,
                    r.hierarchy+1 AS hierarchy,
                    wp.wp AS wp
                FROM r
                INNER JOIN
                    wp_tree AS wr
                ON

                    wr.parent_id = r.id
                INNER JOIN
                    wp
                ON
                    wr.wp_id = wp.id
            )
        SELECT *
        FROM r
        ORDER BY hierarchy,id;
    """,
    'get_wp_tree_s':"""
            SELECT
                wr.id AS id,
                wr.parent_id AS parent_id,
                wr.wp_id AS wp_id,
                wp.wp AS wp
            FROM wp_tree AS wr
            INNER JOIN
                wp
            ON
                wp_id = wp.id
            WHERE
                parent_id = %s;
    """,
    'get_all_wp_tree':"""
        WITH RECURSIVE r AS(
            SELECT
                wr.id AS id,
                wr.parent_id AS parent_id,
                wr.wp_id AS wp_id,
                0 AS hierarchy,
                wp.wp AS wp
            FROM
                wp_tree AS wr
            INNER JOIN
                wp
            ON
                wp_id = wp.id
            WHERE
                parent_id is NULL

            UNION ALL
                SELECT
                    wr.id AS id,
                    wr.parent_id AS parent_id,
                    wr.wp_id AS wp_id,
                    r.hierarchy+1 AS hierarchy,
                    wp.wp AS wp
                FROM r
                INNER JOIN
                    wp_tree AS wr
                ON

                    wr.parent_id = r.id
                INNER JOIN
                    wp
                ON
                    wr.wp_id = wp.id
            )
        SELECT *
        FROM r
        ORDER BY hierarchy,id;
    """,
    'get_all_vwp':"""
        SELECT
            wr.id AS id,
            wr.parent_id AS parent_id,
            wr.wp_id AS wp_id,
            0 AS hierarchy,
            wp.wp AS wp
        FROM
            wp_tree AS wr
        INNER JOIN
            wp
        ON
            wr.wp_id = wp.id
        WHERE
            parent_id is NULL
    """,
    'get_selected_vwp':"""
        SELECT
            wr.id AS id,
            wp.wp AS wp
        FROM wp_tree AS wr
        INNER JOIN
            wp
        ON
            wp_id = wp.id
        WHERE
            wp in ({0})
    """,
    'get_rfl':"""
        SELECT
            requirement_s_id,
            function_id,
            logic_s_id
        FROM
            rfl
        WHERE
            rfl.id = %s
    """,
    'get_r_tree_from_hr2':"""
        WITH hr2 AS(
            SELECT
                wp.wp AS hr2_wp,
                rfl.requirement_s_id AS hr2_req,
                rfl.logic_s_id AS hr2_logic
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
                AND r.hierarchy_id = 2
        ),hr3 AS(
            SELECT
                hr2_wp AS hr2_wp,
                hr2_req AS hr2_req,
                hr3_wp.wp AS hr3_wp
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
            WHERE
                hr3_r.hierarchy_id = 3
        ),hr1 AS(
            SELECT
                hr1_wp.wp AS hr1_wp,
                hr2_wp AS hr2_wp,
                hr3_wp AS hr3_wp
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
            WHERE
                hr1_r.hierarchy_id = 1
            )
        SELECT
            DISTINCT ON (hr1_wp,hr2_wp,hr3_wp)
            hr1_wp,
            hr2_wp,
            hr3_wp
        FROM
            hr1;
    """,
    'get_r_tree_from_hr3':"""
        WITH hr3 AS(
            SELECT
                wp.wp AS hr3_wp,
                rfl.requirement_s_id AS hr3_req,
                rfl.logic_s_id AS hr3_logic
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
                hr2_rfl.requirement_s_id AS hr2_req,
                hr3_req AS hr3_req,
                hr2_wp.wp AS hr2_wp
            FROM
                hr3
            INNER JOIN
                l_r_relation AS hr2_lrr
            ON
                hr3_req = hr2_lrr.r_s_id
            INNER JOIN
                setup_l_relation AS hr2_slr
            ON
                hr2_lrr.l_s_id  = hr2_slr.id
            INNER JOIN
                rfl AS hr2_rfl
            ON
                hr2_slr.id = hr2_rfl.logic_s_id
            INNER JOIN
                setup_r_relation AS hr2_srr
            ON
                hr2_srr.id = hr2_rfl.requirement_s_id
            INNER JOIN
                r_parameter AS hr2_r
            ON
                hr2_srr.r_parameter_id = hr2_r.id
            INNER JOIN
                wp AS hr2_wp
            ON
                hr2_r.wp_id = hr2_wp.id
            WHERE
                hr2_r.hierarchy_id = 2
        ),hr1 AS(
            SELECT
                hr1_wp.wp AS hr1_wp,
                hr2_wp AS hr2_wp,
                hr3_wp AS hr3_wp
            FROM
                hr2
            INNER JOIN
                l_r_relation AS hr1_lrr
            ON
                hr2_req = hr1_lrr.r_s_id
            INNER JOIN
                setup_l_relation AS hr1_slr
            ON
                hr1_lrr.l_s_id  = hr1_slr.id
            INNER JOIN
                rfl AS hr1_rfl
            ON
                hr1_slr.id = hr1_rfl.logic_s_id
            INNER JOIN
                setup_r_relation AS hr1_srr
            ON
                hr1_srr.id = hr1_rfl.requirement_s_id
            INNER JOIN
                r_parameter AS hr1_r
            ON
                hr1_srr.r_parameter_id = hr1_r.id
            INNER JOIN
                wp AS hr1_wp
            ON
                hr1_r.wp_id = hr1_wp.id
            WHERE
                hr1_r.hierarchy_id = 1
        )
        SELECT * FROM hr1;
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