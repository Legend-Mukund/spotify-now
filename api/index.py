import spotipy
from pathlib import Path
from spotipy import util
import re, base64, requests, random, os
from flask import Flask, Response, render_template, request

cwd = Path.cwd()
cwd = re.sub(r"\\", r"/", str(cwd))
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
scope = "user-read-playback-state user-read-recently-played"
redirect_uri = "http://127.0.0.1:5000/spotify"

app = Flask(__name__)
try:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": os.environ["REFRESH_TOKEN"],
    }

    res = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": os.environ["REFRESH_TOKEN"],
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )
    token = res.json()["access_token"]
except:
    token = util.prompt_for_user_token(
        "", scope, CLIENT_ID, CLIENT_SECRET, redirect_uri, cache_path=f"token.json"
    )
sp = spotipy.Spotify(auth=token)


def spotify():
    try:
        current = sp.current_playback()
        songname = current["item"]["name"]
        artist = current["item"]["artists"][0]["name"]
        cover = current["item"]["album"]["images"][0]["url"]
        return ["Now Playing", songname, cover, artist]
    except:
        current = sp.current_user_recently_played(limit=1)
        songname = current["items"][0]["track"]["name"]
        artist = current["items"][0]["track"]["artists"][0]["name"]
        cover = current["items"][0]["track"]["album"]["images"][0]["url"]
        return ["last played", songname, cover, artist]


@app.route("/")
def home():
    return "UwU"

@app.route("/health")
def health():
    return "OK", 200

@app.route("/spotify")
def spotify():
    code = request.args.get("code")
    if code:
        res = requests.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            }
        )
        with open("token.json", "w") as f:
            f.write(res.text)
        return "Authorization successful! You can close this window."
    else:
        info = spotify()
        songname = info[1].replace("&", "&amp;")
        artist = info[3].replace("&", "&amp;")
        response = requests.get(info[2])
        imgstr = base64.b64encode(response.content).decode()
        bars = ""
        for i in range(0, 32):
            bars += f'<div class="bar" style="animation-delay: {random.randint(500,800)}ms; animation-duration: {random.randint(800,1000)}ms"></div>'
        data = {
            "status": info[0],
            "songname": songname,
            "artist": artist,
            "imgstr": imgstr,
            "bars": bars,
        }
        aight = render_template("card.html.j2", **data)
        resp = Response(aight, mimetype="image/svg+xml")
        resp.headers["Cache-Control"] = "public, max-age=0, must-revalidate"
        return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
