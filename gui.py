import pygame
import pygame_textinput
from enum import Enum 
import time
import socket
import threading

# GUI for the players
# It contains: 
# - Nickname input field (done)
#   -> Prompt the user to enter a different nickname in case of clash (done)
# - Points
# - Timer countdown (done)
# - Keyword
# - Hint
# - Guess single character
# - Guess the whole word (after 2 turns)
#   -> Wait for the user's turn
# - Rankings after the game
# - An option to join the next game (done)

pygame.font.init()
font = pygame.font.SysFont('roboto.ttf', 35)

host = "localhost"
port = 5555
connected = True
game_exiting_event = threading.Event()
game_ending_event = threading.Event()
player_turn_event = threading.Event()
player_disqualified_event = threading.Event()

class GameState(Enum):
    REGISTERING = 0
    WAITING_FOR_START = 2
    PLAYING = 3
    ENDING = 4
    EXITING = 5

class TurnState(Enum):
    PLAYER_TURN = 0
    WAITING = 1
    DISQUALIFIED = 2
 
class Game:
    def __init__(self):
        self._running = True
        pygame.init()

        # Connect to the server
        self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client_socket.connect((host, port))
        # self.buffer_responses()
        
        thread = threading.Thread(target=self.handle_message)
        thread.start()

        # Display configurations
        self._display_info = pygame.display.Info()
        self._screen = pygame.display.set_mode([self._display_info.current_w, self._display_info.current_h], pygame.HWSURFACE | pygame.DOUBLEBUF)

        # Game configurations
        self._game_state = GameState.REGISTERING
        self._turn_state = TurnState.WAITING
        
        self._start_time = pygame.time.get_ticks()
        self._timer_duration = 5000

        self._keyword = ""
        self._description = ""

        # Utility flags
        # self._wait_flag = False
        # self._play_flag = False

        # Nickname input
        self._nickname_input_label = font.render('Enter a nickname: ', True, (0, 0, 0))
        self._nickname_input_field = pygame_textinput.TextInputVisualizer()

        # Points
        self._points = 0
        self._points_text = font.render('Points: ' + str(self._points), True, (0, 0, 0))

        # Timer initial configurations
        self._start_time = pygame.time.get_ticks()
        self._timer_duration = 60000
        self._remaining_time = self._timer_duration // 1000
        self._timer = font.render('Time remaining: ' + str(self._remaining_time), True, (255, 0, 0))

        # Answer input
        self.set_keyword_and_description('', '')
        self._answer_input_label = font.render('Enter your answer (a character or the whole keyword): ', True, (0, 0, 0))
        self._answer_input_field = pygame_textinput.TextInputVisualizer()

        # Game announcement
        self._annoucement_1 = ''
        self._announcement_1_text = font.render(self._annoucement_1, True, (0, 0, 0))
        self._annoucement_2 = ''
        self._announcement_2_text = font.render(self._annoucement_2, True, (0, 0, 0))
        self._annoucement_3 = ''
        self._announcement_3_text = font.render(self._annoucement_3, True, (0, 0, 0))
        self._annoucement_4 = ''
        self._announcement_4_text = font.render(self._annoucement_4, True, (0, 0, 0))
        self._annoucement_5 = ''
        self._announcement_5_text = font.render(self._annoucement_5, True, (0, 0, 0))
        self._annoucement_6 = ''
        self._announcement_6_text = font.render(self._annoucement_6, True, (0, 0, 0))
        self._annoucement_7 = ''
        self._announcement_7_text = font.render(self._annoucement_7, True, (0, 0, 0))

        self.on_execute()
    
    # Helper to buffer the unnecessary responses from the server
    # def buffer_responses(self):
    #     self._client_socket.recv(1024).decode()

    # Check with the server if the nickname is already taken
    def on_submit_nickname(self, nickname):
        self._client_socket.send(nickname.encode())
    #     response = self._client_socket.recv(1024).decode()
    #     if response == "Nickname already taken. Please enter a different one: ":
    #         return False
    #     return True
    
    def restart_game(self):
        # self._wait_flag = False
        # self._play_flag = False
        game_exiting_event.clear()
        game_ending_event.clear()
        player_turn_event.clear()
        player_disqualified_event.clear()
        self._game_state = GameState.WAITING_FOR_START

    # Wait for the server to send the game start message
    # def wait_for_start(self):
    #     response = self._client_socket.recv(1024).decode()
    #     while ("Game started!" not in response):
    #         response = self._client_socket.recv(1024).decode()
    #     self._game_state = GameState.PLAYING
    #     self.reset_timer()

    #     # Parse the keyword and description
    #     tmp = response.split('\n')
    #     keyword = tmp[3]
    #     description = tmp[2]
    #     self.set_keyword_and_description(keyword, description)
    #     self.set_annoucement(2, '')

    def set_keyword_and_description(self, keyword, description):
        self._keyword = keyword
        self._description = description
        self._keyword = font.render('Keyword: {}'.format(self._keyword), True, (0, 0, 255))
        self._hint = font.render('Hint: {}'.format(self._description), True, (0, 0, 255))

    def set_nickname_input_label(self, announcement):
        self._nickname_input_label = font.render(announcement, True, (255, 0, 0))
    
    def handle_message(self):
        while True:
            try:
                message = self._client_socket.recv(1024).decode()
                if not message:
                    break
                print(message)
                if message == "Nickname already taken or invalid length. Choose another one: ":
                    self.set_nickname_input_label(message)
                elif message == "Registration Completed Successfully":
                    self.set_nickname_input_label('Enter a nickname: ')
                    self._game_state = GameState.WAITING_FOR_START
                elif "Game started!" in message:
                    self._game_state = GameState.PLAYING
                    self.reset_timer()

                    # Parse the keyword and description
                    tmp = message.split('\n')
                    keyword = tmp[3]
                    description = tmp[2]
                    self.set_keyword_and_description(keyword, description)
                    self.set_annoucement(2, '')
                elif "Game ended!" in message:
                    game_ending_event.set()
                    lines = message.splitlines()

                    for i in range(len(lines)):
                        if (i == 0):
                            self.set_annoucement(i + 1, lines[i], (255, 0, 0))
                        else: 
                            self.set_annoucement(i + 1, lines[i])
                    self.set_annoucement(7, 'Press Y to join the next game or N to exit.', (0, 0, 255))
                elif "Game is ending" in message:
                    game_exiting_event.set()
                    break
                elif "it's your turn" in message:
                    player_turn_event.set()
                elif "You missed your turn." in message or "Waiting for other player's turn..." in message:
                    player_turn_event.clear()
                elif "You are out of the game." in message:
                    player_disqualified_event.set()
                elif message == "You can only guess the keyword from the 2nd turn." or message == "Invalid guess. Please try again." or message == "This character has been guessed. Please guess again.":
                    self.set_annoucement(2, message)
                elif "occurrence" in message:
                    words = message.split()
                    keyword = words[len(words) - 1]
                    message = " ".join(words[i] for i in range(5) if i < len(words))
                    self.set_keyword_and_description(keyword, self._description)
                    self.set_annoucement(2, message)
                elif "is not in the keyword." in message:
                    self.set_annoucement(2, message)
                elif "correct keyword" in message:
                    self.set_annoucement(1, '')
                    self.set_annoucement(2, message)
                else:
                    self.set_annoucement(1, message)
            except socket.timeout:
                player_turn_event.clear()
                break

    def set_annoucement(self, index, announcement, color=(0, 0, 0)):
        if (index == 1):
            self._annoucement_1 = announcement
            self._announcement_1_text = font.render(self._annoucement_1, True, color)
        elif (index == 2):
            self._annoucement_2 = announcement
            self._announcement_2_text = font.render(self._annoucement_2, True, (0, 0, 0))
        elif (index == 3):
            self._annoucement_3 = announcement
            self._announcement_3_text = font.render(self._annoucement_3, True, (0, 0, 0))
        elif (index == 4):
            self._annoucement_4 = announcement
            self._announcement_4_text = font.render(self._annoucement_4, True, (0, 0, 0))
        elif (index == 5):
            self._annoucement_5 = announcement
            self._announcement_5_text = font.render(self._annoucement_5, True, (0, 0, 0))
        elif (index == 6):
            self._annoucement_6 = announcement
            self._announcement_6_text = font.render(self._annoucement_6, True, (0, 0, 0))
        elif (index == 7):
            self._annoucement_7 = announcement
            self._announcement_7_text = font.render(self._annoucement_7, True, color)

    def on_submit_answer(self):
        self._client_socket.send(self._answer_input_field.value.encode())
        self.reset_timer()
        self._answer_input_field.value = ''

    def reset_timer(self):
        self._start_time = pygame.time.get_ticks()

    def handle_timer(self):
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self._start_time

        # Check if timer has finished
        if elapsed_time >= self._timer_duration:
            self.on_submit_answer()

        # Display remaining time
        self._remaining_time = (self._timer_duration - elapsed_time) // 1000 if (self._timer_duration - elapsed_time) // 1000 >= 0 else 0
        self._timer = font.render('Time remaining: ' + str(self._remaining_time), True, (255, 0, 0))

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

        if event.type == pygame.USEREVENT:
            pass

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_y and self._game_state == GameState.ENDING:
                self._client_socket.send("y".encode())
                self.restart_game()
            elif event.key == pygame.K_n and self._game_state == GameState.ENDING:
                self._client_socket.send("n".encode())
                game_exiting_event.set()
            elif event.key == pygame.K_RETURN:
                if (self._game_state == GameState.REGISTERING):
                    self.on_submit_nickname(self._nickname_input_field.value)
                    # nickname = self._nickname_input_field.value
                    # if (self.on_submit_nickname(nickname)):
                    #     self._game_state = GameState.WAITING_FOR_START
                    # else:
                    #     self._nickname_input_label = font.render('Nickname already taken. Please enter a different one: ', True, (255, 0, 0))
                    #     self._nickname_input_field.value = ''
                    pass
                elif (self._game_state == GameState.PLAYING):
                    self.on_submit_answer()

    def on_render(self):
        self._screen.fill((255, 255, 255))
        
        if (self._game_state == GameState.REGISTERING):
            label_rect = self._nickname_input_label.get_rect()
            label_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 - 50)
            self._screen.blit(self._nickname_input_label, label_rect)

            input_field_rect = self._nickname_input_field.surface.get_rect()
            input_field_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2)
            self._screen.blit(self._nickname_input_field.surface, input_field_rect)

        elif (self._game_state == GameState.WAITING_FOR_START):
            announce_1_rect = self._announcement_1_text.get_rect()
            announce_1_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2)
            self._screen.blit(self._announcement_1_text, announce_1_rect)

            announce_2_rect = self._announcement_2_text.get_rect()
            announce_2_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 + 50)
            self._screen.blit(self._announcement_2_text, announce_2_rect)

        elif (self._game_state == GameState.PLAYING):
            # points_rect = self._points_text.get_rect()
            # points_rect.center = (self._display_info.current_w // 2, 30)
            # self._screen.blit(self._points_text, points_rect)

            keyword_rect = self._keyword.get_rect()
            keyword_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 - 50)
            self._screen.blit(self._keyword, keyword_rect)

            hint_rect = self._hint.get_rect()
            hint_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2)
            self._screen.blit(self._hint, hint_rect)

            if (self._turn_state == TurnState.PLAYER_TURN):
                timer_rect = self._timer.get_rect()
                timer_rect.center = (self._display_info.current_w // 2, 80)
                self._screen.blit(self._timer, timer_rect)

                answer_label_rect = self._answer_input_label.get_rect()
                answer_label_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 + 50)
                self._screen.blit(self._answer_input_label, answer_label_rect)

                input_field_rect = self._answer_input_field.surface.get_rect()
                input_field_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 + 100)
                self._screen.blit(self._answer_input_field.surface, input_field_rect)

            announce_1_rect = self._announcement_1_text.get_rect()
            announce_1_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 + 150)
            self._screen.blit(self._announcement_1_text, announce_1_rect)

            announce_2_rect = self._announcement_2_text.get_rect()
            announce_2_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 + 200)
            self._screen.blit(self._announcement_2_text, announce_2_rect)

        elif (self._game_state == GameState.ENDING):
            announce_1_rect = self._announcement_1_text.get_rect()
            announce_1_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 - 150)
            self._screen.blit(self._announcement_1_text, announce_1_rect)

            announce_2_rect = self._announcement_2_text.get_rect()
            announce_2_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 - 100)
            self._screen.blit(self._announcement_2_text, announce_2_rect)

            announce_3_rect = self._announcement_3_text.get_rect()
            announce_3_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 - 50)
            self._screen.blit(self._announcement_3_text, announce_3_rect)

            announce_4_rect = self._announcement_4_text.get_rect()
            announce_4_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2)
            self._screen.blit(self._announcement_4_text, announce_4_rect)

            announce_5_rect = self._announcement_5_text.get_rect()
            announce_5_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 + 50)
            self._screen.blit(self._announcement_5_text, announce_5_rect)

            announce_6_rect = self._announcement_6_text.get_rect()
            announce_6_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 + 100)
            self._screen.blit(self._announcement_6_text, announce_6_rect)

            announce_7_rect = self._announcement_7_text.get_rect()
            announce_7_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 + 150)
            self._screen.blit(self._announcement_7_text, announce_7_rect)

        pygame.display.flip()
 
    def on_execute(self):
        while (self._running) :
            self.on_render()

            events = pygame.event.get()
            for event in events:
                self.on_event(event)

            if (self._game_state == GameState.REGISTERING):
                self._nickname_input_field.update(events)

            # if (self._game_state == GameState.WAITING_FOR_START and not self._wait_flag):
            if (self._game_state == GameState.WAITING_FOR_START):
                self.set_annoucement(1, 'Waiting for other players...')
                self.set_annoucement(2, 'Game will exit automatically if not enough player joins.')
                # Start the handler thread only once
                # self._wait_flag = True
                # thread = threading.Thread(target=self.wait_for_start)
                # thread.start()

            
            if (self._game_state == GameState.PLAYING):
                # Start the handler thread only once
                # if (not self._play_flag):
                #     print('reach self._play_flag')
                #     self._play_flag = True
                #     thread = threading.Thread(target=self.handle_message)
                #     thread.start()
                
                if (game_ending_event.is_set()):
                    self._game_state = GameState.ENDING

                elif (player_disqualified_event.is_set()):
                    self._turn_state = TurnState.DISQUALIFIED
                    self.set_annoucement(1, 'Incorrect guess! You are out of the game!')

                elif (player_turn_event.is_set()):
                    self._turn_state = TurnState.PLAYER_TURN
                    self.set_annoucement(1, '')
                    self._answer_input_field.update(events)
                    self.handle_timer()

                else:
                    self._turn_state = TurnState.WAITING
                    self.set_annoucement(1, 'Waiting for other players\' turn...')

            if (self._game_state == GameState.ENDING):
                pass

            if (game_exiting_event.is_set()):
                self._game_state = GameState.EXITING

            if (self._game_state == GameState.EXITING):
                self._running = False

        self.on_cleanup()

    def on_cleanup(self):
        pygame.quit()
 
game = Game()