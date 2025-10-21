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

highlight_patches = []

minx, miny, maxx, maxy = world.total_bounds

DEFAULT_XLIM = (minx, maxx)
DEFAULT_YLIM = (miny, maxy)


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


# --- Matplotlib figure inside Tkinter ---
fig, ax = plt.subplots(figsize=(12, 6))
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

# Set default zoom to fit the map to the window width
ax.set_xlim(minx, maxx)
ax.set_ylim(miny, maxy)
ax.set_aspect("equal")
ax.axis("off")
ax.autoscale(False)
ax.margins(0)
ax.set_facecolor("#b3d1ff")

# Draw country borders for visibility
world.boundary.plot(ax=ax, linewidth=0.5, color="dimgray", zorder=1)

# --- Input field, button, feedback, and flag moved to the right of the map ---

# --- Layout: map and controls in separate columns ---

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=1)

# Left column: map
map_frame = ttk.Frame(main_frame)
map_frame.grid(row=0, column=0, sticky="nsew")
main_frame.columnconfigure(0, weight=3)
main_frame.rowconfigure(0, weight=1)

canvas = FigureCanvasTkAgg(fig, master=map_frame)
canvas.get_tk_widget().pack(
    fill=tk.BOTH, expand=1, padx=0, pady=0
)  # No padding for map

# Right column: controls (fixed width)
controls_frame = ttk.Frame(main_frame, width=300)
controls_frame.grid(
    row=0, column=1, sticky="ns", padx=10, pady=10
)  # <-- Remove horizontal padding
main_frame.columnconfigure(1, weight=0)  # Prevent stretching

controls_frame.pack_propagate(False)  # Prevent shrinking when window is resized

feedback_label = ttk.Label(
    controls_frame, text="Guess the highlighted country", font=("Segoe UI", 16)
)
feedback_label.pack(side=tk.TOP, pady=8, anchor="center")

entry_frame = ttk.Frame(controls_frame)
entry_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

entry = ttk.Entry(entry_frame, font=("Segoe UI", 14))
entry.pack(side=tk.TOP, fill=tk.X, expand=1, padx=0)  # Remove left padding


def submit_guess(event=None):
    global current_country
    guess = entry.get().strip()
    entry.delete(0, tk.END)
    reset_map_zoom()
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
submit_button.pack(side=tk.TOP, fill=tk.X, expand=1, pady=(10, 0))

entry.bind("<Return>", submit_guess)


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


def reset_map_zoom():
    ax.set_xlim(DEFAULT_XLIM)
    ax.set_ylim(DEFAULT_YLIM)
    ax.set_aspect("equal")
    ax.autoscale(False)
    ax.margins(0)
    canvas.draw()


# --- Mouse wheel zoom at cursor position ---
def on_mouse_wheel(event):
    widget = canvas.get_tk_widget()
    # Only zoom if the mouse is over the map canvas and this is a real scroll event
    if widget.winfo_containing(event.x_root, event.y_root) == widget:
        x_pixel = event.x
        y_pixel = event.y

        inv = ax.transData.inverted()
        xdata, ydata = inv.transform((x_pixel, y_pixel))

        # Only zoom once per event
        if hasattr(event, "delta"):
            factor = 0.8 if event.delta > 0 else 1.25
        elif hasattr(event, "num"):
            factor = 0.8 if event.num == 4 else 1.25
        else:
            factor = 1.0

        zoom(factor, center=(xdata, ydata))


# Bind mouse wheel to zoom at cursor
canvas.get_tk_widget().bind("<MouseWheel>", on_mouse_wheel)  # Windows/macOS
canvas.get_tk_widget().bind("<Button-4>", on_mouse_wheel)  # Linux scroll up
canvas.get_tk_widget().bind("<Button-5>", on_mouse_wheel)  # Linux scroll down

# --- Drag to pan functionality ---
_drag_data = {"x": None, "y": None, "xlim": None, "ylim": None, "dragging": False}


def on_mouse_press(event):
    # Only start drag if left mouse button and not zoomed out to default
    if event.num == 1 or (hasattr(event, "button") and event.button == 1):
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        # Only allow drag if zoomed in
        if cur_xlim != DEFAULT_XLIM or cur_ylim != DEFAULT_YLIM:
            _drag_data["x"] = event.x
            _drag_data["y"] = event.y
            _drag_data["xlim"] = cur_xlim
            _drag_data["ylim"] = cur_ylim
            _drag_data["dragging"] = True


def on_mouse_release(event):
    _drag_data["dragging"] = False


