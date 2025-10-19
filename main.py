import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Polygon
import random

# Load world map
WORLD_GEOJSON_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
world = gpd.read_file(WORLD_GEOJSON_URL)

countries = list(world["NAME"].dropna())
remaining_countries = set(countries)
guessed_countries = set()

# Create figure
fig, ax = plt.subplots(figsize=(12, 6))

# Plot base map once
world.boundary.plot(ax=ax, linewidth=0.5, color="gray", zorder=1)

# Fixed axis limits
minx, miny, maxx, maxy = world.total_bounds
ax.set_xlim(minx, maxx)
ax.set_ylim(miny, maxy)
ax.set_aspect("equal")
ax.axis("off")
ax.autoscale(False)  # prevents autoscaling

# Store Polygon patches for highlights
highlight_patches = []

def draw_country_highlight(country_name, color):
    """Draw a country using Polygon patches instead of GeoDataFrame.plot."""
    global highlight_patches
    country = world[world["NAME"] == country_name]
    for geom in country.geometry:
        if geom.type == "Polygon":
            poly = Polygon(list(geom.exterior.coords), facecolor=color, edgecolor="black", zorder=2)
            ax.add_patch(poly)
            highlight_patches.append(poly)
        elif geom.type == "MultiPolygon":
            for part in geom.geoms:
                poly = Polygon(list(part.exterior.coords), facecolor=color, edgecolor="black", zorder=2)
                ax.add_patch(poly)
                highlight_patches.append(poly)

def draw_map(current_country=None):
    """Redraw all highlights without touching the base map."""
    # Remove previous highlight patches
    for patch in highlight_patches:
        patch.remove()
    highlight_patches.clear()

    # Draw guessed countries
    for country in guessed_countries:
        draw_country_highlight(country, "limegreen")

    # Draw current country
    if current_country:
        draw_country_highlight(current_country, "gold")

    # Legend
    legend_elements = [
        Patch(facecolor="gold", label="Current"),
        Patch(facecolor="limegreen", label="Guessed")
    ]
    ax.legend(handles=legend_elements, loc="lower left")
    plt.title(f"Which country is highlighted?\nGuessed {len(guessed_countries)}/{len(countries)}", fontsize=13)

    fig.canvas.draw()
    fig.canvas.flush_events()

# --- Game loop ---
plt.ion()
plt.show(block=False)

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

# Final map
draw_map()
plt.title(f"🎯 Game over! You guessed {len(guessed_countries)} countries correctly.")
plt.ioff()
plt.show()
