import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ✅ Load the world dataset directly from Natural Earth's GitHub
WORLD_GEOJSON_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
)

print("Loading world map from Natural Earth GitHub...")
world = gpd.read_file(WORLD_GEOJSON_URL)
print("Map data loaded successfully!")

# Setup
remaining_countries = set(world["NAME"].dropna())
guessed_countries = set()

# Draw base map
fig, ax = plt.subplots(figsize=(12, 6))
world.boundary.plot(ax=ax, linewidth=0.5, color="gray")
plt.title("Guess the Country! Type names in the console.\n(Type 'exit' to quit)", fontsize=14)
plt.tight_layout()
plt.show(block=False)

# Game loop
while remaining_countries:
    answer = input(f"{len(guessed_countries)}/{len(world)} correct. Enter a country name (or 'exit'): ").strip()
    if not answer or answer.lower() == "exit":
        break

    # Case-insensitive matching
    match = [c for c in remaining_countries if c.lower() == answer.lower()]

    if match:
        country_name = match[0]
        guessed_countries.add(country_name)
        remaining_countries.remove(country_name)

        # Highlight guessed country
        country_shape = world[world["NAME"] == country_name]
        country_shape.plot(ax=ax, color="limegreen", edgecolor="black")

        legend_elements = [Patch(facecolor="limegreen", label="Guessed")]
        ax.legend(handles=legend_elements, loc="lower left")
        plt.title(f"✅ Correct! {country_name}\n{len(guessed_countries)}/{len(world)} guessed.")
        plt.draw()
    else:
        plt.title(f"❌ '{answer}' not found. Try again.")
        plt.draw()

print(f"\nGame over! You guessed {len(guessed_countries)} countries correctly.")
plt.show()
