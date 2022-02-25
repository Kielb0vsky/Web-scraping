### Modules ###
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import pandas as pd
import csv
import requests
import re
from unidecode import unidecode
import time

### Class ###
class Player:
    def __init__(self, id, name, transfermarkt):
        self._id = id
        self._name = name
        self._tm = transfermarkt
        self._headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
           'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
           'Accept-Language':'pl'}

    def playerInfo(self, df):
        # ['ID', 'Name', 'Name in home country', 'Date of birth', 'Age', 'Height', 'Position', 
        #  'Foot', 'Player agent', 'Highest market value', 'Current value',
        #  'Current club', 'Joined', 'Contract expires']
        if self._tm == 'No link found':
            return
        bs = getPage(self._tm, self._headers)
        tab = bs.find('div', {'class':'info-table'}).find_all('span', {'class':'info-table__content'})
        info = list()
        info.append(self._id)
        info.append(bs.find('div', {'class':'dataName'}).find('h1', {'itemprop':'name'}).get_text())
        for i in range(0, len(tab)):
            tab[i] = tab[i].get_text(strip=True).replace(u'\xa0', u' ')
        if 'Name in home country:' in tab:
            info.append(tab[tab.index('Name in home country:')+1])
        else:
            info.append('-')
        if 'Date of birth:' in tab:
            info.append(tab[tab.index('Date of birth:')+1])
        else:
            info.append('-')
        if 'Age:' in tab:
            info.append(tab[tab.index('Age:')+1])
        else:
            info.append('-')
        if 'Height:' in tab:
            info.append(tab[tab.index('Height:')+1][:tab[tab.index('Height:')+1].find(' ')])
        else:
            info.append('-')
        try:
            pos = bs.find('div', {'class':'detail-position__box'}).find_all('dd', {'class':'detail-position__position'})
            posstr = ''
            for i in range(0, len(pos)):
                if i != len(pos) - 1:
                    posstr += pos[i].get_text(strip=True) + ', '
                else:
                    posstr += pos[i].get_text(strip=True)
            info.append(posstr)
        except AttributeError:
            if 'Position:' in tab:
                info.append(tab[tab.index('Position:')+1])
            else:
                info.append('-')
        if 'Foot:' in tab:
            info.append(tab[tab.index('Foot:')+1])
        else:
            info.append('-')
        if 'Player agent:' in tab:
            info.append(tab[tab.index('Player agent:')+1])
        else:
            info.append('-')
        try:
            highpricedate = bs.find('div', {'class':'auflistung'}).find('div', {'class':'zeile-unten'}).find('div', {'class':'right-td'}).find('span').get_text(strip=True)
            highprice = bs.find('div', {'class':'auflistung'}).find('div', {'class':'zeile-unten'}).find('div', {'class':'right-td'}).get_text(strip=True)
            info.append(highprice[1:highprice.find(highpricedate)])
        except AttributeError:
            info.append('-')
        try:
            currprice = bs.find('div', {'class':'auflistung'}).find('div', {'class':'zeile-oben'}).find('div', {'class':'right-td'}).get_text(strip=True)
            info.append(currprice[1::])
        except AttributeError:
            info.append('-')
        if 'Current club:' in tab:
            info.append(tab[tab.index('Current club:')+1])
        else:
            info.append('-')
        if 'Joined:' in tab:
            info.append(tab[tab.index('Joined:')+1])
        else:
            info.append('-')
        if 'Contract expires:' in tab:
            info.append(tab[tab.index('Contract expires:')+1])
        else:
            info.append('-')
        try:
            info.append(bs.find('div', {'id':'modal-1'}).find('div', {'id':'modal-1-content'}).find('img')['src'])
        except AttributeError:
            info.append('Placeholder')
        df.loc[len(df)] = info
        return

    def playerStats(self, df):
         #['ID', 'Season', 'Competition', 'Club', 'Appearances',
         # 'Points per match', 'Goals', 'Assists', 'Own goals'
         # 'Substitutions on', 'Substitutions off', 'Yellow cards',
         # 'Second yellow cards', 'Red cards', 'Penalty goals', 'Minutes per goal', 'Minutes played']
        if self._tm == 'No link found':
            return
        bs = getPage(self._tm.replace('profil', 'leistungsdatendetails'), self._headers)
        new_url = bs.find('div', {'class':'tm-tabs'}).find('a').next_sibling['href']
        bs = getPage('https://www.transfermarkt.com' + new_url,  self._headers)
        try:
            gk = bs.find('div', {'class':'dataBottom'}).find('div', {'class':'dataDaten'}).next_sibling.next_sibling.p.next_sibling.next_sibling.find('span', {'class':'dataValue'}).get_text(strip=True)
        except AttributeError:
            return
        if gk == 'Goalkeeper':
            return
        tab = bs.find('div', {'class':'grid-view'}).find('table', {'class':'items'}).find('tbody').find_all('tr')
        for row in tab:
            info = list()
            data = row.find_all('td')
            info.append(self._id)
            for i in range(0, len(data)):
                if i == 1 or i == 4:
                    continue
                if i == 3:
                    info.append(data[i].find('a')['title'])
                else:
                    if data[i].get_text(strip=True) == '-':
                        info.append(data[i].get_text(strip=True).replace('-', '0'))
                    else:
                        info.append(data[i].get_text(strip=True))
            info[5] = info[5].replace(".", ",")
            info[15] = info[15].replace("'", "")
            info[16] = info[16].replace("'", "")
            info[15] = info[15].replace(".", "")
            info[16] = info[16].replace(".", "")
            df.loc[len(df)] = info
        return

    def playerAbsence(self, df):
        # ['ID', 'Season', 'Injury/Absence/Suspension', 'From', 
        #  'Until', 'Days', 'Games missed']
        if self._tm == 'No link found':
            return
        bs = getPage(self._tm.replace('profil', 'verletzungen') + '/plus/1', self._headers)
        try:
            tab = bs.find('div', {'class':'responsive-table'}).find('div', {'class':'grid-view'}).find('table', {'class':'items'}).find('tbody').find_all('tr')
        except AttributeError:
            return
        nextpage = 1
        while nextpage != -1:
            for row in tab:
                info = list()
                data = row.find_all('td')
                info.append(self._id)
                for i in range(0, len(data)):
                    if i == 4:
                        days = data[i].get_text(strip=True)
                        info.append(days[:days.find(' ')])
                    else:
                        info.append(data[i].get_text(strip=True).replace('-', '0'))
                df.loc[len(df)] = info
            try:
                nextpage = bs.find('div', {'class':'pager'}).find('li', {'class':'tm-pagination__list-item tm-pagination__list-item--icon-next-page'}).find('a')['href']
                bs = getPage('https://www.transfermarkt.com' + nextpage, self._headers)
                tab = bs.find('div', {'class':'responsive-table'}).find('div', {'class':'grid-view'}).find('table', {'class':'items'}).find('tbody').find_all('tr')
            except AttributeError:
                nextpage = -1
        bs = getPage(self._tm.replace('profil', 'ausfaelle'), self._headers)
        try:
            tab = bs.find('div', {'class':'responsive-table'}).find('div', {'class':'grid-view'}).find('table', {'class':'items'}).find('tbody').find_all('tr')
        except AttributeError:
            return
        nextpage = 1
        while nextpage != -1:
            for row in tab:
                info = list()
                data = row.find_all('td')
                info.append(self._id)
                for i in range(0, len(data)):
                    if i == 2:
                        continue
                    if i == 5:
                        days = data[i].get_text(strip=True)
                        info.append(days[:days.find(' ')])
                    else:
                        info.append(data[i].get_text(strip=True).replace('?','0'))
                df.loc[len(df)] = info
            try:
                nextpage = bs.find('div', {'class':'pager'}).find('li', {'class':'tm-pagination__list-item tm-pagination__list-item--icon-next-page'}).find('a')['href']
                bs = getPage('https://www.transfermarkt.com' + nextpage, self._headers)
                tab = bs.find('div', {'class':'responsive-table'}).find('div', {'class':'grid-view'}).find('table', {'class':'items'}).find('tbody').find_all('tr')
            except AttributeError:
                nextpage = -1
        return

    def print(self):
        print('Player ID:\t', self._id)
        print('Player name:\t', self._name)
        print('Transfermarkt:\t', self._tm)


