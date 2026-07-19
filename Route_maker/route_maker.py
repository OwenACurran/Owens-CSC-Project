"""This program manages climbing routes.

It allows for the manual or automatic creation of routes,
which can then be saved to a json file.
"""
import pygame
from dataclasses import dataclass
import json
import os

pygame.init()

# Sets up directorys so the program can be run anywhere and work (Constant since they never change)
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
menu_dragging = False
SPACING_ON_HOLDS_menu = 80
ROOM_FOR_BUTTONS = 200
on_row = 0

# Creates a font
FONT_SIZE = 30
font = pygame.font.Font(None, FONT_SIZE) # Pygame default font

# Draws the text with the default pygame font
clear_button = font.render("Clear", True, "Black")
save_button = font.render("Save", True, "Black")
load_button = font.render("Load", True, "Black")

# Assigns a pygame Rect object that matches the height and width of the text
clear_button_rect = clear_button.get_rect()
save_button_rect = save_button.get_rect()
load_button_rect = load_button.get_rect()

# Defaults for the settings menu
settings_menu_open = False 
settings_popup_rect = pygame.Rect(0, 0, 220, 180)

# Creation of variables for the file browser
file_browser_open = False
file_browser_mode = None
file_browser_files = []
file_browser_selected = 0
file_browser_input = ""
file_browser_rect = pygame.Rect(0, 0, 520, 420)

# Constants for the file browser
FILE_BROWSER_LIST_X_OFFSET = 20
FILE_BROWSER_LIST_Y_OFFSET = 40
FILE_BROWSER_ITEM_HEIGHT = 28
FILE_BROWSER_MAX_VISIBLE_ITEMS = 10


def get_file_browser_item_rects() -> list[pygame.Rect]: 
    """Make file rects for the file browser."""
    # Starting pos for files
    list_x = file_browser_rect.x + FILE_BROWSER_LIST_X_OFFSET
    list_y = file_browser_rect.y + FILE_BROWSER_LIST_Y_OFFSET

    max_items = min(FILE_BROWSER_MAX_VISIBLE_ITEMS, len(file_browser_files)) # Caps the amout of rects that can be displayed

    # Returning a list of rects
    rects = []
    for i in range(max_items):
        rects.append(pygame.Rect(list_x, list_y + i * FILE_BROWSER_ITEM_HEIGHT, file_browser_rect.width - 40, FILE_BROWSER_ITEM_HEIGHT - 2))
    return rects



def refresh_file_list():
    """Makes a list of files for all the files in the save folder that end with .json"""
    try:
        files = [] 
        for file in os.listdir(SAVES_FOLDER_NAME): # Iterates through the saves folder for each file inside
            if file.lower().endswith(".json"): # Ensures that the file ends with .json (not case sensitive)
                files.append(file)
    # Stops the error when there are no files in the saves
    except FileNotFoundError:
        files = [] 

    return files


#---------Image loading---------
try:
    #  Load images and scales and flips them to the appropriate sizes
    settings_button = pygame.image.load(SETTINGS_BUTTON_PATH).convert_alpha()
    settings_button = pygame.transform.scale(settings_button, (60, 60))
    right_arrow = pygame.image.load(RIGHT_ARROW_PATH).convert_alpha()
    right_arrow = pygame.transform.scale(right_arrow, (50, 50))
    left_arrow = pygame.transform.flip(right_arrow, True, False)

    # If the image files are not found, this will create a new surface with filled in colours to represent the buttons
except FileNotFoundError:
    print("Failed to load image")
    right_arrow = pygame.Surface((50, 50))
    right_arrow.fill("black")
    left_arrow = pygame.Surface((50, 50))
    left_arrow.fill("black")
    settings_button = pygame.Surface((60,60))
    settings_button.fill("red")


def length_from_mouse_pos(v):
    """Uses pygamethagoras's theorem to compare relative distances from the mouse.
    Does not give exact distance since no square root.
    """
    mouse = pygame.mouse.get_pos()
    return (v[0] - mouse[0]) ** 2 + (v[1] - mouse[1]) ** 2



