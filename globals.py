import json
import cookielib
from databasemanager import DatabaseManager

DATA_FILE = "datafile.dat"
COOKIE_FILE = "cookies.lwp"
API_URL = "https://auth.api.sonyentertainmentnetwork.com/2.0"
UA_ANDROID_TV = "Mozilla/5.0 (Linux; Android 6.0.1; Hub Build/MHC19J; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/61.0.3163.98 Safari/537.36"
UA_ADOBE = "Adobe Primetime/1.4 Dalvik/2.1.0 (Linux; U; Android 6.0.1 Build/MOB31H"
ANDROID_TV_CLIENT_ID = "0a5fe341-cb16-47d9-991e-0110fff49713"
REQ_CLIENT_ID = "dee6a88d-c3be-4e17-aec5-1018514cee40"
LOGIN_CLIENT_ID = "71a7beb8-f21a-47d9-a604-2e71bee24fe0"
DEVICE_TYPE = "android_tv"
EPG_URL = "https://epg-service.totsuko.tv/epg_service_sony/service/v2"
THEMIS = "https://themis.dl.playstation.net/themis/destro/redirect.html"
CHANNEL_URL = "https://media-framework.totsuko.tv/media-framework/media/v2.1/stream/channel/"
PORT = 54321
TAG = "Globals: "
VERIFY = False

def save_setting(key, value):
    print(TAG, "saving setting " + key + ", " + value)
    database_manager = DatabaseManager()
    database_manager.save_setting(key, value)


def get_setting(key):

    database_manager = DatabaseManager()

    value = database_manager.get_setting(key)

    if value is None:
        print(TAG + "setting("+key+") not found")
        return False
    else:
        print(TAG + "Retrieved setting[" + key + "]: " + str(value))
        return value


def get_all_settings():
    settingsFile = open(DATA_FILE)

    try:
        settingsFileContents = json.load(settingsFile)
    except:
        print(TAG + "could not load settings file as JSON")
        return None

    settingsFile.close()

    return settingsFileContents

def save_cookies(cookie_jar):
    cj = cookielib.LWPCookieJar()

    try:
        cj.load(COOKIE_FILE, ignore_discard=True)
    except:
        pass

    for c in cookie_jar:
        args = dict(vars(c).items())
        args['rest'] = args['_rest']
        del args['_rest']
        c = cookielib.Cookie(**args)
        cj.set_cookie(c)

    cj.save(COOKIE_FILE, ignore_discard=True)

def load_cookies():
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(COOKIE_FILE, ignore_discard=True)
    except:
        pass
    return cj
