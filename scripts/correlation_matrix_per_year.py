# plot.py
import argparse
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import polertiek


# Parse command-line arguments
parser = argparse.ArgumentParser(
    description="Generate a heatmap of sorted correlation matrix of party votes."
)
parser.add_argument(
    "--year",
    type=int,
    default=None,
    help="Specify the year to fetch votes for (default: 2022).",
)
args = parser.parse_args()

# Check if the provided year is equal to the default and if the argument was explicitly set by the user
if args.year is None:
    year = 2022
    print(
        "Warning: Using the default year, 2022. Consider specifying a different year using the --year option."
    )
else:
    year = args.year

# Path to SQLite database
database_path = "./data/votes.sqlite"

# Fetch and preprocess data
df = polertiek.fetch_and_preprocess_data(database_path, year=year)

# Standardize the data
df_standardized = (df - df.mean()) / df.std()

# Apply PCA
pca = PCA()
pca_result = pca.fit_transform(df_standardized)

# Sort columns based on principal component loadings
sorted_columns = df.columns[pca.components_[0].argsort()]

# Reorder DataFrame columns
df_sorted = df[sorted_columns]

# Calculate the correlation matrix of the sorted DataFrame
correlation_matrix_sorted = df_sorted.corr()

# Create a heatmap using seaborn
plt.figure(figsize=(15, 12))
sns.heatmap(
    correlation_matrix_sorted,
    annot=True,
    cmap="coolwarm",
    fmt=".2f",
    linewidths=0.5,
    vmin=-1,
)
plt.title("Sorted Correlation Matrix of Party Votes")
plt.show()
