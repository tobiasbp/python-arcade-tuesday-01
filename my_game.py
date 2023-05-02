"""
Simple program to show moving a sprite with the keyboard.

This program uses the Arcade library found at http://arcade.academy

Artwork from https://kenney.nl/assets/space-shooter-redux

"""

import arcade
from math import sin, cos, pi, sqrt, inf
import random
from time import sleep
from typing import Tuple

SPRITE_SCALING = 0.5
BACKGROUND_COLOR = arcade.color.BLACK

# Set the size of the screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Variables controlling the player
PLAYER_LIVES = 3
PLAYER_THRUST = 0.2
PLAYER_START_X = SCREEN_WIDTH / 2
PLAYER_START_Y = SCREEN_HEIGHT / 2
PLAYER_SHOT_SPEED = 4
PLAYER_SHOT_RANGE = max(SCREEN_HEIGHT, SCREEN_WIDTH) * 1
PLAYER_ROTATE_SPEED = 5
PLAYER_MAX_SPEED = 7

# Configure UFOs
UFO_CHANGE_DIR_TIME_MAX = 10
UFO_CHANGE_DIR_TIME_MIN = 2
UFO_SPAWN_TIME_MAX = 35
UFO_SPAWN_TIME_MIN = 80

# Configure asteroids
ASTEROIDS_TIMER_SECONDS = inf  # inf == spawn all asteroids at the same time
ASTEROIDS_SPEED = 1
ASTEROIDS_PER_LEVEL = 5
ASTEROIDS_DEFAULT_SIZE = 4
ASTEROIDS_SCALE = 0.4
ASTEROIDS_MIN_DIST = 50
ASTEROIDS_MAX_SPLIT_ANGLE = 45
# the points you get for the smallest size (1) asteroids: less points for big asteroids.
ASTEROIDS_MAX_POINTS = 100
ASTEROIDS_MIN_DIST = 10

# Play sound?
SOUND_ON = True

GAME_PAUSE_LENGTH_SECONDS = 2

FIRE_KEY = arcade.key.SPACE
MUTE_KEY = arcade.key.M


class Asteroid(arcade.Sprite):

    def __init__(self, size, player, center_x = None, center_y = None, angle = None):
        
        if center_x is None and center_y is None:
        
            while True:
            
                center_x = random.randint(0, SCREEN_WIDTH)
                center_y = random.randint(0, SCREEN_HEIGHT)

                if arcade.get_distance(center_x, center_y, player.center_x, player.center_y) > ASTEROIDS_MIN_DIST:
                    break

        self.size = size

        super().__init__(
            center_x = center_x,
            center_y = center_y,
            filename="images/Meteors/meteorBrown_big1.png",
            scale= SPRITE_SCALING * ASTEROIDS_SCALE * self.size 
        )
        
        if angle is None:
            self.angle = random.randint(1, 360)
        else:
            self.angle = angle

        self.forward(ASTEROIDS_SPEED)
        self.change_angle = random.uniform(-1, 1)
        
    def on_update(self, delta_time: float = 1 / 60):
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.angle += self.change_angle