# ---------Grid class----------
class Grid:
    """Creates a grid after update method is called. Can take a tuple for size"""
    def __init__(self, size: tuple=(10, 10)):
        self.x = 0
        self.y = 0
        self.size = size
        self.gap = 1
        self.grid = []

    def update(self, menu_height, width, height):
        """Update the grid if the window changes size"""

        self.width = width 
        self.height = (height - menu_height) # Adjust for the room that the hold menu takes up

        # Finds the correct gap between cells for space on the window
        self.gapx = self.width // self.size[0]
        self.gapy = self.height // self.size[1]
        self.gap = min(self.gapx, self.gapy) # Takes whichever gap is smaller so that the grid will fit in the screen
        
        # Centres the grid on the screen
        self.x = (self.width - self.gap * (self.size[0] - 1)) // 2
        self.y = (self.height - self.gap * (self.size[1] - 1)) // 2

        # Add the positions of the grid cells to the grid list
        self.grid = []
        for w in range(self.size[0]):
            for h in range(self.size[1]):  
                self.grid.append((self.x + w * self.gap, self.y + h * self.gap))

# Makes a grid with the grid class
grid = Grid((25, 25))
grid.update(holds_menu_height,display_width, display_height) # Initial layout

#--------Making Classes-----------


@dataclass # Makes code tidy by doing __init__ for you
class ProcessedHold:
    """Stores data for holds"""
    radius: int
    colour: str
    x : int
    y : int
    row : int

class DisplayedHold:
    """Stores data for holds that are being displayed on screen"""
    def __init__(self, hold_clicked: ProcessedHold):
        self.x, self.y = hold_clicked.x, hold_clicked.y 
        self.colour = hold_clicked.colour 
        self.radius = hold_clicked.radius 
        
        # Track which grid coordinate this holds belongs to
        self.grid_col = None
        self.grid_row = None
        self.is_on_grid = False
        
        self.update() # Calls the update method

    def update(self):
        """Updates the rect and size of the displayed hold for the size of the grid"""
        self.displayed_size = self.radius * grid.gap / 50 # Bases it off of the gap between points in the grid
        
        # Recalculate the position when the grids x and y coordinates change
        if self.is_on_grid:
            if self.grid_col != None:
                if self.grid_row != None:
                    self.x = grid.x + self.grid_col * grid.gap
                    self.y = grid.y + self.grid_row * grid.gap
       
        # Updates the size and position of the rect so the mouse can click it
        self.mouse_rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        self.mouse_rect.center = (self.x, self.y)

def save_route(filename=None):
    """Creates a json file for a route with the defualt being route.json"""

    # Defualts to route.json
    if filename == None:
        filename = "route.json"

    

    # Adds the data to a list for each hold displayed on the grid
    data = []
    for hold in holds_on_grid:
        data.append({
            "radius": hold.radius,
            "colour": hold.colour,
            "grid_col": hold.grid_col,
            "grid_row": hold.grid_row
        })


    path = os.path.join(SAVES_FOLDER_NAME, filename) # Makes the path complete

    # Makes a new save file if one with the name doesn't already exist and adds the data
    with open(path, "w") as f:
        json.dump(data, f, indent=4) # Indent 4 makes the data readable


def load_route(filename=None):
    """This function will clear the grid of all the current holds, and will load from a save file."""
    if filename is None:
        filename = "route.json" # Default for loading

  
    path = os.path.join(SAVES_FOLDER_NAME, filename) # Makes the path complete

    # Loads the data from the save file into data[]
    with open(path, "r") as f:
        data = json.load(f)

    holds_on_grid.clear() # Clears the current grid


    for item in data:
        # Makes a DisplayedHold object for the hold
        hold = DisplayedHold(
            ProcessedHold(
                radius = item["radius"],
                colour = item["colour"],
                x = 0,
                y = 0,
                row = 0
            )
        )

        # Assigns the hold a position on the grid
        hold.grid_col = item["grid_col"]
        hold.grid_row = item["grid_row"]
        hold.is_on_grid = True

        hold.update() # Makes the hold appear on the screen

        holds_on_grid.append(hold) # Adds the hold to the list of holds being shown on screen

