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

# dungeon generation params
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

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
        # move by given amount, if destination is not blocked
        if not map[self.x + dx][self.y + dy].blocked:
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

# rectangle on the map, used to characterize a room
class Rect:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)

    # returns true if this rectangle intersects with another one
    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

# creates a room and fills with unblocked tiles
def create_room(room):
    global map

    # go through the tiles in the rectangle to make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False

# inits map based on global map properties
def make_map():
    global map

    # fill map with "blocked" tiles
    map = [[ Tile(True)
        for y in range(MAP_HEIGHT) ]
            for x in range(MAP_WIDTH) ]

    # loop to iterate until max num of rooms, assigning random coordinates and sizes
    rooms = []
    num_rooms = 0

    for r in range(MAX_ROOMS):
        # random width & height
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        # random position without going out of map boundaries
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

        # "Rect" class makes rectangles easier to work with
        new_room = Rect(x, y, w, h)

        # run through the other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            # this means there are no intersections, so room is valid

            # "paint" it to the map's tiles
            create_room(new_room)

            # center coordinates of new room, will be useful later
            (new_x, new_y) = new_room.center()
            
            #################################################################################################
            # optional: print "room number" to see how the map drawing worked                               #
            #          we may have more than ten rooms, so print 'A' for the first room, 'B' for the next...#
            #################################################################################################
            #room_no = Object(new_x, new_y, chr(65+num_rooms), libtcod.white)
            #objects.insert(0, room_no) #draw early, so monsters are drawn on top

            if num_rooms == 0:
                # this is the first room, PC will start here
                player.x = new_x
                player.y = new_y
            else:
                # all rooms after first:
                #connect it to the previous room with a tunnel

                # center coordinates of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()

                # draw a coin (random number that is 0 or 1)
                if libtcod.random_get_int(0, 0, 1) == 1:
                    # first move horizontally, then vertically
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    # first move vertically, then horizontally
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)
                
            # finally, append new room to list
            rooms.append(new_room)
            num_rooms += 1

# carves a horizontal tunnel
def create_h_tunnel(x1, x2, y):
    global map
    for x in range(min(x1, x2), max(x1, x2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

# carves a vertical tunnel
def create_v_tunnel(y1, y2, x):
    global map
    for y in range(min(y1, y2), max(y1, y2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

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
    if libtcod.console_is_key_pressed(libtcod.KEY_KP8):
        player.move(0, -1)
    
    elif libtcod.console_is_key_pressed(libtcod.KEY_KP2):
        player.move(0, 1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_KP4):
        player.move(-1, 0)

    elif libtcod.console_is_key_pressed(libtcod.KEY_KP6):
        player.move(1, 0)

    elif libtcod.console_is_key_pressed(libtcod.KEY_KP7):
        player.move(-1, -1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_KP9):
        player.move(1, -1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_KP1):
        player.move(-1, 1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_KP3):
        player.move(1, 1)
    
    elif libtcod.console_is_key_pressed(libtcod.KEY_UP):
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