import requests
import dotenv
import base64
import os
import json
from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy

# ------------------------------ This is the Spotify API data fetch portion of this project's backend code. ------------------------------
# Loading the contents of the .env file (the client information).
dotenv.load_dotenv()

# Obtaining the values of the variables saved in the .env environment.
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

# This function, as its name suggests, uses the proper endpoint (from Spotify's Dev Portal) to search for a specific artist and acquire data about their discography. 
def searchForArtist(token, artistName):
    # Obtained from Spotify Developer Portal in Web API page under the "Search" category. 
    searchEndpoint = "https://api.spotify.com/v1/search"
    headers = obtainAuthHeader(token)

    # A Python f string, as shown below, allows you to add variables, comma separators, put dates, etc. This variable query, uses the input parameter artistName to make a query to the web API of what artist's data you want to see. The format of the string is obviously a bit weird, but this is how queries are made (for instance, the argument "limit=1" quite literally limits your search down to the most popular artist, since there could be many artists with the same name).
    query = f"q={artistName}&type=artist&limit=1"
    queryURL = searchEndpoint + "?" + query

    # Using the get method from requests to obtain that artist's information, then parsing it into a json object. Here, the parts of the json object that we're looking for are the contents of "artists" and "items" (since the whole json object has many different pieces of information about the artists such as followers, etc). The reason being that if the length of the string returned is 0, then that artist does not exist. 
    result = requests.get(queryURL, headers=headers)
    jsonResult = json.loads(result.content)["artists"]["items"]

    if len(jsonResult) == 0:
        print("No artist with this name exists.")
        return None
    
    return jsonResult[0]

# Similar to the above function, this function uses the proper endpoint and an artist ID (endpoint retrieved from Spotify's Dev Portal) to obtain a specific artist's top songs. 
def artistTopSongs(token, ID):
    # Although this URL does need to have a specific country as an argument (the top streamed tracks in that specific country), because I'm providing an access token to get this data, the country that the user is in (which is me) will take over (hence the US). 
    topTracksEndpoint = f"https://api.spotify.com/v1/artists/{ID}/top-tracks"
    headers = obtainAuthHeader(token)
    result = requests.get(topTracksEndpoint, headers=headers)
    jsonResult = json.loads(result.content)["tracks"]
    return jsonResult

# This function, like the previous ones, uses the proper endpoint and an artist ID (endpoint retrieved from Spotify's Dev Portal) to find artists similar to the specified artist.
def artistAlbums(token, ID):
    relatedEndpoint = f"https://api.spotify.com/v1/artists/{ID}/albums"
    headers = obtainAuthHeader(token)
    result = requests.get(relatedEndpoint, headers=headers)
    jsonResult = json.loads(result.content)["items"]
    return jsonResult

# This function, like the previous ones, uses the proper endpoint and an album ID (endpoint retrieved from Spotify's Dev Portal) to obtain the tracks of a specific album that the artist created.
def artistAlbumTracks(token, ID):
    relatedEndpoint = f"https://api.spotify.com/v1/albums/{ID}"
    headers = obtainAuthHeader(token)
    result = requests.get(relatedEndpoint, headers=headers)
    jsonResult = json.loads(result.content)["tracks"]["items"]
    return jsonResult

# This function calls obtainToken to obviously obtain the token needed to authorize the data fetch. Then, using that token and the inputted var, searchForArtist is called. With that, the artist ID is obtained so that specific queries could be made in the future. Additionally, a new variable is initialized with the artist's followers as is value. Finally, artistID, accessToken, and artistFollowers are all returned.
def fetch(artistName):
    # Saving the token needed for the data fetch into a variable. The obtained access token and the input variable will be used as arguments for the searchForArtist() function so that the artist's ID could be obtained for the other functions.
    accessToken = obtainToken()
    searchResult = searchForArtist(accessToken, artistName)
    artistID = searchResult["id"]

    # Getting the followers of the inputted artist as a json object.
    artistFollowers = searchResult["followers"]["total"]

    return accessToken, artistID, artistFollowers

# This function, using its two input vars, searches for the artist and specifically obtains the genres they cover. Due to the fact that the returned value is a json object, the function then creates an empty list and populates it with each genre the artist covers.
def getGenres(accessToken, artistName):
    # First calling searchForArtists to get the json object containing the information about the artist.
    searchResult = searchForArtist(accessToken, artistName)

    # Getting the genres of the inputted artist as a json object.
    artistGenres = searchResult["genres"]

    # Creating a list that's the same length of the json object containing the genres of the inputted artist.
    genres = list(range(len(artistGenres)))

    # Populating genres.
    for idx, genre in enumerate(artistGenres):
        genres[idx] = f"{genre}"

    return genres

