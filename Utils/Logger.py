# 📦 Built-in modules
import logging

# 📥 Custom modules
from rich.console import Console as RichConsole
from rich.highlighter import RegexHighlighter
from rich.traceback import install as Install
from rich.logging import RichHandler
from rich.theme import Theme

# ⚙️ Settings
from Config import LogLevel


# 💡 Custom highlighter for log messages
class Highlighter(RegexHighlighter):
	base_style = f'{__name__}.'
	highlights = [
		r'(?P<Url>https?://[^\s]+)',
		r'Currently playing: (?P<Title>.*?) by (?P<Artist>.*?) from (?P<Album>.*)',
	]


# 🌱 Initialize and define logging
def InitLogging():
	ThemeDict = {
		'log.time': 'bright_black',
		'logging.level.debug': '#B3D7EC',
		'logging.level.info': '#A0D6B4',
		'logging.level.warning': '#F5D7A3',
		'logging.level.error': '#F5A3A3',
		'logging.level.critical': '#ffc6ff',
		f'{__name__}.Url': 'bold green',
		f'{__name__}.Title': 'bold blue',
		f'{__name__}.Artist': 'bold green',
		f'{__name__}.Album': 'bold red',
	}
	Console = RichConsole(
		theme=Theme(ThemeDict),
		force_terminal=True,
		log_path=False,
		highlighter=Highlighter(),
		color_system='truecolor',
	)

	ConsoleHandler = RichHandler(
		markup=True,
		rich_tracebacks=True,
		show_time=True,
		console=Console,
		show_path=False,
		omit_repeated_times=True,
		highlighter=Highlighter(),
		show_level=True,
	)

	ConsoleHandler.setFormatter(logging.Formatter('│ %(message)s', datefmt='[%H:%M:%S]'))

	logging.basicConfig(level=LogLevel, handlers=[ConsoleHandler], force=True)

	Logger = logging.getLogger('rich')
	Logger.handlers.clear()
	Logger.addHandler(ConsoleHandler)
	Logger.propagate = False

	return Console, Logger


Console, Logger = InitLogging()
Install()

# 🧪 Logging test messages
if __name__ == '__main__':
	Logger.debug('This is a debug message.')
	Logger.info('This is an info message.')
	Logger.warning('This is a warning message.')
	Logger.error('This is an error message.')
	Logger.critical('This is a critical message.')
