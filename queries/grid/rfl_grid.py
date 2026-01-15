"""
Summary:
    RFL_Grid
Attributes:
    RFL_SELECT_QUERIES : RFL_SELECT文
Author:
    Telema Tanaka
Created:
    2025-07-17
"""

def get_rfl_historical_grid():
    select_clause = """
        SELECT
            {1}
            {2}
            {3}
            hr{0}_wp.wp AS hr{0}_wp,
            hr{0}_rfl.id AS hr{0}_rfl_id,
            hr{0}_rfl.logic_s_id AS hr{0}_rfl_logic_s_id,
            concat(hr{0}_r.design_item_1,'  ',hr{0}_r.design_item_2,'  ',hr{0}_r.design_item_3) AS hr{0}_r_item,
            hr{0}_prj_rfl.requirement AS hr{0}_req,
            hr{0}_r.unit AS hr{0}_r_unit,
            hr{0}_r_scene.usecase AS hr{0}_r_scene,
            hr{0}_f.design_item AS hr{0}_f_item,
            hr{0}_prj_rfl.function AS hr{0}_func,
            hr{0}_f_unit.unit AS hr{0}_f_unit,
            hr{0}_l.design_item AS hr{0}_l_item,
            hr{0}_prj_rfl.logic AS hr{0}_logic,
            hr{0}_l_unit.unit AS hr{0}_l_unit,
            hr{0}_l_scene.usecase AS hr{0}_l_scene,
            hr{0}_prj_rfl.note AS hr{0}_note,
            hr{0}_prj_rfl.sender_judge AS hr{0}_sender_judge,
            hr{0}_prj_rfl.sender_name AS hr{0}_sender_name,
            hr{0}_prj_rfl.sender_date AS hr{0}_sender_date,
            hr{0}_prj_rfl.sender_comment AS hr{0}_sender_comment,
            hr{0}_prj_rfl.receiver_judge AS hr{0}_receiver_judge,
            hr{0}_prj_rfl.receiver_name AS hr{0}_receiver_name,
            hr{0}_prj_rfl.receiver_date AS hr{0}_receiver_date,
            hr{0}_prj_rfl.receiver_comment AS hr{0}_receiver_comment,
            hr{0}_rfl.index AS hr{0}_index
    """


    where_clause1 = """
        WHERE
            pji.project_code = %s
            and hr1_phase.phase = %s
            and hr1_r.hierarchy_id = 1
            and wp in %s
    """

    where_clause2_3 = """
        WHERE
            hr{0}_r.hierarchy_id = {0}
            and hr{0}_prj_rfl.project_info_id = pj_id
    """

    cte_blocks = []
    join1 = """
        INNER JOIN
            project_info AS pji
        ON
            pji.id = hr1_prj_rfl.project_info_id
        INNER JOIN
            rfl AS hr1_rfl
        ON
            hr1_prj_rfl.rfl_id = hr1_rfl.id
        INNER JOIN
            setup_r_relation AS hr1_srr
        ON
        hr1_srr.id = hr1_rfl.requirement_s_id
        INNER JOIN
            r_parameter AS hr1_r
        ON
            hr1_srr.r_parameter_id = hr1_r.id
        INNER JOIN
            usecase AS hr1_r_scene
        ON
            hr1_r_scene.id = hr1_srr.usecase_id
        INNER JOIN
            f_parameter AS hr1_f
        ON
            hr1_f.id = hr1_rfl.function_Id
        INNER JOIN
            units AS hr1_f_unit
        ON
                hr1_f_unit.id = hr1_f.unit_id
        INNER JOIN
            setup_l_relation as hr1_slr
        ON
            hr1_slr.id = hr1_rfl.logic_s_id
        INNER JOIN
            l_parameter as hr1_l
        ON
            hr1_l.id = hr1_slr.l_parameter_id
        INNER JOIN
            units AS hr1_l_unit
        ON
            hr1_l_unit.id = hr1_l.unit_id
        INNER JOIN
            usecase AS hr1_l_scene
        ON
            hr1_l_scene.id = hr1_slr.usecase_id
        INNER JOIN
            wp AS hr1_wp
        ON
            hr1_r.wp_id = hr1_wp.id
        INNER JOIN
            phase AS hr1_phase
        ON
            hr1_phase.id = hr1_prj_rfl.phase_id
    """

    join2_3 = """
        INNER JOIN
            l_r_relation AS hr{0}_lrr
        ON
            hr{0}_lrr.l_s_id = hr{1}_rfl_logic_s_id
        INNER JOIN
            setup_r_relation AS hr{0}_srr
        ON
            hr{0}_srr.id = hr{0}_lrr.r_s_id
        INNER JOIN
            rfl AS hr{0}_rfl
        ON
            hr{0}_rfl.requirement_s_id = hr{0}_srr.id
        INNER JOIN
            prj_rfl AS hr{0}_prj_rfl
        ON
            hr{0}_prj_rfl.rfl_id = hr{0}_rfl.id
        INNER JOIN
            r_parameter AS hr{0}_r
        ON
            hr{0}_r.id = hr{0}_srr.r_parameter_id
        INNER JOIN
            usecase AS hr{0}_r_scene
        ON
            hr{0}_r_scene.id = hr{0}_srr.usecase_id
        INNER JOIN
            f_parameter AS hr{0}_f
        ON
            hr{0}_f.id = hr{0}_rfl.function_id
        INNER JOIN
            units AS hr{0}_f_unit
        ON
            hr{0}_f_unit.id = hr{0}_f.unit_id
        INNER JOIN
            setup_l_relation AS hr{0}_slr
        ON
            hr{0}_slr.id = hr{0}_rfl.logic_s_id
        INNER JOIN
            l_parameter AS hr{0}_l
        ON
            hr{0}_l.id = hr{0}_slr.l_parameter_id
        INNER JOIN
            units AS hr{0}_l_unit
        ON
            hr{0}_l_unit.id = hr{0}_l.unit_id
        INNER JOIN
            usecase AS hr{0}_l_scene
        ON
            hr{0}_l_scene.id = hr{0}_slr.usecase_id
        INNER JOIN
            wp AS hr{0}_wp
        ON
            hr{0}_wp.id = hr{0}_r.wp_id
        INNER JOIN
            phase AS hr{0}_phase
        ON
            hr{0}_phase.id = hr{0}_prj_rfl.phase_id
    """

    cte_blocks = []

    for i in range(1, 4):

        if i == 1 :
            where_clause = where_clause1.format(i)
            select = select_clause.format(i,'','pji.project_code AS pj_code,','pji.id AS pj_id,')
            join = join1.format(i)
            from_clause = 'prj_rfl AS hr1_prj_rfl'
        if i == 2 :
            where_clause = where_clause2_3.format(i)
            select = select_clause.format(i,f'hr{i-1}.*,','','')
            from_clause = 'hr1'
            join = join2_3.format(i,i-1)
        if i == 3:
            where_clause = where_clause2_3.format(i)
            select = select_clause.format(i,f'hr{i-1}.*,','','')
            from_clause = 'hr2'
            join = join2_3.format(i,i-1)


        cte = f"""
        hr{i} AS (
            {select}
            FROM
                {from_clause}
                {join}
            {where_clause}
        )
        """.strip()
        cte_blocks.append(cte)

    query = 'WITH ' + ",\n".join(cte_blocks) + """SELECT
            hr1_wp,
            hr1_r_item,
            hr1_req,
            hr1_r_unit,
            hr1_r_scene,
            hr1_f_item,
            hr1_func,
            hr1_f_unit,
            hr1_l_item,
            hr1_logic,
            hr1_l_unit,
            hr1_l_scene,
            hr1_note,
            hr1_sender_judge,
            hr1_sender_name,
            hr1_sender_date,
            hr1_sender_comment,
            hr1_receiver_judge,
            hr1_receiver_name,
            hr1_receiver_date,
            hr1_receiver_comment,
            hr1_index,
            hr2_wp,
            hr2_r_item,
            hr2_req,
            hr2_r_unit,
            hr2_r_scene,
            hr2_f_item,
            hr2_func,
            hr2_f_unit,
            hr2_l_item,
            hr2_logic,
            hr2_l_unit,
            hr2_l_scene,
            hr2_note,
            hr2_sender_judge,
            hr2_sender_name,
            hr2_sender_date,
            hr2_sender_comment,
            hr2_receiver_judge,
            hr2_receiver_name,
            hr2_receiver_date,
            hr2_receiver_comment,
            hr2_index,
            hr3_wp,
            hr3_r_item,
            hr3_req,
            hr3_r_unit,
            hr3_r_scene,
            hr3_f_item,
            hr3_func,
            hr3_f_unit,
            hr3_l_item,
            hr3_logic,
            hr3_l_unit,
            hr3_l_scene,
            hr3_note,
            hr3_sender_judge,
            hr3_sender_name,
            hr3_sender_date,
            hr3_sender_comment,
            hr3_receiver_judge,
            hr3_receiver_name,
            hr3_receiver_date,
            hr3_receiver_comment,
            hr3_index
            FROM hr3;
        """
    return query
