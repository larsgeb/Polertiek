# plot.py
import argparse
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from scipy.cluster import hierarchy

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
sorted_columns_PCA = df.columns[pca.components_[0].argsort()]

# Hierarchical clustering
linkage_matrix = hierarchy.linkage(df_standardized.T, method="ward")

# Get the order of columns based on clustering
dendrogram = hierarchy.dendrogram(linkage_matrix, no_plot=True)
sorted_columns_hierarchy = df.columns[dendrogram["leaves"]]

# Create subplots
fig, axes = plt.subplots(1, 2, figsize=(24, 12))

# Plot PCA-based sorting
sns.heatmap(
    df[sorted_columns_PCA].corr(),
    annot=True,
    cmap="coolwarm",
    fmt=".2f",
    linewidths=0.5,
    vmin=-1,
    ax=axes[0],
    square=True,  # Ensure square axes
)
axes[0].set_title("PCA Sorted Correlations")

# Plot hierarchical clustering-based sorting
sns.heatmap(
    df[sorted_columns_hierarchy].corr(),
    annot=True,
    cmap="coolwarm",
    fmt=".2f",
    linewidths=0.5,
    vmin=-1,
    ax=axes[1],
    square=True,  # Ensure square axes
)
axes[1].set_title("Hierarchical Clustering Sorted Correlations")

plt.show()
