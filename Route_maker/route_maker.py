"""This program manages climbing routes.

It allows for the manual or automatic creation of routes,
which can then be saved to a json file.
"""
import pygame
from dataclasses import dataclass
import json
import os

pygame.init()

# Sets up directorys so the program can be run anywhere and work
DIR_ROUTEMAKER_FOLDER = os.path.dirname(os.path.abspath(__file__))
DIR_ICONS = os.path.join(DIR_ROUTEMAKER_FOLDER, "icons")
DIR_SAVES = os.path.join(DIR_ROUTEMAKER_FOLDER, "saves")
RIGHT_ARROW_PATH = os.path.join(DIR_ICONS, "right_arrow.png")
SETTINGS_BUTTON_PATH = os.path.join(DIR_ICONS, "settings.png")


SAVES_FOLDER_NAME = "saves"
os.makedirs(SAVES_FOLDER_NAME, exist_ok=True) # Makes a saves folder if one does not exist

# ----------Set up the display-----------
DISP_DEFAULT_WIDTH = 800
DISP_DEFAULT_HEIGHT = 600

display_width, display_height = DISP_DEFAULT_WIDTH, DISP_DEFAULT_HEIGHT
screen = pygame.display.set_mode((display_width, display_height),pygame.RESIZABLE)  # The RESIZABLE flag allows the window to be adjusted
pygame.display.set_caption("Route Maker")

# Holds menu dimensions
holds_menu_width = display_width
holds_menu_height = 100

# Dragging state
mouse_down = False
SPACING_ON_HOLDS_menu = 80
ROOM_FOR_BUTTONS = 200
on_row = 0

# Creates a font
FONT_SIZE = 30
font = pygame.font.Font(None, FONT_SIZE) # Pygame default font

clear_button = font.render("Clear", True, "Black")
clear_button_rect = clear_button.get_rect()

save_button = font.render("Save", True, "Black")
save_button_rect = save_button.get_rect()

load_button = font.render("Load", True, "Black")
load_button_rect = load_button.get_rect()

settings_menu_open = False
settings_popup_rect = pygame.Rect(0, 0, 220, 180)


file_browser_open = False
file_browser_mode = None
file_browser_files = []
file_browser_selected = 0
file_browser_input = ""
file_browser_rect = pygame.Rect(0, 0, 520, 420)

def refresh_file_list():
    try:
        files = [f for f in os.listdir(SAVES_FOLDER_NAME) if f.lower().endswith('.json')]
    except FileNotFoundError:
        files = []
    files.sort()
    return files


#---------Image loading---------
try:
    settings_button = pygame.image.load(SETTINGS_BUTTON_PATH)
    settings_button = pygame.transform.scale(settings_button, (60, 60))
    right_arrow = pygame.image.load(RIGHT_ARROW_PATH).convert_alpha()
    right_arrow = pygame.transform.scale(right_arrow, (50, 50))
    left_arrow = pygame.transform.flip(right_arrow, True, False)
except pygame.error:
    print("Failed to load image")
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
        
        # Track which grid coordinate this holds belongs to
        self.grid_col = None
        self.grid_row = None
        self.is_on_grid = False
        
        self.update()

    def update(self):
        """Updates the rect and size of the displayed hold"""
        self.displayed_size = self.radius * grid.gap / 50
        
        # Recalculate the position
        if self.is_on_grid and self.grid_col is not None and self.grid_row is not None:
            self.x = grid.x + self.grid_col * grid.gap
            self.y = grid.y + self.grid_row * grid.gap
            
        self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        self.rect.center = (self.x, self.y)

def save_route(filename=None):
    if filename is None:
        filename = "route.json"
    data = []

    for hold in holds_on_grid:
        data.append({
            "radius": hold.radius,
            "colour": hold.colour,
            "grid_col": hold.grid_col,
            "grid_row": hold.grid_row
        })

    if os.path.isabs(filename):
        path = filename
    else:
        path = os.path.join(SAVES_FOLDER_NAME, filename)

    os.makedirs(os.path.dirname(path) or SAVES_FOLDER_NAME, exist_ok=True)

    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Saved route to {path}")


