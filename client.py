import socket
import time

SERVER_IP = '127.0.0.1'
SERVER_PORT = 9999

def connect_to_server():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, SERVER_PORT))
        return client_socket
    except Exception as e:
        print("Error connecting to the server:", e)
        return None

def main():
    connected = False
    while not connected:
        client_socket = connect_to_server()
        if client_socket:
            print("Connected to the server.")
            connected = True
        else:
            print("Retrying to connect in 5 seconds...")
            time.sleep(5)

    data = input("Enter your username: ")
    client_socket.send(data.encode())
    data = client_socket.recv(1024).decode()
    print(data)
    start_game(client_socket)
    client_socket.close()

def start_game(client_socket):
    try:
        client_socket.send("start_game".encode())
        response = client_socket.recv(1024).decode()
        if response == "game_started":
            print("Game started!")
            while True:
                game_info = client_socket.recv(1024).decode()
                if "Game over" in game_info:
                    print(game_info)
                    break
                print(game_info)
                guess = input("Enter your guess: ")
                client_socket.send(guess.encode())
            # No need to wait for server response here, just keep sending guesses
        else:
            print("Error: Failed to start the game.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
