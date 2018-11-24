import libtcodpy as libtcod
import math
import textwrap
import shelve
import random
from time import sleep
 
#actual size of the window
SCREEN_WIDTH = 113
SCREEN_HEIGHT = 64
 
#size of the map
MAP_WIDTH = 83
MAP_HEIGHT = 54

#size of the hud
HUD_WIDTH = 30

# sizes and coordinates relevant for the GUI
BAR_WIDTH = 28
LOG_HEIGHT = 10
LOG_Y = MAP_HEIGHT
MSG_X = 2
MSG_WIDTH = MAP_WIDTH - 2
MSG_HEIGHT = LOG_HEIGHT - 1
INVENTORY_WIDTH = 50
LEVEL_SCREEN_WIDTH = 40
CHARACTER_SCREEN_WIDTH = 30

# Z-Axis values
BLOODDROP_Z_VAL = 0
CORPSE_Z_VAL = 1
TRAP_Z_VAL = 2
STAIRS_Z_VAL = 3
ITEM_Z_VAL = 4
MONSTER_Z_VAL = 5
PLAYER_Z_VAL = 6
RETICULE_Z_VAL = 99
 
# parameters for dungeon generator (num of monsters, items, etc.)
ROOM_MAX_SIZE = 14
ROOM_MIN_SIZE = 6
MAX_ROOMS = 99 # this was 30

# Experience and level-ups
## TODO: Return back to normal (200)
LEVEL_UP_BASE = 20000
LEVEL_UP_FACTOR = 150
LEVEL_UP_XP = LEVEL_UP_BASE + LEVEL_UP_FACTOR

# Run values
RUN_DURATION = 50

# spell values
HEAL_AMOUNT = 35
LIGHTNING_DAMAGE = 20
LIGHTNING_RANGE = 5
CONFUSE_NUM_TURNS = 10
CONFUSE_RANGE = 8
IMPACT_GRENADE_RADIUS = 5
IMPACT_GRENADE_DAMAGE = '4d6+10'

############################
## Canister Color Globals ##
############################
HEAL_CANISTER_COLOR = ''
STRENGTH_CANISTER_COLOR = ''

##############################
## Canister Is_Id'd Globals ##
##############################
IS_HEAL_CANISTER_IDENTIFIED = False
IS_STRENGTH_CANISTER_IDENTIFIED = False

#########################
## Fixed Weapon Values ##
#########################
PROJECTILE_SLEEP_TIME = 0.01

# Fists/Unarmed
UNARMED_DAMAGE = '1d3'

# Pistol
PISTOL_RANGED_DAMAGE = '2d4'
PISTOL_MELEE_DAMAGE = '1d3'
PISTOL_RANGE = 5 #TODO: CHANGE THIS TO 12-15. FOV RANGE IS 10
PISTOL_ACCURACY_BONUS = 1

# Dagger
DAGGER_DAMAGE = '2d4'
DAGGER_ACCURACY_BONUS = 3

#########################

##########################
## Fixed Monster Values ##
#TODO: Finish porting over these fixed values
# TERMINATRON
TERMINATRON_MELEE_DAMAGE = '2d6'

# MECHARACHNID
MECHARACHNID_MELEE_DAMAGE = '2d6'

# CYBORG
CYBORG_RANGED_DAMAGE = '2d4'

FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = True  #light walls or not
TORCH_RADIUS = 10
 
LIMIT_FPS = 60  #60 frames-per-second maximum
 
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
    # TODO: Remove max_capacity from game? Currently no purpose.
    def __init__(self, x, y, char, name, color, capacity=None, max_capacity=None, blocks=False, always_visible=False, fighter=None, ai=None, item=None, equipment=None, canister=None, trap=None, z=0):
        self.x = x
        self.y = y
        self.z = z
        self.char = char
        self.color = color
        self.capacity = capacity
        self.max_capacity = max_capacity
        self.name = name
        self.blocks = blocks
        self.always_visible = always_visible
        self.fighter = fighter
        if self.fighter: #let the fighter component know who owns it
            self.fighter.owner = self

        self.ai = ai
        if self.ai: #let the AI component know who owns it
            self.ai.owner = self

        self.item = item
        if self.item: # let the Item component know who owns it
            self.item.owner = self

        self.trap = trap
        if self.trap: # let the Trap component know who owns it
            self.trap.owner = self

        self.canister = canister
        if self.canister: # let the Canister component know who owns it
            self.canister.owner = self
            self.name = self.canister.get_name()

            # there must be an Item component for the Canister component to work properly
            self.item = Item()
            self.item.owner = self

        self.equipment = equipment
        if self.equipment: #let the Equipment component know who owns it
            self.equipment.owner = self
            self.name = self.equipment.get_name()

            # there must be an Item component for the Equipment component to work properly
            self.item = Item()
            self.item.owner = self
 
    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if not is_blocked(self.x + dx, self.y + dy):
            self.clear()
            if self.fighter is not None:
                self.fighter.has_moved_this_turn = True
                if (float(self.fighter.hp) / self.fighter.base_max_hp) <= 0.2:
                    blooddrop = Object(self.x, self.y, '.', 'Droplet of blood', libtcod.red, always_visible=False, z=BLOODDROP_Z_VAL)
                    objects.append(blooddrop)

            self.x += dx
            self.y += dy

    def move_reticule(self, dx, dy):
        #move the reticule by the given amount, don't check for blocking structures
        if ((self.x + dx < MAP_WIDTH and self.y + dy < MAP_HEIGHT) and (self.x + dx >= 0 and self.y + dy >= 0)):
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

    # CURRENTLY UNUSED
    # make this object be drawn first, so all others appear above it if they're in the same tile
    def send_to_back(self):
        global objects
        objects.remove(self)
        objects.insert(0, self)

    # CURRENTLY UNUSED
    # make this object be drawn last, so all others appear below it if they're in the same tile
    def send_to_front(self):
        global objects
        objects.remove(self)
        objects.insert(len(objects), self)
 
    def draw(self):
        #only show if it's visible to the player OR if it's explored and always_visible = True OR if the object is the aiming reticule
        if (libtcod.map_is_in_fov(fov_map, self.x, self.y) or (self.always_visible and map[self.x][self.y].explored) or (self.name == 'Reticule')):
            #set the color and then draw the character that represents this object at its position
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
 
    def clear(self):
        #erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

    # aStar movement AI: allows monsters to walk around unwalkable objects, take into account monsters, move diagonally, etc.
    def move_astar(self, target):
        # create a FOV map that has the dimensions of the map
        fov = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)

        # scan the current map each turn and set all the walls as unwalkable
        for y1 in range(MAP_HEIGHT):
            for x1 in range(MAP_WIDTH):
                libtcod.map_set_properties(fov, x1, y1, not map[x1][y1].block_sight, not map[x1][y1].blocked)

        # Scan all the objects to see if there are objects that must be navigated around
        # Check also that the object isn't self or the target (so that the start and the end points are free)
        # The AI class handles the situation if self is next to the target so it will not use this A* function anyway
        for obj in objects:
            if obj.blocks and obj != self and obj != target:
                # set the tile as a wall so it must be navigated around
                libtcod.map_set_properties(fov, obj.x, obj.y, True, False)
        
        # Allocate a A* path
        # The 1.41 is the normal diagonal cost of moving, it can be set as 0.0 if diagonal moves are prohibited
        my_path = libtcod.path_new_using_map(fov, 1.41)

        # Compute the path between self's coordinates and the target's coordinates
        libtcod.path_compute(my_path, self.x, self.y, target.x, target.y)

        # Check if the path exists, and in this case, also the path is shorter than 25 tiles
        # The path size matters if you want the monster to use alternative longer paths (for example, through other rooms) if for example the player is in a corridor
        # It makes sense to keep path size relatively low to keep the monsters from running around the map if there's an alternative path really far away
        if not libtcod.path_is_empty(my_path) and libtcod.path_size(my_path) < 25:
            # Find the next coordinates in the computed full path
            x, y = libtcod.path_walk(my_path, True)
            if x or y:
                # Set self's coordinates to the next path tile
                # self.x = x
                # self.y = y
                self.move(x - self.x, y - self.y)

        else:
            # keep the old move function as a backup so that if there are no paths (for example, another monster blocks a corridor)
            # it will still try to move towards the player (closer to the corridor opening)
            # TODO: Does this ever get called? It seems that monsters attempt to always find a way around if a corridor is blocked, instead of moving closer
            self.move_towards(target.x, target.y)

        # delete the path to free memory
        libtcod.path_delete(my_path)

# combat-related properties and methods (monster, player, NPC)
class Fighter:
    def __init__(self, hp=0, strength=0, accuracy=0, finesse=0, evasion=0, armor=0, melee_damage=None, ranged_damage=None, xp=0, 
        ten_mm_rounds=0, max_ten_mm_rounds=100, death_function=None, run_status=None, run_duration=0, has_moved_this_turn=False):
        self.base_max_hp = hp
        self.hp = hp
        self.base_strength = strength
        self.base_accuracy = accuracy
        self.base_finesse = finesse
        self.base_evasion = evasion
        self.base_armor = armor
        self.base_melee_damage = melee_damage
        self.base_ranged_damage = ranged_damage
        self.run_duration = run_duration
        self.xp = xp
        self.ten_mm_rounds = ten_mm_rounds
        self.max_ten_mm_rounds = max_ten_mm_rounds
        self.death_function = death_function
        self.run_status = run_status
        self.has_moved_this_turn = has_moved_this_turn

    # return actual power, by summing up the bonuses from all equipped items
    @property
    def melee_damage(self):
        if self.owner == player: # if Fighter is player
            weapon = get_equipped_in_slot('weapon')
            if weapon is not None: # and if holding a weapon
                if (self.strength != 0):
                    return str(weapon.melee_damage) + '+' + str(self.strength)
                else:
                    return str(weapon.melee_damage)
            else: # or if melee_damage is none (not holding weapon)
                if (self.strength != 0):
                    return UNARMED_DAMAGE + '+' + str(self.strength)
                else:
                    return UNARMED_DAMAGE
        else: # if Fighter is NOT player
            return str(self.base_melee_damage) + '+' + str(self.strength)

    @property
    def ranged_damage(self):
        if self.owner == player: # if Fighter is player
            weapon = get_equipped_in_slot('weapon')
            if weapon is not None and weapon.ranged_damage is not None: # and if holding a weapon
                if (self.finesse != 0):
                    return str(weapon.ranged_damage) + '+' + str(self.finesse)
                else:
                    return str(weapon.ranged_damage)
            else: # or if ranged_damage is none (not holding weapon)
                return None
        else: # if Fighter is NOT player
            return str(self.base_ranged_damage) + '+' + str(self.finesse)

    @property
    def strength(self):
        bonus = sum(equipment.strength_bonus for equipment in get_all_equipped(self.owner))
        return self.base_strength + bonus

    @property
    def accuracy(self):
        bonus = sum(equipment.accuracy_bonus for equipment in get_all_equipped(self.owner))
        if self.owner is player and player.fighter.run_status == 'running':
            bonus -= 1
        return self.base_accuracy + bonus

    @property
    def finesse(self):
        bonus = sum(equipment.finesse_bonus for equipment in get_all_equipped(self.owner))
        return self.base_finesse + bonus

    @property
    def evasion(self):
        bonus = sum(equipment.evasion_bonus for equipment in get_all_equipped(self.owner))
        if self.owner is player and player.fighter.run_status == 'running':
            bonus += 1
        if self.owner is player and player.fighter.has_moved_this_turn:
            bonus += 1
        return self.base_evasion + bonus

    @property
    def armor(self):
        bonus = sum(equipment.armor_bonus for equipment in get_all_equipped(self.owner))
        return self.base_armor + bonus

    @property
    def max_hp(self):
        bonus = sum(equipment.max_hp_bonus for equipment in get_all_equipped(self.owner))
        return self.base_max_hp + bonus

    # a simple formula for attack damage
    def attack(self, target):
        self.has_moved_this_turn = False
        if roll_to_hit(accuracy_bonus=self.accuracy, evasion_penalty=target.fighter.evasion):
            totalDamage = roll_dice(self.melee_damage)
            totalDamage -= target.fighter.armor

            if totalDamage > 0:
                # make the target take some damage
                message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(totalDamage) + ' hit points.')
                target.fighter.take_damage(totalDamage)
            else:
                message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')
        else:
            message(self.owner.name.capitalize() + ' misses the attack on ' + target.name + '!')

    # apply damage if possible
    def take_damage(self, damage):
        if damage > 0:
            self.hp -= damage

            # check for death. if there's a death function, call it
            if self.hp <= 0:
                function = self.death_function
                if function is not None:
                    function(self.owner)

                if self.owner != player: #yield experience to the player
                    player.fighter.xp += self.xp

    # heal by the given amount, without going over maximum
    def heal(self, amount):
        if player.fighter.run_status == 'running' or player.fighter.run_status == 'tired':
            player.fighter.run_status = 'rested'
            player.fighter.run_duration = RUN_DURATION
        self.hp += amount
        if self.hp > self.base_max_hp:
            self.hp = self.base_max_hp

