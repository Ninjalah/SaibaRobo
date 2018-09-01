import libtcodpy as libtcod
import math
import textwrap
 
#actual size of the window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
 
#size of the map
MAP_WIDTH = 80
MAP_HEIGHT = 43

# sizes and coordinates relevant for the GUI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1
INVENTORY_WIDTH = 50
 
# parameters for dungeon generator (num of monsters, items, etc.)
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3
MAX_ROOM_ITEMS = 2

# spell values
HEAL_AMOUNT = 10
LIGHTNING_DAMAGE = 20
LIGHTNING_RANGE = 5
CONFUSE_NUM_TURNS = 10
CONFUSE_RANGE = 8
IMPACT_GRENADE_RADIUS = 3
IMPACT_GRENADE_DAMAGE = 12
 
FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = True  #light walls or not
TORCH_RADIUS = 10
 
LIMIT_FPS = 20  #20 frames-per-second maximum
 
color_dark_wall = libtcod.Color(0, 0, 100)
color_light_wall = libtcod.Color(130, 110, 50)
color_dark_ground = libtcod.Color(50, 50, 150)
color_light_ground = libtcod.Color(200, 180, 50)

fov_recompute = True
game_state = 'playing'

#####################
# CLASS DEFINITIONS #
#####################

class Tile:
    #a tile of the map and its properties
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked

        # all tiles start unexplored
        self.explored = False
 
        #by default, if a tile is blocked, it also blocks sight
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight
 
class Rect:
    #a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
 
    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)
 
    def intersect(self, other):
        #returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)
 
class Object:
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, blocks=False, fighter=None, ai=None, item=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.fighter = fighter
        if self.fighter: #let the fighter component know who owns it
            self.fighter.owner = self

        self.ai = ai
        if self.ai: #let the AI component know who owns it
            self.ai.owner = self

        self.item = item
        if self.item: # let the Item component know who owns it
            self.item.owner = self
 
    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def move_towards(self, target_x, target_y):
        # vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # normalize it to length 1 (preserving direction), then round it and
        # convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def distance_to(self, other):
        # return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def distance(self, x, y):
        # return to distance to some coordinates
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    # make this object be drawn first, so all others appear above it if they're in the same tile
    def send_to_back(self):
        global objects
        objects.remove(self)
        objects.insert(0, self)
 
    def draw(self):
        #only show if it's visible to the player
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
            #set the color and then draw the character that represents this object at its position
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
 
    def clear(self):
        #erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

# combat-related properties and methods (monster, player, NPC)
class Fighter:
    def __init__(self, hp, defense, power, death_function=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function

    # a simple formula for attack damage
    def attack(self, target):
        damage = self.power - target.fighter.defense

        if damage > 0:
            # make the target take some damage
            message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)
        else:
            message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')

    # apply damage if possible
    def take_damage(self, damage):
        if damage > 0:
            self.hp -= damage

            # check for death. if there's a death function, call it
            if self.hp <= 0:
                function = self.death_function
                if function is not None:
                    function(self.owner)

    # heal by the given amount, without going over maximum
    def heal(self, amount):
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp

# AI for basic monsters
class BasicMonster:
    def take_turn(self):
        # a basic monster takes its turn. If you can see it, it can see you
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):

            # move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)
            
            # close enough, attack! (if the player is still alive)
            elif player.fighter.hp > 0:
                monster.fighter.attack(player)

# AI for a temporarily confused monster (reverts to previous AI after a while).
class ConfusedMonster:
    def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns

    def take_turn(self):
        if self.num_turns > 0: # monster still confused...
            # move in a random direction, and decrease the number of turns confused
            self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
            self.num_turns -= 1
        else: # restore the previous AI (this one will be deleted because it's not referenced anymore)
            self.owner.ai = self.old_ai
            message('The ' + self.owner.name + ' is no longer confused!', libtcod.red)

