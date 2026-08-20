import re
from typing import NamedTuple

python_window_title = 'Daoc Parser'

grey_color = '646464'
realm_list = ['', 'Albion', 'Midgard', 'Hibernia', 'Frontier', 'Darkness Falls']
realm_colors = ['LIGHT_BLACK', 'LIGHT_RED', 'LIGHT_BLUE', 'LIGHT_GREEN', 'LIGHT_YELLOW', 'MAGENTA', 'RED', 'BLUE', 'GREEN', 'LIGHT_CYAN', 'YELLOW', 'LIGHT_BLACK', '646464']
albion_zones = ['Forest Sauvage', "Hadrian's Wall", 'Pennine Mountains', 'Snowdonia', 'Folley Lake', 'Brough Ruins', 'Caer', 'Albion Portal', '!Castle Excalibur', '!Castle Myrddin']
hibernia_zones = ['Breifine', 'Cruachan Gorge', 'Emain Macha', 'Mount Collory', 'Moydruim Castle', "Nuala's Ruins", 'Dun', 'Hibernia Portal', '!Dun Lamfhota', '!Dun Dagda']
midgard_zones = ['Jamtland Mountains', "Odin's Gate", 'Uppland', 'Yggdra Forest', 'Hvedungr Ruins', 'Trellebourg', 'Faste', 'Midgard Portal', '!Mjollner Faste', '!Grallarhorn Faste']
frontier_zones = ['Ellan', 'Tower', 'Irish Sea', 'Passage of Conflict', 'Knoc Meayll', "Summoner's Hall", 'Proving Grounds', 'Fort Brolorn', 'Celestius']
other_zones = ['Darkness Falls']
arena_zones = ["Manannan's Room"]
zones = [albion_zones, midgard_zones, hibernia_zones, frontier_zones, other_zones, arena_zones]
npc_list = ['Dockmaster', 'Runemaster', 'Druid', 'Scout', 'Armsman', 'Armswoman', 'Hunter', 'Healer', 'Cleric', 'Eldritch', 'Huscarl', 'Ranger', 'Champion', 'Guardian', 'Palintone', 'Templar', 'Albion', 'Midgard', 'Hibernia', 'Infernalist', 'Wizard', 'Channeler']

realm_eden = {0: 'NPC', 1: 'Albion',  2: 'Midgard', 3: 'Hibernia', 5: 'Bot'}

class_realm_index = {
    1: ['Paladin', 'Armsman', 'Scout', 'Minstrel', 'Theurgist', 'Cleric', 'Wizard', 'Sorcerer', 'Infiltrator', 'Friar', 'Mercenary', 
        'Necromancer', 'Cabalist', 'Reaver', 'Heretic', 'Occultist'],
    2: ['Thane', 'Warrior', 'Shadowblade', 'Skald', 'Hunter', 'Healer', 'Spiritmaster', 'Shaman', 'Runemaster', 'Bonedancer', 'Berserker', 
        'Savage', 'Valkyrie', 'Warlock'],
    3: ['Bainshee', 'Eldritch', 'Enchanter', 'Mentalist', 'Blademaster', 'Hero', 'Champion', 'Warden', 'Druid', 'Bard', 'Nightshade', 
        'Ranger', 'Animist', 'Valewalker', 'Vampiir'],
    5: ['Bot'], 
}

eden_urls = {
    'top': {
        'albion': 'https://eden-daoc.net/hrald/proxy.php?top/players?realm=1',
        'midgard': 'https://eden-daoc.net/hrald/proxy.php?top/players?realm=2',
        'hibernia': 'https://eden-daoc.net/hrald/proxy.php?top/players?realm=3'
        },
    'stats': {
        'player': 'https://eden-daoc.net/hrald/proxy.php?player/',
        'pvp': 'https://eden-daoc.net/hrald/proxy.php?rank/pvp/',
        'character': 'https://eden-daoc.net/hrald/proxy.php?rank/character/'
        },
    'week': {
        'lwrp': 'https://eden-daoc.net/hrald/proxy.php?top/lwrp?class=',
        'lwsk': 'https://eden-daoc.net/hrald/proxy.php?top/lwsk?class='
        },
    'duel': {
        'hunter': 'https://eden-daoc.net/hrald/proxy.php?killer/',
        'hunted': 'https://eden-daoc.net/hrald/proxy.php?killed/',
        },
    'guild': 'https://eden-daoc.net/hrald/proxy.php?guild/'
}

