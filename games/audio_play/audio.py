# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: audio.py
from pygame import mixer

class Audio:

    def get_init(self):
        init = mixer.get_init()
        return init

    def init(self):
        print("audio init")
        mixer.quit()
        mixer.init(buffer=4096)

    def play_sync(self, audio_name):
        mixer.music.load(audio_name)
        mixer.music.play()

    def play(self, audio_name):
        try:
            mixer.find_channel(force=True).play(mixer.Sound(audio_name))
        except:
            pass

    def stop(self):
        print("audio stop")
        mixer.stop()
        mixer.music.unload()

    def quit(self):
        mixer.quit()

    def queue(self, filename):
        try:
            if self.get_busy():
                mixer.music.queue(filename)
            else:
                self.play_bmg(filename)
        except:
            pass

    def get_busy(self):
        return mixer.music.get_busy()

    def play_bmg(self, audio_file_name, start_second=0, loops=0):
        ret = True
        time_tmp = 0
        try:
            mixer.music.load(audio_file_name)
            mixer.music.play(loops=loops, start=start_second)
        except:
            ret = False

        return ret

# okay decompiling /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/audio_play/audio.pyc