# an item that can be picked up and used
class Item:
    def __init__(self, use_function=None):
        self.use_function = use_function

    def pick_up(self):
        # add to the player's inventory and remove from map
        if len(inventory) >= 26: # limited to 26 as there are 26 letters in the alphabet, A - Z
            message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.yellow)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '!', libtcod.green)

    def drop(self):
        # add to the map and remove from the player's inventory. also, place it at the player's coordinates
        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message('You dropped a ' + self.owner.name + '.', libtcod.yellow)

    def use(self):
        # just call the "use_function" if it is defined
        if self.use_function is None:
            message('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self.owner) # destroy after use, unless it was cancelled for some reason

########################
# FUNCTION DEFINITIONS #
########################

# tests a map tile if blocked or not
def is_blocked(x, y):
    if map[x][y].blocked:
        return True

    # check for any blocking objects
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False
 
def create_room(room):
    global map
    #go through the tiles in the rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False
 
def create_h_tunnel(x1, x2, y):
    global map
    #horizontal tunnel. min() and max() are used in case x1>x2
    for x in range(min(x1, x2), max(x1, x2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False
 
def create_v_tunnel(y1, y2, x):
    global map
    #vertical tunnel
    for y in range(min(y1, y2), max(y1, y2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False
 
def make_map():
    global map, objects

    #the list of objects with those two
    objects = [player]
 
    #fill map with "blocked" tiles
    map = [[ Tile(True)
        for y in range(MAP_HEIGHT) ]
            for x in range(MAP_WIDTH) ]
 
    rooms = []
    num_rooms = 0
 
    for r in range(MAX_ROOMS):
        #random width and height
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        #random position without going out of the boundaries of the map
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)
 
        #"Rect" class makes rectangles easier to work with
        new_room = Rect(x, y, w, h)
 
        #run through the other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break
 
        if not failed:
            #this means there are no intersections, so this room is valid
 
            #"paint" it to the map's tiles
            create_room(new_room)
 
            #center coordinates of new room, will be useful later
            (new_x, new_y) = new_room.center()
 
            if num_rooms == 0:
                #this is the first room, where the player starts at
                player.x = new_x
                player.y = new_y
            else:
                #all rooms after the first:
                #connect it to the previous room with a tunnel
 
                #center coordinates of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()
 
                #draw a coin (random number that is either 0 or 1)
                if libtcod.random_get_int(0, 0, 1) == 1:
                    #first move horizontally, then vertically
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)

            # add some contents to this room, such as monsters
            place_objects(new_room)
 
            #finally, append the new room to the list
            rooms.append(new_room)
            num_rooms += 1

def place_objects(room):
    # choose random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        # choose random spot for this monster
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

        # chances: 5% monster A, 25% monster B, 70% monster C, etc.
        # alternatively, can create more chances and create squads of monsters
        # only place object if tile is not blocked
        if not is_blocked(x, y):
            choice = libtcod.random_get_int(0, 0, 100)
            if choice < 5:
                # 5% create Terminatron
                fighter_component = Fighter(hp=100, defense=5, power=10, death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'T', 'Terminatron', libtcod.dark_red, blocks=True, fighter=fighter_component, ai=ai_component)
            elif choice < 5 + 25:
                # 25% create Mecharachnid
                fighter_component = Fighter(hp=15, defense=1, power=4, death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'm', 'Mecharachnid', libtcod.light_grey, blocks=True, fighter=fighter_component, ai=ai_component)
            else:
                # 70% create Cyborg
                fighter_component = Fighter(hp=10, defense=0, power=2, death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'c', 'Cyborg', libtcod.darker_gray, blocks=True, fighter=fighter_component, ai=ai_component)

            objects.append(monster)

    # choose random number of items
    num_items = libtcod.random_get_int(0, 0, MAX_ROOM_ITEMS)

    for i in range(num_items):
        # choose random spot for this item
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

        # only place it if the tile is NOT BLOCKED
        if not is_blocked(x, y):
            dice = libtcod.random_get_int(0, 0, 100)
            if dice < 70: # 70% chance for a health pack
                # create a health pack
                item_component = Item(use_function=cast_heal)
                item = Object(x, y, '!', 'Health Pack', libtcod.violet, item=item_component)
            elif dice < 70 + 10: # 10% chance for a lightning device
                # create a lightning device
                item_component = Item(use_function=cast_lightning)
                item = Object(x, y, '#', 'Lightning Device', libtcod.light_yellow, item=item_component)
            elif dice < 70 + 10 + 10: # 10% chance for an EMP device
                item_component = Item(use_function=cast_EMP_device)
                item = Object(x, y, '#', 'EMP Device', libtcod.light_yellow, item=item_component)
            else: # 10% chance for an impact grenade
                item_component = Item(use_function=cast_impact_grenade)
                item = Object(x, y, '#', 'Impact Grenade', libtcod.light_yellow, item=item_component)

            objects.append(item)
            item.send_to_back() # items appear below other objects

# render a bar (HP, experience, etc). first calculate the width of the bar
def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    bar_width = int(float(value) / maximum * total_width)
    
    # render the background first
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    # now render the bar on top
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    # finally, some centered text with the values
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER, name + ': ' + str(value) + '/' + str(maximum))

# get information of entities under mouse cursor
def get_names_under_mouse():
    global mouse
    
    # return a string with the names of all objects under the mouse
    (x, y) = (mouse.cx, mouse.cy)

    # create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in objects
        if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]

    names = ', '.join(names) # join the names separated by commas
    return names.capitalize()

def render_all():
    global fov_map, color_dark_wall, color_light_wall
    global color_dark_ground, color_light_ground
    global fov_recompute
 
    if fov_recompute:
        #recompute FOV if needed (the player moved or something)
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
 
        #go through all tiles, and set their background color according to the FOV
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = map[x][y].block_sight
                if not visible:
                    # only show non-visible if it has been explored
                    if map[x][y].explored:
                        #it's out of the player's FOV
                        if wall:
                            libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
                else:
                    #it's visible
                    if wall:
                        libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET )
                    else:
                        libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET )
                    # since it's visible, it's explored
                    map[x][y].explored = True
 
    #draw all objects in the list
    for object in objects:
        if object != player:
            object.draw()
    player.draw()
 
    #blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)

    # prepare to render the GUI panel
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)

    # print the game messages one line at a time
    y = 1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1

    # show the player's stats
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp, libtcod.light_red, libtcod.darker_red)

    # display names of objects under the mouse
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())

    # blit the contents of "panel" to the root console
    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)