rvr_urls = {
    'player': 'https://eden-daoc.net/hrald/proxy.php?player/',
    'pvp': 'https://eden-daoc.net/hrald/proxy.php?rank/pvp/',
    'character': 'https://eden-daoc.net/hrald/proxy.php?rank/character/',
    'lwrp': 'https://eden-daoc.net/hrald/proxy.php?top/lwrp?class=',
    'lwsk': 'https://eden-daoc.net/hrald/proxy.php?top/lwsk?class=',
    'hunter': 'https://eden-daoc.net/hrald/proxy.php?killed/',
}

rename_stats = {
    'stats': {
        'kills': 'Kills',
        'deaths': 'Deaths',
        'deathblows': 'Deathblows',
    },
    'lwrp': {
        'lwrp': 'LWRP',
        'lwrp_rank': 'Rank',
        'lwrp_needed': 'Needed',
        'lwrp_leader': '#1',
    },
    'lwsk': {
        'lwsk': 'LWSK',
        'lwsk_rank': 'Rank',
        'lwsk_needed': 'Needed',
        'lwsk_leader': '#1',
    },
    'kills': {
        'kills': 'Kills',
        'albion_kills': 'Alb',
        'midgard_kills': 'Mid',
        'hibernia_kills': 'Hib',
    },
    'deathblows': {
        'deathblows': 'Deathblows',
        'albion_deathblows': 'Alb',
        'midgard_deathblows': 'Mid',
        'hibernia_deathblows': 'Hib',
    },
    'solo': {
        'solo_kills': 'Solo Kills',
        'albion_solo_kills': 'Alb',
        'midgard_solo_kills': 'Mid',
        'hibernia_solo_kills': 'Hib',
    },
}

classes = {
    1: 'Paladin',
    2: 'Armsman',
    3: 'Scout',
    4: 'Minstrel',
    5: 'Theurgist',
    6: 'Cleric',
    7: 'Wizard',
    8: 'Sorcerer',
    9: 'Infiltrator',
    10: 'Friar',
    11: 'Mercenary',
    12: 'Necromancer',
    13: 'Cabalist',
    19: 'Reaver',
    21: 'Thane',
    22: 'Warrior',
    23: 'Shadowblade',
    24: 'Skald',
    25: 'Hunter',
    26: 'Healer',
    27: 'Spiritmaster',
    28: 'Shaman',
    29: 'Runemaster',
    30: 'Bonedancer',
    31: 'Berserker',
    32: 'Savage',
    34: 'Valkyrie',
    59: 'Warlock',
    33: 'Heretic',
    63: 'Occultist',
    39: 'Bainshee',
    40: 'Eldritch',
    41: 'Enchanter',
    42: 'Mentalist',
    43: 'Blademaster',
    44: 'Hero',
    45: 'Champion',
    46: 'Warden',
    47: 'Druid',
    48: 'Bard',
    49: 'Nightshade',
    50: 'Ranger',
    55: 'Animist',
    56: 'Valewalker',
    58: 'Vampiir',
}

races = {
    1: 'Briton',
    2: 'Avalonian',
    3: 'Highlander',
    4: 'Saracen',
    13: 'Inconnu',
    16: 'Half Ogre',
    5: 'Norseman',
    6: 'Troll',
    7: 'Dwarf',
    8: 'Kobold',
    14: 'Valkyn',
    17: 'Frostalf',
    9: 'Celt',
    10: 'Firbolg',
    11: 'Elf',
    12: 'Lurikeen',
    15: 'Sylvan',
    18: 'Shar',
}

