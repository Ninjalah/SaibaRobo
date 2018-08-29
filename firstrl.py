import libtcodpy as libtcod

# First RL
# Aug 29, 2018

# libtcod settings, size of window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
# size of map
MAP_WIDTH = 80
MAP_HEIGHT = 45

# set color of map tiles
color_dark_wall = libtcod.Color(0, 0, 100)
color_dark_ground = libtcod.Color(50, 50, 150)

LIMIT_FPS = 20

# track PC position
playerx = SCREEN_WIDTH/2
playery = SCREEN_HEIGHT/2

# generic object definition: player, monster, item, stairs, etc.
# always represented by a character on screen
class Object:
    def __init__(self, x, y, char, color):
        self.x = x
        self.y = y
        self.char = char
        self.color = color

    # move by given amount
    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    # set the color and then draw char that represents this object at its position
    def draw(self):
        libtcod.console_set_default_foreground(con, self.color)
        libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    # erases the char that represents this object
    def clear(self):
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

# tile of the map and its properties
class Tile:
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked

        # by default, if a tile is blocked, it also blocks sight
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight

# inits map based on global map properties
def make_map():
    global map

    # fill map with "unblocked" tiles
    map = [[ Tile(False)
        for y in range(MAP_HEIGHT) ]
            for x in range(MAP_WIDTH) ]

    #############################
    # Place two pillars to TEST #
    #############################
    map[30][22].blocked = True
    map[30][22].block_sight = True
    map[50][22].blocked = True
    map[50][22].block_sight = True

# render all objects in object list
def render_all():
    global color_light_wall
    global color_light_ground

    # iterate through all tiles and set their background color
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            wall = map[x][y].block_sight
            if wall:
                libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
            else:
                libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)

    # draw all objects in object list
    for object in objects:
        object.draw()

    # blit contents of new console to root console, display
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)

# keyboard input support
def handle_keys():
    # keys to toggle FULLSCREEN, exit game
    key = libtcod.console_wait_for_keypress(True)
    if key.vk == libtcod.KEY_ENTER and key.ralt:
        # Alt + Enter: toggles fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    # EXITs game
    elif key.vk == libtcod.KEY_ESCAPE:
        return True

    # movement keys
    if libtcod.console_is_key_pressed(libtcod.KEY_UP):
        player.move(0, -1)
    
    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
        player.move(0, 1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
        player.move(-1, 0)

    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
        player.move(1, 0)

##############################################################################
# Main loop, keeps running the logic of game as long as window is not closed #
##############################################################################

# Set font
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
# initialize libtcod window
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)
# set fps
libtcod.sys_set_fps(LIMIT_FPS)
# initialize off-screen console
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

# create object representing PC
player = Object(SCREEN_WIDTH/2, SCREEN_HEIGHT/2, '@', libtcod.white)

# create an NPC
npc = Object(SCREEN_WIDTH/2, SCREEN_HEIGHT/2, '@', libtcod.yellow)

# the list of objects
objects = [npc, player]

# generate map (not drawn to the screen at this point)
make_map()

while not libtcod.console_is_window_closed():
    # draw all objects in the list
    render_all()

    # present changes to screen
    libtcod.console_flush()

    # erase all objects at their old locations before they move
    for object in objects:
        object.clear()

    # handle keys and exit game if needed
    exit = handle_keys()
    if exit:
        print "Exiting game..."
        break