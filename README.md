# N1 Health Data Ops Take-Home Challenge

## Overview

This project combines and standardizes five member rosters from a SQLite database to create an analysis-ready membership table with one row per member.

The project uses Python and SQLite to perform data-quality checks, build the standardized member population, and calculate the requested summary statistics.

## Data Quality Investigation

During exploration of the source data, 24,620 members were found in more than one roster.

Further investigation identified systematic formatting differences between overlapping roster records:

- `roster_2` and `roster_5` contained different date formats (`MM/DD/YYYY` vs. `YYYY-MM-DD`).
- `roster_3` and `roster_4` represented California as either `California` or `CA`.

After standardizing these fields, the overlapping records matched and could be safely deduplicated.

## Project Structure

- `src/data_quality_checks.py` — investigates roster overlap, duplicate members, and field-level differences.
- `src/build_member_tables.py` — discovers roster tables, standardizes the source data, and creates `std_member_info`.
- `src/analysis.py` — calculates and displays the requested analysis results.

## Key Assumptions

- "Active eligibility this year" means a member's eligibility period overlaps any portion of January 1 through December 31, 2025.
- April eligibility means a member's eligibility period overlaps any portion of April 1 through April 30, 2025.
- Tables following the `roster_<number>` naming convention are treated as member roster tables.

## Running the Project

Place the provided SQLite database in:

`data/n1_data_ops_challenge.db`

From the project root, run:

python src/data_quality_checks.py
python src/build_member_tables.py
python src/analysis.py