def on_mouse_motion(event):
    if _drag_data["dragging"]:
        # Convert pixel movement to data coordinates
        inv = ax.transData.inverted()
        x0, y0 = inv.transform((_drag_data["x"], _drag_data["y"]))
        x1, y1 = inv.transform((event.x, event.y))
        delta_x = x0 - x1
        delta_y = y1 - y0  # REVERSED vertical direction

        # Calculate new limits
        new_xlim = (_drag_data["xlim"][0] + delta_x, _drag_data["xlim"][1] + delta_x)
        new_ylim = (_drag_data["ylim"][0] + delta_y, _drag_data["ylim"][1] + delta_y)

        # Clamp to default bounds
        x_range = new_xlim[1] - new_xlim[0]
        y_range = new_ylim[1] - new_ylim[0]

        # Prevent panning if at maximum zoom in (minimum range)
        min_x_range = (DEFAULT_XLIM[1] - DEFAULT_XLIM[0]) / 3.0
        min_y_range = (DEFAULT_YLIM[1] - DEFAULT_YLIM[0]) / 3.0
        if abs(x_range - min_x_range) < 1e-8 and abs(y_range - min_y_range) < 1e-8:
            # If at max zoom in, clamp to center
            center_x = (DEFAULT_XLIM[0] + DEFAULT_XLIM[1]) / 2
            center_y = (DEFAULT_YLIM[0] + DEFAULT_YLIM[1]) / 2
            new_xlim = (center_x - min_x_range / 2, center_x + min_x_range / 2)
            new_ylim = (center_y - min_y_range / 2, center_y + min_y_range / 2)
        else:
            # Clamp to default bounds as usual
            if new_xlim[0] < DEFAULT_XLIM[0]:
                new_xlim = (DEFAULT_XLIM[0], DEFAULT_XLIM[0] + x_range)
            if new_xlim[1] > DEFAULT_XLIM[1]:
                new_xlim = (DEFAULT_XLIM[1] - x_range, DEFAULT_XLIM[1])
            if new_ylim[0] < DEFAULT_YLIM[0]:
                new_ylim = (DEFAULT_YLIM[0], DEFAULT_YLIM[0] + y_range)
            if new_ylim[1] > DEFAULT_YLIM[1]:
                new_ylim = (DEFAULT_YLIM[1] - y_range, DEFAULT_YLIM[1])

        ax.set_xlim(new_xlim)
        ax.set_ylim(new_ylim)
        ax.set_aspect("equal")
        ax.autoscale(False)
        ax.margins(0)
        canvas.draw()


# Bind mouse events for drag-to-pan
canvas.get_tk_widget().bind("<ButtonPress-1>", on_mouse_press)
canvas.get_tk_widget().bind("<ButtonRelease-1>", on_mouse_release)
canvas.get_tk_widget().bind("<B1-Motion>", on_mouse_motion)


# --- Add this zoom function ---
def zoom(factor, center=None):
    cur_xlim = ax.get_xlim()
    cur_ylim = ax.get_ylim()
    default_x_range = DEFAULT_XLIM[1] - DEFAULT_XLIM[0]
    default_y_range = DEFAULT_YLIM[1] - DEFAULT_YLIM[0]
    aspect = default_y_range / default_x_range

    if center is None:
        x_center = (cur_xlim[0] + cur_xlim[1]) / 2
        y_center = (cur_ylim[0] + cur_ylim[1]) / 2
    else:
        x_center, y_center = center

    x_range = cur_xlim[1] - cur_xlim[0]
    new_x_range = x_range * factor
    new_y_range = new_x_range * aspect

    # Prevent zooming in beyond 300% (minimum range)
    min_x_range = default_x_range / 3.0
    min_y_range = default_y_range / 3.0
    if new_x_range < min_x_range or new_y_range < min_y_range:
        new_xlim = cur_xlim
        new_ylim = cur_ylim
    elif new_x_range >= default_x_range or new_y_range >= default_y_range:
        new_xlim = DEFAULT_XLIM
        new_ylim = DEFAULT_YLIM
    else:
        new_xlim = (x_center - new_x_range / 2, x_center + new_x_range / 2)
        new_ylim = (y_center - new_y_range / 2, y_center + new_y_range / 2)

        # Clamp to default bounds as usual
        if new_xlim[0] < DEFAULT_XLIM[0]:
            shift = DEFAULT_XLIM[0] - new_xlim[0]
            new_xlim = (DEFAULT_XLIM[0], new_xlim[1] + shift)
        if new_xlim[1] > DEFAULT_XLIM[1]:
            shift = new_xlim[1] - DEFAULT_XLIM[1]
            new_xlim = (new_xlim[0] - shift, DEFAULT_XLIM[1])
        if new_ylim[0] < DEFAULT_YLIM[0]:
            shift = DEFAULT_YLIM[0] - new_ylim[0]
            new_ylim = (DEFAULT_YLIM[0], new_ylim[1] + shift)
        if new_ylim[1] > DEFAULT_YLIM[1]:
            shift = new_ylim[1] - DEFAULT_YLIM[1]
            new_ylim = (new_ylim[0] - shift, DEFAULT_YLIM[1])

    ax.set_xlim(new_xlim)
    ax.set_ylim(new_ylim)
    ax.set_aspect("equal")
    ax.autoscale(False)
    ax.margins(0)
    canvas.draw()


# --- Start Tkinter loop ---
root.mainloop()
