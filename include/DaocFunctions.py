from pathlib import Path

cwd = Path.cwd()
if 'include' in str(cwd):
    cwd = Path.cwd().parent
    from DataVariables import *
else:
    from include.DataVariables import *
import json
import sys
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from threading import Event
import shutil
import logging
import requests
from requests.exceptions import HTTPError, Timeout, ConnectionError, RequestException
import configparser
from tcolorpy import tcolor
import json_repair
import ctypes
import datetime
from collections import OrderedDict
import math
import tkinter as tk
from tkinter import colorchooser
import win32gui
import win32con
import psutil
import re

logging.basicConfig(
    filename=cwd / 'daocparse.log', 
    level=logging.INFO,
    format='%(asctime)s %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

session = requests.Session()

highlight_names = {}
invalid_list = []

class CommentConfigParser(configparser.ConfigParser):
    """ConfigParser modified to allow for easier reading and writing of text comments to settings.ini"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('allow_no_value', True)
        super().__init__(*args, **kwargs)
        self._comment_count = 0

    def _read(self, fp, fpname):
        lines = []
        for line in fp:
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith(';'):
                self._comment_count += 1
                lines.append(f'_#{self._comment_count} = {line}')
            else:
                lines.append(line)

        super()._read(lines, fpname)

    def write(self, fp, space_around_delimiters=True):
        for section in self._sections:
            fp.write(f'[{section}]\n')
            for k, v in self._sections[section].items():
                if k.startswith('_#'):
                    fp.write(f'{v}\n')
                else:
                    delimiter = ' = ' if space_around_delimiters else '='
                    if k.startswith('#') and not v:
                        fp.write(f'{k}\n')
                    else:
                        fp.write(f'{k}{delimiter}{v}\n')
            fp.write('\n')

config = CommentConfigParser()
group_config = configparser.ConfigParser(allow_no_value=True)

class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

def set_window_title(title: str):
    """Change console window title"""
    ctypes.windll.kernel32.SetConsoleTitleW(title)

def set_window_position(pos: window_pos):
    """Move console window to specific position and set size"""
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()

    if not pos: 
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, 958, 420, win32con.SWP_NOACTIVATE)
        return

    win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, pos.x, pos.y, pos.w, pos.h, win32con.SWP_NOACTIVATE)

def get_window_position() -> window_pos:
    """Retrieve x, y, width, height for console window"""
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if not hwnd: return

    rect = RECT()
    if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        x = rect.left
        y = rect.top
        width = rect.right - rect.left
        height = rect.bottom - rect.top

        return window_pos(x, y, width, height)

def save_window_position(reset: bool = False):
    """Save current window position to settings, or reset back to default"""
    if reset:
        set_window_position(None)
        save_settings(x=0, y=0, width=958, height=420)
        printt(colored(f'Window Position Reset', fore='YELLOW'))
        logger.info('Window Position Reset')
        return

    if pos := get_window_position():
        save_settings(x=pos.x, y=pos.y, width=pos.w, height=pos.h)
        printt('%s x=%s, y=%s, width=%s, height=%s' % (colored(f'Window Position Saved:', fore='YELLOW'), pos.x, pos.y, pos.w, pos.h))
        logger.info('Window Position Saved: x=%s, y=%s, width=%s, height=%s' % (pos.x, pos.y, pos.w, pos.h))

def printt(text: str, large_space: bool = False, new_line: bool = False, end_line: bool = False):
    """Print function with spaces to move text away from left edge"""
    spaces = ' ' * (22 if large_space else 2)
    first_line = '\n' if new_line else ''
    second_line = '\n' if end_line else ''
    print(f'{first_line}{spaces}{text}{second_line}')

def draw_line(blank_line: bool = True):
    """Draw a line using the _ character"""
    line = ''.center(128, '_')
    printt(colored(line, fore='LIGHT_BLACK'))
    if blank_line: print()

def add_lines(func):
    """Decorator for printing horizontal lines before and after a function"""
    def wrapper(*args, **kwargs):
        draw_line()
        func(*args, **kwargs)
        draw_line()
    return wrapper

def file_exists(file_path: str) -> bool:
    """Check if a file exists"""
    return Path(file_path).is_file()

def dir_exists(path: str) -> bool:
    """Check if a directory exists"""
    if not path: return False
    return os.path.isdir(path)

def get_daoc_folder() -> str:
    """
    Attempt to find Dark Age of Camelot logs folder - uses ui.log file generated by game incase there is no chat.log
    Default location is C:/Users/{User}/Documents/Electronic Arts/Dark Age of Camelot
    """
    user_path = Path.home() / 'Documents/Electronic Arts/Dark Age of Camelot'
    if file_exists(f'{user_path}/ui.log'):
        return str(user_path)
    return False

def create_ini(daoc_folder: str = '', eden_sid: str = '', user_agent: str = ''):
    """Create settings.ini file"""
    user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36'
    config.add_section('EDEN')
    config.set('EDEN', '# eden website login cookie (32 characters long)')
    config.set('EDEN', 'eden_daoc_sid', eden_sid)
    config.set('EDEN', '# example: e96cafe42e651488d9ee01b627102031')
    config.set('EDEN', 'user_agent', user_agent)
    config.set('EDEN', '# must match your user_agent when logging into eden website')
    config.add_section('DAOC')
    config.set('DAOC', '# path to DAOC log folder')
    config.set('DAOC', 'daoc_folder', daoc_folder or get_daoc_folder())
    config.set('DAOC', '# automatically copy chat.log into saved_logs folder')
    config.set('DAOC', 'save_logs', '1')
    config.add_section('SETTINGS')
    config.set('SETTINGS', '# show AI bots (magenta names)')
    config.set('SETTINGS', 'show_bots', '1')
    config.set('SETTINGS', '# show keep/tower/relic captures')
    config.set('SETTINGS', 'show_captures', '1')
    config.set('SETTINGS', '# Color RR12+')
    config.set('SETTINGS', 'show_rr12', '1')
    config.set('SETTINGS', '# Use small text for class names')
    config.set('SETTINGS', 'smoll_text', '1')
    config.add_section('EVENTS')
    config.set('EVENTS', '# additional data collection')
    config.set('EVENTS', 'realm_points', '1')
    config.set('EVENTS', 'money', '0')
    config.set('EVENTS', 'battlegroup', '0')
    config.add_section('WINDOW')
    config.set('WINDOW', 'x', '0')
    config.set('WINDOW', 'y', '0')
    config.set('WINDOW', 'width', '0')
    config.set('WINDOW', 'height', '0')

    with open(cwd / 'settings.ini', 'w', encoding='utf-8', errors='ignore') as configfile:
        config.write(configfile)

def save_settings(**kwargs):
    """Change settings and save to settings.ini"""
    for k, v in kwargs.items():
        for section in config:
            if k in config[section]:
                config.set(section, k, str(v))

    with open(cwd / 'settings.ini', 'w', encoding='utf-8', errors='ignore') as configfile:
        config.write(configfile)

def load_settings() -> dict:
    """Load settings from settings.ini"""
    if not file_exists(cwd / 'settings.ini'):
        create_ini()

    config.clear()
    config.read(cwd / 'settings.ini')
    config_dict = {
        'eden_daoc_sid': config.get('EDEN', 'eden_daoc_sid'),
        'user_agent': config.get('EDEN', 'user_agent'),
        'daoc_folder': config.get('DAOC', 'daoc_folder'),
        'save_logs': config.get('DAOC', 'save_logs'),
        'show_bots': config.getboolean('SETTINGS', 'show_bots'),
        'show_captures': config.getboolean('SETTINGS', 'show_captures'),
        'show_rr12': config.getboolean('SETTINGS', 'show_rr12'),
        'smoll_text': config.getboolean('SETTINGS', 'smoll_text'),
        'realm_points': config.getboolean('EVENTS', 'realm_points'),
        'money': config.getboolean('EVENTS', 'money'),
        'battlegroup': config.getboolean('EVENTS', 'battlegroup'),
        'pos': window_pos(config.getint('WINDOW', 'x'), config.getint('WINDOW', 'y'), config.getint('WINDOW', 'width'), config.getint('WINDOW', 'height'))
    }

    return config_dict

def create_groups():
    """Create groups.ini file with a few highlight groups"""
    group_config['Alb'] = {
        'color': 'RED', 
        'style': '',
        'extra': '',
        'names': 'Prack'
    }
    group_config['Hib'] = {
        'color': 'GREEN', 
        'style': '',
        'extra': '',
        'names': 'Pilzpower'
    }
    group_config['Mid'] = {
        'color': 'LIGHT_BLUE', 
        'style': '',
        'extra': '',
        'names': 'Klarinogampros'
    }
    group_config['Group'] = {
        'color': 'False', 
        'style': '',
        'extra': '[]',
        'names': ''
    }
    group_config['Me'] = {
        'color': 'YELLOW', 
        'style': 'invert',
        'extra': '',
        'names': ''
    }

    with open(cwd / 'groups.ini', 'w', encoding='utf-8', errors='ignore') as configfile:
        group_config.write(configfile)

def load_groups() -> dict:
    """Load groups.ini file for highlight groups"""
    if not file_exists(cwd / 'groups.ini'):
        create_groups()

    group_config.read(cwd / 'groups.ini', encoding='utf-8')
    _config = {}

    for k, v in group_config.items():
        if k == 'DEFAULT': continue
        _config[k.title()] = {
            'color': tuple([item.strip() for item in v['color'].split(',')]),
            'style': list([item.strip() for item in v['style'].split(',') if len(item)]),
            'extra': list([item.strip() for item in v.get('extra', '')]),
            'hidden': v.get('hidden', 'False'),
            'names': [item.title().strip() for item in v['names'].split(',') if item],
        }

    return _config

def save_groups(highlight_dict: dict):
    """Save highlight groups to groups.ini"""
    group_config.clear()
    for k, v in highlight_dict.items():
        _color = v.get('color')
        if isinstance(_color, list) or isinstance(_color, tuple):
            _color = ', '.join(_color)

        group_config[k] = {
            'color': _color,
            'style': ''.join(v.get('style', [])),
            'extra': ''.join(v.get('extra', '')),
            'hidden': v.get('hidden', 'False'),
            'names': ', '.join(v['names'])
            }

    printt('Groups Saved')
    with open(cwd / 'groups.ini', 'w', encoding='utf-8', errors='ignore') as configfile:
        group_config.write(configfile)

def colored(text: str, fore: str = 'WHITE', back: str = 'BLACK', style: list = []) -> str:
    """Return colored text"""
    fore = fore.replace('#', '')
    back = back.replace('#', '')

    return tcolor(text, color=fore, bg_color=back, styles=style)

def create_blank_class():
    """Create a blank class.txt file to store all characters class"""
    with open(cwd / 'class.txt', 'w', encoding='utf-8', errors='ignore') as f:
        f.write(json.dumps(blank_class_list, indent=2))

def load_characters() -> dict:
    """Load file containing stored class information"""
    if not file_exists(cwd / 'class.txt'):
        create_blank_class()

    with open(cwd / 'class.txt', 'r') as f:
        return json.load(f)

def update_rank12():
    """Fetch rank 12+ for all realms and save"""
    rr12_names = get_rr12()
    save_rr12(rr12_names)

def create_blank():
    """Create a blank chat.log file to prevent errors reading a file that doesn't exist"""
    logger.info('Created blank chat.log')
    with open(f'{log_path}/chat.log', 'w', encoding='utf-8', errors='ignore') as f:
        f.write('')


highlight_names = load_groups()
class_list = load_characters()
settings = load_settings()

daoc_sid = settings['eden_daoc_sid']
user_agent = settings['user_agent']
log_path = settings['daoc_folder']
show_bots = settings['show_bots']
show_captures = settings['show_captures']
show_rr12 = settings['show_rr12']
save_logs = settings['save_logs']
smoll_text = settings['smoll_text']
include_rp = settings['realm_points']
include_money = settings['money']
include_battlegroup = settings['battlegroup']
pos = settings['pos']

if include_rp: events.extend(events_rp)
if include_money: events.extend(events_money)
if include_battlegroup: events.extend(events_battlegroup)

if not file_exists(f'{log_path}/chat.log'):
    create_blank()

if pos.w and pos.h:
    set_window_position(pos)

rr12_list = []
for group_name, v in highlight_names.items():
    if '12' in group_name:
        rr12_list.extend(v['names'])

headers = {
    'User-Agent': user_agent,
    'Cookie': f'eden_daoc_sid={daoc_sid}'
}
session.headers.update(headers)

def save_characters():
    """Save file containing stored class information"""
    with open(cwd / 'class.txt', 'w+') as f:      
        f.write(json.dumps(class_list, indent=2))


def check_dir(path: str) -> None:
    """Creates directory if it does not exist"""
    return Path(path).mkdir(parents=True, exist_ok=True)

def copy_file(file1_path: str, file2_path: str) -> None:
    if os.path.exists(file1_path):
        shutil.copyfile(file1_path, file2_path)

def is_open(file_path: str) -> bool:
    """Check if a file is opened by attempting to rename it"""
    try:
        os.rename(file_path, file_path)
        return False
    except OSError:
        return True

def current_time(file_string: bool = False):
    """Get current date/time - Windows filenames must use ; instead of :"""
    if file_string:
        return datetime.datetime.now().strftime('%m-%d-%Y %H;%M;%S')
    return datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S')

def delete_log_file(file_text: str = '', realm_points: int = 0):
    """Deletes current chat.log file. Saves to /saved_logs folder if save_logs is enabled"""
    now = current_time(file_string=True)

    file_name = f'chat {now} ({realm_points} RP) {file_text}'.strip()
    current_log = f'{log_path}/chat.log'
    saved_log_path = f'{log_path}/saved_logs'
    save_new = f'{saved_log_path}/{file_name}.log'
    save_logs = settings['save_logs']
    check_dir(saved_log_path)

    if save_logs:
        copy_file(current_log, save_new)
        print(f'log saved to: {save_new}')
        logger.info(f'(AUTOSAVE) {save_new}')

    if os.path.exists(current_log):
        if is_open(current_log):
            print(f'chat.log is currently in use. turn off in game logging')
            return

        os.remove(current_log)
        create_blank()

def add_character(character_name: str, character_class: str):
    """Adds new characters to class list and saves to class.txt"""
    for k, v in class_list.items():
        if is_same(character_class, k):
            if character_name not in v:
                v.append(character_name)
                # logger.info(f'(Added) {character_name} - {character_class}')
                save_characters()
                return

def verify_cookie():
    """Check if Eden login cookie is valid to pull data from website"""
    try:
        response = session.get('https://eden-daoc.net/hrald/proxy.php?player/Pilzpower', timeout=5)
        response.raise_for_status()
        return response.status_code == 200

    except RequestException as e:
        logger.error('(Cookie) Unable to get data from Eden website')
        return False

def fetch_player(player_name: str) -> tuple[str, str, str, str, str]:
    """Fetch player data from Eden Herald"""
    if is_npc(player_name): return
    if _data := open_url(f'https://eden-daoc.net/hrald/proxy.php?player/{player_name}'):
        _class = class_name(_data.get('class'))
        _rp = _data.get('realm_points')
        _race = race_name(_data.get('race_id'))
        _guild = _data.get('guild_name') or ''
        _female = _data.get('is_female')
        _last = _data.get('last_name') or ''
        _fullname = f'{player_name} {_last}' if _last else player_name
        _realm = get_realm_name(_data.get('realm'))
        _, _rank, _, _, _ = rp_to_rr(_rp)
        _title = get_realm_title(_realm, _rank, _female)
        _racetitle = f'{_race} {_title}'
        _realm_index, _realm_name = class_realm(_class)
        _realm_color = realm_colors[_realm_index]

        if not get_class(player_name):
            add_character(player_name, _class)

        return (_class, _rp, _guild, _racetitle, _fullname)
    else:
        add_character(player_name, 'Bot')
        return ('Bot', '0', '', '', player_name)

def open_url(url: str):
    """Open a URL and return data only if the server responds 200 OK"""
    response = session.get(url)

    if response.status_code == 200:
        if 'class' in response.text:
            data = remove_garbage(response.text)
            _data = json_repair.loads(data)[1]
            return _data

    if response.status_code == 403:
        logger.warning('(COOKIE) Unable to get data from Eden - check eden_daoc_sid')
        raise InvalidCookie('403 Forbidden. Check cookie and user agent.')

def get_player_herald(player_name: str, data_only: bool = False):
    """Fetch and display Herald information"""
    if player_info := fetch_player(player_name):
        _player_class, _player_rp, _player_guild, _player_title, _player_name = player_info
        _realm_index, _realm_name = class_realm(_player_class)
        _rvr_rank, _rvr_title, _rvr_next, _rvr_next_rank, _rvr_next_rank_remaining = rp_to_rr(_player_rp)
        _realm_color = realm_colors[_realm_index]
        _realm_points = comma(_player_rp)
        _rvr_next = comma(_rvr_next)

        _data = {'Class': _player_class, 
                'Race': _player_title, 
                'Guild': _player_guild, 
                'RR': _rvr_rank, 
                'RP': _realm_points, 
                'Next': _rvr_next}
                # f'Rank {_rvr_next_rank}L0': _rvr_next_rank_remaining}

        if data_only:
            return (_data, _realm_color, _player_class)

        box = InfoBox(color=_realm_color)
        box.add_text(_player_name, _data)

        box.display()

def get_guild_members(guild_name: str, page: int = 0) -> list:
    """Fetch all characters from a specific guild (Eden guild page is case sensitive)"""
    member_list = []
    guild_name = guild_name.replace(' ', '_')

    guild_url = eden_urls['guild']
    guild_page = f'{guild_url}{guild_name}?page={page}'

    if _data := open_url(guild_page):
        for member_index, member_data in _data.items():
            if member_index.isnumeric():
                _name = member_data.get('name')
                _rp = member_data.get('realm_points')
                _class = member_data.get('class')
                member_list.append(_name)

    if not member_list:
        print(f'{guild_name} - Not Found')

    return member_list

def get_rr12() -> dict[list, list, list]:
    """Fetch list of all players with over 23,308,097 RP"""
    rr12_data = {'albion': [], 'midgard': [], 'hibernia': []}

    def get_top(url_type: str, url: str):
        if _data := open_url(url):
            for k, v in _data.items():
                if isinstance(v, dict):
                    _name = v['name']
                    _rp = int(v['realm_points'])
                    if _rp >= 23308097:
                        rr12_data[url_type].append(_name)

            _text = ', '.join(rr12_data[url_type])
            _realm = realm_name_to_index(url_type.title())
            _color = realm_colors[_realm]
            printt('%s - %s' % (colored(url_type.title(), fore=_color), _text))

    for url_type, url in eden_urls['top'].items():
        threading.Thread(target=get_top, args=(url_type, url)).start()

    while not all(value for value in rr12_data.values()):
        time.sleep(0.1)

    return rr12_data

def save_rr12(rr12_data):
    """Save rank 12+ to groups.ini"""
    highlight_names['Hib12'] = {
        'color': 'False', 
        'style': '',
        'extra': '',
        'hidden': True,
        'names': rr12_data['hibernia']
    }
    highlight_names['Mid12'] = {
        'color': 'False', 
        'style': '',
        'extra': '',
        'hidden': True,
        'names': rr12_data['midgard']
    }
    highlight_names['Alb12'] = {
        'color': 'False', 
        'style': '',
        'extra': '',
        'hidden': True,
        'names': rr12_data['albion']
    }

    rearrange_highlight = OrderedDict(highlight_names)
    # Move to beginning of list to ensure names in actual groups take priority
    rearrange_highlight.move_to_end('Mid12', last=False)
    rearrange_highlight.move_to_end('Hib12', last=False)
    rearrange_highlight.move_to_end('Alb12', last=False)

    print()
    printt(f'Rank 12 List Saved')
    save_groups(rearrange_highlight)

def get_duel(player_name: str) -> dict:
    """Fetch information on player duel stats (hunter of, prey of)"""
    duel_list = {'hunter': {}, 'hunted': {}}

    def get_top(url_type: str, url: str):
        if _data := open_url(f'{url}{player_name}'):
            for i, (k, v) in enumerate(_data.items()):
                if isinstance(v, dict):
                    _name = v['name']
                    _realm = int(v['realm'])
                    _count = v['count']
                    _color = realm_colors[_realm]

                    duel_list[url_type] |= {_name: (_count, _color)}

                if i >= 10: break

    for url_type, url in eden_urls['duel'].items():
        threading.Thread(target=get_top, args=(url_type, url)).start()

    while not all(value for value in duel_list.values()):
        time.sleep(0.1)

    return duel_list

class FullStats():
    """
    Fetch all stats from Herald pages

    https://eden-daoc.net/hrald/proxy.php?player/
    https://eden-daoc.net/hrald/proxy.php?rank/pvp/
    https://eden-daoc.net/hrald/proxy.php?rank/character/
    https://eden-daoc.net/hrald/proxy.php?top/lwrp?class=
    https://eden-daoc.net/hrald/proxy.php?top/lwsk?class=
    https://eden-daoc.net/hrald/proxy.php?killed/
    """
    def __init__(self, player_name: str):
        self.player_name = player_name
        self.data = {}
        self.data_display = {}
        self.pages_loaded = 0
        self.player_class = ''
        self.class_id = 0
        self.lwrp_data = {}
        self.lwsk_data = {}
        self.duel_data = {}
        self.player_lwrp = 0
        self.rank_lwrp = 0
        self.top_lwrp = 0
        self.player_lwsk = 0
        self.rank_lwsk = 0
        self.top_lwsk = 0
        self.leader_lwrp = ''
        self.leader_lwsk = ''

        self.lwsk_done = False
        self.lwrp_done = False

        self.player_data = {}
        self.player_class = get_class(player_name) or ''

        if not get_class(player_name):
            if _player_data := get_player_herald(self.player_name, True):
                self.player_data = _player_data
                self.player_class = _player_data[2]

        self.class_id = get_class_id(self.player_class) or ''
        self.color = 'WHITE'

    def get_stats(self) -> dict:
        """Loop through pages and wait for all data to be fetched"""
        start_time = time.time()

        if self.player_class == 'Bot' or not get_class(self.player_name): return

        set_window_title(f'Fetching... ({self.pages_loaded})')

        for url_type, url in rvr_urls.items():
            threading.Thread(target=self.fetch_player, args=(url_type, url)).start()

        while not get_class(self.player_name):
            time.sleep(0.1)

        self.class_id = get_class_id(self.player_class) or ''

        while self.pages_loaded < len(rvr_urls):
            time.sleep(0.1)

        for i, (k, v) in enumerate(self.lwrp_data.items()):
            if isinstance(v, dict):
                _name = v.get('name')
                _lwrp = int(v.get('lwrp', 0))
                if i == 0:
                    self.top_lwrp = _lwrp
                    self.leader_lwrp = _name
                if is_same(_name, self.player_name):
                    self.player_lwrp = _lwrp
                    self.rank_lwrp = i+1
                    lwrp_needed = comma(self.top_lwrp - self.player_lwrp)
                    self.data |= {'lwrp': comma(_lwrp), 'lwrp_rank': self.rank_lwrp, 'lwrp_needed': lwrp_needed, 'lwrp_leader': self.leader_lwrp}
                    break

        for i, (k, v) in enumerate(self.lwsk_data.items()):
            if isinstance(v, dict):
                _name = v.get('name')
                _lwsk = int(v.get('lwsk', 0))
                if i == 0:
                    self.top_lwsk = _lwsk
                    self.leader_lwsk = _name
                if is_same(_name, self.player_name):
                    self.player_lwsk = _lwsk
                    self.rank_lwsk = i+1
                    lwsk_needed = comma(self.top_lwsk - self.player_lwsk)
                    self.data |= {'lwsk': comma(_lwsk), 'lwsk_rank': self.rank_lwsk, 'lwsk_needed': lwsk_needed, 'lwsk_leader': self.leader_lwsk}
                    break

        set_window_title(python_window_title)

        _realm_index, _realm_name = class_realm(self.player_class)
        self.color = realm_colors[_realm_index]

        box = InfoBox(color=self.color)
        box.add_text(self.player_name, self.player_data[0])

        for header, stat_type in rename_stats.items():
            self.data_display[header] = {}
            for stat_header, new_header in stat_type.items():
                if header_data := self.data.get(stat_header):
                    header_data = comma(header_data)
                    self.data_display[header][new_header] = header_data

        box.add_text('Stats', self.data_display['stats'])
        box.add_text('LWRP', self.data_display['lwrp'])
        box.add_text('LWSK', self.data_display['lwsk'])
        box.add_text('Kills', self.data_display['kills'])
        box.add_text('Deathblows', self.data_display['deathblows'])
        box.add_text('Solo', self.data_display['solo'])
        box.add_text('Hunter of', self.duel_data['hunter'])
        box.add_text('Prey of', self.duel_data['hunted'])
        box.display()

        # printt('%-10s %s\n' % ('Time:', round(time.time() - start_time, 4)))

        return self.data

    def fetch_player(self, url_type: str, url: str):
        _page = self.player_name

        if url_type in ('lwrp', 'lwsk'):
            while not self.class_id:
                time.sleep(0.1)
            _page = self.class_id

        if url_type in ('hunter', 'hunted'):
            if _duel_data := get_duel(self.player_name):
                self.duel_data |= _duel_data
                self.pages_loaded += 1
                set_window_title(f'Fetching... ({self.pages_loaded})')
                return

        if url_type == 'player':
            if _player_data := get_player_herald(self.player_name, True):
                self.player_data = _player_data
                self.data |= _player_data[0]
                self.color = _player_data[1]
                self.pages_loaded += 1
                set_window_title(f'Fetching... ({self.pages_loaded})')
                return

        if _data := open_url(f'{url}{_page}'):
            match url_type:
                case 'lwrp':
                    self.lwrp_data = _data
                    self.lwrp_done = True
                case 'lwsk':
                    self.lwsk_data = _data
                    _zero = self.lwsk_data.get('0')
                    _z1 = _zero.get('name')
                    _z2 = _zero.get('lwsk')
                    self.lwsk_done = True
                case _:
                    self.data |= _data

            self.pages_loaded += 1
            set_window_title(f'Fetching... ({self.pages_loaded})')


def comma(number: int | str) -> str:
    """Add commas to numbers"""
    if isinstance(number, str):
        if number.isnumeric():
            number = f'{int(number):,}'
    elif isinstance(number, int):
        number = f'{number:,}'
    return number

class Character():
    """Stores all character data, colored text, offsets"""
    def __init__(self, character_name: str):
        self.name = character_name[:20]
        self.realm = ''
        self.realm_index = 0
        if not get_class(character_name):
            fetch_player(character_name)
        self.player_class = get_class(character_name) or ' '
        self.color = realm_colors[12]
        self.class_color = self.color
        self.colored = colored(self.name, fore=self.color)
        self.smoll = self.player_class.lower()
        if smoll_text:
            self.smoll = smoll(self.player_class)
        self.smoll_c = colored(self.smoll, fore=realm_colors[12])

        self.style = []
        self.extra = ()
        _extra = 0
        _extra_space = 0
        _spaces = ''

        if not is_npc(character_name):
            self.realm_index, self.realm = class_realm(self.player_class)
            self.color = realm_colors[self.realm_index]
            self.class_color = self.color
            self.colored = colored(self.name, fore=self.color)

            if is_bot(character_name):
                self.smoll = ''

            self.smoll_c = colored(self.smoll, fore=realm_colors[12])

            if settings['show_rr12'] and self.name in rr12_list:
                self.smoll_c = colored(self.smoll, fore=self.color)

            bg_color = None

            for k, v in highlight_names.items():
                if self.name in v['names']:
                    self.color, bg_color = fix_color(v['color'], self.class_color)

                    self.style = v['style']
                    self.extra = v.get('extra', '')

                    self.colored = colored(
                        self.name, 
                        fore=self.color, 
                        back=bg_color or 'BLACK', 
                        style=self.style)

            if self.extra:
                if len(self.extra) == 1:
                    _spaces = ' '
                    _extra_space = 2

                self.colored = colored(
                    '%s%s%s' 
                    % (self.extra[0], self.name, self.extra[len(self.extra) - 1]), 
                    fore=self.color, 
                    back=bg_color or 'BLACK', 
                    style=self.style)

                _extra = offset('', self.extra[0], self.extra[len(self.extra) - 1])

        self.name_offset = offset(self.colored, self.name, extra=_extra)
        self.class_offset = offset(self.smoll, self.smoll_c)


def get_class(character_name: str) -> str:
    """Get class information stored in class.txt file"""
    if is_npc(character_name): return
    for k, v in class_list.items():
        for name in v:
            if character_name == name:
                return k
      
def get_class_id(player_class: str) -> int:
    """Convert class into numerical class id - Eden uses class id for a few Herald pages"""
    for k, v in classes.items():
        if player_class == v:
            return k

def class_name(class_id: int) -> str:
    """Convert class id into class name"""
    if isinstance(class_id, str): 
        class_id = int(class_id)
    return classes.get(class_id)

def race_name(race_id: int) -> str:
    """Convert race into numerical race id - Eden uses race id for a few Herald pages"""
    if isinstance(race_id, str): 
        race_id = int(race_id)
    return races.get(race_id)

def class_realm(character_class: str) -> list[int, str]:
    """Return the realm index and realm name for a specific class"""
    realm_index = 0
    realm_name = ''

    for k, v in class_realm_index.items():
        if character_class in v:
            realm_index = k
            break
    
    realm_name = realm_eden.get(realm_index)

    return realm_index, realm_name

def get_realm_name(realm_index: int) -> str:
    """Convert realm index to realm name"""
    return realm_eden.get(realm_index)

def realm_name_to_index(realm_name: str) -> str:
    """Convert realm name into realm index"""
    for k, v in realm_eden.items():
        if v == realm_name:
            return k

def get_realm_title(realm_name: str, realm_rank: str, is_male: bool) -> str:
    """Return correct realm rank title for male/female characters"""
    try:
        _title = (
            realm_titles
            .get(realm_name)
            .get(realm_rank)
            [1 if is_male else 0]
        )
        return _title
    except:
        return ''

def zone_realm(zone_name: str):
    """Colors zone names based on which realm the zone is in"""
    for i in range(len(zones)):
        for zone_area in zones[i]:
            relic_area = False
            # Relic keeps use a darker color
            if zone_area.startswith('!'):
                zone_area = zone_area[1:]
                relic_area = True

            if is_same_area(zone_area, zone_name):
                if relic_area: i += 5

                return colored(zone_name, fore=realm_colors[i + 1])

    return zone_name

def clear():
    _ = os.system('cls') 

class InfoBox:
    """
    Box made with ascii to display information
    """
    def __init__(self, color='WHITE', back='BLACK'):
        self.sections = {}
        self.colors = {}
        self.color = color
        self.back = back

    def add_text(self, header: str, dicts: dict, colors: tuple = ('YELLOW', 'BLACK')):
        if not dicts: return
        self.sections[header] = dicts
        self.colors[header] = colors

    def clear(self):
        self.sections = {}
        self.colors = {}
        self.color = 'WHITE'
        self.back = 'BLACK'

    def set_color(self, color='WHITE', back='BLACK'):
        self.color = color
        self.back = back

    def display(self):
        edge = colored('==', fore=self.color)

        for i, (header_text, data_dict) in enumerate(self.sections.items()):
            match i:
                case 0:
                    printt(colored(f' {header_text} '.center(58, '='), fore=self.color, back=self.back), large_space=True)
                case _:
                    printt(colored('==%s==' % (f' {header_text} ').center(54, '-'), fore=self.color, back=self.back), large_space=True)

            for key, value in data_dict.items():
                key = key[:20]
                _color = 'YELLOW'

                if isinstance(value, tuple):
                    value, _color = value

                value = str(value)[:24]

                key_text = colored(key, fore=_color, back=self.back)
                k_offset = offset(key_text, key)

                value_text = colored(value, fore='WHITE', back=self.back)
                v_offset = offset(value_text, value)

                printt('%s%26s: %-26s%s' % (
                    edge, 
                    key_text.rjust(26 + k_offset), 
                    value_text.ljust(26 + v_offset), 
                    edge), large_space=True)

        printt(colored('=' * 58, fore=self.color, back=self.back), large_space=True, end_line=True)
        self.clear()

def rp_to_rr(realm_points: int) -> list[str, int]:
    """Convert realm points into realm rank, and calculate rp needed for next level"""
    if isinstance(realm_points, str): realm_points = int(realm_points)

    rank_count = 0
    rank_next = 0
    rank_rr = 0
    rank_level = 0

    for i, x in enumerate(realm_ranks):
        if int(realm_points) >= x:
            rank_count = str(i)
            rank_next = i + 1

    if len(rank_count) == 1: 
        rank_count = f'0{rank_count}'

    rank_rr = int(rank_count[:-1]) + 1
    rank_level = int(rank_count[-1:])
    rp_remaining = realm_ranks[rank_next] - realm_points

    # Used to get how many realm points is needed for the next full realm level
    realm_levels_next_rank = 10 - rank_level
    next_rank = rank_rr + 1
    next_full_level_index = int(rank_count) + realm_levels_next_rank
    next_full_level_remaining = '?'

    # RP values for rr14 aren't added, so cap at 13L0
    if next_full_level_index < len(realm_ranks):
        next_full_level = realm_ranks[next_full_level_index]
        next_full_level_remaining = comma(next_full_level - realm_points)

    return (
        f'{rank_rr}L{rank_level}',
        f'rr{rank_rr}',
        rp_remaining,
        next_rank,
        next_full_level_remaining
    )

def make_invalid():
    """Create lists containing bot names, and names from groups with hidden set to True"""
    _invalid_list = []
    _ignore_list = []

    for k, v in class_list.items():
        if k != 'Bot': continue
        for name in v:
            _invalid_list.append(name)

    for k, v in highlight_names.items():
        _ignore = v.get('hidden')
        if _ignore == 'True':
            _ignore_list.extend(v['names'])
        elif _ignore == 'False':
            for n in v['names']:
                if n in _ignore_list:
                    _ignore_list.remove(n)

    return _invalid_list, _ignore_list

def is_player(character_name: str) -> bool:
    return get_class(character_name) != None

def is_bot(character_name: str) -> bool:
    return get_class(character_name) == 'Bot'

def has_bots(kill_info: rvr_event) -> bool:
    return (
        is_bot(kill_info.killer)
        or is_bot(kill_info.victim)
    )

def is_npc(character_name: str) -> bool:
    """
    Basic checks to determine if a name is an NPC
    Players with names of NPC such as "Guardian" are excluded because there is no way to determine if it is the player or a guard
    """
    return (
        character_name[:1].islower() 
        or ' ' in character_name
        # or character_name == 'Total'
        or character_name in npc_list
    )

def has_npc(kill_info: rvr_event) -> bool:
    """Check if either the killer or victim is an NPC"""
    return (
        is_npc(kill_info.killer)
        or is_npc(kill_info.victim)
    )

def is_keep(kill_event: rvr_event) -> bool:
    """
    Check if event is a tower or keep capture
    [02:09:01] The forces of Midgard led by Cobx have captured Dun Crauchon!
    rvr_event values for captures:
        time: 02:09:01
        victim: Midgard
        killer: Cobx
        zone: Dun Crauchon
    """
    return (
        kill_event.victim in realm_list
        and kill_event.victim != 'Frontier'
    )

def is_relic(kill_event: rvr_event) -> bool:
    """
    Check if event is a relic capture
    [02:19:12] Akwards from Midgard has stored the Merlins Staff in Glenlock Faste.
    rvr_event values for relic:
        time: 02:19:12
        victim: Akwards
        killer: Midgard
        zone: Merlins Staff
        extra: Glenlock Faste
    """
    return (
        kill_event.killer in realm_list
        and not zone_realm(kill_event.zone)
    )

def is_same_area(zone_1: str, zone_2: str) -> bool:
    """Compare two zone texts for finding zones based on partial matches"""
    return (
        zone_1.title() in zone_2.title()
        or zone_2.title() in zone_1.title()
    )

def player_match(character_name: str, player_1: str, player_2: str) -> bool:
    """Check if character_name matches either player_1 or player_2"""
    return character_name in (player_1, player_2)

def contains_name(name_list: list, player_1: str, player_2: str) -> bool:
    """Check if a list contains either player_1 or player_2"""
    return (
        player_1 in name_list
        or player_2 in name_list
    )

def is_same(text_1: str, text_2: str) -> bool:
    """Lower case comparison of text"""
    return text_1.lower() == text_2.lower()

def remove_garbage(text: str) -> str:
    """Remove a few html tags"""
    return (
        text
        .replace('&nbsp;', ' ')
        .replace('<br>', '')
        .replace('<br/>', '')
    )

def get_time_difference(date_string: str):
    """
    Calculate how many hours have passed between now and a previous date for auto updating the list of rank 12+
    Currently unused
    """
    format_pattern = '%m-%d-%Y %H:%M:%S'
    dt1 = datetime.datetime.strptime(date_string, format_pattern)
    dt2 = datetime.datetime.strptime(current_time(), format_pattern)

    return math.floor((dt2 - dt1).total_seconds() / 3600)

def offset(*args, **kwargs) -> int:
    """Calculate the amount of text offset to make colored text line up correctly"""
    args = list(args)
    c_off = len(args[0])
    args.pop(0)

    extra = abs(kwargs.get('extra', 0))

    for arg in args:
        c_off -= len(arg)

    c_off -= extra

    return c_off

def re_list(data: tuple | list) -> list:
    return [item for t in data for item in t]

chr_list = [chr(i) for i in range(97, 123)]

def generate_smoll() -> list:
    """Create a list of small characters to use for class names"""
    chr_list.append(' ')
    _smoll_list = []
    smoll_characters = 'ᵃᵇᶜᵈᵉᶠᵍʰᶦʲᵏˡᵐⁿᵒᵖᵠʳˢᵗᵘᵛʷˣʸᶻ '
        
    for x in range(len(smoll_characters)):
        _smoll_list.append(smoll_characters[x:x+1])

    return _smoll_list

smoll_list = generate_smoll()

def smoll(text: str) -> str:
    """Convert text into small characters"""
    smoll_text = ''

    for c in text.lower():
        smoll_text = smoll_text + smoll_list[chr_list.index(c)]

    return smoll_text

def fix_color(color: tuple, class_color: str = None) -> tuple[str, str]:
    """Fix for when the color is set to False - which uses realm colors for names instead of specific colors"""
    fore_color = 'WHITE'
    back_color = 'BLACK'

    if isinstance(color, tuple):
        if len(color) == 1:
            fore_color = color[0]
            if color[0] == 'False':
                fore_color = 'WHITE'
                fore_color = class_color or 'WHITE'

        if len(color) == 2:
            fore_color, back_color = color

    return fore_color, back_color

@add_lines
def display_help():
    """Help menu for displaying different commands"""
    printt(colored('Commands', fore='YELLOW'))
    printt('%-10s %-20s %s' % ('{name}', 'Filter Player', 'Shows all kills from {name}'))
    printt('%-10s %-20s %s' % ('!{name}', 'Herald Search', 'Get player info from Eden Herald'))
    printt('%-10s %-20s %s' % ('.{name}', 'Herald Search', 'Get full player info (lwrp, lwsk, hunter of, prey of)'))
    print()
    printt('%-10s %-20s %s' % ('/{n}', 'Recent Kills', 'Shows last {n} kills (/100)'))
    printt('%-10s %-20s %s' % ('@{zone}', 'Filter Zone', 'Kills from {zone} (@darkness, @ellan)'))
    printt('%-10s %-20s %s' % (',', 'Filter No EV', 'Kills from zones that are not inside of Ellan Vannin'))
    printt('%-10s %-20s %s' % ('#', 'Filter Group', 'Kills from names in all custom groups'))
    printt('%-10s %-20s %s' % ('#{id}', 'Filter Group', 'Kills from names found in specific custom group {id}'))
    print()
    printt('%-10s %-20s %s' % ('%', 'AI Bots', 'Toggle whether AI bot players are shown'))
    printt('%-10s %-20s %s' % ('^', 'Currency', 'Shows session RP, BP, and money earned'))
    printt('%-10s %-20s %s' % ('$', 'Captures', 'Shows all tower/keep/relic captures'))
    printt('%-10s %-20s %s' % ('>', 'BG Count', 'Shows BG join/leave count. Requires in game /bg count'))
    print()
    printt('%-10s %-20s %s' % ('*{text}', 'Delete Log', 'Deletes current chat.log. Saved to /saved_logs/{date}{text}.log if autosave is enabled'))
    print()
    printt('%-10s %-20s %s' % ('<', '', 'Editor to create custom groups'))
    print()
    printt('%-10s %-20s %s' % ('&', 'Rank 12+', 'Update list of rank 12+ characters'))
    printt('%-10s %-20s %s' % ('-', '', 'Save current position and size of the window'))
    printt('%-10s %-20s %s' % ('+', '', 'Reset position and size'))
    print()
    printt(colored('Hidden groups will only show if you search them specifically (#alb12, #hib12, #mid12)', fore=grey_color))
    print()

    printt(colored('%-10s %-10s %s' % ('ID', 'Hidden', 'Preview'), fore='YELLOW'))

    for k, v in highlight_names.items():
        _style = v.get('style')
        _name = 'Name'
        if len(v.get('names')): 
            _name = v.get('names')[0]

        _color, _bg_color = fix_color(v['color'])
        _hide = v.get('hidden')
        _hidden = '+' if _hide == 'True' else ''
        _realm_color = '+' if v['color'][0] == 'False' else ''
        _extra = v.get('extra', '')

        _display = colored(_name, fore=_color, style=_style)

        if _extra:
            _display = colored('%s%s%s' % (_extra[0], _name, _extra[len(_extra) - 1]), fore=_color, style=_style)

        printt('%-10s %-10s %s' % (k, _hidden, _display))

class SetupApp():
    """Basic setup to ensure we are able to pull data from Eden website"""
    def __init__(self):
        self.my_user_agent = ''
        self.my_daoc_sid = ''
        self.log_exists = file_exists(f'{log_path}/chat.log')
        self.daoc_path = get_daoc_folder()
        self.my_user_agent = headers.get('User-Agent')
        self.my_daoc_sid = ''
        path_exists = dir_exists(self.daoc_path)

        if path_exists:
            if not self.log_exists:
                create_blank()
        else:
            printt('Could not find Dark Age of Camelot log folder')
            printt('Edit settings.ini with the location')
            printt('Default: C:/Users/{USER}/Documents/Electronic Arts/Dark Age of Camelot')
            time.sleep(3)
            sys.exit()

        self.begin()

    def main_page_print(self):
        print()
        text_daoc_folder = colored('Dark Age of Camelot Log Folder:', fore='YELLOW')
        printt('%s %s\n' % (text_daoc_folder, self.daoc_path))

        printt(colored('Pulling data from Eden website requires your browsers user-agent and login cookie (32 character long)', fore=grey_color))
        printt(colored('Check images to see how to get this information', fore=grey_color))
        print()
        text_user_agent = colored('User-Agent:', fore='YELLOW')
        printt(text_user_agent)
        printt(self.my_user_agent)
        print()

    def begin(self):
        self.main_page_print()
        printt(colored('Is this User-Agent correct?', fore=grey_color))
        printt(colored('Press enter to continue, or paste in your updated version', fore=grey_color))
        if input_user_agent := input('  > '):
            self.my_user_agent = input_user_agent
        while not verify_cookie():
            clear()
            self.main_page_print()
            print()
            printt(colored('Example daoc_sid: e94caae42d651488d9fe01b637092041', fore=grey_color))
            input_daoc_sid = input(colored('  Enter eden_daoc_sid: ', fore='YELLOW'))

            if len(input_daoc_sid) != 32:
                inv = colored('Invalid:', fore='LIGHT_RED')
                printt('%-20s %s' % (inv, colored(input_daoc_sid, fore=grey_color)))

            self.my_daoc_sid = input_daoc_sid

            headers = {
                'User-Agent': self.my_user_agent,
                'Cookie': f'eden_daoc_sid={self.my_daoc_sid}'
            }
            session.headers.update(headers)

        clear()
        self.main_page_print()
        text_daoc_sid = colored('Cookie:', fore='YELLOW')
        printt('%s %s' % (text_daoc_sid, self.my_daoc_sid))
        print('\n')

        # Test to verify everything is working
        if player_info := fetch_player('Pilzpower'):
            _, _rp, _, _racetitle, _fullname = player_info
            text_pilz = colored(_fullname, fore='LIGHT_GREEN')
            text_rp = colored(comma(_rp), fore='YELLOW')
            printt('%s currently has %s realm points' % (text_pilz, text_rp))

        save_settings(daoc_folder=self.daoc_path, eden_daoc_sid=self.my_daoc_sid, user_agent=self.my_user_agent)

        print('\n')
        printt(colored('Fetching RR12+ Data...', fore='YELLOW'))
        update_rank12()
        print()
        printt('Setup Complete... Restart DaocParse')
        a = input('  > ')
        logger.info(f'Setup complete')
        sys.exit()

def pick_color():
    """Color picker window"""
    root = tk.Tk()
    root.withdraw()

    rgb_color, hex_color = colorchooser.askcolor(title='Select a Color')

    if hex_color:
        hex_color = hex_color.replace('#', '')

        root.destroy()

        return rgb_color, hex_color

def inputt(input_text='>'):
    return input(f' {input_text} ')

def print_line(hotkey: str = '', title: str = '', value: str = ''):
    """Prints text from the group editor"""
    _hotkey = f'({hotkey})' if hotkey else hotkey
    printt('%-10s %-30s %-30s' % (_hotkey, title, value))

def does_group_exist(group_id: str):
    """Check if a custom group id exists"""
    return highlight_names.get(group_id.title()) != None

def add_my_characters():
    """Add your own character names to the Me highlight group"""
    self_names = highlight_names['Me']['names']

    def print_me():
        clear()
        printt(colored('My Characters', fore='YELLOW'), new_line=True)
        printt(', '.join(self_names), end_line=True)

    print_me()
    while character_name := inputt('Add names or press enter when finished:').title():
        if character_name not in self_names:
            self_names.append(character_name)

        print_me()

    save_groups(highlight_names)

def increment_group_id(group_id: str) -> str:
    """Increment up a group_id to get a unique name"""
    _group_id = group_id
    i = 0
    while 1:
        if not does_group_exist(_group_id): break
        i += 1
        _group_id = f'{group_id}{i}'
    
    return _group_id

prompt = {}

class StyleBuilder():
    """
    Create new custom highlight groups
    
    Editing the groups.ini file is a much faster way to customize existing groups
    """
    def __init__(self):
        self.group_id = increment_group_id('New')
        self.fg_color = 'ff8000'
        self.bg_color = 'BLACK'
        self.style = []
        self.extra_left = ''
        self.extra_right = ''
        self.hidden = False
        self.names = []
        self.menu = 'options'

        self.highlight_text = {}

        set_window_title('Group Editor (Kills Paused)')

    def generate_group(self):
        if not self.group_id:
            printt('Group ID required')
            return

        if self.bg_color == 'BLACK':
            both_colors = (self.fg_color,)
        else:
            both_colors = (self.fg_color, self.bg_color)

        both_extra = f'{self.extra_left}{self.extra_right}'

        highlight_names[self.group_id] = {
            'color': both_colors, 
            'style': self.style,
            'extra': (self.extra_left, self.extra_right),
            'hidden': self.hidden,
            'names': self.names
        }

        save_groups(highlight_names)

    def set_color(self, fore_color: bool = True):
        rgb, _color = pick_color()
        if fore_color:
            self.fg_color = _color
        else:
            self.bg_color = _color

        self.option_menu()

    def extra_menu(self):
        self.option_menu()
        _single = colored(f'.Example.', fore=self.fg_color, back=self.bg_color, style=self.style)
        _double = colored(f'[Example]', fore=self.fg_color, back=self.bg_color, style=self.style)

        prompt['extra'] = {
            'info': 'Add extra characters to name text',
            'menu': [
                editor_display('.', '1 character on both sides', _single),
                editor_display('[]', 'Left and right side', _double),
            ]
        }

        print()
        this = prompt['extra']
        printt(colored(this['info'], fore='YELLOW'))
        print()
        for p in this['menu']:
            print_line(p.key, p.display, p.value)

        print()

        user_input = inputt()
        input1 = input2 = user_input

        if len(user_input) == 2:
            input1 = user_input[:-1]
            input2 = user_input[1:]

        self.extra_left = input1
        self.extra_right = input2

        self.option_menu()

    def add_name(self, character_name: str):
        character_name = character_name.title()
        if character_name not in self.names:
            self.names.append(character_name)

    def guild_menu(self):
        self.option_menu()
        printt(colored('Add Guild', fore='YELLOW'))
        printt(colored('Adds all members of guild (case sensitive)', fore=grey_color))

        if user_input := inputt():
            if guild_members := get_guild_members(user_input):
                self.names.extend(guild_members)

        self.option_menu()

    def name_menu(self):
        self.option_menu()
        printt(colored('Enter a character name to add', fore='YELLOW'))

        if user_input := inputt():
            self.add_name(user_input)

        self.option_menu()

    def id_menu(self):
        self.option_menu()

        printt(colored('Enter a short unique ID', fore='YELLOW'))
        printt(colored('Used to filter kills by specific groups by typing #ID', fore=grey_color))

        if user_input := inputt().title():
            if not does_group_exist(user_input):
                self.group_id = user_input

        self.option_menu()

    def style_menu(self):
        self.option_menu()

        _normal = colored('Example', fore=self.fg_color, back=self.bg_color, style=[])
        _underline = colored('Example', fore=self.fg_color, back=self.bg_color, style=['underline'])
        _invert = colored('Example', fore=self.fg_color, back=self.bg_color, style=['invert'])

        prompt['style'] = {
            'info': 'Text Style',
            'menu': [
                editor_display('n', 'Normal', _normal),
                editor_display('i', 'Invert', _invert),
                editor_display('u', 'Underline', _underline),
            ]
        }

        print()
        this = prompt['style']
        printt(colored(this['info'], fore='YELLOW'))
        for p in this['menu']:
            print_line(p.key, p.display, p.value)
        print()

        user_input = inputt()
        match user_input:
            case 'i':
                self.style = ['invert']
            case 'u':
                self.style = ['underline']
            case _:
                self.style = []

        self.option_menu()

    def option_menu(self):
        clear()
        print('\n')

        prompt['options'] = {
            'info': 'Create custom highlight groups',
            'menu': [
                editor_display('i', 'Group ID', f'#{self.group_id}'),
                editor_display('c', 'Color', self.fg_color),
                editor_display('b', 'Back Color', self.bg_color),
                editor_display('s', 'Style', ''.join(self.style)),
                editor_display('e', 'Extra', self.extra_left + self.extra_right),
                editor_display('h', 'Hidden', self.hidden),
                editor_display('g', 'Add Guild (Case Sensitive)', ''),
                editor_display('n', 'Add Name', ', '.join(self.names)),
            ]
        }

        this = prompt['options']
        printt(colored(this['info'], fore='YELLOW'))
        for p in this['menu']:
            print_line(p.key, p.display, p.value)

        print()
        print_line('!', 'Finish + Save')
        print()
        printt(colored('Hidden only show when searching with #ID', fore=grey_color))
        print()

        _ex = ''
        printt('%s' % (colored(f'{self.extra_left}{_ex}Example{_ex}{self.extra_right}', fore=self.fg_color, back=self.bg_color, style=self.style)))
        if self.names:
             for x in self.names[:3]:
                 printt('%s' % (colored(f'{self.extra_left}{x}{self.extra_right}', fore=self.fg_color, back=self.bg_color, style=self.style)))
        print()

    def run_editor(self):
        """Handle user input to navigate the menus"""
        if not highlight_names['Me']['names']:
            add_my_characters()

        self.option_menu()

        while 1:
            user_input = inputt()
            match user_input:
                case 'i':
                    self.id_menu()
                case 'c':
                    self.set_color()
                case 'b':
                    self.set_color(fore_color=False)
                case 's':
                    self.style_menu()
                case 'e':
                    self.extra_menu()
                case 'h':
                    self.hidden = not self.hidden
                    self.option_menu()
                case 'g':
                    self.guild_menu()
                case 'n':
                    self.name_menu()
                case '!':
                    self.generate_group()
                case _:
                    clear()
                    set_window_title(python_window_title)
                    break

if __name__ == '__main__':
    ...