# This function, using its two input vars, searches for the artist and specifically obtains their top songs. Due to the fact that the returned value is a json object, the function creates an empty dictionary and populates each of its keys with the name of the song and each of its values with the song's popularity score and duration.
def getTopSongs(accessToken, artistID):
    # Getting the top songs of an artist as a json object. These songs also have tidbits of information including how long they are, their popularity, etc.
    songs = artistTopSongs(accessToken, artistID)

    # Creating an empty dictionary to populate the songs and their data (song length and popularity) into.
    topSongs = {}

    # Populating topSongs. The name of the songs will be the keys, while the song's length and popularity score will be the values. This for loop also makes sure to set the song's duration in seconds as an integer.
    for idx, song in enumerate(songs):
        songLength = (int(int(song["duration_ms"]) / 1000))

        # Getting the number of hours of the song's duration by dividing songLength by 3600 (since there are select few songs on Spotify that are hours long).
        songHours = int(songLength / 3600)

        # Getting the number of minutes of the song's duration by first finding the result of songLength modulus 3600, then dividing that remainder by 60.
        songMin = int((songLength % 3600) / 60)

        # Getting the number of seconds of the song's duration by first finding the result of songLength modulus 3600, then finding the result of that remainder modulus 60.
        songSec = int((songLength % 3600) % 60)

        songPopularity = song["popularity"]

        # This section of code takes care of each case of the song's duration if the song is hours long..
        if songHours > 0:
            if songMin < 10 and songSec >= 10:
                topSongs[f"{song["name"]}"] = f"{songHours}:0{songMin}:{songSec} hours | Popularity score: {songPopularity}"
            elif songMin >= 10 and songSec < 10:
                topSongs[f"{song["name"]}"] = f"{songHours}:{songMin}:0{songSec} hours | Popularity score: {songPopularity}"
            elif songMin < 10 and songSec < 10:
                topSongs[f"{song["name"]}"] = f"{songHours}:0{songMin}:0{songSec} hours | Popularity score: {songPopularity}"
            else:
                topSongs[f"{song["name"]}"] = f"{songHours}:{songMin}:{songSec} hours | Popularity score: {songPopularity}"
        # This section of code takes care of each case of the song's duration if the song is minutes long.
        elif songHours == 0 and songMin > 0:
            if songSec < 10:
                topSongs[f"{song["name"]}"] = f"{songMin}:0{songSec} minutes | Popularity score: {songPopularity}"
            else:
                topSongs[f"{song["name"]}"] = f"{songMin}:{songSec} minutes | Popularity score: {songPopularity}"
        # This section is intutitive, as the song's length can only be in seconds if this condition is met.
        elif songHours == 0 and songMin == 0:
            topSongs[f"{song["name"]}"] = f"{songSec} seconds | Popularity score: {songPopularity}"
        
    return topSongs

# This function, using its two input vars, searches for the artist and specifically obtains the albums that the artist has made. Due to the fact that the returned value is a json object, the function creates an empty dictionary and populates each key with the album's name and each value with information about the album.
def getAlbums(accessToken, artistID):
    # Calling the function above to obtain the json object of the albums the artist created.
    albums = artistAlbums(accessToken, artistID)

    # Creating an empty dictionary that will have the current album's name and info as the key, and a list of the album's tracks as the value.
    allAlbums = {}

    # Initializing the currentAlbumTracks as an empty list (as its name suggests, this list will be populated with each track and its duration for the current album). 
    currentAlbumTracks = []

    # Populating allAlbums using albums.
    for idx, album in enumerate(albums):
        # Obtaining the current album's ID, then calling artistAlbumTracks to a variable called albumTracks.
        albumID = album["id"]
        albumTracks = artistAlbumTracks(accessToken, albumID)

        # Populating currentAlbumTracks using albumTracks.
        for idx, track in enumerate(albumTracks):
            trackLength = int(int(track["duration_ms"]) / 1000)

            # Substituting the above code implemented earlier in getTopSongs to write out each track's length formally.
            trackHours = int(trackLength / 3600)
            trackMin = int((trackLength % 3600) / 60)
            trackSec = int((trackLength % 3600) % 60)

            if trackHours > 0:
                if trackMin < 10 and trackSec >= 10:
                    trackStr = f"{trackHours}:0{trackMin}:{trackSec} hours"
                elif trackMin >= 10 and trackSec < 10:
                    trackStr = f"{trackHours}:{trackMin}:0{trackSec} hours"
                elif trackMin < 10 and trackSec < 10:
                    trackStr = f"{trackHours}:0{trackMin}:0{trackSec} hours"
                else:
                    trackStr = f"{trackHours}:{trackMin}:{trackSec} hours"
            elif trackHours == 0 and trackMin > 0:
                if trackSec < 10:
                    trackStr = f"{trackMin}:0{trackSec} minutes"
                else:
                    trackStr = f"{trackMin}:{trackSec} minutes"
            elif trackHours == 0 and trackMin == 0:
                trackStr = f"{trackSec} seconds"

            currentAlbumTracks.append(f"{track["name"]} - {trackStr}")

        # Setting the current album's name, release date, total tracks, and type as the key, and currentAlbumTracks as the value in allAlbums.
        allAlbums[f"{album["name"]} - Released on: {album["release_date"]} | Total Tracks: {album["total_tracks"]} | Type: {album["album_type"]}"] = currentAlbumTracks

        # Resetting currentAlbumTracks for the next iteration.
        currentAlbumTracks = []

    return allAlbums

