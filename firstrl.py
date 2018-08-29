import libtcodpy as libtcod

# First RL
# Aug 29, 2018

# libtcod settings, size of window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

LIMIT_FPS = 20

# keyboard input support
def handle_keys():
    global playerx, playery

    # keys to toggle FULLSCREEN, exit game
    key = libtcod.console_wait_for_keypress(True)
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt + Enter: toggles fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    # EXITs game
    elif key.vk == libtcod.KEY_ESCAPE:
        return True

    # movement keys
    if libtcod.console_is_key_pressed(libtcod.KEY_UP):
        playery -= 1
    
    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
        playery += 1

    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
        playerx -= 1

    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
        playerx += 1

############################################################################
# Main loop, keeps running the logic of game as long as window is not closed
############################################################################

# Set font
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)

# initialize libtcod window
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)

# set fps
libtcod.sys_set_fps(LIMIT_FPS)

# track PC position
playerx = SCREEN_WIDTH/2
playery = SCREEN_HEIGHT/2

while not libtcod.console_is_window_closed():
    # sets print location to console, font color to white
    libtcod.console_set_default_foreground(0, libtcod.white)

    # print a character to (1, 1)
    libtcod.console_put_char(0, playerx, playery, '@', libtcod.BKGND_NONE)

    # present changes to screen
    libtcod.console_flush()

    # print a space to replace PC char after moving
    libtcod.console_put_char(0, playerx, playery, ' ', libtcod.BKGND_NONE)

    # handle keys and exit game if needed
    exit = handle_keys()
    if exit:
        print "Exiting game..."
        break