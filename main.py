__version__ = '1.05' # Changed name to Naval Assault V1 and Changed Icon
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.dropdown import DropDown
from kivy.core.audio import SoundLoader
from radarGauge import radar
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.utils import platform
from hitMark import hitBang
from radarHitMark import hitPin
from shipPlacement import ship
import time, random, socket, threading, json

global i
i = 0
global horText
horText = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
global verText
verText = [' ', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
global occupied
occupied = []
global usrFire
usrFire = 0
global board
global ships
global seaman
global captain
global admiral
global chkRank
global multiplayer
global ip
global conn
multiplayer = False
seaman = False
captain = False
admiral = False
chkRank = False

# Socket Information to be used in any needed class
global address
global player_ID
global player_start
global client
global socketServerErr
global server
global serverErr
global player1_conn
global player2_conn
global player1_ready
global player2_ready
player1_ready = ''
player2_ready = ''
player1_conn = ''
player2_conn = ''
player_ID = ''
serverErr = ''
socketServerErr = ''
client = None
server = None
max_size = 2048
player_ID = 'player1:'


'''Note that the pyjnius calls only works correctly in the main thread.
Calling autoclass in the other screen classes dont work. Three day to
figure this out. :-('''


def int_to_ip(ipnum):
    oc1 = int(ipnum / 16777216) % 256
    oc2 = int(ipnum / 65536) % 256
    oc3 = int(ipnum / 256) % 256
    oc4 = int(ipnum) % 256
    return '%d.%d.%d.%d' %(oc4, oc3, oc2, oc1)


if platform == 'android':
    from jnius import autoclass
    Activity = autoclass('android.app.Activity')
    ConnectivityManager = autoclass('android.net.ConnectivityManager')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    SystemProperties = autoclass('android.os.SystemProperties')
    Context = autoclass('android.content.Context')
    con_mgr = PythonActivity.mActivity.getSystemService(Context.CONNECTIVITY_SERVICE)
    conn = con_mgr.getNetworkInfo(ConnectivityManager.TYPE_WIFI).isConnectedOrConnecting()
    wifi_manager = PythonActivity.mActivity.getSystemService(Context.WIFI_SERVICE)
    ip = wifi_manager.getConnectionInfo()
    ip = ip.getIpAddress()
    ip = int_to_ip(int(ip))
    if ip == '0.0.0.0':
        conn = True


def closeAndClear():
    # Clear and close the current connection to the server
    global client
    global player_ID
    global player_start
    global player1_conn
    global player2_conn
    global player1_ready
    global player2_ready
    player1_ready = ''
    player2_ready = ''
    player_ID = ''
    player_start = ''
    player1_conn = ''
    player2_conn = ''
    client.close()


def serverTread(ip, port):
    global player1_conn
    global player2_conn
    global player1_ready
    global player2_ready
    global killServer
    global player1
    global player2
    global test
    player1 = None
    player2 = None
    player1_Is_Rdy = False
    player2_Is_Rdy = False
    playersIn = False
    address = (ip, int(port))
    max_size = 2048
    player_list = ['player1:', 'player2:']
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(address)
        server.listen(3)
    except socket.error as msg:
        global socketServerErr
        socketServerErr = msg
        print 'socket error says: ' + str(msg)
        exit(0)
    try:
        player1, addr1 = server.accept()
        player1_conn = 'player1 connected to: ' + str(addr1)
        print player1_conn
        player1.send('player1:')
        test, addr2 = server.accept()
        test.close()
        player2, addr3 = server.accept()
        player2_conn = 'player2 connected to: ' + str(addr3)
        print player2_conn
        player2.send('player2:')
        player1_ready = player1.recv(max_size)
        print player1_ready
        player2_ready = player2.recv(max_size)
        print player2_ready
        if player1_ready == 'player1:Ready':
            player1_Is_Rdy = True
        if player2_ready == 'player2:Ready':
            player2_Is_Rdy = True
        if player1_Is_Rdy&player2_Is_Rdy:
            print 'Players Ready'
            first_Player_is = player_list[random.randint(0,1)]
            print first_Player_is + ' starting'
            player1.send(first_Player_is)
            player2.send(first_Player_is)

        #Exchange the players ship coordinates with each other
        player1_Ships = json.loads(player1.recv(max_size))
        player2.send(json.dumps(player1_Ships))
        player2_Ships = json.loads(player2.recv(max_size))
        player1.send(json.dumps(player2_Ships))

    except Exception as msg:
        print 'Player connection says: ' + str(msg)

    try:
        while True:
            if first_Player_is == 'player1:':

                player1_data = player1.recv(max_size)
                player1.send('wait')
                player2.send(player1_data)
                print player1_data

                player2_data = player2.recv(max_size)
                player2.send('wait')
                player1.send(player2_data)
                print player2_data
            else:
                player2_data = player2.recv(max_size)
                player2.send('wait')
                player1.send(player2_data)
                print player2_data

                player1_data = player1.recv(max_size)
                player1.send('wait')
                player2.send(player1_data)
                print player1_data
    except Exception as msg:
        print msg
        player1.close()
        player2.close()


def startServer(ip, port):
    serverStart = threading.Thread(target=serverTread, args=(ip, port))
    serverStart.deamon = True
    serverStart.start()


def getScoreCards(cardName, storeName):
    if cardName not in storeName:
        dictName = {}
        dictName['wins'] = 0
        dictName['losses'] = 0
        dictName['number_shots'] = 0
        dictName['lowest_shots'] = 100
        storeName.put(cardName, scores=dictName)
    else:
        dictName = storeName.get(cardName)['scores']
    return dictName


def popScoreScards():
    global scoresSeaman
    global scoresCaptain
    global scoresAdmiral
    global scoresMulti
    global store
    scoresSeaman = getScoreCards('Seaman', store)
    scoresCaptain = getScoreCards('Captain', store)
    scoresAdmiral = getScoreCards('Admiral', store)
    scoresMulti = getScoreCards('Multi', store)


    store.put("Seaman", scores=scoresSeaman)
    store.put("Captain", scores=scoresCaptain)
    store.put("Admiral", scores=scoresAdmiral)
    store.put("Multi", scores=scoresMulti)



def computer_place_ships(board, ships):

    for ship in ships.keys():
        #genreate random coordinates and validate the postion
        valid = False
        while(not valid):
            x = random.randint(1, 10) - 1
            y = random.randint(1, 10) - 1
            o = random.randint(0, 1)
            if o == 0:
                ori = "v"
            else:
                ori = "h"
            valid = validate(board, ships[ship], x, y, ori)
        #place the ship
        board = place_ship(board, ships[ship], ship[0], ori, x, y)
    return board


def place_ship(board, ship, s, ori, x, y):
    #place ship based on orientation
    if ori == "v":
        for i in range(ship):
            board[x + i][y] = s
    elif ori == "h":
        for i in range(ship):
            board[x][y + i] = s
    return board


def validate(board, ship, x, y, ori):
    #validate the ship can be placed at given coordinates
    if ori == "v" and x + ship > 10:
        return False
    elif ori == "h" and y + ship > 10:
        return False
    else:
        if ori == "v":
            for i in range(ship):
                if board[x + i][y] != -1:
                    return False
        elif ori == "h":
            for i in range(ship):
                if board[x][y + i] != -1:
                    return False

    return True


class CreditScreen(Screen):
    def __init__(self, **kwargs):
        super(CreditScreen, self).__init__(**kwargs)
        self.ids.creditView.bind(minimum_height=self.creditView.setter('height'))

    def newGame(self):
        global sm
        global multiplayer
        if multiplayer:
            sm.transition.direction = 'left'
            sm.current = 'multi'
        else:
            sm.transition.direction = 'left'
            sm.current = 'game'


class HelpScreen(Screen):
    def __init__(self, **kwargs):
        super(HelpScreen, self).__init__(**kwargs)

    def newGame(self):
        global sm
        global multiplayer
        if multiplayer:
            sm.transition.direction = 'left'
            sm.current = 'multi'
        else:
            sm.transition.direction = 'left'
            sm.current = 'game'

    def showCredits(self):
        global sm
        sm.transition.direction = 'right'
        sm.current = 'credits'

    def showSonar(self):
        global sm
        sm.transition.direction = 'right'
        sm.current = 'sonar'

    def battleMatch(self):
        global sm
        sm.transition.direction = 'right'
        sm.current = 'battle'

    def showPlacement(self):
        global sm
        sm.transition.direction = 'right'
        sm.current = 'placement'


class PlacementHelp(Screen):
    def __init__(self, **kwargs):
        super(PlacementHelp, self).__init__(**kwargs)
        self.ids.placeView.bind(minimum_height=self.placeView.setter('height'))
        self.figureNo = 0

    def newGame(self):
        global sm
        global multiplayer
        if multiplayer:
            sm.transition.direction = 'left'
            sm.current = 'multi'
        else:
            sm.transition.direction = 'left'
            sm.current = 'game'

    def lastFigure(self):
        if self.figureNo > 0:
            self.figureNo -= 1
            self.dispFigure(self.figureNo)

    def nextFigure(self):
        if self.figureNo < 2:
            self.figureNo += 1
            self.dispFigure(self.figureNo)

    def dispFigure(self, number):
        if number == 0:
            self.ids.helpFigure.source = 'placeHelp1.png'
        if number == 1:
            self.ids.helpFigure.source = 'placeHelp2.png'
        if number == 2:
            self.ids.helpFigure.source = 'placeHelp3.png'


class SonarGridHelp(Screen):
    def __init__(self, **kwargs):
        super(SonarGridHelp, self).__init__(**kwargs)
        self.ids.helpView.bind(minimum_height=self.helpView.setter('height'))

    def newGame(self):
        global sm
        global multiplayer
        if multiplayer:
            sm.transition.direction = 'left'
            sm.current = 'multi'
        else:
            sm.transition.direction = 'left'
            sm.current = 'game'

class BattleMatchHelp(Screen):
    def __init__(self, **kwargs):
        super(BattleMatchHelp, self).__init__(**kwargs)

    def newGame(self):
        global sm
        global multiplayer
        if multiplayer:
            sm.transition.direction = 'left'
            sm.current = 'multi'
        else:
            sm.transition.direction = 'left'
            sm.current = 'game'

class MultiPlayerGame(Screen):

    def __init__(self, **kwargs):
        super(MultiPlayerGame, self).__init__(**kwargs)
        self.serverTimer = Clock.create_trigger(self.goServe, 0.25)
        self.clientTimer = Clock.create_trigger(self.goClient, 1)
        self.gameTimer = Clock.create_trigger(self.newGame, 0.5)
        self.joinHost = Clock.create_trigger(self.joinaHost, 0.25)
        self.iamServer = False
        self.scanedIp = None
        self.hostIP = '0.0.0.0'
        self.gamePort = str(6789)
        self.ids.p1Conn.text = ''
        self.ids.p2Conn.text = ''
        self.ids.errMsg.text = ''
        self.ids.hostConn.text = ''
        self.droidIP = ''
        self.iterating = 0
        if platform == 'android':
            global ip
            self.hostIP = ip
            if ip == '0.0.0.0':
                self.hostIP = '192.168.43.1'
        else:
            import os
            f = os.popen('ifconfig wlan0 | grep inet', 'rt').read().replace(':', ' ').split(' ')
            ip = os.popen('hostname -I', 'rt').read().split(' ')
            for items in range(0, len(ip)-1):
                testIP = ip[items] in f
                if testIP:
                    ip = ip[items]
                    self.hostIP = ip

    def createClient(self, ip, port):
        max_size = 2048
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((ip, int(port)))
            self.ids.p1Conn.text = 'Host game found.'
            self.scanedIp = ip
        except Exception as msg:
            print msg

    def iterateClient(self, ip, port):
        global gameHostIp
        getIp = ip.split('.')
        print 'Iteration loop'
        for i in range(1, 255):
            newIp = '%d.%d.%d.%d' %(int(getIp[0]), int(getIp[1]), int(getIp[2]), i)
            findIp = threading.Thread(target=self.createClient, args=(newIp, port)).start()

    def toggleFlopHost(self):
        self.ids.p1Conn.text = ''
        self.ids.p2Conn.text = ''
        self.ids.hostConn.text = ''
        self.ids.errMsg.text = ''
        if self.ids.hostGame.state == 'down':
            self.ids.joinGame.state = 'normal'
            self.ids.gameStarter.text = 'Create Game'
        else:
            self.ids.gameStarter.text = 'Select Option'

    def toggleFlopJoin(self):
        self.ids.p1Conn.text = ''
        self.ids.p2Conn.text = ''
        self.ids.hostConn.text = ''
        self.ids.errMsg.text = ''
        if self.ids.joinGame.state == 'down':
            self.ids.hostGame.state = 'normal'
            self.ids.gameStarter.text = 'Join Game'
        else:
            self.ids.gameStarter.text = 'Select Option'


    def lanRecv(self):
        global client
        global player_ID
        global player_start
        global max_size
        global server
        global player1_conn
        global player2_conn
        try:
            player_ID = client.recv(max_size)
            client.send(player_ID + 'Ready')
            player_start = client.recv(max_size)
            print player_start
        except Exception as msg:
            print 'lanRecv Thread says: ' + str(msg)
            client.close()

    def killServer(self):
        dummy_test = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dummy_test.connect((self.hostIP, int(self.gamePort)))
        dummy_p2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dummy_p2.connect((self.hostIP, int(self.gamePort)))
        dummy_p2.send('player2:Ready')
        time.sleep(0.5)
        closeAndClear()
        self.ids.scanTime.value = 0
        self.ids.hostConn.text = ''
        self.ids.p1Conn.text = ''
        self.ids.p2Conn.text = ''
        self.ids.errMsg.text = ''
        self.clientTimer.cancel()

    def goClient(self, dt):
        global client
        global player_ID
        global player_start
        global max_size
        global server
        global player1
        global test
        global player2
        global player1_conn
        global player2_conn
        try:
            if self.iamServer:
                if player_ID == '':
                    self.clientTimer()
                else:
                    self.ids.p1Conn.text = str(player1_conn)
                    self.ids.p2Conn.text = 'Waiting for player2 to join.'
                    if player2_conn == '':
                        self.iterating += 1
                        self.ids.scanTime.value = self.iterating
                        if self.iterating > 20:
                            self.ids.hostConn.text = 'Host game timed out.'
                            self.ids.p1Conn.text = 'Closing host service.'
                            self.ids.p2Conn.text = ''
                            if self.iterating > 25:
                                self.killServer()
                                return
                        self.clientTimer()
                    else:
                        if self.iterating < 30:
                            self.ids.scanTime.value = 0
                            self.iterating = 0
                            self.ids.p2Conn.text = str(player2_conn)
                        self.gameTimer()
            else:
                self.ids.p2Conn.text = 'Connecting to host ' + self.scanedIp
                self.gameTimer()
        except socket.error as msg:
            self.ids.errMsg.text = str(msg)
            global server
            if server != None:
                server.shutdown(2)

    def serverJoin(self):
        global client
        global player_ID
        global player_start
        global max_size
        global socketServerErr
        if socketServerErr == '':
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((self.hostIP, int(self.gamePort)))
                self.ids.errMsg.text = 'No Error Reported'
                self.clientTimer()
                self.lanService = threading.Thread(target=self.lanRecv).start()
            except socket.error as msg:
                self.ids.errMsg.text = str(msg)
                global server
                if server != None:
                    server.shutdown(2)
        else:
            self.ids.errMsg.text = str(socketServerErr)


    def joinaHost(self, dt):
        global client
        global player_ID
        global player_start
        global max_size
        global socketServerErr
        global gameHostIp
        if socketServerErr == '':
            try:
                if self.scanedIp == None:
                    self.iterating += 1
                    self.ids.scanTime.value = self.iterating
                    if not self.iamServer:
                        if self.iterating > 10:
                            self.ids.hostConn.text = 'Timed out.'
                            self.ids.p1Conn.text = 'Sorry, no host found.'
                            self.joinHost.cancel()
                            self.iterating = 0
                            self.ids.scanTime.value = 0
                            return
                    self.joinHost()
                else:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect((self.scanedIp, int(self.gamePort)))
                    self.ids.errMsg.text = 'No Error Reported'
                    self.clientTimer()
                    self.joinHost.cancel()
                    self.lanService = threading.Thread(target=self.lanRecv).start()
            except socket.error as msg:
                self.ids.hostConn.text = 'Connection failed, '
                self.ids.p1Conn.text = ' Check that host game is running.'
                self.ids.errMsg.text = str(msg)
                global server
                if server != None:
                    server.shutdown(2)
        else:
            self.ids.errMsg.text = str(socketServerErr)


    def goServe(self, dt):
        self.serverJoin()

    def createGame(self):
        #global client
        global player_ID
        global player_start
        global max_size
        if self.ids.gameStarter.text == 'Create Game':
            self.ids.hostConn.text = 'Creating service'
            startServer(self.hostIP, self.gamePort)
            self.iamServer = True
            self.ids.scanTime.max = 25
            self.iterating = 0
            self.clientTimer.cancel()
            self.serverTimer()
        if self.ids.gameStarter.text == 'Join Game':
            self.iterating = 0
            self.iamServer = False
            self.ids.scanTime.max = 10
            self.ids.hostConn.text = 'Scanning for host...'
            self.ids.errMsg.txt = ''
            self.ids.p1Conn.text = ''
            self.iterateClient(self.hostIP, self.gamePort)
            self.joinHost()

    def closeGame(self):
        global client
        self.killServer()

    def newGame(self, dt):
        global sm
        sm.transition.direction = 'up'
        sm.current = 'game'
        self.ids.p1Conn.text = ''
        self.ids.p2Conn.text = ''
        self.ids.errMsg.text = ''
        self.ids.hostConn.text = ''

    def gotoMenu(self):
        global sm
        global server
        global client
        global multiplayer
        global player1
        global player2
        try:
            self.closeGame()
            multiplayer = False
            self.ids.p1Conn.text = ''
            self.ids.p2Conn.text = ''
            self.ids.hostConn.text = ''
            self.ids.errMsg.text = ''
        except Exception as msg:
            print msg
            sm.transition.direction = 'up'
            sm.current = 'menu'
            self.ids.p1Conn.text = ''
            self.ids.p2Conn.text = ''
            self.ids.hostConn.text = ''
            self.ids.errMsg.text = ''
        sm.transition.direction = 'up'
        sm.current = 'menu'

    def gotoHelp(self):
        global sm
        sm.transition.direction = 'up'
        sm.current = 'battle'



class SelectLevel(Screen):
    global conn
    def __init__(self, **kwargs):
        super(SelectLevel, self).__init__(**kwargs)
        self.ocean = SoundLoader.load('ocean.wav')
        self.ocean.loop = True
        self.loadTimer = Clock.create_trigger(self.newGame, 0.5)
        self.ocean.play()
        self.ids.Version.text = 'Naval Assault ' + str(__version__)
        if platform == 'android':
            if conn:
                self.ids.bM.disabled = False
            else:
                self.ids.bM.disabled = True

    def newGame(self):
        global sm
        sm.transition.direction = 'up'
        sm.current = 'game'

    def multiGame(self):
        global sm
        sm.transition.direction = 'down'
        sm.current = 'multi'

    def startSeaman(self):
        global seaman
        global captain
        global admiral
        global multiplayer
        multiplayer = False
        seaman = True
        captain = False
        admiral = False
        self.newGame()

    def startCaptain(self):
        global seaman
        global captain
        global admiral
        global multiplayer
        multiplayer = False
        seaman = False
        captain = True
        admiral = False
        self.newGame()

    def startAdmiral(self):
        global seaman
        global captain
        global admiral
        global multiplayer
        multiplayer = False
        seaman = False
        captain = False
        admiral = True
        self.newGame()

    def startMulti(self):
        global seaman
        global captain
        global admiral
        global multiplayer
        multiplayer = True
        seaman = False
        captain = False
        admiral = False
        self.multiGame()


class LoseGameDialog(Screen):
    def __init__(self, **kwargs):
        super(LoseGameDialog, self).__init__(**kwargs)
        self.loseTimer = Clock.create_trigger(self.newGame, 0.5)
        self.updateScore = Clock.create_trigger(self.showScoreCard, 0.2)
        self.updateScore()

    def showScoreCard(self, dt):
        global sm
        global store
        if sm.current == 'lose':
            #Seaman Stats
            self.ids.seamanWin.text = str(store.get('Seaman')['scores']['wins'])
            self.ids.seamanLose.text = str(store.get('Seaman')['scores']['losses'])
            self.ids.seamanShotsNow.text = str(store.get('Seaman')['scores']['number_shots'])
            self.ids.seamanShotsLeast.text = str(store.get('Seaman')['scores']['lowest_shots'])

            #Captain Stats
            self.ids.captainWin.text = str(store.get('Captain')['scores']['wins'])
            self.ids.captainLose.text = str(store.get('Captain')['scores']['losses'])
            self.ids.captainShotsNow.text = str(store.get('Captain')['scores']['number_shots'])
            self.ids.captainShotsLeast.text = str(store.get('Captain')['scores']['lowest_shots'])

            #Admiral Stats
            self.ids.admiralWin.text = str(store.get('Admiral')['scores']['wins'])
            self.ids.admiralLose.text = str(store.get('Admiral')['scores']['losses'])
            self.ids.admiralShotsNow.text = str(store.get('Admiral')['scores']['number_shots'])
            self.ids.admiralShotsLeast.text = str(store.get('Admiral')['scores']['lowest_shots'])

            #Multiplayer Stats
            self.ids.multiWin.text = str(store.get('Multi')['scores']['wins'])
            self.ids.multiLose.text = str(store.get('Multi')['scores']['losses'])
            self.ids.multiShotsNow.text = str(store.get('Multi')['scores']['number_shots'])
            self.ids.multiShotsLeast.text = str(store.get('Multi')['scores']['lowest_shots'])
        self.updateScore()



    def newGame(self):
        global sm
        global multiplayer
        if multiplayer:
            sm.transition.direction = 'left'
            sm.current = 'multi'
        else:
            sm.transition.direction = 'left'
            sm.current = 'game'

    def startNew(self):
        self.newGame()


class WinGameDialog(Screen):
    def __init__(self, **kwargs):
        super(WinGameDialog, self).__init__(**kwargs)
        self.winTimer = Clock.create_trigger(self.newGame, 0.5)
        self.updateScore = Clock.create_trigger(self.showScoreCard, 0.2)
        self.updateScore()

    def showScoreCard(self, dt):
        global sm
        global store
        if sm.current == 'win':
            #Seaman Stats
            self.ids.seamanWin.text = str(store.get('Seaman')['scores']['wins'])
            self.ids.seamanLose.text = str(store.get('Seaman')['scores']['losses'])
            self.ids.seamanShotsNow.text = str(store.get('Seaman')['scores']['number_shots'])
            self.ids.seamanShotsLeast.text = str(store.get('Seaman')['scores']['lowest_shots'])

            #Captain Stats
            self.ids.captainWin.text = str(store.get('Captain')['scores']['wins'])
            self.ids.captainLose.text = str(store.get('Captain')['scores']['losses'])
            self.ids.captainShotsNow.text = str(store.get('Captain')['scores']['number_shots'])
            self.ids.captainShotsLeast.text = str(store.get('Captain')['scores']['lowest_shots'])

            #Admiral Stats
            self.ids.admiralWin.text = str(store.get('Admiral')['scores']['wins'])
            self.ids.admiralLose.text = str(store.get('Admiral')['scores']['losses'])
            self.ids.admiralShotsNow.text = str(store.get('Admiral')['scores']['number_shots'])
            self.ids.admiralShotsLeast.text = str(store.get('Admiral')['scores']['lowest_shots'])

            #Multiplayer Stats
            self.ids.multiWin.text = str(store.get('Multi')['scores']['wins'])
            self.ids.multiLose.text = str(store.get('Multi')['scores']['losses'])
            self.ids.multiShotsNow.text = str(store.get('Multi')['scores']['number_shots'])
            self.ids.multiShotsLeast.text = str(store.get('Multi')['scores']['lowest_shots'])
        self.updateScore()

    def newGame(self):
        global sm
        global multiplayer
        if multiplayer:
            sm.transition.direction = 'left'
            sm.current = 'multi'
        else:
            sm.transition.direction = 'left'
            sm.current = 'game'

    def startNew(self):
        self.newGame()


class rootScreen(Screen):

    def __init__(self, **kwargs):
        super(rootScreen, self).__init__(**kwargs)
        global myRadar
        self.playerWon = False
        self.resetGame()

    def resetGame(self):
        global occupied
        global admiral
        global seaman
        global captain
        global multiplayer
        global player_start
        global player_ID
        occupied = []
        global usrFire
        usrFire = 0
        self.itsDone = False
        self.playerNoShots = 0
        self.ids.selectShip.text = 'Place Ship'
        self.ids.cpuInfo.text = 'wait'
        self.ids.usrInfo.text = ''
        self.plocker = SoundLoader.load('splash.wav')
        self.banger = SoundLoader.load('bang.wav')
        self.bomb = SoundLoader.load('bomb.wav')
        self.sinker = SoundLoader.load('warning.wav')
        self.beep = SoundLoader.load('beep.wav')
        self.victory = SoundLoader.load('Victory.wav')
        self.hitOnShip = False
        self.sonarping = SoundLoader.load('sonarping.wav')
        self.expert = []
        self.sweepTimer = Clock.create_trigger(self.updateRadar, 0.01)
        self.menuTimer = Clock.create_trigger(self.gotoMenu, 0.5)
        self.playerWin = Clock.create_trigger(self.YouWin, 1)
        self.playerLose = Clock.create_trigger(self.YouLose, 0.5)
        self.multiPlaceDone = Clock.create_trigger(self.mutliPlace, 1)
        self.recvTimer = Clock.create_trigger(self.multiShot, 0.5)
        self.hangOn = Clock.create_trigger(self.hangForReceive, 0.05)
        self.ids.radarScreen.bind(size=self._update_LayoutSize)
        self.ai_cor = []
        self.playerScore = {}
        self.computerScore = {}
        self.shipbtn = {}
        self.firebtn = {}
        self.degSweep = {}
        self.splash = {}
        self.fireMark = {}
        self.bubbles = {}
        self.cpufire = {}
        self.myShips = {}
        self.myShipCoor = {}
        self.cpuCoor = {}
        self.ShipMenu = {}
        self.sunkenShips = {}
        self.mySunkenShips = {}
        self.cpuOccupation = []
        self.shipTypes = ['Carrier(5)',
                    'Battleship(4)',
                    'Submarine(3)',
                    'Destroyer(3)',
                    'Patrolboat(2)']
        self.ShipList = ['btnCarrier_1.png', 'btnBattleship.png', 'btnSubmarine.png', 'btnDestroyer.png', 'btnPatrolboat.png']
        self.dropdown = DropDown()
        for setShip in range(0, 5):
            self.ShipMenu[self.shipTypes[setShip]] = self.populateMenu(setShip)
            self.dropdown.add_widget(self.ShipMenu[self.shipTypes[setShip]])
        self.ids.selectShip.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select = lambda instance, x: setattr(self.ids.selectShip, 'text', x))

        self.ids.selectShip.values = self.shipTypes
        self.myShips['Carrier'] = ship(file_ship='Carrier_1.png')
        self.myShips['Battleship'] = ship(file_ship='Battleship.png')
        self.myShips['Submarine'] = ship(file_ship='Submarine.png')
        self.myShips['Destroyer'] = ship(file_ship='Destroyer.png')
        self.myShips['Patrolboat'] = ship(file_ship='Patrolboat.png')
        self.sunkenShips['Carrier'] = ship(file_ship='sunkCarrier_1.png')
        self.sunkenShips['Submarine'] = ship(file_ship='sunkSubmarine.png')
        self.sunkenShips['Battleship'] = ship(file_ship='sunkBattleship.png')
        self.sunkenShips['Destroyer'] = ship(file_ship='sunkDestroyer.png')
        self.sunkenShips['Patrolboat'] = ship(file_ship='sunkPatrolboat.png')
        self.mySunkenShips['Carrier'] = ship(file_ship ='mysunkCarrier.png')
        self.mySunkenShips['Battleship'] = ship(file_ship='mysunkBattleship.png')
        self.mySunkenShips['Submarine'] = ship(file_ship='mysunkSubmarine.png')
        self.mySunkenShips['Destroyer'] = ship(file_ship='mysunkDestroyer.png')
        self.mySunkenShips['Patrolboat'] = ship(file_ship='mysunkPatrolboat.png')
        self.cpuCoor['Carrier'] = []
        self.cpuCoor['Battleship'] = []
        self.cpuCoor['Submarine'] = []
        self.cpuCoor['Destroyer'] = []
        self.cpuCoor['Patrolboat'] = []
        self.playerScore['Carrier'] = 5
        self.playerScore['Battleship'] = 4
        self.playerScore['Submarine'] = 3
        self.playerScore['Destroyer'] = 3
        self.playerScore['Patrolboat'] = 2
        self.playerScore['Total'] = 17
        self.computerScore['Carrier'] = 5
        self.computerScore['Battleship'] = 4
        self.computerScore['Submarine'] = 3
        self.computerScore['Destroyer'] = 3
        self.computerScore['Patrolboat'] = 2
        self.computerScore['Total'] = 17
        self.hit_miss = ''
        self.myCoor = []
        self.admiralCoor = []

        if multiplayer:
            global player_ID
            global player_start
            global multiTurnJammer
            self.connFails = Clock.create_trigger(self.brokenConn, 2)
            self.ids.cpuInfo.text = 'wait'
            if player_ID == "player1:":
                self.ids.chgMultiPlayer1.text = 'player2:'
                self.ids.chgMultiPlayer2.text = 'player1:'
            else:
                self.ids.chgMultiPlayer1.text = 'player1:'
                self.ids.chgMultiPlayer2.text = 'player2:'

        for row in range(0, 10):
            for col in range(0, 10):
                self.myCoor.append(verText[row + 1] + ',' + horText[col])

        for row in range(0, 10):
            for col in range(0, 10):
                if row % 2 == 0:
                    if col % 2 == 0:
                        self.admiralCoor.append(verText[row + 1] + ',' + horText[col])
                if row % 2 != 0:
                    if col % 2 != 0:
                        self.admiralCoor.append(verText[row + 1] + ',' + horText[col])

    def resetMenu(self):
        self.dropdown.clear_widgets()
        self.ShipMenu = {}
        for setShip in range(0, len(self.shipTypes)):
            self.ShipMenu[self.shipTypes[setShip]] = self.populateMenu(setShip)
            self.dropdown.add_widget(self.ShipMenu[self.shipTypes[setShip]])

    def populateMenu(self, items):
        self.Menu = BoxLayout(size_hint_y=None, height='60dp')
        if items == 0:
            with self.Menu.canvas:
                    Color(0, 0, 0, 1)
                    Rectangle(size=self.size)
        self.Description = BoxLayout(size_hint_y=None, height='60dp', orientation='vertical')
        self.Buttons = BoxLayout(size_hint_y=None, height='60dp', orientation='vertical')
        self.HorzBtn = Button(text='horizontal', background_normal='btnRadarNormal.png', background_down='btnRadarFire.png', font_name='digital-7.regular.ttf', color=(0,1,0,1))
        self.VertBtn = Button(text='vertical', background_normal='btnRadarNormal.png', background_down='btnRadarFire.png', font_name='digital-7.regular.ttf', color=(0,1,0,1))
        self.Shiplbl = Label(text=self.shipTypes[items], font_name='digital-7.regular.ttf', color=(0,1,0,1))
        self.icon = Image(source=self.ShipList[items], allow_stretch=False, keep_ratio=False)
        self.HorzBtn.bind(on_release=lambda btn: self.dropdown.select(self.shipTypes[items] + '-' + self.HorzBtn.text))
        self.VertBtn.bind(on_release=lambda btn: self.dropdown.select(self.shipTypes[items] + '-' + self.VertBtn.text))
        self.Description.add_widget(self.icon)
        self.Description.add_widget(self.Shiplbl)
        self.Buttons.add_widget(self.VertBtn)
        self.Buttons.add_widget(self.HorzBtn)
        self.Menu.add_widget(self.Description)
        self.Menu.add_widget(self.Buttons)
        return self.Menu

    def testGrid(self, startPoint, vertical, ship_length):
        checkGrid = []
        t = startPoint.split(',')[0]
        if vertical == True:
            for items in range(verText.index(t) - ship_length, verText.index(t)):
                    taken = str(verText[items + 1] + ',' + startPoint.split(',')[1])
                    checkGrid.append(taken)
        else:
            t = startPoint.split(',')[1]
            for items in range(horText.index(t), horText.index(t) + ship_length):
                if items < 10:
                    taken = startPoint.split(',')[0] + ',' +  str(horText[items])
                else:
                    pre = False
                    return pre
                checkGrid.append(taken)
        for items in range(0, len(checkGrid)):
            pre = checkGrid[items] in occupied
            if pre == True:
                break
        return pre

    def addShiptoGrid(self, startPoint, vertical, ship_length):
        shipCoor = []
        t = startPoint.split(',')[0]
        if vertical == True:
            for items in range(verText.index(t) - ship_length, verText.index(t)):
                taken = str(verText[items + 1] + ',' + startPoint.split(',')[1])
                occupied.append(taken)
                shipCoor.append(taken)
        else:
            t = startPoint.split(',')[1]
            for items in range(horText.index(t), horText.index(t) + ship_length):
                taken = startPoint.split(',')[0] + ',' + str(horText[items])
                occupied.append(taken)
                shipCoor.append(taken)
        return shipCoor

    def computerShips(self):
        global board
        global ships
        board = []
        line_row = []
        myCoor = []
        ships = {"Carrier": 5,
             "Battleship": 4,
              "Submarine": 3,
             "Destroyer": 3,
             "Patrolboat": 2}
        for i in range(10):
            board_row = []
            for j in range(10):
                board_row.append(-1)
            board.append(board_row)
        comp_board = computer_place_ships(board, ships)
        for row in range(0, 10):
            line_row = []
            for col in range(0, 10):
                line_row.append(verText[row + 1] + ',' + horText[col])
            myCoor.append(line_row)
        for row in range(0, 10):
            for col in range(0, 10):
                if comp_board[row][col] != -1:
                    if comp_board[row][col] == 'C':
                        self.cpuCoor['Carrier'].append(myCoor[row][col])
                    if comp_board[row][col] == 'B':
                        self.cpuCoor['Battleship'].append(myCoor[row][col])
                    if comp_board[row][col] == 'S':
                        self.cpuCoor['Submarine'].append(myCoor[row][col])
                    if comp_board[row][col] == 'D':
                        self.cpuCoor['Destroyer'].append(myCoor[row][col])
                    if comp_board[row][col] == 'P':
                        self.cpuCoor['Patrolboat'].append(myCoor[row][col])
        self.ids.usrInfo.text = 'Tap sonar to fire!'

    def placeShips(self, instance):
        if self.ids.selectShip.text == 'Placement Done':
            return
        #Aircraft carrier
        global multiplayer
        checkGrid = []
        if self.ids.selectShip.text == 'Carrier(5)-vertical':
            self.myShips['Carrier'].width_ship = self.shipbtn[str(instance.id)].size[0]
            self.myShips['Carrier'].height_ship = self.shipbtn[str(instance.id)].size[1]*5
            self.myShips['Carrier'].pos = self.shipbtn[str(instance.id)].pos
            self.myShips['Carrier'].value = 0
            chkGrid = self.testGrid(instance.id, True, 5)
            chkPlace = instance.id.split(',')[0]
            if (chkPlace == 'A')|(chkPlace == 'B')|(chkPlace == 'C')|(chkPlace == 'D'):
                self.beep.play()
                self.ids.usrInfo.text = 'Move ship down'
                return
            else:
                if chkGrid:
                    self.beep.play()
                    self.ids.usrInfo.text = 'Grid Occupied'
                    return
                else:
                    self.myShipCoor['Carrier'] = self.addShiptoGrid(instance.id, True, 5)
                    self.ids.shipScreen.add_widget(self.myShips['Carrier'])
                    self.shipTypes.remove('Carrier(5)')
                    self.ShipList.remove('btnCarrier_1.png')
                    self.resetMenu()
                    self.ids.selectShip.values=self.shipTypes
                    self.ids.selectShip.text = 'Place Ship'
                    self.ids.usrInfo.text = 'Carrier placed'

        if self.ids.selectShip.text == 'Carrier(5)-horizontal':
            self.myShips['Carrier'].width_ship = self.shipbtn[str(instance.id)].size[1]
            self.myShips['Carrier'].height_ship = self.shipbtn[str(instance.id)].size[0]*5
            self.myShips['Carrier'].pos = self.shipbtn[str(instance.id)].pos
            self.myShips['Carrier'].value = 90
            chkGrid = self.testGrid(instance.id, False, 5)
            chkPlace = instance.id.split(',')[1]
            if (chkPlace == '7')|(chkPlace == '8')|(chkPlace == '9')|(chkPlace == '10'):
                self.beep.play()
                self.ids.usrInfo.text = 'Move ship left'
            else:
                if chkGrid:
                    self.beep.play()
                    self.ids.usrInfo.text = 'Grid Occupied'
                else:
                    self.myShipCoor['Carrier'] = self.addShiptoGrid(instance.id, False, 5)
                    self.ids.shipScreen.add_widget(self.myShips['Carrier'])
                    self.shipTypes.remove('Carrier(5)')
                    self.ShipList.remove('btnCarrier_1.png')
                    self.resetMenu()
                    self.ids.selectShip.values=self.shipTypes
                    self.ids.selectShip.text = 'Place Ship'
                    self.ids.usrInfo.text = 'Carrier placed'

        #Battleship
        if self.ids.selectShip.text == 'Battleship(4)-vertical':
            self.myShips['Battleship'].width_ship = self.shipbtn[str(instance.id)].size[0]
            self.myShips['Battleship'].height_ship = self.shipbtn[str(instance.id)].size[1]*4
            self.myShips['Battleship'].pos = self.shipbtn[str(instance.id)].pos
            self.myShips['Battleship'].value = 0
            chkGrid = self.testGrid(instance.id, True, 4)
            chkPlace = instance.id.split(',')[0]
            if (chkPlace == 'A')|(chkPlace == 'B')|(chkPlace == 'C'):
                self.beep.play()
                self.ids.usrInfo.text = 'Move ship down'
            else:
                if chkGrid:
                    self.beep.play()
                    self.ids.usrInfo.text = 'Grid Occupied'
                else:
                    self.myShipCoor['Battleship'] = self.addShiptoGrid(instance.id, True, 4)
                    self.ids.shipScreen.add_widget(self.myShips['Battleship'])
                    self.shipTypes.remove('Battleship(4)')
                    self.ShipList.remove('btnBattleship.png')
                    self.resetMenu()
                    self.ids.selectShip.values=self.shipTypes
                    self.ids.selectShip.text = 'Place Ship'
                    self.ids.usrInfo.text = 'Battleship placed'

        if self.ids.selectShip.text == 'Battleship(4)-horizontal':
            self.myShips['Battleship'].width_ship = self.shipbtn[str(instance.id)].size[1]
            self.myShips['Battleship'].height_ship = self.shipbtn[str(instance.id)].size[0]*4
            self.myShips['Battleship'].pos = self.shipbtn[str(instance.id)].pos
            self.myShips['Battleship'].value = 90
            chkGrid = self.testGrid(instance.id, False, 4)
            chkPlace = instance.id.split(',')[1]
            if (chkPlace == '8')|(chkPlace == '9')|(chkPlace == '10'):
                self.beep.play()
                self.ids.usrInfo.text = 'Move ship left'
            else:
                if chkGrid:
                    self.beep.play()
                    self.ids.usrInfo.text = 'Grid Occupied'
                else:
                    self.myShipCoor['Battleship'] = self.addShiptoGrid(instance.id, False, 4)
                    self.ids.shipScreen.add_widget(self.myShips['Battleship'])
                    self.shipTypes.remove('Battleship(4)')
                    self.ShipList.remove('btnBattleship.png')
                    self.resetMenu()
                    self.ids.selectShip.values=self.shipTypes
                    self.ids.selectShip.text = 'Place Ship'
                    self.ids.usrInfo.text = 'Battleship placed'

        #Submarine
        if self.ids.selectShip.text == 'Submarine(3)-vertical':
            self.myShips['Submarine'].width_ship = self.shipbtn[str(instance.id)].size[0]
            self.myShips['Submarine'].height_ship = self.shipbtn[str(instance.id)].size[1]*3
            self.myShips['Submarine'].pos = self.shipbtn[str(instance.id)].pos
            self.myShips['Submarine'].value = 0
            chkGrid = self.testGrid(instance.id, True, 3)
            chkPlace = instance.id.split(',')[0]
            if (chkPlace == 'A')|(chkPlace == 'B'):
                self.beep.play()
                self.ids.usrInfo.text = 'Move ship down'
            else:
                if chkGrid:
                    self.beep.play()
                    self.ids.usrInfo.text = 'Grid Occupied'
                else:
                    self.myShipCoor['Submarine'] = self.addShiptoGrid(instance.id, True, 3)
                    self.ids.shipScreen.add_widget(self.myShips['Submarine'])
                    self.shipTypes.remove('Submarine(3)')
                    self.ShipList.remove('btnSubmarine.png')
                    self.resetMenu()
                    self.ids.selectShip.values=self.shipTypes
                    self.ids.selectShip.text = 'Place Ship'
                    self.ids.usrInfo.text = 'Submarine placed'

        if self.ids.selectShip.text == 'Submarine(3)-horizontal':
            self.myShips['Submarine'].width_ship = self.shipbtn[str(instance.id)].size[1]
            self.myShips['Submarine'].height_ship = self.shipbtn[str(instance.id)].size[0]*3
            self.myShips['Submarine'].pos = self.shipbtn[str(instance.id)].pos
            self.myShips['Submarine'].value = 90
            chkGrid = self.testGrid(instance.id, False, 3)
            chkPlace = instance.id.split(',')[1]
            if (chkPlace == '9')|(chkPlace == '10'):
                self.beep.play()
                self.ids.usrInfo.text = 'Move ship left'
            else:
                if chkGrid:
                    self.beep.play()
                    self.ids.usrInfo.text = 'Grid Occupied'
                else:
                    self.myShipCoor['Submarine'] = self.addShiptoGrid(instance.id, False, 3)
                    self.ids.shipScreen.add_widget(self.myShips['Submarine'])
                    self.shipTypes.remove('Submarine(3)')
                    self.ShipList.remove('btnSubmarine.png')
                    self.resetMenu()
                    self.ids.selectShip.values=self.shipTypes
                    self.ids.selectShip.text = 'Place Ship'
                    self.ids.usrInfo.text = 'Submarine placed'

        #Destroyer
        if self.ids.selectShip.text == 'Destroyer(3)-vertical':
            self.myShips['Destroyer'].width_ship = self.shipbtn[str(instance.id)].size[0]
            self.myShips['Destroyer'].height_ship = self.shipbtn[str(instance.id)].size[1]*3
            self.myShips['Destroyer'].pos = self.shipbtn[str(instance.id)].pos
            self.myShips['Destroyer'].value = 0
            chkGrid = self.testGrid(instance.id, True, 3)
            chkPlace = instance.id.split(',')[0]
            if (chkPlace == 'A')|(chkPlace == 'B'):
                self.beep.play()
                self.ids.usrInfo.text = 'Move ship down'
            else:
                if chkGrid:
                    self.beep.play()
                    self.ids.usrInfo.text = 'Grid Occupied'
                else:
                    self.myShipCoor['Destroyer'] = self.addShiptoGrid(instance.id, True, 3)
                    self.ids.shipScreen.add_widget(self.myShips['Destroyer'])
                    self.shipTypes.remove('Destroyer(3)')
                    self.ShipList.remove('btnDestroyer.png')
                    self.resetMenu()
                    self.ids.selectShip.values=self.shipTypes
                    self.ids.selectShip.text = 'Place Ship'
                    self.ids.usrInfo.text = 'Destroyer placed'

        if self.ids.selectShip.text == 'Destroyer(3)-horizontal':
            self.myShips['Destroyer'].width_ship = self.shipbtn[str(instance.id)].size[1]
            self.myShips['Destroyer'].height_ship = self.shipbtn[str(instance.id)].size[0]*3
            self.myShips['Destroyer'].pos = self.shipbtn[str(instance.id)].pos
            self.myShips['Destroyer'].value = 90
            chkGrid = self.testGrid(instance.id, False, 3)
            chkPlace = instance.id.split(',')[1]
            if (chkPlace == '9')|(chkPlace == '10'):
                self.beep.play()
                self.ids.usrInfo.text = 'Move ship left'
            else:
                if chkGrid:
                    self.beep.play()
                    self.ids.usrInfo.text = 'Grid Occupied'
                else:
                    self.myShipCoor['Destroyer'] = self.addShiptoGrid(instance.id, False, 3)
                    self.ids.shipScreen.add_widget(self.myShips['Destroyer'])
                    self.shipTypes.remove('Destroyer(3)')
                    self.ShipList.remove('btnDestroyer.png')
                    self.resetMenu()
                    self.ids.selectShip.values=self.shipTypes
                    self.ids.selectShip.text = 'Place Ship'
                    self.ids.usrInfo.text = 'Destroyer placed'

        #Patrolboat
        if self.ids.selectShip.text == 'Patrolboat(2)-vertical':
            self.myShips['Patrolboat'].width_ship = self.shipbtn[str(instance.id)].size[0]
            self.myShips['Patrolboat'].height_ship = self.shipbtn[str(instance.id)].size[1]*2
            self.myShips['Patrolboat'].pos = self.shipbtn[str(instance.id)].pos
            self.myShips['Patrolboat'].value = 0
            chkGrid = self.testGrid(instance.id, True, 2)
            chkPlace = instance.id.split(',')[0]
            if (chkPlace == 'A'):
                self.beep.play()
                self.ids.usrInfo.text = 'Move ship down'
            else:
                if chkGrid:
                    self.beep.play()
                    self.ids.usrInfo.text = 'Grid Occupied'
                else:
                    self.myShipCoor['Patrolboat'] = self.addShiptoGrid(instance.id, True, 2)
                    self.ids.shipScreen.add_widget(self.myShips['Patrolboat'])
                    self.shipTypes.remove('Patrolboat(2)')
                    self.ShipList.remove('btnPatrolboat.png')
                    self.resetMenu()
                    self.ids.selectShip.values=self.shipTypes
                    self.ids.selectShip.text = 'Place Ship'
                    self.ids.usrInfo.text = 'Patrolboat placed'

        if self.ids.selectShip.text == 'Patrolboat(2)-horizontal':
            self.myShips['Patrolboat'].width_ship = self.shipbtn[str(instance.id)].size[1]
            self.myShips['Patrolboat'].height_ship = self.shipbtn[str(instance.id)].size[0]*2
            self.myShips['Patrolboat'].pos = self.shipbtn[str(instance.id)].pos
            self.myShips['Patrolboat'].value = 90
            chkGrid = self.testGrid(instance.id, False, 2)
            chkPlace = instance.id.split(',')[1]
            if (chkPlace == '10'):
                self.beep.play()
                self.ids.usrInfo.text = 'Move ship left'
            else:
                if chkGrid:
                    self.beep.play()
                    self.ids.usrInfo.text = 'Grid Occupied'
                else:
                    self.myShipCoor['Patrolboat'] = self.addShiptoGrid(instance.id, False, 2)
                    self.ids.shipScreen.add_widget(self.myShips['Patrolboat'])
                    self.shipTypes.remove('Patrolboat(2)')
                    self.ShipList.remove('btnPatrolboat.png')
                    self.resetMenu()
                    self.ids.selectShip.values=self.shipTypes
                    self.ids.selectShip.text = 'Place Ship'
                    self.ids.usrInfo.text = 'Patrolboat placed'
        if self.ids.selectShip.values == []:
            print self.myShipCoor
            self.ids.selectShip.text = 'Placement Done'
            if not multiplayer:
                self.ids.cpuInfo.text = 'Computer is ready'
                self.computerShips()
            else:
                self.ids.cpuInfo.text = 'wait'
                self.multiPlaceDone()

    def multiWaitForPlayer(self):
        try:
            self.cpuCoor = json.loads(client.recv(max_size))
            global player_ID
            global player_start
            if player_start != player_ID:
                self.ids.cpuInfo.text = 'wait'
                self.recvTimer()
            else:
                self.ids.cpuInfo.text = 'Fire away!'
        except Exception as msg:
            self.ids.cpuInfo.text = 'Player - quiting'
            self.connFails()


    def mutliPlace(self, dt):
        global client
        serialCoor = json.dumps(self.myShipCoor)
        client.send(serialCoor)
        self.placeThread = threading.Thread(target=self.multiWaitForPlayer).start()

    def setValue(sender, value):
        global myRadar
        myRadar.value = value

    def updateRadar(self, dt):
        global i
        global admiral
        global seaman
        global captain
        global multiplayer
        global player_ID
        if seaman:
            self.ids.currentRank.text = 'Seaman'
            self.ids.rankIcon.source = 'seaman.png'
        if captain:
            self.ids.currentRank.text = 'Captain'
            self.ids.rankIcon.source = 'captain.png'
        if admiral:
            self.ids.currentRank.text = 'Admiral'
            self.ids.rankIcon.source = 'admiral.png'
        if multiplayer:
            self.ids.currentRank.text = player_ID
            self.ids.rankIcon.source = 'multi.png'
            if self.ids.cpuInfo.text == 'wait':
                self.ids.mainMenu.disabled = True
                self.ids.helpMenu.disabled = True
            else:
                self.ids.mainMenu.disabled = False
                self.ids.helpMenu.disabled = False
        if not multiplayer:
            self.ids.mainMenu.disabled = False
            self.ids.helpMenu.disabled = False
        if i <= 360:
            i += 3
        if i == 360:
            i = 0
        self.degSweep[' 1'].text = str(i)
        self.setValue(i)
        self.sweepTimer()

    def screenPopulate(self):
        global myRadar
        global horText
        global multiplayer
        myRadar = radar(fntColor=(0, 1, 0,.5),
                width_radar=self.ids.radarScreen.width - self.ids.radarScreen.width/11,
                height_radar=self.ids.radarScreen.height - self.ids.radarScreen.height/11,
                pos=(self.ids.radarScreen.x + self.ids.radarScreen.width/11, self.ids.radarScreen.y))
        self.ids.radarScreen.clear_widgets()
        self.fireGrid = GridLayout(cols=11, rows=11, pos=self.ids.radarScreen.pos)
        for row in range(0,11):
            if row == 0:
                self.degSweep[verText[row]+horText[0]] = Label(font_name='digital-7.regular.ttf', font_size="20dp", color=(0,1,0,1))
                self.fireGrid.add_widget(self.degSweep[verText[row]+horText[0]])
            else:
                self.fireGrid.add_widget(Label(text=verText[row], font_name='digital-7.regular.ttf', font_size="20dp", color=(0,1,0,1)))
            for col in range(0,10):
                if row == 0:
                        self.fireGrid.add_widget(Label(text=horText[col], font_name='digital-7.regular.ttf', font_size="20dp", color=(0,1,0,1)))
                else:
                    self.firebtn[verText[row] + ',' + horText[col]] = Button(background_normal='btnRadarNormal.png',
                        background_down='btnRadarFire.png',
                        id=verText[row]+','+horText[col])
                    self.firebtn[verText[row] + ',' + horText[col]].bind(on_press=self.takeShot)
                    self.fireGrid.add_widget(self.firebtn[verText[row] + ',' + horText[col]])
            self.ids.shipScreen.clear_widgets()
        self.shipGrid = GridLayout(cols=11, rows=11, pos=self.ids.shipScreen.pos)
        for row in range(0,11):
            if row == 0:
                self.shipGrid.add_widget(Label())
            else:
                self.shipGrid.add_widget(Button(text=verText[row], font_name='digital-7.regular.ttf', font_size="20dp"))
            for col in range(0,10):
                if row == 0:
                        self.shipGrid.add_widget(Button(text=horText[col], font_name='digital-7.regular.ttf', font_size="20dp"))
                else:
                    self.shipbtn[verText[row] + ',' + horText[col]] = Button(background_normal='btnRadarNormal.png',
                        background_down='btnRadarNormal.png',
                        id=verText[row] + ',' + horText[col])
                    self.shipbtn[verText[row] + ',' + horText[col]].bind(on_press=self.placeShips)
                    self.shipGrid.add_widget(self.shipbtn[verText[row] + ',' + horText[col]])
        self.ids.shipScreen.add_widget(self.shipGrid)
        self.ids.radarScreen.add_widget(myRadar)
        self.ids.radarScreen.add_widget(self.fireGrid)
        self.sweepTimer()


    def _update_LayoutSize(self, instance, value):
        self.ids.radarScreen.size = instance.size
        if self.ids.radarScreen.height != 100:
            self.resetGame()
            self.screenPopulate()


    def killShipProtocol(self, name, score):
        global captain
        global admiral
        newAI = []
        if name == 'Carrier':
            if captain:
                if self.computerScore[name] <= 2 :
                    preAI = self.myShipCoor[name]
                    for items in range(0,len(self.myShipCoor[name])):
                        if self.myShipCoor[name][items] in self.myCoor:
                            newAI.append(self.myShipCoor[name][items])
                    self.ai_cor = newAI
            if admiral:
                if self.computerScore[name] <= 3 :
                    preAI = self.myShipCoor[name]
                    for items in range(0,len(self.myShipCoor[name])):
                        if self.myShipCoor[name][items] in self.myCoor:
                            newAI.append(self.myShipCoor[name][items])
                    self.ai_cor = newAI

        if name == 'Battleship':
            if captain:
                if self.computerScore[name] <= 2 :
                    preAI = self.myShipCoor[name]
                    for items in range(0,len(self.myShipCoor[name])):
                        if self.myShipCoor[name][items] in self.myCoor:
                            newAI.append(self.myShipCoor[name][items])
                    self.ai_cor = newAI
            if admiral:
                    if self.computerScore[name] <= 2 :
                        preAI = self.myShipCoor[name]
                        for items in range(0,len(self.myShipCoor[name])):
                            if self.myShipCoor[name][items] in self.myCoor:
                                newAI.append(self.myShipCoor[name][items])
                        self.ai_cor = newAI
        if name == 'Submarine':
            if admiral|captain:
                    if self.computerScore[name] <= 1 :
                        preAI = self.myShipCoor[name]
                        for items in range(0,len(self.myShipCoor[name])):
                            if self.myShipCoor[name][items] in self.myCoor:
                                newAI.append(self.myShipCoor[name][items])
                        self.ai_cor = newAI
        if name == 'Destroyer':
            if admiral|captain:
                    if self.computerScore[name] <= 1 :
                        preAI = self.myShipCoor[name]
                        for items in range(0,len(self.myShipCoor[name])):
                            if self.myShipCoor[name][items] in self.myCoor:
                                newAI.append(self.myShipCoor[name][items])
                        self.ai_cor = newAI

    def updateComputerScore(self, name, ori):
        global captain
        global admiral
        global multiplayer
        if not multiplayer:
            if not admiral:
                self.myCoor.remove(ori)
            else:
                if ori in self.admiralCoor:
                    self.admiralCoor.remove(ori)
                if ori in self.myCoor:
                    self.myCoor.remove(ori)
            if self.ai_cor != []:
                if ori in self.ai_cor:
                    self.ai_cor.remove(ori)
            if self.ai_cor == []:
                y_cor = ['','A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', '']
                split_ori = str(ori).split(',')
                self.ai_cor = []
                c_1 = split_ori[0] + ',' + str(int(split_ori[1]) - 1)
                c_2 = split_ori[0] + ',' + str(int(split_ori[1]) + 1)
                c_3 = y_cor[y_cor.index(split_ori[0]) - 1] + ',' + split_ori[1]
                c_4 = y_cor[y_cor.index(split_ori[0]) + 1] + ',' + split_ori[1]
                preAI = [c_1, c_2, c_3, c_4]
                for items in range(0, 4):
                    if not admiral:
                        if preAI[items] in self.myCoor:
                            self.ai_cor.append(preAI[items])
                    else:
                        if preAI[items] in self.myCoor:
                            self.ai_cor.append(preAI[items])
            if captain|admiral:
                self.hitOnShip = True
        self.banger.play()
        self.ids.cpuInfo.text = 'Hit on ' + ori + ' - '+ name
        self.computerScore[name]-= 1
        self.killShipProtocol(name, self.computerScore[name])
        self.cpufire[ori] = hitBang(width_shot=self.shipbtn[ori].size[0],
                        height_shot=self.shipbtn[ori].size[1],
                        file_pin='bang_1.png',
                        pos=self.shipbtn[ori].pos)
        self.ids.shipScreen.add_widget(self.cpufire[ori])
        if self.computerScore[name] == 0:
            if name == 'Carrier':
                # if self.myShipCoor['Carrier'][0].split(',')[1] != self.myShipCoor['Carrier'][1].split(',')[1]:
                #     self.mySunkenShips['Carrier'].width_ship = self.shipbtn[self.myShipCoor['Carrier'][0]].size[1]
                #     self.mySunkenShips['Carrier'].height_ship = self.shipbtn[self.myShipCoor['Carrier'][0]].size[0]*5
                #     self.mySunkenShips['Carrier'].pos = self.shipbtn[self.myShipCoor['Carrier'][0]].pos
                #     self.mySunkenShips['Carrier'].value = 90
                # else:
                #     self.mySunkenShips['Carrier'].width_ship = self.shipbtn[self.myShipCoor['Carrier'][0]].size[0]
                #     self.mySunkenShips['Carrier'].height_ship = self.shipbtn[self.myShipCoor['Carrier'][0]].size[1]*5
                #     self.mySunkenShips['Carrier'].pos = self.shipbtn[self.myShipCoor['Carrier'][4]].pos
                #     self.mySunkenShips['Carrier'].value = 0
                for hits in range(0,5):
                    self.ids.shipScreen.remove_widget(self.cpufire[self.myShipCoor['Carrier'][hits]])
                self.ids.shipScreen.remove_widget(self.myShips['Carrier'])
                #self.ids.shipScreen.add_widget(self.mySunkenShips['Carrier'])
                self.makeBubbles(self.myShipCoor['Carrier'])
            if name == 'Battleship':
                # if self.myShipCoor['Battleship'][0].split(',')[1] != self.myShipCoor['Battleship'][1].split(',')[1]:
                #     self.mySunkenShips['Battleship'].width_ship = self.shipbtn[self.myShipCoor['Battleship'][0]].size[1]
                #     self.mySunkenShips['Battleship'].height_ship = self.shipbtn[self.myShipCoor['Battleship'][0]].size[0]*4
                #     self.mySunkenShips['Battleship'].pos = self.shipbtn[self.myShipCoor['Battleship'][0]].pos
                #     self.mySunkenShips['Battleship'].value = 90
                # else:
                #     self.mySunkenShips['Battleship'].width_ship = self.shipbtn[self.myShipCoor['Battleship'][0]].size[0]
                #     self.mySunkenShips['Battleship'].height_ship = self.shipbtn[self.myShipCoor['Battleship'][0]].size[1]*4
                #     self.mySunkenShips['Battleship'].pos = self.shipbtn[self.myShipCoor['Battleship'][3]].pos
                #     self.mySunkenShips['Battleship'].value = 0
                for hits in range(0,4):
                    self.ids.shipScreen.remove_widget(self.cpufire[self.myShipCoor['Battleship'][hits]])
                self.ids.shipScreen.remove_widget(self.myShips['Battleship'])
                # self.ids.shipScreen.add_widget(self.mySunkenShips['Battleship'])
                self.makeBubbles(self.myShipCoor['Battleship'])
            if name == 'Submarine':
                # if self.myShipCoor['Submarine'][0].split(',')[1] != self.myShipCoor['Submarine'][1].split(',')[1]:
                #     self.mySunkenShips['Submarine'].width_ship = self.shipbtn[self.myShipCoor['Submarine'][0]].size[1]
                #     self.mySunkenShips['Submarine'].height_ship = self.shipbtn[self.myShipCoor['Submarine'][0]].size[0]*3
                #     self.mySunkenShips['Submarine'].pos = self.shipbtn[self.myShipCoor['Submarine'][0]].pos
                #     self.mySunkenShips['Submarine'].value = 90
                # else:
                #     self.mySunkenShips['Submarine'].width_ship = self.shipbtn[self.myShipCoor['Submarine'][0]].size[0]
                #     self.mySunkenShips['Submarine'].height_ship = self.shipbtn[self.myShipCoor['Submarine'][0]].size[1]*3
                #     self.mySunkenShips['Submarine'].pos = self.shipbtn[self.myShipCoor['Submarine'][2]].pos
                #     self.mySunkenShips['Submarine'].value = 0
                for hits in range(0,3):
                    self.ids.shipScreen.remove_widget(self.cpufire[self.myShipCoor['Submarine'][hits]])
                self.ids.shipScreen.remove_widget(self.myShips['Submarine'])
                #self.ids.shipScreen.add_widget(self.mySunkenShips['Submarine'])
                self.makeBubbles(self.myShipCoor['Submarine'])
            if name == 'Destroyer':
                # if self.myShipCoor['Destroyer'][0].split(',')[1] != self.myShipCoor['Destroyer'][1].split(',')[1]:
                #     self.mySunkenShips['Destroyer'].width_ship = self.shipbtn[self.myShipCoor['Destroyer'][0]].size[1]
                #     self.mySunkenShips['Destroyer'].height_ship = self.shipbtn[self.myShipCoor['Destroyer'][0]].size[0]*3
                #     self.mySunkenShips['Destroyer'].pos = self.shipbtn[self.myShipCoor['Destroyer'][0]].pos
                #     self.mySunkenShips['Destroyer'].value = 90
                # else:
                #     self.mySunkenShips['Destroyer'].width_ship = self.shipbtn[self.myShipCoor['Destroyer'][0]].size[0]
                #     self.mySunkenShips['Destroyer'].height_ship = self.shipbtn[self.myShipCoor['Destroyer'][0]].size[1]*3
                #     self.mySunkenShips['Destroyer'].pos = self.shipbtn[self.myShipCoor['Destroyer'][2]].pos
                #     self.mySunkenShips['Destroyer'].value = 0
                for hits in range(0,3):
                    self.ids.shipScreen.remove_widget(self.cpufire[self.myShipCoor['Destroyer'][hits]])
                self.ids.shipScreen.remove_widget(self.myShips['Destroyer'])
                #self.ids.shipScreen.add_widget(self.mySunkenShips['Destroyer'])
                self.makeBubbles(self.myShipCoor['Destroyer'])
            if name == 'Patrolboat':
                # if self.myShipCoor['Patrolboat'][0].split(',')[1] != self.myShipCoor['Patrolboat'][1].split(',')[1]:
                #     self.mySunkenShips['Patrolboat'].width_ship = self.shipbtn[self.myShipCoor['Patrolboat'][0]].size[1]
                #     self.mySunkenShips['Patrolboat'].height_ship = self.shipbtn[self.myShipCoor['Patrolboat'][0]].size[0]*2
                #     self.mySunkenShips['Patrolboat'].pos = self.shipbtn[self.myShipCoor['Patrolboat'][0]].pos
                #     self.mySunkenShips['Patrolboat'].value = 90
                # else:
                #     self.mySunkenShips['Patrolboat'].width_ship = self.shipbtn[self.myShipCoor['Patrolboat'][0]].size[0]
                #     self.mySunkenShips['Patrolboat'].height_ship = self.shipbtn[self.myShipCoor['Patrolboat'][0]].size[1]*2
                #     self.mySunkenShips['Patrolboat'].pos = self.shipbtn[self.myShipCoor['Patrolboat'][1]].pos
                #     self.mySunkenShips['Patrolboat'].value = 0
                for hits in range(0,2):
                    self.ids.shipScreen.remove_widget(self.cpufire[self.myShipCoor['Patrolboat'][hits]])
                self.ids.shipScreen.remove_widget(self.myShips['Patrolboat'])
                # self.ids.shipScreen.add_widget(self.mySunkenShips['Patrolboat'])
                self.makeBubbles(self.myShipCoor['Patrolboat'])
            self.ai_cor = []
            self.bomb.play()
            self.hitOnShip = False
            self.ids.cpuInfo.text = '%s has been sunk' %name

    def makeBubbles(self, coordinates):
        for bub in range(0, len(coordinates)):
            self.bubbles[coordinates[bub]] = hitBang(width_shot=self.shipbtn[coordinates[bub]].size[0],
                height_shot=self.shipbtn[coordinates[bub]].size[0],
                file_pin='Bubbles.png',
                pos=self.shipbtn[str(coordinates[bub])].pos)
            self.ids.shipScreen.add_widget(self.bubbles[coordinates[bub]])

    def computerMiss(self, ori):
        global admiral
        global multiplayer
        if not multiplayer:
            if not admiral:
                self.myCoor.remove(ori)
            else:
                if ori in self.admiralCoor:
                    self.admiralCoor.remove(ori)
                    self.myCoor.remove(ori)
            if self.ai_cor != []:
                if ori in self.ai_cor:
                    self.ai_cor.remove(ori)
        self.ids.cpuInfo.text = 'Missed on ' + ori
        self.cpufire[ori] = hitBang(width_shot=self.shipbtn[ori].size[0],
                        height_shot=self.shipbtn[ori].size[1],
                        file_pin='splash.png',
                        pos=self.shipbtn[ori].pos)
        self.plocker.play()
        self.ids.shipScreen.add_widget(self.cpufire[ori])


    def computerShot(self):
        global seaman
        global w
        global captain
        global admiral
        global sm
        global scoresSeaman
        global scoresCaptain
        global scoresAdmiral
        global store
        global multiplayer
        global client
        global max_size
        if not multiplayer:
            if not self.hitOnShip:
                if not admiral:
                    w = self.myCoor[random.randint(0, len(self.myCoor)-1)]
                else:
                    w = self.admiralCoor[random.randint(0, len(self.admiralCoor)-1)]
            else:
                if self.ai_cor != []:
                    w = self.ai_cor[random.randint(0, len(self.ai_cor)-1)]
                else:
                    if not admiral:
                        w = self.myCoor[random.randint(0, len(self.myCoor)-1)]
                    else:
                        w = self.admiralCoor[random.randint(0, len(self.admiralCoor)-1)]
        else:
            w = w
        test = False
        for name in self.myShipCoor.keys():
            nameId = self.myShipCoor[name]
            test = w in nameId
            if test == True:
                if name == 'Carrier':
                    self.updateComputerScore(name, w)
                    self.computerScore['Total']-= 1
                    break
                if name == 'Battleship':
                    self.updateComputerScore(name, w)
                    self.computerScore['Total']-= 1
                    break
                if name == 'Submarine':
                    self.updateComputerScore(name, w)
                    self.computerScore['Total']-= 1
                    break
                if name == 'Destroyer':
                    self.updateComputerScore(name, w)
                    self.computerScore['Total']-= 1
                    break
                if name == 'Patrolboat':
                    self.updateComputerScore(name, w)
                    self.computerScore['Total']-= 1
                    break
        if test == False:
            self.computerMiss(w)
        if self.computerScore['Total'] == 0:
            self.ids.cpuInfo.text = 'You Lose!'
            if seaman:
                scoresSeaman['losses'] += 1
                store.put("Seaman", scores=scoresSeaman)
            if captain:
                scoresCaptain['losses'] += 1
                store.put("Captain", scores=scoresCaptain)
            if admiral:
                scoresAdmiral['losses'] += 1
                store.put("Admiral", scores=scoresAdmiral)
            if multiplayer:
                scoresMulti['losses'] += 1
                store.put("Multi", scores=scoresMulti)
            self.playerLose()

    def brokenConn(self, dt):
        self.menuTimer()

    def gotoMenu(self, dt):
        global sm
        global multiplayer
        if multiplayer:
            if self.ids.cpuInfo.text == 'wait':
                return
            else:
                try:
                    client.send('quiting')
                except Exception as msg:
                    print msg
                closeAndClear()
        sm.transition.direction = 'down'
        sm.current = 'menu'
        self.resetGame()
        self.screenPopulate()

    def toMenu(self):
        self.menuTimer()

    def gotoHelp(self):
        global sm
        global multiplayer
        global player_ID
        if multiplayer:
            if self.ids.cpuInfo.text == 'wait':
                return
            else:
                client.send('quiting')
                closeAndClear()
        sm.transition.direction = 'down'
        sm.transition.direction = 'left'
        sm.current = 'help'
        self.resetGame()
        self.screenPopulate()

    def YouLose(self, dt):
        self.sinker.play()
        if multiplayer:
            closeAndClear()
        global sm
        sm.transition.direction = 'right'
        sm.current = 'lose'
        self.sweepTimer.cancel()
        self.resetGame()
        self.ids.cpuInfo.text = 'wait'
        self.ids.usrInfo.text = ''
        self.screenPopulate()

    def YouWin(self, dt):
        self.victory.play()
        if multiplayer:
            closeAndClear()
        global sm
        sm.transition.direction = 'right'
        sm.current = 'win'
        self.sweepTimer.cancel()
        self.resetGame()
        self.ids.cpuInfo.text = 'wait'
        self.ids.usrInfo.text = ''
        self.screenPopulate()

    def multiGame(self):
        global w
        global gotResp
        try:
            w = client.recv(max_size)
            w = w.split(':')[1]
            gotResp = True
        except Exception as msg:
            self.ids.cpuInfo.text = 'Player quiting'
            self.connFails()
            print 'mulitGame says - ' + str(msg)

    def hangForReceive(self, dt):
        global gotResp
        if not gotResp:
            self.hangOn()
        else:
            self.computerShot()

    def multiShot(self, dt):
        global gotResp
        gotResp = False
        multiThread = threading.Thread(target=self.multiGame).start()
        self.hangOn()

    def takeShot(self, instance):
        global usrFire
        global seaman
        global captain
        global admiral
        global sm
        global scoresSeaman
        global scoresCaptain
        global scoresAdmiral
        global scoresMulti
        global store
        global player_ID
        global multiplayer
        if self.ids.cpuInfo.text != 'wait':
            if multiplayer:
                try:
                    time.sleep(0.05)
                    client.send(player_ID + instance.id)
                    self.ids.cpuInfo.text = client.recv(max_size)
                except Exception as msg:
                    print msg
                    self.connFails()
            if self.cpuCoor['Submarine'] != []:
                self.ids.usrInfo.text = 'Firing on' + ' ' + str(instance.id)
                self.playerNoShots += 1
                if seaman:
                    scoresSeaman['number_shots'] = self.playerNoShots
                    store.put("Seaman", scores=scoresSeaman)
                if captain:
                    scoresCaptain['number_shots'] = self.playerNoShots
                    store.put("Captain", scores=scoresCaptain)
                if admiral:
                    scoresAdmiral['number_shots'] = self.playerNoShots
                    store.put("Admiral", scores=scoresAdmiral)
                if multiplayer:
                    scoresMulti['number_shots'] = self.playerNoShots
                    store.put("Multi", scores=scoresMulti)
                usrFire += 1
                self.fireMark[str(instance.id)] = hitPin(width_shot=instance.size[0],
                height_shot=instance.size[1],
                file_pin='grnPin.png',
                pos=instance.pos)
                self.ids.radarScreen.add_widget(self.fireMark[str(instance.id)])
                self.ids.usrInfo.text = 'Missed on ' + str(instance.id)
                for name in self.cpuCoor.keys():
                    t = self.cpuCoor[name]
                    x = instance.id in t
                    if x:
                        self.ids.radarScreen.remove_widget(self.fireMark[str(instance.id)])
                        self.sonarping.play()
                        self.ids.usrInfo.text = 'Hit on ' + str(instance.id) + ' - ' + str(name)
                        self.playerScore['Total']-= 1
                        if name == 'Carrier':
                            self.playerScore['Carrier']-= 1
                            self.fireMark[str(instance.id)] = hitPin(width_shot=instance.size[0],
                            height_shot=instance.size[1],
                            file_pin='carrier_hit.png',
                            pos=instance.pos)
                            self.ids.radarScreen.add_widget(self.fireMark[str(instance.id)])
                            if self.playerScore['Carrier'] == 0:
                                if self.cpuCoor['Carrier'][0].split(',')[1] != self.cpuCoor['Carrier'][1].split(',')[1]:
                                    self.sunkenShips['Carrier'].width_ship = self.firebtn[self.cpuCoor['Carrier'][0]].size[1]
                                    self.sunkenShips['Carrier'].height_ship = self.firebtn[self.cpuCoor['Carrier'][0]].size[0]*5
                                    self.sunkenShips['Carrier'].pos = self.firebtn[self.cpuCoor['Carrier'][0]].pos
                                    self.sunkenShips['Carrier'].value = 90
                                else:
                                    self.sunkenShips['Carrier'].width_ship = self.firebtn[self.cpuCoor['Carrier'][0]].size[0]
                                    self.sunkenShips['Carrier'].height_ship = self.firebtn[self.cpuCoor['Carrier'][0]].size[1]*5
                                    self.sunkenShips['Carrier'].pos = self.firebtn[self.cpuCoor['Carrier'][4]].pos
                                    self.sunkenShips['Carrier'].value = 0
                                for hits in range(0,5):
                                    self.ids.radarScreen.remove_widget(self.fireMark[self.cpuCoor['Carrier'][hits]])
                                self.ids.radarScreen.add_widget(self.sunkenShips['Carrier'])
                                self.ids.usrInfo.text = 'Enemy %s sunk!' %name
                        if name == 'Battleship':
                            self.playerScore['Battleship']-= 1
                            self.fireMark[str(instance.id)] = hitPin(width_shot=instance.size[0],
                            height_shot=instance.size[1],
                            file_pin='battleship_hit.png',
                            pos=instance.pos)
                            self.ids.radarScreen.add_widget(self.fireMark[str(instance.id)])
                            if self.playerScore['Battleship'] == 0:
                                if self.cpuCoor['Battleship'][0].split(',')[1] != self.cpuCoor['Battleship'][1].split(',')[1]:
                                    self.sunkenShips['Battleship'].width_ship = self.firebtn[self.cpuCoor['Battleship'][0]].size[1]
                                    self.sunkenShips['Battleship'].height_ship = self.firebtn[self.cpuCoor['Battleship'][0]].size[0]*4
                                    self.sunkenShips['Battleship'].pos = self.firebtn[self.cpuCoor['Battleship'][0]].pos
                                    self.sunkenShips['Battleship'].value = 90
                                else:
                                    self.sunkenShips['Battleship'].width_ship = self.firebtn[self.cpuCoor['Battleship'][0]].size[0]
                                    self.sunkenShips['Battleship'].height_ship = self.firebtn[self.cpuCoor['Battleship'][0]].size[1]*4
                                    self.sunkenShips['Battleship'].pos = self.firebtn[self.cpuCoor['Battleship'][3]].pos
                                    self.sunkenShips['Battleship'].value = 0
                                for hits in range(0,4):
                                    self.ids.radarScreen.remove_widget(self.fireMark[self.cpuCoor['Battleship'][hits]])
                                self.ids.radarScreen.add_widget(self.sunkenShips['Battleship'])
                                self.ids.usrInfo.text = 'Enemy %s sunk!' %name
                        if name == 'Submarine':
                            self.playerScore['Submarine']-= 1
                            self.fireMark[str(instance.id)] = hitPin(width_shot=instance.size[0],
                            height_shot=instance.size[1],
                            file_pin='submarine_hit.png',
                            pos=instance.pos)
                            self.ids.radarScreen.add_widget(self.fireMark[str(instance.id)])
                            if self.playerScore['Submarine'] == 0:
                                if self.cpuCoor['Submarine'][0].split(',')[1] != self.cpuCoor['Submarine'][1].split(',')[1]:
                                    self.sunkenShips['Submarine'].width_ship = self.firebtn[self.cpuCoor['Submarine'][0]].size[1]
                                    self.sunkenShips['Submarine'].height_ship = self.firebtn[self.cpuCoor['Submarine'][0]].size[0]*3
                                    self.sunkenShips['Submarine'].pos = self.firebtn[self.cpuCoor['Submarine'][0]].pos
                                    self.sunkenShips['Submarine'].value = 90
                                else:
                                    self.sunkenShips['Submarine'].width_ship = self.firebtn[self.cpuCoor['Submarine'][0]].size[0]
                                    self.sunkenShips['Submarine'].height_ship = self.firebtn[self.cpuCoor['Submarine'][0]].size[1]*3
                                    self.sunkenShips['Submarine'].pos = self.firebtn[self.cpuCoor['Submarine'][2]].pos
                                    self.sunkenShips['Submarine'].value = 0
                                for hits in range(0,3):
                                    self.ids.radarScreen.remove_widget(self.fireMark[self.cpuCoor['Submarine'][hits]])
                                self.ids.radarScreen.add_widget(self.sunkenShips['Submarine'])
                                self.ids.usrInfo.text = 'Enemy %s sunk!' %name
                        if name == 'Destroyer':
                            self.playerScore['Destroyer']-= 1
                            self.fireMark[str(instance.id)] = hitPin(width_shot=instance.size[0],
                            height_shot=instance.size[1],
                            file_pin='destroyer_hit.png',
                            pos=instance.pos)
                            self.ids.radarScreen.add_widget(self.fireMark[str(instance.id)])
                            if self.playerScore['Destroyer'] == 0:
                                if self.cpuCoor['Destroyer'][0].split(',')[1] != self.cpuCoor['Destroyer'][1].split(',')[1]:
                                    self.sunkenShips['Destroyer'].width_ship = self.firebtn[self.cpuCoor['Destroyer'][0]].size[1]
                                    self.sunkenShips['Destroyer'].height_ship = self.firebtn[self.cpuCoor['Destroyer'][0]].size[0]*3
                                    self.sunkenShips['Destroyer'].pos = self.firebtn[self.cpuCoor['Destroyer'][0]].pos
                                    self.sunkenShips['Destroyer'].value = 90
                                else:
                                    self.sunkenShips['Destroyer'].width_ship = self.firebtn[self.cpuCoor['Destroyer'][0]].size[0]
                                    self.sunkenShips['Destroyer'].height_ship = self.firebtn[self.cpuCoor['Destroyer'][0]].size[1]*3
                                    self.sunkenShips['Destroyer'].pos = self.firebtn[self.cpuCoor['Destroyer'][2]].pos
                                    self.sunkenShips['Destroyer'].value = 0
                                for hits in range(0,3):
                                    self.ids.radarScreen.remove_widget(self.fireMark[self.cpuCoor['Destroyer'][hits]])
                                self.ids.radarScreen.add_widget(self.sunkenShips['Destroyer'])
                                self.ids.usrInfo.text = 'Enemy %s sunk!' %name
                        if name == 'Patrolboat':
                            self.playerScore['Patrolboat']-= 1
                            self.fireMark[str(instance.id)] = hitPin(width_shot=instance.size[0],
                            height_shot=instance.size[1],
                            file_pin='patrolboat_hit.png',
                            pos=instance.pos)
                            self.ids.radarScreen.add_widget(self.fireMark[str(instance.id)])
                            if self.playerScore['Patrolboat'] == 0:
                                if self.cpuCoor['Patrolboat'][0].split(',')[1] != self.cpuCoor['Patrolboat'][1].split(',')[1]:
                                    self.sunkenShips['Patrolboat'].width_ship = self.firebtn[self.cpuCoor['Patrolboat'][0]].size[1]
                                    self.sunkenShips['Patrolboat'].height_ship = self.firebtn[self.cpuCoor['Patrolboat'][0]].size[0]*2
                                    self.sunkenShips['Patrolboat'].pos = self.firebtn[self.cpuCoor['Patrolboat'][0]].pos
                                    self.sunkenShips['Patrolboat'].value = 90
                                else:
                                    self.sunkenShips['Patrolboat'].width_ship = self.firebtn[self.cpuCoor['Patrolboat'][0]].size[0]
                                    self.sunkenShips['Patrolboat'].height_ship = self.firebtn[self.cpuCoor['Patrolboat'][0]].size[1]*2
                                    self.sunkenShips['Patrolboat'].pos = self.firebtn[self.cpuCoor['Patrolboat'][1]].pos
                                    self.sunkenShips['Patrolboat'].value = 0
                                for hits in range(0,2):
                                    self.ids.radarScreen.remove_widget(self.fireMark[self.cpuCoor['Patrolboat'][hits]])
                                self.ids.radarScreen.add_widget(self.sunkenShips['Patrolboat'])
                                self.ids.usrInfo.text = 'Enemy %s sunk!' %name
                        if self.playerScore['Total'] == 0:
                            self.ids.usrInfo.text = 'You Won!'
                            self.playerWon = True
                            self.playerWin()
                if self.playerWon != True:
                    if multiplayer:
                        self.recvTimer()
                    else:
                        self.computerShot()
                if self.playerWon == True:
                    if multiplayer:
                        client.send(player_ID + instance.id)
                    if seaman:
                        scoresSeaman['wins'] += 1
                        store.put("Seaman", scores=scoresSeaman)
                        if self.playerNoShots < store.get('Seaman')['scores']['lowest_shots']:
                            scoresSeaman['lowest_shots'] = self.playerNoShots
                            store.put("Seaman", scores=scoresSeaman)
                    if captain:
                        scoresCaptain['wins'] += 1
                        store.put("Captain", scores=scoresCaptain)
                        if self.playerNoShots < store.get('Captain')['scores']['lowest_shots']:
                            scoresCaptain['lowest_shots'] = self.playerNoShots
                            store.put("Captain", scores=scoresCaptain)
                    if admiral:
                        scoresAdmiral['wins'] += 1
                        store.put("Admiral", scores=scoresAdmiral)
                        if self.playerNoShots < store.get('Admiral')['scores']['lowest_shots']:
                            scoresAdmiral['lowest_shots'] = self.playerNoShots
                            store.put("Admiral", scores=scoresAdmiral)
                    if multiplayer:
                        scoresMulti['wins'] += 1
                        store.put("Multi", scores=scoresMulti)
                        if self.playerNoShots < store.get('Multi')['scores']['lowest_shots']:
                            scoresMulti['lowest_shots'] = self.playerNoShots
                            store.put("Multi", scores=scoresMulti)
                    self.playerWon = False
global sm
sm = ScreenManager(transition=SlideTransition())

class navalassault(App):
    def build(self):
        sm.add_widget(SelectLevel(name='menu'))
        sm.add_widget(LoseGameDialog(name='lose'))
        sm.add_widget(WinGameDialog(name='win'))
        sm.add_widget(HelpScreen(name='help'))
        sm.add_widget(CreditScreen(name='credits'))
        sm.add_widget(SonarGridHelp(name='sonar'))
        sm.add_widget(PlacementHelp(name='placement'))
        sm.add_widget(BattleMatchHelp(name='battle'))
        sm.add_widget(MultiPlayerGame(name='multi'))
        sm.add_widget(rootScreen(name='game'))
        self.initilize_global_vars()
        return sm

    def initilize_global_vars(self):
        from kivy.storage.jsonstore import JsonStore
        from os.path import join
        global store
        if platform == 'android':
            data_dir = self.user_data_dir
            store = JsonStore(join(data_dir, 'playerScoreCard.json'))
        else:
            store = JsonStore("playerScoreCard.json")

        popScoreScards()

    def on_pause(self):
        return True

    def on_resume(self):
        pass

if __name__ == '__main__':
    navalassault().run()
