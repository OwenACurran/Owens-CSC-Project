"""This program manages climbing routes.

It allows for the manual or automatic creation of routes,
which can then be saved to a jsononON file.
"""
import pygame
from dataclasses import dataclass, field
import json

pygame.init()

# ----------Set up the display-----------
display_width, display_height = 800, 600
screen = pygame.display.set_mode(
    (display_width, display_height),
    pygame.RESIZABLE
)
pygame.display.set_caption("Route Maker")

# Holds menu dimensions
holds_menu_width = display_width
holds_menu_height = 100

# Dragging state
mouse_down = False
SPACING_ON_HOLDS_menu = 80
ROOM_FOR_BUTTONS = 200
on_row = 0

# stuff
font = pygame.font.SysFont(None, 36)
clear_button = font.render("Clear", True, "Black")
clear_button_rect = clear_button.get_rect()

#---------Image loading---------
try:
    right_arrow = pygame.image.load("icons/right_arrow.png").convert_alpha()
    right_arrow = pygame.transform.scale(right_arrow, (50, 50))
    left_arrow = pygame.transform.flip(right_arrow, True, False)
except pygame.error:
    print("Failed to load image")
    # Fallbacks to prevent crash if assets are missing
    right_arrow = pygame.Surface((50, 50))
    right_arrow.fill((0, 0, 255))
    left_arrow = pygame.Surface((50, 50))
    left_arrow.fill((0, 0, 255))


def length_from_mouse_pos(v):
    """Uses pygamethagoras's theorem (with no square root for efficiency) to compare relative distances from the mouse.
    Does not give exact distance.
    """
    mouse = pygame.mouse.get_pos()
    return (v[0] - mouse[0]) ** 2 + (v[1] - mouse[1]) ** 2

# ---------Grid class----------
class Grid:
    def __init__(self, x: int, y: int, size: tuple=(10, 10)):
        """Grid X and Y"""
        self.x = x
        self.y = y
        self.size = size
        self.gap = 1.0
        self.grid = []

    # Update grid cell positions
    def update(self, width = pygame.display.get_window_size()[0], height = pygame.display.get_window_size()[1]):
        """Update the grid if the window changes size"""
        global holds_menu_height

        # Calculate the gap between cells based on the new window size
        self.width = width 
        self.height = (height - holds_menu_height)
        self.gapx = self.width // self.size[0]
        self.gapygame = self.height // self.size[1]
        self.gap = max(1, (min(self.gapx, self.gapygame))) # Prevent division by zero if gap drops to 0
        
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
    radius: int
    colour: str
    x : int
    y : int
    row : int

class DisplayedHold:
    def __init__(self, hold_clicked: ProcessedHold):
        self.x, self.y = hold_clicked.x, hold_clicked.y 
        self.colour = hold_clicked.colour 
        self.radius = hold_clicked.radius 
        
        # Track which grid coordinate intersection this holds belongs to
        self.grid_col = None
        self.grid_row = None
        self.is_on_grid = False
        
        self.update()

    def update(self):
        """Updates the rect and size of the displayed hold"""
        self.displayed_size = self.radius * grid.gap / 50
        
        # Recalculate the position relative to grid offsets
        if self.is_on_grid and self.grid_col is not None and self.grid_row is not None:
            self.x = grid.x + self.grid_col * grid.gap
            self.y = grid.y + self.grid_row * grid.gap
            
        self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        self.rect.center = (self.x, self.y)


# --------------Holds dictionary and size, colour, and type variables-------------- 
try:
    with open("inventory.json", "r") as f:
        holds_data = json.load(f)
except FileNotFoundError:
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
menu_displayed_holds: list[DisplayedHold] = []
possible_rows = 1

