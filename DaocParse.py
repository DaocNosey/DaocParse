from include.DaocFunctions import *

class DaocParser():
	def __init__(self):
		set_window_title(python_window_title)

		if not verify_cookie():
			set_window_title(f'{python_window_title} (INVALID COOKIE)')

		self.loading = True

		self.log_full = []
		self.log_data = []
		self.log_count = 0

		self.start_time = 0
		self.end_time = 0

		self.loot = loot()
		self.box = InfoBox()
		self.thread_event = Event()

		self.kills = {}
		self.total_kills = 0

		self.show_bots = settings['show_bots']
		self.show_captures = settings['show_captures']

		self.highlight_names = {}
		self.highlight_names = highlight_names
		self.highlight = []
		self.invalid_list, self.ignore_list = make_invalid()

		self.bg_count = 0
		self.bg_init = False
		self.bg_data = []

		for k, v in self.highlight_names.items():
			self.highlight.extend(v['names'])

		threading.Thread(target=self.startup).start()
		threading.Thread(target=self.command_handler).start()

		self.thread_event.set()

	class FileHandler(FileSystemEventHandler):
		def __init__(self, outer):
			self.outer = outer

		def on_modified(self, event):
			"""Called when files have been modified"""
			modified_file = Path(event.src_path).name

			if modified_file == 'chat.log' and not self.outer.loading:
				self.outer.open_log()

	def startup(self):
		"""Initialize file monitoring"""
		self.event_handler = self.FileHandler(self)
		self.observer = Observer()
		self.observer.schedule(self.event_handler, path=log_path, recursive=True)
		self.observer.start()

		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			self.observer.stop()
		self.observer.join()

	def open_log(self):
		"""Read each line of chat.log and store into a list"""
		self.start_time = time.time()
		self.log_full.clear()

		with open(f'{log_path}/chat.log', encoding='utf8', errors='ignore') as f:
			lines = f.readlines()
			for line in lines:
				if '\n' in line:
					self.log_full.append(line.strip())

		time.sleep(0.1)
		self.process_log()
		# printt('%-10s %s\n' % ('Time:', round(time.time() - self.start_time, 4)))

	def process_log(self):
		"""Process new lines from chat.log"""
		new_log = len(self.log_data)
		if self.log_count != len(self.log_full):
			for x in range(self.log_count, len(self.log_full)):
				self.event_check(self.log_full[x])

			self.log_count = len(self.log_full)

		self.log_full.clear()

		if self.log_data and new_log == 0:
			self.recent_kills(100)

		self.loading = False

	def event_check(self, line: str):
		"""Check if line returns values for specific events"""
		for event in events:
			pattern = event.pattern
			if event_data := pattern.findall(line):
				self.add_event(line, event_data[0], event)
				return

	def add_event(self, line: str, data: tuple, game_data: game_event):
		"""Handle different event types"""
		event = game_data.event
		event_dir = game_data.event_direction
		event_type = game_data.type_of_event
		kill_info = rvr_event(*data)

		if event_type == 'money' or event_dir == '$':
			if 'due to your buff' in line: return
			self.loot.add_loot(event_dir, event_type, data)
			return

		if event_type == 'bg':
			self.bg_count_event(event_dir, data)
			return

		if event == 'kill':
			self.total_kills += 1

			if kill_info.killer not in self.kills: 
				self.kills[kill_info.killer] = [0, 0, 0, 0]
			if kill_info.victim not in self.kills: 
				self.kills[kill_info.victim] = [0, 0, 0, 0]

			self.kills[kill_info.killer][0] += 1
			self.kills[kill_info.victim][1] += 1

			if (contains_name(self.invalid_list, kill_info.killer, kill_info.victim) or has_npc(kill_info)):
				self.kills[kill_info.killer][2] += 1
				self.kills[kill_info.victim][3] += 1

		if not self.loading:
			self.print_kill(kill_info)

		self.log_data.append(kill_info)

	def generate_highlight_list(self, highlight_group: str = '', zone: str = '') -> list:
		"""Generate list for highlight group kills"""
		_highlight_kills = []
		filter_list_names = []

		if highlight_group:
			if _group := self.highlight_names.get(highlight_group):
				filter_list_names = _group['names']
			else:
				printt(f'{highlight_group} Not Found.')
				return

		for rvr in self.log_data:
			if is_keep(rvr) or is_relic(rvr):
				continue

			if not highlight_group and contains_name(self.highlight, rvr.killer, rvr.victim):
				if contains_name(self.ignore_list, rvr.killer, rvr.victim) or has_npc(rvr):
					continue

				_highlight_kills.append(rvr)

			valid_highlight = (
				highlight_group
				and contains_name(filter_list_names, rvr.killer, rvr.victim)
				and is_same_area(rvr.zone, zone)
				)

			if valid_highlight:
				_highlight_kills.append(rvr)

		return _highlight_kills

	@add_lines
	def filter_highlight(self, highlight_group: str = '', zone: str = ''):
		"""Filter kills by custom highlight groups in groups.ini"""
		_highlight_group = self.generate_highlight_list(highlight_group, zone)
		valid_group = self.highlight_names.get(highlight_group) != None

		kill_count = death_count = total_count = 0

		if _highlight_group:
			filtered_names = self.highlight

			if valid_group:
				filtered_names = self.highlight_names.get(highlight_group).get('names')

			if self.show_bots:
				kill_count = len([x.killer for x in _highlight_group if (x.killer in filtered_names)])
				death_count = len([x.victim for x in _highlight_group if (x.victim in filtered_names)])
			else:
				kill_count = len(
					[x.killer for x in _highlight_group 
					if (x.killer in filtered_names
						and not contains_name(self.invalid_list, x.killer, x.victim)
						and not has_npc(x))])

				death_count = len(
					[x.victim for x in _highlight_group 
					if (x.victim in filtered_names 
						and not contains_name(self.invalid_list, x.killer, x.victim) 
						and not has_npc(x))])

			total_count = kill_count + death_count

		if highlight_group:
			if not valid_group: return

			_color, _back = fix_color(self.highlight_names.get(highlight_group).get('color'))

			_information = {'Kills': kill_count, 'Deaths': death_count}
			if zone:
				_information['Zone'] = zone

			self.box.set_color(_color, _back)
			self.box.add_text(highlight_group or 'All', _information)
			self.box.display()

		for rvr in _highlight_group:
			self.print_kill(rvr)

	def print_keep(self, kill_info: rvr_event):
		"""Print text for Keep/Tower captures"""
		timestamp = colored(kill_info.time, fore=grey_color)
		realm = kill_info.victim
		color = realm_colors[realm_list.index(realm)]
		zone = zone_realm(kill_info.zone)

		capture = colored('◄ %s (%s) ►' 
			% (kill_info.zone, kill_info.killer), 
			fore=color)

		printt('[%s] %s' 
			% (timestamp, capture.center(90)))

	def print_relic(self, kill_info: rvr_event):
		"""Print text for Relic captures"""
		timestamp = colored(kill_info.time, fore=grey_color)
		realm = kill_info.killer
		color = realm_colors[realm_list.index(realm)]
		zone = zone_realm(kill_info.extra)

		capture = colored('◄◄◄◄ %s (%s) ►►►►' 
			% (kill_info.zone, kill_info.victim), 
			fore=color)

		printt('[%s]  %s (%s)' 
			% (timestamp, capture.center(88), zone))

	def print_kill(self, kill_info: rvr_event):
		"""Print text for RVR kills"""
		self.thread_event.wait()

		if self.show_captures:
			if is_keep(kill_info):
				self.print_keep(kill_info)
				return

			if is_relic(kill_info):
				self.print_relic(kill_info)
				return

		killer = Character(kill_info.killer)
		victim = Character(kill_info.victim)
		
		if (not self.show_bots and (has_bots(kill_info) or has_npc(kill_info))):
			return

		killer_name = (
			'%21s %28s') % (
			killer.smoll_c.rjust(14 - killer.class_offset), 
			killer.colored.rjust(21 + killer.name_offset)
			)
		victim_name = (
			'%-28s %-21s') % (
			victim.colored.ljust(21 + victim.name_offset), 
			victim.smoll_c.ljust(14 - victim.class_offset)
			)

		arrow = colored('→', fore='RED')
		timestamp = colored(kill_info.time, fore=grey_color)
		zone = zone_realm(kill_info.zone)

		printt('[%s] %s %s %s (%s)' 
			% (timestamp, killer_name, arrow, victim_name, zone))

	def recent_kills(self, display_count: int):
		"""Print n most recent kills"""
		if display_count >= 300: clear()

		kill_list = self.log_data[-display_count:]
		for rvr in kill_list:
			self.print_kill(rvr)

	def bg_count_event(self, event_dir: str, event_data: str):
		"""Handles all battlegroup events for bg count, players joining, leaving"""
		timestamp = colored(event_data[0], fore=grey_color)
		status = ''

		match event_dir:
			case '=':
				count = event_data[1]
				if count.isnumeric(): count = int(count)
				self.bg_count = count
				status = colored('count', fore='LIGHT_BLUE')
			case '+':
				if self.bg_count == 0: return
				self.bg_count += 1
				status = colored('join', fore='LIGHT_GREEN')
			case '-':
				if self.bg_count == 0: return
				self.bg_count -= 1
				status = colored('leave', fore='LIGHT_RED')
			case '^':
				self.bg_count = 0
				status = colored('disband', fore='YELLOW')
			case '*':
				return

		bg_text = ('%-26s %-24s %-8s' 
			% (f'[{timestamp}]', status, self.bg_count or ''))

		self.bg_data.append(bg_text)

	@add_lines
	def get_bg_count(self):
		if not include_battlegroup:
			printt(colored('Battlegroup data is disabled', fore='RED'))
			return

		for bg_event in self.bg_data:
			printt(bg_event)

	@add_lines
	def filter_zone(self, zone_name: str):
		"""Filters kills based on zone"""
		zone_kill_list = []
		printt('%s %s\n' 
			% (colored('Zone:', fore='YELLOW'), zone_name),
			new_line=True)

		for rvr in self.log_data:
			if is_same_area(zone_name, rvr.zone):
				zone_kill_list.append(rvr)

		for x in zone_kill_list[-500:]:
			self.print_kill(x)

	@add_lines
	def filter_character(self, character_name: str):
		"""Filters kills based on character"""
		character = Character(character_name)
		kill_count, death_count = self.get_kill_death(character_name)

		if is_player(character_name):
			self.box.set_color(character.class_color)
			self.box.add_text(character_name, {'Class': character.player_class, 'Kills': kill_count, 'Deaths': death_count})
			self.box.display()

		for rvr in self.log_data:
			if player_match(character_name, rvr.killer, rvr.victim):
				self.print_kill(rvr)

	def get_kill_death(self, character_name: str) -> tuple[int, int]:
		"""
		Calculate kill and death count
		Subtract count for bot kills if AI bots are turned off
		"""
		if character_name in self.kills:
			if not self.show_bots:
				return (
					self.kills[character_name][0] - self.kills[character_name][2], 
					self.kills[character_name][1] - self.kills[character_name][3]
				)
			return (self.kills[character_name][0], self.kills[character_name][1])
		return (0, 0)	  

	def toggle_bot_display(self):
		self.show_bots = not self.show_bots
		clear()
		self.recent_kills(300)

	def display_currency(self):
		"""Get RP, BP, and money values"""
		_rp, _bp, _p, _g, _s, _c = self.loot.get_items()

		display_data = {}
		currency_data = {
			'RP': _rp,
			'BP': _bp,
		}
		money_data = {
			'Plat': _p,
			'Gold': _g,
			'Silver': _s,
			'Copper': _c
		}

		if include_rp: display_data |= currency_data
		if include_money: display_data |= money_data

		if not display_data:
			printt(colored('RP and money data is disabled', fore='RED'))
			return

		self.box.add_text('Currency', display_data)
		self.box.display()

	@add_lines
	def filter_captures(self):
		"""Filter keep/tower captures"""
		for rvr in self.log_data:
			if is_keep(rvr):
				self.print_keep(rvr)
				continue

			if is_relic(rvr):
				self.print_relic(rvr)
				continue

	def command_handler(self):
		"""Handle all user input commands"""
		try:
			while 1:
				full_command = input().strip().title()
				command_type = full_command[:1]

				if command_type.isalpha():
					self.filter_character(character_name=full_command)
				else:
					command = full_command[1:]

					match command_type:
						case '!':
							get_player_herald(player_name=command)
						case '@':
							self.filter_zone(zone_name=command)
						case '#':
							_zone = ''
							# Used to filter by group and zone
							if group_command := re_list(re.findall(r'#(.*?) @(.*?)\Z', full_command)):
								command = group_command[0].strip()
								_zone = group_command[1].strip()

							self.filter_highlight(highlight_group=command, zone=_zone)
						case '$':
							self.filter_captures()
						case '%':
							self.toggle_bot_display()
						case '^':
							self.display_currency()
						case '&':
							...
						case '*':
							_rp = self.loot.i.get('r', 0)
							logger.info(f'(RESET) Session RP: {_rp}')
							delete_log_file()
						case '/':
							_count = int(command) if command.isnumeric() else 1000
							self.recent_kills(display_count=_count)
						case ',':
							...
						case '.':
							FullStats(player_name=command).get_stats()
						case '+':
							save_window_position()
						case '-':
							save_window_position(reset=True)
						case '?':
							display_help()
						case '>':
							self.get_bg_count()
						case '<':
							self.thread_event.clear()
							StyleBuilder().run_editor()
							self.thread_event.set()
							self.recent_kills(display_count=300)

		except Exception as e:
			print(f'(Error) {e}')
			logger.error(e)

if __name__ == '__main__':
	# Run setup if no eden_daoc_sid is found in settings.ini
	if not daoc_sid:
		SetupApp()

	LogParser = DaocParser()
	LogParser.open_log()
