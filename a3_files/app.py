"""
Simple 2d world where the player can interact with the items in the world.
"""
from tkinter import filedialog

__author__ = "aryaman sharma"
__date__ = ""
__version__ = "1.1.0"
__copyright__ = "The University of Queensland, 2019"

import math
import tkinter as tk

from typing import Tuple, List

import pymunk

from game.block import Block, MysteryBlock
from game.entity import Entity, BoundaryWall
from game.mob import Mob, CloudMob, Fireball
from game.item import DroppedItem, Coin
from game.view import GameView, ViewRenderer
from game.world import World

from level import load_world, WorldBuilder
from player import Player

BLOCK_SIZE = 2 ** 4
MAX_WINDOW_SIZE = (1080, math.inf)

GOAL_SIZES = {
    "flag": (0.2, 9),
    "tunnel": (2, 2)
}

BLOCKS = {
    '#': 'brick',
    '%': 'brick_base',
    '?': 'mystery_empty',
    '$': 'mystery_coin',
    '^': 'cube'
}

ITEMS = {
    'C': 'coin'
}

MOBS = {
    '&': "cloud"
}


def create_block(world: World, block_id: str, x: int, y: int, *args):
    """Create a new block instance and add it to the world based on the block_id.

    Parameters:
        world (World): The world where the block should be added to.
        block_id (str): The block identifier of the block to create.
        x (int): The x coordinate of the block.
        y (int): The y coordinate of the block.
    """
    block_id = BLOCKS[block_id]
    if block_id == "mystery_empty":
        block = MysteryBlock()
    elif block_id == "mystery_coin":
        block = MysteryBlock(drop="coin", drop_range=(3, 6))
    else:
        block = Block(block_id)

    world.add_block(block, x * BLOCK_SIZE, y * BLOCK_SIZE)


def create_item(world: World, item_id: str, x: int, y: int, *args):
    """Create a new item instance and add it to the world based on the item_id.

    Parameters:
        world (World): The world where the item should be added to.
        item_id (str): The item identifier of the item to create.
        x (int): The x coordinate of the item.
        y (int): The y coordinate of the item.
    """
    item_id = ITEMS[item_id]
    if item_id == "coin":
        item = Coin()
    else:
        item = DroppedItem(item_id)

    world.add_item(item, x * BLOCK_SIZE, y * BLOCK_SIZE)


def create_mob(world: World, mob_id: str, x: int, y: int, *args):
    """Create a new mob instance and add it to the world based on the mob_id.

    Parameters:
        world (World): The world where the mob should be added to.
        mob_id (str): The mob identifier of the mob to create.
        x (int): The x coordinate of the mob.
        y (int): The y coordinate of the mob.
    """
    mob_id = MOBS[mob_id]
    if mob_id == "cloud":
        mob = CloudMob()
    elif mob_id == "fireball":
        mob = Fireball()
    else:
        mob = Mob(mob_id, size=(1, 1))

    world.add_mob(mob, x * BLOCK_SIZE, y * BLOCK_SIZE)


def create_unknown(world: World, entity_id: str, x: int, y: int, *args):
    """Create an unknown entity."""
    world.add_thing(Entity(), x * BLOCK_SIZE, y * BLOCK_SIZE,
                    size=(BLOCK_SIZE, BLOCK_SIZE))


BLOCK_IMAGES = {
    "brick": "brick",
    "brick_base": "brick_base",
    "cube": "cube"
}

ITEM_IMAGES = {
    "coin": "coin_item"
}

MOB_IMAGES = {
    "cloud": "floaty",
    "fireball": "fireball_down"
}


class MarioViewRenderer(ViewRenderer):
    """A customised view renderer for a game of mario."""

    @ViewRenderer.draw.register(Player)
    def _draw_player(self, instance: Player, shape: pymunk.Shape,
                     view: tk.Canvas, offset: Tuple[int, int]) -> List[int]:

        if shape.body.velocity.x >= 0:
            image = self.load_image("mario_right")
        else:
            image = self.load_image("mario_left")

        return [view.create_image(shape.bb.center().x + offset[0], shape.bb.center().y,
                                  image=image, tags="player")]

    @ViewRenderer.draw.register(MysteryBlock)
    def _draw_mystery_block(self, instance: MysteryBlock, shape: pymunk.Shape,
                            view: tk.Canvas, offset: Tuple[int, int]) -> List[int]:
        if instance.is_active():
            image = self.load_image("coin")
        else:
            image = self.load_image("coin_used")

        return [view.create_image(shape.bb.center().x + offset[0], shape.bb.center().y,
                                  image=image, tags="block")]


