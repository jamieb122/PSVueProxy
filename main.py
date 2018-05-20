from sony import SONY
from muxmanager import MuxManager

import time
import webservice

TAG = "Main: "


#makes sure we have preferences etc and logs in to sony; also allows us to retrieve the channel list
s = SONY()

muxManager = MuxManager(s)

#initialization
muxManager.generate_playlist()
muxManager.generate_pipe_shell_file()

#create and start the web service
web_server = webservice.PSVueProxyWebService(s, muxManager)
web_server.start()


#could use this main loop to keep the m3u file updated
while True:
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
        web_server.stop()
        web_server.join(0)
        break

print(TAG + "Exiting....")