class BonusUFO(arcade.Sprite):
    # when the UFO wraps it says a sound
    try:
        sound_wraps = arcade.load_sound("sounds/forcefield_004.ogg")
    except FileNotFoundError:
        print("Could not load sound: sounds/forcefield_004.ogg")
        sound_wraps = None

    def __init__(self):
        super().__init__(
            # center_x=SCREEN_WIDTH/2,
            center_y=SCREEN_HEIGHT / 2,
            filename="images/ufoGreen.png"
        )
        self.ufo_spawn = 0
        self.speed = 1.0
        self.dir_timer = random.uniform(UFO_CHANGE_DIR_TIME_MIN, UFO_CHANGE_DIR_TIME_MAX)
        self.scale, self.value = random.choice(
            [(1 * SPRITE_SCALING, 100), (2 * SPRITE_SCALING, 200)]
        )

        self.where_to_spawn = random.randint(1, 4)

        if self.where_to_spawn == 1:
            # Right. When spawning to the left it wraps right.
            self.center_x = SCREEN_WIDTH + self.width
            self.center_y = random.randint(0, SCREEN_HEIGHT)
        elif self.where_to_spawn == 2:
            # Left. When spawning to the right it wraps left.
            self.center_x = - 1 * self.width
            self.center_y = random.randint(0, SCREEN_HEIGHT)
        elif self.where_to_spawn == 3:
            # Top. When spawning to at the bottom it wraps to the top.
            self.center_x = random.randint(0, SCREEN_WIDTH)
            self.center_y = SCREEN_HEIGHT + self.height
        else:
            # Bottom. When spawning to at the top it wraps to the bottom.
            self.center_x = random.randint(0, SCREEN_WIDTH)
            self.center_y = -1 * self.height

        self.change_dir()

    def change_dir(self):

        self.angle = arcade.rand_angle_360_deg()

        # Calculate speed based on angle.
        self.change_x = self.speed * cos(self.radians)
        self.change_y = self.speed * sin(self.radians)

    def on_update(self, delta_time):

        # Moves sprite
        self.center_x += self.change_x
        self.center_y += self.change_y

        # Time passes
        self.dir_timer -= delta_time

        # No more time, change direction
        if self.dir_timer < 0:
            self.change_dir()
            self.dir_timer = random.uniform(UFO_CHANGE_DIR_TIME_MIN, UFO_CHANGE_DIR_TIME_MAX)
            # print(self.dir_timer)


class Player(arcade.Sprite):
    """
    The player
    """
    try:
        sound_dies = arcade.load_sound("sounds/explosionCrunch_000.ogg")
    except FileNotFoundError:
        sound_dies = None

    def __init__(self, **kwargs):
        """
        Setup new Player object
        """

        # Graphics to use for Player
        kwargs['filename'] = "images/playerShip2_red.png"

        # How much to scale the graphics
        kwargs['scale'] = SPRITE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)
        self.score = 0
        self.lives = PLAYER_LIVES

    def dies(self):
        """
        Return True if player has no more lives, otherwise return False
        """

        self.lives -= 1

        global SOUND_ON

        if SOUND_ON is True:
            if Player.sound_dies is not None:
                Player.sound_dies.play()

        if self.lives < 1:
            return True
        else:
            return False

    def player_thrust(self):
        self.change_x += PLAYER_THRUST * cos(self.radians + pi / 2)
        self.change_y += PLAYER_THRUST * sin(self.radians + pi / 2)

        speed = sqrt(self.change_x ** 2 + self.change_y ** 2)

        if speed > PLAYER_MAX_SPEED:
            self.change_x /= speed / PLAYER_MAX_SPEED
            self.change_y /= speed / PLAYER_MAX_SPEED

    def update(self):
        """
        Move the sprite
        """
        # Update center_x
        self.center_x += self.change_x

        # Update center_y
        self.center_y += self.change_y


class PlayerShot(arcade.Sprite):
    """
    A shot fired by the Player
    """
    try:
        sound_fire = arcade.load_sound("sounds/laserlarge_000.mp3")
    except FileNotFoundError:
        print("Could not load sound: sounds/laserlarge_000.mp3")
        sound_fire = None

    def __init__(self, my_player):
        """
        Setup new PlayerShot object
        """
        global SOUND_ON
        if SOUND_ON is True:
            if PlayerShot.sound_fire is not None:
                PlayerShot.sound_fire.play()

        # Set the graphics to use for the sprite
        super().__init__("images/Lasers/laserBlue01.png", SPRITE_SCALING)

        self.angle = my_player.angle
        self.center_x = my_player.center_x
        self.center_y = my_player.center_y
        self.change_x = PLAYER_SHOT_SPEED * cos(self.radians + pi / 2)
        self.change_y = PLAYER_SHOT_SPEED * sin(self.radians + pi / 2)
        self.distance_traveled = 0

    def update(self):
        """
        Move the sprite
        """

        # Update y position
        self.center_x += self.change_x
        self.center_y += self.change_y

        # Updates how far player shot moved.
        self.distance_traveled += arcade.get_distance(0, 0, self.change_x, self.change_y)

        # Removes/kills player shot if it moves longer than the range
        if self.distance_traveled > PLAYER_SHOT_RANGE:
            self.kill()


