import threading
import globals
import socket
import urllib
import sony

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urlparse import parse_qs

TAG = "WebService: "


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        sonyObj = self.server.sonyObj
        muxManager = self.server.muxManager

        if str(self.path)[0:6] == "/psvue":
            parameters = parse_qs(self.path[7:])
            channel_url = urllib.unquote(str(parameters["params"][0]))

            self.send_redirect(sonyObj.epg_get_stream(channel_url))

        elif str(self.path)[0:13] == "/playlist.m3u":
            self.send_response(200)
            self.send_header("Content-type", "Application/m3u")
            self.end_headers()
            self.wfile.write(muxManager.get_playlist())


    def send_redirect(self, stream_url):

        print(TAG + "Redirecting to: " + stream_url)

        self.send_response(303)

        headers = {
            "Content-type": "text/html;charset=utf-8",
            "Connection": "close",
            #"Host": "media-framework.totsuko.tv",
            "Location": stream_url,
            "Set-Cookie": 'reqPayload=' + '"' + globals.get_setting("EPGreqPayload") + '"' + '; Domain=totsuko.tv; Path=/'
        }

        for key in headers:
            try:
                value = headers[key]
                self.send_header(key, value)
            except Exception as e:
                pass

        self.end_headers()

        self.wfile.close()


class Server(HTTPServer):
    sonyObj = None
    muxManager = None

    def set_context(self, s, muxManager):
        self.sonyObj = s
        self.muxManager = muxManager

    def get_request(self):
        self.socket.settimeout(5.0)
        result = None
        while result is None:
            try:
                result = self.socket.accept()
            except socket.timeout:
                pass
        result[0].settimeout(1000)
        return result       #return the accepted socket


class ThreadedHTTPServer(ThreadingMixIn, Server):
    """"Handle requests in a separate thread"""


class PSVueProxyWebService(threading.Thread):

    port = 0
    httpd = None
    hostname = "127.0.0.1"


    def __init__(self, s, muxManager):
        #TODO: Make the port dynamic based  on script parameters
        self.port = globals.PORT

        if  self.httpd == None:
            socket.setdefaulttimeout(10)
            server_class = ThreadedHTTPServer
            self.httpd = server_class((self.hostname, self.port), RequestHandler)
            self.httpd.set_context(s, muxManager)

        threading.Thread.__init__(self)

    def run(self):
        try:
            self.httpd.serve_forever()
        except Exception as e:
            print(TAG + "Server closing: " + e.message)

    def stop(self):
        try:
            self.httpd.server_close()
        except Exception as e:
            print(TAG + "Could not close the server: " + e.message)

        self.join(0)   #wait for server to stop serving before returning

