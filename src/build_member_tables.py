import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "n1_data_ops_challenge.db"


def get_roster_tables(cursor):
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name LIKE 'roster_%'
    """)

    results = cursor.fetchall()

    rosters = [
        name
        for name, in results
        if name.removeprefix("roster_").isdigit()
    ]

    rosters.sort(
        key=lambda name: int(name.removeprefix("roster_"))
    )

    return rosters


def standardized_roster_query(table_name):
    return f"""
        SELECT
            Person_Id AS member_id,
            First_Name AS member_first_name,
            Last_Name AS member_last_name,

            CASE
                WHEN instr(Dob, '/') > 0
                THEN
                    substr(Dob, 7, 4) || '-' ||
                    substr(Dob, 1, 2) || '-' ||
                    substr(Dob, 4, 2)
                ELSE Dob
            END AS date_of_birth,

            Street_Address AS main_address,
            City AS city,

            CASE
                WHEN State = 'California' THEN 'CA'
                ELSE State
            END AS state,

            Zip AS zip_code,
            payer,

            CASE
                WHEN instr(eligibility_start_date, '/') > 0
                THEN
                    substr(eligibility_start_date, 7, 4) || '-' ||
                    substr(eligibility_start_date, 1, 2) || '-' ||
                    substr(eligibility_start_date, 4, 2)
                ELSE eligibility_start_date
            END AS eligibility_start_date,

            CASE
                WHEN instr(eligibility_end_date, '/') > 0
                THEN
                    substr(eligibility_end_date, 7, 4) || '-' ||
                    substr(eligibility_end_date, 1, 2) || '-' ||
                    substr(eligibility_end_date, 4, 2)
                ELSE eligibility_end_date
            END AS eligibility_end_date

        FROM {table_name}
    """


def build_std_member_info():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    rosters = get_roster_tables(cursor)

    if not rosters:
        connection.close()
        raise ValueError("No roster tables were found.")

    print(f"Roster tables found: {len(rosters)}")

    for roster in rosters:
        print(f"   {roster}")

    roster_queries = []

    for roster in rosters:
        query = standardized_roster_query(roster)
        roster_queries.append(query)

    combined_query = "\nUNION ALL\n".join(roster_queries)

    cursor.execute("""
        DROP TABLE IF EXISTS std_member_info
    """)

    create_query = f"""
        CREATE TABLE std_member_info AS

        WITH standardized_members AS (

            {combined_query}

        ),

        eligible_members AS (
            SELECT DISTINCT *
            FROM standardized_members
            WHERE eligibility_start_date <= '2025-12-31'
              AND eligibility_end_date >= '2025-01-01'
        )

        SELECT *
        FROM eligible_members
    """

    cursor.execute(create_query)

    connection.commit()

    cursor.execute("""
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT member_id) AS distinct_members
        FROM std_member_info
    """)

    total_rows, distinct_members = cursor.fetchone()

    print("\nstd_member_info successfully created.")
    print(f"Total rows: {total_rows:,}")
    print(f"Distinct members: {distinct_members:,}")

    if total_rows != distinct_members:
        connection.close()
        raise ValueError(
            "Validation failed: std_member_info does not contain "
            "one row per member."
        )

    connection.close()


if __name__ == "__main__":
    build_std_member_info()