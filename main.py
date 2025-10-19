import geopandas as gpd
import matplotlib.pyplot as plt
import random
from matplotlib.patches import Patch

# ✅ Load Natural Earth GeoJSON directly (no local files)
WORLD_GEOJSON_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
)
print("Loading world map...")
world = gpd.read_file(WORLD_GEOJSON_URL)
print("Map loaded!")

# Prepare country lists
countries = list(world["NAME"].dropna())
remaining_countries = set(countries)
guessed_countries = set()

# Create figure
fig, ax = plt.subplots(figsize=(12, 6))
plt.ion()  # interactive mode
plt.show(block=False)

def draw_map(current_country=None):
    """Redraws the map with guessed (green) and current (yellow) highlights."""
    ax.clear()
    world.boundary.plot(ax=ax, linewidth=0.5, color="gray")

    # Plot guessed countries
    if guessed_countries:
        world[world["NAME"].isin(guessed_countries)].plot(ax=ax, color="limegreen", edgecolor="black")

    # Plot current country
    if current_country:
        world[world["NAME"] == current_country].plot(ax=ax, color="gold", edgecolor="black")

    # Legend + title
    legend_elements = [
        Patch(facecolor="gold", label="Current"),
        Patch(facecolor="limegreen", label="Guessed"),
    ]
    ax.legend(handles=legend_elements, loc="lower left")
    plt.title(
        f"Which country is highlighted?\nGuessed {len(guessed_countries)}/{len(countries)}",
        fontsize=13,
    )
    plt.draw()

# --- Game loop ---
while remaining_countries:
    current_country = random.choice(list(remaining_countries))
    draw_map(current_country)

    answer = input("Your guess (or 'exit' to quit): ").strip()
    if not answer or answer.lower() == "exit":
        break

    if answer.lower() == current_country.lower():
        print(f"✅ Correct! It was {current_country}.")
        guessed_countries.add(current_country)
    else:
        print(f"❌ Wrong! It was {current_country}.")

    remaining_countries.remove(current_country)

# End screen
draw_map()
plt.title(f"🎯 Game over! You guessed {len(guessed_countries)} countries correctly.")
plt.ioff()
plt.show()