def regenerate_menu():
    """Generates menu items"""
    global menu_displayed_holds, possible_rows, holds_menu_width, holds_menu_height
    
    rows_visible = max(1, holds_menu_height // 70)
    usable_width = holds_menu_width - ROOM_FOR_BUTTONS
    holds_per_row = max(1, usable_width // SPACING_ON_HOLDS_menu)

    processed_holds_data: list[ProcessedHold] = []
    for i, hold in enumerate(holds_data):
        row_index = i // holds_per_row
        col_index = i % holds_per_row

        processed_holds_data.append(
            ProcessedHold(
                radius = size_properies[hold["size"]],
                colour = colour_properies[hold["colour"]],
                x = col_index * SPACING_ON_HOLDS_menu + 40,
                y = holds_menu_height // 2,
                row = row_index
            )
        )

    possible_rows = (processed_holds_data[-1].row + 1) if processed_holds_data else 1
    possible_rows = max(1, possible_rows)

    menu_displayed_holds = []
    for hold in processed_holds_data:
        slot = (hold.row - on_row) % possible_rows
        y = (holds_menu_height // (rows_visible + 1)) * (slot + 1)
        if slot < rows_visible:
            disp_hold = DisplayedHold(hold)
            disp_hold.y = y
            disp_hold.update()
            menu_displayed_holds.append(disp_hold)


regenerate_menu()

# --------------Main loop-------------- 
run = True
while run:

    #--------Clear button---------
    box_round_clear_button_rect = pygame.Rect(0,0,100,50)
    box_round_clear_button_rect.center = clear_button_rect.center
    clear_button_rect.center = (holds_menu_width - 180, holds_menu_height // 2)

    # ----------Event handling-------------
    display_width, display_height = pygame.display.get_window_size()
    mouse_grab_area = pygame.Rect(0, display_height - holds_menu_height - 5, display_width, 10)

    l_arrow_rect = left_arrow.get_rect(center =(holds_menu_width - 90, holds_menu_height // 2))
    r_arrow_rect = right_arrow.get_rect(center = (holds_menu_width - 30, holds_menu_height// 2))

    mouse_pos = pygame.mouse.get_pos()
    
    clicked_hold = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.VIDEORESIZE:
            display_width = max(event.size[0], 400)
            display_height = max(event.size[1], 400)
            screen = pygame.display.set_mode((display_width, display_height), pygame.RESIZABLE)
            grid.update(display_width, display_height)
            regenerate_menu()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if mouse_grab_area.collidepoint(mouse_pos):
                mouse_down = True
            elif l_arrow_rect.move(0,display_height - holds_menu_height).collidepoint(mouse_pos):
                on_row = (on_row - 1) % possible_rows
                regenerate_menu()
            elif r_arrow_rect.move(0,display_height - holds_menu_height).collidepoint(mouse_pos):
                on_row = (on_row + 1) % possible_rows
                regenerate_menu()
            elif box_round_clear_button_rect.move(0,display_height - holds_menu_height).collidepoint(mouse_pos):
                holds_on_grid.clear()
            else:
                for hold in menu_displayed_holds:
                    if hold.rect.move(0, display_height - holds_menu_height).collidepoint(mouse_pos):
                        clicked_hold = hold
                        break
                if clicked_hold:
                    drag_hold = DisplayedHold(
                        ProcessedHold(
                            radius=clicked_hold.radius, 
                            colour=clicked_hold.colour, 
                            x=clicked_hold.x, 
                            y=clicked_hold.y, 
                            row=0
                        )
                    )
                    drag_hold.y += (display_height - holds_menu_height) 
                    drag_hold.update()
                    
        elif event.type == pygame.MOUSEMOTION:
            if drag_hold:
                if grid.x <= event.pos[0] <= grid.x + grid.gap * (grid.size[0] - 1) and grid.y <= event.pos[1] <= grid.y + grid.gap * (grid.size[1] - 1):
                    snap_x, snap_y = min(grid.grid, key = length_from_mouse_pos)
                    drag_hold.x, drag_hold.y = snap_x, snap_y
                    
                    drag_hold.grid_col = round((snap_x - grid.x) / grid.gap)
                    drag_hold.grid_row = round((snap_y - grid.y) / grid.gap)
                    drag_hold.is_on_grid = True
                else: 
                    drag_hold.x, drag_hold.y = event.pos
                    drag_hold.is_on_grid = False
                drag_hold.update()
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if drag_hold and drag_hold.is_on_grid:
                holds_on_grid.append(drag_hold)
            drag_hold = False
            mouse_down = False

    # -----------menu-------------
    holds_menu_width = display_width
    holds_menu = pygame.Surface((holds_menu_width, holds_menu_height))
    holds_menu.fill(("#c8c8c8"))

    if mouse_grab_area.collidepoint(mouse_pos):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENS)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    if mouse_down:
        new_mouse_y = mouse_pos[1]
        new_height = display_height - new_mouse_y
        min_h = 70
        max_h = 70 * possible_rows
        holds_menu_height = max(min_h, min(max_h, new_height))
        grid.update(display_width, display_height)
        regenerate_menu()
        
    pygame.draw.line(holds_menu, ("#000000"), (0, 0), (holds_menu_width, 0), 2)
    grid.update(display_width, display_height)
    
    if holds_on_grid:
        for hold in holds_on_grid:
            hold.update()

    # Display holds on the menu
    for hold in menu_displayed_holds:
        pygame.draw.circle(
            holds_menu, 
            hold.colour, 
            (hold.x, hold.y), 
            hold.radius
        )

    # Buttons
    holds_menu.blit(right_arrow, r_arrow_rect)
    holds_menu.blit(left_arrow, l_arrow_rect)

    # -----------Drawing for the main screen-------------
    screen.fill(("#ffffffff"))

    for cell in grid.grid:
        pygame.draw.circle(screen, ("#000000"), cell, 2)

    if drag_hold:
        if not pygame.mouse.get_pressed()[0]: 
            drag_hold.update()
        pygame.draw.circle(screen,
                        color = drag_hold.colour, 
                        center = (drag_hold.x, drag_hold.y),
                        radius = max(2, int(drag_hold.displayed_size))
                        )
    
    if holds_on_grid:
        for hold in holds_on_grid:
            pygame.draw.circle(screen,
                            color = hold.colour, 
                            center = (hold.x, hold.y),
                            radius = max(2, int(hold.displayed_size))
                            )
    
    pygame.draw.rect(holds_menu, (255, 255, 255), box_round_clear_button_rect, 3)
    holds_menu.blit(clear_button, clear_button_rect)
    screen.blit(holds_menu, (0, display_height - holds_menu_height))

    pygame.display.flip()