realm_titles = {
    'Albion': {
      'rr0': ('Invader', 'Invader'),
      'rr1': ('Guardian', 'Guardian'),
      'rr2': ('Warder', 'Warder'),
      'rr3': ('Myrmidon', 'Myrmidon'),
      'rr4': ('Gryphon Knight', 'Gryphon Knight'),
      'rr5': ('Eagle Knight', 'Eagle Knight'),
      'rr6': ('Phoenix Knight', 'Phoenix Knight'),
      'rr7': ('Alerion Knight', 'Alerion Knight'),
      'rr8': ('Unicorn Knight', 'Unicorn Knight'),
      'rr9': ('Lion Knight', 'Lion Knight'),
      'rr10': ('Dragon Knight', 'Dragon Knight'),
      'rr11': ('Lady', 'Lord'),
      'rr12': ('Baronetess', 'Baronet'),
      'rr13': ('Baroness', 'Baron'),
      'rr14': ('Arch Duchess', 'Arch Duke'),
    },
    'Hibernia': {
      'rr0': ('Defender', 'Defender'),
      'rr1': ('Savant', 'Savant'),
      'rr2': ('Cosantoir', 'Cosantoir'),
      'rr3': ('Brehon', 'Brehon'),
      'rr4': ('Grove Protector', 'Grove Protector'),
      'rr5': ('Raven Ardent', 'Raven Ardent'),
      'rr6': ('Silver Hand', 'Silver Hand'),
      'rr7': ('Thunderer', 'Thunderer'),
      'rr8': ('Gilded Spear', 'Gilded Spear'),
      'rr9': ('Bantiarna', 'Tiarna'),
      'rr10': ('Emerald Ridere', 'Emerald Ridere'),
      'rr11': ('Banbharun', 'Barun'),
      'rr12': ('Ard Bantiarna', 'Ard Tiarna'),
      'rr13': ('Ciann Cath', 'Ciann Cath'),
      'rr14': ('Ard Bandiuc', 'Ard Diuc'),
    },
    'Midgard': {
      'rr0': ('Invader', 'Invader'),
      'rr1': ('Skiltvakten', 'Skiltvakten'),
      'rr2': ('Isen Vakten', 'Isen Vakten'),
      'rr3': ('Flammen Vakten', 'Flammen Vakten'),
      'rr4': ('Elding Vakten', 'Elding Vakten'),
      'rr5': ('Stormur Vakten', 'Stormur Vakten'),
      'rr6': ('Isen Fru', 'Isen Herra'),
      'rr7': ('Flammen Fru', 'Flammen Herra'),
      'rr8': ('Elding Fru', 'Elding Herra'),
      'rr9': ('Stormur Fru', 'Stormur Herra'),
      'rr10': ('Einherjar', 'Einherjar'),
      'rr11': ('Fru', 'Herra'),
      'rr12': ('Baronsfru', 'Hersir'),
      'rr13': ('Vicomtessa', 'Vicomte'),
      'rr14': ('Stor Hurfru', 'Stor Jarl'),
    }
}

realm_ranks = (
    #       0           1           2           3           4           5           6           7           8           9
            0,          1,          25,         125,        350,        720,        1375,       2750,       3500,       5100,       # RR1
            7125,       9626,       12650,      16250,      20475,      25375,      31000,      37400,      44625,      52725,      # RR2
            61750,      71750,      82775,      94875,      108100,     122500,     138125,     155025,     173250,     192850,     # RR3
            213875,     236375,     260400,     286000,     313225,     342125,     372750,     405150,     439375,     475475,     # RR4
            513500,     553500,     595525,     639625,     685850,     734250,     784875,     837775,     893000,     950500,     # RR5
            1010625,    1073125,    1138150,    1205750,    1275975,    1348875,    1424500,    1502900,    1584125,    1668025,    # RR6
            1755250,    1845250,    1938275,    2034375,    2133600,    2236000,    2341625,    2450525,    2562750,    2678350,    # RR7
            2797375,    2919875,    3045900,    3175500,    3308752,    3445625,    3586250,    3730650,    3878875,    4030975,    # RR8
            4187000,    4347000,    4511025,    4679125,    4851350,    5027750,    5208385,    5393275,    5582500,    5776100,    # RR9
            5974125,    6176625,    6383650,    6595250,    6811475,    7032375,    7258000,    7488400,    7723625,    7963725,    # RR10
            8208750,    9111713,    10114001,   11226541,   12461460,   13832221,   15353765,   17042680,   18917374,   20998286,   # RR11
            23308097,   25871988,   28717906,   31876876,   35383333,   39275499,   43595804,   48391343,   53714390,   59622973,   # RR12
            66181501,   73461466,   81542227,   90511872,   100468178,  111519678,  123786843,  137403395,  152517769,  169294723   # RR13
    #       0           1           2           3           4           5           6           7           8           9
)

