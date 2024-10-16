from vidstream import CameraClient, ScreenShareClient
# for Azure comment and for gcp un-comment from next line
from scripts.translatio.azure import AudioReceiver,AudioSender
from scripts.translatio.azure import StreamingServer
from scripts.translatio.azure import lang_dict
# for Azure comment and for gcp un-comment till here
# for Azure un-comment and for gcp comment from next line
# from scripts.translatio.gcp import AudioReceiver
# from scripts.translatio.gcp import StreamingServer
# from scripts.translatio.gcp import lang_dict
# for Azure un-comment and for gcp comment till here
import tkinter as tk
import socket
import threading
import json
from PIL import Image, ImageTk
import cv2
from tkinter import ttk
from ttkbootstrap import Style

is_muted = False
t1, t2, t3, t4, t5, t6 = None, None, None, None, None, None

# Middle frame
video_stream_width, video_stream_height = 1000, 490

'''
if you are using Mac Machine , then comment lines 'MAC COMMENT START'-'MAC COMMENT END'.
run the following command : ipconfig getifaddr en0
copy the ip address and assign the value to the ip-address
'''
local_ip_address = "<YOUR IP HERE>"

##   MAC COMMENT START
try:
    local_ip_address = socket.gethostbyname(socket.gethostname())
except Exception as e:
    local_ip_address = "<YOUR IP HERE>"
    pass
## MAC COMMENT END

print(local_ip_address)
with open('config.json') as f:
    config = json.load(f)


def update_output(text):
    output_box.insert(tk.END, text + "\n")
    output_box.see(tk.END)


def update_video_stream(frame):
    if frame is not None:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        video_stream_image = ImageTk.PhotoImage(image=img)
        video_stream_label.configure(image=video_stream_image)
        video_stream_label.image = video_stream_image
    else:
        # Show a black screen when there is no video stream
        black_screen = Image.new("RGB", (video_stream_width, video_stream_height), "black")
        black_screen_img = ImageTk.PhotoImage(image=black_screen)
        video_stream_label.configure(image=black_screen_img)
        video_stream_label.image = black_screen_img


server = StreamingServer(local_ip_address, 7777, updater_cb=update_video_stream)
# for Azure un comment this and for gcp comment this
reciever = AudioReceiver(local_ip_address, 6666, speech_key=config['azure_speech_key'],
                         service_region=config['azure_loc'], update_op_cb=update_output)


# For GCP uncomment this and for azure comment this
# reciever = AudioReceiver(local_ip_address, 6666, key_path=config['gcp_key_loc'], update_op_cb=update_output)


def start_listening():
    t1 = threading.Thread(target=server.start_server)
    t2 = threading.Thread(target=reciever.start_server)
    t1.start()
    t2.start()


def mute_unmute():
    global is_muted
    is_muted = not is_muted

    if is_muted:
        # reciever.mute()
        pass
    else:
        # reciever.unmute()
        pass

isTranslatioRunning = False
def start_translate():
    global isTranslatioRunning
    if isTranslatioRunning:
        isTranslatioRunning = False
        btn_audio_translate.configure(text="Translate", command=start_translate, style='primary.TButton')
        reciever.stop_transcriber()
        reciever.stop_translation()
        return
    style.configure('W.TButton',foreground='white',background='red')
    btn_audio_translate.configure(text="Stop Translate", command=start_translate,style='W.TButton')
    isTranslatioRunning = True
    t6 = threading.Thread(target=reciever.start_translate)
    t6.start()

def start_camera_stream():
    client_target = text_target_ip.get()
    port = 7777
    if client_target == "":
        client_target = local_ip_address
        port = 9999
    camera_client = CameraClient(client_target, port)
    t3 = threading.Thread(target=camera_client.start_stream)
    t3.start()


def start_screen_sharing():
    client_target = text_target_ip.get()
    port = 7777
    if client_target == "":
        client_target = local_ip_address
        port = 9999
    screen_client = ScreenShareClient(client_target, port)
    t4 = threading.Thread(target=screen_client.start_stream)
    t4.start()


audio_client: AudioSender


def start_audio_sharing():
    client_target = text_target_ip.get()
    port = 6666
    if client_target == "":
        client_target = local_ip_address
        port = 8888
    global audio_client
    audio_client = AudioSender(client_target, port)
    t5 = threading.Thread(target=audio_client.start_stream)
    t5.start()
    update_src_des()



def auto_translate_changed():
    update_src_des()


def update_src_des(*args):
    reciever.update_src_dest(lang_dict[selected_listener_language.get().title()]["dest"], auto_translate_var.get())
    try:
        global audio_client
        audio_client.update_lang(lang_dict[selected_listener_language.get().title()]["src"])
    except Exception as e:
        pass


# GUI
style = Style('lumen')
window = style.master
window.title("Translatio")
window.geometry('1800x800')

