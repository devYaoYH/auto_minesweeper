import sys
import time
import queue
import random
import pygame

from pygame.locals import *

# Constants
FPS = 30
SIZE = 30
MARGIN = 15
HEADER = 50
FOOTER = 100
FONT = None

# PLAY GRID FLAGS
ADJS = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
# PROXIM = ((1, 0), (-1, 0), (0, 1), (0, -1))
MINE = -1
HIDDEN = 0
OPEN = 1
FLAGGED = 2
PEEK_UNDER = False
AUTO_PRESSED = False
GAME_PAUSED = False

MOVE_OPEN = 1
MOVE_FLAG = 2
AUTO_HIDDEN = -1
AUTO_FLAGGED = -2

AUTO_SPEED = 100

GAME_DELAY = 2

# Game Time Counter
GAME_TIME = 0

# Colors
class Color(object):
    def __init__(self, hex_col=None, rgb=None):
        # Default Color (Black)
        self.red = 0
        self.green = 0
        self.blue = 0
        self.rgb = (0, 0, 0)
        self.hex = "#000000"
        if (rgb is not None):
            self.red = rgb[0]
            self.green = rgb[1]
            self.blue = rgb[2]
            self.rgb = rgb
            pre_hex = self.red*16**2 + self.green*16 + self.blue
            self.hex = hex(pre_hex)[2:]
            if (len(self.hex) < 6):
                self.hex = '0'*(6-len(self.hex)) + self.hex
            self.hex = '#' + self.hex
        if (hex_col is not None):
            # Check formatting
            if (hex_col[0] == '#' and len(hex_col) == 7):
                self.red = int(hex_col[1:3], 16)
                self.green = int(hex_col[3:5], 16)
                self.blue = int(hex_col[5:7], 16)
                self.rgb = (self.red, self.green, self.blue)
                self.hex = hex_col
            else:
                print("Hex encoding: {} invalid".format(hex_col))

    def col(self, hex_col):
        if (hex_col == True):
            return self.hex
        return self.rgb

    def darker(self):
        return Color(rgb=(int(0.9*self.red), int(0.9*self.green), int(0.9*self.blue)))

# Default Colors
LIGHTGRAY = Color(hex_col="#cccccc")
MEDIUMGRAY = Color(hex_col="#666666")
DARKGRAY = Color(hex_col="#333333")
WHITE = Color(hex_col="#ffffff")
BLACK = Color(hex_col="#000000")
RED = Color(hex_col="#ff3333")
GREEN = Color(hex_col="#33ff33")
BLUE = Color(hex_col="#3333ff")

# Drawing Utilities
def draw_text(text, font, color, surface, x, y, background=None, margin=0):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.centerx = x
    textrect.centery = y
    if (background is not None):
        pygame.draw.rect(DISPLAY, background, (textrect.centerx - textrect.width/2 - margin, textrect.centery - textrect.height/2 - margin, textrect.width + 2*margin, textrect.height + 2*margin))
    surface.blit(textobj, textrect)

def draw_text_right(text, font, color, surface, x, y, background=None, margin=0):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.centerx = x - textrect.width/2
    textrect.centery = y
    if (background is not None):
        pygame.draw.rect(DISPLAY, background, (textrect.centerx - textrect.width/2 - margin, textrect.centery - textrect.height/2 - margin, textrect.width + 2*margin, textrect.height + 2*margin))
    surface.blit(textobj, textrect)

def draw_text_left(text, font, color, surface, x, y, background=None, margin=0):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.centerx = x + textrect.width/2
    textrect.centery = y
    if (background is not None):
        pygame.draw.rect(DISPLAY, background, (textrect.centerx - textrect.width/2 - margin, textrect.centery - textrect.height/2 - margin, textrect.width + 2*margin, textrect.height + 2*margin))
    surface.blit(textobj, textrect)

def draw_rect(l, w, c, x, y, outline=None):
    # (display surface, color, tuple(left, top, length, width))
    if (outline is None):
        pygame.draw.rect(DISPLAY, c, (x-w/2, y-l/2, l, w))
    elif (len(outline) == 2):
        outline_color, outline_width = outline
        pygame.draw.rect(DISPLAY, c, (x-w/2, y-l/2, l, w))
        pygame.draw.rect(DISPLAY, outline_color, (x-w/2, y-l/2, l, w), outline_width)

