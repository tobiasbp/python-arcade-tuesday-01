"""
Simple program to show moving a sprite with the keyboard.

This program uses the Arcade library found at http://arcade.academy

Artwork from https://kenney.nl/assets/space-shooter-redux

"""

import arcade
from math import sin, cos, pi

SPRITE_SCALING = 0.5
BACKGROUND_COLOR = arcade.color.BLACK 

# Set the size of the screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Variables controlling the player
PLAYER_LIVES = 3
PLAYER_THRUST = 0.2
PLAYER_START_X = SCREEN_WIDTH / 2
PLAYER_START_Y = 50
PLAYER_SHOT_SPEED = 4
PLAYER_ROTATE_SPEED = 5


FIRE_KEY = arcade.key.SPACE

class Asteroid(arcade.Sprite):

    def __init__(self):
        super().__init__(
            center_x=SCREEN_WIDTH/2,
            center_y=SCREEN_HEIGHT/2,
            filename="images/Meteors/meteorBrown_big1.png",
        )

        self.change_x = -0.5
        self.change_y = -0.5


class Player(arcade.Sprite):
    """
    The player
    """

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

    def __init__(self, center_x, center_y, angle):
        """
        Setup new PlayerShot object
        """

        # Set the graphics to use for the sprite
        super().__init__("images/Lasers/laserBlue01.png", SPRITE_SCALING)

        self.angle = angle
        self.center_x = center_x
        self.center_y = center_y
        self.change_x = PLAYER_SHOT_SPEED * cos(self.radians + pi/2)
        self.change_y = PLAYER_SHOT_SPEED * sin(self.radians + pi/2)

    def update(self):
        """
        Move the sprite
        """

        # Update y position
        self.center_x += self.change_x
        self.center_y += self.change_y

        # Remove shot when over top of screen
        if self.bottom > SCREEN_HEIGHT:
            self.kill()


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self, width, height):
        """
        Initializer
        """

        # Call the parent class initializer
        super().__init__(width, height)

        # Variable that will hold a list of shots fired by the player
        self.player_shot_list = None

        self.asteroids_list = None

        # Set up the player info
        self.player_sprite = None
        self.player_score = None
        self.player_lives = None

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


            #self.joystick.
        # Set the background color
        arcade.set_background_color(BACKGROUND_COLOR)

    def setup(self):
        """ Set up the game and initialize the variables. """

        # No points when the game starts
        self.player_score = 0

        # No of lives
        self.player_lives = PLAYER_LIVES

        # Sprite lists
        self.player_shot_list = arcade.SpriteList()

        # Asteroid list
        self.asteroids_list = arcade.SpriteList()

        self.asteroids_list.append(Asteroid())

        # Create a Player object
        self.player_sprite = Player(
            center_x=PLAYER_START_X,
            center_y=PLAYER_START_Y
        )

    def on_draw(self):
        """
        Render the screen.
        """

        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw the player shot
        self.player_shot_list.draw()

        # Draw the player sprite
        self.player_sprite.draw()

        # Draw the asteriod(s)
        self.asteroids_list.draw()

        # Draw players score on screen
        arcade.draw_text(
            "SCORE: {}".format(self.player_score),  # Text to show
            10,                  # X position
            SCREEN_HEIGHT - 20,  # Y position
            arcade.color.WHITE   # Color of text
        )

        # Draw player lifes
        arcade.draw_text(
            "LIVES: {}".format(self.player_lives ),  # text to show
            10,                  # X position
            SCREEN_HEIGHT - 50,  # Y position
            arcade.color.WHITE    # color of text
        )


    def screen_wrap(self, list_to_wrap):
        """
        Object wraps around screen
        """

        for p in list_to_wrap:
            if p.right < 0:
                p.left = SCREEN_WIDTH
            elif p.left > SCREEN_WIDTH:
                p.right = 0

            if p.top < 0:
                p.bottom = SCREEN_HEIGHT
            elif p.bottom > SCREEN_HEIGHT:
                p.top = 0

    def on_update(self, delta_time):
        """
        Movement and game logic
        """

        # Calculate player speed based on the keys pressed
        #self.player_sprite.change_x = 0

        # Move player with keyboard
        if self.left_pressed and not self.right_pressed:
            self.player_sprite.angle += PLAYER_ROTATE_SPEED
        elif self.right_pressed and not self.left_pressed:
            self.player_sprite.angle -= PLAYER_ROTATE_SPEED

        # Player rocket engine
        if self.up_pressed:
            # rotate player graphics to match direction
            self.player_sprite.change_x += PLAYER_THRUST * cos(self.player_sprite.radians + pi/2)
            self.player_sprite.change_y += PLAYER_THRUST * sin(self.player_sprite.radians + pi/2)
        

        # Move player with joystick if present
        #if self.joystick:
        #    self.player_sprite.change_x = round(self.joystick.x) * PLAYER_SPEED

        # Update player sprite
        self.player_sprite.update()

        # Update the player shots
        self.player_shot_list.update()

        # Update the asteroids
        self.asteroids_list.update()

        # Asteroids wraps
        self.screen_wrap(self.asteroids_list)

        # Player wraps
        self.screen_wrap([self.player_sprite])


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
                self.player_sprite.center_x,
                self.player_sprite.center_y,
                self.player_sprite.angle
            )

            self.player_shot_list.append(new_shot)

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

def main():
    """
    Main method
    """

    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
