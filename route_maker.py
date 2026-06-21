"""This program manages climbing routes.

It allows for the manual or automatic creation of routes,
which can then be saved to a JSON file.
"""
import pygame as py
from dataclasses import dataclass, field
import json as js

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
mouse_down = False
SPACING_ON_HOLDS_PANEL = 80
ROOM_FOR_BUTTONS = 200
on_row = 0

# stuff
font = py.font.SysFont(None, 36)
clear_button = font.render("Clear", True, "Black")
clear_button_rect = clear_button.get_rect()

#---------Image loading---------
try:
    right_arrow = py.image.load("icons/right_arrow.png").convert_alpha()
    right_arrow = py.transform.scale(right_arrow, (50, 50))
    left_arrow = py.transform.flip(right_arrow, True, False)
except py.error:
    print("Failed to load image")
    # Fallbacks to prevent crash if assets are missing
    right_arrow = py.Surface((50, 50))
    right_arrow.fill((0, 0, 255))
    left_arrow = py.Surface((50, 50))
    left_arrow.fill((0, 0, 255))


def length_from_mouse_pos(v):
    """Uses Pythagoras's theorem (with no square root for efficiency) to compare relative distances from the mouse.
    Does not give exact distance.
    """
    mouse = py.mouse.get_pos()
    return (v[0] - mouse[0]) ** 2 + (v[1] - mouse[1]) ** 2

# ---------Grid class----------
class Grid:
    def __init__(self, x: int, y: int, size: tuple=(10, 10)):
        """Grid X and Y"""
        self.x = x
        self.y = y
        self.size = size
        self.gap = 1.0  # Safe initialization default float
        self.grid = []

    # Update grid cell positions
    def update(self, width = py.display.get_window_size()[0], height = py.display.get_window_size()[1]):
        """Update the grid if the window changes size"""
        global holds_panel_height

        # Calculate the gap between cells based on the new window size
        self.width = width 
        self.height = (height - holds_panel_height)
        self.gapx = self.width // self.size[0]
        self.gapy = self.height // self.size[1]
        self.gap = max(1, (min(self.gapx, self.gapy))) # Prevent division by zero if gap drops to 0
        
        # Adjust the position of the grid
        self.x = (self.width - self.gap * (self.size[0] - 1)) // 2
        self.y = (self.height - self.gap * (self.size[1] - 1)) // 2

        # Add the positions of the grid cells to the grid list
        self.grid = []
        for w in range(self.size[0]):
            for h in range(self.size[1]):  
                self.grid.append((self.x + w * self.gap, self.y + h * self.gap))

grid = Grid(0, 50, (25, 25))
grid.update(display_width, display_height) # Initial layout generation right away

#--------Making Classes-----------
@dataclass
class ProcessedHold:
    size: int
    colour: str
    x : int
    y : int
    row : int

class DisplayedHold:
    def __init__(self, hold_clicked: ProcessedHold):
        self.x, self.y = hold_clicked.x, hold_clicked.y 
        self.colour = hold_clicked.colour 
        self.size = hold_clicked.size 
        self.update()
        
    def pos_on_panel(self):
        pass

    def update(self):
        """Updates the rect and size of the displayed hold"""
        self.displayed_size = (self.size / grid.gap) * 10
        self.rect = py.Rect(0, 0, self.size * 2, self.size * 2)
        self.rect.center = (self.x, self.y)


# --------------Holds dictionary and size, colour, and type variables-------------- 
try:
    with open("inventory.json", "r") as f:
        holds_data = js.load(f)
except FileNotFoundError:
    # Safe structural mock dataset fallback if files do not exist locally
    holds_data = [
        {"size": "Small", "colour": "Red"},
        {"size": "Medium", "colour": "Blue"},
        {"size": "Large", "colour": "Green"}
    ]

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

drag_hold = False
holds_on_grid: list[DisplayedHold] = []

