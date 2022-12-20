import socket
import sys
import threading

from Message import Unchoke, Choke, KeepAlive


def receiver():
    global client
    while True:
        print("Waiting for message")
        data = client.recv(1024)
        print(data)

        if data == b'':
            print("Client disconnected!")
            input("Type to continue...")

        try:
            msg2 = data[1:20].decode()
            if "protocol" in msg2:
                print("\nReceived handshake, sending back")
                client.send(data)

        except Exception as e:
            print("fuck", e)
            pass


PORT = int(sys.argv[-1])
sock = socket.socket()
sock.bind(('127.0.0.1', PORT))

print(f"Listening on 127.0.0.1:{PORT}")

while True:
    sock.listen()
    sock.accept()
    client, addr = sock.accept()
    print("Accepted:", addr)

    receiver_thread = threading.Thread(target=receiver)
    receiver_thread.start()

    while True:
        choice = int(input("Enter your choice: "))
        if choice == 0:
            print("Stopping with client", addr)
            break
        elif choice == 1:
            msg = Unchoke()
        elif choice == 2:
            msg = Choke()
        elif choice == 3:
            msg = KeepAlive()
        else:
            print("wtf?")
            continue

        print('Sending:', msg.to_bytes())
        client.send(msg.to_bytes())
