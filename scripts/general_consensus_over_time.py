import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from scipy.cluster import hierarchy
import seaborn as sns
import matplotlib.pyplot as plt
import polertiek
import mplcursors

# Connect to the SQLite database
database_path = "./data/votes.sqlite"

# Create a DataFrame from the results
(
    consensus_per_quarter,
    party_agreement,
) = polertiek.fetch_and_preprocess_consensus_data(
    database_path, start_year=2012
)

# Customize the x-axis ticks
n = 4  # Display every n-th quarter
selected_quarters = consensus_per_quarter["quarter"][::n]


# Plot the time series
plt.figure(figsize=(12, 6))
plt.plot(
    consensus_per_quarter["quarter"],
    consensus_per_quarter["consensus"],
    label="Total Consensus",
)
plt.xticks(
    selected_quarters, rotation=45
)  # Rotate labels for better readability

plt.xlabel("Jaar")
plt.ylabel("Consensus als gemiddelde correlatie")
plt.title("Consensus tussen alle parrtijen over de jaren")
plt.legend()
plt.show()


# Plot
fig, ax = plt.subplots()
lines = ax.plot(party_agreement)
plt.xticks(
    selected_quarters, rotation=45
)  # Rotate labels for better readability

# Add labels and title
ax.set_xlabel("Jaar")
ax.set_ylabel("Overeenkomst met andere partijen")
ax.set_title("Overeenkomst met andere partijen over de jaren")

# Enable tooltips on hover using mplcursors
cursor = mplcursors.cursor(hover=True)


# Add custom highlight for displaying DataFrame labels (party names)
@cursor.connect("add")
def on_add(sel):
    artist = sel.artist
    x, y = sel.target
    party_index = lines.index(artist)
    label = party_agreement.columns[party_index]
    sel.annotation.set_text(f"{label}: {y:.2%}")


# Show the plot
plt.show()
