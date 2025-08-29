# 📦 Built-in modules
import urllib.request
import urllib.parse
import time
import json
import os

# 📥 Custom modules
from Config import ApiVersion, ClientName, CoverArtSize, DefaultCoverUrl, UpdateInterval
from Utils.Logger import Logger
from Utils.RPC import RPC


# 🌱 Load environment variables from .env file
def LoadEnv():
    EnvDict = {}
    try:
        with open('.env', 'r') as File:
            for Line in File:
                if '=' in Line:
                    Key, Value = Line.strip().split('=', 1)
                    EnvDict[Key] = Value
        return EnvDict
    except FileNotFoundError:
        # 🔄 Fallback to process environment when .env is missing
        Keys = [
            'NAVIDROME_HOST',
            'NAVIDROME_USER',
            'NAVIDROME_PASSWORD',
            'DISCORD_USER_TOKEN',
            'DISCORD_BOT_APPLICATION_ID',
        ]
        for Key in Keys:
            Value = os.environ.get(Key)
            if Value:
                EnvDict[Key] = Value
        if not EnvDict:
            Logger.error('Error: .env file not found and no environment variables set.')
            return None
        return EnvDict


# 🌐 Fetch currently playing song from Navidrome
def GetCurrentSong():
	Env = LoadEnv()
	if not Env:
		return None

	Host = Env.get('NAVIDROME_HOST')
	User = Env.get('NAVIDROME_USER')
	Password = Env.get('NAVIDROME_PASSWORD')

	if not Host or not User or not Password:
		Logger.error('Error: Missing environment variables.')
		return None

	# 📡 Build the API URL for getNowPlaying
	Params = {'u': User, 'p': Password, 'v': ApiVersion, 'c': ClientName, 'f': 'json'}
	Query = urllib.parse.urlencode(Params)
	Url = f'{Host}/rest/getNowPlaying.view?{Query}'

	Logger.debug(f'API URL: {Url}')

	try:
		# 🔗 Make the request
		with urllib.request.urlopen(Url) as Response:
			Data = json.loads(Response.read().decode('utf-8'))

		# 📊 Parse the response
		SubsonicResponse = Data.get('subsonic-response', {})
		if SubsonicResponse.get('status') == 'ok':
			NowPlaying = SubsonicResponse.get('nowPlaying', {})
			Entries = NowPlaying.get('entry', [])
			if Entries:
				# ‼️ Assuming the first entry is the current song
				Song = Entries[0]
				Title = Song.get('title', 'Unknown')
				Artist = Song.get('artist', 'Unknown')
				Album = Song.get('album', 'Unknown')
				CoverArtId = Song.get('coverArt', None)
				Duration = Song.get('duration', 0)
				Logger.info(f'Currently playing: {Title} by {Artist} from {Album}')

				# 🎨 Build cover art URL for external asset processing
				CoverUrl = None
				if CoverArtId:
					CoverParams = {
						'u': User,
						'p': Password,
						'v': ApiVersion,
						'c': ClientName,
						'id': CoverArtId,
						'size': CoverArtSize,
					}
					CoverQuery = urllib.parse.urlencode(CoverParams)
					CoverUrl = f'{Host}/rest/getCoverArt.view?{CoverQuery}'
				return {
					'title': Title,
					'artist': Artist,
					'album': Album,
					'cover_url': CoverUrl,
					'duration': Duration,
				}
			else:
				Logger.info('No song currently playing.')
				return None
		else:
			Logger.error('Error: API response not ok.')
			return None
	except Exception as E:
		Logger.error(f'Error fetching data: {E}')
		return None


# 🚀 Main execution
if __name__ == '__main__':
	Env = LoadEnv()
	if not Env:
		exit()
	AppId = Env.get('DISCORD_BOT_APPLICATION_ID')
	Token = Env.get('DISCORD_USER_TOKEN')
	if not AppId or not Token:
		Logger.error('Error: Missing DISCORD_BOT_APPLICATION_ID or DISCORD_USER_TOKEN.')
		exit()

	Rpc = RPC(AppId, Token)
	Logger.info('Discord RPC initialized.')

	# 🕒 Keep stable timestamps for the current song (prevent resets)
	LastTrackKey = None
	StartMs = None
	EndMs = None
	WasPlaying = False

	try:
		while True:
			SongData = GetCurrentSong()
			if SongData:
				# 🔑 Identify the track (no unique ID in sample, so use tuple)
				TrackKey = f'{SongData["title"]}|{SongData["artist"]}|{SongData["album"]}|{SongData["duration"]}'
				if TrackKey != LastTrackKey:
					# ⏱️ Only set once when the track changes
					StartMs = int(time.time() * 1000)
					EndMs = (
						StartMs + (SongData['duration'] * 1000) if SongData['duration'] else None
					)
					LastTrackKey = TrackKey

					ActivityData = {
						'name': SongData['title'],
						'type': 2,  # 🎧 Listening
						'state': f'by {SongData["artist"]}',
						'details': SongData['album'],
						'assets': {
							'large_image': SongData['cover_url'] or DefaultCoverUrl,
							'large_text': SongData['album'],
						},
						'timestamps': {'start': StartMs, 'end': EndMs}
						if EndMs
						else {'start': StartMs},
					}
					Rpc.SendActivity(ActivityData)
					Logger.info('Discord rich presence updated.')
				else:
					# 🔁 Same track; do not resend or reset timestamps
					pass
				WasPlaying = True
			else:
				if WasPlaying:
					Rpc.ClearActivity()
					Logger.info('Discord rich presence cleared.')
				# 🔄 Reset state when nothing is playing
				LastTrackKey = None
				StartMs = None
				EndMs = None
				WasPlaying = False

			time.sleep(UpdateInterval)
	except KeyboardInterrupt:
		Rpc.ClearActivity()
		Rpc.Close()
		Logger.info('Exiting gracefully.')