# split the message if necessary, among multiple lines
def message(new_msg, color = libtcod.white):
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

    for line in new_msg_lines:
        # if the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]

        # add the new line as a tuple, with the text and the color
        game_msgs.append( (line, color) )

# determines play movement/attack
def player_move_or_attack(dx, dy):
    global fov_recompute

    # the coordinates the player is moving to/attacking
    x = player.x + dx
    y = player.y + dy

    # attempt to find attackable object there
    target = None
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break

    # attack if target found, otherwise move
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        fov_recompute = True
 
# handle player inputs
def handle_keys():
    global fov_recompute, key
 
    if key.vk == libtcod.KEY_ENTER and key.ralt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'  #exit game

    if game_state == 'playing':
        #movement keys
        if key.vk == libtcod.KEY_UP:
            player_move_or_attack(0, -1)
            fov_recompute = True
    
        elif key.vk == libtcod.KEY_DOWN:
            player_move_or_attack(0, 1)
            fov_recompute = True
    
        elif key.vk == libtcod.KEY_LEFT:
            player_move_or_attack(-1, 0)
            fov_recompute = True
    
        elif key.vk == libtcod.KEY_RIGHT:
            player_move_or_attack(1, 0)
            fov_recompute = True

        elif key.vk == libtcod.KEY_KP8:
            player_move_or_attack(0, -1)
            fov_recompute = True

        elif key.vk == libtcod.KEY_KP2:
            player_move_or_attack(0, 1)
            fov_recompute = True

        elif key.vk == libtcod.KEY_KP4:
            player_move_or_attack(-1, 0)
            fov_recompute = True

        elif key.vk == libtcod.KEY_KP6:
            player_move_or_attack(1, 0)
            fov_recompute = True

        elif key.vk == libtcod.KEY_KP1:
            player_move_or_attack(-1, 1)
            fov_recompute = True

        elif key.vk == libtcod.KEY_KP7:
            player_move_or_attack(-1, -1)
            fov_recompute = True

        elif key.vk == libtcod.KEY_KP9:
            player_move_or_attack(1, -1)
            fov_recompute = True

        elif key.vk == libtcod.KEY_KP3:
            player_move_or_attack(1, 1)
            fov_recompute = True

        elif key.vk == libtcod.KEY_BACKSPACE:
            # show the inventory; if an item is selected, drop it
            chosen_item = inventory_menu('Press the key next to an item to drop it, or any other to cancel.\n')
            if chosen_item is not None:
                chosen_item.drop()

        else:
            # test for other keys
            key_char = chr(key.c)

            if key_char == 'g':
                # pick up an item
                for object in objects: #look for an item in the player's tile
                    if object.x == player.x and object.y == player.y and object.item:
                        object.item.pick_up()
                        break

            if key_char == 'i':
                # show the inventory; if an item is selected, use it
                chosen_item = inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.use()

            return 'didnt-take-turn'

