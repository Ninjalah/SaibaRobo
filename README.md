# SaibaRobo
Description: Cyberpunk Roguelike Action

## Monsters
Cyborg: Normal cybernetically enhanced human. Low health, low defense, low attack power. The most common monster type.

Mecharachnid: A robotic spider-like machine. Medium health, medium defense, medium attack power. Relatively common.

Terminatron: A large, hulking robot that mercilessly pursues interlopers. Massive health, high defense, high attack power.

# Brainstorming

## Monsters
Cyborg
* **AI**: Feels fear, and if damaged enough, runs away from the player (at a reduced speed to allow players to catch up with them). Runs away from player FoV, and if not seen, hides in hidable locations (this can be punctuated with a sound or console text, ex: "You hear the sound of a metal door closing!"

* **Mechanic**: Cyborg brains are jackable, meaning the player can obtain information from fallen Cyborgs. This will reveal the location of items/monsters that the Cyborg knows about (has seen before?)

Robotic Enemies
* **Mechanic**: Relentlessly pursue player until destruction.

Mecharachnids
* **Combat**: Can only use melee.

* **AI**: Can jump onto ceilings if damaged enough. Will attempt to land on player after a certain # of turns. While walking on ceiling, is invisible/untargettable to player. (In lore, why would the player be unable to see the mecharachnid on the ceiling? Perhaps change char color to very light (still visible), but make accuracy against this monster incredibly reduced while ceiling-bound. Cannot attack while ceiling-bound (melee only).
  * **If landing and misses player**: Nothing special happens, lands on ground and normal stats resume.
  * **If landing and lands on player**: Player makes a saving roll (based on DEX?). 
    * **If roll is successful**: Parry mecharachnid landing, putting mecharachnid next to player (grounded) and player takes minimal damage (perhaps none if DEX is high enough?). 
    * **If roll is unsuccessful**: then player falls and mecharachnid deals major damage. Mecharachnid ends up next to player afterwards. (Alternatively, have some "struggle" action available to the player, and loop the roll: If player successfully struggles, flip mecharachnid off. If unsuccessful, mecharachnid gets a hit in for free, and the loop restarts.