class StoppableEmitter():
    """
    It is possible to start and stop this emitter
    """
    def __init__(self,
            target: arcade.Sprite,
            particle_lifetime: float = 0.5,
            noise: int = 15,
            offset: Tuple[int] = (0, 6),
            emit_interval: float = 0.01,
            particle_count: int = 30,
            start_alpa: int = 100):

        self.target = target
        self.noise = noise
        self.emit_interval = emit_interval
        self.particle_count = particle_count

        # Emit controller enters endless loop with an interval of 0
        assert self.emit_interval > 0, "Emit interval must be greater than 0"

        # An emitter with a controller which does not have particles to emit (it's off)
        self.emitter = arcade.Emitter(
            center_xy=target.position,
            emit_controller = arcade.EmitterIntervalWithCount(self.emit_interval,0),
            particle_factory=lambda emitter: arcade.FadeParticle(
                filename_or_texture = arcade.make_circle_texture(random.randint(7, 30), arcade.color.CYAN),
                change_xy=offset,
                lifetime=particle_lifetime,
                start_alpha=start_alpa
            )
        )

    def start(self):
        """
        Start emitter
        """
        self.emitter.rate_factory = arcade.EmitterIntervalWithCount(self.emit_interval, self.particle_count)

    def stop(self):
        """
        Stop emitter
        """
        self.emitter.rate_factory = arcade.EmitterIntervalWithCount(self.emit_interval,0)

    def update(self):
        self.emitter.center_x, self.emitter.center_y = self.target.position
        self.emitter.angle = (self.target.angle + 180) + random.randint(-1 * self.noise, self.noise)
        self.emitter.update()