# --------------Main loop-------------- 
run = True
while run:

    #--------Clear button---------
    box_round_clear_button_rect = py.Rect(0,0,100,50)
    box_round_clear_button_rect.center = clear_button_rect.center
    clear_button_rect.center = (holds_panel_width - 180, holds_panel_height // 2)

    rows_visible = max(1, holds_panel_height // 70)
    usable_width = holds_panel_width - ROOM_FOR_BUTTONS
    holds_per_row = max(1, usable_width // SPACING_ON_HOLDS_PANEL)

    processed_holds_data: list[ProcessedHold] = []

    for i, hold in enumerate(holds_data):
        row_index = i // holds_per_row
        col_index = i % holds_per_row

        processed_holds_data.append(
            ProcessedHold(
                size = size_properies[hold["size"]],
                colour = colour_properies[hold["colour"]],
                x = col_index * SPACING_ON_HOLDS_PANEL + 40,
                y = holds_panel_height // 2,
                row = row_index
            )
        )

    possible_rows = (processed_holds_data[-1].row + 1) if processed_holds_data else 1
    possible_rows = max(1, possible_rows)

    displayed_holds: list[DisplayedHold] = []
    for hold in processed_holds_data:
        slot = (hold.row - on_row) % possible_rows
        y = (holds_panel_height // (rows_visible + 1)) * (slot + 1)
        if slot < rows_visible:
            disp_hold = DisplayedHold(hold)
            disp_hold.y = y
            disp_hold.update()
            displayed_holds.append(disp_hold)

    # ----------Event handling-------------
    display_width, display_height = py.display.get_window_size()
    mouse_grab_area = py.Rect(0, display_height - holds_panel_height - 5, display_width, 10)

    l_arrow_rect = left_arrow.get_rect(center =(holds_panel_width - 90, holds_panel_height // 2))
    r_arrow_rect = right_arrow.get_rect(center = (holds_panel_width - 30, holds_panel_height// 2))

    mouse_pos = py.mouse.get_pos()
    
    clicked_hold = False
    for event in py.event.get():
        if event.type == py.QUIT:
            run = False
        elif event.type == py.VIDEORESIZE:
            display_width = max(event.size[0], 400)
            display_height = max(event.size[1], 400)
            screen = py.display.set_mode((display_width, display_height), py.RESIZABLE)
        elif event.type == py.MOUSEBUTTONDOWN:
            if mouse_grab_area.collidepoint(mouse_pos):
                mouse_down = True
            elif l_arrow_rect.move(0,display_height - holds_panel_height).collidepoint(mouse_pos):
                on_row = (on_row - 1) % possible_rows
            elif r_arrow_rect.move(0,display_height - holds_panel_height).collidepoint(mouse_pos):
                on_row = (on_row + 1) % possible_rows
            elif box_round_clear_button_rect.move(0,display_height - holds_panel_height).collidepoint(mouse_pos):
                holds_on_grid.clear()
            else:
                for hold in displayed_holds:
                    if hold.rect.move(0, display_height - holds_panel_height).collidepoint(mouse_pos):
                        clicked_hold = hold
                        break
                if clicked_hold:
                    drag_hold = clicked_hold
                    drag_hold.y += (display_height - holds_panel_height) 
                    drag_hold.update()
                    
        elif event.type == py.MOUSEMOTION:
            if drag_hold:
                if grid.x <= event.pos[0] <= grid.x + grid.gap * (grid.size[0] - 1) and grid.y <= event.pos[1] <= grid.y + grid.gap * (grid.size[1] - 1):
                    drag_hold.x, drag_hold.y = min(grid.grid, key = length_from_mouse_pos)
                else: 
                    drag_hold.x, drag_hold.y = event.pos
                drag_hold.update()
                
        elif event.type == py.MOUSEBUTTONUP:
            if drag_hold:
                holds_on_grid.append(drag_hold)
            drag_hold = False
            mouse_down = False

    # -----------Panel-------------
    holds_panel_width = display_width
    holds_panel = py.Surface((holds_panel_width, holds_panel_height))
    holds_panel.fill(("#c8c8c8"))

    if mouse_grab_area.collidepoint(mouse_pos):
        py.mouse.set_cursor(py.SYSTEM_CURSOR_SIZENS)
    else:
        py.mouse.set_cursor(py.SYSTEM_CURSOR_ARROW)

    if mouse_down:
        new_mouse_y = mouse_pos[1]
        new_height = display_height - new_mouse_y
        min_h = 70
        max_h = 70 * possible_rows
        holds_panel_height = max(min_h, min(max_h, new_height))
        
    py.draw.line(holds_panel, ("#000000"), (0, 0), (holds_panel_width, 0), 2)
    grid.update(display_width, display_height)
    
    # Display holds on the panel
    for hold in displayed_holds:
        py.draw.circle(
            holds_panel, 
            hold.colour, 
            (hold.x, hold.y), 
            hold.size
        )

    # Buttons
    holds_panel.blit(right_arrow, r_arrow_rect)
    holds_panel.blit(left_arrow, l_arrow_rect)

    # -----------Drawing for the main screen-------------
    screen.fill(("#ffffffff"))

    for cell in grid.grid:
        py.draw.circle(screen, ("#000000"), cell, 2)

    # FIX: Continually update existing grid hold scaling settings relative to window shifts
    if holds_on_grid:
        for hold in holds_on_grid:
            hold.update()

    if drag_hold:
        drag_hold.update()
        py.draw.circle(screen,
                        color = drag_hold.colour, 
                        center = (drag_hold.x, drag_hold.y),
                        radius = max(2, int(drag_hold.displayed_size))
                        )
    
    if holds_on_grid:
        for hold in holds_on_grid:
            py.draw.circle(screen,
                            color = hold.colour, 
                            center = (hold.x, hold.y),
                            radius = max(2, int(hold.displayed_size))
                            )
    
    py.draw.rect(holds_panel, (255, 255, 255), box_round_clear_button_rect, 3)
    holds_panel.blit(clear_button, clear_button_rect)
    screen.blit(holds_panel, (0, display_height - holds_panel_height))

    py.display.flip()