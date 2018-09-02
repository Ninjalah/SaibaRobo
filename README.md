# SaibaRobo
Description: Cyberpunk Roguelike Action

**Current tutorial progress**: At "Dungeon levels and character progression": http://www.roguebasin.com/index.php?title=Complete_Roguelike_Tutorial,_using_python%2Blibtcod,_part_11

**Change pathfinding to allow monsters to walk diagonally/around other monsters**: http://www.roguebasin.com/index.php?title=Complete_Roguelike_Tutorial,_using_Python%2Blibtcod,_extras#A.2A_Pathfinding

**Package game into a single binary**: http://www.roguebasin.com/index.php?title=Complete_Roguelike_Tutorial,_using_Python%2Blibtcod,_extras#Creating_a_Binary

## Player
### Stats
* HP: Player's current health points. Reach 0, player dies.
* AP: Attack power. Increases the damage done by the player.
* DF: Defense. Decreases damage received by the player.

## Monsters
Cyborg: Normal cybernetically enhanced human. Low health, low defense, low attack power. The most common monster type.

Mecharachnid: A robotic spider-like machine. Medium health, medium defense, medium attack power. Relatively common.

Terminatron: A large, hulking robot that mercilessly pursues interlopers. Massive health, high defense, high attack power.

# Brainstorming

## Player
### Stats
* DX/CN: (Dexterity/Cunning) Determines player ability to make saving throws in dire situations (such as, mecharachnid grapple).
* IN/TC: (Intellect/Technical) Determines the success rate of certain technical rolls, such as success chance when jacking a fallen Cyborg's brain.

### Weapons
General section for weapons used by the player character (and some monsters).

* **Pistol**: Basic semi-automatic pistol. Does minimal damage, has average crit chance, uses bullets.

### Items
General section for items used by the player character (and some monsters).

* **Health pack**: Basic healing item, heals player for 10 points of HP.

* **Mechanic**: Allow items to be thrown in a straight line from the player to target tile. Can allow for interesting strategies:
  * **Health Pack**: Throw a health pack at a damaged (humanoid) enemy, the enemy attempts to pick up and use health pack (burning a few turns in the process), allowing Player to effectively "stun" the enemy at risk of taking too long, after which the enemy would use said Health Pack. Alternatively, enemy takes one turn to pick up Health Pack and one turn to use Health Pack, and it is up to the Player to "bait" the enemy by throwing the Health Pack far enough away from the enemy.
    * Does this mean that enemies need their own FoV?
  
  * **Battery Pack**: Idea for energy weapon ammo. If thrown, has a percentage chance of causing an explosion for moderate damage to a few tile radius around it.

* **Devices**: Akin to "spells" in more traditional roguelikes; have one-time usage unless otherwise specified.
    * **Detect Electrical Fields**: Detects electro-magnetic pulses, allowing the Player to see any robotic enemy through the fog-of-war. Lasts a certain duration.
    * **Detect Minds**: Detects brain activity, allowing the Player to see any humanoid enemy through the fog-of-war. Lasts a certain duration.
    * **Lightning**: Shoots a bolt of lightning from the Player to the *nearest enemy*. Does moderate damage.
    * **EMP**: Damages enemy circuits, causing a Confusion state for a duration.
    * **Impact Grenade**: A grenade that immediately explodes on impact, damaging all monsters (including the player) nearby.

* **Weapon Modifications**: Modify weapons to give certain specific advantages, etc.
  * **Flashlight**: Can be attached to any weapon, increases Player's FOV while wielding that weapon.

## Monsters
### Mechanics
* **Enemy dodging**: If an enemy is perceptive enough (perhaps this means non-robotic, or INT or some other stat is high enough, is a ranged enemy, etc.) makes an evasive action. The evasive action has a percentage chance to occur, and a percentage chance to succeed (perhaps based on player DEX or some other stat).

### Cyborg
* **AI**: Feels fear, and if critically damaged, runs away from the player (at a reduced speed to allow players to catch up with them). Runs away from player FoV, and if not seen, hides in hidable locations, such as lockers (this can be punctuated with a sound or console text, ex: "You hear the sound of a metal door closing!")

* **AI**: If damaged/low on ammo, can pick up health and/or ammo packs to use against the player. Only picks up ammo if out of ammo, only picks up health if in critical condition (while running away from player, for example).

* **Mechanic**: Cyborg brains are jackable, meaning the player can obtain information from fallen Cyborgs. This will reveal the location of items/monsters that the Cyborg knows about (has seen before?) through the fog-of-war. Also reveals some information about the Cyborg personally (remnants of human life, duration employed as a military cyborg, likes/dislikes, etc.).

### Robotic Enemies
* **AI**: Relentlessly pursue player until destruction.

### Mecharachnid
* **Combat**: Can only use melee.

* **AI/Mechanic**: Can jump onto ceilings if damaged enough. Will attempt to land on player after a certain # of turns. While walking on ceiling, is invisible/untargettable to player. (In lore, why would the player be unable to see the mecharachnid on the ceiling? Perhaps change char color to very light (still visible), but make accuracy against this monster incredibly reduced while ceiling-bound. Cannot attack while ceiling-bound (melee only)).
  * **If landing and misses player**: Nothing special happens, lands on ground and normal stats resume.
  * **If landing and lands on player**: Player makes a saving roll (based on DEX?). 
    * **If roll is successful**: Parry mecharachnid landing, putting mecharachnid next to player (grounded) and player takes minimal damage (perhaps none if DEX is high enough?). 
    * **If roll is unsuccessful**: then player falls and mecharachnid deals major damage. Mecharachnid ends up next to player afterwards. (Alternatively, have some "struggle" action available to the player, and loop the roll: If player successfully struggles, flip mecharachnid off. If unsuccessful, mecharachnid gets a hit in for free, and the loop restarts.
    
### Terminatron
* **Combat**: Can only use melee (pick up other weapons?)

* **AI**: The mission is to destroy the player and nothing else, and will relentlessly pursue. Breaks doors when moving through them while pursuing the player.

* **Combat/AI**: At 10% health, a servo motor connection is damaged, disabling the Terminatron's legs, arms, or head.
  * **If legs disabled**: Crawls after player using arms, has reduced speed.
  * **If arms disabled**: Charges after player in a straight line.
    * **If successful charge**: Hits player for massive damage, player is knocked back.
    * **If unsuccessful charge (hits wall before player)**: Is stunned for multiple turns, takes minor damage.
  * **If head disabled**: Charges after player's last known location
    * **If successful charge**: Hits player for massive damage, player is knocked back.
    * **If unsuccessful charge (hits wall before player)**: Is stunned for multiple turns, takes minor damage.
    * **After any charge**: Picks a random omnidirectional vector and charges again.
  * **If dies while charging**: Explodes, dealing damage to any player/monsters in near vicinity.

## Map & Dungeon Generation

### Mechanics
* **Windows**: Extends FoV from a wall into a room (using regular FOV calculation). If the player's FOV intersects with the FOV cast by the Window, the Player's FOV is extended by the Window's FOV, allowing the player to see further/more of a room.