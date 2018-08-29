import libtcodpy as libtcod

# First RL
# Aug 29, 2018

# libtcod settings
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)

# initialize libtcod window
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)

# Main loop, keeps running the logic of game as long as window is not closed
while not libtcod.console_is_window_closed():
    # sets print location to console, font color to white
    libtcod.console_set_default_foreground(0, libtcod.white)

    # print a character to (1, 1)
    libtcod.console_put_char(0, 1, 1, '@', libtcod.BKGND_NONE)

    # present changes to screen
    libtcod.console_flush()