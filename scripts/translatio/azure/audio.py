import socket
import pyaudio
import threading
from better_profanity import profanity
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech.audio import AudioStreamFormat
from scripts.translatio.azure.voice_map import voice_map_dict, auto_translate_dict


class AudioSender:

    def __init__(self, host, port, audio_format=pyaudio.paInt16, channels=1, rate=44100, frame_chunk=4096):
        self.__host = host
        self.__port = port

        self.__audio_format = audio_format
        self.__channels = channels
        self.__rate = rate
        self.__frame_chunk = frame_chunk
        self.__language = "English"
        self.__sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sending_socket_mtdata = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__audio = pyaudio.PyAudio()

        self.__running = False

    def update_lang(self, language):
        self.__language = language
        print(self.__language)

    def start_stream(self):
        if self.__running:
            print("Already streaming")
        else:
            self.__running = True
            thread = threading.Thread(target=self.__client_streaming)
            thread.start()

    def stop_stream(self):
        if self.__running:
            self.__running = False
        else:
            print("Client not streaming")

    def __client_streaming(self):
        self.__sending_socket.connect((self.__host, self.__port))
        self.__sending_socket_mtdata.connect((self.__host, 8081))
        self.__stream = self.__audio.open(format=self.__audio_format, channels=self.__channels, rate=self.__rate,
                                          input=True, frames_per_buffer=self.__frame_chunk)
        while self.__running:
            self.__sending_socket_mtdata.send(self.__language.encode())
            self.__sending_socket.send(self.__stream.read(self.__frame_chunk))


