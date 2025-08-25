import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import math
import json
import os

chunks = []
selected_chunk_index = None  # Track the selected chunk index
preview_chunk = None  # Track the preview chunk coordinates

# Variables for zoom and pan
zoom_level = 1.0
pan_offset_x = 0
pan_offset_y = 0
is_panning = False
last_x = 0
last_y = 0
chunk_size = 5

ZOOM_IN_LIMIT = 200.0
VERSION_NUMBER = 1.0

# Simplified continent outlines for world map
# Format: List of [longitude, latitude] coordinates
world_map_data = {
    "africa": [
        [18.5, 35.0], [51.5, 12.0], [42.5, -12.0], [33.0, -34.0], [17.0, -34.0],
        [-17.0, 14.0], [-12.0, 32.0], [-6.0, 36.0], [18.5, 35.0]
    ],
    "europe": [
        [-11.0, 36.0], [-9.0, 42.0], [9.0, 60.0], [32.0, 70.0], [45.0, 60.0],
        [41.0, 44.0], [28.0, 41.0], [18.5, 35.0], [-6.0, 36.0], [-11.0, 36.0]
    ],
    "asia": [
        [28.0, 41.0], [41.0, 44.0], [60.0, 55.0], [150.0, 60.0], [150.0, 45.0],
        [145.0, 30.0], [120.0, 20.0], [98.0, 5.0], [77.0, 6.0], [60.0, 20.0],
        [51.5, 12.0], [18.5, 35.0], [28.0, 41.0]
    ],
    "north_america": [
        [-168.0, 65.0], [-120.0, 30.0], [-90.0, 30.0], [-83.0, 10.0], [-79.0, 25.0],
        [-60.0, 50.0], [-50.0, 65.0], [-168.0, 65.0]
    ],
    "south_america": [
        [-83.0, 10.0], [-78.0, -5.0], [-70.0, -55.0], [-55.0, -55.0], [-35.0, -5.0],
        [-50.0, 10.0], [-79.0, 25.0], [-83.0, 10.0]
    ],
    "australia": [
        [114.0, -33.0], [153.0, -28.0], [150.0, -38.0], [115.0, -35.0], [114.0, -33.0]
    ],
    "antarctica": [
        [-180.0, -60.0], [-180.0, -85.0], [180.0, -85.0], [180.0, -60.0], [-180.0, -60.0]
    ]
}

def load_chunks():
    global chunks
    try:
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as file:
                chunks = json.load(file)
            messagebox.showinfo("Loaded", "Chunks loaded successfully.")
            draw_chunks()
            status_label.config(text=f"Loaded {len(chunks)} chunks from {os.path.basename(file_path)}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load chunks: {str(e)}")

def save_chunks():
    global chunks
    try:
        if not chunks:
            messagebox.showinfo("Info", "No chunks to save.")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(chunks, file)
            messagebox.showinfo("Saved", "Chunks saved successfully.")
            status_label.config(text=f"Saved {len(chunks)} chunks to {os.path.basename(file_path)}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save chunks: {str(e)}")

def snap_to_grid(value, grid_size):
    return round(value / grid_size) * grid_size

def delete_selected_chunk():
    global chunks, selected_chunk_index
    if selected_chunk_index is not None:
        if messagebox.askyesno("Confirm", "Delete selected chunk?"):
            del chunks[selected_chunk_index]
            selected_chunk_index = None
            draw_chunks()
            status_label.config(text="Chunk deleted")
    else:
        messagebox.showinfo("Info", "No chunk selected")

def draw_world_map():
    """Draw a simplified world map outline"""
    for continent, points in world_map_data.items():
        # Convert all points to canvas coordinates
        canvas_points = []
        for lon, lat in points:
            x, y = lon_lat_to_canvas(lon, lat)
            canvas_points.append(x)
            canvas_points.append(y)
            
        # Draw the continent outline
        if canvas_points:
            canvas.create_polygon(canvas_points, outline="#AAAAAA", fill="#F5F5F5", 
                                 width=1, smooth=True, tags="map")

