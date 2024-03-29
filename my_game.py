"""
Simple program to show moving a sprite with the keyboard.

This program uses the Arcade library found at http://arcade.academy

Artwork from https://kenney.nl/assets/space-shooter-redux
"""

import arcade
import arcade.gui
from math import sin, cos, pi, sqrt, inf
import random
from time import sleep
from typing import Tuple
from pyglet.math import Vec2
import requests
import simplejson
import yaml

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
PLAYER_SHOT_RANGE = max(SCREEN_HEIGHT, SCREEN_WIDTH) * 0.5
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
ASTEROIDS_MIN_SPAWN_DIST = 150
ASTEROIDS_MAX_SPLIT_ANGLE = 45
# the points you get for the smallest size (1) asteroids: less points for big asteroids.
ASTEROIDS_MAX_POINTS = 100

# API settings
with open("highscores_config.yml", "r") as f:
    config = yaml.safe_load(f)
    API_URL = config["api-url"]
    API_GAME_KEY = config["api-game-key"]
    API_ACCESS_TOKEN = config["api-access-token"]

# Play sound?
SOUND_ON = True

GAME_PAUSE_LENGTH_SECONDS = 2

FIRE_KEY = arcade.key.SPACE
MUTE_KEY = arcade.key.M

# Shake
SHAKE_AMPLITUDE = 12
SHAKE_SPEED = 1.5
SHAKE_DAMPING = 0.9

FONT_NAME = "Kenney Blocks"


def api_get_highscores(api_url, game_key, limit):
	"""
	Retrieves scores and returns a list of
	dictionaries with player names and scores
	"""

	r = requests.get(api_url + f"v1/games/{game_key}/scores")

	player_highscores = []

	for score in r.json()["_items"]:
	    # Check for errors before appending
	    player_highscores.append({
	        "player": requests.get(api_url + f"v1/players/{score['player_key']}").json()["name"],
	        "score": score["score"]
	    })

	return player_highscores

