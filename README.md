# Dark Age of Camelot Log Parser
RVR kill feed with player class information and realm coloring

## Features
- Filter kills by player, zone, or custom groups
- AI bot players have their own color, and can be filtered out to only show real players
- Search player stats using Eden Herald
- Track session realm point and bounty point gains
- Rank 12+ players are indicated by colored class name
- Show all keep/tower/relic captures
- Battlegroup logs for player count
- Automatically save previous log files

## Installing
_Python version is recommended but an exe is available_ (https://github.com/DaocNosey/DaocParse/releases/tag/v1.0.0)<br/>
- Download the zip file, and extract to any folder<br/>
![Download](https://i.imgur.com/FvRLdaU.png)
- Open command prompt and navigate to the folder (type `cd path/to/folder`)<br/>
- Install libraries from requirements.txt<br/>
`python -m pip install -r requirements.txt`<br/>
- Run DaocParse.py<br/>
- Eden website cookie and user-agent are required to pull data from Herald<br/>
[Cookie Information](#cookie)
- Turn on Dark Age of Camelot logging by typing /chatlog (chat.log file only updates when logging is toggled off)<br/>

> [!TIP]
> Make two macros with `/chatlog` and bind them to keys next to each other like `[ ]` keys. Daoc has a small cooldown on qbinds, but two different keys can be used instantly to turn logging off and back on.
  
## Commands
| Command  | Function |
| ------------ | ------------- |
| `name`       | Show kills from name  |
| `!name`      | Search name on Herald  |
| `.name`      | Get full Herald stats (LWRP, LWSK, duels)  |
| `@zone`      | Show kills from zone  |
| `#`          | Show all custom highlight groups  |
| `#id`        | Show specific custom highlight group by id  |
| `#id @zone`  | Show specific custom group kills in a certain zone  |
| `/n`         | Show last n number of kills  |
| `%`          | Toggle showing AI Bots  |
| `$`          | Show all tower/keep/relic captures  |
| `^`          | Display session RP, BP, money  |
| `-`          | Save the current position and size of the Daoc Parse window  |
| `+`          | Reset window position  |
| `*filename`  | Delete current log. Autosaves to `/saved_logs/{date}{filename}.log` |
| `>`          | Show all battlegroup leave/join messages and number of players in BG |
| `&`          | Update list of rank 12+ players |
| `<`          | Launch custom highlight group editor  |
| `?`          | Command list and information  |
##

### RVR Kill Feed
Shows all RVR kills with class information and coloring<br/>
Group members are shown in yellow to stand out<br/>
AI Bot players are colored magenta
![RVR Kills (Bots)](https://i.imgur.com/dVozaMm.png)

### RVR Kill Feed (Bots Removed)
Exclude AI Bot kills/deaths (% to toggle)
![RVR Kills (No Bots)](https://i.imgur.com/TiU7eS6.png)

### Player Filtering
Search for specific players
![Filter Player](https://i.imgur.com/Rlj6xqw.png)

### Zone Filtering
Search specific zones
![Filter Zone](https://i.imgur.com/E1BK2ZG.png)

### Custom Group Filtering
Create custom highlight groups for guild/group/friends
![Filter Group](https://i.imgur.com/Fiif4mz.png)

### Eden Herald Stats
Fetch player stats from Eden Herald
![Player Stats](https://i.imgur.com/j59zo0m.png)

### Eden Herald All Stats
Fetch full player stats from Eden Herald
![Full Stats](https://i.imgur.com/g8XBEPp.png)

### Currency Tracking
Realm points, bounty points, and money are tracked<br/>
![Currency Tracking](https://i.imgur.com/xebyOq5.png)

## Cookie
Eden Herald requires you to be logged in to pull data. Using your browsers cookie and user-agent allows you to access it.
- Open https://eden-daoc.net/herald and make sure you are logged in
- Press F12 to open developer tools
- Refresh the page
- Go to the Network tab
- Select Fetch/XHR, or search for proxy
- Click on any of the `proxy.php?compet`
- Find eden_daoc_sid (32 letters/numbers) and user-agent

![Cookie](https://i.imgur.com/aeLTQQV.png)
> [!WARNING]
> Do NOT share your eden_daoc_sid
  