### Functions ###
def getPage(url, headers):
    try:
        req = requests.get(url, headers=headers)
    except requests.exceptions.RequestException:
        print("An error occured!")
        return None
    return BeautifulSoup(req.text, 'html.parser')

def getAbsoluteURL(baseUrl, source):
    if source.startswith('https://www.'):
        url = 'https://{}'.format(source[12:])
    elif source.startswith('https://'):
        url = source
    elif source.startswith('www.'):
        url = source[4:]
        url = 'https://{}'.format(source)
    elif source.startswith('/'):
        url = '{}{}'.format(baseUrl, source)
    else:
        url = '{}/{}'.format(baseUrl, source)
    if baseUrl not in url:
        return None
    return url

def getPlayersTM(csv, added, df):   #Function for fiding link to Transfermarkt profile of players
    session = requests.Session()
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
           'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
           'Accept-Language':'pl'}
    players = pd.read_csv(csv, delimiter=';')
    players = players.drop_duplicates(['Player Name','Team Name'])[['Player Name','Team Name']]
    try:
        db = pd.read_csv(added, delimiter=';', encoding='cp1250')
    except FileNotFoundError:
        player_cols = ['ID', 'Player Name', 'Team Name', 'Transfermarkt Link']
        db = pd.DataFrame(columns = player_cols)
    for i in range(0, len(players)):
        if players['Player Name'].iloc[i] in db['Player Name'].unique():
            print('Player num. {}:\tPlayer {} already added to database\n'.format(i, players['Player Name'].iloc[i]))
            idx = db['Player Name'].tolist()
            idx = idx.index(players['Player Name'].iloc[i])
            temp = db.iloc[idx].tolist()[1:]
            df.loc[len(df)] = [i, temp[0], temp[1], temp[2]]
            continue
        print('Player num. {}:\t{}'.format(i, players['Player Name'].iloc[i]))
        search = getPage('https://www.bing.com/search?q={}+{}+transfermarkt'.format(players['Player Name'].iloc[i].replace(' ','+').lower(), players['Team Name'].iloc[i].replace(' ','+').lower()), headers)
        try:
            search = search.find('ol', {'id':'b_results'}).find_all('li', {'class':'b_algo'})
        except AttributeError:
            print('Error! Internet connection lost')
            return 1
        for k in range(0,len(search)):
            if str(search[k].find('a')['href']).find('/profil/spieler/') != -1:
                search = search[k].find('a')['href']
                break
            if k == len(search)-1:
                print("No link found - Trying different approach")
                search = 'No link found'
                site_club = getPage('https://www.bing.com/search?q={}+transfermarkt'.format(players['Team Name'].iloc[i].replace(' ','+').lower()), headers)
                try:
                    site_club = site_club.find('ol', {'id':'b_results'}).find_all('li', {'class':'b_algo'})
                except AttributeError:
                    print('Error! Internet connection lost')
                    return 1
                for z in range(0,len(site_club)):
                    if str(site_club[z].find('a')['href']).find('/startseite/verein/') != -1:
                        surname = players['Player Name'].iloc[i]
                        surname = unidecode(surname[:surname.find(' ')])
                        club = getPage(site_club[z].find('a')['href'].replace('.pl','.com'), headers)
                        names = club.find('table',{'class':'items'}).find('tbody').find_all('tr', {'class':'odd'})
                        for t in range(0, len(names)):
                            temp = names[t].find('td', {'class':'posrela'}).find('table', {'class':'inline-table'}).find('span').find('a')['title']
                            if unidecode(temp).find(surname) != -1:
                                search = 'https://www.transfermarkt.com'+names[t].find('td', {'class':'posrela'}).find('table', {'class':'inline-table'}).find('span',{'class':'hide-for-small'}).find('a')['href']
                                break
                        names = club.find('table',{'class':'items'}).find('tbody').find_all('tr', {'class':'even'})
                        for t in range(0, len(names)):
                            temp = names[t].find('td', {'class':'posrela'}).find('table', {'class':'inline-table'}).find('span').find('a')['title']
                            if unidecode(temp).find(surname) != -1:
                                search = 'https://www.transfermarkt.com'+names[t].find('td', {'class':'posrela'}).find('table', {'class':'inline-table'}).find('span',{'class':'hide-for-small'}).find('a')['href']
                                break
                        print('No link found - Searching for transfer')
                        club = site_club[z].find('a')['href'].replace('.pl','.com')
                        transfers = getPage(club.replace('startseite','alletransfers'), headers)
                        names = transfers.find_all('td', {'class':'hauptlink'})
                        for u in range(0,len(names)):
                            try:
                                if unidecode(names[u].find('a')['title']).find(surname) != -1:
                                    search = 'https://www.transfermarkt.com'+names[u].find('a')['href']
                                    break
                                if u == len(names)-1:
                                    search = None
                            except TypeError:
                                continue
                        break
        print(i, players['Player Name'].iloc[i], players['Team Name'].iloc[i], search, '\n')
        df.loc[len(df)] = [i, players['Player Name'].iloc[i], players['Team Name'].iloc[i], search.replace('.pl','.com')]
    return 0

