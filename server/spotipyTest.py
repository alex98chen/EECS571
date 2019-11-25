import spotipy
import spotipy.util as util
import sys

#http://mysite.com/callback/?code=AQDDsK8BHw1nfpJA-emPYB4sckNLbM-GwKZPjtVMLn0DOLw-mdJjcYc1RGGJVSIDt_ioVKr4YGdRbWQm6-15jEUj6QAzsiCg9USe9Xf8CIZvh6I0IJccrTIQ2o0Ub44L-0sI7k6TZNEUjKuVmF-Zi6Vujwvip2idHABp1eK6rgQ-I3Zpp2IN9pkXN_0-2zZauSlNv1an3uBhRpkQpvSHkB2GeCY

scope = 'user-library-read'

if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    print("Usage: %s username" % (sys.argv[0],))
    sys.exit()

token = util.prompt_for_user_token(username, scope)

if token:
    sp = spotipy.Spotify(auth=token)
    results = sp.current_user_saved_tracks()
    for item in results['items']:
        track = item['track']
        print(track['name'] + ' - ' + track['artists'][0]['name'])
else:
    print ("Can't get token for ", username)

