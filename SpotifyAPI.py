# The requests module will be used to fetch the data from the Spotify Web API since it has the HTTP methods needed and the dotenv module (alongside with the os module) will be used to access the environment variables located in the .env file (the client ID and secret). The base64 module will come in handy whenever trying to encode or decode binary data to and from plain text.
import requests
import dotenv
import base64
import os
import json

# Loading the contents of the .env file (the client information).
dotenv.load_dotenv()

clientID = os.getenv("CLIENT_ID")
clientSecret = os.getenv("CLIENT_SECRET")

# Defining the function that will be used to obtain a new token from Spotify to access its web API (this is a necessary authorization process).
def obtainToken():
    # The authString variable is a string of both the CLIENT_ID and CLIENT_SECRET variables since the client information will be needed to authorize fetching data from the Spotify web API. The authBytes variable encodes the string created earlier via UTF-8 into bytes (AKA a binary string). The authBase64 variable takes the binary data from authBytes and encodes it into base64.
    authString = clientID + ":" + clientSecret   # The colon is necessary.
    authBytes = authString.encode("utf-8")
    authBase64 = str(base64.b64encode(authBytes), "utf-8")

    # The variable url is just the url that will be used to access the token. The variable headers uses authBase64 and ensures that the web API knows what type of authorization I'm seeking. The variable data ensures that the web API knows I'm specifically requesting a token via my client credentials. All three of these variables will later be used as arguments for a post call to obtain the token. 
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + authBase64, 
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    # Obtaining the token through the post method from requests, then converting it into a json object, and then initializing a variable that stores the value belonging to the "access_token" key in the json object.
    result = requests.post(url, headers=headers, data=data)
    jsonResult = json.loads(result.content)
    token = jsonResult["access_token"]
    return token

# This function will be used in future functions that will make queries (queries need headers).
def obtainAuthHeader(token):
    return {"Authorization": "Bearer " + token}

def artistSearch(token, artistName):
    # Obtained from Spotify Developer Portal in Web API page under the "Search" category. 
    searchEndpoint = "https://api.spotify.com/v1/search"
    headers = obtainAuthHeader(token)

    # A python f string, as show below, allows you to add variables, comma separators, put dates, etc. This variable query, uses the input parameter artistName to make a query to the web API of what artist's data you want to see. The format of the string is obviously a bit weird, but this is how queries are made (for instance, the argument "limit=1" quite literally limits your search down to the most popular artist, since there could be many artists with the same name).
    query = f"q={artistName}&type=artist&limit=1"
    queryURL = searchEndpoint + "?" + query
    # Using the get method from requests to obtain that artist's information, then parsing it into a json object. Here, the parts of the JSON object that we're looking for are the contents of "artists" and "items" (since the whole json object has many different pieces of information about the artists such as followers, etc). The reason being that if the length of the string returned is 0, then that artist does not exist. 
    result = requests.get(queryURL, headers=headers)
    jsonResult = json.loads(result.content)["artists"]["items"]

    if len(jsonResult) == 0:
        print("No artist with this name exists.")
        return None
    
    return jsonResult[0]

# This function, as it name suggests, uses the proper endpoint and an artist ID (from Spotify's Dev Portal) to obtain a specific artist's top songs. 
def artistTopSongs(token, ID):
    # Although this URL does need to have a specific country as an argument (the top streamed tracks in that specific country), because I'm providing an access token to get this data, the country that the user is in (which is me) will take over (hence the US). 
    topTracksEndpoint = f"https://api.spotify.com/v1/artists/{ID}/top-tracks"
    headers = obtainAuthHeader(token)
    result = requests.get(topTracksEndpoint, headers=headers)
    jsonResult = json.loads(result.content)["tracks"]
    return jsonResult

# Similar to the above function, this function uses the proper endpoint and an artist ID (from Spotify's Dev Portal) to find artists similar to the specified artist.
def relatedArtists(token, ID):
    relatedEndpoint = f"https://api.spotify.com/v1/artists/{ID}/related-artists"
    headers = obtainAuthHeader(token)
    result = requests.get(relatedEndpoint, headers=headers)
    jsonResult = json.loads(result.content)["artists"]
    return jsonResult

# Prompting the user to input their favorite artist's name and saving it as a String var. This var along with the obtained access token will be used as arguments for the searchArtist() function so that the artist's ID could be obtained for the other functions.
accessToken = obtainToken()
name = input("Enter your favorite artist's name: ")
searchResult = artistSearch(accessToken, name)
artistID = searchResult["id"]

# Getting the followers/genres of the inputted artist, and then printing it out to the console using a for loop.
artistFollowers = searchResult["followers"]["total"]
artistGenres = searchResult["genres"]
print(f"{searchResult["name"]} currently has {artistFollowers} followers. They cover genres such as: ")
for genre in artistGenres:
    print(f"{genre}")
print()

# This json object contains lots of tidbits of information about the tracks, so in order to make the returned string a bit more readable, the following code will do so:
songs = artistTopSongs(accessToken, artistID)

# In this for loop, we are taking the returned json object of songs and enumerating it (make it iterable by giving each track an index). The idx variable gives an index for each top track of the artist. So, the most popular track from that artist in the US will be number 0 (hence why in the print statement idx is incremented by 1). Each song json object from songs has keys such as "popularity_score" and "duration_ms", so printing out the respective values of those keys to the console as well.
print(f"Here are some of {searchResult["name"]}'s top tracks: ")
for idx, song in enumerate(songs):
    songLength = int(int(song["duration_ms"]) / 1000)
    songPopularity = song["popularity"]
    print(f"{idx + 1}. {song["name"]}: {songLength} seconds | Popularity score: {songPopularity}")
print()

# Calling the function above to obtain the json object of artists that are similar to the input artist then printing those artists to the console via a for loop.
similarArtists = relatedArtists(accessToken, artistID)
print(f"Here are some similar artists: ")
for idx, artist in enumerate(similarArtists):
    print(f"{artist["name"]}")