blank_class_list = {
        'Bot': [],
        'Paladin': [],
        'Armsman': [],
        'Scout': [],
        'Minstrel': [],
        'Theurgist': [],
        'Cleric': [],
        'Wizard': [],
        'Sorcerer': [],
        'Infiltrator': [],
        'Friar': [],
        'Mercenary': [],
        'Necromancer': [],
        'Cabalist': [],
        'Reaver': [],
        'Heretic': [],
        'Occultist': [],
        'Thane': [],
        'Warrior': [],
        'Shadowblade': [],
        'Skald': [],
        'Hunter': [],
        'Healer': [],
        'Spiritmaster': [],
        'Shaman': [],
        'Runemaster': [],
        'Bonedancer': [],
        'Berserker': [],
        'Savage': [],
        'Valkyrie': [],
        'Warlock': [],
        'Bainshee': [],
        'Eldritch': [],
        'Enchanter': [],
        'Mentalist': [],
        'Blademaster': [],
        'Hero': [],
        'Champion': [],
        'Warden': [],
        'Druid': [],
        'Bard': [],
        'Nightshade': [],
        'Ranger': [],
        'Animist': [],
        'Valewalker': [],
        'Vampiir': []
}

class window_pos(NamedTuple):
    x: int
    y: int
    w: int
    h: int

class editor_display(NamedTuple):
    key: str
    display: str
    value: str

class game_event(NamedTuple):
    event: str = ''
    pattern: str = ''
    type_of_event: str = '' 
    event_direction: str = '+'

class rvr_event(NamedTuple):
    time: str = ''
    victim: str = ''
    killer: str = '' 
    zone: str = ''
    extra: str = ''

events = [
    game_event(event='kill',
        pattern=re.compile(r'\[(.*?)\] (.*?) was just killed by (.*?) in (.*?)\.'),
        type_of_event='k',
        event_direction='+'),
    game_event(event='cap',
        pattern=re.compile(r'\[(.*?)\] The forces of (.*?) led by (.*?) have captured (.*?)\!'),
        type_of_event='c',
        event_direction='+'),
    game_event(event='relic',
        pattern=re.compile(r'\[(.*?)\] (.*?) from (.*?) has stored the (.*?) in (.*?)\.'),
        type_of_event='c',
        event_direction='+'),
]

