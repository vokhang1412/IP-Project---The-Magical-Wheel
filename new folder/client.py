import socket
import threading

connected = True
game_ended = False
game_end_event = threading.Event()

def receive_messages(client_socket):
    global connected, game_ended, game_end_event
    while connected and not game_ended:
        try:
            message = client_socket.recv(1024).decode()
            if not message:
                break
            print(message)
            if message == "Game is ending. Thank you for playing!":
                game_ended = True
                print("Game ended. Press enter to exit...")
                game_end_event.set()
                break
        except Exception as e:
            print("Error:", e)
            break
    connected = False

def input_thread_func(client_socket):
    global connected
    while connected:
        if game_end_event.is_set():
            break
        message = input()
        client_socket.send(message.encode())

def main():
    global connected, game_ended
    host = "localhost"
    port = 5555

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Register to the server
    print(client_socket.recv(1024).decode())
    nickname = input()
    client_socket.send(nickname.encode())

    # Receive initial messages from the server
    print(client_socket.recv(1024).decode())

    # Start receiving messages in a separate thread
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()

    # Start input thread
    input_thread = threading.Thread(target=input_thread_func, args=(client_socket,))
    input_thread.start()

    # Wait for threads to finish
    receive_thread.join()
    input_thread.join()
    client_socket.close()

if __name__ == "__main__":
    main()