# --------------Holds dictionary and size, colour, and type variables-------------- 
try:
    # Loads the inventory file into the program
    with open("inventory.json", "r") as f:
        holds_data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError): # Prevents crash if the inventory file is missing of there isn't any data in it
        holds_data = []

# How large the holds will be depending on size given
size_properies = {
    "Tiny": 10,
    "Small": 15,
    "Medium": 20,
    "Large": 30
}

# Matches the colour to a hex value
colour_properies = {
    "Black": "#000000",
    "Blue": "#0000ff",
    "Red": "#ff0000",
    "Green": "#31b431",
    "Yellow": "#ffff00",
    "Purple": "#BD5DBD",
    "Orange": "#FF9100"
}

# Creates and lists that will be used in the loop
drag_hold = False
holds_on_grid: list[DisplayedHold] = []
menu_displayed_holds: list[DisplayedHold] = []
possible_rows = 1

def regenerate_menu():
    """Generates menu items"""
    global menu_displayed_holds, possible_rows, holds_menu_width, holds_menu_height
    
    # Calculates how many hold should be displayed in the menu, adjusts for the room required for buttons
    holds_menu_width = pygame.display.get_window_size()[0]
    usable_width = holds_menu_width - ROOM_FOR_BUTTONS
    holds_per_row = max(1, usable_width // SPACING_ON_HOLDS_menu)

    rows_visible = max(1, holds_menu_height // 70) # How many vertical row should be visible

    processed_holds_data: list[ProcessedHold] = []

    # Calculatation of where each hold should be and what row it goes on
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

    # Calculates possible rows
    possible_rows = (processed_holds_data[-1].row + 1) if processed_holds_data else 1 # Prevents crash if there is nothing in processed holds data
    possible_rows = max(1, possible_rows) # Ensure there is always 1 row visible

    
    menu_displayed_holds = []
    
    # Calculates the y position of the hold in the menu based off of the slot its in
    for hold in processed_holds_data:
        row_slot = (hold.row - on_row) % possible_rows # Uses modulo to make it loop around
        y = (holds_menu_height // (rows_visible + 1)) * (row_slot + 1)

        # Hides the rows that there isn't space for
        if row_slot < rows_visible: 
            disp_hold = DisplayedHold(hold) 
            disp_hold.y = y
            disp_hold.update() # Moves the rect that allows the mouse to click the hold (important since holds change pos)
            menu_displayed_holds.append(disp_hold)


regenerate_menu()

# --------------Main loop-------------- 
run = True
while run:

    #--------Menu Setup---------

    # Getting rects for the buttons
    l_arrow_rect = left_arrow.get_rect(center =(holds_menu_width - 150, holds_menu_height // 2))
    r_arrow_rect = right_arrow.get_rect(center = (holds_menu_width - 100, holds_menu_height // 2))
    settings_button_rect = settings_button.get_rect(center = (holds_menu_width -50, holds_menu_height))

    # Positioning the menus and buttons based on display
    display_width, display_height = pygame.display.get_window_size()
    holds_menu_width = display_width
    settings_button_rect.center = (display_width - 40, holds_menu_height // 2)
    file_browser_rect.center = (display_width // 2, display_height // 2)
    settings_popup_rect.width = 200
    settings_popup_rect.height = 170
    settings_popup_rect.center = (display_width // 2, display_height // 2)

    # Pop up menu buttons
    popup_button_width = settings_popup_rect.width - 40
    clear_popup_button_rect = pygame.Rect(settings_popup_rect.x + 20, settings_popup_rect.y + 15, popup_button_width, 40)
    save_popup_button_rect = pygame.Rect(settings_popup_rect.x + 20, settings_popup_rect.y + 65, popup_button_width, 40)
    load_popup_button_rect = pygame.Rect(settings_popup_rect.x + 20, settings_popup_rect.y + 115, popup_button_width, 40)

    # ----------Event handling-------------

    # Setting varibles that are needed for the event handling
    drag_area_for_menu = pygame.Rect(0, display_height - holds_menu_height - 5, display_width, 10)
    mouse_pos = pygame.mouse.get_pos()
    holds_menu_width = display_width
    clicked_hold = False


    for event in pygame.event.get():
        # ---------File browser event handling-------------
        if file_browser_open:
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Will close the file browser if clicked elsewhere
                if not file_browser_rect.collidepoint(mouse_pos):
                    file_browser_open = False
                    

                # Determines which file was clicked
                for i, rect in enumerate(get_file_browser_item_rects()):
                    if rect.collidepoint(mouse_pos):
                        file_browser_selected = i
                        break
                
                
                if confirm_rect.collidepoint(mouse_pos):
                    # Saving a file
                    if file_browser_mode == 'save':
                        # Strips spaces if a name gets typed
                        if file_browser_input.strip():
                            chosen = file_browser_input.strip()

                        # Otherwise it will use the selected file in the list
                        elif file_browser_files:
                            chosen = file_browser_files[file_browser_selected]

                        # Defaults to route.json if nothing selected
                        else:
                            chosen = None

                        # Ensures the file ends with .json
                        if chosen != None:
                            if not chosen.lower().endswith('.json'):
                                chosen += '.json'
                        save_route(chosen)

                    # Loading a file
                    else:
                        if file_browser_files:
                            chosen = file_browser_files[file_browser_selected]
                            load_route(chosen)
                    file_browser_open = False
                    
                # Will close the file browser if cancel is clicked
                if cancel_rect.collidepoint(mouse_pos):
                    file_browser_open = False
                    

            elif event.type == pygame.KEYDOWN:
                # Allows typing in the file browser if in save mode and there is room for more files
                save_can_type = file_browser_mode == 'save' and len(file_browser_files) < FILE_BROWSER_MAX_VISIBLE_ITEMS
                if file_browser_mode == 'save':
                    if event.key == pygame.K_BACKSPACE and save_can_type:
                        file_browser_input = file_browser_input[:-1] # Removes the last character from the string
                    else:
                        # Saves character input
                        if save_can_type and 32 <= ord(event.unicode) <= 126: # Keeps the ASCII between 32 and 126 (printable characters)
                            file_browser_input += event.unicode

        # ---------Main event handling-------------
        if event.type == pygame.QUIT: 
            run = False
        # resizes the window and updates the grid and menu when the window is resized
        elif event.type == pygame.VIDEORESIZE:
            display_width = max(event.size[0], 400)
            display_height = max(event.size[1], 400)
            screen = pygame.display.set_mode((display_width, display_height), pygame.RESIZABLE)
            grid.update(holds_menu_height,display_width, display_height)
            regenerate_menu()

        # Handles clicking and dragging of holds and buttons
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if drag_area_for_menu.collidepoint(mouse_pos):
                menu_dragging = True

            # Arrow click detection
            elif l_arrow_rect.move(0, display_height - holds_menu_height).collidepoint(mouse_pos):
                on_row = (on_row - 1) % possible_rows # Loops around
                regenerate_menu()
            elif r_arrow_rect.move(0, display_height - holds_menu_height).collidepoint(mouse_pos):
                on_row = (on_row + 1) % possible_rows # Loops around
                regenerate_menu()
            
            # Settings button click detection
            elif settings_button_rect.move(0, display_height - holds_menu_height).collidepoint(mouse_pos):
                settings_menu_open = not settings_menu_open
            
            # If clicked on the settings menu
            elif settings_menu_open and settings_popup_rect.collidepoint(mouse_pos):
                # Clears the grid of holds
                if clear_popup_button_rect.collidepoint(mouse_pos):
                    holds_on_grid.clear()
                    settings_menu_open = False
                elif save_popup_button_rect.collidepoint(mouse_pos):
                    # open file browser in save mode
                    file_browser_open = True
                    file_browser_mode = 'save'
                    file_browser_files = refresh_file_list()
                    file_browser_input = ''
                    file_browser_selected = 0
                    settings_menu_open = False
                elif load_popup_button_rect.collidepoint(mouse_pos):
                    # open file browser in load mode
                    file_browser_open = True
                    file_browser_mode = 'load'
                    file_browser_files = refresh_file_list()
                    file_browser_selected = 0
                    settings_menu_open = False

            # Close if clicked ouside the menu
            elif settings_menu_open:
                settings_menu_open = False
            
            # Dragging of holds
            else:
                clicked_hold = None
                for hold in menu_displayed_holds:
                    # Detects which hold was clicked
                    if hold.mouse_rect.move(0, display_height - holds_menu_height).collidepoint(mouse_pos):
                        clicked_hold = hold
                        break

                if clicked_hold:
                    # Makes the clicked hold into a DisplayedHold object
                    drag_hold = DisplayedHold(
                        ProcessedHold(
                            radius=clicked_hold.radius,
                            colour=clicked_hold.colour,
                            x=clicked_hold.x,
                            y=clicked_hold.y,
                            row=0
                        )
                    )

                    drag_hold.y += (display_height - holds_menu_height) # Initial y pos needs to be adjusted correctly
                    drag_hold.update()
                else:
                    # Allows for the movement of holds on the grid
                    for hold in reversed(holds_on_grid): # Reversing it allow them to be picked up in the order they were placed
                        if hold.mouse_rect.collidepoint(mouse_pos):
                            drag_hold = hold
                            holds_on_grid.remove(hold)
                            break
        
        # Snap to grid
        elif event.type == pygame.MOUSEMOTION:
            if drag_hold:
                if grid.x <= event.pos[0] <= grid.x + grid.gap * (grid.size[0] - 1) and grid.y <= event.pos[1] <= grid.y + grid.gap * (grid.size[1] - 1): # Checks to see if it's on the grid
                    snap_x, snap_y = min(grid.grid, key = length_from_mouse_pos) # It will compare distances for every point on the grid and will find the minimum one
                    drag_hold.x, drag_hold.y = snap_x, snap_y # Sets the coordinates of the hold to the point on the grid it snaps to
                    
                    # Finds which collumn and row the hold belongs to
                    drag_hold.grid_col = round((snap_x - grid.x) / grid.gap)
                    drag_hold.grid_row = round((snap_y - grid.y) / grid.gap)
                    drag_hold.is_on_grid = True
                else: 
                    # Will go directly to the mouse if the mouse isn't hovering over the grid
                    drag_hold.x, drag_hold.y = event.pos
                    drag_hold.is_on_grid = False
                drag_hold.update()
                
        
        elif event.type == pygame.MOUSEBUTTONUP:
            # If the hold is being dragged and is on the grid, it will be added to the list of holds on the grid
            if drag_hold and drag_hold.is_on_grid:
                holds_on_grid.append(drag_hold)
            drag_hold = False
            menu_dragging = False

    # -----------menu-------------
    # Creates a surface for the menu and fills it gray
    holds_menu = pygame.Surface((holds_menu_width, holds_menu_height))
    holds_menu.fill(("#c8c8c8"))

    # Changes the cursor to a resizing cursor
    if drag_area_for_menu.collidepoint(mouse_pos):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENS)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    # Will update the menu height when its dragged
    if menu_dragging:
        new_mouse_y = mouse_pos[1]
        new_height = display_height - new_mouse_y
        min_h = 70 # Minimum height
        max_h = 70 * possible_rows # Height limit
        holds_menu_height = max(min_h, min(max_h, new_height))
        regenerate_menu()
        

    pygame.draw.line(holds_menu, ("#000000"), (0, 0), (holds_menu_width, 0), 2) # separator line
    grid.update(holds_menu_height,display_width, display_height)
    
    # Moves the holds on the grid to their new positions if the grid has been resized
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

    # Draws the grid points
    for cell in grid.grid:
        pygame.draw.circle(screen, ("#000000"), cell, 2)
    
    # Draws the holds on the grid
    if holds_on_grid:
        for hold in holds_on_grid:
            pygame.draw.circle(screen,
                            color = hold.colour, 
                            center = (hold.x, hold.y),
                            radius = max(2, int(hold.displayed_size))
                            )

    # Draws the hold currently being dragged
    if drag_hold:
        pygame.draw.circle(screen,
                        color = drag_hold.colour,
                        center = (drag_hold.x, drag_hold.y),
                        radius = max(2, int(drag_hold.displayed_size))
                        )

    # Drawing the settings menu
    if settings_menu_open:
        # Draws the setting popup with a border
        pygame.draw.rect(screen, "#282828", settings_popup_rect)
        pygame.draw.rect(screen, "#ffffff", settings_popup_rect, 3)

        # Draws a clear button witha border
        pygame.draw.rect(screen, "#464646", clear_popup_button_rect)
        pygame.draw.rect(screen, "#ffffff", clear_popup_button_rect, 2)
        clear_button_rect.center = clear_popup_button_rect.center
        screen.blit(clear_button, clear_button_rect)

        # Draws a save button with a border
        pygame.draw.rect(screen, "#464646", save_popup_button_rect)
        pygame.draw.rect(screen, "#ffffff", save_popup_button_rect, 2)
        save_button_rect.center = save_popup_button_rect.center
        screen.blit(save_button, save_button_rect)

        # Draws a load button with a border
        pygame.draw.rect(screen, "#464646", load_popup_button_rect)
        pygame.draw.rect(screen, "#FFFFFF", load_popup_button_rect, 2)
        load_button_rect.center = load_popup_button_rect.center
        screen.blit(load_button, load_button_rect)

    # Draw file browser
    if file_browser_open:

        # Background
        pygame.draw.rect(screen, "#1e1e1e", file_browser_rect)
        pygame.draw.rect(screen, "#c8c8c8", file_browser_rect, 2)

        title = font.render(("Save File" if file_browser_mode == 'save' else "Load File"), True, "#ffffff") # Changes based on mode
        screen.blit(title, (file_browser_rect.x + 20, file_browser_rect.y + 8)) 

        # Drawing the files list
        for i, rect in enumerate(get_file_browser_item_rects()):
            file_name = file_browser_files[i]
            # Selected
            if i == file_browser_selected:
                pygame.draw.rect(screen, "#505078", rect)
            else:
            # Not selected
                pygame.draw.rect(screen, "#323232", rect)
            txt = font.render(file_name, True, (255, 255, 255))
            screen.blit(txt, (rect.x + 6, rect.y + 2))

        # Only shows the typing box if there is less than the maximum amount of visible files
        save_can_type = file_browser_mode == 'save' and len(file_browser_files) < FILE_BROWSER_MAX_VISIBLE_ITEMS
        if save_can_type:
            input_rect = pygame.Rect(file_browser_rect.x + 20, file_browser_rect.bottom - 95, file_browser_rect.width - 40, 30)
            pygame.draw.rect(screen, (255, 255, 255), input_rect, 1)
            input_txt = font.render(file_browser_input or "Type new filename (optional)", True, (200, 200, 200) if not file_browser_input else (255, 255, 255))
            screen.blit(input_txt, (input_rect.x + 6, input_rect.y + 2))

        # Drawing confirm and cancel buttons
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

    screen.blit(holds_menu, (0, display_height - holds_menu_height)) # Adds the holds menu surface to the main screen

    pygame.display.flip() # Updates display