events_rp = [
    game_event(event='rp',
        pattern=re.compile(r'\[(.*?)\] You get (\d+) realm points\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='bp',
        pattern=re.compile(r'\[(.*?)\] You get (\d+) bounty points\!'),
        type_of_event='b',
        event_direction='$'),
    game_event(event='rp_event',
        pattern=re.compile(r'\[(.*?)\] You get (\d+) realm points for participating in the event\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='rp_task',
        pattern=re.compile(r'\[(.*?)\] You get (\d+) realm points for completing your task\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='rp_order',
        pattern=re.compile(r'\[(.*?)\] You get (\d+) realm points for helping with the Assault Order\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='rp_front',
        pattern=re.compile(r'\[(.*?)\] You get (\d+) realm points for participating in the Living Frontier Zone\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='rp_quest',
        pattern=re.compile(r'\[(.*?)\] You get (\d+) realm points for finishing your Campaign Quest\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='rp_effort',
        pattern=re.compile(r'\[(.*?)\] You get (\d+) realm points for your efforts in the (.*?) Capture\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='rp_tick',
        pattern=re.compile( r'\[(.*?)\] You get (\d+) realm points from a (.*?) Battle Tick for your efforts\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='rp_support',
        pattern=re.compile(r'\[(.*?)\] You get an additional (\d+) realm points for your support activity in battle\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='rp_supply',
        pattern=re.compile(r'\[(.*?)\] You get (\d+) realm points for your help with the War Supplies Objective\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='rp_camp',
        pattern=re.compile(r'\[(.*?)\] You get (\d+) realm points for your contribution to the Campaign\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='rp_award',
        pattern=re.compile(r'\[(.*?)\] You have taken (.*?) and are awarded with (\d+) Realm Points\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='rp_streak',
        pattern=re.compile(r'\[(.*?)\] You get an additional (\d+) realm points due to your (.*?)\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='rp_parti',
        pattern=re.compile(r'\[(.*?)\] You get (\d+) realm points for reaching (.*?) Participation\!'),
        type_of_event='r',
        event_direction='$'),
    game_event(event='rp_depo',
        pattern=re.compile(r'\[(.*?)\] You get (\d+) realm points for depositing War Supplies\!'),
        type_of_event='r',
        event_direction='$'),
]

events_money = [
    game_event(event='m_cash',
        pattern=re.compile(r'\[(.*?)\] You receive (.*?)\.'),
        type_of_event='money',
        event_direction='+'),
    game_event(event='m_cash1',
        pattern=re.compile(r'\[(.*?)\] You pick up (.*?)\.'),
        type_of_event='money',
        event_direction='+'),
    game_event(event='m_share',
        pattern=re.compile(r'\[(.*?)\] Your share of the loot is (.*?)\.'),
        type_of_event='money',
        event_direction='+'),
    game_event(event='m_dep',
        pattern=re.compile(r'\[(.*?)\] You deposit (.*?) into the guild bank\.'),
        type_of_event='money',
        event_direction='-'),
    game_event(event='m_task',
        pattern=re.compile(r'\[(.*?)\] You recieve (.*?) for completing your task\.'),
        type_of_event='money',
        event_direction='+'),
    game_event(event='m_chest',
        pattern=re.compile(r'\[(.*?)\] You find a pouch filled with (.*?) coins in the supply chest\.'),
        type_of_event='money',
        event_direction='+'),
    game_event(event='m_sell',
        pattern=re.compile(r'\[(.*?)\] (.*?) gives you (.*?) for the (.*?)\.'),
        type_of_event='money',
        event_direction='+'),
    game_event(event='m_give',
        pattern=re.compile(r'\[(.*?)\] You give to ([A-Za-z ]+) (.*?)\.'),
        type_of_event='money',
        event_direction='-'),
    game_event(event='m_pay',
        pattern=re.compile(r'\[(.*?)\] You pay ([A-Za-z ]+) (.*?)\.'),
        type_of_event='money',
        event_direction='-'),
]

events_battlegroup = [
    game_event(event='bg_join',
        pattern=re.compile(r'\[(.*?)\] (.*?) has joined the battle group\.'),
        type_of_event='bg',
        event_direction='+'),
    game_event(event='bg_leave',
        pattern=re.compile(r'\[(.*?)\] (.*?) has left the battle group\.'),
        type_of_event='bg',
        event_direction='-'),
    game_event(event='bg_count',
        pattern=re.compile(r'\[(.*?)\] There are currently (\d+) members in your battlegroup\.'),
        type_of_event='bg',
        event_direction='='),
    game_event(event='bg_left',
        pattern=re.compile(r'\[(.*?)\] You leave (.*?) battle group\.'),
        type_of_event='bg',
        event_direction='^'),
    game_event(event='bg_new',
        pattern=re.compile(r'\[(.*?)\] You join (.*?) battle group\.'),
        type_of_event='bg',
        event_direction='*'),
]

class InvalidCookie(Exception):
    """Raised when Eden returns a 403 forbidden."""
    ...

class loot():
    """Track currency and convert money"""
    i = {
        'r': 0, 'b': 0,
        'p': 0, 'g': 0, 's': 0, 'c': 0,
    }

    def add_loot(self, loot_dir, loot_type, loot_data):
        if loot_type == 'money':
            money = loot_data[1]
            if len(loot_data) > 2:
                money = loot_data[2]

            self.add_money(money, loot_dir)
        else:
            money_amount = loot_data[1]
            if 'Place' in money_amount: money_amount = loot_data[2]
            self.i[loot_type] += int(money_amount)

    def add_money(self, money_text: str, loot_dir: str):
        try:
            for money in money_text.split(','):
                split_money = money.strip().split(' ')
        
                money_amount = int(split_money[0])
                _money_type = split_money[1]
                money_type = _money_type[:1]

                self.i[money_type] += money_amount if loot_dir == '+' else -money_amount
                self.convert()

        except Exception as e:
            print(f'add_money {e} ({money_text})')
        
    def convert(self):
        if self.i['p'] < 0 or self.i['g'] < 0 or self.i['s'] < 0:
            return

        self.i['s'] += self.i['c'] // 100
        self.i['g'] += self.i['s'] // 100
        self.i['p'] += self.i['g'] // 1000
        self.i['c'] %= 100
        self.i['s'] %= 100
        self.i['g'] %= 1000
    
    def get_items(self):
        return (
            self.i['r'], 
            self.i['b'], 
            self.i['p'], 
            self.i['g'], 
            self.i['s'], 
            self.i['c']
        )

if __name__ == '__main__':
    pass