def drawButton(text, color, bgcolor, center_x, center_y):
    # similar to drawText but text has bg color and returns obj & rect
    butSurf = FONT.render(text, True, color, bgcolor)
    butRect = butSurf.get_rect()
    butRect.centerx = center_x
    butRect.centery = center_y + butRect.height/2
    DISPLAY.blit(butSurf, butRect)
    return (butSurf, butRect)

def highlightBox(c, r):
    pygame.draw.rect(DISPLAY, GREEN.rgb, (c*SIZE+MARGIN, r*SIZE+MARGIN+HEADER, SIZE, SIZE), 3)

def highlightRect(rect, col):
    pygame.draw.rect(DISPLAY, col, (rect.centerx - rect.width/2, rect.centery - rect.height/2, rect.width, rect.height), 3)

def draw_grid(r, c):
    for y in range(r):
        for x in range(c):
            draw_rect(SIZE, SIZE, MEDIUMGRAY.rgb, (x+0.5)*SIZE+MARGIN, (y+0.5)*SIZE+MARGIN+HEADER, outline=(BLACK.rgb, 3))

def update_LOSE():
    draw_text(":(", FONT, WHITE.rgb, DISPLAY, WIN_X//2, HEADER - 10, background=RED.rgb, margin=3)

def update_WIN():
    draw_text(":)", FONT, WHITE.rgb, DISPLAY, WIN_X//2, HEADER - 10, background=GREEN.rgb, margin=3)

def update_UI(mines):
    # Buttons
    global FONT, DISPLAY, WIN_X
    global RESTART_BTN, AUTO_BTN, DEBUG_NEXT_BTN, AUTO_PRESSED
    RESTART_BTN = drawButton('RESTART', BLACK.rgb, WHITE.rgb, WIN_X/2, WIN_Y - FOOTER)
    AUTO_BTN = drawButton('AUTO_PLAY', BLACK.rgb if not AUTO_PRESSED else WHITE.rgb, WHITE.rgb if not AUTO_PRESSED else GREEN.darker().darker().darker().rgb, WIN_X/2, RESTART_BTN[1].centery + MARGIN)
    DEBUG_NEXT_BTN = drawButton('NEXT MOVE', BLACK.rgb, WHITE.rgb, WIN_X/2, AUTO_BTN[1].centery + MARGIN)

    # Text Handles
    num_mines_left = mines
    c = len(GRID)
    r = len(GRID[0])
    for x in range(c):
        for y in range(r):
            if (PLAY_GRID[x][y] == FLAGGED):
                num_mines_left -= 1
    draw_text_left(str(num_mines_left), FONT, RED.rgb, DISPLAY, MARGIN, HEADER - 10)
    draw_text_right(format_time(int(time.time() - GAME_TIME)), FONT, WHITE.rgb, DISPLAY, WIN_X - MARGIN, HEADER - 10, background=RED.rgb, margin=3)

def update_grid(r, c):
    global PEEK_UNDER
    DISPLAY.fill(LIGHTGRAY.rgb)

    half = int(SIZE*0.5)
    quarter = int(SIZE*0.25)
    eighth = int(SIZE*0.125)
    for x in range(c):
        for y in range(r):
            if (PEEK_UNDER or PLAY_GRID[x][y] == OPEN):
                draw_rect(SIZE, SIZE, LIGHTGRAY.rgb, (x+0.5)*SIZE+MARGIN, (y+0.5)*SIZE+MARGIN+HEADER, outline=(BLACK.rgb, 3))
                txt = ''
                if (GRID[x][y] == MINE):
                    txt = 'X'
                    left = int((x+0.5)*SIZE+MARGIN - SIZE/2)
                    top = int((y+0.5)*SIZE+MARGIN+HEADER - SIZE/2)
                    pygame.draw.circle(DISPLAY, DARKGRAY.rgb, (left+half, top+half), quarter)
                    pygame.draw.circle(DISPLAY, WHITE.rgb, (left+half, top+half), eighth)
                    pygame.draw.line(DISPLAY, DARKGRAY.rgb, (left+eighth, top+half), (left+half+quarter+eighth, top+half))
                    pygame.draw.line(DISPLAY, DARKGRAY.rgb, (left+half, top+eighth), (left+half, top+half+quarter+eighth))
                    pygame.draw.line(DISPLAY, DARKGRAY.rgb, (left+quarter, top+quarter), (left+half+quarter, top+half+quarter))
                    pygame.draw.line(DISPLAY, DARKGRAY.rgb, (left+quarter, top+half+quarter), (left+half+quarter, top+quarter))
                    continue
                elif (GRID[x][y] > 0):
                    txt = str(GRID[x][y])
                draw_text(txt, FONT, BLUE.rgb, DISPLAY, (x+0.5)*SIZE+MARGIN, (y+0.5)*SIZE+MARGIN+HEADER)
            elif (PLAY_GRID[x][y] == FLAGGED):
                draw_rect(SIZE, SIZE, MEDIUMGRAY.rgb, (x+0.5)*SIZE+MARGIN, (y+0.5)*SIZE+MARGIN+HEADER, outline=(BLACK.rgb, 3))
                draw_text('F', FONT, RED.rgb, DISPLAY, (x+0.5)*SIZE+MARGIN, (y+0.5)*SIZE+MARGIN+HEADER)
            else:
                draw_rect(SIZE, SIZE, MEDIUMGRAY.rgb, (x+0.5)*SIZE+MARGIN, (y+0.5)*SIZE+MARGIN+HEADER, outline=(BLACK.rgb, 3))

# Helpers
def format_time(t_secs):
    time_str = ""
    mins = t_secs//60
    secs = t_secs%60
    if (mins < 10):
        time_str = '0' + str(mins) + ':'
    else:
        time_str = str(mins) + ':'
    if (secs < 10):
        time_str += '0' + str(secs)
    else:
        time_str += str(secs)
    return time_str

def getBox(mouse_x, mouse_y, row, col):
    bx = mouse_x - MARGIN
    by = mouse_y - MARGIN - HEADER
    br = by//SIZE
    bc = bx//SIZE
    if (br >= 0 and br < row and bc >= 0 and bc < col):
        return (bc, br)
    else:
        return (None, None)

# Game Logic
def gen_grid(row, col, mines):
    new_grid = [[0 for r in range(row)] for c in range(col)]
    play_grid = [[HIDDEN for r in range(row)] for c in range(col)]
    list_mines = []
    while(mines > 0):
        rx = random.randint(0, col-1)
        ry = random.randint(0, row-1)
        print(rx, ry, file=sys.stderr)
        if (new_grid[rx][ry] != 0):
            continue
        list_mines.append((rx, ry))
        new_grid[rx][ry] = MINE
        mines -= 1
    for rx, ry in list_mines:
        for adj in ADJS:
            nx = rx+adj[0]
            ny = ry+adj[1]
            if (nx >= 0 and nx < col and ny >= 0 and ny < row and new_grid[nx][ny] != MINE):
                new_grid[nx][ny] += 1
    for x in range(col):
        for y in range(row):
            if (new_grid[x][y] == MINE):
                print('X', file=sys.stderr, end="")
            else:
                print(new_grid[x][y], file=sys.stderr, end="")
        print("", file=sys.stderr)
    return (new_grid, play_grid)

def bfs_cells(x, y, row, col):
    if (GRID[x][y] == MINE):
        PLAY_GRID[x][y] = OPEN
        return False
    elif (GRID[x][y] > 0):
        PLAY_GRID[x][y] = OPEN
        return True

    PLAY_GRID[x][y] = OPEN
    q = queue.Queue()
    v = set()

    q.put((x, y))
    v.add((x, y))

    while(not q.empty()):
        loc = q.get()
        if (GRID[loc[0]][loc[1]] == 0):
            for p in ADJS:
                px = loc[0]+p[0]
                py = loc[1]+p[1]
                if ((px, py) not in v and px >= 0 and px < col and py >= 0 and py < row):
                    v.add((px, py))
                    PLAY_GRID[px][py] = OPEN
                    if (GRID[px][py] == 0):
                        q.put((px, py))
    return True

# Event Handlers
def terminate():
    pygame.quit()
    print("bye-bye")
    sys.stdout.flush()
    sys.exit()

def update_keyboard_events():
    global PEEK_UNDER
    if (len(pygame.event.get(QUIT)) > 0):
        terminate()
    keyUpEvents = pygame.event.get(KEYUP)
    keyDownEvents = pygame.event.get(KEYDOWN)
    if (len(keyUpEvents) == 0 and len(keyDownEvents) == 0):
        return (None, None)
    if (len(keyUpEvents) > 0):
        if (keyUpEvents[0].key == K_ESCAPE):
            terminate()
        if (keyUpEvents[0].key == K_BACKSLASH):
            PEEK_UNDER = False
        return (False, keyUpEvents[0].key)
    if (len(keyDownEvents) > 0):
        if (keyDownEvents[0].key == K_BACKSLASH):
            PEEK_UNDER = True
        return (True, keyDownEvents[0].key)

def setup(row, col, mines):
    global FPSCLOCK, DISPLAY, FONT
    pygame.init()
    pygame.display.set_caption("Auto-Minesweeper")
    # Game Window Settings
    global WIN_X, WIN_Y
    WIN_X = col*SIZE + MARGIN*2
    WIN_Y = row*SIZE + MARGIN*2 + HEADER + FOOTER
    DISPLAY = pygame.display.set_mode((WIN_X, WIN_Y))
    FPSCLOCK = pygame.time.Clock()
    # Setup Font
    FONT = pygame.font.Font("Roboto-Regular.ttf", 20)
    # FONT = pygame.font.SysFont('Courier New', 20)
    # Setup Button States
    global AUTO_PRESSED
    AUTO_PRESSED = False
    # Draw Grid
    draw_grid(row, col)
    global GRID, PLAY_GRID
    GRID, PLAY_GRID = gen_grid(row, col, mines)
    global GAME_TIME
    GAME_TIME = time.time()
    global GAME_LOSE, GAME_WIN, LAST_GAME_TIME, LAST_AUTO_TIME
    GAME_LOSE = False
    GAME_WIN = False
    LAST_GAME_TIME = time.time()
    LAST_AUTO_TIME = time.time()

# AI Player
def auto_play(grid):
    list_hints = []
    r = len(grid)
    c = len(grid[0])
    for x in range(r):
        for y in range(c):
            if (grid[x][y] > 0):
                list_hints.append((grid[x][y], x, y))
    list_hints = sorted(list_hints)
    for num, x, y in list_hints:
        hiddens = []
        flagged = []
        for adj in ADJS:
            nx = x + adj[0]
            ny = y + adj[1]
            if (nx >= 0 and ny >= 0 and nx < c and ny < r):
                if (grid[nx][ny] == AUTO_HIDDEN):
                    hiddens.append((nx, ny))
                elif (grid[nx][ny] == AUTO_FLAGGED):
                    flagged.append((nx, ny))
        if (num - len(flagged) == len(hiddens) and len(hiddens) > 0):
            return (MOVE_FLAG, hiddens[0][0], hiddens[0][1])
        elif (num == len(flagged) and len(hiddens) > 0):
            return (MOVE_OPEN, hiddens[0][0], hiddens[0][1])
    return (None, None, None)

# Main Game
def game(row, col, mines):
    global AUTO_PRESSED, GAME_LOSE, GAME_WIN, LAST_GAME_TIME, LAST_AUTO_TIME

    #########
    # SETUP #
    #########
    setup(row, col, mines)

    #############
    # GAME LOOP #
    #############
    mouse_x = 0
    mouse_y = 0

    while True:
        # Refresh Display
        update_grid(row, col)
        update_UI(mines)

        # Restart game after pause
        if ((GAME_LOSE or GAME_WIN) and time.time() - LAST_GAME_TIME > GAME_DELAY):
            setup(row, col, mines)
            pygame.display.update()
            FPSCLOCK.tick(FPS)
            continue

        # Check for Lose
        if (GAME_LOSE):
            update_LOSE()
            print("LOSE", file=sys.stderr)
            pygame.display.update()
            FPSCLOCK.tick(FPS)
            continue
        elif (GAME_WIN):
            update_WIN()
            print("WIN", file=sys.stderr)
            pygame.display.update()
            FPSCLOCK.tick(FPS)
            continue
        else:
            # Check for Win
            possible_win = True
            for r in range(row):
                if (not possible_win):
                    break
                for c in range(col):
                    if (PLAY_GRID[r][c] == HIDDEN):
                        possible_win = False
                        break
                    if (PLAY_GRID[r][c] == FLAGGED and GRID[r][c] != MINE):
                        possible_win = False
                        break
                    if (GRID[r][c] == MINE and PLAY_GRID[r][c] != FLAGGED):
                        possible_win = False
                        break
            if (possible_win):
                GAME_WIN = True
                update_WIN()
                pygame.display.update()
                FPSCLOCK.tick(FPS)
                continue

        LAST_GAME_TIME = time.time()

        # User Interaction
        mouseClicked = False
        spacePressed = False
        key_down, key_event = update_keyboard_events()
        key_up = not key_down

        if (key_down is not None):
            print(key_down, key_event, file=sys.stderr)

        # Keyboard Events
        if (key_down and key_event == K_SPACE):
            spacePressed = True

        for event in pygame.event.get():
            if (event.type == QUIT):
                terminate()
            elif (event.type == MOUSEMOTION):
                mouse_x, mouse_y = event.pos
            elif (event.type == MOUSEBUTTONDOWN):
                mouse_x, mouse_y = event.pos
                mouseClicked = True

        # Check UI Buttons Interaction
        if (RESTART_BTN[1].collidepoint(mouse_x, mouse_y)):
            highlightRect(RESTART_BTN[1], GREEN.rgb)
            if (mouseClicked):
                setup(row, col, mines)
                pygame.display.update()
                FPSCLOCK.tick(FPS)
                continue

        if (AUTO_BTN[1].collidepoint(mouse_x, mouse_y)):
            highlightRect(AUTO_BTN[1], GREEN.rgb)
            if (mouseClicked):
                AUTO_PRESSED = not AUTO_PRESSED

        if (DEBUG_NEXT_BTN[1].collidepoint(mouse_x, mouse_y)):
            highlightRect(DEBUG_NEXT_BTN[1], GREEN.rgb)

        # Check for interactions with grid | Disable Interaction if AUTO PLAYER
        if (not AUTO_PRESSED):
            box_x, box_y = getBox(mouse_x, mouse_y, row, col)
            if (box_x is not None):    # Highlight box
                highlightBox(box_x, box_y)
                if (mouseClicked):
                    # Check if opening this cell is valid
                    if (PLAY_GRID[box_x][box_y] == HIDDEN):
                        GAME_LOSE = not bfs_cells(box_x, box_y, row, col)
                elif (spacePressed):
                    # Check if cell is valid to be flagged
                    if (PLAY_GRID[box_x][box_y] == HIDDEN):
                        PLAY_GRID[box_x][box_y] = FLAGGED
                    elif (PLAY_GRID[box_x][box_y] == FLAGGED):
                        PLAY_GRID[box_x][box_y] = HIDDEN
        elif (time.time() - LAST_AUTO_TIME >= 1/AUTO_SPEED):
            # Auto-Solve board
            grid = [[AUTO_HIDDEN for y in range(col)] for x in range(row)]
            for x in range(row):
                for y in range(col):
                    if (PLAY_GRID[x][y] == OPEN):
                        grid[x][y] = GRID[x][y]
                    elif (PLAY_GRID[x][y] == FLAGGED):
                        grid[x][y] = AUTO_FLAGGED

            result, x, y = auto_play(grid)
            if (result == MOVE_OPEN):
                GAME_LOSE = not bfs_cells(x, y, row, col)
            elif (result == MOVE_FLAG):
                PLAY_GRID[x][y] = FLAGGED
            elif (result is None):
                AUTO_PRESSED = False
            LAST_AUTO_TIME = time.time()

        pygame.display.update()
        FPSCLOCK.tick(FPS)

# Test a game
argc = len(sys.argv)
argv = sys.argv
if (argc == 2 and int(argv[1]) > 0):
    game(15, 15, int(argv[1]))
elif (argc == 4 and int(argv[1]) > 0 and int(argv[2]) > 0 and int(argv[3]) > 0):
    r = int(argv[1])
    c = int(argv[2])
    m = int(argv[3])
    game(r, c, m)
else:
    game(15, 15, 20)