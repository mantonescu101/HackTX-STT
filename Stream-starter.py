"""Basic streaming to Revs speech recognition API."""
from ws4py.client.threadedclient import WebSocketClient
import json
import time
import threading
import pyaudio
import wave
import pdb
import os
import dropbox
from rev_ai.speechrec import RevSpeechAPI
from apscheduler.schedulers.background import BackgroundScheduler

class TransferData:
    def __init__(self, access_token):
        self.access_token = access_token

    def upload_file(self, file_from, file_to):
        """upload a file to Dropbox using API v2
        """
        dbx = dropbox.Dropbox(self.access_token)

        with open(file_from, 'rb') as f:
            dbx.files_upload(f.read(), file_to)


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WAVE_OUTPUT_FILENAME = "output.wav"
TEXT_OUTPUT_FILENAME = "output.txt"
DROPBOX_FILE = "/HackTX/Presentation.txt"
RECORD_SECONDS = 15
MESSAGES = 0
DONE_JOB = 0



def rate_limited(max_per_second):
    """Decorator to limit the rate client sends data."""
    min_interval = 1.0 / float(max_per_second)

    def decorate(func):
        last_called = [0.0]

        def rate_limited_function(*args, **kargs):
            elapsed = time.clock() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kargs)
            last_called[0] = time.clock()
            return ret

        return rate_limited_function

    return decorate


class RevClient(WebSocketClient):
    """Client for streaming data to the server and receiving the responses."""

    @rate_limited(4)
    def send_data(self, data):
        self.send(data, binary=True)

    def send_file(self, audiofile, byterate):
        """Open and stream a file to the server.
        Creates an additional thread to stream.
        Note: socket is closed once the file is finished.
        """

        def send_data_to_ws():
            with open(audiofile, 'rb') as audiostream:
                block = audiostream.read(byterate // 4)
                while block:
                    self.send_data(block)
                    block = audiostream.read(byterate // 4)
            self.finish_session()

        t = threading.Thread(target=send_data_to_ws)
        t.start()

    def finish_session(self):
        """Close the socket by sending the end-of-sentence signal."""
        print('i ended socket')
        self.send("EOS")

    def received_message(self, m):
        global MESSAGES
        MESSAGES += 1
        print(str(MESSAGES))
        """Parse a transcript result."""
        response = json.loads(str(m))
        if response['status'] == 0:
            if 'result' in response:
                trans = response['result']['hypotheses'][0]['transcript']
                if response['result']['final']:
                    print("Final transcript: " + trans)
                else:
                    if len(trans) > 80:
                        trans = "... %s" % trans[-76:]
                    print(trans)


class Record(threading.Thread):

    def __init__(self, stream, out_file):
        super(Record, self).__init__()
        self.stream = stream
        wf = wave.open(out_file, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        self.out_file = wf

    def setInterval(self, interval):
        self._interval = interval

    def run(self):
        global frames
        while True:
            data = self.stream.read(CHUNK)
            frames.append(data)


def update_recording(input_file, client):
    while True:
        print('reading...')
        data = input_file.read(RATE // 4)
        if str(data) != "":
            client.send_data(data)


class Transcript(threading.Thread):

    def __init__(self, client, id):
        super(Transcript, self).__init__()
        self.client = client
        self.id = id

    def run(self):
        global DONE_JOB
        out_file = open('C:\Users\ErrolWilliamsII\Dropbox\HackTX (1)\Presentation{0}.txt'.format(int(DONE_JOB)), 'a')
        DONE_JOB += 1
        while self.client.view_job(self.id)['status'] == 'in_progress':
            print('waiting')
        transcript = client.get_transcript(self.id)

        for word in transcript['monologues'][0]['elements']:
            out_file.write('{0} '.format(word['value']))
        print('uploaded job {0}'.format(self.id))


if __name__ == '__main__':
    client = RevSpeechAPI(
    '01ao_KcVCQtnbg8FgkQFtKSJyiBLHXTWudFxGRlREPBoDiAuwAkX3CtaJIkvPp6tRFJX2MB99Z_chrq2bL5tKBzse6uYw')

    access_token = 'hfstaMFnZNAAAAAAAAAAneGtPMpM_gFTpDE1FtOuCxWX_cZcBVQPSK9vjWCnJ1fP'
    transfer_data = TransferData(access_token)

    p = pyaudio.PyAudio()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dir_path, WAVE_OUTPUT_FILENAME)

    frames = []

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    stream.start_stream()

    clear_file = open(TEXT_OUTPUT_FILENAME, 'w')
    clear_file.write('')


    out_file = open(TEXT_OUTPUT_FILENAME, 'a')

    while True:
        frames = []

        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        result = client.submit_job_local_file(filename)
        transcriber = Transcript(client, result['id'])
        transcriber.start()


    # time.sleep(.1)

    # Usage 1
    # c = RevClient('ws://54.201.48.144:8080/client/ws/speech')
    # c.connect()

        # c.send_file(WAVE_OUTPUT_FILENAME, RATE)
        # time.sleep(20)
        # audiostream = open(WAVE_OUTPUT_FILENAME, 'rb')
        # update_recording(audiostream, c)
    # c.finish_session()

    # Usage 2
    # c = RevClient("ws://localhost:8080/client/ws/speech")
    # c.connect()
    # c.send_file(audiofile, byterate)
    # time.sleep(20)