def create_info_panel():
    global info_panel
    info_panel = ttk.LabelFrame(root, text="Chunk Information")
    info_panel.grid(row=1, column=1, padx=10, pady=10, sticky="new")
    
    global chunk_info_label, chunk_area_label
    chunk_info_label = ttk.Label(info_panel, text="No chunk selected")
    chunk_info_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
    
    chunk_area_label = ttk.Label(info_panel, text="")
    chunk_area_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    
    ttk.Button(info_panel, text="Center on Chunk", 
              command=center_on_selected_chunk).grid(
              row=2, column=0, padx=10, pady=5, sticky="w")

def set_theme():
    style = ttk.Style()
    
    # Configure a custom theme - you can expand this
    style.configure("TButton", padding=6, relief="flat", background="#ccc")
    style.configure("TLabel", padding=3)
    style.configure("TFrame", padding=5)
    style.configure("TLabelframe", padding=10)
    style.configure("TLabelframe.Label", font=("Arial", 10, "bold"))

    # Create some accent colors for different states
    style.map("TButton",
        foreground=[('pressed', 'blue'), ('active', 'blue')],
        background=[('pressed', '!disabled', '#aaa'), ('active', '#ddd')]
    )

def update_info_panel():
    if selected_chunk_index is None:
        chunk_info_label.config(text="No chunk selected")
        chunk_area_label.config(text="")
    else:
        chunk = chunks[selected_chunk_index]
        chunk_info_label.config(text=f"Chunk #{selected_chunk_index + 1}")
        # Calculate area in square km (approximate)
        lat_diff = abs(chunk['max_lat'] - chunk['min_lat'])
        lon_diff = abs(chunk['max_lon'] - chunk['min_lon'])
        area_km2 = lat_diff * 111 * lon_diff * 111 * math.cos(math.radians((chunk['max_lat'] + chunk['min_lat'])/2))
        chunk_area_label.config(text=f"Area: ~{area_km2:.2f} km²")

def center_on_selected_chunk():
    if selected_chunk_index is not None:
        chunk = chunks[selected_chunk_index]
        center_lat = (chunk['min_lat'] + chunk['max_lat']) / 2 # Center latitude
        center_lon = (chunk['min_lon'] + chunk['max_lon']) / 2 # Center longitude
        go_to_location(center_lat, center_lon)

def calculate_area():
    global chunks, preview_chunk
    try:
        min_lat = float(entry_min_lat.get())
        min_lon = float(entry_min_lon.get())

        # Snap to grid
        min_lat = snap_to_grid(min_lat, chunk_size / 111)
        min_lon = snap_to_grid(min_lon, chunk_size / (111 * math.cos(math.radians(min_lat))))

        # Calculate degrees per km
        degree_per_km_lat = 1 / 111
        degree_per_km_lon = 1 / (111 * math.cos(math.radians(min_lat)))

        # Calculate max latitude and longitude for a 5km x 5km square
        max_lat = min_lat + (chunk_size * degree_per_km_lat)
        max_lon = min_lon + (chunk_size * degree_per_km_lon)

        # Check for overlap
        for chunk in chunks:
            if (min_lat == chunk['min_lat'] and min_lon == chunk['min_lon']):
                messagebox.showinfo("Overlap", "This chunk was already generated.")
                return

        # Store the chunk
        chunks.append({
            'min_lat': min_lat,
            'max_lat': max_lat,
            'min_lon': min_lon,
            'max_lon': max_lon
        })

        # Clear the preview now that we've created the actual chunk
        preview_chunk = None

        # Display the calculated values with clickable labels
        label_min_lat_val.config(text=f"{min_lat}")
        label_max_lat_val.config(text=f"{max_lat}")
        label_min_lon_val.config(text=f"{min_lon}")
        label_max_lon_val.config(text=f"{max_lon}")

        status_label.config(text=f"Created chunk: ({min_lat}, {min_lon}) to ({max_lat}, {max_lon})")
        draw_chunks()
    except ValueError:
        messagebox.showerror("Error", "Please enter valid numeric values for latitude and longitude.")

def copy_to_clipboard(value):
    root.clipboard_clear()
    root.clipboard_append(value)
    status_label.config(text=f"Copied to clipboard: {value}")