# AI for melee monsters (chase, no ranged)
class MeleeAI:
    def take_turn(self):
        move_chance = 100
        if player.fighter.run_status == 'running':
            move_chance -= 20
        # roll to see if monster moves
        monster = self.owner
        if libtcod.random_get_int(0, 1, 100) < move_chance:
            # a basic monster takes its turn. If monster sees player, chase
            if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):

                # move towards player if far away
                if monster.distance_to(player) >= 2:
                    monster.clear()
                    monster.move_astar(player)
                
                # close enough, attack! (if the player is still alive)
                elif player.fighter.hp > 0:
                    monster.fighter.attack(player)
            else: # if monster doesn't see player, move randomly
                monster.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))

# AI for Cyborgs (ranged)
class CyborgAI:
    def take_turn(self):
        if player.fighter.hp > 0:
            render_all()
            monster = self.owner
            if libtcod.map_is_in_fov(fov_map, monster.x, monster.y): # if Cyborg sees Player, chance to fire/move
                if is_line_blocked_by_wall(monster.x, monster.y, player.x, player.y) is False:
                    atk_chance = libtcod.random_get_int(0, 1, 100)

                    if atk_chance < 75: #chance to fire weapon, 75%
                        totalDamage = roll_dice(monster.fighter.ranged_damage)
                        # slope between player and reticule
                        dx = player.x
                        dy = player.y

                        m_x = dx - monster.x
                        m_y = dy - monster.y
                        # starting x and y
                        start_x = monster.x
                        start_y = monster.y

                        # Find furthest blocking tile
                        hasHit = False
                        
                        while (hasHit is False):
                            libtcod.line_init(start_x, start_y, dx, dy)
                            prev_x, prev_y = start_x, start_y
                            x, y = libtcod.line_step()
                            while (x is not None):
                                (min, max) = get_min_max_dmg(monster.fighter.ranged_damage)
                                if (totalDamage == max):
                                    libtcod.console_set_default_foreground(con, libtcod.sky)
                                elif (totalDamage == min):
                                    libtcod.console_set_default_foreground(con, libtcod.red)
                                else:
                                    libtcod.console_set_default_foreground(con, libtcod.white)
                                #if libtcod.map_is_in_fov(fov_map, x, y):
                                normal_vec = point_to_point_vector(prev_x, prev_y, x, y)
                                if normal_vec == (1, 0) or normal_vec == (-1, 0): # bullet traveling right or left
                                    libtcod.console_put_char(con, x, y, '-', libtcod.BKGND_NONE)
                                elif normal_vec == (0, 1) or normal_vec == (0, -1): # bullet traveling up or down
                                    libtcod.console_put_char(con, x, y, '|', libtcod.BKGND_NONE)
                                elif normal_vec == (1, 1) or normal_vec == (-1, -1): # bullet traveling upright or downleft
                                    libtcod.console_put_char(con, x, y, '\\', libtcod.BKGND_NONE)
                                elif normal_vec == (-1, 1) or normal_vec == (1, -1): # bullet traveling upleft or downright
                                    libtcod.console_put_char(con, x, y, '/', libtcod.BKGND_NONE)
                                else: # TODO: DEBUG: this shouldn't be reached but if so, debug
                                    libtcod.console_put_char(con, x, y, '*', libtcod.BKGND_NONE)
                                libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
                                libtcod.console_flush()
                                sleep(PROJECTILE_SLEEP_TIME)
                                obj = get_object_by_tile(x, y)
                                if is_blocked(x, y) and obj is not None and obj.fighter and roll_to_hit(accuracy_bonus=monster.fighter.accuracy, evasion_penalty=obj.fighter.evasion) is True: # if bullet hits a blocked tile at x, y
                                    #if libtcod.map_is_in_fov(fov_map, x, y):
                                    libtcod.console_put_char(con, x, y, 'x', libtcod.BKGND_NONE)
                                    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
                                    libtcod.console_flush()
                                    sleep(PROJECTILE_SLEEP_TIME)
                                    hit_obj = get_fighter_by_tile(x, y)
                                    hasHit = True
                                    if hit_obj and hit_obj.fighter:
                                        monsterFound = True
                                        message(hit_obj.name + ' is shot for ' + str(totalDamage) + ' hit points.', libtcod.orange)
                                        hit_obj.fighter.take_damage(totalDamage)
                                        break
                                    if monsterFound is False:
                                        message('The ' + monster.name + '\'s shot misses!', libtcod.red)
                                    break
                                elif is_blocked(x, y) and obj is None:
                                    #if libtcod.map_is_in_fov(fov_map, x, y):
                                    libtcod.console_put_char(con, x, y, 'x', libtcod.BKGND_NONE)
                                    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
                                    libtcod.console_flush()
                                    sleep(PROJECTILE_SLEEP_TIME)
                                    hasHit = True
                                    message('The ' + monster.name + '\'s shot misses!', libtcod.red)
                                    break
                                else:
                                    libtcod.console_put_char(con, x, y, ' ', libtcod.BKGND_NONE)
                                    # redraws objs if a bullet is shot over them
                                    if obj is not None:
                                        obj.draw()
                                    prev_x, prev_y = x, y
                                    x, y = libtcod.line_step()
                            if (x is not None): # delete bullet char from spot hit
                                libtcod.console_put_char(con, x, y, ' ', libtcod.BKGND_NONE)
                                libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
                            # bullet reached reticule, extend reticule
                            start_x = dx
                            start_y = dy
                            dx = dx + m_x
                            dy = dy + m_y

                    else: # chance to move, 25%
                        monster.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
                else: # if Cyborg sees player but can't shoot player, move
                    monster.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
            else: # if Cyborg doesn't see player, move
                monster.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))

# AI for a temporarily confused monster (reverts to previous AI after a while).
class ConfusedMonster:
    def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns

    def take_turn(self):
        if self.num_turns > 0: # monster still confused...
            # move in a random direction, and decrease the number of turns confused
            self.owner.clear()
            self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
            self.num_turns -= 1
        else: # restore the previous AI (this one will be deleted because it's not referenced anymore)
            self.owner.ai = self.old_ai
            message('The ' + self.owner.name + ' is no longer confused!', libtcod.red)