class AudioReceiver:

    def __init__(self, host, port, slots=8, audio_format=pyaudio.paInt16, channels=1, rate=44100, frame_chunk=4096,
                 speech_key=None, service_region=None, update_op_cb=None):
        self._audio_config1 = None
        self.__speech_config1 = None
        self.__transcribe_cb = None
        self.__conversational_transcriber = None
        self.__host = host
        self.__port = port

        self.__slots = slots
        self.__used_slots = 0

        self.__audio_format = audio_format
        self.__channels = channels
        self.__rate = rate
        self.__frame_chunk = frame_chunk
        self.__speech_key = speech_key
        self.__service_region = service_region
        self.__sendpoint_string = "wss://{}.stt.speech.microsoft.com/speech/universal/v2".format(self.__service_region)
        self.__audio = pyaudio.PyAudio()
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__metadata_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server_socket.bind((self.__host, self.__port))
        self.__metadata_socket.bind((self.__host, 8081))
        self.__block = threading.Lock()
        self.__running = False
        self._translate = False
        self.__transcribe_op = update_op_cb
        self.__push_stream = speechsdk.audio.PushAudioInputStream(stream_format=AudioStreamFormat(rate, 16, 1))
        self.__push_stream2 = speechsdk.audio.PushAudioInputStream(stream_format=AudioStreamFormat(rate, 16, 1))

        self._speech_translation_config = speechsdk.translation.SpeechTranslationConfig(subscription=self.__speech_key,
                                                                                        endpoint=self.__sendpoint_string,
                                                                                        speech_recognition_language='en-US')
        self._target_language = "hi"
        self._speech_translation_config.add_target_language(self._target_language)
        self._audio_config = speechsdk.audio.AudioConfig(stream=self.__push_stream)
        self._translation_recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=self._speech_translation_config, audio_config=self._audio_config)
        self._translation_recognizer.recognized.connect(self.recognized_cb)
        self.__speech_config = speechsdk.SpeechConfig(subscription=self.__speech_key, region=self.__service_region)
        self.__speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.__speech_config)
        self.__auto_translate = False

    def start_server(self):
        if self.__running:
            print("Audio server is running already")
        else:
            self.__running = True
            self.__stream = self.__audio.open(format=self.__audio_format, channels=self.__channels, rate=self.__rate,
                                              output=True, frames_per_buffer=self.__frame_chunk)
            thread = threading.Thread(target=self.__server_listening)
            thread_m = threading.Thread(target=self.__server_listening_mtdata)
            thread.start()
            thread_m.start()

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
            thread = threading.Thread(target=self.__client_connection, args=(connection, address))
            thread.start()

    def __server_listening_mtdata(self):
        self.__metadata_socket.listen()
        while self.__running:
            self.__block.acquire()
            connection1, address1 = self.__metadata_socket.accept()
            if self.__used_slots >= self.__slots:
                print("Connection refused! No free slots!")
                connection1.close()
                self.__block.release()
                continue
            else:
                self.__used_slots += 1

            self.__block.release()
            thread = threading.Thread(target=self.__client_connection_mtdata, args=(connection1, address1))
            thread.start()

    def recognized_cb(self, evt: speechsdk.translation.TranslationRecognitionEventArgs):
        translation_recognition_result = evt.result
        if translation_recognition_result.reason == speechsdk.ResultReason.TranslatedSpeech:
            if self.__auto_translate:
                self.__transcribe_op('\tlanguage={}'.format(
                    evt.result.properties[speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult]))
            # self.__transcribe_op('RECOGNIZED: {}'.format(translation_recognition_result.text))
            # self.__transcribe_op("""Translated into '{}': {}""".format(
            #     self._target_language,
            #     translation_recognition_result.translations[self._target_language]))
            self.__transcribe_op("""{}""".format(
                # self._target_language,
                translation_recognition_result.translations[self._target_language]))
            # Use SSML to adjust the volume and pitch of the synthesized speech
            ssml_string = f"""
                    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{voice_map_dict[self._target_language][0]}'>
                        <voice name='{voice_map_dict[self._target_language][2]}'>
                            <prosody volume='loud' pitch='+0%'>
                                {translation_recognition_result.translations[self._target_language]}
                            </prosody>
                        </voice>
                    </speak>
                    """
            self.__speech_synthesizer.speak_ssml_async(ssml_string).get()

    def update_src_dest(self, des, auto):
        self.__auto_translate = auto
        self.update_lang(self._speech_translation_config.speech_recognition_language, des)

    def update_lang(self, src, des):
        if (self._translate):
            self._translation_recognizer.stop_continuous_recognition_async()
        self._audio_config = speechsdk.audio.AudioConfig(stream=self.__push_stream)
        if self.__auto_translate:
            self._speech_translation_config = speechsdk.translation.SpeechTranslationConfig(
                subscription=self.__speech_key,
                endpoint=self.__sendpoint_string,
                speech_recognition_language='en-US')
            self._speech_translation_config.remove_target_language(self._target_language)
            self._target_language = des
            self._speech_translation_config.add_target_language(self._target_language)
            print(list(auto_translate_dict.keys()))
            self._speech_translation_config.set_property(
                property_id=speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode, value='Continuous')
            auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                languages=list(auto_translate_dict.keys()))
            self._translation_recognizer = speechsdk.translation.TranslationRecognizer(
                translation_config=self._speech_translation_config, audio_config=self._audio_config,
                auto_detect_source_language_config=auto_detect_source_language_config)
        else:
            self._speech_translation_config = speechsdk.translation.SpeechTranslationConfig(
                subscription=self.__speech_key,
                region=self.__service_region,
                )
            self._speech_translation_config.remove_target_language(self._target_language)
            self._target_language = des
            self._speech_translation_config.add_target_language(self._target_language)
            self._speech_translation_config.speech_recognition_language = src
            self._translation_recognizer = speechsdk.translation.TranslationRecognizer(
                translation_config=self._speech_translation_config, audio_config=self._audio_config)

        self._translation_recognizer.recognized.connect(self.recognized_cb)
        if (self._translate):
            result_future = self._translation_recognizer.start_continuous_recognition_async()
            result_future.get()
        print("called")

    def conversation_transcriber_transcribed_cb(self, evt: speechsdk.SpeechRecognitionEventArgs):
        print('TRANSCRIBED:')
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            # print('\tText={}'.format(evt.result.text))
            print('\tSpeaker ID={}'.format(evt.result.speaker_id))
            # print('\tlanguage={}'.format(evt.result.properties[speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult]))
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            print('\tNOMATCH: Speech could not be TRANSCRIBED: {}'.format(evt.result.no_match_details))

    def initialize_multi(self):
        self.__speech_config1 = speechsdk.SpeechConfig(subscription=self.__speech_key, region=self.__service_region)
        self.__speech_config1.speech_recognition_language = self._speech_translation_config.speech_recognition_language
        self._audio_config1 = speechsdk.audio.AudioConfig(stream=self.__push_stream2)
        self.__conversational_transcriber = speechsdk.transcription.ConversationTranscriber(
            speech_config=self.__speech_config1, audio_config=self._audio_config1)
        self.__conversational_transcriber.transcribed.connect(self.conversation_transcriber_transcribed_cb)
        # self.__transcribe_cb=cb
        result = self.__conversational_transcriber.start_transcribing_async()
        result.get()

    def stop_transcriber(self):
        self.__conversational_transcriber.stop_transcribing_async()

    def start_translate(self):
        """Starts the transcription process."""
        self._closed = False
        self._translate = True
        result_future = self._translation_recognizer.start_continuous_recognition_async()
        result_future.get()

    def stop_translation(self):
        """Stops the transcription process."""
        self._closed = True
        self._translate = False
        self._translation_recognizer.stop_continuous_recognition_async()

    def __client_connection(self, connection, address):
        while self.__running:
            data = connection.recv(self.__frame_chunk)
            if not self._translate:
                self.__stream.write(data)
            else:
                self.__push_stream.write(data)
                self.__push_stream2.write(data)

    def __client_connection_mtdata(self, connection, address):
        while self.__running:
            # data = connection.recv(self.__frame_chunk)
            language = str(connection.recv(1024).decode())
            if not (self._speech_translation_config is None or
                    language.startswith(self._speech_translation_config.speech_recognition_language)):
                print('lang- {} ; new_lang - {}, target_lang {} ; '.format(language,
                                                                           self._speech_translation_config.speech_recognition_language,
                                                                           self._target_language))
                self.update_lang(language, self._target_language)
                print('lang- {} ; new_lang - {}, target_lang {} ; '.format(language,
                                                                           self._speech_translation_config.speech_recognition_language,
                                                                           self._target_language))

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