def draw_chunks():
    canvas.delete("all")
    
    # First, draw the world map
    draw_world_map()
    
    # Then draw a grid for reference
    draw_grid()
    
    # Draw preview chunk if exists
    if preview_chunk:
        min_lat = preview_chunk['min_lat']
        min_lon = preview_chunk['min_lon']
        max_lat = preview_chunk['max_lat']
        max_lon = preview_chunk['max_lon']
        x1, y1 = lon_lat_to_canvas(min_lon, min_lat)
        x2, y2 = lon_lat_to_canvas(max_lon, max_lat)
        
        # Draw preview chunk with blue dashed outline
        canvas.create_rectangle(x1, y1, x2, y2, 
                             fill="#ADD8E6", 
                             outline="#0000FF",
                             width=2,
                             dash=(5, 3),
                             stipple="gray50",
                             tags="preview")
    
    # Draw all existing chunks
    for i, chunk in enumerate(chunks):
        min_lat = chunk['min_lat']
        min_lon = chunk['min_lon']
        max_lat = chunk['max_lat']
        max_lon = chunk['max_lon']
        x1, y1 = lon_lat_to_canvas(min_lon, min_lat)
        x2, y2 = lon_lat_to_canvas(max_lon, max_lat)
        
        # Make the selection more noticeable with a different color scheme
        if i == selected_chunk_index:
            fill_color = "#4682B4"  # Steel blue for selected chunk
            outline_color = "red"
            outline_width = 3
            fill_alpha = 0.8  # More opaque for selected
        else:
            fill_color = "#ADD8E6"  # Light blue for unselected chunks
            outline_color = "black" 
            outline_width = 1
            fill_alpha = 0.5  # Semi-transparent
            
        # Create chunk rectangle with partial transparency to see map underneath
        chunk_id = canvas.create_rectangle(x1, y1, x2, y2, 
                               fill=fill_color, 
                               outline=outline_color, 
                               width=outline_width,
                               stipple="gray50",  # Makes the fill semi-transparent
                               tags=f"chunk_{i}")
        
        # Add a label to show coordinates in the chunk
        text_color = "white" if i == selected_chunk_index else "black"
        canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, 
                          text=f"{i+1}", 
                          fill=text_color,
                          font=("Arial", 10, "bold"))
        
        # Bind tooltip event to show coordinates on hover
        canvas.tag_bind(f"chunk_{i}", "<Enter>", 
                       lambda e, lat=min_lat, lon=min_lon: 
                       status_label.config(text=f"Chunk at ({lat}, {lon})"))
        canvas.tag_bind(f"chunk_{i}", "<Leave>", 
                       lambda e: status_label.config(text=""))