# an item that can be picked up and used
class Item:
    def __init__(self, use_function=None, shootable=False, is_being_used=False):
        self.use_function = use_function
        self.is_being_used = is_being_used
        self.shootable = shootable

    def pick_up(self):
        print('In pick_up()...')
        # add to the player's inventory and remove from map
        if self.owner.capacity is not None: # if ammo, add to player's ammo TODO: Generalize this function
            if "10mm" in self.owner.name: # if the item we're picking up is 10mm ammo
                amount_to_pickup = player.fighter.max_ten_mm_rounds - player.fighter.ten_mm_rounds
                if amount_to_pickup > 0: # if we can pick up some ammo
                    if self.owner.capacity > amount_to_pickup: # we can pick up some ammo, but not all
                        player.fighter.ten_mm_rounds += amount_to_pickup
                        self.owner.capacity -= amount_to_pickup
                    else: # we can pick up all ammo and delete obj
                        player.fighter.ten_mm_rounds += self.owner.capacity
                        objects.remove(self.owner)
                    message('Picked up some 10mm ammo!', libtcod.green)
                else: # we're full on ammo
                    message('You cannot pick up any more 10mm ammo.', libtcod.yellow)
        elif len(inventory) >= 26: # limited to 26 as there are 26 letters in the alphabet, A - Z
            message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.yellow)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '!', libtcod.green)

            # special case: automatically equip, if the corresponding equipment slot is unused
            equipment = self.owner.equipment
            if equipment and get_equipped_in_slot(equipment.slot) is None:
                equipment.equip()

    def drop(self):
        # special case: if the object has the Equipment component, dequip it before dropping
        if self.owner.equipment:
            self.owner.equipment.dequip()

        # add to the map and remove from the player's inventory. also, place it at the player's coordinates
        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message('You dropped a ' + self.owner.name + '.', libtcod.yellow)

    def use(self):
        # special case: if the object has the Equipment component, the "use" action is to equip/dequip
        if self.owner.equipment:
            self.owner.equipment.toggle_equip()
            return

        # special case: if the object has the Canister component, the "use" action is to quaff
        if self.owner.canister:
            self.owner.canister.quaff()
            return

        # just call the "use_function" if it is defined
        if self.use_function is None:
            message('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                if self.shootable is False:
                    inventory.remove(self.owner) # destroy after use, unless it was cancelled for some reason

    def scan(self):
        if self.owner.equipment:
            self.owner.equipment.scan()
            return
        
        if self.owner.canister:
            self.owner.canister.scan()
            return

# a canister that can be drank (or thrown) for various effects
class Canister:
    def __init__(self, color, canister_function=None, is_identified=False):
        self.color = color
        self.canister_function = canister_function
        self.is_identified = is_identified

    def get_name(self):
        if self.is_identified is False:
            return self.color + ' Canister'
        elif self.is_identified is True:
            return get_canister_name_from_function(self.canister_function)

    def quaff(self):
        self.canister_function()
        inventory.remove(self.owner)
        return

    def scan(self):
        self.is_identified = True
        self.owner.name = self.get_name()
        for c in objects:
            if c.canister and c.canister.color == self.color:
                c.canister.is_identified = True
                c.name = c.canister.get_name()
        for c in inventory:
            if c.canister and c.canister.color == self.color:
                c.canister.is_identified = True
                c.name = c.canister.get_name()
        return

# an object that can be equipped, yielding bonuses. Automatically adds the Item component
class Equipment:
    def __init__(self, slot, is_ranged=False, shoot_function=None, range=0, max_ammo=0, ammo=0, melee_damage=None, ranged_damage=None, 
        max_hp_bonus=0, strength_bonus=0, accuracy_bonus=0, finesse_bonus=0, evasion_bonus=0, armor_bonus=0, quality=None, is_identified=False):
        self.slot = slot
        self.melee_damage = melee_damage
        self.ranged_damage = ranged_damage
        self.max_hp_bonus = max_hp_bonus
        self.strength_bonus = strength_bonus
        self.accuracy_bonus = accuracy_bonus
        self.finesse_bonus = finesse_bonus
        self.evasion_bonus = evasion_bonus
        self.armor_bonus = armor_bonus
        self.is_equipped = False
        self.is_ranged = is_ranged
        self.max_ammo = ammo
        self.ammo = ammo
        self.max_range = range
        self.shoot_function = shoot_function
        self.quality = quality
        self.is_identified = is_identified

    def get_name(self):
        if self.is_identified is False:
            return self.owner.name
        elif self.is_identified is True:
            return self.quality + ' ' + self.owner.name

    def toggle_equip(self): # toggle equip status
        if self.is_equipped:
            self.dequip()
        else:
            self.equip()

    def equip(self):
        # if the slot is already being used, dequip whatever is there first
        old_equipment = get_equipped_in_slot(self.slot)
        if old_equipment is not None:
            old_equipment.dequip()

        # equip object and show a message about it
        self.is_equipped = True
        message('Equipped ' + self.owner.name + '.', libtcod.light_green)

    def dequip(self):
        # dequip object and show a message about it
        if not self.is_equipped: return
        self.is_equipped = False
        message('Unequipped ' + self.owner.name + '.', libtcod.light_yellow)

    def use(self):
        # just call the "use_function" if it is defined
        if self.use_function is None:
            message('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                return

    def scan(self):
        self.is_identified = True
        self.owner.name = self.get_name()
        print('In equipment scan! ' + self.owner.name + ' Id\'d?: ' + str(self.is_identified))
        return

# a trap that triggers when walked over
class Trap:
    def __init__(self, is_triggered=False, trigger_function=None):
        self.is_triggered = is_triggered
        self.trigger_function = trigger_function

    def trigger(self):
        if self.trigger_function is None:
            message('You hear a click, but nothing happens.')
        else:
            self.trigger_function(self.owner.x, self.owner.y)

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

# tests if a line has at least one segment blocked, excluding objects
def is_line_blocked_by_wall(x1, y1, x2, y2):
    libtcod.line_init(x1, y1, x2, y2)
    x, y = libtcod.line_step()
    while (x is not None):
        if (is_blocked(x, y) and (x != x2 and y != y2) and get_object_by_tile(x, y) is None):
            return True
        x, y = libtcod.line_step()
    return False

# finds a tile around (x, y) that is not blocked, and returns it
def get_unblocked_tile_around(x, y):
    foundUnblocked = False
    while foundUnblocked is False:
        (dx, dy) = (libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
        if is_blocked(dx + x, dy + y) is False:
            return (dx + x, dy + y)

# returns an object by tile
# NOTE: Excludes corpses!
def get_object_by_tile(x, y):
    for obj in objects:
        if (obj.x, obj.y) == (x, y) and 'remains' not in obj.name:
            return obj
    return None
 
# returns a fighter by tile
def get_fighter_by_tile(x, y):
    for obj in objects:
        if (obj.x, obj.y) == (x, y) and obj.fighter:
            return obj
    return None

# returns a trap by tile
def get_trap_by_tile(x, y):
    for obj in objects:
        if obj.trap and (obj.x, obj.y) == (x, y):
            return obj
    return None

# take two points, return the vector between them
def point_to_point_vector(start_x, start_y, end_x, end_y):
    return (end_x - start_x, end_y - start_y)

# get the distance between two points
def get_dist_between_points(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - x1)

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
    global map, objects, stairs

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

    # create stairs at the center of the last room
    stairs = Object(new_x, new_y, '>', 'stairs', libtcod.white, always_visible=True, z=STAIRS_Z_VAL)
    objects.append(stairs)
    # stairs.send_to_back() #so it's drawn below the monsters

    #########################################################################################
    # DEBUG: Print chance of each monster spawning #
    print('------- Dungeon_Level: ' + str(dungeon_level) + ' -------')
    #mon_sum = 0
    #for key, value in monster_chances.iteritems():
        #print('Adding chance val of ' + str(value) + ' to spawn: ' + key)
        #mon_sum += value
    #print('Total val: ' + str(mon_sum))
    
    #for key, value in monster_chances.iteritems():
        #print('Chance of ' + key + ' to spawn: ' + str((float(value) / mon_sum) * 100))

    # DEBUG: Print chance of each item spawning
    #item_sum = 0
    #for key, value in item_chances.iteritems():
        #print('Adding chance val of ' + str(value) + ' to spawn: ' + key)
        #item_sum += value
    #print('Total val: ' + str(item_sum))

    #for key, value in item_chances.iteritems():
        #print('Chance of ' + key + ' to spawn: ' + str((float(value) / item_sum) * 100))
    ##########################################################################################

# choose one option from list of chances, returning its index
def random_choice_index(chances):
    # the dice will land on some number between 1 and the sum of chances
    dice = libtcod.random_get_int(0, 1, sum(chances))

    # go through all chances, keeping the sum so far
    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w

        # see if the dice landed in the part that corresponds to this choice
        if dice <= running_sum:
            return choice
        choice += 1

# choose one option from dictionary of chances, returning its key
def random_choice(chances_dict):
    chances = chances_dict.values()
    strings = chances_dict.keys()

    return strings[random_choice_index(chances)]

# throw a single die of SIDES sides
def d(sides):
    return libtcod.random_get_int(0, 1, sides)

# throw n dice of SIDES sides
# NOTE: d_str = 'nds+b' ex: 2d4+1, p is the sign
# n = number of dice
# s = number of sides
# b = bonus
# p = sign
def roll_dice(d_str):
    print('D_str: ' + d_str)
    d_arr = d_str.split('d')
    n = int(d_arr[0])
    s = d_arr[1]
    b = None
    p = ''
    if '+' in s:
        b = s.split('+')
        s = b[0]
        b = int(b[1])
        p = '+'
    elif '-' in s:
        b = s.split('-')
        s = b[0]
        b = int(b[1])
        p = '-'
    vals = []
    for i in range (n):
        vals.append(d(int(s)))

    if b is None:
        return sum(vals)
    elif p is '+':
        return sum(vals) + b
    elif p is '-':
        return sum(vals) - b

# helper function to return (min, max) damage of a dice roll
def get_min_max_dmg(d_str):
    d_arr = d_str.split('d')
    n = int(d_arr[0])
    s = d_arr[1]
    b = None
    p = ''
    if '+' in s:
        b = s.split('+')
        s = b[0]
        b = int(b[1])
        p = '+'
    elif '-' in s:
        b = s.split('-')
        s = b[0]
        b = int(b[1])
        p = '-'

    min = 0
    max = 0
    # calculate the minimum
    for i in range(n):
        min += 1
    
    # calculate the maximum
    for i in range(n):
        max += int(s)

    if b is None:
        return (min, max)
    elif p is '+':
        return (min+b, max+b)
    elif p is '-':
        return (min-b, max-b)

# roll to hit. Base chance is 50%. Adds player's accuracy bonus
def roll_to_hit(accuracy_bonus=0, evasion_penalty=0):
    totalChance = 0
    totalChance += roll_dice('3d6')
    totalChance += evasion_penalty
    accuracy = 10 # standard chance to hit is 10 (about 50%)
    accuracy += accuracy_bonus
    if accuracy >= totalChance:
        return True
    else:
        return False

# returns a value that depends on level. the table specifies what value occurs after each level, default is 0
def from_dungeon_level(table):
    for (value, level) in reversed(table):
        if dungeon_level >= level:
            return value
    return 0

# returns a libtcod color value based on a string param
# TODO: Add all other colors
def get_libtcod_color_from_string(color):
    if color == 'Blue':
        return libtcod.blue
    elif color == 'Red':
        return libtcod.red
    return libtcod.grey

# returns a canister name string from the canister use function
def get_canister_name_from_function(function):
    if function == cast_heal:
        return 'Heal Canister'
    elif function == cast_increase_strength:
        return 'Strength Canister'
    else:
        return 'ADD CANISTER NAME'

##################################
## Equipment Creation Functions ##
##################################

# Create and return a pistol component
def create_pistol_equipment():
    chance = libtcod.random_get_int(0, 0, 100) # roll for quality
    ranged_dmg = PISTOL_RANGED_DAMAGE
    quality = ''
    if chance < 10:
        quality = 'Flawless'
        ranged_dmg += '+2'
    elif chance < 25 and chance >= 10:
        quality = 'Superior'
        ranged_dmg += '+1'
    elif chance < 55 and chance >= 25:
        quality = 'Standard'
    elif chance < 75 and chance >= 55:
        quality = 'Inferior'
        ranged_dmg += '-1'
    elif chance <= 100 and chance >= 75:
        quality = 'Makeshift'
        ranged_dmg += '-2'

    return Equipment(slot='weapon', ammo=7, is_ranged=True, shoot_function=cast_shoot_pistol, range=PISTOL_RANGE, melee_damage=PISTOL_MELEE_DAMAGE, ranged_damage=ranged_dmg, accuracy_bonus=PISTOL_ACCURACY_BONUS, quality=quality)

# Create and return a dagger component
def create_dagger_equipment():
    chance = libtcod.random_get_int(0, 0, 100) # roll for quality
    melee_dmg = DAGGER_DAMAGE
    quality = ''
    if chance < 10:
        quality = 'Flawless'
        melee_dmg += '+2'
    elif chance < 25 and chance >= 10:
        quality = 'Superior'
        melee_dmg += '+1'
    elif chance < 55 and chance >= 25:
        quality = 'Standard'
    elif chance < 75 and chance >= 55:
        quality = 'Inferior'
        melee_dmg += '-1'
    elif chance <= 100 and chance >= 75:
        quality = 'Makeshift'
        melee_dmg += '-2'
    return Equipment(slot='weapon', is_ranged=False, melee_damage=melee_dmg, accuracy_bonus=DAGGER_ACCURACY_BONUS, quality=quality)

#############################
## Item Creation Functions ##
#############################
def create_health_pack_item_component():
    return Item(use_function=cast_heal)

def create_scanner_item_component():
    return Item(use_function=cast_scan_item, shootable=True)

def create_lightning_device_item_component():
    return Item(use_function=cast_lightning)

def create_emp_device_item_component():
    return Item(use_function=cast_EMP_device)

def create_impact_grenade_item_component():
    return Item(use_function=cast_aim_impact_grenade, shootable=True)

#################################
## Canister Creation Functions ##
#################################
# Create and return a health canister component
def create_health_canister_component():
    print('HEAL_CANISTER_COLOR: ' + HEAL_CANISTER_COLOR)
    return Canister(color=HEAL_CANISTER_COLOR, canister_function=cast_heal, is_identified=IS_HEAL_CANISTER_IDENTIFIED)

def create_strength_canister_component():
    print('STRENGTH_CANISTER_COLOR: ' + STRENGTH_CANISTER_COLOR)
    return Canister(color=STRENGTH_CANISTER_COLOR, canister_function=cast_increase_strength, is_identified=IS_STRENGTH_CANISTER_IDENTIFIED)

#############################
## Trap Creation Functions ##
#############################
# Create and return an explosive trap component
def create_explosive_trap_component():
    return Trap(is_triggered=False, trigger_function=trigger_explosive_trap)

################################
## Monster Creation Functions ##
################################

# Create and return a teminatron fighter component
def create_terminatron_fighter_component():
    return Fighter(hp=100, armor=5, strength=13, accuracy=4, melee_damage=TERMINATRON_MELEE_DAMAGE, xp=10000, death_function=basic_monster_death)

# Create and return a mecharachnid fighter component
def create_mecharachnid_fighter_component():
    return Fighter(hp=15, armor=1, strength=3, accuracy=3, melee_damage=MECHARACHNID_MELEE_DAMAGE, xp=100, death_function=basic_monster_death)

# Create and return a cyborg fighter component
def create_cyborg_fighter_component():
    return Fighter(hp=8, armor=0, strength=2, accuracy=2, xp=35, ranged_damage=CYBORG_RANGED_DAMAGE, death_function=cyborg_death)

#############################
## Fighter Death Functions ##
#############################

# ends game is player dies!
def player_death(player):
    global game_state
    message('You died!', libtcod.red)
    game_state = 'dead'

    # for added effect, transform the player into a corpse!
    player.char = '%'
    player.color = libtcod.dark_red

# transform into a nasty corpse! it doesn't block, can't be attacked, and doesn't move
# NOTE: Generic monster death function
def basic_monster_death(monster):
    message(monster.name.capitalize() + ' is dead! You gain ' + str(monster.fighter.xp) + ' experience points.', libtcod.orange)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.z = CORPSE_Z_VAL
    monster.send_to_back()

    totalMonstersLeft = 0
    for obj in objects:
        if obj.fighter and obj != player:
            totalMonstersLeft += 1
    if (totalMonstersLeft == 0):
        message('The halls become quiet...', libtcod.light_blue)

# Cyborg death function (drop ammo, weapon)
def cyborg_death(monster):
    # drop pistol on death
    (x, y) = get_unblocked_tile_around(monster.x, monster.y)
    pistol_drop_chance = libtcod.random_get_int(0, 1, 100)
    if x is not None and pistol_drop_chance < 25:
        equipment_component = create_pistol_equipment()
        item = Object(x, y, '}', 'Pistol', libtcod.gray, equipment=equipment_component, always_visible=True, z=ITEM_Z_VAL)
        objects.append(item)

    # drop ammo on death
    (x, y) = get_unblocked_tile_around(monster.x, monster.y)
    ammo_drop_chance = libtcod.random_get_int(0, 1, 100)
    if x is not None and ammo_drop_chance < 75:
        item_component = Item()
        item = Object(x, y, '\'', '10mm ammo', libtcod.gray, capacity=7, max_capacity=100, item=item_component, always_visible=True, z=ITEM_Z_VAL) #TODO: debug: fix capacity
        objects.append(item)
        item.send_to_back()

    message(monster.name.capitalize() + ' is dead! You gain ' + str(monster.fighter.xp) + ' experience points.', libtcod.orange)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.z = CORPSE_Z_VAL
    monster.send_to_back()

    totalMonstersLeft = 0
    for obj in objects:
        if obj.fighter and obj != player:
            totalMonstersLeft += 1
    if (totalMonstersLeft == 0):
        message('The halls become quiet...', libtcod.light_blue)

#########################
## Animation Functions ##
#########################
# plays standard explosion animation with x, y at the center
# TODO: Finish explosion animation
#def explosion_animation(dx, dy, r):
#    print('In explosion animation...')
#    for i in range(r):
#        print('Setting char background...')
#        libtcod.console_set_char_background(con, dx, dy, libtcod.red, libtcod.BKGND_SET)
#        libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
#
#        if i != 0:
#            libtcod.console_set_char_background(con, dx+i, dy, libtcod.red, libtcod.BKGND_SET)
#            libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
#
#            libtcod.console_set_char_background(con, dx-i, dy, libtcod.red, libtcod.BKGND_SET)
#            libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
#
#            libtcod.console_set_char_background(con, dx, dy+i, libtcod.red, libtcod.BKGND_SET)
#            libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
#
#            libtcod.console_set_char_background(con, dx, dy-i, libtcod.red, libtcod.BKGND_SET)
#            libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
#
#        libtcod.console_flush()
#        sleep(1)

# this is where we decide the chance of each monster or item appearing
def place_objects(room):
    global monster_chances, item_chances, trap_chances, objects

    # max number of monsters per room
    max_monsters = from_dungeon_level([[2, 1], [5, 3], [7, 5]])

    # chance of each mosnter
    monster_chances = {}
    monster_chances['cyborg'] = 70
    monster_chances['mecharachnid'] = from_dungeon_level([[29, 1], [25, 3], [50, 5]])
    monster_chances['terminatron'] = from_dungeon_level([[1, 1], [5, 3], [8, 5]])

    # maximum number of items per room
    max_items = from_dungeon_level([[2, 1], [3, 3]])

    # chance of each item (by default they have a chance of 0 at level 1, which then goes up)
    item_chances = {}
    item_chances['heal'] = from_dungeon_level([[20, 1]])
    item_chances['scanner'] = from_dungeon_level([[500, 1]])
    item_chances['lightning'] = from_dungeon_level([[5, 1], [5, 4]])
    item_chances['impact_grenade'] = from_dungeon_level([[5, 1], [5, 6]])
    item_chances['emp'] = from_dungeon_level([[5, 1], [10, 2]])
    item_chances['dagger'] = from_dungeon_level([[15, 1]])
    item_chances['pistol'] = from_dungeon_level([[15, 1]])
    item_chances['10mm ammo'] = from_dungeon_level([[15, 1]])
    item_chances['heal_canister'] = from_dungeon_level([[999, 1]]) # TODO: Fix these numbers
    item_chances['strength_canister'] = from_dungeon_level([[999, 1]])

    # maximum number of traps
    max_traps = from_dungeon_level([[2, 1]])

    # chance of each trap spawning
    trap_chances = {}
    trap_chances['none'] = from_dungeon_level([[95, 1]])
    trap_chances['explosive_trap'] = from_dungeon_level([[5, 1]]) # TODO: DEBUGGING, CHANGE

    # choose random number of traps
    num_traps = libtcod.random_get_int(0, 0, max_traps)

    for i in range(num_traps):
        # choose random spot for this trap
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

        # only place it if the tile is NOT BLOCKED
        if not is_blocked(x, y):
            choice = random_choice(trap_chances)
            if choice is not 'none':
                if choice == 'explosive_trap':
                    # create an explosive trap
                    trap_component = create_explosive_trap_component()
                    trap = Object(x, y, ' ', 'Explosive Trap', libtcod.red, blocks=False, trap=trap_component, always_visible=True, z=TRAP_Z_VAL)

                if trap is not None:
                    print('Adding trap...')
                    objects.append(trap)

    # choose random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, max_monsters)

    for i in range(num_monsters):
        # choose random spot for this monster
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

        # alternatively, can create more chances and create squads of monsters
        # only place object if tile is not blocked
        if not is_blocked(x, y):
            choice = random_choice(monster_chances)
            if choice == 'terminatron':
                fighter_component = create_terminatron_fighter_component()
                ai_component = MeleeAI()
                monster = Object(x, y, 'T', 'Terminatron', libtcod.dark_red, always_visible=True, blocks=True, fighter=fighter_component, ai=ai_component, z=MONSTER_Z_VAL)
            elif choice == 'mecharachnid':
                fighter_component = create_mecharachnid_fighter_component()
                ai_component = MeleeAI()
                monster = Object(x, y, 'm', 'Mecharachnid', libtcod.light_grey, always_visible=True, blocks=True, fighter=fighter_component, ai=ai_component, z=MONSTER_Z_VAL)
            elif choice == 'cyborg':
                fighter_component = create_cyborg_fighter_component()
                ai_component = CyborgAI()
                monster = Object(x, y, 'c', 'Cyborg', libtcod.darker_gray, always_visible=True, blocks=True, fighter=fighter_component, ai=ai_component, z=MONSTER_Z_VAL)

            objects.append(monster)

    # choose random number of items
    num_items = libtcod.random_get_int(0, 0, max_items)

    for i in range(num_items):
        # choose random spot for this item
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

        # only place it if the tile is NOT BLOCKED
        if not is_blocked(x, y):
            choice = random_choice(item_chances)
            if choice == 'heal':
                # create a health pack
                item_component = create_health_pack_item_component()
                item = Object(x, y, '+', 'Health Pack', libtcod.violet, item=item_component, always_visible=True, z=ITEM_Z_VAL)
            elif choice == 'scanner':
                # create a scanner
                item_component = create_scanner_item_component()
                item = Object(x, y, '#', 'Scanner', libtcod.white, item=item_component, always_visible=True, z=ITEM_Z_VAL)
            elif choice == 'lightning':
                # create a lightning device
                item_component = create_lightning_device_item_component()
                item = Object(x, y, '#', 'Lightning Device', libtcod.light_blue, item=item_component, always_visible=True, z=ITEM_Z_VAL)
            elif choice == 'emp':
                # create an emp device
                item_component = create_emp_device_item_component()
                item = Object(x, y, '#', 'EMP Device', libtcod.light_yellow, item=item_component, always_visible=True, z=ITEM_Z_VAL)
            elif choice == 'impact_grenade':
                # create an impact grenade
                item_component = create_impact_grenade_item_component()
                item = Object(x, y, '#', 'Impact Grenade', libtcod.light_red, item=item_component, always_visible=True, z=ITEM_Z_VAL)
            elif choice == 'dagger':
                # create an energy dagger
                equipment_component = create_dagger_equipment()
                item = Object(x, y, '/', 'Dagger', libtcod.gray, equipment=equipment_component, always_visible=True, z=ITEM_Z_VAL)
            elif choice == 'pistol':
                # create a standard pistol
                equipment_component = create_pistol_equipment()
                item = Object(x, y, '}', 'Pistol', libtcod.gray, equipment=equipment_component, always_visible=True, z=ITEM_Z_VAL)
            elif choice == '10mm ammo':
                # create a 10mm_ammo
                item_component = Item()
                item = Object(x, y, '\'', '10mm Ammo', libtcod.gray, capacity=7, max_capacity=100, item=item_component, always_visible=True, z=ITEM_Z_VAL)
            elif choice == 'heal_canister':
                # create a health canister
                canister_component = create_health_canister_component()
                item = Object(x, y, '!', canister_component.get_name(), get_libtcod_color_from_string(canister_component.color), canister=canister_component, always_visible=True, z=ITEM_Z_VAL)
            elif choice == 'strength_canister':
                # create a strength canister
                canister_component = create_strength_canister_component()
                item = Object(x, y, '!', canister_component.get_name(), get_libtcod_color_from_string(canister_component.color), canister=canister_component, always_visible=True, z=ITEM_Z_VAL)

            objects.append(item)
            # item.send_to_back() # items appear below other objects

# render a bar (HP, experience, etc). first calculate the width of the bar
def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    bar_width = int(float(value) / maximum * total_width)
    
    # render the background first
    libtcod.console_set_default_background(hud_panel, back_color)
    libtcod.console_rect(hud_panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    # now render the bar on top
    libtcod.console_set_default_background(hud_panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(hud_panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    # finally, some centered text with the values
    libtcod.console_set_default_foreground(hud_panel, libtcod.white)
    libtcod.console_print_ex(hud_panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER, name + ': ' + str(value) + '/' + str(maximum))

# get information of entities under mouse cursor
def get_names_under_mouse():
    global mouse
    
    # return a string with the names of all objects under the mouse
    (x, y) = (mouse.cx, mouse.cy)

    # create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in objects
        if obj.x == x and obj.y == y and (libtcod.map_is_in_fov(fov_map, obj.x, obj.y) or (map[x][y].explored and obj.always_visible))]

    names = ', '.join(names) # join the names separated by commas
    return names

# get equipment and ammo information from player
def display_equipment_info():
    equipment_component = get_equipped_in_slot('weapon')
    if equipment_component is not None: # if there is some equipped item
        if equipment_component.is_ranged: # if equipment is ranged
            libtcod.console_print_ex(hud_panel, 1, 7, libtcod.BKGND_NONE, libtcod.LEFT, str(equipment_component.owner.name) + ' (' + str(equipment_component.ammo) + '/' + str(equipment_component.max_ammo) + ')')
        else:
            libtcod.console_print_ex(hud_panel, 1, 7, libtcod.BKGND_NONE, libtcod.LEFT, str(equipment_component.owner.name))
    else:
        libtcod.console_print_ex(hud_panel, 1, 7, libtcod.BKGND_NONE, libtcod.LEFT, 'Unarmed')    

# get total ammo info and display
def display_ammo_count():
    libtcod.console_print_ex(hud_panel, 1, 8, libtcod.BKGND_NONE, libtcod.LEFT, '10mm: ' + str(player.fighter.ten_mm_rounds) + '/' + str(player.fighter.max_ten_mm_rounds))

# display the chance to hit Fighter at Reticule
def display_info_at_reticule():
    string = ''
    if game_state == 'aiming': # if aiming
        enemy = get_fighter_by_tile(reticule.x, reticule.y)
        if enemy is not None and enemy is not player:
            chance_to_hit = 10 + (player.fighter.accuracy - enemy.fighter.evasion)
            string = 'Chance to hit: ' + str(round((chance_to_hit / float(18)) * 100, 1)) + '%%'
    else: # if looking
        # create a list with the names of all objects at the reticule's coordinates and in FOV
        string = [obj.name for obj in objects
            if obj.x == reticule.x and obj.y == reticule.y and obj.name != 'Reticule' and ((libtcod.map_is_in_fov(fov_map, obj.x, obj.y) or (map[reticule.x][reticule.y].explored and obj.always_visible)))]

        string = ', '.join(string) # join the names separated by commas
    
    return string

# display the player's stats to hud screen
def display_player_stats():
    # get equipment to test for identified status
    equipment = get_equipped_in_slot('weapon')

    # RUN_STATUS
    if player.fighter.run_status == 'rested':
        libtcod.console_set_default_foreground(hud_panel, libtcod.white)
    elif player.fighter.run_status == 'running':
        libtcod.console_set_default_foreground(hud_panel, libtcod.yellow)
    elif player.fighter.run_status == 'tired':
        libtcod.console_set_default_foreground(hud_panel, libtcod.grey)
    libtcod.console_print_ex(hud_panel, 1, SCREEN_HEIGHT/3 - 1, libtcod.BKGND_NONE, libtcod.LEFT, player.fighter.run_status)

    # MOVE STATUS
    if player.fighter.has_moved_this_turn is True:
        libtcod.console_set_default_foreground(hud_panel, libtcod.yellow)
        libtcod.console_print_ex(hud_panel, HUD_WIDTH/2, SCREEN_HEIGHT/3 - 1, libtcod.BKGND_NONE, libtcod.CENTER, 'moving')
    else:
        libtcod.console_set_default_foreground(hud_panel, libtcod.white)
        libtcod.console_print_ex(hud_panel, HUD_WIDTH/2, SCREEN_HEIGHT/3 - 1, libtcod.BKGND_NONE, libtcod.CENTER, 'standing')

    # STR
    libtcod.console_set_default_foreground(hud_panel, libtcod.gold)
    libtcod.console_print_ex(hud_panel, 1, SCREEN_HEIGHT/3 + 1, libtcod.BKGND_NONE, libtcod.LEFT, 'STR: ')
    libtcod.console_set_default_foreground(hud_panel, libtcod.silver)
    libtcod.console_print_ex(hud_panel, 6, SCREEN_HEIGHT/3 + 1, libtcod.BKGND_NONE, libtcod.LEFT, str(player.fighter.strength))

    # FIN
    libtcod.console_set_default_foreground(hud_panel, libtcod.gold)
    libtcod.console_print_ex(hud_panel, 1, SCREEN_HEIGHT/3 + 2, libtcod.BKGND_NONE, libtcod.LEFT, 'FIN: ')
    libtcod.console_set_default_foreground(hud_panel, libtcod.silver)
    libtcod.console_print_ex(hud_panel, 6, SCREEN_HEIGHT/3 + 2, libtcod.BKGND_NONE, libtcod.LEFT, str(player.fighter.finesse))

    # ACC
    libtcod.console_set_default_foreground(hud_panel, libtcod.gold)
    libtcod.console_print_ex(hud_panel, 1, SCREEN_HEIGHT/3 + 3, libtcod.BKGND_NONE, libtcod.LEFT, 'ACC: ')
    libtcod.console_set_default_foreground(hud_panel, libtcod.silver)
    libtcod.console_print_ex(hud_panel, 6, SCREEN_HEIGHT/3 + 3, libtcod.BKGND_NONE, libtcod.LEFT, str(player.fighter.accuracy))

    # EVA
    libtcod.console_set_default_foreground(hud_panel, libtcod.gold)
    libtcod.console_print_ex(hud_panel, 1, SCREEN_HEIGHT/3 + 4, libtcod.BKGND_NONE, libtcod.LEFT, 'EVA: ')
    libtcod.console_set_default_foreground(hud_panel, libtcod.silver)
    libtcod.console_print_ex(hud_panel, 6, SCREEN_HEIGHT/3 + 4, libtcod.BKGND_NONE, libtcod.LEFT, str(player.fighter.evasion))

    # ARM
    libtcod.console_set_default_foreground(hud_panel, libtcod.gold)
    libtcod.console_print_ex(hud_panel, 1, SCREEN_HEIGHT/3 + 5, libtcod.BKGND_NONE, libtcod.LEFT, 'ARM: ')
    libtcod.console_set_default_foreground(hud_panel, libtcod.silver)
    libtcod.console_print_ex(hud_panel, 6, SCREEN_HEIGHT/3 + 5, libtcod.BKGND_NONE, libtcod.LEFT, str(player.fighter.armor))

    # MELEE DAMAGE
    libtcod.console_set_default_foreground(hud_panel, libtcod.gold)
    libtcod.console_print_ex(hud_panel, HUD_WIDTH/2 - 5, SCREEN_HEIGHT/3 + 2, libtcod.BKGND_NONE, libtcod.LEFT, 'MELEE DMG: ')
    libtcod.console_set_default_foreground(hud_panel, libtcod.silver)
    if equipment.is_identified is True:
        libtcod.console_print_ex(hud_panel, HUD_WIDTH/2 + 6, SCREEN_HEIGHT/3 + 2, libtcod.BKGND_NONE, libtcod.LEFT, str(player.fighter.melee_damage))
    else:
        libtcod.console_print_ex(hud_panel, HUD_WIDTH/2 + 6, SCREEN_HEIGHT/3 + 2, libtcod.BKGND_NONE, libtcod.LEFT, '?')

    # RANGED DAMAGE
    libtcod.console_set_default_foreground(hud_panel, libtcod.gold)
    libtcod.console_print_ex(hud_panel, HUD_WIDTH/2 - 5, SCREEN_HEIGHT/3 + 4, libtcod.BKGND_NONE, libtcod.LEFT, 'RANGE DMG: ')
    libtcod.console_set_default_foreground(hud_panel, libtcod.silver)
    if equipment.is_identified is True:
        libtcod.console_print_ex(hud_panel, HUD_WIDTH/2 + 6, SCREEN_HEIGHT/3 + 4, libtcod.BKGND_NONE, libtcod.LEFT, str(player.fighter.ranged_damage))
    else:
        libtcod.console_print_ex(hud_panel, HUD_WIDTH/2 + 6, SCREEN_HEIGHT/3 + 4, libtcod.BKGND_NONE, libtcod.LEFT, '?')

# render game information to screen
def render_all():
    global fov_map, color_dark_wall, color_light_wall
    global color_dark_ground, color_light_ground
    global fov_recompute

    # prepare to render the LOG panel
    libtcod.console_set_default_background(log_panel, libtcod.black)
    libtcod.console_clear(log_panel)

    # prepare to render the HUD panel
    libtcod.console_set_default_background(hud_panel, libtcod.black)
    libtcod.console_clear(hud_panel)
 
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
                    # TODO: scale lighting based on distance
                    if wall:
                        libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET)
                    # since it's visible, it's explored
                    map[x][y].explored = True
 
    # draw all objects in the list except player and reticule
    objects_sorted = sorted(objects, key=lambda x: x.z, reverse=False)
    for object in objects_sorted:
        if object != player or object != reticule:
            object.draw()
    player.draw() # draw the player object
    # draw the reticule object last (over the player)
    if reticule is not None:
        if libtcod.map_is_in_fov(fov_map, reticule.x, reticule.y) or map[reticule.x][reticule.y].explored:
            # display names of objects under the mouse
            libtcod.console_set_default_foreground(hud_panel, libtcod.light_grey) #changed to light_gray
            libtcod.console_print_ex(hud_panel, 1, SCREEN_HEIGHT/2, libtcod.BKGND_NONE, libtcod.LEFT, display_info_at_reticule())
        reticule.draw()
        libtcod.line_init(player.x, player.y, reticule.x, reticule.y)
        prev_x, prev_y = player.x, player.y
        x, y = libtcod.line_step()
        while (x is not None):
            #stop drawing line segments once we're at the reticule
            if (x == reticule.x and y == reticule.y):
                break
            #set the color and then draw the character that represents this object at its position
            #if a segment intersects with a blocking tile, color it red
            if (is_blocked(x, y) or not libtcod.map_is_in_fov(fov_map, x, y)):
                libtcod.console_set_default_foreground(con, libtcod.red)
            else:
                libtcod.console_set_default_foreground(con, reticule.color)
            normal_vec = point_to_point_vector(prev_x, prev_y, x, y)
            if normal_vec == (1, 0) or normal_vec == (-1, 0): # bullet traveling right or left
                libtcod.console_put_char(con, x, y, '-', libtcod.BKGND_NONE)
            elif normal_vec == (0, 1) or normal_vec == (0, -1): # bullet traveling up or down
                libtcod.console_put_char(con, x, y, '|', libtcod.BKGND_NONE)
            elif normal_vec == (1, 1) or normal_vec == (-1, -1): # bullet traveling upright or downleft
                libtcod.console_put_char(con, x, y, '\\', libtcod.BKGND_NONE)
            elif normal_vec == (-1, 1) or normal_vec == (1, -1): # bullet traveling upleft or downright
                libtcod.console_put_char(con, x, y, '/', libtcod.BKGND_NONE)
            else: # TODO: DEBUG: this shouldn't be reached but if so, debug
                libtcod.console_put_char(con, x, y, '*', libtcod.BKGND_NONE)
            prev_x, prev_y = x, y
            x, y = libtcod.line_step()

    # blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)

    # print the game messages one line at a time
    y = 1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(log_panel, color)
        libtcod.console_print_ex(log_panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1

    # show the player's health
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.base_max_hp, libtcod.light_red, libtcod.darker_red)

    # show the player's XP
    # TODO: THIS IS UNTESTED. Make sure this works with all levels/XP levels.
    render_bar(1, 3, BAR_WIDTH, 'XP', player.fighter.xp, LEVEL_UP_XP, libtcod.dark_yellow, libtcod.darkest_yellow)

    # show the player's current level
    # TODO: Add titles next to the player's level
    libtcod.console_print_ex(hud_panel, HUD_WIDTH/2, 5, libtcod.BKGND_NONE, libtcod.CENTER, 'Level ' + str(player.level))

    # show the player's equipment and ammo (if applicable)
    display_equipment_info()

    # show the player's total ammo count
    # TODO: Leverage for multiple ammo types
    display_ammo_count()

    # show the player's stats
    display_player_stats()

    # display dungeon level to GUI
    libtcod.console_print_ex(hud_panel, HUD_WIDTH/2, SCREEN_HEIGHT - 2, libtcod.BKGND_NONE, libtcod.CENTER, 'Dungeon level ' + str(dungeon_level))

    # display names of objects under the mouse
    libtcod.console_set_default_foreground(hud_panel, libtcod.light_grey) #changed to light_gray
    libtcod.console_print_ex(hud_panel, 1, SCREEN_HEIGHT/2, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())

    # blit the contents of "panel" to the root console
    libtcod.console_blit(log_panel, 0, 0, SCREEN_WIDTH - HUD_WIDTH, LOG_HEIGHT, 0, 0, LOG_Y)
    libtcod.console_blit(hud_panel, 0, 0, HUD_WIDTH, SCREEN_HEIGHT, 0, SCREEN_WIDTH - HUD_WIDTH, 0)

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
    if target is not None: # TODO: add AND conditional to check that weapon is melee
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        if player.fighter.run_status == 'running':
            if player.fighter.run_duration > 0:
                player.fighter.run_duration -= 1
            elif player.fighter.run_duration <= 0:
                player.fighter.run_status = 'tired'
                message('You become tired!', libtcod.red)
        fov_recompute = True

        trap = get_trap_by_tile(player.x, player.y)
        if trap is not None and trap.trap.is_triggered is False:
            trap.char = '^'
            trap.trap.is_triggered = True
            trap.trap.trigger_function(player.x, player.y)

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

# see if the player's experience is enough to level-up
# TODO: REVAMP THIS FUNCTION TOTALLY
def check_level_up():
    LEVEL_UP_XP = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
    if player.fighter.xp >= LEVEL_UP_XP:
        # level up!
        player.level += 1
        player.fighter.xp -= LEVEL_UP_XP
        message('Your battle skills grow stronger! You reached level ' + str(player.level) + '!', libtcod.yellow)

        choice = None
        while choice == None: # keep asking until a choice is made
            choice = menu('Level up! Choose a stat to raise:\n',
                ['Health (+20 HP, from ' + str(player.fighter.base_max_hp) + ')',
                'Attack (+1 attack, from ' + str(player.fighter.base_power) + ')',
                'Defense (+1 defense, from ' + str(player.fighter.base_defense) + ')'], LEVEL_SCREEN_WIDTH)

        if choice == 0:
            player.fighter.base_max_hp += 20
            player.fighter.hp += 20
        elif choice == 1:
            player.fighter.base_power += 1
        elif choice == 2:
            player.fighter.base_defense += 1

# returns the equipment in a slot, or None if it's empty
def get_equipped_in_slot(slot):
    for obj in inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
            return obj.equipment
    return None

# returns a list of equipped items
def get_all_equipped(obj):
    if obj == player:
        equipped_list = []
        for item in inventory:
            if item.equipment and item.equipment.is_equipped:
                equipped_list.append(item.equipment)
        return equipped_list
    else:
        return [] # other objects have no equipment

# define a menu window. Has a string at the top (header), list of strings (options. can be names of items, for ex), and the window's width (width)
def menu(header, options, width):
    global key, mouse

    if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')

    # calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
    if header == '':
        header_height = 0
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

    # compute x and y offsets to convert console position to menu position
    x_offset = x #x is the left edge of the menu
    y_offset = y + header_height #subtract the height of the header from the top edge of the menu

    while True:
        # present the root console to the player and wait for a key-press
        libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

        if (mouse.lbutton_pressed):
            (menu_x, menu_y) = (mouse.cx - x_offset, mouse.cy - y_offset)
            # check if click is within the menu and on a choice
            if menu_x >= 0 and menu_x < width and menu_y >= 0 and menu_y < height - header_height:
                return menu_y

        if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            return None #cancel if the player right-clicked or pressed Escape

        if key.vk == libtcod.KEY_ENTER and key.ralt:    #Alt+Enter: toggle fullscreen
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        # convert the ASCII code to an index; if it corresponds to an option, return it
        index = key.c - ord('a')
        if index >= 0 and index < len(options): return index
        # if they pressed a letter that is not an option, return None
        if index >= 0 and index <= 26: return None

# show a menu with each item of the inventory as an option
def inventory_menu(header):
    global inventory

    if len(inventory) == 0:
        options = ['Inventory is empty.']
    else:
        inventory.sort(key=lambda k: k.name, reverse=False)
        options = []
        for item in inventory:
            # if equipment, show ammo. if not, show item name
            text = item.name + ' (' + str(item.equipment.ammo) + '/' + str(item.equipment.max_ammo) + ')' if (item.equipment and item.equipment.is_ranged) else item.name
            # show additional information, in case it's equipped
            if item.equipment and item.equipment.is_equipped:
                text = text + ' (on ' + item.equipment.slot + ')'
            options.append(text)

    index = menu(header, options, INVENTORY_WIDTH)

    # if an item was chosen, return it
    if index is None or len(inventory) == 0: return None
    return inventory[index].item

# show a menu with items to scan
def scan_menu(header):
    scan_inventory = []
    if inventory is not None and len(inventory) == 0:
        options = ['Nothing to scan.']
    else:
        inventory.sort(key=lambda k: k.name, reverse=False)
        options = []
        for item in inventory:
            if item.equipment and item.equipment.is_identified is False:
                scan_inventory.append(item)
                # if equipment, show ammo. if not, show item name
                text = item.name + ' (' + str(item.equipment.ammo) + '/' + str(item.equipment.max_ammo) + ')' if (item.equipment and item.equipment.is_ranged) else item.name
                if item.equipment and item.equipment.is_equipped:
                    text = text + ' (on ' + item.equipment.slot + ')'
                options.append(text)
            elif item.canister and item.canister.is_identified is False:
                scan_inventory.append(item)
                text = item.name
                options.append(text)

    index = menu(header, options, INVENTORY_WIDTH)

    # if an item was chosen, return it
    if index is None or len(scan_inventory) == 0: return None
    return scan_inventory[index].item

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

# player takes aim at a target tile
def take_aim(key_char):
    global game_state, reticule, is_aiming_item

    monster = closest_monster(TORCH_RADIUS)
    if monster is not None:
        (x, y) = (monster.x, monster.y)
    else:
        (x, y) = (player.x+1, player.y)

    reticule = Object(x, y, 'X', 'Reticule', libtcod.red, always_visible=True, z=RETICULE_Z_VAL)
    if key_char == 'f': # if aiming
        game_state = 'aiming'
        reticule = Object(x, y, 'X', 'Reticule', libtcod.green, always_visible=True, z=RETICULE_Z_VAL)
        message('Press \'F\' again to shoot weapon, any other key to cancel.', libtcod.cyan)
    elif key_char == 'l': # if looking
        game_state = 'looking'
        reticule = Object(x, y, 'X', 'Reticule', libtcod.white, always_visible=True, z=RETICULE_Z_VAL)
        message('Press any key to cancel examining.', libtcod.cyan)
    else:
        game_state = 'aiming'
        message('Press any key to cancel using item.', libtcod.cyan)
        
    objects.append(reticule)

# clear all reticule segments between player and reticule
def clear_reticule_segments():
    libtcod.line_init(player.x, player.y, reticule.x, reticule.y)
    x, y = libtcod.line_step()
    while (x is not None):
        if (x == reticule.x and y == reticule.y):
            break
        libtcod.console_put_char(con, x, y, ' ', libtcod.BKGND_NONE)
        x, y = libtcod.line_step()

def move_reticule(dx, dy):
    # before moving reticule, clear reticule segments
    clear_reticule_segments()

    # move reticule to specified coordinates
    reticule.move_reticule(dx, dy)

# heal the player
def cast_heal():
    if player.fighter.hp == player.fighter.base_max_hp: # don't heal the player if at full hp already
        message('You are already at full health.', libtcod.red)
        return 'cancelled'

    message('Your wounds start to feel better!', libtcod.light_violet)
    player.fighter.heal(HEAL_AMOUNT)

def cast_increase_strength():
    message('You feel stronger.', libtcod.light_violet)
    player.fighter.strength += 1

# scan an item to reveal its properties
# TODO: Finish scan item
def cast_scan_item():
    render_all()
    chosen_item = scan_menu('Press the key next to an item to scan it, or any other to cancel.\n')
    print('Chosen_item: ' + str(chosen_item.owner.name))
    if chosen_item is not None:
        player.fighter.has_moved_this_turn = False
        chosen_item.scan()
        scanner = next((i for i in inventory if i.name == 'Scanner'), None)
        inventory.remove(scanner)
        return 'turn-taken'

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
# TODO: When EMP is used and cast_shoot(), ghost images exist
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
def cast_impact_grenade(dx, dy, item):
    global is_aiming_item, objects

    if dx is None: return 'cancelled'

    # if there is a blocking tile between player and reticule, explode at that blocking tile instead
    libtcod.line_init(player.x, player.y, dx, dy)
    x, y = libtcod.line_step()
    while (x is not None and x != dx):
        if is_blocked(x, y):
            (dx, dy) = (x, y)
            break
        x, y = libtcod.line_step()

    message('The impact grenade explodes, burning everything within ' + str(IMPACT_GRENADE_RADIUS) + ' tiles!', libtcod.orange)

    for obj in objects: # damage every fighter in range, including the player
        if obj.fighter and is_line_blocked_by_wall(player.x, player.y, dx, dy) is False and obj.distance(dx, dy) <= IMPACT_GRENADE_RADIUS:
            totalDamage = roll_dice(IMPACT_GRENADE_DAMAGE)
            message('The ' + obj.name + ' gets burned for ' + str(totalDamage) + ' hit points.', libtcod.orange)
            obj.fighter.take_damage(totalDamage)

    is_aiming_item = False
    inventory.remove(item)

# aim the impact grenade using the reticule
def cast_aim_impact_grenade():
    global is_aiming_item, game_state

    is_aiming_item = True
    i = find_in_inventory('Impact Grenade')
    i.item.is_being_used = True
    take_aim(None)

# shoot pistol at tile (dx, dy)
def cast_shoot_pistol(dx, dy, weapon):
    monsterFound = False

    if weapon != None and weapon.is_ranged:
        if dx is None: return 'cancelled'

        if weapon.ammo > 0:
            totalDamage = roll_dice(player.fighter.ranged_damage)
            weapon.ammo -= 1

            # check if player shot themselves
            if (player.x == dx and player.y == dy):
                message(player.name + ' shoots themselves for ' + str(totalDamage) + ' hit points!', libtcod.red)
                player.fighter.take_damage(totalDamage)
                return # exit the function

            # slope between player and reticule
            m_x = dx - player.x
            m_y = dy - player.y
            # starting x and y
            start_x = player.x
            start_y = player.y

            # Find furthest blocking tile
            hasHit = False
            
            while (hasHit is False):
                libtcod.line_init(start_x, start_y, dx, dy)
                prev_x, prev_y = start_x, start_y
                x, y = libtcod.line_step()
                while (x is not None):
                    (min, max) = get_min_max_dmg(player.fighter.ranged_damage)
                    if (totalDamage == max):
                        libtcod.console_set_default_foreground(con, libtcod.sky)
                    elif (totalDamage == min):
                        libtcod.console_set_default_foreground(con, libtcod.red)
                    else:
                        libtcod.console_set_default_foreground(con, libtcod.white)
                    #if libtcod.map_is_in_fov(fov_map, x, y):
                    normal_vec = point_to_point_vector(prev_x, prev_y, x, y)
                    if normal_vec == (1, 0) or normal_vec == (-1, 0): # bullet traveling right or left
                        libtcod.console_put_char(con, x, y, '-', libtcod.BKGND_NONE)
                    elif normal_vec == (0, 1) or normal_vec == (0, -1): # bullet traveling up or down
                        libtcod.console_put_char(con, x, y, '|', libtcod.BKGND_NONE)
                    elif normal_vec == (1, 1) or normal_vec == (-1, -1): # bullet traveling upright or downleft
                        libtcod.console_put_char(con, x, y, '\\', libtcod.BKGND_NONE)
                    elif normal_vec == (-1, 1) or normal_vec == (1, -1): # bullet traveling upleft or downright
                        libtcod.console_put_char(con, x, y, '/', libtcod.BKGND_NONE)
                    else: # TODO: DEBUG: this shouldn't be reached but if so, debug
                        libtcod.console_put_char(con, x, y, '*', libtcod.BKGND_NONE)
                    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
                    libtcod.console_flush()
                    sleep(PROJECTILE_SLEEP_TIME)
                    obj = get_object_by_tile(x, y)
                    if is_blocked(x, y) and obj is not None and obj.fighter is not None and roll_to_hit(accuracy_bonus=player.fighter.accuracy, evasion_penalty=obj.fighter.evasion) is True: # if bullet hits a blocked tile at x, y
                        #if libtcod.map_is_in_fov(fov_map, x, y):
                        libtcod.console_put_char(con, x, y, 'x', libtcod.BKGND_NONE)
                        libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
                        libtcod.console_flush()
                        sleep(PROJECTILE_SLEEP_TIME)
                        hit_obj = get_fighter_by_tile(x, y)
                        hasHit = True
                        if hit_obj and hit_obj.fighter:
                            monsterFound = True
                            message(hit_obj.name + ' is shot for ' + str(totalDamage) + ' hit points.', libtcod.orange)
                            hit_obj.fighter.take_damage(totalDamage)
                            break
                        if monsterFound is False:
                            message('The shot misses any meaningful target.', libtcod.red)
                        break
                    elif is_blocked(x, y) and obj is None:
                        #if libtcod.map_is_in_fov(fov_map, x, y):
                        libtcod.console_put_char(con, x, y, 'x', libtcod.BKGND_NONE)
                        libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
                        libtcod.console_flush()
                        sleep(PROJECTILE_SLEEP_TIME)
                        hasHit = True
                        message('The shot misses any meaningful target.', libtcod.red)
                        break
                    else:
                        libtcod.console_put_char(con, x, y, ' ', libtcod.BKGND_NONE)
                        # redraws objs if a bullet is shot over them
                        if obj is not None:
                            obj.draw()
                        prev_x, prev_y = x, y
                        x, y = libtcod.line_step()
                if (x is not None): # delete bullet char from spot hit
                    libtcod.console_put_char(con, x, y, ' ', libtcod.BKGND_NONE)
                    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
                # bullet reached reticule, extend reticule
                start_x = dx
                start_y = dy
                dx = dx + m_x
                dy = dy + m_y

        else:
            message('Your ' + weapon.owner.name + ' is empty!', libtcod.orange)
            return 'cancelled'

# shoot currently equipped weapon at tile (dx, dy)
def cast_shoot(dx, dy):
    remove_reticule()
    render_all()
    weapon = get_equipped_in_slot('weapon')
    return weapon.shoot_function(dx, dy, weapon)

# shoot currently used item at tile (dx, dy)
def cast_shoot_item(dx, dy, item):
    remove_reticule()
    render_all()

    # cases for which item to fire
    if item.name == 'Impact Grenade':
        cast_impact_grenade(dx, dy, item)

# reload the weapon in your right hand
def cast_reload():
    weapon = get_equipped_in_slot('weapon')
    ammo_to_reload = player.fighter.ten_mm_rounds > 0

    if weapon != None and weapon.is_ranged and weapon.ammo < weapon.max_ammo and ammo_to_reload is True:
        message('You reload ' + weapon.owner.name + '!', libtcod.orange)
        amount_to_reload = weapon.max_ammo - weapon.ammo
        if amount_to_reload > player.fighter.ten_mm_rounds: # if we can reload some but not all
            weapon.ammo += player.fighter.ten_mm_rounds
            player.fighter.ten_mm_rounds = 0
        else: # we can reload to full
            weapon.ammo += amount_to_reload
            player.fighter.ten_mm_rounds -= amount_to_reload
        #equipped = get_equipped_in_slot(weapon.slot)
        #equipped.ammo += equipped.max_ammo - equipped.ammo
    elif weapon != None and weapon.is_ranged and weapon.ammo == weapon.max_ammo:
        message(weapon.owner.name + ' is already full of ammo!', libtcod.red)
        return 'cancelled'
    elif weapon == None:
        message('Nothing to reload!', libtcod.red)
        return 'cancelled'
    elif ammo_to_reload is False:
        message('No ammo!', libtcod.red)
        return 'cancelled'

############################
## Trap Trigger Functions ##
############################
# TODO: Finish explosive trap
def trigger_explosive_trap(dx, dy):
    global fov_map

    fighter = get_fighter_by_tile(dx, dy)
    if fighter is not None:
        #explosion_animation(dx, dy, IMPACT_GRENADE_RADIUS)
        message('The tile underneath ' + fighter.name + ' explodes!', libtcod.orange)
        for obj in objects: # damage every fighter in range, including the player
            if obj.fighter and is_line_blocked_by_wall(fighter.x, fighter.y, dx, dy) is False and obj.distance(dx, dy) <= IMPACT_GRENADE_RADIUS:
                totalDamage = roll_dice(IMPACT_GRENADE_DAMAGE)
                message('The ' + obj.name + ' gets burned for ' + str(totalDamage) + ' hit points.', libtcod.orange)
                obj.fighter.take_damage(totalDamage)

# a box for messages straight to MAIN MENU
def msgbox(text, width=50):
    menu(text, [], width) #use menu() as a sort of "message box"

# finds an object in inventory, retrieves it
def find_in_inventory(obj_str):
    for item in inventory:
        print('Item: ' + item.name)
        if item.name == obj_str:
            return item
    
    return None

# finds an object and removes it from inventory
def remove_from_inventory(obj_str):
    for item in inventory:
        if item.name == obj_str:
            inventory.remove(item)
            return True
    return False

def remove_reticule():
    global game_state, reticule

    clear_reticule_segments()

    objects.remove(reticule)
    reticule = None
    game_state = 'playing'

# handle player inputs
def handle_keys():
    global fov_recompute, key, reticule, game_state, inventory, is_aiming_item
 
    if key.vk == libtcod.KEY_ENTER and key.ralt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
        return 'didnt-take-turn'
 
    elif key.vk == libtcod.KEY_ESCAPE and game_state is not 'aiming' and game_state is not 'looking':
        return 'exit'  #exit game

    if game_state == 'looking':
        if key.vk == libtcod.KEY_UP:
            move_reticule(0, -1)
    
        elif key.vk == libtcod.KEY_DOWN:
            move_reticule(0, 1)
    
        elif key.vk == libtcod.KEY_LEFT:
            move_reticule(-1, 0)
    
        elif key.vk == libtcod.KEY_RIGHT:
            move_reticule(1, 0)

        elif key.vk == libtcod.KEY_KP8:
            move_reticule(0, -1)

        elif key.vk == libtcod.KEY_KP2:
            move_reticule(0, 1)

        elif key.vk == libtcod.KEY_KP4:
            move_reticule(-1, 0)

        elif key.vk == libtcod.KEY_KP6:
            move_reticule(1, 0)

        elif key.vk == libtcod.KEY_KP1:
            move_reticule(-1, 1)

        elif key.vk == libtcod.KEY_KP7:
            move_reticule(-1, -1)

        elif key.vk == libtcod.KEY_KP9:
            move_reticule(1, -1)

        elif key.vk == libtcod.KEY_KP3:
            move_reticule(1, 1)
        else:
            # test for other keys
            key_char = chr(key.c)

            # cancel look with any key
            if key.c is not 0 and key.vk is not 0:
                print('Cancelling look! ' + key_char)
                game_state = 'playing'
                remove_reticule()
                return 'didnt-take-turn'

    if game_state == 'aiming':
        if key.vk == libtcod.KEY_UP:
            move_reticule(0, -1)
    
        elif key.vk == libtcod.KEY_DOWN:
            move_reticule(0, 1)
    
        elif key.vk == libtcod.KEY_LEFT:
            move_reticule(-1, 0)
    
        elif key.vk == libtcod.KEY_RIGHT:
            move_reticule(1, 0)

        elif key.vk == libtcod.KEY_KP8:
            move_reticule(0, -1)

        elif key.vk == libtcod.KEY_KP2:
            move_reticule(0, 1)

        elif key.vk == libtcod.KEY_KP4:
            move_reticule(-1, 0)

        elif key.vk == libtcod.KEY_KP6:
            move_reticule(1, 0)

        elif key.vk == libtcod.KEY_KP1:
            move_reticule(-1, 1)

        elif key.vk == libtcod.KEY_KP7:
            move_reticule(-1, -1)

        elif key.vk == libtcod.KEY_KP9:
            move_reticule(1, -1)

        elif key.vk == libtcod.KEY_KP3:
            move_reticule(1, 1)
        else:
            # test for other keys
            key_char = chr(key.c)
            item = next((i for i in inventory if i.item.is_being_used == True), None)

            # shoot if Player presses F while aiming
            if key_char == 'f':
                if is_aiming_item is False: # if not aiming an item
                    if cast_shoot(reticule.x, reticule.y) is not 'cancelled':
                        player.fighter.has_moved_this_turn = False
                        return 'turn-taken'
                    else:
                        return 'didnt-take-turn'
                elif is_aiming_item is True: # if you are aiming an item
                    print('Item is ' + str(item))
                    if item is not None and cast_shoot_item(reticule.x, reticule.y, item) is not 'cancelled':
                        player.fighter.has_moved_this_turn = False
                        return 'turn-taken'
                    else:
                        return 'didnt-take-turn'
            elif key_char is not 'f' and key.c is not 0 and key.vk is not 0:
                remove_reticule()
                if item is not None:
                    item.item.is_being_used = False
                is_aiming_item = False
                return 'didnt-take-turn'

    if game_state == 'playing':
        #movement keys
        if key.vk == libtcod.KEY_UP:
            player_move_or_attack(0, -1)
    
        elif key.vk == libtcod.KEY_DOWN:
            player_move_or_attack(0, 1)
    
        elif key.vk == libtcod.KEY_LEFT:
            player_move_or_attack(-1, 0)
    
        elif key.vk == libtcod.KEY_RIGHT:
            player_move_or_attack(1, 0)

        elif key.vk == libtcod.KEY_KP8:
            player_move_or_attack(0, -1)

        elif key.vk == libtcod.KEY_KP2:
            player_move_or_attack(0, 1)

        elif key.vk == libtcod.KEY_KP4:
            player_move_or_attack(-1, 0)

        elif key.vk == libtcod.KEY_KP6:
            player_move_or_attack(1, 0)

        elif key.vk == libtcod.KEY_KP1:
            player_move_or_attack(-1, 1)

        elif key.vk == libtcod.KEY_KP7:
            player_move_or_attack(-1, -1)

        elif key.vk == libtcod.KEY_KP9:
            player_move_or_attack(1, -1)

        elif key.vk == libtcod.KEY_KP3:
            player_move_or_attack(1, 1)

        elif key.vk == libtcod.KEY_KP5: #player does nothing, same as "Wait"
            player.fighter.has_moved_this_turn = False
            pass

        elif key.vk == libtcod.KEY_BACKSPACE:
            player.fighter.has_moved_this_turn = False
            # show the inventory; if an item is selected, drop it
            chosen_item = inventory_menu('Press the key next to an item to drop it, or any other to cancel.\n')
            if chosen_item is not None:
                chosen_item.drop()

        elif key.vk == libtcod.KEY_TAB:
            player.fighter.has_moved_this_turn = False
            # if player is rested, begin running. If running, stop running. If tired, display message saying "Can't run"
            if player.fighter.run_status == 'rested':
                player.fighter.run_status = 'running'
            elif player.fighter.run_status == 'running':
                player.fighter.run_status = 'tired'
            elif player.fighter.run_status == 'tired':
                message('You are too tired to run!', libtcod.red)

        else:
            # test for other keys
            key_char = chr(key.c)

            if key_char == 'g':
                # pick up an item
                for object in objects: #look for an item in the player's tile
                    if object.x == player.x and object.y == player.y and object.item:
                        player.fighter.has_moved_this_turn = False
                        object.item.pick_up()
                        return 'turn-taken'

            if key_char == 'i':
                # show the inventory; if an item is selected, use it
                chosen_item = inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
                if chosen_item is not None:
                    player.fighter.has_moved_this_turn = False
                    chosen_item.use()
                    return 'turn-taken'

            if key_char == 'c':
                # show character stats
                print('Player.fighter: ' + str(player.fighter))
                LEVEL_UP_XP = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
                msgbox('Character Information\n\nLevel: ' + str(player.level) + '\nExperience: ' + str(player.fighter.xp) + 
                    '\nExperience to level up: ' + str(LEVEL_UP_XP) + '\n\nMaximum HP: ' + str(player.fighter.max_hp) + 
                    '\nMelee Damage: ' + str(player.fighter.melee_damage) + '\nRanged Damage: ' + str(player.fighter.ranged_damage) +
                     '\nArmor: ' + str(player.fighter.armor), CHARACTER_SCREEN_WIDTH)

            if key_char == 'r':
                # reload current weapon
                player.fighter.has_moved_this_turn = False
                if cast_reload() is not 'cancelled':
                    return 'turn-taken'

            # use equipment; if ranged, call cast_shoot() function
            if key_char == 'f':
                if get_equipped_in_slot('weapon') is not None and get_equipped_in_slot('weapon').is_ranged:
                    if take_aim(key_char) is not 'cancelled':
                        return 'turn-taken'
                else:
                    message('No weapon to shoot with!', libtcod.red)

            # call cast_look() function
            if key_char == 'l':
                take_aim(key_char)

            if key_char == '.' and key.shift:
                # go down the stairs, if the player is on them
                if stairs.x == player.x and stairs.y == player.y:
                    player.fighter.has_moved_this_turn = False
                    next_level()

            return 'didnt-take-turn'

#############################################
# Initialization & Main Loop                #
#############################################

# SAVE A GAME
def save_game():
    # open a new empty shelve (possibly overwriting an old one) to write the game data
    file = shelve.open('savegame', 'n')
    file['map'] = map
    file['objects'] = objects
    file['player_index'] = objects.index(player) # index of player in objects list. Shelve saves variable references recursively, meaning that
    # if you attempt file['player'] = player, then you'll get two player objects! This is because one instance is saved by file['objects'] = objects
    # and another by file['player'] = player. To avoid this, we simply save the index of the player in the list.
    file['inventory'] = inventory
    file['game_msgs'] = game_msgs
    file['game_state'] = game_state
    file['stairs_index'] = objects.index(stairs)
    file['dungeon_level'] = dungeon_level
    file.close()

# LOAD A SAVED GAME
def load_game():
    # open the previously saved shelve and load the game data
    global map, objects, player, inventory, game_msgs, game_state, stairs, dungeon_level

    file = shelve.open('savegame', 'r')
    map = file['map']
    objects = file['objects']
    player = objects[file['player_index']] # get index of player in objects list and access it
    inventory = file['inventory']
    game_msgs = file['game_msgs']
    game_state = file['game_state']
    stairs = objects[file['stairs_index']]
    dungeon_level = file['dungeon_level']
    file.close()

    initialize_fov()

# START A NEW GAME
def new_game():
    global player, inventory, game_msgs, game_state, dungeon_level, reticule, is_aiming_item, objects
    global HEAL_CANISTER_COLOR, STRENGTH_CANISTER_COLOR

    #create empty reticule object
    reticule = None

    # if aiming and this value is not None, then use this item as the object when aiming/firing
    is_aiming_item = False

    objects = []
    
    #create object representing the player
    fighter_component = Fighter(hp=10000, xp=0, accuracy=10, death_function=player_death, run_status="rested", run_duration=RUN_DURATION)
    player = Object(0, 0, '@', 'Player', libtcod.white, blocks=True, fighter=fighter_component, z=PLAYER_Z_VAL)

    player.level = 1
    
    # initialize dungeon level
    dungeon_level = 1

    # create the list of game messages and their colors, starts empty
    game_msgs = []

    # player inventory
    inventory = []

    # TODO: FINISH THIS
    # assign canister colors to canister types
    colors = ['Blue', 'Red']
    random.shuffle(colors)
    HEAL_CANISTER_COLOR = colors.pop()
    STRENGTH_CANISTER_COLOR = colors.pop()

    #generate map (at this point it's not drawn to the screen)
    make_map()

    # initialize fov map
    initialize_fov()

    # change game state to playing
    game_state = 'playing'

    # print a welcome message!
    message('Welcome to MurDur Corps. Make it out alive. Good luck.', libtcod.red)

    # TODO: DELETE THIS DEBUGGING/TESTING CODE
    equipment_component = create_pistol_equipment()
    obj = Object(0, 0, '}', 'Pistol', libtcod.gray, equipment=equipment_component, always_visible=True, z=ITEM_Z_VAL)
    inventory.append(obj)
    equipment_component.equip()

    # TODO: REMOVE THIS, TESTING
    #item_component = create_impact_grenade_item_component()
    #item = Object(0, 0, '#', 'Impact Grenade', libtcod.light_red, item=item_component, always_visible=True, z=ITEM_Z_VAL)
    #inventory.append(item)

    # TODO: REMOVE THIS, TESTING
    #item_component = create_emp_device_item_component()
    #item = Object(0, 0, '#', 'EMP Device', libtcod.light_yellow, item=item_component, always_visible=True, z=ITEM_Z_VAL)
    #inventory.append(item)

    # # initial equipment: a dagger
    #equipment_component = Equipment(slot='weapon', is_ranged=False, melee_power_bonus=DAGGER_DAMAGE)
    #obj = Object(0, 0, 'i', 'Dagger', libtcod.green, equipment=equipment_component, always_visible=True)
    #inventory.append(obj)
    #equipment_component.equip()

# advance to the next level
def next_level():
    global dungeon_level

    dungeon_level += 1
    message('You descend deeper into the facility...', libtcod.red)
    make_map() # create a new level!
    initialize_fov()

# INITIALIZE FOV MAP
def initialize_fov():
    global fov_recompute, fov_map
    fov_recompute = True

    #create the FOV map, according to the generated map
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)

    libtcod.console_clear(con) #unexplored areas start black (default background color)

# run the main game functions
def play_game():
    global key, mouse

    player_action = None

    while not libtcod.console_is_window_closed():
        # check for key/mouse input event
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
    
        #render the screen
        render_all()
    
        libtcod.console_flush()

        # check if player levels up
        check_level_up()
    
        #erase all objects at their old locations, before they move
        for object in objects:
            object.clear()
    
        #handle keys and exit game if needed
        player_action = handle_keys()
        if player_action == 'exit':
            # saves game automatically on exit
            save_game()
            break

        # let monsters take their turn
        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for object in objects:
                if object.ai:
                    object.ai.take_turn()

#############
# MAIN LOOP #
#############

def main_menu():
    img = libtcod.image_load('another_stolen_title.png')

    while not libtcod.console_is_window_closed():
        # show the background image, at twice the regular console resolution
        libtcod.image_blit_2x(img, 0, 0, 0)

        # show the game's title, and some credits
        libtcod.console_set_default_foreground(0, libtcod.gold)
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE, libtcod.CENTER, 'SaibaRobo: Cyberpunk Roguelike Action')
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-2, libtcod.BKGND_NONE, libtcod.CENTER, 'By Ninjalah')

        # show options and wait for the player's choice
        choice = menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)

        if choice == 0: #new game
            new_game()
            play_game()
        elif choice == 1: #load last game
            try:
                load_game()
            except:
                msgbox('\n No saved game to load.\n', 24)
                continue
            play_game()
        elif choice == 2: # quit
            break

libtcod.console_set_custom_font('dejavu_wide12x12_gs_tc.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
#libtcod.console_set_custom_font('dejavu_wide16x16_gs_tc.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
#libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)
libtcod.sys_set_fps(LIMIT_FPS)
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
log_panel = libtcod.console_new(MAP_WIDTH, LOG_HEIGHT)
hud_panel = libtcod.console_new(HUD_WIDTH, SCREEN_HEIGHT)

# set mouse/keyboard controls
mouse = libtcod.Mouse()
key = libtcod.Key()

# open the main menu
main_menu()