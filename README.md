# SaibaRobo
Description: Cyberpunk Roguelike Action

## Monsters
Cyborg: Normal cybernetically enhanced human. Low health, low defense, low attack power. The most common monster type.

Mecharachnid: A robotic spider-like machine. Medium health, medium defense, medium attack power. Relatively common.

Terminatron: A large, hulking robot that mercilessly pursues interlopers. Massive health, high defense, high attack power.

# Brainstorming

## Monsters
Cyborg
* **AI**: Feels fear, and if critically damaged, runs away from the player (at a reduced speed to allow players to catch up with them). Runs away from player FoV, and if not seen, hides in hidable locations, such as lockers (this can be punctuated with a sound or console text, ex: "You hear the sound of a metal door closing!"

* **AI**: If damaged/low on ammo, can pick up health and/or ammo packs to use against the player. Only picks up ammo if out of ammo, only picks up health if in critical condition (while running away from player, for example).

* **Mechanic**: Cyborg brains are jackable, meaning the player can obtain information from fallen Cyborgs. This will reveal the location of items/monsters that the Cyborg knows about (has seen before?). Also reveals some information about the Cyborg personally (remnants of human life, duration employed as a military cyborg, likes/dislikes, etc.).

Robotic Enemies
* **AI**: Relentlessly pursue player until destruction.

Mecharachnid
* **Combat**: Can only use melee.

* **AI/Mechanic**: Can jump onto ceilings if damaged enough. Will attempt to land on player after a certain # of turns. While walking on ceiling, is invisible/untargettable to player. (In lore, why would the player be unable to see the mecharachnid on the ceiling? Perhaps change char color to very light (still visible), but make accuracy against this monster incredibly reduced while ceiling-bound. Cannot attack while ceiling-bound (melee only).
  * **If landing and misses player**: Nothing special happens, lands on ground and normal stats resume.
  * **If landing and lands on player**: Player makes a saving roll (based on DEX?). 
    * **If roll is successful**: Parry mecharachnid landing, putting mecharachnid next to player (grounded) and player takes minimal damage (perhaps none if DEX is high enough?). 
    * **If roll is unsuccessful**: then player falls and mecharachnid deals major damage. Mecharachnid ends up next to player afterwards. (Alternatively, have some "struggle" action available to the player, and loop the roll: If player successfully struggles, flip mecharachnid off. If unsuccessful, mecharachnid gets a hit in for free, and the loop restarts.
    
Terminatron
* **Combat**: Can only use melee (pick up other weapons?)

* **AI**: The mission is to destroy the player and nothing else, and will relentlessly pursue. Breaks doors when moving through them.

* **Combat/AI**: At 10% health, a servo motor connection is damaged, disabling the Terminatron's legs, arms, or head.
  * **If legs disabled**: Crawls after player using arms, has reduced speed.
  * **If arms disabled**: Charges after player in a straight line.
    * **If successful charge**: Hits player for massive damage, player is knocked back.
    * **If unsuccessful charge (hits wall before player)**: Is stunned for multiple turns, takes minor damage.
  * **If head disabled**: Charges after player's last known location
    * **If successful charge**: Hits player for massive damage, player is knocked back.
    * **If unsuccessful charge (hits wall before player)**: Is stunned for multiple turns, takes minor damage.
    * **After any charge**: Picks a random omnidirectional vector and charges again.
