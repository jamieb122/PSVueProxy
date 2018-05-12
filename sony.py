
import globals
import json
import random
import cookielib
import getpass
import urllib
import requests
import sys
import os

TAG = "SONY: "

class SONY:
    settings = {}
    device_id = None
    username = ''
    password = ''
    npsso = ''
    reqPayload= ''
    EPGreqPayload=''
    verify = False


    def __init__(self):
        # check to see if data has been stored, if not create the file

        self.parse_settings_file()
        self.check_login()
        self.authorize_device()
        self.set_profile()
        self.write_req_payload()


    def get_user_profile(self):
        url = "https://sentv-user-ext.totsuko.tv/sentv_user_ext/ws/v2/profile/ids"

        headers = {
            "User-Agent": globals.UA_ANDROID_TV,
            "reqPayload" : self.reqPayload,
            "Accept": "*/*",
            "Origin": "https://themis.dl.playstation.net",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "X-Requested-With": "com.snei.vue.atv"
        }

        r = requests.get(url, headers=headers, verify=self.verify)

        if 'body' in r.json() and 'profiles' in r.json()['body']:
            profiles = r.json()['body']['profiles']
            prof_dict = {}
            prof_list = []
            print(TAG + "Profile not set getting available profiles")
            for profile in profiles:
                prof_dict[str(profile['profile_name'])] = str(profile['profile_id'])
                prof_list.append(str(profile['profile_name']))
                print(TAG + "Profile Name: " + str(profile['profile_name']))

            selected_profile = raw_input("Please enter profile name: ")
            while selected_profile not in prof_list:
                print(TAG + "Invalid profile name")
                selected_profile = raw_input("Please enter profile name: ")

            globals.save_setting("default_profile", str(prof_dict[selected_profile]))
        else:
            print TAG + "ERROR: Could not retrieve profile list"
            sys.exit()

    def set_profile(self):

        # If default profile is not set, then ask the user
        if not globals.get_setting("default_profile"):
            profile_id = self.get_user_profile()


        url = "https://sentv-user-ext.totsuko.tv/sentv_user_ext/ws/v2/profile/" + globals.get_setting("default_profile")

        headers = {
            "User-Agent": globals.UA_ANDROID_TV,
            "reqPayload": self.reqPayload,
            "Accept": "*/*",
            "Origin": "https://themis.dl.playstation.net",
            "Host": "sentv-user-ext.totsuko.tv",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "X-Requested-With": "com.snei.vue.atv"
        }

        r = requests.get(url, headers=headers, verify=self.verify)
        self.EPGreqPayload = str(r.headers['reqPayload'])
        globals.save_setting("EPGreqPayload", self.EPGreqPayload)
        auth_time = r.json()['header']['time_stamp']
        globals.save_setting("last_auth", auth_time)


    def authorize_device(self):
        url = "https://sentv-user-auth.totsuko.tv/sentv_user_auth/ws/oauth2/token"
        url += "?device_type_id=" + globals.DEVICE_TYPE
        url += "&device_id=" + self.device_id
        url += "&code=" + self.get_grant_code()     #TODO: Implement function
        url += "&redirect_uri=" + urllib.quote_plus(globals.THEMIS)

        headers = {
            "Origin": "https://themis.dl.playstation.net",
            "User-Agent": globals.UA_ANDROID_TV,
            "Accept": "*/*",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "X-Requested-With": "com.snei.vue.atv"
        }

        r = requests.get(url, headers=headers, verify=self.verify)
        device_status = str(r.json()["body"]["status"])

        print TAG + "Device Status = " + device_status

        if self.reqPayload != '':
            headers['reauth'] = '1'
            headers['reqPayload'] = self.reqPayload

        if device_status == "UNAUTHORIZED":
            auth_error = str(r.json()['header']['error']['message'])
            error_code = str(r.json()['header']['error']['code'])
            print TAG + "Auth Error : " + auth_error + "(" + error_code + ")"

        elif 'reqPayload' in r.headers:
            self.reqPayload = str(r.headers['reqPayload'])
            globals.save_setting("reqPayload", self.reqPayload)
            auth_time = r.json()['header']['time_stamp']
            globals.save_setting("last_auth", auth_time)
            print TAG + "setting last auth time"

        else:
            print(TAG + "[-] ERROR: Could not authorize device: reqPayload: " + str(self.reqPayload))
            sys.exit()


    def get_grant_code(self):
        url = globals.API_URL  + "/oauth/authorize"
        url += "?request_theme=tv"
        url += "&ui=ds"
        url += "&client_id=" + globals.REQ_CLIENT_ID
        url += "&hidePageElements=noAccountSelection"
        url += "&redirect_uri=" + urllib.quote_plus(globals.THEMIS)
        url += "&request_locale=en"
        url += "&response_type=code"
        url += "&resolution=1080"
        url += "&scope=psn%3As2s"
        url += "&service_logo=ps"
        url += "&smcid=tv%3Apsvue"
        url += "&duid=" + self.device_id

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US",
            "User-Agent": globals.UA_ANDROID_TV,
            "Connection": "Keep-Alive",
            "X-Requested-With": "com.snei.vue.atv"
        }

        code = ''

        r = requests.get(url, headers=headers, allow_redirects=False, cookies=globals.load_cookies(), verify=self.verify)

        if "X-NP-GRANT-CODE" in r.headers:
            code = r.headers["X-NP-GRANT-CODE"]
            globals.save_cookies(r.cookies)
        else:
            print(TAG + "[-] ERROR: Could not get grant code")

        return code

    def check_login(self):
        '''Check to see if member is current logged in
        This utilizes the cookie lib; after login the cookie SSO cookie is stored'''
        expired_cookies = True  #default is to force login unless a valid unexpired cookie is found

        try:
            cj = cookielib.LWPCookieJar()
            cj.load(globals.COOKIE_FILE, ignore_discard=True)

            if self.npsso != '':    #if it is set, check to see if cookie expired
                for cookie in cj:
                    if cookie.name == 'npsso':
                        expired_cookies = cookie.is_expired()
                        break
        except:
            print(TAG + "[-] ERROR: Could not find npsso cookie")
            pass

        if expired_cookies:
            print(TAG + " not logged in, logging in")
            self.login()

    def login(self):
        url = globals.API_URL + '/ssocookie' #request a single sign on cookie

        headers = {"Accept": "*/*",
                   "Content-type": "application/x-www-form-urlencoded",
                   "Origin": "https://id.sonyentertainmentnetwork.com",
                   "Accept-Language": "en-US, en; q=0.8",
                   "Accept-Encoding": "deflate",
                   "User-Agent": globals.UA_ANDROID_TV,
                   "X-Requested-With": "com.snei.vue.atv",
                   "Connection": "Keep-Alive"}

        payload = "authentication_type=password&username="+urllib.quote_plus(self.username)+"&password="+urllib.quote_plus(self.password)+"&client_id="+globals.ANDROID_TV_CLIENT_ID
        r = requests.post(url, headers=headers, cookies = globals.load_cookies(), data=payload, verify=self.verify)
        json_source = r.json()
        globals.save_cookies(r.cookies)

        if 'npsso' in json_source:
            npsso = json_source['npsso']
            globals.save_setting('npsso', npsso)
            self.set_profile()
            print(TAG + "Login success")
        elif 'authentication_type' in json_source:
            if json_source['authentication_type'] == 'two_step':
                ticket_uuid = json_source['ticket_uuid']
                self.two_step_verification(ticket_uuid)
        elif 'error_description' in json_source:
            print(TAG + "[-] ERROR: Login error - " + json_source['error_description'])
            sys.exit()
        else:
            #something bas must have happened
            print(TAG + "[-] ERROR: Login error (generic)")
            sys.exit()

        self.write_req_payload()

    def write_req_payload(self):
        # save of the current epg req payload
        save_dir = os.path.dirname(os.path.realpath(__file__))
        req_payload_file = open(os.path.join(save_dir, "reqPayload.dat"), "w")

        contents = "COOKIE=\""
        contents += globals.get_setting("EPGreqPayload")
        contents += "\""

        req_payload_file.write(contents)
        req_payload_file.close()

    def two_step_verification(self, ticket_uuid):
        code = raw_input("Code: ")
        if code == '': sys.exit()

        url = globals.API_URL + '/sso_cookie'

        headers = {"Accept": "*/*",
                   "Content-type": "application/x-www-form-urlencoded",
                   "Origin": "https://id.sonyentertainmentnetwork.com",
                   "Accept-Language": "en-US, en;q=0.8",
                   "User-Agent": globals.UA_ANDROID_TV,
                   "Connection": "Keep-Alive",
                   "Referer": "https://id.sonyentertainmentnetwork.com/signin/?service_entity=urn:service-entity:psn&ui=pr&service_logo=ps&response_type=code&scope=psn:s2s&client_id="+globals.REQ_CLIENT_ID+"&request_locale=en_US&redirect_uri=https://io.playstation.com/playstation/psn/acceptLogin&error=login_required&error_code=4165&error_description=User+is+not+authenticated"
                   }
        payload = 'authentication_type=two_step&ticket_uuid='+ticket_uuid+'&code='+code+'&client_id='+globals.LOGIN_CLIENT_ID
        r = requests.post(url, headers=headers, cookies=globals.load_cookies(), data=payload, verify=verify)
        json_source = r.json()
        globals.save_cookies(r.cookies)

        if 'npsso' in json_source:
            npsso = json_source['npsso']
            globals.save_setting("npsso", json_source['npsso'])
            print(TAG + "Two factor login success")
        elif 'error_description' in json_source:
            print(TAG + "[-] ERROR: Login error - " + json_source['error_description'])
            sys.exit()
        else:
            print(TAG + "[-] ERROR: Login error (generic)")
            sys.exit()

    def create_device_id(self):

        if(self.device_id == None):
            android_id = ''.join(random.choice('0123456789abcdef') for i in range(16))
            android_id = android_id.rjust(30, '0')
            manufacturer = 'Asus'
            model = 'Nexus 7'
            manf_model = ":%s:%s" % (manufacturer.rjust(10,' '), model.rjust(10, ' '))
            manf_model = manf_model.encode("hex").upper()
            zero = '0'
            device_id = "0000%s%s01a8%s%s" % ("0007", "0002", android_id, manf_model + zero.ljust(32, '0'))

            print(TAG + "Device ID generated " + device_id)

            globals.save_setting("device_id", device_id)

        #else, don't do anything


    def parse_settings_file(self):

        dataFile = open(globals.DATA_FILE, "a+")
        settingsFileJson="{}"

        try:
            dataFileContents = json.load(dataFile)
        except:
            print(TAG + "No valid JSON found, probably a first run")
            dataFile.seek(0, 0)
            dataFile.truncate()
            dataFile.write("{}")
            dataFile.close()

        if not globals.get_setting("device_id"):
            self.create_device_id()
        else:
            self.device_id = globals.get_setting("device_id")

        if not globals.get_setting("username"):
            globals.save_setting("username", raw_input("Username: "))
        else:
            self.username = globals.get_setting("username")

        if not globals.get_setting("password"):
            globals.save_setting("password", getpass.getpass("Password: "))
        else:
            self.password = globals.get_setting("password")

        if globals.get_setting("npsso"):
            self.npsso = globals.get_setting("npsso")

        if globals.get_setting("reqPayload"):
            self.reqPayload = globals.get_setting("reqPayload")

    def get_json(self, url):
        #TODO: Check to see if cookie is expired and re-authenticate to get new EPGReqPayload
        headers = {
            "Accept": "*/*",
            "reqPayload": globals.get_setting("EPGreqPayload"),
            "User-Agent": globals.UA_ANDROID_TV,
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "X-Requested-With": "com.snei.vue.android",
            "Connection": "keep-alive"
        }

        r = requests.get(url, headers=headers, cookies=globals.load_cookies(), verify=self.verify)

        if r.status_code != 200:
            print(TAG + "ERROR - could not complete json request: ")
            try:
                json_source = r.json()
                print(TAG + "\t" + json_source['header']['error']['message'])
            except:
                pass
            sys.exit()

        return r.json()


    def get_channel_list(self):
        json_source = self.get_json(globals.EPG_URL + "/browse/items/channels/filter/all/sort/channeltype/offset/0/size/500")
        channel_list = []
        for channel in json_source['body']['items']:
            title = channel['title']
            if channel['channel_type'] == 'linear':
                channel_id = str(channel['id'])
                logo = None
                for image in channel['urls']:
                    if 'width' in image:
                        if image['width'] == 600 or image['width'] == 440:
                            logo = image['src']
                            break

                channel_list.append([channel_id, title, logo])

        return channel_list

    def epg_get_stream(self, url):
        headers = {
            "Accept": "*/*",
            "Content-type": "application/x-www-form-urlencoded",
            "Origin": "https://vue.playstation.com",
            "Accept-Language": "en-US,en;q=0.8",
            "Referer": "https://vue.playstation.com/watch/live",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": globals.UA_ANDROID_TV,
            "Connection": "Keep-Alive",
            "Host": "media-framework.totsuko.tv",
            "reqPayload": globals.get_setting("EPGreqPayload"),
            "X-Requested-With": "com.snei.vue.android"
        }

        r = requests.get(url, headers=headers, cookies = globals.load_cookies(), verify=globals.VERIFY)
        json_source = r.json()
        stream_url = json_source['body']['video']

        return stream_url
