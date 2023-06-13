import requests


api_url = "https://highscoredb-1-q4331561.deta.app/"
game_key = "g2y9a6nl0lbb"


def get_highscores(api_url, game_key, limit):

	r = requests.get(api_url + f"v1/games/{game_key}/scores")

	player_highscores = []
	
	for score in r.json()["_items"]:
	    # Check for errors before appending
	    player_highscores.append({
	        "player": requests.get(api_url + f"v1/players/{score['player_key']}").json()["name"],
	        "score": score["score"]
	    })
	
	return player_highscores


print(get_highscores(api_url, game_key, 10))
