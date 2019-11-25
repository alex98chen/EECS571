import spotipy
import spotipy.util as util
import sys
from spotipy.oauth2 import SpotifyClientCredentials

#http://mysite.com/callback/?code=AQDDsK8BHw1nfpJA-emPYB4sckNLbM-GwKZPjtVMLn0DOLw-mdJjcYc1RGGJVSIDt_ioVKr4YGdRbWQm6-15jEUj6QAzsiCg9USe9Xf8CIZvh6I0IJccrTIQ2o0Ub44L-0sI7k6TZNEUjKuVmF-Zi6Vujwvip2idHABp1eK6rgQ-I3Zpp2IN9pkXN_0-2zZauSlNv1an3uBhRpkQpvSHkB2GeCY

client_id = '685a1af809f94ac881016d869898d0fa'
client_secret = '20fd967fac724a9d80307f622fa43618'
uri = 'http://mysite.com/callback/'

scope = 'user-library-read playlist-modify-private user-read-currently-playing user-read-playback-state streaming'

if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    print("Usage: %s username" % (sys.argv[0],))
    sys.exit()

client_credentials_manager = SpotifyClientCredentials()


token = util.prompt_for_user_token(username, scope, client_id = client_id, client_secret = client_secret, redirect_uri = uri)

def getDevice(sp):
    devs = sp.devices()
    print(devs)
    #print(devs['devices'][0]['id'])
    for device in devs['devices']:
        if device['type'] == 'Smartphone':
            return device['id']
    return ''



if token:
    sp = spotipy.Spotify(auth=token, client_credentials_manager = client_credentials_manager)
    #devs = sp.devices()
    #print(devs)
    #print(devs['devices'][0]['id'])
    #device_id = devs['devices'][0]['id']
    device_id = getDevice(sp)
    if device_id == '':
        print('no smartphone device')
    else:
        uriArr = {"uris" : ["spotify:track:6wVbHLCBOCqp6052WcWXLG"]} 
        sp.start_playback(device_id = device_id, context_uri = None, uris = uriArr['uris'], offset = None) 


else:
    print ("Can't get token for ", username)

