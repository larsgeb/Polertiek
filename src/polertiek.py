import sqlite3
import os
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import numpy as np

from joblib import Memory

# Create a directory for caching if it doesn't exist
if not os.path.exists("./data"):
    os.makedirs("./data")

# Specify the cache directory
cache_dir = "./data/cache"
memory = Memory(cache_dir, verbose=0)


def table_exists(cursor, table_name):
    """
    Check if a table exists in the database.
    """
    cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    )
    return cursor.fetchone() is not None


def ensure_master_table(cursor):
    """
    Create the master_table if it doesn't exist.
    """

    # Commit any changes before creating the master_table
    cursor.connection.commit()

    # Check if master_table exists and create if necessary
    if not table_exists(cursor, "master_table"):
        cursor.execute(
            """
            CREATE TABLE limited_info_table AS
            SELECT voteMatrix.*, votePerParty.vote_date
            FROM voteMatrix
            JOIN votePerParty ON voteMatrix.id = votePerParty.id
            GROUP BY voteMatrix.id
            ORDER BY votePerParty.vote_date;
        """
        )

        cursor.execute(
            """
            CREATE TABLE master_table AS
            SELECT 
                limited_info_table.*, 
                categoryList.category,
                categoryList.subcategory,
                metaList.title,
                metaList.subject,
                metaList.date,
                metaList.proposaldate,
                metaList.proposaltype,
                metaList.result,
                metaList.proposalURL,
                metaList.voteURL
            FROM query = f"SELECT * FROM master_table WHERE vote_date BETWEEN '{start_date}' AND '{end_date}';"
            JOIN categoryList ON limited_info_table.id = categoryList.id
            JOIN metaList ON limited_info_table.id = metaList.id
            JOIN votePerParty ON limited_info_table.id = votePerParty.id
            GROUP BY limited_info_table.id
            ORDER BY votePerParty.vote_date;
        """
        )


@memory.cache
def fetch_and_preprocess_consensus_data(
    database_path, start_year=1922, end_year=2022
):
    """
    Fetches and preprocesses consensus data from the specified SQLite database.

    Args:
    - database_path (str): Path to the SQLite database.
    - start_year (int): Start year for data retrieval (default: 1922).
    - end_year (int): End year for data retrieval (default: 2022).

    Returns:
    - consensus_per_year (pd.DataFrame): DataFrame with years and corresponding consensus values.
    - party_agreement_with_other_parties_per_year (pd.DataFrame): DataFrame with party agreements per year.
    """
    if not os.path.isfile(database_path):
        raise ValueError(
            f"Database {database_path} does not exist yet. Please download."
        )

    # Initialize empty lists to store results
    years = []
    total_consensus_list = []
    in_line_votes_list = []

    # Loop through each year
    for year in range(start_year, end_year + 1):
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()
            ensure_master_table(cursor=cursor)

            query = f"SELECT * FROM votePerParty WHERE vote_date >= '{start_date}' AND vote_date < '{end_date}';"

            stem_df = pd.read_sql_query(
                query, conn
            )  # Assuming 'vote_date' is the date column

        # Drop parties with only 9 votes
        stem_df = stem_df.loc[:, (stem_df != 9).any()]

        # Calculate total votes
        try:
            total_votes = (
                stem_df["vote_1"] + stem_df["vote_0"] + stem_df["vote_8"]
            )
        except KeyError:
            # Add results to the lists
            years.append(year)
            total_consensus_list.append(np.nan)
            in_line_votes_list.append(pd.Series())
            continue

        # Normalize counts to obtain proportions
        stem_df["prop_votes_1"] = stem_df["vote_1"] / total_votes
        stem_df["prop_votes_0"] = stem_df["vote_0"] / total_votes
        stem_df["prop_votes_8"] = stem_df["vote_8"] / total_votes

        # Pivot the DataFrame to have each party as a column
        pivot_stem_df = stem_df.pivot_table(
            index="id", columns="party", values=["prop_votes_1"], aggfunc="sum"
        )

        # Fill NaN values with 0
        pivot_stem_df = pivot_stem_df.fillna(0)

        # Perform weighted correlation
        weighted_corr = pivot_stem_df.corr()

        # Calculate the total number of votes for each party
        total_votes_cast = (
            stem_df.groupby("party")["vote_0"].sum()
            + stem_df.groupby("party")["vote_1"].sum()
            + stem_df.groupby("party")["vote_8"].sum()
        )

        # Calculate the outer product with the correlation matrix
        weight = np.outer(total_votes_cast, total_votes_cast)
        np.fill_diagonal(weight, 0)
        weight = weight.astype(float)  # Explicitly convert to float
        weight /= weight.sum(axis=1)
        in_line_votes = (weighted_corr * weight).sum(axis=0)

        # Recalculate the weight matrix
        weight = np.outer(total_votes_cast, total_votes_cast)
        np.fill_diagonal(weight, 0)
        weight = weight.astype(float)  # Explicitly convert to float
        weight /= weight.sum()

        # Calculate total consensus
        total_consensus = (weighted_corr * weight).sum().sum()

        # Add results to the lists
        years.append(year)
        total_consensus_list.append(total_consensus)
        in_line_votes_list.append(in_line_votes)

    # Create a DataFrame from the results
    consensus_per_year = pd.DataFrame(
        {
            "year": years,
            "consensus": total_consensus_list,
        }
    )

    party_agreement_with_other_parties_per_year = pd.concat(
        in_line_votes_list, axis=1
    ).T
    party_agreement_with_other_parties_per_year.index = years

    party_agreement_with_other_parties_per_year.columns = (
        party_agreement_with_other_parties_per_year.columns.get_level_values(1)
    )

    return consensus_per_year, party_agreement_with_other_parties_per_year


def fetch_and_preprocess_data(database_path, year=2022, drop_meta=True):
    if not os.path.isfile(database_path):
        raise ValueError(
            f"Database {database_path} does not exists yet, please download."
        )

    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    with sqlite3.connect(database_path) as conn:
        cursor = conn.cursor()
        ensure_master_table(cursor=cursor)

        # Calculate the date from one year ago
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime(
            "%Y-%m-%d"
        )

        # Ensure master_table is created
        ensure_master_table(cursor=cursor)

        if year < 1922:
            raise ValueError("No data before 1922.")
        elif year > 2022:
            raise ValueError("No data after 2022.")
        elif year < 1994:
            # Data before 1994 doesn't have meta info
            query = f"SELECT * FROM limited_info_table WHERE vote_date BETWEEN '{start_date}' AND '{end_date}';"
        else:
            # Fetch data from SQLite and load it into a pandas DataFrame
            query = f"SELECT * FROM master_table WHERE vote_date BETWEEN '{start_date}' AND '{end_date}';"

        df = pd.read_sql_query(
            query, conn, index_col="vote_date"
        )  # Assuming 'vote_date' is the date column

    # Drop the 'id' column
    df = df.drop(columns=["id"], errors="ignore")

    # Drop parties with only 9's
    df = df.loc[:, (df != 9).any()]

    if drop_meta:
        # Split the DataFrame based on categories
        meta_columns = [
            "category",
            "subcategory",
            "title",
            "subject",
            "date",
            "proposaldate",
            "proposaltype",
            "result",
            "proposalURL",
            "voteURL",
        ]
        df = df.drop(columns=meta_columns, errors="ignore")

    return df
