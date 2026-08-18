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


def run_analysis():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    print("\nN1 DATA OPS CHALLENGE RESULTS\n")

    cursor.execute("""
        SELECT COUNT(*)
        FROM std_member_info
    """)

    total_count = cursor.fetchone()[0]

    print(f"There are {total_count:,} distinct members in the database.")

    # Question 1
    cursor.execute("""
        SELECT COUNT(*)
        FROM std_member_info
        WHERE eligibility_start_date <= '2025-04-30'
          AND eligibility_end_date >= '2025-04-01'
    """)

    april_members = cursor.fetchone()[0]

    print(
        f"1. There are {april_members:,} eligible members "
        f"in April 2025."
    )

    # Question 2
    rosters = get_roster_tables(cursor)

    if not rosters:
        connection.close()
        raise ValueError("No roster tables were found.")

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
        f"2. {duplicate_count:,} members were included more than once."
    )

    # Question 3
    cursor.execute("""
        SELECT payer, COUNT(*)
        FROM std_member_info
        GROUP BY payer
        ORDER BY payer
    """)

    payer_results = cursor.fetchall()

    print("3. Member breakdown by payer:")

    for payer, count in payer_results:
        print(f"   {payer}: {count:,} members")

    # Question 4
    cursor.execute("""
        SELECT COUNT(*)
        FROM std_member_info AS member
        INNER JOIN model_scores_by_zip AS model
            ON CAST(member.zip_code AS INTEGER) = model.zcta
        WHERE model.food_access_score < 2
    """)

    food_access_count = cursor.fetchone()[0]

    print(
        f"4. {food_access_count:,} members live in ZIP codes "
        f"with a food access score below 2."
    )

    # Question 5
    cursor.execute("""
        SELECT AVG(model.social_isolation_score)
        FROM std_member_info AS member
        INNER JOIN model_scores_by_zip AS model
            ON CAST(member.zip_code AS INTEGER) = model.zcta
    """)

    social_isolation_score = cursor.fetchone()[0]

    print(
        f"5. Average Social Isolation Score: "
        f"{social_isolation_score:.2f}"
    )

    # Question 6
    cursor.execute("""
        SELECT
            member.member_id,
            member.member_first_name,
            member.member_last_name,
            member.zip_code,
            model.algorex_sdoh_composite_score
        FROM std_member_info AS member
        INNER JOIN model_scores_by_zip AS model
            ON CAST(member.zip_code AS INTEGER) = model.zcta
        WHERE model.algorex_sdoh_composite_score = (
            SELECT MAX(algorex_sdoh_composite_score)
            FROM model_scores_by_zip
        )
        ORDER BY
            member.member_last_name,
            member.member_first_name
    """)

    highest_score_members = cursor.fetchall()

    if highest_score_members:
        highest_score = highest_score_members[0][4]
        highest_zip = highest_score_members[0][3]

        print(
            f"6. Highest Algorex SDOH composite score: "
            f"{highest_score:.2f}"
        )

        print(f"   ZIP code: {highest_zip}")

        print(
            f"   Members living in this ZIP: "
            f"{len(highest_score_members)}"
        )

        for member_id, first_name, last_name, _, _ in highest_score_members:
            print(
                f"   {member_id} - {first_name} {last_name}"
            )

    connection.close()


if __name__ == "__main__":
    run_analysis()