def load_route(filename=None):
    if filename is None:
        filename = "route.json"

    if os.path.isabs(filename):
        path = filename
    else:
        path = os.path.join(SAVES_FOLDER_NAME, filename)

    if not os.path.exists(path):
        print(f"No save file found at {path}")
        return

    with open(path, "r") as f:
        data = json.load(f)

    holds_on_grid.clear()

    for item in data:
        hold = DisplayedHold(
            ProcessedHold(
                radius=item["radius"],
                colour=item["colour"],
                x=0,
                y=0,
                row=0
            )
        )

        hold.grid_col = item["grid_col"]
        hold.grid_row = item["grid_row"]
        hold.is_on_grid = True
        hold.update()

        holds_on_grid.append(hold)

    print(f"Loaded route from {path}")


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
    
    holds_menu_width = pygame.display.get_window_size()[0]
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

    #--------Toolbar and settings button---------
    l_arrow_rect = left_arrow.get_rect(center =(holds_menu_width - 150, holds_menu_height // 2))
    r_arrow_rect = right_arrow.get_rect(center = (holds_menu_width - 100, holds_menu_height // 2))
    settings_button_rect = settings_button.get_rect(center = (holds_menu_width -50, holds_menu_height))
    display_width, display_height = pygame.display.get_window_size()
    holds_menu_width = display_width
    settings_button_rect.center = (display_width - 40, holds_menu_height // 2)
    file_browser_rect.center = (display_width // 2, display_height // 2)
    settings_popup_rect.width = 260
    settings_popup_rect.height = 210
    settings_button_screen_rect = settings_button_rect.move(0, display_height - holds_menu_height)
    settings_popup_rect.bottomright = (
        settings_button_screen_rect.right - 10,
        settings_button_screen_rect.top - 10
    )

    popup_button_width = settings_popup_rect.width - 40
    clear_popup_button_rect = pygame.Rect(settings_popup_rect.x + 20, settings_popup_rect.y + 15, popup_button_width, 40)
    save_popup_button_rect = pygame.Rect(settings_popup_rect.x + 20, settings_popup_rect.y + 65, popup_button_width, 40)
    load_popup_button_rect = pygame.Rect(settings_popup_rect.x + 20, settings_popup_rect.y + 115, popup_button_width, 40)

    # ----------Event handling-------------
    mouse_grab_area = pygame.Rect(0, display_height - holds_menu_height - 5, display_width, 10)

    mouse_pos = pygame.mouse.get_pos()
    holds_menu_width = display_width

    clicked_hold = False
    for event in pygame.event.get():
        if file_browser_open:
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if not file_browser_rect.collidepoint(mouse_x, mouse_y):
                    file_browser_open = False
                fx, fy = file_browser_rect.x + 20, file_browser_rect.y + 20
                item_h = 28
                rel_y = mouse_y - fy
                idx = rel_y // item_h
                if 0 <= idx < len(file_browser_files) and rel_y >= 0 and rel_y < item_h * 10:
                    file_browser_selected = int(idx)
                    continue
                # confirm / cancel buttons
                confirm_rect = pygame.Rect(file_browser_rect.right - 120, file_browser_rect.bottom - 50, 100, 35)
                cancel_rect = pygame.Rect(file_browser_rect.x + 20, file_browser_rect.bottom - 50, 100, 35)
                input_rect = pygame.Rect(file_browser_rect.x + 20, file_browser_rect.bottom - 95, file_browser_rect.width - 40, 30)
                if confirm_rect.collidepoint(mouse_x, mouse_y):
                    # perform save or load
                    if file_browser_mode == 'save':
                        if file_browser_input.strip():
                            chosen = file_browser_input.strip()
                        elif file_browser_files:
                            chosen = file_browser_files[file_browser_selected]
                        else:
                            chosen = 'route.json'
                        # ensure .json extension
                        if not chosen.lower().endswith('.json'):
                            chosen += '.json'
                        save_route(chosen)
                    else:  # load
                        if file_browser_files:
                            chosen = file_browser_files[file_browser_selected]
                            load_route(chosen)
                    file_browser_open = False
                if cancel_rect.collidepoint(mouse_x, mouse_y):
                    file_browser_open = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    file_browser_input = file_browser_input[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    # treat as confirm
                    if file_browser_mode == 'save':
                        if file_browser_input.strip():
                            chosen = file_browser_input.strip()
                            # ensure .json extension
                            if not chosen.lower().endswith('.json'):
                                chosen += '.json'
                            save_route(chosen)
                        elif file_browser_files:
                            chosen = file_browser_files[file_browser_selected]
                            save_route(chosen)
                    else:
                        if file_browser_files:
                            chosen = file_browser_files[file_browser_selected]
                            load_route(chosen)
                    file_browser_open = False
                else:
                    # append printable characters
                    if event.unicode and len(event.unicode) == 1 and 32 <= ord(event.unicode) <= 126:
                        file_browser_input += event.unicode
            continue
        # events
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
            elif l_arrow_rect.move(0, display_height - holds_menu_height).collidepoint(mouse_pos):
                on_row = (on_row - 1) % possible_rows
                regenerate_menu()
            elif r_arrow_rect.move(0, display_height - holds_menu_height).collidepoint(mouse_pos):
                on_row = (on_row + 1) % possible_rows
                regenerate_menu()
            elif settings_button_screen_rect.collidepoint(mouse_pos):
                settings_menu_open = not settings_menu_open
            elif settings_menu_open and settings_popup_rect.collidepoint(mouse_pos):
                if clear_popup_button_rect.collidepoint(mouse_pos):
                    holds_on_grid.clear()
                    settings_menu_open = False
                elif save_popup_button_rect.collidepoint(mouse_pos):
                    # open file browser in save mode
                    file_browser_open = True
                    file_browser_mode = 'save'
                    file_browser_files = refresh_file_list()
                    file_browser_selected = 0
                    file_browser_input = ''
                    settings_menu_open = False
                elif load_popup_button_rect.collidepoint(mouse_pos):
                    # open file browser in load mode
                    file_browser_open = True
                    file_browser_mode = 'load'
                    file_browser_files = refresh_file_list()
                    file_browser_selected = 0
                    file_browser_input = ''
                    settings_menu_open = False
            elif settings_menu_open:
                settings_menu_open = False
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
                else:
                    for hold in reversed(holds_on_grid):
                        if hold.rect.collidepoint(mouse_pos):
                            drag_hold = hold
                            holds_on_grid.remove(hold)
                            break

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
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                save_route()

            elif event.key == pygame.K_l:
                load_route()

    # -----------menu-------------
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
    holds_menu.blit(settings_button, settings_button_rect)

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

    if settings_menu_open:
        pygame.draw.rect(screen, (40, 40, 40), settings_popup_rect)
        pygame.draw.rect(screen, (255, 255, 255), settings_popup_rect, 3)

        pygame.draw.rect(screen, (70, 70, 70), clear_popup_button_rect)
        pygame.draw.rect(screen, (255, 255, 255), clear_popup_button_rect, 2)
        clear_button_rect.center = clear_popup_button_rect.center
        screen.blit(clear_button, clear_button_rect)

        pygame.draw.rect(screen, (70, 70, 70), save_popup_button_rect)
        pygame.draw.rect(screen, (255, 255, 255), save_popup_button_rect, 2)
        save_button_rect.center = save_popup_button_rect.center
        screen.blit(save_button, save_button_rect)

        pygame.draw.rect(screen, (70, 70, 70), load_popup_button_rect)
        pygame.draw.rect(screen, (255, 255, 255), load_popup_button_rect, 2)
        load_button_rect.center = load_popup_button_rect.center
        screen.blit(load_button, load_button_rect)

    # Draw file browser
    if file_browser_open:
        # dim background
        overlay = pygame.Surface((display_width, display_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # file browser window
        pygame.draw.rect(screen, (30, 30, 30), file_browser_rect)
        pygame.draw.rect(screen, (200, 200, 200), file_browser_rect, 2)

        title = font.render(("Save File" if file_browser_mode == 'save' else "Load File"), True, (255, 255, 255))
        screen.blit(title, (file_browser_rect.x + 20, file_browser_rect.y + 8))

        # file list
        list_x = file_browser_rect.x + 20
        list_y = file_browser_rect.y + 40
        item_h = 28
        max_items = min(10, len(file_browser_files))
        for i in range(max_items):
            if i >= len(file_browser_files):
                break
            fname = file_browser_files[i]
            item_rect = pygame.Rect(list_x, list_y + i * item_h, file_browser_rect.width - 40, item_h - 2)
            if i == file_browser_selected:
                pygame.draw.rect(screen, (80, 80, 120), item_rect)
            else:
                pygame.draw.rect(screen, (50, 50, 50), item_rect)
            txt = font.render(fname, True, (255, 255, 255))
            screen.blit(txt, (item_rect.x + 6, item_rect.y + 2))

        # input for new filename (save mode)
        input_rect = pygame.Rect(file_browser_rect.x + 20, file_browser_rect.bottom - 95, file_browser_rect.width - 40, 30)
        pygame.draw.rect(screen, (255, 255, 255), input_rect, 1)
        input_txt = font.render(file_browser_input or "Type new filename (optional)", True, (200, 200, 200) if not file_browser_input else (255, 255, 255))
        screen.blit(input_txt, (input_rect.x + 6, input_rect.y + 2))

        # buttons
        confirm_rect = pygame.Rect(file_browser_rect.right - 120, file_browser_rect.bottom - 50, 100, 35)
        cancel_rect = pygame.Rect(file_browser_rect.x + 20, file_browser_rect.bottom - 50, 100, 35)

        pygame.draw.rect(screen, (70, 130, 70), confirm_rect)
        pygame.draw.rect(screen, (200, 200, 200), confirm_rect, 2)
        confirm_txt = font.render("Confirm", True, (255, 255, 255))
        screen.blit(confirm_txt, (confirm_rect.x + 10, confirm_rect.y + 6))

        pygame.draw.rect(screen, (130, 70, 70), cancel_rect)
        pygame.draw.rect(screen, (200, 200, 200), cancel_rect, 2)
        cancel_txt = font.render("Cancel", True, (255, 255, 255))
        screen.blit(cancel_txt, (cancel_rect.x + 10, cancel_rect.y + 6))

    screen.blit(holds_menu, (0, display_height - holds_menu_height))

    pygame.display.flip()