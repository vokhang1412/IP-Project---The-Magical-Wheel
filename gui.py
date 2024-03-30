import pygame
import pygame_textinput
from enum import Enum 
import time

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

class GameState(Enum):
    REGISTERING = 0
    WAITING_FOR_START = 1
    PLAYING = 2
    WAITING_FOR_SERVER_RESPONSE = 3
    PLAYING_DISQUALIFIED = 4
 
class Game:
    def __init__(self):
        self._running = True
        pygame.init()
        pygame.time.set_timer(pygame.USEREVENT, 200)

        # Display configurations
        self._display_info = pygame.display.Info()
        self._screen = pygame.display.set_mode([self._display_info.current_w, self._display_info.current_h], pygame.HWSURFACE | pygame.DOUBLEBUF)

        # Game configurations
        self._game_state = GameState.REGISTERING
        
        self._start_time = pygame.time.get_ticks()
        self._timer_duration = 5000

        # Nickname input
        self._nickname_input_label = font.render('Enter a nickname:', True, (0, 0, 0))
        self._nickname_input_field = pygame_textinput.TextInputVisualizer()

        # Waiting announcement
        self._waiting = font.render('Waiting for game server to start...', True, (0, 0, 0))

        # Points
        self._points = 0
        self._points_text = font.render('Points: ' + str(self._points), True, (0, 0, 0))

        # Timer initial configurations
        self._start_time = pygame.time.get_ticks()
        self._timer_duration = 10000
        self._remaining_time = self._timer_duration // 1000
        self._timer = font.render('Time remaining: ' + str(self._remaining_time), True, (255, 0, 0))

        # Answer input
        self._keyword = font.render('Keyword: ******', True, (0, 0, 255))
        self._hint = font.render('Hint: This is a hint.', True, (0, 0, 255))
        self._answer_input_label = font.render('Enter your answer (a character or the whole keyword): ', True, (0, 0, 0))
        self._answer_input_field = pygame_textinput.TextInputVisualizer()

        # Disqualified announcement
        self._disqualified_1 = font.render('You have been disqualified!', True, (0, 0, 0))
        self._disqualified_2 = font.render('Waiting for the game to end...', True, (0, 0, 0))

        self.on_execute()
    
    # Check with the server if the nickname is already taken
    def is_nickname_valid(self, nickname):
        return True
    
    def on_submit_answer(self):
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
                    if (self.is_nickname_valid(nickname)):
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
            waiting_rect = self._waiting.get_rect()
            waiting_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2)
            self._screen.blit(self._waiting, waiting_rect)

            # TODO: Temporary code to simulate waiting for game server to start, remove later
            pygame.display.flip()
            time.sleep(3)
            self._game_state = GameState.PLAYING
            self.reset_timer()

        if (self._game_state == GameState.PLAYING):
            points_rect = self._points_text.get_rect()
            points_rect.center = (self._display_info.current_w // 2, 30)
            self._screen.blit(self._points_text, points_rect)

            timer_rect = self._timer.get_rect()
            timer_rect.center = (self._display_info.current_w // 2, 80)
            self._screen.blit(self._timer, timer_rect)

            keyword_rect = self._keyword.get_rect()
            keyword_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 - 50)
            self._screen.blit(self._keyword, keyword_rect)

            hint_rect = self._hint.get_rect()
            hint_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2)
            self._screen.blit(self._hint, hint_rect)

            answer_label_rect = self._answer_input_label.get_rect()
            answer_label_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 + 50)
            self._screen.blit(self._answer_input_label, answer_label_rect)

            input_field_rect = self._answer_input_field.surface.get_rect()
            input_field_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 + 100)
            self._screen.blit(self._answer_input_field.surface, input_field_rect)

        if (self._game_state == GameState.PLAYING_DISQUALIFIED):
            points_rect = self._points_text.get_rect()
            points_rect.center = (self._display_info.current_w // 2, 30)
            self._screen.blit(self._points_text, points_rect)

            disqualified_1_rect = self._disqualified_1.get_rect()
            disqualified_1_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2 - 50)
            self._screen.blit(self._disqualified_1, disqualified_1_rect)

            disqualified_2_rect = self._disqualified_2.get_rect()
            disqualified_2_rect.center = (self._display_info.current_w // 2, self._display_info.current_h // 2)
            self._screen.blit(self._disqualified_2, disqualified_2_rect)

        pygame.display.flip()
 
    def on_execute(self):
        while (self._running) :
            events = pygame.event.get()
            for event in events:
                self.on_event(event)

            if (self._game_state == GameState.REGISTERING):
                self._nickname_input_field.update(events)

            if (self._game_state == GameState.WAITING_FOR_START):
                pass
            
            if (self._game_state == GameState.PLAYING): 
                self._answer_input_field.update(events)
                self.handle_timer()

            if (self._game_state == GameState.PLAYING_DISQUALIFIED):
                pass   

            self.on_render()
        self.on_cleanup()

    def on_cleanup(self):
        pygame.quit()
 
game = Game()