class Asteroid(arcade.Sprite):

    def __init__(self, size, player, center_x=None, center_y=None, angle=None):

        # If no position given, spawn at random position not on Player
        if center_x is None and center_y is None:
            # If asteroid position not legal, give new position
            while True:
                center_x = random.randint(0, SCREEN_WIDTH)
                center_y = random.randint(0, SCREEN_HEIGHT)
                if arcade.get_distance(center_x, center_y, player.center_x, player.center_y) > ASTEROIDS_MIN_SPAWN_DIST:
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

        # Making the player invisible
        self.alpha = 0

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

    def __init__(self, my_player,offset=8):
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
        # Calculate speeds base on angle
        self.change_x = PLAYER_SHOT_SPEED * cos(self.radians + pi / 2)
        self.change_y = PLAYER_SHOT_SPEED * sin(self.radians + pi / 2)

        self.distance_traveled = 0

        # Player shot spawns on the tip of the player instead of inside the player
        self.center_x += self.change_x * offset
        self.center_y += self.change_y * offset

    def update(self):
        """
        Move the sprite
        """

        # Update y position
        self.center_x += self.change_x
        self.center_y += self.change_y

        # Updates how far player shot moved.
        self.distance_traveled += arcade.get_distance(0, 0, self.change_x, self.change_y)


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
        self.camera_sprites = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera_GUI = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Variable that will hold a list of shots fired by the player
        self.player_shot_list = None
        self.asteroids_list = None
        self.UFO_list = None
        self.is_paused = False
        self.paused_time_left = inf
        self.level = 1

        # Variables for keeping track of accuracy
        self.shots_fired = 0
        self.shots_hit = 0
        self.shots_accuracy = 0

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

        for i in range(ASTEROIDS_PER_LEVEL):
            self.asteroids_list.append(Asteroid(ASTEROIDS_DEFAULT_SIZE, self.player_sprite))

        # Time between asteroid spawn
        self.asteroids_timer_seconds = ASTEROIDS_TIMER_SECONDS

        # UFO list
        self.UFO_list = arcade.SpriteList()
        self.UFO_spawn_timer = 0

        # Emitter list
        self.emitter_list = []
        
        # Player rocket emitter
        self.player_rocket_emitter = StoppableEmitter(self.player_sprite)
        # self.emitter_list.append(self.player_rocket_emitter.emitter)

        # Reset player position
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y

        # Player should not keep moving when reset
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        
        # Making the player visible again after death
        self.player_sprite.alpha = 255

        # Giving the player some random initial movement
        self.player_sprite.angle = arcade.rand_angle_360_deg()
        self.player_sprite.forward(1)

        # Compensating for wrong angle of the player graphic
        self.player_sprite.angle -= 90

        # Rocket should not emit particles under reset
        self.player_rocket_emitter.stop()

    def shake_cam(self,amplitude):
        random_dir = random.uniform(0, 2 * pi)
        sv = Vec2(amplitude * cos(random_dir), amplitude * sin(random_dir))
        self.camera_sprites.shake(sv, SHAKE_SPEED, SHAKE_DAMPING)

    def on_draw(self):
        """
        Render the screen.
        """

        # Use the camera
        self.camera_sprites.use()

        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw the player shot
        self.player_shot_list.draw()

        # Draw emitters
        for e in self.emitter_list:
            e.draw()

        # Draw player rocket
        self.player_rocket_emitter.emitter.draw()

        # Draw the player sprite
        self.player_sprite.draw()

        # Draw the asteriod(s)
        self.asteroids_list.draw()

        # Draw UFO
        self.UFO_list.draw()

        # Use the camera
        self.camera_GUI.use()

        # Draw mute icon
        if SOUND_ON is False:
            self.mute_icon.draw()
        else:
            self.unmute_icon.draw()


        # Draw players score on screen
        arcade.draw_text(
            f"SCORE: {self.player_sprite.score} +{round(self.player_sprite.score * self.shots_accuracy)}",  # Text to show
            5,  # X position
            SCREEN_HEIGHT - 20,  # Y position
            arcade.color.WHITE,  # Color of text
            font_name=FONT_NAME
        )

        # Draw player lives
        arcade.draw_text(
            "LIVES: {}".format(self.player_sprite.lives),  # text to show
            5,  # X position
            SCREEN_HEIGHT - 50,  # Y position
            arcade.color.WHITE,  # color of text
            font_name=FONT_NAME
        )

        # Draw player level
        arcade.draw_text(
            "LEVEL: {}".format(self.level),  # text to show
            5,  # X position
            SCREEN_HEIGHT - 80,  # Y position
            arcade.color.WHITE,  # color of text
            font_name = FONT_NAME
        )

        # Draw player accuracy
        arcade.draw_text(
            "ACCURACY: {}%".format(round(self.shots_accuracy * 100)),  # text to show
            5,  # X position
            SCREEN_HEIGHT - 110,  # Y position
            arcade.color.WHITE,  # color of text
            font_name = FONT_NAME
        )

    def game_over(self):
        #menu_view = GameOverView(self.player_sprite.score)
        menu_view = GameOverView()
        menu_view.setup_scores("MyUser", self.player_sprite.score + round(self.player_sprite.score * self.shots_accuracy))
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

    def get_explosion(self, pos_x, pos_y):

        new_emitter = arcade.make_burst_emitter(
            center_xy=[pos_x, pos_y],
            filenames_and_textures = [arcade.make_circle_texture(5, arcade.color.ORANGE)],
            particle_count=10,
            particle_speed=10,
            particle_lifetime_min=2,
            particle_lifetime_max=5)

        return new_emitter


    def on_update(self, delta_time):
        """
        Movement and game logic
        """

        # Emitters can not be paused
        for e in self.emitter_list:
            e.update()
        self.player_rocket_emitter.update()

        if self.is_paused:
            # Decrease time until pause ends
            self.paused_time_left -= delta_time

            # Unpause when timer reaches 0
            if self.paused_time_left <= 0:
                self.is_paused = False
                # Restart game if player is dead
                if self.player_sprite.lives < 1:
                    self.game_over()
                self.reset()

            # Skip on_update when game is paused
            return

        # Do player_shot and UFO collide?
        for s in self.player_shot_list:
            for u in s.collides_with_list(self.UFO_list):
                self.shots_fired += 1
                self.shots_hit += 1
                self.shots_accuracy = self.shots_hit / self.shots_fired
                self.player_sprite.score += u.value
                s.kill()
                u.kill()

        # Do UFO and player collide? If so remove a life
        for u in self.player_sprite.collides_with_list(self.UFO_list):
            u.kill()
            self.player_sprite.dies()
            self.emitter_list.append(self.get_explosion(self.player_sprite.center_x, self.player_sprite.center_y))
            self.shake_cam(SHAKE_AMPLITUDE)
            self.is_paused = True
            self.paused_time_left = GAME_PAUSE_LENGTH_SECONDS

            if self.player_sprite.lives < 1:
                self.game_over()

        # Asteroid hit by player_shot
        for s in self.player_shot_list:
            for a in s.collides_with_list(self.asteroids_list):
                self.shots_fired += 1
                self.shots_hit += 1
                self.shots_accuracy = self.shots_hit / self.shots_fired
                
                # Asteroids explosion
                self.emitter_list.append(self.get_explosion(a.center_x, a.center_y))
                
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
            self.emitter_list.append(self.get_explosion(self.player_sprite.center_x, self.player_sprite.center_y))
            self.shake_cam(SHAKE_AMPLITUDE)
            self.is_paused = True
            self.paused_time_left = GAME_PAUSE_LENGTH_SECONDS


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

        if self.up_pressed:
            self.player_sprite.player_thrust()
            self.player_rocket_emitter.start()

        # Update player sprite
        self.player_sprite.update()

        # Update the player shots
        self.player_shot_list.update()

        for s in self.player_shot_list:
            # Removes/kills player shot if it moves longer than the range
            if s.distance_traveled > PLAYER_SHOT_RANGE:
                self.shots_fired += 1
                self.shots_accuracy = self.shots_hit / self.shots_fired
                s.kill()

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

        if len(self.asteroids_list) == 0:
            self.reset()
            self.level += 1

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

        if button_no == 0:
            self.up_pressed = True

        # Press the fire key
        if button_no == 1:
            self.on_key_press(FIRE_KEY, [])

    def on_joybutton_release(self, joystick, button_no):
        print("Button released:", button_no)
        self.up_pressed = False


    def on_joyaxis_motion(self, joystick, axis, value):
        print("Joystick axis {}, value {}".format(axis, value))
        
        if axis == "x":
            if value == -1:
                self.left_pressed = True
            elif value == 1:
                self.right_pressed = True
            else:
                self.right_pressed = False
                self.left_pressed = False

    def on_joyhat_motion(self, joystick, hat_x, hat_y):
        print("Joystick hat ({}, {})".format(hat_x, hat_y))

