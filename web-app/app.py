from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from sklearn.decomposition import PCA
from flask_bootstrap import Bootstrap  # Import Bootstrap
import numpy as np

app = Flask(__name__)
Bootstrap(app)  # Initialize Bootstrap

from sklearn.impute import SimpleImputer


# Function to fetch data based on the selected year
def fetch_correlation_data(selected_year):
    print(f"Fetch data for {selected_year}")
    try:
        conn = sqlite3.connect("./data/votes.sqlite")
        cursor = conn.cursor()

        query = f"SELECT * FROM master_table WHERE strftime('%Y', vote_date) = '{selected_year}';"
        df = pd.read_sql_query(query, conn, index_col="vote_date")

        if df.empty:
            query = f"SELECT * FROM limited_info_table WHERE strftime('%Y', vote_date) = '{selected_year}';"
            df = pd.read_sql_query(query, conn, index_col="vote_date")
            if df.empty:
                raise Exception(
                    f"No data available for the year {selected_year}"
                )

        conn.close()

        if df.empty:
            raise Exception(f"No data available for the year {selected_year}")

        df = df.drop(columns=["id"], errors="ignore")

        columns_to_drop = df.columns[df.eq(9).all()]
        df = df.drop(columns=columns_to_drop)

        df_with_meta = df.copy()

        # Replace values of 8 or 9 with NaN
        df.replace({9: np.nan}, inplace=True)
        df.replace({8: np.nan}, inplace=True)

        df = df.dropna(axis=0, how="all")
        df = df.dropna(axis=1, how="all")

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
        for meta_column in meta_columns:
            try:
                df = df.drop(columns=meta_column)
            except KeyError as e:
                if not str(e) == f"\"['{meta_column}'] not found in axis\"":
                    raise e

        correlation_matrix = df.corr()

        # Impute NaNs with the mean (you can also use median or other imputation methods)
        imputer = SimpleImputer(strategy="mean")
        df_imputed = pd.DataFrame(
            imputer.fit_transform(df), columns=df.columns, index=df.index
        )

        # Perform PCA on the imputed DataFrame
        pca = PCA()
        pca_result = pca.fit_transform(df_imputed)

        # Use the sorting order from PCA to reorder the correlation matrix
        sorted_columns = df_imputed.columns[pca.components_[0].argsort()]
        correlation_matrix_sorted = correlation_matrix.loc[
            sorted_columns, sorted_columns
        ]

        correlation_matrix_sorted.replace({np.nan: None}, inplace=True)

        # Count occurrences of each category and subcategory
        try:
            category_counts = df_with_meta["category"].value_counts().to_dict()
            subcategory_counts = (
                df_with_meta["subcategory"].value_counts().to_dict()
            )
        except KeyError:
            category_counts = {None: None}
            subcategory_counts = {None: None}

        return (
            correlation_matrix_sorted,
            df_with_meta,
            category_counts,
            subcategory_counts,
        )

    except Exception as e:
        raise e


def get_available_years():
    conn = sqlite3.connect("./data/votes.sqlite")
    cursor = conn.cursor()

    query = "SELECT DISTINCT strftime('%Y', vote_date) as year FROM limited_info_table;"
    available_years = [str(row[0]) for row in cursor.execute(query)]

    conn.close()

    return available_years


# New route to get available years
@app.route("/get_available_years", methods=["GET"])
def get_available_years_route():
    try:
        years = get_available_years()
        return jsonify({"available_years": years})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/update_plot", methods=["POST"])
def update_plot():
    selected_year = request.json["selected_year"]

    balbla = fetch_correlation_data(selected_year)

    result, df_all_votes, category_counts, subcategory_counts = balbla

    if isinstance(result, str):  # If an error occurred
        return jsonify({"error": result})

    correlation_matrix_list = result.values.tolist()
    df_all_votes = df_all_votes.values.tolist()
    parties = result.index.tolist()

    return jsonify(
        {
            "selected_year": selected_year,
            "correlation_matrix": correlation_matrix_list,
            "meta_info": df_all_votes,
            "parties": parties,
            "category_counts": dict(category_counts),
            "subcategory_counts": dict(subcategory_counts),
        }
    )


# Function to fetch data based on the selected year
def fetch_voting_data(selected_year):
    print(f"Fetch data for {selected_year}")
    try:
        conn = sqlite3.connect("other_data_formats/votes.sqlite")
        cursor = conn.cursor()

        query = f"SELECT * FROM new_table WHERE strftime('%Y', vote_date) = '{selected_year}';"
        df = pd.read_sql_query(query, conn, index_col="vote_date")

        conn.close()

        if df.empty:
            raise Exception(f"No data available for the year {selected_year}")

        df = df.drop(columns=["id"], errors="ignore")
        df = df.loc[:, (df != 9).any()]
        df_standardized = (df - df.mean()) / df.std()
        pca = PCA()
        pca_result = pca.fit_transform(df_standardized)
        sorted_columns = df.columns[pca.components_[0].argsort()]
        df_sorted = df[sorted_columns]
        correlation_matrix_sorted = df_sorted.corr()

        return correlation_matrix_sorted

    except Exception as e:
        return str(e)  # Return the error message


if __name__ == "__main__":
    app.run(port=8000, debug=True)
