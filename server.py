import socket
import threading
import random

# Constants
SERVER_IP = '127.0.0.1'
SERVER_PORT = 9999
MAX_PLAYERS = 2
DATABASE_FILE = "database.txt"

# Global variables
players = []
player_points = {}
player_order = {}
keyword = ""
hint = ""
correct_keyword = False
turn_count = 0
clients = []

def generate_random_keyword():
    global keyword, hint
    with open(DATABASE_FILE, 'r') as file:
        lines = file.readlines()
        n = int(lines[0])
        keyword_index = random.randint(1, n)
        keyword = lines[keyword_index*2-1].strip().lower()
        hint = lines[keyword_index*2].strip()

def client_handler(client_socket, player_address):
    global players, player_order, player_points, keyword, hint, correct_keyword, turn_count
    
    nickname = client_socket.recv(1024).decode()
    if nickname in players:
        client_socket.send("Nickname already taken. Please choose another one.".encode())
        client_socket.close()
        return
    players.append(nickname)
    player_points[nickname] = 0
    player_order[nickname] = len(players)
    print(f"Player {nickname} has joined the game.")
    client_socket.send(f"Registration Completed Successfully. Your order is: {player_order[nickname]}".encode())

    while len(players) < MAX_PLAYERS:
        pass  # Waiting for all players to join
    
    # Generate random keyword for all players
    generate_random_keyword()
    for client in clients:
        client.send(f"The length of the keyword is {len(keyword)}: {'*' * len(keyword)}\nHints: {hint}".encode())

    # Gameplay loop
    while not correct_keyword and turn_count < 5:
        guess = client_socket.recv(1024).decode()
        if len(guess) == 1:	
            if guess.lower() in keyword:
                count = keyword.count(guess.lower())
                new_keyword = ''.join([char if char == guess.lower() else '*' for char in keyword])
                client_socket.send(f"Character '{guess}' has {count} occurrence.\nThe current keyword is \"{new_keyword}\"".encode())
                if '*' not in new_keyword:
                    correct_keyword = True
                    player_points[nickname] += 5
                    for client in clients:
                        client.send(f"Congratulations to the winner with the correct keyword: \"{keyword}\"".encode())
                else:
                    player_points[nickname] += 1
            else:
                client_socket.send(f"Character '{guess}' is not in the keyword.".encode())
                turn_count += 1
            pass
        else:
            # Check if it's the second turn or onwards to allow guessing the whole word
            if turn_count >= 1:
                # Check if the guessed word is correct
                if guess.lower() == keyword:
                    correct_keyword = True
                    player_points[nickname] += 5
                    for client in clients:
                        client.send(f"Congratulations to the winner '{nickname}' with the correct keyword: \"{keyword}\"".encode())
                    break;    #end the game upon correct keyword is guessed correctly
                else:
                    client_socket.send("Incorrect guess. Try again.".encode())
                    turn_count += 1
            else:
                client_socket.send("You can only guess the whole word from the second turn onwards.".encode())

    if not correct_keyword:
    # Inform players that the game is over
        for client in clients:
            client.send("Game over!".encode())
            client.close()

def start_game(client_socket):
    global correct_keyword
    try:
        response = client_socket.recv(1024).decode()
        if response == "start_game":
            client_socket.send("game_started".encode())
            print("Game started!")
            return True
        else:
            print("Error: Failed to start the game.")
            return False
    except Exception as e:
        print("Error:", e)
        return False

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(MAX_PLAYERS)

    print("Server is running...")

    while (len(clients) < MAX_PLAYERS):
        client_socket, client_address = server_socket.accept()
        clients.append(client_socket)
        print(f"Connection from {client_address}")
        threading.Thread(target=client_handler, args=(client_socket, client_address)).start()

    for client in clients:
        if not start_game(client):
            client.close()

if __name__ == "__main__":
    main()
