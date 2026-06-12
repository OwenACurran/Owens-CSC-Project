import pygame as py
import os
import json as js
import math

py.init()

# ----------Set up the display-----------
display_width, display_height = 800, 600
screen = py.display.set_mode(
    (display_width, display_height),
    py.RESIZABLE
)
py.display.set_caption("Route Maker")

# Holds panel dimensions
holds_panel_width = display_width
holds_panel_height = 100

# Dragging state
is_dragging = False
SPACING_ON_HOLDS_PANEL = 80
ROOM_FOR_BUTTONS = 200
on_row = 0

#---------Image loading---------
try:
    right_arrow = py.image.load("icons/right_arrow.png").convert_alpha()
    right_arrow = py.transform.scale(right_arrow, (50, 50))
    left_arrow = py.transform.flip(right_arrow, True, False)
except py.error:
    print("Failed to load image")
    

# ---------Grid class-------------
class Grid:
    def __init__(self, x, y, size=(10, 10)):
        self.x = x
        self.y = y
        self.size = size

    # Update grid cell positions
    def update(self, width = py.display.get_window_size()[0], height = py.display.get_window_size()[1]):
        global holds_panel_height

        # Calculate the gap between cells based on the new window size
        self.width = width 
        self.height = (height - holds_panel_height)
        self.gapx = self.width // self.size[0]
        self.gapy = self.height // self.size[1]
        self.gap = (min(self.gapx, self.gapy))
        
        # Adjust the position of the grid
        self.x = (self.width - self.gap * (self.size[0] - 1)) // 2
        self.y = (self.height - self.gap * (self.size[1] - 1)) // 2

        # Add the positions of the grid cells to the grid list
        self.grid = []
        for w in range(self.size[0]):
            for h in range(self.size[1]):  
                self.grid.append((self.x + w * self.gap, self.y + h * self.gap))

grid = Grid(0, 0, (25, 25))

# --------------Holds dictionary and size, colour, and type variables-------------- 
with open("inventory.json", "r") as f:
    holds_data = js.load(f)

size_properies = {
    "Tiny": 5,
    "Small": 10,
    "Medium": 20,
    "Large": 30
}

colour_properies = {
    "Black": "#000000",
    "Blue": "#0000ff",
    "Red": "#ff0000",
    "Green": "#31b431",
    "Yellow": "#ffff00",
    "Purple": "#BD5DBD",
    "Orange": "#FF9100"
}

# --------------Main loop-------------- 
run = True
while run:
    processed_holds_data = []
    rows_visible = holds_panel_height // 70

    usable_width = holds_panel_width - ROOM_FOR_BUTTONS
    holds_per_row = usable_width // SPACING_ON_HOLDS_PANEL

    if holds_per_row < 1:
        holds_per_row = 1 


    for i, hold in enumerate(holds_data):
        row_index = i // holds_per_row
        col_index = i % holds_per_row

        processed_holds_data.append({
            "size": size_properies[hold["size"]],
            "colour": colour_properies[hold["colour"]],
            "x": col_index * SPACING_ON_HOLDS_PANEL + 40,
            "y": holds_panel_height // 2,
            "row": row_index
        })
    
    possible_rows = (processed_holds_data[-1]["row"] + 1) if processed_holds_data else 1
    possible_rows = max(1, possible_rows)
    

    # ----------Event handling-------------
    display_width, display_height = py.display.get_window_size()
    mouse_grab_area = py.Rect(0, display_height - holds_panel_height - 5, display_width, 10)

    l_arrow_rect = left_arrow.get_rect(center =(holds_panel_width - 90, holds_panel_height // 2))
    r_arrow_rect = right_arrow.get_rect(center = (holds_panel_width - 30, holds_panel_height// 2))

    for event in py.event.get():
        if event.type == py.QUIT:
            run = False
        elif event.type == py.VIDEORESIZE:
            display_width = max(event.size[0], 400)
            display_height = max(event.size[1], 400)
            screen = py.display.set_mode((display_width, display_height), py.RESIZABLE)
        elif event.type == py.MOUSEBUTTONDOWN:
            # Only start dragging if the click originates in the grab area
            if mouse_grab_area.collidepoint(py.mouse.get_pos()):
                is_dragging = True
            elif l_arrow_rect.move(0,display_height - holds_panel_height).collidepoint(py.mouse.get_pos()):
                on_row = (on_row - 1) % possible_rows
            elif r_arrow_rect.move(0,display_height - holds_panel_height).collidepoint(py.mouse.get_pos()):
                on_row = (on_row + 1) % possible_rows
        elif event.type == py.MOUSEBUTTONUP:
            is_dragging = False

    # Use dragging state for panel movement
    mouse_down = is_dragging

    # -----------Panel-------------
    holds_panel_width = display_width
    holds_panel = py.Surface((holds_panel_width, holds_panel_height))
    holds_panel.fill(("#c8c8c8"))

    # Cursor feedback
    if mouse_grab_area.collidepoint(py.mouse.get_pos()):
        py.mouse.set_cursor(py.SYSTEM_CURSOR_SIZENS)
    else:
        py.mouse.set_cursor(py.SYSTEM_CURSOR_ARROW)

    if mouse_down:
        new_mouse_y = py.mouse.get_pos()[1]
        new_height = display_height - new_mouse_y
        min_h = 70
        max_h = 70 * possible_rows
        holds_panel_height = max(min_h, min(max_h, new_height))
        

    # Drawing on the panel
    py.draw.line(holds_panel, ("#000000"), (0, 0), (holds_panel_width, 0), 2)
    
    grid.update(display_width, display_height)
    
    # Display holds on the panel
    for hold in processed_holds_data:

        slot = (hold["row"] - on_row) % possible_rows

        if slot < rows_visible:

            x = hold["x"]
            y = (holds_panel_height // (rows_visible + 1)) * (slot + 1)
            colour = hold["colour"]
            size = hold["size"]

            py.draw.circle(
                holds_panel, 
                colour, 
                (x, y), 
                size
            )

    # Buttons
    holds_panel.blit(right_arrow, r_arrow_rect)
    holds_panel.blit(left_arrow, l_arrow_rect)

    # -----------Drawing for the main screen-------------
    screen.fill(("#ffffffff"))

    for cell in grid.grid:
        py.draw.circle(screen, ("#000000"), cell, 2)

    # Update the display
    screen.blit(holds_panel, (0, display_height - holds_panel_height))
    py.display.flip()