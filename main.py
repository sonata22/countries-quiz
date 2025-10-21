import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Polygon, Rectangle
import random
import tkinter as tk
import tkinter.ttk as ttk  # ADDED
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import signal
import sys
import pycountry
import requests
from PIL import Image
import io


# --- Load world map ---
WORLD_GEOJSON_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
world = gpd.read_file(WORLD_GEOJSON_URL)
countries = list(world["NAME"].dropna())
remaining_countries = set(countries)
guessed_countries = set()


# --- Tkinter setup ---
root = tk.Tk()
root.title("World Countries Guessing Game")
root.geometry("1200x700")
root.configure(bg="#f5f5f5")  # MODERN BG

# --- Modern ttk style ---
style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame", background="#f5f5f5")
style.configure("TLabel", background="#f5f5f5", font=("Segoe UI", 16))
style.configure("TButton", font=("Segoe UI", 14), padding=6)
style.configure("TEntry", font=("Segoe UI", 14), padding=6)


# --- Handle Ctrl+C and window close instantly ---
def _exit_on_sigint(signum, frame):
    root.destroy()
    sys.exit(0)


signal.signal(signal.SIGINT, _exit_on_sigint)


def _exit_on_close():
    root.destroy()
    sys.exit(0)


root.protocol("WM_DELETE_WINDOW", _exit_on_close)

# --- Header ---
header_frame = ttk.Frame(root)
header_frame.pack(side=tk.TOP, fill=tk.X, pady=(20, 10))
header_label = ttk.Label(
    header_frame, text="🌍 World Countries Quiz", font=("Segoe UI", 24, "bold")
)
header_label.pack(anchor="center")

# --- Matplotlib figure inside Tkinter ---
fig, ax = plt.subplots(figsize=(12, 6))
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=20, pady=10)

# Fixed axis limits
minx, miny, maxx, maxy = world.total_bounds
ax.set_xlim(minx, maxx)
ax.set_ylim(miny, maxy)
ax.set_aspect("equal")
ax.axis("off")
ax.autoscale(False)
ax.margins(0)
ax.set_facecolor("#b3d1ff")

highlight_patches = []

# Plot base boundaries once (dark gray)
world.boundary.plot(ax=ax, linewidth=0.5, color="dimgray", zorder=1)

# --- Input field, button, and feedback ---
bottom_frame = ttk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

# Center-aligned feedback text
feedback_label = ttk.Label(
    bottom_frame, text="Guess the highlighted country", font=("Segoe UI", 16)
)
feedback_label.pack(side=tk.TOP, pady=8, anchor="center")

entry_frame = ttk.Frame(bottom_frame)
entry_frame.pack(side=tk.TOP, fill=tk.X, padx=20)

entry = ttk.Entry(entry_frame, font=("Segoe UI", 14))
entry.pack(side=tk.LEFT, fill=tk.X, expand=1, padx=(0, 10))
entry.focus()


# --- Helper functions ---
def draw_country_highlight(country_name, color):
    country = world[world["NAME"] == country_name]
    for geom in country.geometry:
        if geom.geom_type == "Polygon":
            poly = Polygon(
                list(geom.exterior.coords),
                facecolor=color,
                edgecolor="dimgray",
                zorder=2,
            )
            ax.add_patch(poly)
            highlight_patches.append(poly)
        elif geom.geom_type == "MultiPolygon":
            for part in geom.geoms:
                poly = Polygon(
                    list(part.exterior.coords),
                    facecolor=color,
                    edgecolor="dimgray",
                    zorder=2,
                )
                ax.add_patch(poly)
                highlight_patches.append(poly)


def get_flag_image(country_name):
    """Return a PIL image of the flag for the given country name, or None if not found."""
    try:
        country = pycountry.countries.lookup(country_name)
        code = country.alpha_2.lower()
        url = f"https://flagcdn.com/w80/{code}.png"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        img = img.resize((80, 48), Image.Resampling.LANCZOS)
        return img
    except Exception:
        return None


def update_counter():
    guessed = len(guessed_countries)
    total = len(countries)
    root.title(f"World Countries Guessing Game ({guessed}/{total})")


def draw_map(current_country=None):
    for patch in highlight_patches:
        patch.remove()
    highlight_patches.clear()

    # Draw ocean background as a large blue rectangle
    ocean_rect = Rectangle(
        (minx, miny),
        maxx - minx,
        maxy - miny,
        facecolor="#b3d1ff",
        edgecolor=None,
        zorder=0,
    )
    ax.add_patch(ocean_rect)
    highlight_patches.append(ocean_rect)

    for country in guessed_countries:
        draw_country_highlight(country, "limegreen")
    if current_country:
        draw_country_highlight(current_country, "gold")
    # Draw flag overlay on map (bottom right corner, no margins)
    if current_country:
        flag_img = get_flag_image(current_country)
        if flag_img:
            try:
                import numpy as np
            except ImportError:
                np = None
            if np:
                flag_np = np.array(flag_img)
                flag_width = (maxx - minx) * 0.12
                flag_height = (maxy - miny) * 0.12
                ax.imshow(
                    flag_np,
                    extent=[maxx - flag_width, maxx, miny, miny + flag_height],
                    zorder=100,
                )
    # Legend
    legend_elements = [
        Patch(facecolor="gold", label="Current"),
        Patch(facecolor="limegreen", label="Guessed"),
    ]
    ax.legend(handles=legend_elements, loc="lower left")
    canvas.draw()
    update_counter()


# Pick first random country
current_country = random.choice(list(remaining_countries))
draw_map(current_country)


def end_game():
    draw_map()
    feedback_label.config(
        text=f"🎯 Game over! You guessed {len(guessed_countries)} countries correctly.",
        foreground="blue",  # ttk uses 'foreground'
    )
    submit_button.config(state=tk.DISABLED)
    entry.config(state=tk.DISABLED)
    update_counter()


def submit_guess(event=None):
    global current_country
    guess = entry.get().strip()
    entry.delete(0, tk.END)
    if not guess:
        feedback_label.config(
            text=f"⏭️ Skipped! It was {current_country}.", foreground="orange"
        )
        remaining_countries.discard(current_country)
        if remaining_countries:
            current_country = random.choice(list(remaining_countries))
            draw_map(current_country)
        else:
            end_game()
        return

    if guess.lower() == current_country.lower():
        guessed_countries.add(current_country)
        feedback_label.config(
            text=f"✅ Correct! It was {current_country}.", foreground="green"
        )
    else:
        feedback_label.config(
            text=f"❌ Wrong! It was {current_country}.", foreground="red"
        )

    remaining_countries.discard(current_country)

    if remaining_countries:
        current_country = random.choice(list(remaining_countries))
        draw_map(current_country)
    else:
        end_game()
    update_counter()


submit_button = ttk.Button(entry_frame, text="Submit", command=submit_guess)
submit_button.pack(side=tk.RIGHT)

entry.bind("<Return>", submit_guess)

# --- Start Tkinter loop ---
root.mainloop()
