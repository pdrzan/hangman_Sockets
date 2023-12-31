import threading
import time
import json
import hashlib
from socket import *

# message pattern
# ' ' is the separator
# message[0]: id
# message[1]: type


def requestUDP(message, address):
    message = message.decode('utf-8').split()
    print("Recived:\n", message)
    if (message[1] == 'login'):
        if not verifyUserExistence(message[3]):
            registerUser(message[2], message[3], message[4])
            authenticationSucess(message[0], address)
            addUserOnline(message[3], address[0], address[1])
        elif verifyPassword(message[3], message[4]):
            addUserOnline(message[3], address[0], address[1])
            authenticationSucess(message[0], address)
        else:
            authenticationFailed(message[0], address)

    elif (message[1] == 'disconnect'):
        if verifyUserOnline(message[2], address):
            delUserOnline(message[2])
        else:
            notLogged(message[0], address)
    elif (message[1] == 'listOnline'):
        # user // pattern
        if verifyUserOnline(message[2], address):
            sendMessage(f"{message[0]} {returnUsersOnline()}", address)
        else:
            notLogged(message[0], address)
    elif (message[1] == 'listPlaying'):
        # user // pattern
        if verifyUserOnline(message[2], address):
            sendMessage(f"{message[0]} {returnUsersPlaying()}", address)
        else:
            notLogged(message[0], address)
    elif (message[1] == 'userInformation'):
        # user opponent // pattern
        if verifyUserOnline(message[2], address):
            sendMessage(
                f"{message[0]} {returnOpponent(message[3])}", address)
        else:
            notLogged(message[0], address)
    elif (message[1] == 'playing'):
        if verifyUserOnline(message[2], address):
            addUsersPlaying(message[2], message[3])
        else:
            notLogged(message[0], address)
    elif (message[1] == 'stopPlaying'):
        if verifyUserOnline(message[2], address):
            delUsersPlaying(message[2], message[3])
        else:
            notLogged(message[0], address)


def sendMessage(message, address):
    print("Sent:\n", message)
    serverSocket.sendto(bytes(message, 'utf-8'), address)


def notLogged(idMessage, address):
    sendMessage(f"{idMessage} Not logged in", address)


def authenticationFailed(idMessage, address):
    sendMessage(f"{idMessage} Authentication failed", address)


def authenticationSucess(idMessage, address):
    sendMessage(f"{idMessage} Successfully authenticated", address)


def formatIntSizeTwo(number):
    return f'{number:02d}'


def registerLog(users, type):
    localTime = time.localtime()
    localTime = f"{formatIntSizeTwo(localTime.tm_hour)}:{formatIntSizeTwo(localTime.tm_min)}:{formatIntSizeTwo(localTime.tm_sec)} {formatIntSizeTwo(localTime.tm_mday)}/{formatIntSizeTwo(localTime.tm_mon)}/{localTime.tm_year}"
    if (type == 'register'):
        appendData('../Data/game.log',
                   f"{localTime}: User {users[0]} registered\n")
    elif (type == 'connect'):
        appendData('../Data/game.log',
                   f"{localTime}: User {users[0]} connected\n")
    elif (type == 'timeout'):
        appendData('../Data/game.log',
                   f"{localTime}: User {users[0]} does not reply (timeout)\n")
    elif (type == 'inactive'):
        appendData('../Data/game.log',
                   f"{localTime}: User {users[0]} became inactive\n")
    elif (type == 'active'):
        appendData('../Data/game.log',
                   f"{localTime}: User {users[0]} became active\n")
    elif (type == 'playing'):
        appendData('../Data/game.log',
                   f"{localTime}: Users {users[0]} and {users[1]} are playing\n")
    elif (type == 'stopPlaying'):
        appendData('../Data/game.log',
                   f"{localTime}: Users {users[0]} and {users[1]} are not playing anymore\n")
    elif (type == 'disconnect'):
        appendData('../Data/game.log',
                   f"{localTime}: User {users[0]} disconnected\n")


