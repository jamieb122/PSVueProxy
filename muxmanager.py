import globals
import sony
import os
import stat
import urllib

class MuxManager():
    sonyObj = None

    def __init__(self, s):
        self.sonyObj = s
        pass

    def generate_playlist(self):

        save_dir = os.path.dirname(os.path.realpath(__file__))

        self.sonyObj.check_login()
        channel_list = self.sonyObj.get_channel_list()

        m3u_file = open(os.path.join(save_dir, "playlist.m3u"), "w")
        m3u_file.write("#EXTM3U")
        m3u_file.write("\n")

        for channel_id, title, logo in channel_list:

            """pipe:///tmp/test.sh http://dsc-animalplanet-live-sonytv-i.akamaihd.net/npid=48B65C3665A42DBEC5E0ACF95450DBC23EC089405CB7B4B47D5103E210DAABAB&deviceid=android_tv&e=1526144299&hmac=66be0727a7735bb62e4eb766ae1d7c95f0699a67/PROD01/sony/DSC_ANIMALPLANET/live/master_wired_ads.m3u8"""

            url = "pipe://" + os.path.join(save_dir, "pipe.sh ")
            url += "\"http://127.0.0.1:"+str(globals.PORT) + "/psvue?params=" + urllib.quote(globals.CHANNEL_URL + channel_id) + "\""

            m3u_file.write("\n")
            channel_info = '#EXTINF:-1 tvg-id="' + channel_id + '" tvg-name="' + title + '"'

            if logo is not None: channel_info += ' tvg-logo="' + logo + '"'
            channel_info += ' group_title="PS Vue",' + title

            m3u_file.write(channel_info.encode("utf-8") + "\n")
            m3u_file.write(url + "\n")

        m3u_file.close()



        pass

    def get_playlist(self):
        save_dir = os.path.dirname(os.path.realpath(__file__))
        m3u_file = open(os.path.join(save_dir, "playlist.m3u"), "r")

        playlist = m3u_file.read()

        m3u_file.close()

        return playlist


    def generate_pipe_shell_file(self):
        save_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(save_dir, "pipe.sh")
        pipe_shell_file = open(file_path, "w")

        file_contents = "#!/bin/sh"
        file_contents += "\n\n"
        file_contents += ". \"" + os.path.join(save_dir, "reqPayload.dat") + "\""
        file_contents += "\n\n"
        file_contents += "/usr/bin/ffmpeg -loglevel fatal -headers 'Cookie: reqPayload=\"'$COOKIE'\"' -user_agent \"Adobe Primetime/1.4 Dalvik/2.1.0 (Linux; U; Android 6.0.1 Build/MOB31H)\" -i $1 -acodec copy -vcodec copy -f mpegts pipe:1"

        pipe_shell_file.write(file_contents)

        pipe_shell_file.close()

        st = os.stat(file_path)
        os.chmod(file_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXUSR | stat.S_IXOTH)

        pass