class MenuView(arcade.View):

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        arcade.draw_text(
            "Start by pressing any key",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            arcade.color.WHITE,
            font_size=30,
            anchor_x="center",
            font_name=FONT_NAME
        )

    def on_key_press(self, key, _modifiers):
        game_view = GameView()
        self.window.show_view(game_view)

class GameOverView(arcade.View):
    
    def setup_scores(self, player_name, score):

        self.score = score

        try:
            with open("highscores.yml", "r") as f:
                self.highscores = yaml.safe_load(f)
            if self.highscores == None:
                self.highscores = []
            self.highscores.append({"player": player_name, "score": score})
            # Negating score when sorting so the largest score comes first
            self.highscores.sort(key=lambda highscores: -1 * highscores['score'])
            with open("highscores.yml", "w") as f:
                yaml.dump(self.highscores, f)
        except FileNotFoundError:
            # Hardcoded highscores that will be fetched from a file in the future
            # If file dosen't exist it creates a new one
            with open("highscores.yml", "w") as f:
                yaml.dump([{"player": player_name, "score": score}], f)
            self.highscores = [{"player": player_name, "score": score}]
        
        self.position = self.highscores.index({"player": player_name, "score": score})

            
    """
    # WORK IN PROGRESS
    # Retrieving highscores from api, else displaying local highscores
    try:
        highscores = api_get_highscores(API_URL, API_GAME_KEY, 10)

    except requests.exceptions.ConnectionError:
        print("Could not access api, using local highscores")

    except simplejson.errors.JSONDecodeError:
        print("Invalid json response, using local highscores")

    else:
        print("Using api highscores")
    """

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.UImanager = arcade.gui.UIManager()
        self.layout = arcade.gui.UIBoxLayout()
        self.UImanager.enable()

        for i, record in enumerate(self.highscores[:10]):
            
            # Highlight the new score in yellow
            if i == self.position:
                color = arcade.color.YELLOW
            else:
                color = arcade.color.WHITE

            text = arcade.gui.UILabel(
                width=400,
                text=f"{record['player']}: {record['score']}",
                text_color=color,
                font_name=FONT_NAME
            )

            self.layout.add(text.with_space_around(bottom=10))
        
        self.UImanager.add(
            arcade.gui.UIAnchorWidget(
            align_x=100,
            align_y=-20,
            child=self.layout
            )
        )
    
    def on_draw(self):
        self.clear()
        arcade.draw_text("GAME OVER!", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 50,
                         arcade.color.WHITE, 20, anchor_x="center", font_name=FONT_NAME)
        arcade.draw_text(f"Score: {self.score}  Position: #{self.position + 1}", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 110,
                         arcade.color.YELLOW, 14, anchor_x="center", font_name=FONT_NAME)
        self.UImanager.draw()

    def on_key_press(self, key, _modifiers):
        menu_view = MenuView()
        self.window.show_view(menu_view)

def main():
    """
    Main method
    """

    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT,
                           "☆〉Asteroids")
    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()

if __name__ == "__main__":
    main()
