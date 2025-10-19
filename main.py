
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Polygon
import random
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import signal
import sys

# --- Load world map ---
WORLD_GEOJSON_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
world = gpd.read_file(WORLD_GEOJSON_URL)
countries = list(world["NAME"].dropna())
remaining_countries = set(countries)
guessed_countries = set()


# --- Tkinter setup ---
root = tk.Tk()
root.title("World Countries Guessing Game")
root.geometry("1200x700")  # default window size


# --- Handle Ctrl+C and window close instantly ---
def _exit_on_sigint(signum, frame):
    root.destroy()
    sys.exit(0)
signal.signal(signal.SIGINT, _exit_on_sigint)

def _exit_on_close():
    root.destroy()
    sys.exit(0)
root.protocol("WM_DELETE_WINDOW", _exit_on_close)

# --- Matplotlib figure inside Tkinter ---
fig, ax = plt.subplots(figsize=(12, 6))
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)  # remove extra figure padding
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# Fixed axis limits
minx, miny, maxx, maxy = world.total_bounds
ax.set_xlim(minx, maxx)
ax.set_ylim(miny, maxy)
ax.set_aspect("equal")
ax.axis("off")
ax.autoscale(False)
ax.margins(0)  # remove extra margins

highlight_patches = []

# Plot base boundaries once (light gray)
world.boundary.plot(ax=ax, linewidth=0.5, color="lightgray", zorder=1)

# --- Helper functions ---
def draw_country_highlight(country_name, color):
    country = world[world["NAME"] == country_name]
    for geom in country.geometry:
        if geom.geom_type == "Polygon":
            poly = Polygon(list(geom.exterior.coords), facecolor=color, edgecolor="black", zorder=2)
            ax.add_patch(poly)
            highlight_patches.append(poly)
        elif geom.geom_type == "MultiPolygon":
            for part in geom.geoms:
                poly = Polygon(list(part.exterior.coords), facecolor=color, edgecolor="black", zorder=2)
                ax.add_patch(poly)
                highlight_patches.append(poly)

def draw_map(current_country=None):
    for patch in highlight_patches:
        patch.remove()
    highlight_patches.clear()

    for country in guessed_countries:
        draw_country_highlight(country, "limegreen")
    if current_country:
        draw_country_highlight(current_country, "gold")

    # Legend
    legend_elements = [
        Patch(facecolor="gold", label="Current"),
        Patch(facecolor="limegreen", label="Guessed")
    ]
    ax.legend(handles=legend_elements, loc="lower left")
    canvas.draw()

# Pick first random country
current_country = random.choice(list(remaining_countries))
draw_map(current_country)

# --- Input field, button, and feedback ---
bottom_frame = tk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

# Center-aligned feedback text
feedback_label = tk.Label(bottom_frame, text="Guess the highlighted country", font=("Arial", 16))
feedback_label.pack(side=tk.TOP, pady=2)
feedback_label.pack_configure(anchor="center")  # center alignment

entry_frame = tk.Frame(bottom_frame)
entry_frame.pack(side=tk.TOP, fill=tk.X)

entry = tk.Entry(entry_frame, font=("Arial", 14))
entry.pack(side=tk.LEFT, fill=tk.X, expand=1)
entry.focus()

def submit_guess(event=None):
    global current_country
    guess = entry.get().strip()
    entry.delete(0, tk.END)
    if not guess:
        # Skip current country
        feedback_label.config(text=f"⏭️ Skipped! It was {current_country}.", fg="orange")
        remaining_countries.discard(current_country)
        if remaining_countries:
            current_country = random.choice(list(remaining_countries))
            draw_map(current_country)
        else:
            draw_map()
            feedback_label.config(text=f"🎯 Game over! You guessed {len(guessed_countries)} countries correctly.", fg="blue")
            submit_button.config(state=tk.DISABLED)
            entry.config(state=tk.DISABLED)
        return

    # Feedback
    if guess.lower() == current_country.lower():
        guessed_countries.add(current_country)
        feedback_label.config(text=f"✅ Correct! It was {current_country}.", fg="green")
    else:
        feedback_label.config(text=f"❌ Wrong! It was {current_country}.", fg="red")

    remaining_countries.discard(current_country)

    if remaining_countries:
        current_country = random.choice(list(remaining_countries))
        draw_map(current_country)
    else:
        draw_map()
        feedback_label.config(text=f"🎯 Game over! You guessed {len(guessed_countries)} countries correctly.", fg="blue")
        submit_button.config(state=tk.DISABLED)
        entry.config(state=tk.DISABLED)

submit_button = tk.Button(entry_frame, text="Submit", font=("Arial", 14), command=submit_guess)
submit_button.pack(side=tk.RIGHT)

entry.bind("<Return>", submit_guess)

# --- Start Tkinter loop ---
root.mainloop()
