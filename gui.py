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
game_ended = False
game_end_event = threading.Event()
player_turn_event = threading.Event()
player_disqualified_event = threading.Event()

class GameState(Enum):
    REGISTERING = 0
    WAITING_FOR_START = 2
    PLAYING = 3
    WAITING_FOR_SERVER_RESPONSE = 4

class TurnState(Enum):
    PLAYER_TURN = 0
    WAITING = 1
    DISQUALIFIED = 2

class ANSWER(Enum):
    CORRECT_CHARACTER = 0
    INCORRECT_CHARACTER = 1
    CORRECT_KEYWORD = 2
    INCORRECT_KEYWORD = 3
    INVALID = 4
 
class Game:
    def __init__(self):
        self._running = True
        pygame.init()

        # Connect to the server
        self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client_socket.connect((host, port))
        self.buffer_responses()

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
        self._wait_flag = False
        self._play_flag = False

        # Nickname input
        self._nickname_input_label = font.render('Enter a nickname: ', True, (0, 0, 0))
        self._nickname_input_field = pygame_textinput.TextInputVisualizer()

        # Waiting announcement
        self._announcement_text = font.render('Waiting for game server to start...', True, (0, 0, 0))

        # Points
        self._points = 0
        self._points_text = font.render('Points: ' + str(self._points), True, (0, 0, 0))

        # Timer initial configurations
        self._start_time = pygame.time.get_ticks()
        self._timer_duration = 10000
        self._remaining_time = self._timer_duration // 1000
        self._timer = font.render('Time remaining: ' + str(self._remaining_time), True, (255, 0, 0))

        # Answer input
        self.set_keyword_and_description('', '')
        self._answer_input_label = font.render('Enter your answer (a character or the whole keyword): ', True, (0, 0, 0))
        self._answer_input_field = pygame_textinput.TextInputVisualizer()

        # Game announcement
        self._annoucement = ''
        self._announcement_text = font.render(self._annoucement, True, (0, 0, 0))

        self.on_execute()
    
    # Helper to buffer the unnecessary responses from the server
    def buffer_responses(self):
        self._client_socket.recv(1024).decode()

    # Check with the server if the nickname is already taken
    def on_submit_nickname(self, nickname):
        self._client_socket.send(nickname.encode())
        response = self._client_socket.recv(1024).decode()
        if response == "Nickname already taken. Please enter a different one: ":
            return False
        return True
    
    # Wait for the server to send the game start message
    def wait_for_start(self):
        response = self._client_socket.recv(1024).decode()
        while ("Game started!" not in response):
            response = self._client_socket.recv(1024).decode()

        self._game_state = GameState.PLAYING
        self.reset_timer()

        # Parse the keyword and description
        tmp = response.split('\n')
        keyword = tmp[3]
        description = tmp[2]
        self.set_keyword_and_description(keyword, description)

    def set_keyword_and_description(self, keyword, description):
        self._keyword = keyword
        self._description = description
        self._keyword = font.render('Keyword: {}'.format(self._keyword), True, (0, 0, 255))
        self._hint = font.render('Hint: {}'.format(self._description), True, (0, 0, 255))
    
    def handle_turn_events(self):
        while True:
            try:
                message = self._client_socket.recv(1024).decode()
                if not message:
                    break
                print(message)
                if message == "Game is ending. Thank you for playing!":
                    game_end_event.set()
                    break
                elif "your turn" in message.lower():
                    player_turn_event.set()
                elif "missed your turn" in message.lower():
                    player_turn_event.clear()
                elif "out of the game" in message.lower():
                    player_disqualified_event.set()
                elif "occurence" in message.lower():
                    pass
            except socket.timeout:
                player_turn_event.clear()
                break

    def set_annoucement(self, announcement):
        self._annoucement = announcement
        self._announcement_text = font.render(self._annoucement, True, (0, 0, 0))

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
            if event.key == pygame.K_RETURN:
                if (self._game_state == GameState.REGISTERING):
                    nickname = self._nickname_input_field.value
                    if (self.on_submit_nickname(nickname)):
                        self._game_state = GameState.WAITING_FOR_START
                    else:
                        self._nickname_input_label = font.render('Nickname already taken. Please enter a different one: ', True, (255, 0, 0))
                        self._nickname_input_field.value = ''
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

        if (self._game_state == GameState.WAITING_FOR_START):
            announce_rect = self._announcement_text.get_rect()
            announce_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2)
            self._screen.blit(self._announcement_text, announce_rect)

        if (self._game_state == GameState.PLAYING):
            points_rect = self._points_text.get_rect()
            points_rect.center = (self._display_info.current_w // 2, 30)
            self._screen.blit(self._points_text, points_rect)

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
            else:
                announce_rect = self._announcement_text.get_rect()
                announce_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 + 50)
                self._screen.blit(self._announcement_text, announce_rect)

        pygame.display.flip()
 
    def on_execute(self):
        while (self._running) :
            self.on_render()

            events = pygame.event.get()
            for event in events:
                self.on_event(event)

            if (self._game_state == GameState.REGISTERING):
                self._nickname_input_field.update(events)

            if (self._game_state == GameState.WAITING_FOR_START and not self._wait_flag):
                # Start the handler thread only once
                self._wait_flag = True
                thread = threading.Thread(target=self.wait_for_start)
                thread.start()
            
            if (self._game_state == GameState.PLAYING):
                # Start the handler thread only once
                if (not self._play_flag):
                    self._play_flag = True
                    thread = threading.Thread(target=self.handle_turn_events)
                    thread.start()

                if (player_disqualified_event.is_set()):
                    self._turn_state = TurnState.DISQUALIFIED
                    self.set_annoucement('You are out of the game!')
                else:
                    if (player_turn_event.is_set()):
                        self._turn_state = TurnState.PLAYER_TURN
                        self._answer_input_field.update(events)
                        self.handle_timer()
                    else:
                        self._turn_state = TurnState.WAITING
                        self.set_annoucement('Waiting for other players\' turn...')

                if (game_end_event.is_set()):
                    pass

        self.on_cleanup()

    def on_cleanup(self):
        pygame.quit()
 
game = Game()