def addUserOnline(user, ip, port):
    usersOnline[user] = {'status': 'inactive', 'ip': ip, 'port': port}
    registerLog([user], 'connect')


def changeStatusUserOnline(user):
    if usersOnline[user]['status'] == 'active':
        usersOnline[user]['status'] = 'inactive'
        registerLog([user], 'inactive')
    else:
        usersOnline[user]['status'] = 'active'
        registerLog([user], 'active')


def delUserOnline(user):
    usersOnline.pop(user)
    registerLog([user], 'disconnect')


def verifyUserOnline(user, address):
    if user in usersOnline and usersOnline[user]['ip'] == address[0] and usersOnline[user]['port'] == address[1]:
        return True
    return False


def returnUserData(user):
    return f"User: {user} / Status: {usersOnline[user]['status']} / Ip: {usersOnline[user]['ip']} / Port: {usersOnline[user]['port']}"


def returnOpponent(user):
    if user in usersOnline:
        return f"{usersOnline[user]['ip']} {usersOnline[user]['port']}"
    return "Opponent not found"


def returnUsersOnline():
    stringAnswer = ''
    for user in usersOnline:
        stringAnswer = f"{stringAnswer}{returnUserData(user)}\n"
    return stringAnswer


def addUsersPlaying(firstUser, secondUser):
    usersPlaying[firstUser + 'X' + secondUser] = {'ip': [usersOnline[firstUser]['ip'], usersOnline[secondUser]['ip']], 'port': [
        usersOnline[firstUser]['port'], usersOnline[secondUser]['port']]}
    registerLog([firstUser, secondUser], 'playing')
    changeStatusUserOnline(firstUser)
    changeStatusUserOnline(secondUser)


def delUsersPlaying(firstUser, secondUser):
    usersPlaying.pop(firstUser + 'X' + secondUser)
    registerLog([firstUser, secondUser], 'stopPlaying')
    changeStatusUserOnline(firstUser)
    changeStatusUserOnline(secondUser)


def returnMatch(match):
    users = match.split('X')
    return f"{users[0]}({usersPlaying[match]['ip'][0]}:{usersPlaying[match]['port'][0]}) X {users[1]}({usersPlaying[match]['ip'][1]}:{usersPlaying[match]['port'][1]})"


def returnUsersPlaying():
    stringAnswer = ''
    for match in usersPlaying:
        stringAnswer = f"{stringAnswer}{returnMatch(match)}"
    if len(usersPlaying) == 0:
        stringAnswer = "No users playing"
    return stringAnswer


def loadData(file):
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return (data)


def saveData(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def appendData(file, data):
    with open(file, "a", encoding="utf-8") as f:
        f.write(data)


def verifyUserExistence(user):
    if user in usersData:
        return True
    return False


def verifyPassword(user, password):
    h = hashlib.new('sha256')
    h.update(bytes(password, 'utf-8'))
    return usersData[user]['password'] == h.hexdigest()


def registerUser(name, user, password):
    h = hashlib.new('sha256')
    h.update(bytes(password, 'utf-8'))
    usersData[user] = {'name': name, 'password': h.hexdigest()}
    registerLog([user], 'register')
    saveData('../Data/loginData.json', usersData)


def deleteUser(user):
    usersData.pop(user)
    saveData('../Data/loginData.json', usersData)


serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(("", serverPort))
# serverSocket.listen(1)

# usersOnline format:
# {
#   'user':{
#       'status': 'active' | 'inactive',
#       'ip': '',
#       'port':
#       },
#   'userN': {...}
# }
usersOnline = {}

# usersPlaying format:
# {
#   '<first_user>X<second_user>':
#       {
#       ip: ['', ''],
#       port: ['', '']
#       },
#   '<first_user>X<second_user>':
#       {...}
# }
usersPlaying = {}


usersData = loadData('../Data/loginData.json')
# usersData format:
# {
#   'user':{
#       'name': '',
#       'password': '',
#       },
#   'userN': {...}
# }
while 1:
    (threading.Thread(target=requestUDP, args=(serverSocket.recvfrom(1024)))).start()
