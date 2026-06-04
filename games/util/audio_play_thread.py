# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: audio_play_thread.py
import sys, threading, time, traceback, loguru, numpy as np, pygame
from audio_play import audio

class AudioPlayThread(threading.Thread):

    def __init__(self, clip_audio, buffersize=4096, nbytes=2):
        threading.Thread.__init__(self)
        audio_init = audio.Audio().get_init()
        self.running_state = True
        self.clip_audio = clip_audio
        self.fps = audio_init[0]
        self.buffersize = buffersize
        self.nbytes = nbytes

    def run(self):
        fps = self.fps
        clip = self.clip_audio
        self.running_end = False
        if clip:
            loguru.logger.info("AudioPlayThread running")
            try:
                buffersize = self.buffersize
                nbytes = self.nbytes
                totalsize = int(fps * clip.duration)
                pospos = np.array(list(range(0, totalsize, buffersize)) + [totalsize])
                tt = 1.0 / fps * np.arange(pospos[0], pospos[1])
                sndarray = clip.to_soundarray(tt, nbytes=nbytes, quantize=True)
                chunk = pygame.sndarray.make_sound(sndarray)
                channel = chunk.play()
                lenght = 0
                for i in range(1, len(pospos) - 1):
                    if self.running_state:
                        tt = 1.0 / fps * np.arange(pospos[i], pospos[i + 1])
                        sndarray = clip.to_soundarray(tt, nbytes=nbytes, quantize=True)
                        chunk = pygame.sndarray.make_sound(sndarray)
                        lenght = chunk.get_length()
                        chunk.play()
                        if lenght > 4:
                            break
                        time.sleep(lenght)
                    else:
                        break

            except:
                loguru.logger.error("audio thread running except {}", traceback.format_exc())

            self.running_end = True
            loguru.logger.info("audio thread running end. {}", lenght)

# okay decompiling /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/util/audio_play_thread.pyc