class GameView(arcade.View):
    """
    Main application class.
    """

    def on_show_view(self):

        """
        Initializer
        """

        # Variable that will hold a list of shots fired by the player
        self.player_shot_list = None
        self.asteroids_list = None
        self.UFO_list = None
        self.is_paused = False
        self.paused_time_left = inf

        # Set up the player info
        self.player_sprite = None

        self.player_sprite = Player()

        # Define player_rocket_emitter
        self.player_rocket_emitter = StoppableEmitter(self.player_sprite)

        self.mute_icon = arcade.Sprite(
            filename="images/Icons/audioOff.png",
            center_y=SCREEN_HEIGHT-SCREEN_HEIGHT/10,
            center_x=SCREEN_WIDTH-SCREEN_WIDTH/15
        )

        self.unmute_icon = arcade.Sprite(
            filename="images/Icons/audioOn.png",
            center_y=SCREEN_HEIGHT-SCREEN_HEIGHT/10,
            center_x=SCREEN_WIDTH-SCREEN_WIDTH/15
        )


        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        # Get list of joysticks
        joysticks = arcade.get_joysticks()

        if joysticks:
            print("Found {} joystick(s)".format(len(joysticks)))

            # Use 1st joystick found
            self.joystick = joysticks[0]

            # Communicate with joystick
            self.joystick.open()

            # Map joysticks functions to local functions
            self.joystick.on_joybutton_press = self.on_joybutton_press
            self.joystick.on_joybutton_release = self.on_joybutton_release
            self.joystick.on_joyaxis_motion = self.on_joyaxis_motion
            self.joystick.on_joyhat_motion = self.on_joyhat_motion

        else:
            print("No joysticks found")
            self.joystick = None

            # self.joystick.
        # Set the background color
        arcade.set_background_color(BACKGROUND_COLOR)
        self.reset()

    def reset(self):
        """ Set up the game and initialize the variables. """

        # Sprite lists
        self.player_shot_list = arcade.SpriteList()

        # Asteroid list
        self.asteroids_list = arcade.SpriteList()

        # Create a Player object
        self.player_sprite = Player(
            center_x=PLAYER_START_X,
            center_y=PLAYER_START_Y
        )

        for i in range(ASTEROIDS_PER_LEVEL):
            self.asteroids_list.append(Asteroid(ASTEROIDS_DEFAULT_SIZE, self.player_sprite))

        # Time between asteroid spawn
        self.asteroids_timer_seconds = ASTEROIDS_TIMER_SECONDS

        # UFO list
        self.UFO_list = arcade.SpriteList()
        self.UFO_spawn_timer = 0

        # Player rocket emitter
        self.player_rocket_emitter = StoppableEmitter(self.player_sprite)
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y

        # Player should not keep moving when reset
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        
        # Rocket should not emit particles under reset
        self.player_rocket_emitter.stop()

    def on_draw(self):
        """
        Render the screen.
        """

        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw the player shot
        self.player_shot_list.draw()

        # Draw player rocket
        self.player_rocket_emitter.emitter.draw()

        # Draw the player sprite
        self.player_sprite.draw()

        # Draw the asteriod(s)
        self.asteroids_list.draw()

        # Draw UFO
        self.UFO_list.draw()

        # Draw mute icon
        if SOUND_ON is False:
            self.mute_icon.draw()
        else:
            self.unmute_icon.draw()


        # Draw players score on screen
        arcade.draw_text(
            "SCORE: {}".format(self.player_sprite.score),  # Text to show
            10,  # X position
            SCREEN_HEIGHT - 20,  # Y position
            arcade.color.WHITE  # Color of text
        )

        # Draw player lives
        arcade.draw_text(
            "LIVES: {}".format(self.player_sprite.lives),  # text to show
            10,  # X position
            SCREEN_HEIGHT - 50,  # Y position
            arcade.color.WHITE  # color of text
        )

    def game_over(self):
        menu_view = GameOverView()
        self.window.show_view(menu_view)

    def screen_wrap(self, list_to_wrap):
        """
        Object wraps around screen.
        returns True if something wraps else False
        """
        some_thing_wrapped = False

        for p in list_to_wrap:
            # wrap on x axis
            if p.right < 0:
                p.left = SCREEN_WIDTH
                some_thing_wrapped = True
            elif p.left > SCREEN_WIDTH:
                p.right = 0
                some_thing_wrapped = True
            # wrap on y axis
            if p.top < 0:
                p.bottom = SCREEN_HEIGHT
                some_thing_wrapped = True
            elif p.bottom > SCREEN_HEIGHT:
                p.top = 0
                some_thing_wrapped = True

        return some_thing_wrapped

    def on_update(self, delta_time):
        """
        Movement and game logic
        """

        if self.is_paused:
            # Decrease time until pause ends
            self.paused_time_left -= delta_time

            # Unpause when timer reaches 0
            if self.paused_time_left <= 0:
                self.is_paused = False
                self.reset()

            # Skip on_update when game is paused
            return

        # Do player_shot and UFO collide?
        for s in self.player_shot_list:
            for u in s.collides_with_list(self.UFO_list):
                self.player_sprite.score += u.value
                s.kill()
                u.kill()

        # Do UFO and player collide? If so remove a life
        for u in self.player_sprite.collides_with_list(self.UFO_list):
            u.kill()
            self.player_sprite.dies()
            self.is_paused = True
            self.paused_time_left = GAME_PAUSE_LENGTH_SECONDS

            if self.player_sprite.lives < 1:
                self.game_over()
        
        # Asteroid hit by player_shot
        for s in self.player_shot_list:
            for a in s.collides_with_list(self.asteroids_list):

                # split off two asteroids going left or right
                for direction in [-1, 1]:
                    # only split if size is bigger than one
                    if a.size > 1:
                        # + 90 to s.angle because the angle is changed to match the graphic
                        new_angle = (s.angle + 90) + (direction * random.randint(0, ASTEROIDS_MAX_SPLIT_ANGLE))
                        self.asteroids_list.append(
                            Asteroid(a.size-1, self.player_sprite, a.center_x, a.center_y, new_angle)
                        )
                        # Big asteroids gives less points
                    self.player_sprite.score += ASTEROIDS_MAX_POINTS//a.size
                s.kill()
                a.kill()

        # Kill asteroids who collide with player and make player loose a life
        for a in self.player_sprite.collides_with_list(self.asteroids_list):
            a.kill()
            self.player_sprite.dies()
            self.is_paused = True
            self.paused_time_left = GAME_PAUSE_LENGTH_SECONDS

            # Restart game if player is dead
            if self.player_sprite.lives < 1:
                self.game_over()


        # Subtract time from UFO_spawn_timer
        self.UFO_spawn_timer -= delta_time

        if self.UFO_spawn_timer <= 0:
            self.UFO_spawn_timer = random.randint(UFO_CHANGE_DIR_TIME_MIN, UFO_SPAWN_TIME_MAX)
            self.UFO_list.append(BonusUFO())

        # Move player with keyboard
        if self.left_pressed and not self.right_pressed:
            self.player_sprite.angle += PLAYER_ROTATE_SPEED
        elif self.right_pressed and not self.left_pressed:
            self.player_sprite.angle -= PLAYER_ROTATE_SPEED


        self.player_rocket_emitter.update()

        if self.up_pressed:
            self.player_sprite.player_thrust()
            self.player_rocket_emitter.start()

        # Move player with joystick if present
        # if self.joystick:
        #    self.player_sprite.change_x = round(self.joystick.x) * PLAYER_SPEED

        # Update player sprite
        self.player_sprite.update()

        # Update the player shots
        self.player_shot_list.update()

        # Time between asteroid spawn count down
        self.asteroids_timer_seconds -= delta_time

        # Make new asteroid if the right amount of time has passed
        if self.asteroids_timer_seconds <= 0:
            self.asteroids_list.append(Asteroid(ASTEROIDS_DEFAULT_SIZE, self.player_sprite))
            self.asteroids_timer_seconds = ASTEROIDS_TIMER_SECONDS

        # Update the asteroids
        self.asteroids_list.on_update(delta_time)

        # Update the UFOs
        self.UFO_list.on_update(delta_time)

        # Asteroids wraps
        self.screen_wrap(self.asteroids_list)

        # Player wraps
        self.screen_wrap([self.player_sprite])

        # Shot wraps
        self.screen_wrap(self.player_shot_list)

        # UFO wraps
        a_ufo_wrapped = self.screen_wrap(self.UFO_list)
        if a_ufo_wrapped == True and SOUND_ON:
            BonusUFO.sound_wraps.play()

        if SOUND_ON is True:
            if a_ufo_wrapped and BonusUFO.sound_wraps is not None:
                BonusUFO.sound_wraps.play()

    def on_key_press(self, key, modifiers):
        """
        Called whenever a key is pressed.
        """

        # Track state of arrow keys
        if key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.DOWN:
            self.down_pressed = True
        elif key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True

        if key == FIRE_KEY:
            new_shot = PlayerShot(
                self.player_sprite
            )

            self.player_shot_list.append(new_shot)

        global SOUND_ON
        if key == MUTE_KEY:
            SOUND_ON = not SOUND_ON

    def on_key_release(self, key, modifiers):
        """
        Called whenever a key is released.
        """

        if key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False
        elif key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False

    def on_joybutton_press(self, joystick, button_no):
        print("Button pressed:", button_no)
        # Press the fire key
        self.on_key_press(FIRE_KEY, [])

    def on_joybutton_release(self, joystick, button_no):
        print("Button released:", button_no)

    def on_joyaxis_motion(self, joystick, axis, value):
        print("Joystick axis {}, value {}".format(axis, value))

    def on_joyhat_motion(self, joystick, hat_x, hat_y):
        print("Joystick hat ({}, {})".format(hat_x, hat_y))

class MenuView(arcade.View):

    def on_show_view(self):
        arcade.set_background_color(arcade.color.PINK)

    def on_draw(self):
        self.clear()
        arcade.draw_text(
            "omg start the game by clicking any key",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            arcade.color.WHITE,
            font_size=30,
            anchor_x="center"
        )

    def on_key_press(self, key, _modifiers):
        game_view = GameView()
        self.window.show_view(game_view)

class GameOverView(arcade.View):
    def on_show_view(self):
        arcade.set_background_color(arcade.color.PASTEL_PURPLE)

    def on_draw(self):
        self.clear()
        arcade.draw_text("GAME OVER! u lost losr, click any key to start over", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                         arcade.color.LEMON, 20, anchor_x="center")

    def on_key_press(self, key, _modifiers):
        menu_view = MenuView()
        self.window.show_view(menu_view)

def main():
    """
    Main method
    """

    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT,
                           "Kære dagbog, i dag har jeg fri fra jobsamtale. Jeg er megeti godt humør,fornøjet,frejdig,frimodig,fro,henrykt,lykkelig og salig.")
    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()

if __name__ == "__main__":
    main()