import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Polygon
import random
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Load world map ---
WORLD_GEOJSON_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
world = gpd.read_file(WORLD_GEOJSON_URL)
countries = list(world["NAME"].dropna())
remaining_countries = set(countries)
guessed_countries = set()

# --- Tkinter setup ---
root = tk.Tk()
root.title("World Countries Guessing Game")

# --- Matplotlib figure inside Tkinter ---
fig, ax = plt.subplots(figsize=(12, 6))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# Fixed axis limits
minx, miny, maxx, maxy = world.total_bounds
ax.set_xlim(minx, maxx)
ax.set_ylim(miny, maxy)
ax.set_aspect("equal")
ax.axis("off")
ax.autoscale(False)

highlight_patches = []

# Plot base boundaries once
world.boundary.plot(ax=ax, linewidth=0.5, color="lightgray", zorder=1)

# --- Helper functions ---
def draw_country_highlight(country_name, color):
    """Draw a country using Polygon patches."""
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
    for patch in highlight_patches:
        patch.remove()
    highlight_patches.clear()

    # Draw guessed countries in green
    for country in guessed_countries:
        draw_country_highlight(country, "limegreen")
    # Draw current country in gold
    if current_country:
        draw_country_highlight(current_country, "gold")

    # Legend
    legend_elements = [
        Patch(facecolor="gold", label="Current"),
        Patch(facecolor="limegreen", label="Guessed")
    ]
    ax.legend(handles=legend_elements, loc="lower left")

    # Update the title
    plt.title(f"Guessed {len(guessed_countries)}/{len(countries)} countries", fontsize=13)
    canvas.draw()

# Pick first random country
current_country = random.choice(list(remaining_countries))
draw_map(current_country)

# --- GUI input ---
def submit_guess(event=None):
    global current_country
    guess = entry.get().strip()
    entry.delete(0, tk.END)
    if not guess:
        return

    # Feedback
    if guess.lower() == current_country.lower():
        guessed_countries.add(current_country)
        feedback_label.config(text=f"✅ Correct! It was {current_country}.", fg="green")
    else:
        feedback_label.config(text=f"❌ Wrong! It was {current_country}.", fg="red")

    remaining_countries.discard(current_country)

    # Pick next country
    if remaining_countries:
        current_country = random.choice(list(remaining_countries))
        draw_map(current_country)
    else:
        draw_map()
        feedback_label.config(text=f"🎯 Game over! You guessed {len(guessed_countries)} countries correctly.", fg="blue")
        submit_button.config(state=tk.DISABLED)
        entry.config(state=tk.DISABLED)

# --- Input field and button ---
frame = tk.Frame(root)
frame.pack(side=tk.BOTTOM, fill=tk.X)

entry = tk.Entry(frame, font=("Arial", 14))
entry.pack(side=tk.LEFT, fill=tk.X, expand=1)
entry.focus()

submit_button = tk.Button(frame, text="Submit", font=("Arial", 14), command=submit_guess)
submit_button.pack(side=tk.RIGHT)

# Bind Enter key
entry.bind("<Return>", submit_guess)

# Feedback label
feedback_label = tk.Label(root, text="Guess the highlighted country", font=("Arial", 16))
feedback_label.pack(side=tk.TOP)

# Start the Tkinter main loop
root.mainloop()
