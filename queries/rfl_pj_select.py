"""
Summary:
    RFL機能SELECT文外だしファイル
Author:
    Telema Tanaka
Created:
    2025-03-25
"""

# region SQL Queries
RFL_PJ_CHOICE_SELECT_QUERIES = {
    'get_all_archi':"""

        SELECT DISTINCT (architecturename)
        FROM architecture;
    """,

    'get_pj_code':"""
        SELECT DISTINCT pjf.project_code
        FROM architecture AS ar
        JOIN setup AS stp
            ON ar.id = stp.architecture_id
        JOIN project_info AS pjf
            ON stp.id = pjf.setup_id
        WHERE
            ar.architecturename IN (%s);
    """,

    'get_destination':"""
        SELECT DISTINCT dest.destination
        FROM project_info AS pjf
        JOIN setup AS stp
            ON pjf.setup_id = stp.id
        JOIN destination AS dest
            ON stp.destination_id = dest.id
        WHERE
            pjf.project_code IN (%s);
    """,

    'get_drive_system':"""
        SELECT DISTINCT dt.drivetrain
        FROM project_info AS pjf
        JOIN setup AS stp
            ON pjf.setup_id = stp.id
        JOIN destination AS dest
            ON dest.id = stp.destination_id
        JOIN drivetrain AS dt
            ON stp.drivetrain_id = dt.id
        WHERE
            pjf.project_code IN (%s)
            AND dest.destination IN (%s);
    """,

    'get_lot':"""
        SELECT DISTINCT lt.lot
        FROM project_info AS pjf
        JOIN setup AS stp
            ON pjf.setup_id = stp.id
        JOIN destination AS dest
            ON dest.id = stp.destination_id
        JOIN drivetrain AS dt
            ON stp.drivetrain_id = dt.id
        JOIN lot AS lt
            ON pjf.lot_id = lt.id
        WHERE
            pjf.project_code IN (%s)
            AND dest.destination IN (%s)
            AND dt.drivetrain IN (%s);
    """,

    'get_phase':"""
        SELECT DISTINCT ph.phase
        FROM project_info AS pjf
        JOIN setup AS stp
            ON pjf.setup_id = stp.id
        JOIN destination AS dest
            ON dest.id = stp.destination_id
        JOIN drivetrain AS dt
            ON stp.drivetrain_id = dt.id
        JOIN lot AS lt
            ON pjf.lot_id = lt.id
        JOIN prj_rfl AS prfl
            on pjf.id = prfl.project_info_id
        JOIN phase as ph on
            ph.id = prfl.phase_id
        WHERE
            pjf.project_code IN (%s)
            AND dest.destination IN (%s)
            AND dt.drivetrain IN (%s)
            AND lt.lot IN (%s);
    """,

    'get_hierarchy':"""
        SELECT DISTINCT hierarchy
        FROM
            rfl_view
        WHERE
            pj_code IN (%s)
            AND
            phase IN (%s);
    """,

    'get_wp':"""
        SELECT DISTINCT r_wp
        FROM
            rfl_view
        WHERE
            pj_code IN (%s)
            AND phase IN (%s)
            AND hierarchy IN (%s);
    """
}
# endregion

def get_query(query):
    return RFL_PJ_CHOICE_SELECT_QUERIES['query']