# Dropdown menu options
options = list(lang_dict.keys())

# Variable to store the selected options
selected_speaker_language = tk.StringVar()
selected_speaker_language.set(options[0])

selected_listener_language = tk.StringVar()
selected_listener_language.set(options[1])
auto_translate_var = tk.BooleanVar()
auto_translate_var.set(False)  # Set the default state to off

# Create frames
top_frame = ttk.Frame(window)
top_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')

middle_frame = ttk.Frame(window)
middle_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=10)

left_frame = ttk.Frame(middle_frame)
left_frame.grid(row=0, column=0, sticky='nsew')

right_frame = ttk.Frame(middle_frame)
right_frame.grid(row=0, column=1, sticky='nsew')

# Bottom frame
bottom_frame = ttk.Frame(window)
bottom_frame.grid(row=2, column=0, columnspan=2, pady=10)

# Configure grid
window.grid_rowconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=8)
window.grid_rowconfigure(2, weight=1)
window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)

# Update grid row configuration for middle_frame
middle_frame.grid_rowconfigure(0, weight=1)

# Update grid row configuration for bottom_frame
bottom_frame.grid_rowconfigure(0, weight=1)
middle_frame.grid_columnconfigure(0, weight=7)  # Video stream
middle_frame.grid_columnconfigure(1, weight=3)

# Top frame
label_target_ip_add = ttk.Label(top_frame, text="Target IP")
label_target_ip_add.grid(row=0, column=0)

text_target_ip = ttk.Entry(top_frame, style='TEntry')
text_target_ip.grid(row=0, column=1)

btn_listen = ttk.Button(top_frame, text="Connect", command=start_listening, style='primary.TButton')
btn_listen.grid(row=0, column=2)

# Create the Label widget in the top frame
speaker_label = ttk.Label(top_frame, text="Current Speaker")
speaker_label.grid(row=0, column=3)

# # Create the Text widget in the top frame
# speaker_output_box = tk.Text(top_frame)
# speaker_output_box.grid(row=0, column=4)
# Add this to your imports
from tkinter import END

# Define the update_speaker method
# def update_speaker(text):
#     speaker_output_box.insert(END, text + "\n")
#     speaker_output_box.see(END)
video_stream_frame = ttk.Frame(left_frame, width=video_stream_width, height=video_stream_height)
video_stream_frame.pack()

video_stream_label = ttk.Label(video_stream_frame)
# Show a black screen when there is no video stream
black_screen = Image.new("RGB", (video_stream_width, video_stream_height), "black")
black_screen_img = ImageTk.PhotoImage(image=black_screen)
video_stream_label.configure(image=black_screen_img)
video_stream_label.image = black_screen_img
video_stream_label.pack(fill=tk.BOTH, expand=True)

# Output box in right_frame
translationbox_frame = ttk.Frame(right_frame, width=video_stream_width, height=video_stream_height)
translationbox_frame.pack()

output_box = tk.Text(translationbox_frame)
output_box.pack(fill=tk.BOTH, expand=True)

# Bottom frame contents
btn_mute_unmute = ttk.Button(bottom_frame, text="Mute/Unmute", command=mute_unmute, style='primary.TButton')
btn_mute_unmute.grid(row=0, column=3, padx=5)

label_listener_language = ttk.Label(bottom_frame, text="Language")
label_listener_language.grid(row=0, column=0, padx=5)

dropdown_listener_language = ttk.Combobox(bottom_frame, textvariable=selected_listener_language, values=options,
                                          style='TCombobox')
dropdown_listener_language.bind("<<ComboboxSelected>>", update_src_des)
dropdown_listener_language.grid(row=0, column=1, padx=5)

# btn_listen = ttk.Button(bottom_frame, text="Start Listening", command=start_listening, style='primary.TButton')
# btn_listen.grid(row=0, column=5, padx=5)

btn_camera = ttk.Button(bottom_frame, text="Camera", command=start_camera_stream, style='primary.TButton')
btn_camera.grid(row=0, column=6, padx=5)

btn_screen = ttk.Button(bottom_frame, text="Screen Share", command=start_screen_sharing, style='primary.TButton')
btn_screen.grid(row=0, column=7, padx=5)

btn_audio = ttk.Button(bottom_frame, text="Audio Stream", command=start_audio_sharing, style='primary.TButton')
btn_audio.grid(row=0, column=8, padx=5)

btn_audio_translate = ttk.Button(bottom_frame, text="Translate", command=start_translate, style='primary.TButton')
btn_audio_translate.grid(row=0, column=9, padx=5)

auto_translate_checkbox = ttk.Checkbutton(bottom_frame, text="Auto-Detect-Source", variable=auto_translate_var,
                                          command=auto_translate_changed)
auto_translate_checkbox.grid(row=0, column=10, padx=5)

# Start the Tkinter event loop
window.mainloop()
