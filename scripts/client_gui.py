from tkinter import messagebox
import tkinter as tk
import socket
import threading
from ai_assistant import Ai_Helper

ai_helper = Ai_Helper()
window = tk.Tk()
window.title("Client")
username = " "

topFrame = tk.Frame(window)
lblName = tk.Label(topFrame, text="Name:").pack(side=tk.LEFT)
entName = tk.Entry(topFrame)
entName.pack(side=tk.LEFT)
btnConnect = tk.Button(topFrame, text="Connect", command=lambda: connect())
btnConnect.pack(side=tk.LEFT)
#btnConnect.bind('<Button-1>', connect)
topFrame.pack(side=tk.TOP)

# Left chat section
leftFrame = tk.Frame(window)
lblLine_l = tk.Label(leftFrame,
                     text="********************************  DUMMY TRANSCRIPTS  *************************************").pack()
leftScrollbar = tk.Scrollbar(leftFrame)
leftScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
leftTkDisplay = tk.Text(leftFrame, height=20, width=30)
leftTkDisplay.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(5, 0))
leftTkDisplay.tag_config("tag_your_message", foreground="blue")
leftScrollbar.config(command=leftTkDisplay.yview)
leftTkDisplay.config(yscrollcommand=leftScrollbar.set, background="#F4F6F7", highlightbackground="grey",
                     foreground="black",
                     state="disabled")

# Left chat input textbox
bottomLeftFrame = tk.Frame(leftFrame)
tkMessageLeft = tk.Text(bottomLeftFrame, height=2, width=30)
tkMessageLeft.pack(fill=tk.BOTH, expand=True, padx=(5, 13), pady=(5, 10))
tkMessageLeft.config(highlightbackground="grey")
tkMessageLeft.bind("<Return>", (lambda event: getChatMessageLeft(tkMessageLeft.get("1.0", tk.END))))
bottomLeftFrame.pack(side=tk.BOTTOM, fill=tk.BOTH)

leftFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Right chat section
rightFrame = tk.Frame(window)
lblLine_r = tk.Label(rightFrame,
                     text="********************************  CHAT INTERFACE  *************************************").pack()
rightScrollbar = tk.Scrollbar(rightFrame)
rightScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
rightTkDisplay = tk.Text(rightFrame, height=20, width=30)
rightTkDisplay.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(5, 0))
rightTkDisplay.tag_config("tag_your_message", foreground="blue")
rightScrollbar.config(command=rightTkDisplay.yview)
rightTkDisplay.config(yscrollcommand=leftScrollbar.set, background="#F4F6F7", highlightbackground="grey",
                      foreground="black",
                      state="disabled")

# Right chat input textbox
bottomRightFrame = tk.Frame(rightFrame)
tkMessageRight = tk.Text(bottomRightFrame, height=2, width=30)
tkMessageRight.pack(fill=tk.BOTH, padx=(5, 13), pady=(5, 10))
tkMessageRight.config(highlightbackground="grey")
tkMessageRight.bind("<Return>", (lambda event: getChatMessageRight(tkMessageRight.get("1.0", tk.END))))
bottomRightFrame.pack(side=tk.BOTTOM, fill=tk.BOTH)

rightFrame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

msg_queue = []


def connect():
    global username, client
    if len(entName.get()) < 1:
        tk.messagebox.showerror(title="ERROR!!!", message="You MUST enter your first name <e.g. John>")
    else:
        username = entName.get()
        connect_to_server(username)


# network client
client = None
HOST_ADDR = "127.0.0.1"
HOST_PORT = 8081


def connect_to_server(name):
    global client, HOST_PORT, HOST_ADDR
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST_ADDR, HOST_PORT))
        client.send(name.encode())  # Send name to server after connecting

        entName.config(state=tk.DISABLED)
        btnConnect.config(state=tk.DISABLED)
        tkMessageLeft.config(state=tk.NORMAL)

        # start a thread to keep receiving message from server
        # do not block the main thread :)
        threading._start_new_thread(receive_message_from_server, (client, "m"))
    except Exception as e:
        tk.messagebox.showerror(title="ERROR!!!", message="Cannot connect to host: " + HOST_ADDR + " on port: " + str(
            HOST_PORT) + " Server may be Unavailable. Try again later")


def receive_message_from_server(sck, m):
    while True:
        from_server = sck.recv(4096).decode()

        if not from_server: break

        # display message from server on the chat window

        # enable the display area and insert the text and then disable.
        # why? Apparently, tkinter does not allow us insert into a disabled Text widget :(
        texts = leftTkDisplay.get("1.0", tk.END).strip()
        leftTkDisplay.config(state=tk.NORMAL)
        if len(texts) < 1:
            leftTkDisplay.insert(tk.END, from_server)
        else:
            leftTkDisplay.insert(tk.END, "\n\n" + from_server)
            if ':' in from_server:
                speaker, transcription = map(str.strip, from_server.split(':'))
                msg_queue.append({'speaker': speaker, 'spoken_text': transcription})
            ai_helper.update_convo(msg_queue)

        leftTkDisplay.config(state=tk.DISABLED)
        leftTkDisplay.see(tk.END)

        # print("Server says: " +from_server)

    sck.close()
    window.destroy()


def getChatMessageLeft(msg):
    msg = msg.replace('\n', '')
    texts = leftTkDisplay.get("1.0", tk.END).strip()

    # enable the display area and insert the text and then disable.
    # why? Apparently, tkinter does not allow use insert into a disabled Text widget :(
    leftTkDisplay.config(state=tk.NORMAL)
    if len(texts) < 1:
        leftTkDisplay.insert(tk.END, "You : " + msg, "tag_your_message")  # no line
    else:
        leftTkDisplay.insert(tk.END, "\n\n" + "You : " + msg, "tag_your_message")

    leftTkDisplay.config(state=tk.DISABLED)

    send_mssage_to_server(msg)
    msg_queue.append({'speaker': 'You', 'spoken_text': msg})
    ai_helper.update_convo(msg_queue)
    leftTkDisplay.see(tk.END)
    tkMessageLeft.delete('1.0', tk.END)


def getChatMessageRight(msg):
    msg = msg.replace('\n', '')
    texts = rightTkDisplay.get("1.0", tk.END).strip()
    respo = ai_helper.ask_q(msg)
    # enable the display area and insert the text and then disable.
    # why? Apparently, tkinter does not allow use insert into a disabled Text widget :(
    rightTkDisplay.config(state=tk.NORMAL)
    if len(texts) < 1:
        rightTkDisplay.insert(tk.END, "You : " + msg, "tag_your_message")  # no line
        rightTkDisplay.insert(tk.END, "\n\n" + "helper : " + respo, "tag_your_message")  # no line
    else:
        rightTkDisplay.insert(tk.END, "\n\n" + "You : " + msg, "tag_your_message")
        rightTkDisplay.insert(tk.END, "\n\n" + "helper : " + respo, "tag_your_message")

    rightTkDisplay.config(state=tk.DISABLED)

    rightTkDisplay.see(tk.END)
    rightTkDisplay.delete('1.0', tk.END)


def send_mssage_to_server(msg):
    client_msg = str(msg)
    client.send(client_msg.encode())
    if msg == "exit":
        client.close()
        window.destroy()


window.mainloop()