### MAIN ###
session = requests.Session()
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
           'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
           'Accept-Language':'pl'}

playerInfo_cols = ['ID', 'Name', 'Name in home country', 'Date of birth', 'Age', 'Height (m)', 'Position', 
                   'Foot', 'Player agent', 'Highest market value (Euro)', 'Current value (Euro)',
                   'Current club', 'Joined', 'Contract expires', 'Image']
playerInfo = pd.DataFrame(columns = playerInfo_cols)
playerStats_cols = ['ID', 'Season', 'Competition', 'Club', 'Appearances',
                    'Points per match', 'Goals', 'Assists', 'Own goals',
                    'Substitutions on', 'Substitutions off', 'Yellow cards',
                    'Second yellow cards', 'Red cards', 'Penalty goals', 'Minutes per goal', 'Minutes played']
playerStats = pd.DataFrame(columns = playerStats_cols)
playerAbsence_cols = ['ID', 'Season', 'Injury/Absence/Suspension', 'From', 
                      'Until', 'Days', 'Games missed']
playerAbsence = pd.DataFrame(columns = playerAbsence_cols)
player_cols = ['ID', 'Player Name', 'Team Name', 'Transfermarkt Link']
player = pd.DataFrame(columns = player_cols)

t0 = time.time()
flag = getPlayersTM(r'players.csv', r'scouting_players.csv', player)
player.to_csv('scouting_players.csv', sep = ';', index=False, encoding='cp1250')
while flag != 0:
    flag = getPlayersTM(r'players.csv', r'scouting_players.csv', player)
    player.to_csv('scouting_players.csv', sep = ';', index=False, encoding='cp1250')
t1 = time.time()
print('\nTime spent on finding Transfermarkt links:\t', t1-t0, 's\n\n')

t0 = time.time()
p = []
for i in range(0, len(player)):
    p.append(Player(player['ID'].iloc[i], player['Player Name'].iloc[i], player['Transfermarkt Link'].iloc[i]))

for player in p:
    player.print()
    player.playerInfo(playerInfo)
    player.playerStats(playerStats)
    player.playerAbsence(playerAbsence)
    playerInfo.to_csv('scouting_playersInfo.csv', sep = ';', index=False, encoding='utf8')
    playerStats.to_csv('scouting_playersStats.csv', sep = ';', index=False, encoding='utf8')
    playerAbsence.to_csv('scouting_playersAbsence.csv', sep = ';', index=False, encoding='utf8')
t1 = time.time()
print('\n\nTime spent on gathering data from Transfermarkt:\t', t1-t0, 's')