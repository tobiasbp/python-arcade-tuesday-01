# Asteroids
We are building a clone of the classic arcade game [Asteroids](https://en.wikipedia.org/wiki/Asteroids_(video_game)) with Python and the [Arcade](https://api.arcade.academy) library. We are using [this video](https://youtu.be/_TKiRvGfw3Q) as reference.

If you live in Copenhagen (Denmark) and want to learn to code with us, go to [opfinderklubben.dk](https://www.opfinderklubben.dk/programmering-for-born/). 

# Setup virtual environment

* python3 -mvenv .venv
* source .venv/bin/activate
* pip3 install -r requirements.txt

To use highscores you must create a highscores_config.yml


Example of a valid 'highscores_config.yml'
```
# URL to api
api-url: "https://myapi.example.org/"

# Key of the game inside of the api's database
api-game-key: "MyGameKey"

# Secret token required to post to the database
api-access-token: "MySecretToken"
```