class MarioApp:
    """High-level app class for Mario, a 2d platformer"""

    _world: World

    def __init__(self, master: tk.Tk):
        """Construct a new game of a MarioApp game.

        Parameters:
            master (tk.Tk): tkinter root widget
        """
        self._master = master
        self._master.title("Mario bird")

        world_builder = WorldBuilder(BLOCK_SIZE, gravity=(0, 300), fallback=create_unknown)
        world_builder.register_builders(BLOCKS.keys(), create_block)
        world_builder.register_builders(ITEMS.keys(), create_item)
        world_builder.register_builders(MOBS.keys(), create_mob)
        self._builder = world_builder

        self._player = Player(max_health=5)
        self.reset_world('level1.txt')
        self._level_holder = 'level1.txt'

        self._renderer = MarioViewRenderer(BLOCK_IMAGES, ITEM_IMAGES, MOB_IMAGES)

        size = tuple(map(min, zip(MAX_WINDOW_SIZE, self._world.get_pixel_size())))
        self._view = GameView(master, size, self._renderer)
        self._view.pack()
        self.bind()
        self.menubar()

        # Wait for window to update before continuing
        master.update_idletasks()
        self.step()
        self._death_action = False

    def reset_world(self, new_level):
        self._world = load_world(self._builder, new_level)
        self._world.add_player(self._player, BLOCK_SIZE, BLOCK_SIZE)
        self._builder.clear()
        self._setup_collision_handlers()
        self._level_holder = new_level


        self._death_action = False
        self._player.change_health(self._player.get_max_health())

    def menubar(self):
        """Creates a menu bar in GUI interface with options:
                Load level: prompts user to select level to load
                Reset level: Resets current level
                Exit: exits game
        """
        menubar = tk.Menu(self._master)
        self._master.config(menu=menubar)
        filemenu = tk.Menu(menubar)
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="LOAD LEVEL", command=self.load_level_menu)
        filemenu.add_command(label="RESET LEVEL", command=lambda: self.reset_world(self._level_holder))
        filemenu.add_command(label="EXIT", command=self.exit_game)

    def load_level_menu(self):
        """Pop-up window with 3 buttons
            Level1: loads level1
            level2: loads level2
        """
        popup = tk.Tk()
        popup.title("Level select")
        label1 = tk.Label(popup, text="Choose a level")
        label1.pack(side='top')
        level1_button = tk.Button(popup, text="Level1", command=lambda: [self.reset_world('level1.txt'),popup.destroy()])
        level2_button = tk.Button(popup, text="level2", command=lambda: [self.reset_world('level2.txt'),popup.destroy()])
        level1_button.pack(side='left', expand=True)
        level2_button.pack(side='right', expand=True)

    def exit_game(self):
        self._master.destroy()

    def bind(self):
        """Bind all the keyboard events to their event handlers."""
        # jump
        self._master.bind('<Up>', lambda event: self._jump())
        self._master.bind('<space>', lambda event: self._jump())
        self._master.bind('<w>', lambda event: self._jump())
        self._master.bind('<W>', lambda event: self._jump())
        # move left
        self._master.bind('<a>', lambda event: self._move(-50, 0))
        self._master.bind('<Left>', lambda event: self._move(-500, 0))
        self._master.bind('<A>', lambda event: self._move(-500, 0))
        # duck
        self._master.bind('<s>', lambda event: self._duck())
        self._master.bind('<Down>', lambda event: self._duck())
        self._master.bind('<S>', lambda event: self._duck())
        # move right
        self._master.bind('<d>', lambda event: self._move(50, 0))
        self._master.bind('<Right>', lambda event: self._move(500, 0))
        self._master.bind('<D>', lambda event: self._move(500, 0))

    def redraw(self):
        """Redraw all the entities in the game canvas."""
        self._view.delete(tk.ALL)

        self._view.draw_entities(self._world.get_all_things())

    def scroll(self):
        """Scroll the view along with the player in the center unless
        they are near the left or right boundaries
        """
        x_position = self._player.get_position()[0]
        half_screen = self._master.winfo_width() / 2
        world_size = self._world.get_pixel_size()[0] - half_screen

        # Left side
        if x_position <= half_screen:
            self._view.set_offset((0, 0))

        # Between left and right sides
        elif half_screen <= x_position <= world_size:
            self._view.set_offset((half_screen - x_position, 0))

        # Right side
        elif x_position >= world_size:
            self._view.set_offset((half_screen - world_size, 0))

    def step(self):
        """Step the world physics and redraw the canvas."""
        data = (self._world, self._player)
        self._world.step(data)
        self.scroll()
        self.redraw()
        self._master.after(10, self.step)

        #Asking if players want to continue playing or end the game
        if self._player.get_health() == 0:
            if not self._death_action:
                self.on_death()
            else:
                pass

    def on_death(self):
        """
        A popup window asking if player wants to continue or exit
        """
        self._death_action = True
        death_popup = tk.Tk()
        death_popup.geometry("300x200")
        death_popup.configure(background="light blue")
        death_popup.title("You dead")
        label1 = tk.Label(death_popup, text="What next??")
        label1.pack(side='top')
        restart_button = tk.Button(death_popup, text="Restart", command=lambda: [self.reset_world('level1.txt'), death_popup.destroy()])
        end_button = tk.Button(death_popup, text='end', command=lambda: [self.exit_game(), death_popup.destroy()])
        restart_button.pack(side='left', expand=True)
        end_button.pack(side='right', expand=True)



    def _move(self, dx, dy):
        self._player.set_velocity((dx, dy))

    def _jump(self):
        self._player.set_velocity((0, -150))

    def _duck(self):
        # to be used later as if duck == True
        return True

    def _setup_collision_handlers(self):
        self._world.add_collision_handler("player", "item", on_begin=self._handle_player_collide_item)
        self._world.add_collision_handler("player", "block", on_begin=self._handle_player_collide_block,
                                          on_separate=self._handle_player_separate_block)
        self._world.add_collision_handler("player", "mob", on_begin=self._handle_player_collide_mob)
        self._world.add_collision_handler("mob", "block", on_begin=self._handle_mob_collide_block)
        self._world.add_collision_handler("mob", "mob", on_begin=self._handle_mob_collide_mob)
        self._world.add_collision_handler("mob", "item", on_begin=self._handle_mob_collide_item)

    def _handle_mob_collide_block(self, mob: Mob, block: Block, data,
                                  arbiter: pymunk.Arbiter) -> bool:
        if mob.get_id() == "fireball":
            if block.get_id() == "brick":
                self._world.remove_block(block)
            self._world.remove_mob(mob)
        return True

    def _handle_mob_collide_item(self, mob: Mob, block: Block, data,
                                 arbiter: pymunk.Arbiter) -> bool:
        return False

    def _handle_mob_collide_mob(self, mob1: Mob, mob2: Mob, data,
                                arbiter: pymunk.Arbiter) -> bool:
        if mob1.get_id() == "fireball" or mob2.get_id() == "fireball":
            self._world.remove_mob(mob1)
            self._world.remove_mob(mob2)

        return False

    def _handle_player_collide_item(self, player: Player, dropped_item: DroppedItem,
                                    data, arbiter: pymunk.Arbiter) -> bool:
        """Callback to handle collision between the player and a (dropped) item. If the player has sufficient space in
        their to pick up the item, the item will be removed from the game world.

        Parameters:
            player (Player): The player that was involved in the collision
            dropped_item (DroppedItem): The (dropped) item that the player collided with
            data (dict): data that was added with this collision handler (see data parameter in
                         World.add_collision_handler)
            arbiter (pymunk.Arbiter): Data about a collision
                                      (see http://www.pymunk.org/en/latest/pymunk.html#pymunk.Arbiter)
                                      NOTE: you probably won't need this
        Return:
             bool: False (always ignore this type of collision)
                   (more generally, collision callbacks return True iff the collision should be considered valid; i.e.
                   returning False makes the world ignore the collision)
        """

        dropped_item.collect(self._player)
        self._world.remove_item(dropped_item)
        return False

    def _handle_player_collide_block(self, player: Player, block: Block, data,
                                     arbiter: pymunk.Arbiter) -> bool:

        block.on_hit(arbiter, (self._world, player))
        return True

    def _handle_player_collide_mob(self, player: Player, mob: Mob, data,
                                   arbiter: pymunk.Arbiter) -> bool:
        mob.on_hit(arbiter, (self._world, player))
        return True

    def _handle_player_separate_block(self, player: Player, block: Block, data,
                                      arbiter: pymunk.Arbiter) -> bool:
        return True


def main():
    root = tk.Tk()
    app_run = MarioApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