# return the position of a tile left-clicked in player's FOV (optionally in a range), or (None, None) if right-clicked
def target_tile(max_range=None):
    global key, mouse
    while True:
        # render the screen, this erases the inventory and shows the names of objects under the mouse
        libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        render_all()

        (x, y) = (mouse.cx, mouse.cy)

        # accept the target if the player clicked in FOV, and in case a range is specified, if it's in that range
        if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and (max_range is None or player.distance(x, y) <= max_range)):
            return (x, y)

        if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            return (None, None) # cancel if the player right-clicked or hit Escape

# returns a clicked monster inside FOV up to a range, or None if right-clicked
def target_monster(max_range=None):
    while True:
        (x, y) = target_tile(max_range)
        if x is None: #player cancelled
            return None

        # return the first clicked monster, otherwise continue looping
        for obj in objects:
            if obj.x == x and obj.y == y and obj.fighter and obj != player:
                return obj

# ends game is player dies!
def player_death(player):
    global game_state
    message('You died!', libtcod.red)
    game_state = 'dead'

    # for added effect, transform the player into a corpse!
    player.char = '%'
    player.color = libtcod.dark_red

# transform into a nasty corpse! it doesn't block, can't be attacked, and doesn't move
def monster_death(monster):
     message(monster.name.capitalize() + ' is dead!', libtcod.orange)
     monster.char = '%'
     monster.color = libtcod.dark_red
     monster.blocks = False
     monster.fighter = None
     monster.ai = None
     monster.name = 'remains of ' + monster.name
     monster.send_to_back()

# define a menu window. Has a string at the top (header), list of strings (options. can be names of items, for ex), and the window's width (width)
def menu(header, options, width):
    if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')

    # calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
    height = len(options) + header_height

    # create an off-screen console that represents the menu's window
    window = libtcod.console_new(width, height)

    # print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)

    # print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1

    # blit the contents of "window" to the root console
    x = SCREEN_WIDTH/2 - width/2
    y = SCREEN_HEIGHT/2 - height/2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

    # present the root console to the player and wait for a key-press
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(True)

    # convert the ASCII code to an index; if it corresponds to an option, return it
    index = key.c - ord('a')
    if index >= 0 and index < len(options): return index
    return None

