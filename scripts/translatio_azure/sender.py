from vidstream import CameraClient, ScreenShareClient
from scripts.translatio.azure.audio import AudioSender
import tkinter as tk
import socket
import threading
from scripts.translatio.azure import lang_dict

local_ip_address = "192.168.0.105"
try:
    local_ip_address = socket.gethostbyname(socket.gethostname())
except Exception as e:
    local_ip_address = "192.168.0.109"
    pass
audio_client = AudioSender(local_ip_address, 6666)

def start_camera_stream():
    camera_client = CameraClient(local_ip_address, 7777)
    t3 = threading.Thread(target=camera_client.start_stream)
    t3.start()


def start_screen_sharing():
    screen_client = ScreenShareClient(local_ip_address, 7777)
    t4 = threading.Thread(target=screen_client.start_stream)
    t4.start()


def start_audio_sharing():
    t5 = threading.Thread(target=audio_client.start_stream)
    t5.start()
    audio_client.update_lang(lang_dict[selected_language.get().title()]["src"])



# Define the function to be called when an option is selected
def update_language(*args):
    print(f"Language selected: {selected_language.get().title()}")
    audio_client.update_lang(lang_dict[selected_language.get().title()]["src"])
    # Add your code here


# GUI
window = tk.Tk()
window.title("Dummy Machine to Mimic a separate distant sender")
window.geometry('600x200')

# Create a StringVar instance to hold the selected option
selected_language = tk.StringVar(window)

# Set the default value
selected_language.set("English")
# Define the options
options = lang_dict.keys()

# Create the dropdown menu
dropdown = tk.OptionMenu(window, selected_language, *options, command=update_language)

# Display the dropdown menu
dropdown.pack()

btn_camera = tk.Button(window, text="Start Camera Stream", width=50, command=start_camera_stream)
btn_camera.pack(anchor=tk.CENTER, expand=True)
btn_screen = tk.Button(window, text="Start Screen Share", width=50, command=start_screen_sharing)
btn_screen.pack(anchor=tk.CENTER, expand=True)
btn_audio = tk.Button(window, text="Start Audio Stream", width=50, command=start_audio_sharing)
btn_audio.pack(anchor=tk.CENTER, expand=True)

window.mainloop()
