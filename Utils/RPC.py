# 📦 Built-in modules
import urllib.request
import threading
import logging
import time
import json

# 📥 Custom modules
from Config import DefaultCoverUrl, UserAgent
import websocket

# 📴 Disable verbose websocket-client trace logs (prevents duplicate "Websocket connected" line)
websocket.enableTrace(False)


# 💡 Custom Discord RPC class for WebSocket communication
class RPC:
	def __init__(self, AppId, Token):
		self.AppId = AppId
		self.Token = Token
		self.Ws = None
		self.Seq = None
		self.Running = True
		self.Identified = False
		self.HeartbeatInterval = 41.25
		self.AssetCache = {}  # url -> 'mp:...' cache

		threading.Thread(target=self.Connect, daemon=True).start()

	# 🔗 Connect to Discord gateway
	def Connect(self):
		Backoff = 5
		while self.Running:
			time.sleep(Backoff)
			if self.Ws:
				continue
			try:
				Req = urllib.request.Request(
					'https://discord.com/api/gateway',
					headers={'User-Agent': UserAgent},
				)
				with urllib.request.urlopen(Req, timeout=10) as Response:
					Data = json.loads(Response.read().decode('utf-8'))

				DiscordGatewayUrl = Data['url']
				# 📍 Be explicit about gateway protocol version and encoding
				if '?' not in DiscordGatewayUrl:
					DiscordGatewayUrl = f'{DiscordGatewayUrl}?v=10&encoding=json'

				self.Ws = websocket.WebSocketApp(
					DiscordGatewayUrl,
					on_message=self.OnMessage,
					on_error=self.OnError,
					on_close=self.OnClose,
					on_open=self.OnOpen,
				)
				self.Identified = False
				threading.Thread(target=self.Ws.run_forever, daemon=True).start()
				self.PingLoop()
				Backoff = 5  # ✅ reset after a successful session
			except Exception as E:
				logging.error(f'WebSocket connection error: {E}')
				Backoff = min(Backoff * 2, 60)

	# 📨 Handle incoming messages
	def OnMessage(self, Ws, Message):
		try:
			Data = json.loads(Message)
		except Exception as E:
			logging.debug(f'Bad gateway message: {E}')
			return

		if 's' in Data:
			self.Seq = Data['s']

		Op = Data.get('op')
		if Op == 10 and not self.Identified:
			self.HeartbeatInterval = Data['d']['heartbeat_interval'] / 1000
			self.SendHeartbeat()
			self.SendIdentify()
			self.Identified = True
		elif Op == 7:
			# 🔁 Reconnect requested by server
			self._SafeCloseWs()

	# 🔄 Ping loop to keep connection alive
	def PingLoop(self):
		while self.Ws and self.Running:
			time.sleep(self.HeartbeatInterval)
			try:
				self.Ws.send(json.dumps({'op': 1, 'd': self.Seq}))
			except Exception as E:
				logging.error(f'WebSocket ping error: {E}')
				self._SafeCloseWs()
				return

	# 🚀 Handle WebSocket open
	def OnOpen(self, Ws):
		logging.info('WebSocket connected')

	# ⚠️ Handle WebSocket errors
	def OnError(self, Ws, Error):
		logging.error(f'WebSocket error: {Error}')

	# 🔌 Handle WebSocket close
	def OnClose(self, Ws, CloseStatus, CloseMsg):
		self.Ws = None
		self.Identified = False
		logging.info(f'WebSocket closed: {CloseStatus} {CloseMsg}')

	# ❌ Close RPC connection
	def Close(self):
		self.Running = False
		self._SafeCloseWs()

	# 🧹 Internal: safely close and clear WebSocket
	def _SafeCloseWs(self):
		if self.Ws:
			try:
				self.Ws.close()
			except Exception:
				pass
			self.Ws = None
		self.Identified = False

	# 🔧 Try convert a URL to an external asset
	def _ExternalAsset(self, ImageUrl):
		if ImageUrl in self.AssetCache:
			return self.AssetCache[ImageUrl]
		try:
			Url = f'https://discord.com/api/v9/applications/{self.AppId}/external-assets'
			Data = json.dumps({'urls': [ImageUrl]}).encode('utf-8')
			Req = urllib.request.Request(
				Url,
				data=Data,
				headers={
					'Authorization': self.Token,
					'Content-Type': 'application/json',
					'User-Agent': UserAgent,
				},
			)
			with urllib.request.urlopen(Req, timeout=10) as Response:
				ResponseData = json.loads(Response.read().decode('utf-8'))
			if isinstance(ResponseData, list) and ResponseData:
				Path = ResponseData[0].get('external_asset_path')
				if Path:
					Asset = f'mp:{Path}'
					self.AssetCache[ImageUrl] = Asset
					return Asset
		except Exception as E:
			# ℹ️ Often fails for invalid token or unsupported URLs; keep quiet at info level
			logging.debug(f'External asset upload failed: {E}')
		return None

	# 🖼️ Process image for assets
	def ProcessImage(self, ImageUrl):
		if ImageUrl and ImageUrl.startswith('mp:'):
			return ImageUrl

		Candidates = []
		if ImageUrl:
			Candidates.append(ImageUrl)
		if DefaultCoverUrl not in Candidates:
			Candidates.append(DefaultCoverUrl)

		for Url in Candidates:
			Asset = self._ExternalAsset(Url)
			if Asset:
				return Asset

		# 🚫 Give up if external asset fails
		return None

	# 🎮 Send rich presence activity
	def SendActivity(self, ActivityData):
		if not self.Ws or not self.Running:
			return

		Assets = ActivityData.get('assets') or {}
		LargeImageUrl = Assets.get('large_image')
		Processed = self.ProcessImage(LargeImageUrl)
		if Processed:
			Assets['large_image'] = Processed
			ActivityData['assets'] = Assets
		else:
			ActivityData.pop('assets', None)

		Payload = {
			'op': 3,
			'd': {
				'since': None,
				'activities': [ActivityData],
				'status': 'dnd',
				'afk': False,
			},
		}
		try:
			self.Ws.send(json.dumps(Payload))
		except Exception as E:
			logging.error(f'WebSocket send error: {E}')
			self._SafeCloseWs()

	# 🧹 Clear activity
	def ClearActivity(self):
		if not self.Ws or not self.Running:
			return
		Payload = {
			'op': 3,
			'd': {
				'since': None,
				'activities': [],
				'status': 'dnd',
				'afk': False,
			},
		}
		try:
			self.Ws.send(json.dumps(Payload))
		except Exception:
			self._SafeCloseWs()

	# 💓 Send heartbeat
	def SendHeartbeat(self):
		try:
			self.Ws.send(json.dumps({'op': 1, 'd': self.Seq}))  # type: ignore
		except Exception as E:
			logging.error(f'Heartbeat send error: {E}')

	# 🆔 Send identify
	def SendIdentify(self):
		try:
			self.Ws.send(  # type: ignore
				json.dumps(
					{
						'op': 2,
						'd': {
							'token': self.Token,
							'intents': 0,
							'properties': {
								'os': 'Windows 10',
								'browser': 'Discord Client',
								'device': 'Discord Client',
							},
						},
					}
				)
			)
		except Exception as E:
			logging.error(f'Identify send error: {E}')