# show a menu with each item of the inventory as an option
def inventory_menu(header):
    if len(inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = [item.name for item in inventory]

    index = menu(header, options, INVENTORY_WIDTH)

    # if an item was chosen, return it
    if index is None or len(inventory) == 0: return None
    return inventory[index].item

# finds closest enemy, up to a maximum range, and in the player's FOV
def closest_monster(max_range):
    closest_enemy = None
    closest_dist = max_range + 1 #start with (slightly more than) maximum range

    for object in objects:
        if object.fighter and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
            # calculate dist between this object and player
            dist = player.distance_to(object)
            if dist < closest_dist: #it's closer, so remember it
                closest_enemy = object
                closest_dist = dist
    return closest_enemy

# heal the player
def cast_heal():
    if player.fighter.hp == player.fighter.max_hp: # don't heal the player if at full hp already
        message('You are already at full health.', libtcod.red)
        return 'cancelled'

    message('Your wounds start to feel better!', libtcod.light_violet)
    player.fighter.heal(HEAL_AMOUNT)

# finds closest enemy (inside a maximum range) and damage it
def cast_lightning():
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None: #no enemy found within max range
        message('No enemy is close enough to strike.', libtcod.red)
        return 'cancelled'

    # zap it!
    message('A lightning bolt strikes the ' + monster.name + ' with a loud thunder! The damage is ' + str(LIGHTNING_DAMAGE) + ' hit points.', libtcod.light_blue)
    monster.fighter.take_damage(LIGHTNING_DAMAGE)

# find closest enemy in-range and confuse it
def cast_EMP_device():
    # confuse all monsters within a radius
    monsters = []
    for obj in objects:
        if obj.distance(player.x, player.y) <= CONFUSE_RANGE and obj.fighter and obj != player:
            monsters.append(obj)

    if not monsters:
        message('No enemies close enough to use EMP device on.', libtcod.red)
        return 'cancelled'

    for monster in monsters:
        # replace the monster's AI with a "confused" one; after some turns it will restore the old AI
        old_ai = monster.ai
        monster.ai = ConfusedMonster(old_ai)
        monster.ai.owner = monster #tell the new component who owns it
        message('The ' + monster.name + ' starts to go haywire, stumbling around!', libtcod.light_green)

# ask the player for a target tile to throw an impact grenade at
def cast_impact_grenade():
    message('Left-click a target tile to throw the impact grenade, or right-click to cancel.', libtcod.light_cyan)
    (x, y) = target_tile()
    if x is None: return 'cancelled'
    message('The impact grenade explodes, burning everything within ' + str(IMPACT_GRENADE_RADIUS) + ' tiles!', libtcod.orange)

    for obj in objects: # damage every fighter in range, including the player
        if obj.distance(x, y) <= IMPACT_GRENADE_RADIUS and obj.fighter:
            message('The ' + obj.name + ' gets burned for ' + str(IMPACT_GRENADE_DAMAGE) + ' hit points.', libtcod.orange)
            obj.fighter.take_damage(IMPACT_GRENADE_DAMAGE)

#############################################
# Initialization & Main Loop                #
#############################################

# INITIALIZE FOV MAP
def initialize_fov():
    global fov_recompute, fov_map
    fov_recompute = True

    #create the FOV map, according to the generated map
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)

# START A NEW GAME
def new_game():
    global player, inventory, game_msgs, game_state

    #create object representing the player
    fighter_component = Fighter(hp=30, defense=0, power=5, death_function=player_death)
    player = Object(0, 0, '@', 'Player', libtcod.white, blocks=True, fighter=fighter_component)
    
    #generate map (at this point it's not drawn to the screen)
    make_map()

    # initialize fov map
    initialize_fov()

    # create the list of game messages and their colors, starts empty
    game_msgs = []

    # player inventory
    inventory = []

    # print a welcome message!
    message('Welcome to MurDur Corps. Make it out alive. Good luck.', libtcod.red)

# run the main game functions
def play_game():
    global key, mouse

    player_action = None

    # set mouse/keyboard controls
    mouse = libtcod.Mouse()
    key = libtcod.Key()
    while not libtcod.console_is_window_closed():
        # check for key/mouse input event
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
    
        #render the screen
        render_all()
    
        libtcod.console_flush()
    
        #erase all objects at their old locations, before they move
        for object in objects:
            object.clear()
    
        #handle keys and exit game if needed
        player_action = handle_keys()
        if player_action == 'exit':
            break

        # let monsters take their turn
        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for object in objects:
                if object.ai:
                    object.ai.take_turn()

#############
# MAIN LOOP #
#############

libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)
libtcod.sys_set_fps(LIMIT_FPS)
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

# start new_game
new_game()

# begin playing game
play_game()