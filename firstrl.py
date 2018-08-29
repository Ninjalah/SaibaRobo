import libtcodpy as libtcod

# First RL
# Aug 29, 2018

# libtcod settings, size of window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

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

# keyboard input support
def handle_keys():
    global playerx, playery

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

while not libtcod.console_is_window_closed():
    # draw all objects in the list
    for object in objects:
        object.draw()

    # blit contents of new console to root console, display
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
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