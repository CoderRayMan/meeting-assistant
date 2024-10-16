import calendar
import socket
import time
import pyaudio
import queue
import threading
from gtts import gTTS
import google.cloud.speech as speech
from googletrans import Translator
import playsound
import os
import sys
from scripts.translatio.gcp.voice_map import language_codes

from better_profanity import profanity

class AudioReceiver:

    def __init__(self, host, port, slots=8, audio_format=pyaudio.paInt16, channels=1, rate=44100, frame_chunk=4096,key_path=None,update_op_cb=None):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath(key_path)
        # Set properties (optional)
        self.__host = host
        self.__port = port

        self.__slots = slots
        self.__used_slots = 0

        self.__audio_format = audio_format
        self.__channels = channels
        self.__rate = rate
        self.__frame_chunk = frame_chunk

        self.__audio = pyaudio.PyAudio()
        self.__update_cb=update_op_cb
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server_socket.bind((self.__host, self.__port))
        self.__block = threading.Lock()
        self.__running = False
        self._buff = queue.Queue()
        self._audio_generator = self.generator()
        self._speech_client = speech.SpeechClient()
        self._src='hi'
        self._des='en'
        self._language_code = language_codes[self._des]

        self._translate = False
        self._translator = Translator()

    def start_server(self):
        if self.__running:
            print("Audio server is running already")
        else:
            self.__running = True
            self.__stream = self.__audio.open(format=self.__audio_format, channels=self.__channels, rate=self.__rate,
                                              output=True, frames_per_buffer=self.__frame_chunk)
            thread = threading.Thread(target=self.__server_listening)
            thread.start()

    def __server_listening(self):
        self.__server_socket.listen()
        while self.__running:
            self.__block.acquire()
            connection, address = self.__server_socket.accept()
            if self.__used_slots >= self.__slots:
                print("Connection refused! No free slots!")
                connection.close()
                self.__block.release()
                continue
            else:
                self.__used_slots += 1

            self.__block.release()
            thread = threading.Thread(target=self.__client_connection, args=(connection, address,))
            thread.start()

    def generator(self):
        """Generates audio chunks from the stream of audio data in chunks."""
        while not self._closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)
    def transcribe_audio_stream(self):
        """Transcribes the audio stream in real-time."""
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.__rate,
            language_code=self._language_code
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in self._audio_generator
        )

        responses = self._speech_client.streaming_recognize(streaming_config, requests)

        self.listen_print_loop(responses)
    def update_src_dest(self,src,des):
        self._src=src
        self._des=des
    def start_translate(self):
        """Starts the transcription process."""
        self._closed = False
        self._translate = True
        thread = threading.Thread(target=self.transcribe_audio_stream)
        thread.start()

    def stop_translate(self):
        """Stops the transcription process."""
        self._closed = True

    def __client_connection(self, connection, address):
        while self.__running:
            data = connection.recv(self.__frame_chunk)
            if not self._translate:
                self.__stream.write(data)
            else:
                self._buff.put(data)

    def stop_server(self):
        if self.__running:
            self.__running = False
            closing_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            closing_connection.connect((self.__host, self.__port))
            closing_connection.close()
            self.__block.acquire()
            self.__server_socket.close()
            self.__block.release()
        else:
            print("Server not running!")

    def listen_print_loop(self, responses) -> str:
        """Iterates through server responses and prints them.

        The responses passed is a generator that will block until a response
        is provided by the server.

        Each response may contain multiple results, and each result may contain
        multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
        print only the transcription for the top alternative of the top result.

        In this case, responses are provided for interim results as well. If the
        response is an interim one, print a line feed at the end of it, to allow
        the next result to overwrite it, until the response is a final one. For the
        final one, print a newline to preserve the finalized transcription.

        Args:
            responses: List of server responses

        Returns:
            The transcribed text.
        """
        num_chars_printed = 0
        for response in responses:
            try:
                if not response.results:
                    continue

                # The `results` list is consecutive. For streaming, we only care about
                # the first result being considered, since once it's `is_final`, it
                # moves on to considering the next utterance.
                result = response.results[0]
                if not result.alternatives:
                    continue

                # Display the transcription of the top alternative.
                transcript = result.alternatives[0].transcript

                # Display interim results, but with a carriage return at the end of the
                # line, so subsequent lines will overwrite them.
                #
                # If the previous result was longer than this one, we need to print
                # some extra spaces to overwrite the previous result
                overwrite_chars = " " * (num_chars_printed - len(transcript))
                if not result.is_final:
                    sys.stdout.write(transcript + overwrite_chars + "\r")
                    sys.stdout.flush()
                    num_chars_printed = len(transcript)
                else:
                    translated = self._translator.translate((transcript + overwrite_chars),src=self._src,dest=self._des).text
                    censored = profanity.censor(translated.lower())
                    t3=threading.Thread(target=text_to_voice,args=[censored,self._des])
                    t2=threading.Thread(target=self.__update_cb,args=[censored])
                    t2.start()
                    t3.start()
                    num_chars_printed = 0
            except Exception as e:
                print("some issue while translating... "+str(e))
                num_chars_printed = 0
                pass
def text_to_voice(text_data,des):
    myobj = gTTS(text=text_data, lang=des, slow=False)
    gmt = time.gmtime()
    ts = str(calendar.timegm(gmt))
    myobj.save("cache_file"+ts+".mp3")
    playsound.playsound("cache_file"+ts+".mp3")
    os.remove("cache_file"+ts+".mp3")
