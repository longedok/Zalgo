import threading

import pymedia.muxer as muxer
import pymedia.audio.acodec as acodec
import pymedia.audio.sound as sound

class StreamPlayer(threading.Thread):
    __decoder = None
    __sound_device = None
    __is_playing = False
    
    def __init__(self):
        threading.Thread.__init__(self, name="StreamPlayer")
        self.__demuxer = muxer.Demuxer('mp3')
        self.__buffer = ''
        self.start()

    def add_chunk(self, chunk):
        self.__buffer += chunk

    def play(self):
        self.__is_playing = True

    def pause(self):
        self.__sound_device.pause()

    def unpause(self):
        self.__sound_device.unpause()

    def stop(self):
        self.__buffer = ''
        self.__sound_device.stop()
        self.__is_playing = False

    def run(self):
        rate = 1
        card = 0
        while True:
            frames = self.__demuxer.parse(self.__buffer)
            self.__buffer = ''
            for i, frame in enumerate(frames):
                time.sleep(0.01)
                if self.__is_playing:
                    #debug("frame %d/%d" % (i, len(frames)))
                    if self.__decoder == None:
                        self.__decoder = acodec.Decoder(self.__demuxer.streams[frame[0]])
                    raw = self.__decoder.decode(frame[1])
                    if raw and raw.data:
                        if self.__sound_device == None:
                            self.__sound_device = sound.Output(int(raw.sample_rate * rate), raw.channels, sound.AFMT_S16_LE, card)
                        self.__sound_device.play(raw.data)
                else:
                    break