def draw_grid():
    # Draw faint grid lines to help with visualization
    grid_spacing = 50 * zoom_level
    
    # Calculate visible area considering pan offset
    start_x = -pan_offset_x
    end_x = canvas_width - pan_offset_x
    start_y = -pan_offset_y
    end_y = canvas_height - pan_offset_y
    
    # Draw longitude lines (vertical)
    for x in range(int(start_x // grid_spacing) * int(grid_spacing), 
                  int(end_x + grid_spacing), int(max(10, grid_spacing))):
        x_pos = x + pan_offset_x
        canvas.create_line(x_pos, 0, x_pos, canvas_height, fill="#EEEEEE", tags="grid")
        
        # Add longitude labels at bottom
        if zoom_level > 0.5:  # Only show labels when zoomed in enough
            lon = canvas_to_lon_lat(x_pos, canvas_height)[0]
            if abs(lon) < 180 and abs(round(lon) - lon) < 0.1:  # Only label near whole numbers
                canvas.create_text(x_pos, canvas_height - 10, 
                                  text=f"{round(lon)}°", fill="#888888", 
                                  font=("Arial", 8), tags="grid")
    
    # Draw latitude lines (horizontal)
    for y in range(int(start_y // grid_spacing) * int(grid_spacing), 
                  int(end_y + grid_spacing), int(max(10, grid_spacing))):
        y_pos = y + pan_offset_y
        canvas.create_line(0, y_pos, canvas_width, y_pos, fill="#EEEEEE", tags="grid")
        
        # Add latitude labels at right edge
        if zoom_level > 0.5:  # Only show labels when zoomed in enough
            lat = canvas_to_lon_lat(canvas_width, y_pos)[1]
            if abs(lat) < 90 and abs(round(lat) - lat) < 0.1:  # Only label near whole numbers
                canvas.create_text(canvas_width - 20, y_pos, 
                                  text=f"{round(lat)}°", fill="#888888", 
                                  font=("Arial", 8), tags="grid")
    
    # Draw main axes with consideration for pan offset
    center_x = (canvas_width / 2) * zoom_level + pan_offset_x
    center_y = (canvas_height / 2) * zoom_level + pan_offset_y
    canvas.create_line(center_x, 0, center_x, canvas_height, fill="#AAAAAA", width=2, dash=(4, 4), tags="grid")
    canvas.create_line(0, center_y, canvas_width, center_y, fill="#AAAAAA", width=2, dash=(4, 4), tags="grid")

def create_coordinate_display():
    coord_frame = ttk.LabelFrame(root, text="Map Coordinates")
    coord_frame.grid(row=0, column=1, padx=10, pady=10, sticky="new")
    
    global coord_label
    coord_label = ttk.Label(coord_frame, text="Hover over map to see coordinates")
    coord_label.grid(row=0, column=0, padx=10, pady=5)
    
    # Add search functionality
    ttk.Label(coord_frame, text="Search Coordinates:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    
    search_frame = ttk.Frame(coord_frame)
    search_frame.grid(row=2, column=0, padx=5, pady=5)
    
    ttk.Label(search_frame, text="Lat:").grid(row=0, column=0)
    search_lat = ttk.Entry(search_frame, width=10)
    search_lat.grid(row=0, column=1, padx=2)
    
    ttk.Label(search_frame, text="Lon:").grid(row=0, column=2)
    search_lon = ttk.Entry(search_frame, width=10)
    search_lon.grid(row=0, column=3, padx=2)
    
    ttk.Button(search_frame, text="Go", 
              command=lambda: go_to_location(float(search_lat.get()), float(search_lon.get()))).grid(
              row=0, column=4, padx=5)

def go_to_location(lat, lon):
    global pan_offset_x, pan_offset_y, zoom_level
    
    # Set reasonable zoom
    zoom_level = 3.0
    
    # Calculate canvas position for the coordinates
    x, y = lon_lat_to_canvas(lon, lat)
    
    # Center view on this location
    pan_offset_x = canvas_width/2 - (x - pan_offset_x)
    pan_offset_y = canvas_height/2 - (y - pan_offset_y)
    
    draw_chunks()
    status_label.config(text=f"Moved to ({lat}, {lon})")

def update_snap_preview(lat, lon):
    # Clear previous preview
    canvas.delete("snap_preview")
    
    # Convert coordinates to canvas position
    x, y = lon_lat_to_canvas(lon, lat)
    
    # Size of preview marker
    marker_size = 8
    
    # Draw a crosshair at the snap point
    canvas.create_line(x - marker_size, y, x + marker_size, y, 
                      fill="green", width=2, tags="snap_preview")
    canvas.create_line(x, y - marker_size, x, y + marker_size, 
                      fill="green", width=2, tags="snap_preview")
    
    # Draw a small square to represent the potential chunk corner
    canvas.create_rectangle(x - 3, y - 3, x + 3, y + 3, 
                           outline="green", fill="white", tags="snap_preview")

def update_coordinate_display(event):
    lon, lat = canvas_to_lon_lat(event.x, event.y)
    
    # Calculate snapped coordinates
    snapped_lat = snap_to_grid(lat, 5 / 111)
    snapped_lon = snap_to_grid(lon, 5 / (111 * math.cos(math.radians(lat))))
    
    coord_label.config(text=f"Lat: {lat:.6f}, Lon: {lon:.6f}\nSnaps to: ({snapped_lat:.6f}, {snapped_lon:.6f})")
    
    # Update preview marker position
    update_snap_preview(snapped_lat, snapped_lon)

def lon_lat_to_canvas(lon, lat):
    # Convert longitude and latitude to canvas coordinates with zoom and pan
    x = ((lon + 180) * (canvas_width / 360)) * zoom_level + pan_offset_x
    y = ((90 - lat) * (canvas_height / 180)) * zoom_level + pan_offset_y
    return x, y

def canvas_to_lon_lat(x, y):
    # Convert canvas coordinates to longitude and latitude considering zoom and pan
    lon = ((x - pan_offset_x) / zoom_level / canvas_width * 360) - 180
    lat = 90 - ((y - pan_offset_y) / zoom_level / canvas_height * 180)
    return lon, lat

def on_canvas_click(event):
    global selected_chunk_index, preview_chunk
    
    # Convert click to lon/lat considering zoom and pan
    lon, lat = canvas_to_lon_lat(event.x, event.y)
    
    # Check if click was on an existing chunk
    for i, chunk in enumerate(chunks):
        if (chunk['min_lon'] <= lon <= chunk['max_lon'] and
            chunk['min_lat'] <= lat <= chunk['max_lat']):
            # Set as selected chunk and update display
            selected_chunk_index = i
            preview_chunk = None  # Clear any preview when selecting a chunk
            draw_chunks()
            update_info_panel()
            
            # Update entry fields with this chunk's coordinates
            entry_min_lat.delete(0, tk.END)
            entry_min_lat.insert(0, str(chunk['min_lat']))
            entry_min_lon.delete(0, tk.END)
            entry_min_lon.insert(0, str(chunk['min_lon']))
            
            # Update calculated results labels with the chunk's coordinates
            label_min_lat_val.config(text=f"{chunk['min_lat']}")
            label_max_lat_val.config(text=f"{chunk['max_lat']}")
            label_min_lon_val.config(text=f"{chunk['min_lon']}")
            label_max_lon_val.config(text=f"{chunk['max_lon']}")
            
            # Update status bar
            status_label.config(text=f"Selected chunk {i+1} at ({chunk['min_lat']}, {chunk['min_lon']})")
            return
    
    # If no chunk was clicked, handle as new potential chunk
    lon = snap_to_grid(lon, 5 / (111 * math.cos(math.radians(lat))))
    lat = snap_to_grid(lat, 5 / 111)
    
    # Calculate degrees per km
    degree_per_km_lat = 1 / 111
    degree_per_km_lon = 1 / (111 * math.cos(math.radians(lat)))
    
    # Calculate max latitude and longitude for a 5km x 5km square
    max_lat = lat + (5 * degree_per_km_lat)
    max_lon = lon + (5 * degree_per_km_lon)
    
    # Create preview chunk
    preview_chunk = {
        'min_lat': lat,
        'max_lat': max_lat,
        'min_lon': lon,
        'max_lon': max_lon
    }
    
    entry_min_lat.delete(0, tk.END)
    entry_min_lat.insert(0, str(lat))
    entry_min_lon.delete(0, tk.END)
    entry_min_lon.insert(0, str(lon))
    
    # Clear selection when clicking on empty space
    selected_chunk_index = None
    draw_chunks()
    update_info_panel()
    status_label.config(text=f"Cursor at ({lat}, {lon}) - Click Calculate to create chunk")

def on_mouse_wheel(event):
    global zoom_level
    # Get the mouse position
    x, y = event.x, event.y
    
    # Determine zoom direction
    if event.delta > 0:
        # Zoom in
        new_zoom = min(zoom_level * 1.2, ZOOM_IN_LIMIT)  # Increased from 10.0 to 30.0
    else:
        # Zoom out
        new_zoom = max(zoom_level / 1.2, 0.1)
    
    # Get coordinates before zoom
    lon_before, lat_before = canvas_to_lon_lat(x, y)
    
    # Apply zoom
    zoom_level = new_zoom
    
    # Get coordinates after zoom
    x_after, y_after = lon_lat_to_canvas(lon_before, lat_before)
    
    # Adjust pan offset to keep point under cursor
    global pan_offset_x, pan_offset_y
    pan_offset_x += x - x_after
    pan_offset_y += y - y_after
    
    draw_chunks()
    status_label.config(text=f"Zoom level: {zoom_level:.1f}x")

def start_pan(event):
    global is_panning, last_x, last_y
    is_panning = True
    last_x, last_y = event.x, event.y
    canvas.config(cursor="fleur")  # Change cursor to indicate panning

def do_pan(event):
    global pan_offset_x, pan_offset_y, last_x, last_y
    if is_panning:
        # Calculate the difference
        dx = event.x - last_x
        dy = event.y - last_y
        
        # Update the pan offset
        pan_offset_x += dx
        pan_offset_y += dy
        
        # Update the last position
        last_x, last_y = event.x, event.y
        
        # Redraw
        draw_chunks()

def stop_pan(event):
    global is_panning
    is_panning = False
    canvas.config(cursor="")  # Reset cursor

def reset_view():
    global zoom_level, pan_offset_x, pan_offset_y
    zoom_level = 1.0
    pan_offset_x = 0
    pan_offset_y = 0
    draw_chunks()
    status_label.config(text="View reset")

def add_zoom_buttons():
    zoom_frame = ttk.Frame(root)
    zoom_frame.grid(row=3, column=1, padx=5, pady=10, sticky="ns")
    
    zoom_in_btn = ttk.Button(zoom_frame, text="+", width=2,
                           command=lambda: zoom_map(1.2))
    zoom_in_btn.grid(row=0, column=0, pady=2)
    
    zoom_out_btn = ttk.Button(zoom_frame, text="-", width=2,
                            command=lambda: zoom_map(0.8))
    zoom_out_btn.grid(row=1, column=0, pady=2)
    
    ttk.Label(zoom_frame, text="Zoom").grid(row=2, column=0, pady=2)

def bind_keyboard_shortcuts():
    # Add keyboard shortcuts
    root.bind("<Control-s>", lambda e: save_chunks())
    root.bind("<Control-o>", lambda e: load_chunks())
    root.bind("<Delete>", lambda e: delete_selected_chunk())
    root.bind("<Control-r>", lambda e: reset_view())
    root.bind("<plus>", lambda e: zoom_map(1.2))
    root.bind("<minus>", lambda e: zoom_map(0.8))
    root.bind("<Up>", lambda e: pan_with_keyboard(0, 20))
    root.bind("<Down>", lambda e: pan_with_keyboard(0, -20))
    root.bind("<Left>", lambda e: pan_with_keyboard(20, 0))
    root.bind("<Right>", lambda e: pan_with_keyboard(-20, 0))

def pan_with_keyboard(dx, dy):
    global pan_offset_x, pan_offset_y
    pan_offset_x += dx
    pan_offset_y += dy
    draw_chunks()

def zoom_map(factor):
    global zoom_level
    zoom_level = min(max(zoom_level * factor, 0.1), ZOOM_IN_LIMIT)  # Increased from 10.0 to 30.0
    draw_chunks()
    status_label.config(text=f"Zoom level: {zoom_level:.1f}x")

def set_theme():
    style = ttk.Style()
    
    # Configure a custom theme - you can expand this
    style.configure("TButton", padding=6, relief="flat", background="#ccc")
    style.configure("TLabel", padding=3)
    style.configure("TFrame", padding=5)
    style.configure("TLabelframe", padding=10)
    style.configure("TLabelframe.Label", font=("Arial", 10, "bold"))

    # Create some accent colors for different states
    style.map("TButton",
        foreground=[('pressed', 'blue'), ('active', 'blue')],
        background=[('pressed', '!disabled', '#aaa'), ('active', '#ddd')]
    )

# Create the main window
root = tk.Tk()
root.title(f"Chunkgen V{VERSION_NUMBER}")

# Create frames to organize UI elements
input_frame = ttk.LabelFrame(root, text="Input Coordinates")
input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

results_frame = ttk.LabelFrame(root, text="Calculated Results")
results_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

buttons_frame = ttk.Frame(root)
buttons_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

# Create and place labels and entry widgets in the input frame
label_min_lat = ttk.Label(input_frame, text="Min Latitude:")
label_min_lat.grid(row=0, column=0, padx=10, pady=10)
entry_min_lat = ttk.Entry(input_frame)
entry_min_lat.grid(row=0, column=1, padx=10, pady=10)

label_min_lon = ttk.Label(input_frame, text="Min Longitude:")
label_min_lon.grid(row=1, column=0, padx=10, pady=10)
entry_min_lon = ttk.Entry(input_frame)
entry_min_lon.grid(row=1, column=1, padx=10, pady=10)

# Create and place calculate button
button_calculate = ttk.Button(input_frame, text="Calculate Square Area", command=calculate_area)
button_calculate.grid(row=2, columnspan=2, padx=10, pady=10)

# Create and place load, save, and delete buttons
button_load = ttk.Button(buttons_frame, text="Load Chunks", command=load_chunks)
button_load.grid(row=0, column=0, padx=10, pady=10)

button_save = ttk.Button(buttons_frame, text="Save Chunks", command=save_chunks)
button_save.grid(row=0, column=1, padx=10, pady=10)

button_delete = ttk.Button(buttons_frame, text="Delete Selected", command=delete_selected_chunk)
button_delete.grid(row=0, column=2, padx=10, pady=10)

button_reset = ttk.Button(buttons_frame, text="Reset View", command=reset_view)
button_reset.grid(row=0, column=3, padx=10, pady=10)

# Labels to display results and make them clickable in the results frame
label_result_min_lat = ttk.Label(results_frame, text="Min Latitude:")
label_result_min_lat.grid(row=0, column=0, padx=10, pady=10)
label_min_lat_val = ttk.Label(results_frame, text="", foreground="blue", cursor="hand2")
label_min_lat_val.grid(row=0, column=1, padx=10, pady=10)
label_min_lat_val.bind("<Button-1>", lambda e: copy_to_clipboard(label_min_lat_val.cget("text")))

label_result_max_lat = ttk.Label(results_frame, text="Max Latitude:")
label_result_max_lat.grid(row=1, column=0, padx=10, pady=10)
label_max_lat_val = ttk.Label(results_frame, text="", foreground="blue", cursor="hand2")
label_max_lat_val.grid(row=1, column=1, padx=10, pady=10)
label_max_lat_val.bind("<Button-1>", lambda e: copy_to_clipboard(label_max_lat_val.cget("text")))

label_result_min_lon = ttk.Label(results_frame, text="Min Longitude:")
label_result_min_lon.grid(row=2, column=0, padx=10, pady=10)
label_min_lon_val = ttk.Label(results_frame, text="", foreground="blue", cursor="hand2")
label_min_lon_val.grid(row=2, column=1, padx=10, pady=10)
label_min_lon_val.bind("<Button-1>", lambda e: copy_to_clipboard(label_min_lon_val.cget("text")))

label_result_max_lon = ttk.Label(results_frame, text="Max Longitude:")
label_result_max_lon.grid(row=3, column=0, padx=10, pady=10)
label_max_lon_val = ttk.Label(results_frame, text="", foreground="blue", cursor="hand2")
label_max_lon_val.grid(row=3, column=1, padx=10, pady=10)
label_max_lon_val.bind("<Button-1>", lambda e: copy_to_clipboard(label_max_lon_val.cget("text")))

# Create canvas to display chunks
canvas_width = 800
canvas_height = 400
canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="white")
canvas.grid(row=3, column=0, padx=10, pady=10)

create_coordinate_display()
create_info_panel()
add_zoom_buttons()
bind_keyboard_shortcuts()

# Bind mouse events for interaction
canvas.bind("<Button-1>", on_canvas_click)     # Left click for selection
canvas.bind("<Button-2>", start_pan)           # Middle button for panning (start)
canvas.bind("<B2-Motion>", do_pan)             # Middle button drag for panning
canvas.bind("<ButtonRelease-2>", stop_pan)     # Middle button release to stop panning
canvas.bind("<MouseWheel>", on_mouse_wheel)    # Mouse wheel for zoom
canvas.bind("<Motion>", update_coordinate_display)  # Mouse movement for coordinate preview

# Add a status bar at the bottom
status_label = ttk.Label(root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
status_label.grid(row=4, column=0, sticky="ew", padx=10, pady=5)

# Help text
help_text = ttk.Label(root, text="Controls: Left-click to select, Middle-click to pan, Scroll wheel to zoom\nSelected chunks appear in gray with red outline")
help_text.grid(row=5, column=0, padx=10, pady=5, sticky="w")

# Run the main loop
root.mainloop()