# ------------------------------ This is Flask portion of this project's backend code. ------------------------------
artistSearch = Flask(__name__)

# This piece of code should take in the user input and set it equal to the variable artistName. 
@artistSearch.route('/', methods=['POST', 'GET'])
def homepage():
    # Taking a look at the homepage.html file, there's a form tag in which the text input portion of the form has its name set to "artist". This is crucial because the data returned by request.form is a dictionary-like object, where the key in this case is 'artist' (the name of the text input portion of the form), and the value is the name that the user entered in the search bar. Here, request.form.get('artist', '') is used since we're directly accesing the value associated with the key 'artist' (if that key doesn't exist, then '', the default key, is used).
    # So with this if-statement, we're ensuring that the user inputted a valid artist name and pressed enter.
    if request.method == 'POST' and request.form.get('artist', ''):
        # Set validInput to true since a name was entered. 
        validInput = True
        
        # Retrieving the name that the user entered via the 'artist' key, since request.form is a dictionary-like object.
        artistName = request.form['artist']

        # Initializing three variables with the values returned by calling fetch. Then creating a string with artist followers as the value (so that it could be printed to the webpage).
        accessToken, artistID, artistFollowers = fetch(artistName)
        followers = f"{artistFollowers}"

        # Checking if the length of the followers string is 4 or more (meaning that the number will need to have commas).
        if len(followers) >= 4:
            # Finding the remainder of the number of digits in followers divided by 3 so that the number of leading digits before the first comma can be determined. 
            leadingDigits = len(followers) % 3
            if leadingDigits == 0:
                # Adding a comma after the first three leading digits.
                followers = followers[:3] + "," + followers[3:]

                # Since the comma was added after the first three leading digits, that means the starting index for the for loop to continue adding commas if the number is large enough is 4.
                start = 4
                
            elif leadingDigits == 2:
                # Adding a comma after the first two leading digits.
                followers = followers[:2] + "," + followers[2:]

                # Comma was added after the first 2 leading digits, so start should be 3.
                start = 3
            else:
                # Adding a comma after the first leading digit.
                followers = followers[:1] + "," + followers[1:]

                # Comma was added after the first leading digits, so start should be 2.
                start = 2
            
            # The (i - start) % 3 == 0 operation ensures that 3 more digits have been iterated through by the for loop and thus a comma will be needed (also ensure that i and start aren't the same number).
            for i in range(start, len(followers)):
                if (i - start) % 3 == 0 and i != start:
                    followers = followers[:i] + "," + followers[i:]
             
        # Calling the above functions related to obtaining the artist's top songs, albums, and genres and setting them equal to variables that will be used to populate the webpage. 
        topSongsDict = getTopSongs(accessToken, artistID)
        albumsDict = getAlbums(accessToken, artistID)
        genresList = getGenres(accessToken, artistName)
    
        # Here I'm returning the page with the values of followers, topSongs, albums, and genres as the strings/dictionaries/lists derived from the functions that fetched the data from the API.
        return render_template('homepage.html', validInput=validInput, followers=followers, topSongs=topSongsDict, albums=albumsDict, genres=genresList)
    
    # If the user pressed the button, but didn't enter an artist's name, then set followers, topSongsDict, albumsDict, and genresList as empty, cause obviously no information can be printed with no input. 
    elif request.method == 'POST':
        # Set validInput to false since no valid name was entered.
        validInput = False

        # Nothing can be printed, so keep the page empty. 
        return render_template('homepage.html', validInput=validInput, followers="", topSongs={}, albums=[], genres=[])
    
    else:
        # Set validInput to true since nothing was inputted, so there's no possible way the input could be invalid.
        validInput = True

        # Since this is the page that is returned when a user is not trying to search for an artist, the values for followers, topSongs, relArtists, and genres respectively are empty strings/dictionaries/lists (since there's no data to be returned here). These data structures need to be initialized for the page to run.
        return render_template('homepage.html', validInput=validInput, followers="", topSongs={}, albums=[], genres=[])
    
if __name__ == "__main__":
    artistSearch.run(debug=True)