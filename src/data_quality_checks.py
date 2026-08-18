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


def main():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    print("\nDATA QUALITY CHECKS\n")

    # --------------------------------------------------
    # Get all roster tables
    # --------------------------------------------------

    rosters = get_roster_tables(cursor)

    if not rosters:
        connection.close()
        raise ValueError("No roster tables were found.")

    print(f"Roster tables found: {len(rosters)}")

    for roster in rosters:
        print(f"   {roster}")

    # --------------------------------------------------
    # 1. Check overlap between every roster pair
    # --------------------------------------------------

    print("\nROSTER OVERLAP")

    for i in range(len(rosters)):
        for j in range(i + 1, len(rosters)):

            roster_a = rosters[i]
            roster_b = rosters[j]

            cursor.execute(f"""
                SELECT COUNT(*)
                FROM {roster_a} AS a
                INNER JOIN {roster_b} AS b
                    ON a.Person_Id = b.Person_Id
            """)

            overlap_count = cursor.fetchone()[0]

            print(
                f"{roster_a} vs {roster_b}: "
                f"{overlap_count:,} shared members"
            )

    # --------------------------------------------------
    # 2. Count members appearing more than once
    # --------------------------------------------------

    roster_queries = []

    for roster in rosters:
        roster_queries.append(
            f"SELECT Person_Id FROM {roster}"
        )

    combined_members_query = "\nUNION ALL\n".join(roster_queries)

    duplicate_query = f"""
        WITH combined_members AS (

            {combined_members_query}

        ),

        duplicate_members AS (
            SELECT Person_Id
            FROM combined_members
            GROUP BY Person_Id
            HAVING COUNT(*) > 1
        )

        SELECT COUNT(*)
        FROM duplicate_members
    """

    cursor.execute(duplicate_query)

    duplicate_count = cursor.fetchone()[0]

    print(
        f"\nMembers appearing more than once: "
        f"{duplicate_count:,}"
    )

    # --------------------------------------------------
    # 3. Compare roster_3 vs roster_4
    # --------------------------------------------------

    fields_3_4 = [
        "First_Name",
        "Last_Name",
        "Dob",
        "Street_Address",
        "City",
        "State",
        "Zip",
        "eligibility_start_date",
        "eligibility_end_date",
        "payer"
    ]

    print("\nROSTER 3 VS ROSTER 4 FIELD DIFFERENCES")

    for field in fields_3_4:

        cursor.execute(f"""
            SELECT COUNT(*)
            FROM roster_3 AS r3
            INNER JOIN roster_4 AS r4
                ON r3.Person_Id = r4.Person_Id
            WHERE r3.{field} != r4.{field}
        """)

        difference_count = cursor.fetchone()[0]

        print(
            f"{field}: "
            f"{difference_count:,} differences"
        )

    # --------------------------------------------------
    # 4. Compare roster_2 vs roster_5
    #    Raw values first
    # --------------------------------------------------

    fields_2_5 = [
        "First_Name",
        "Last_Name",
        "Dob",
        "Street_Address",
        "City",
        "State",
        "Zip",
        "eligibility_start_date",
        "eligibility_end_date",
        "payer"
    ]

    print("\nROSTER 2 VS ROSTER 5 RAW FIELD DIFFERENCES")

    for field in fields_2_5:

        cursor.execute(f"""
            SELECT COUNT(*)
            FROM roster_2 AS r2
            INNER JOIN roster_5 AS r5
                ON r2.Person_Id = r5.Person_Id
            WHERE r2.{field} != r5.{field}
        """)

        difference_count = cursor.fetchone()[0]

        print(
            f"{field}: "
            f"{difference_count:,} differences"
        )

    # --------------------------------------------------
    # 5. Recheck date differences after standardization
    # --------------------------------------------------

    date_fields = [
        "Dob",
        "eligibility_start_date",
        "eligibility_end_date"
    ]

    print(
        "\nROSTER 2 VS ROSTER 5 "
        "DATE DIFFERENCES AFTER STANDARDIZATION"
    )

    for field in date_fields:

        cursor.execute(f"""
            SELECT COUNT(*)
            FROM roster_2 AS r2
            INNER JOIN roster_5 AS r5
                ON r2.Person_Id = r5.Person_Id
            WHERE
                (
                    substr(r2.{field}, 7, 4)
                    || '-' ||
                    substr(r2.{field}, 1, 2)
                    || '-' ||
                    substr(r2.{field}, 4, 2)
                ) != r5.{field}
        """)

        difference_count = cursor.fetchone()[0]

        print(
            f"{field}: "
            f"{difference_count:,} differences"
        )

    connection.close()


if __name__ == "__main__":
    main()