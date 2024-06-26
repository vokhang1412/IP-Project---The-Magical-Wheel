import socket
import threading
import random
import select

class Player:
    def __init__(self, conn, addr, nickname):
        self.conn = conn
        self.addr = addr
        self.nickname = nickname
        self.points = 0
        self.guess_count = 0
        self.active = True

    def reset(self):
        self.points = 0
        self.guess_count = 0
        self.active = True

def read_database(filename):
    keywords = []
    descriptions = []
    with open(filename, 'r') as file:
        n = int(file.readline())
        for _ in range(n):
            keyword = file.readline().strip()
            description = file.readline().strip()
            keywords.append(keyword)
            descriptions.append(description)
    return keywords, descriptions

def handle_client(player):
    global players, keywords, game_running, descriptions, num_players
    welcome_message = "Welcome to The Magical Wheel, {}!\nEnter your nickname: ".format(player.nickname)
    player.conn.send(welcome_message.encode())

    nickname_taken = True
    while nickname_taken:
        nickname = player.conn.recv(1024).decode().strip()
        if not any(p.nickname.lower() == nickname.lower() for p in players) and len(nickname) <= 10:
            player.nickname = nickname
            nickname_taken = False
            player.conn.send("Registration Completed Successfully".encode())
        else:
            player.conn.send("Nickname already taken or invalid length. Choose another one: ".encode())

    # Player registration completed
    print("Player {} registered".format(player.nickname))
    players.append(player)

    # Wait until all players have joined
    if len(players) == num_players:
        # Load game data
        keywords, descriptions = read_database("database.txt")

        # Start the game
        game_running = True
        print("Starting game...")
        start_game()
    else:
        waiting_message = "Waiting for other players..."
        player.conn.send(waiting_message.encode())

def start_game():
    global players, keywords, game_running, descriptions
    keyword_idx = random.randint(0, len(keywords) - 1)
    keyword = keywords[keyword_idx]
    description = descriptions[keyword_idx]
    current_word = "*" * len(keyword)
    guessed_characters = set()  # Set to store guessed characters
    # Send game start message to all players
    game_running = True
    game_start_message = "Game started!\n{}\n{}\n{}\n".format(len(keyword), description, current_word)
    for player in players:
        player.conn.send(game_start_message.encode())

    # Game logic
    turns = 0
    while game_running and any(p.guess_count < max_turns and p.active for p in players):
        current_player = players[turns % num_players]
        if not current_player.active:
            turns += 1
            continue
        # Send turn message to current player
        turn_message = "Player {}, it's your turn!\nTry to guess a character or the keyword (You can only guess the keyword from the 2nd turn): ".format(current_player.nickname)
        for player in players:
            if player == current_player:
                player.conn.send(turn_message.encode())
            else:
                player.conn.send("Waiting for other player's turn...".encode())

        # Set a timeout for receiving guess
        current_player.conn.settimeout(60)  # 60 seconds timeout for guess
        ready_to_read, _, _ = select.select([current_player.conn], [], [], 60)
        if current_player.conn in ready_to_read:
            try:
                guess = current_player.conn.recv(1024).decode().strip()
            except socket.timeout:
                current_player.conn.send("Timeout occurred. You missed your turn.".encode())
                current_player.guess_count += 1
                turns += 1
                continue
        else:
            current_player.conn.send("Timeout occurred. You missed your turn.".encode())
            turns += 1
            current_player.guess_count += 1
            continue

        if len(guess) > 1:
            if len(guess) == len(keyword):
                if current_player.guess_count > 0:
                    if guess.lower() == keyword.lower():
                        game_running = False
                        current_player.points += 5
                        end_game_message = "Congratulations to {} with the correct keyword: {}".format(current_player.nickname, keyword)
                        for player in players:
                            player.conn.send(end_game_message.encode())
                        end_game()
                        break
                    else:
                        current_player.active = False  # Player is no longer active
                        wrong_guess_message = "Incorrect guess! You are out of the game."
                        current_player.conn.send(wrong_guess_message.encode())
                else:
                    current_player.conn.send("You can only guess the keyword from the 2nd turn.".encode()) 
                    continue
            else:
                current_player.conn.send("Invalid guess. Please try again.".encode())
                continue
        else:
            if guess.lower() in guessed_characters:
                current_player.conn.send("This character has been guessed. Please guess again.".encode())
                continue
            elif guess.lower() in keyword.lower():
                occurrences = keyword.lower().count(guess.lower())
                guessed_characters.add(guess.lower())  # Add guessed character to the set
                current_word = update_current_word(keyword, current_word, guess)
                if "*" not in current_word:
                    game_running = False
                    current_player.points += 5
                    end_game_message = "Congratulations to {} with the correct keyword: {}".format(current_player.nickname, keyword)
                    for player in players:
                        player.conn.send(end_game_message.encode())
                    end_game()
                    break
                else:
                    current_player.points += 1
                    correct_guess_message = "Character '{}' has {} occurrence(s). Current Word: {}".format(guess, occurrences, current_word)
                    for player in players:
                        player.conn.send(correct_guess_message.encode())
            else:
                guessed_characters.add(guess.lower())  # Add guessed character to the set
                wrong_guess_message = "Character '{}' is not in the keyword.".format(guess)
                current_player.conn.send(wrong_guess_message.encode())
            current_player.guess_count += 1
            turns += 1

    # Game ended
    if game_running:
        end_game()


def update_current_word(keyword, current_word, guess):
    updated_word = ""
    for k, c in zip(keyword, current_word):
        if k.lower() == guess.lower() or c != "*":
            updated_word += k
        else:
            updated_word += "*"
    return updated_word

def end_game():
    global players, game_running
    game_running = False

    # Calculate and announce points
    points_message = "Game ended! Points:\n"
    points = [(p.nickname, p.points) for p in players]
    points.sort(key=lambda x: x[1], reverse=True)
    for i, (nickname, point) in enumerate(points):
        points_message += "{}. {}: {}\n".format(i + 1, nickname, point)

    # Announce points to all players
    for player in players:
        player.conn.send(points_message.encode())

    # Prompt players to restart the game
    # restart_message = "Do you want to restart the game? (Y/N): "
    # for player in players:
    #     player.conn.send(restart_message.encode())

    # Check players' responses
    responses = set()
    for player in players:
        response = player.conn.recv(1024).decode().strip().lower()
        responses.add(response)

    # If no player chooses to restart, start a new game
    if 'n' not in responses:
        for player in players:
            player.reset()
        start_game()
    else:
        # Notify players that the game is ending
        disconnect_message = "Game is ending. Thank you for playing!"
        for player in players:
            player.conn.send(disconnect_message.encode())
            player.conn.close()
        players.clear()

def main():
    global players, num_players, max_turns, game_running
    host = "localhost"
    port = 5555

    players = []
    keywords = []
    num_players = 2
    max_turns = 5
    game_running = False

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    print("Server started on {}:{}".format(host, port))

    while True:
        conn, addr = server.accept()
        print("Connected to {}:{}".format(addr[0], addr[1]))

        if len(players) < num_players:
            nickname = "Player{}".format(len(players) + 1)
            player = Player(conn, addr, nickname)
            thread = threading.Thread(target=handle_client, args=(player,))
            thread.start()
        else:
            conn.send("The game is full. Please try again later.\n".encode())

if __name__ == "__main__":
    main()
