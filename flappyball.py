import pygame
from random import randint
import math


class FlappyBall:
    def __init__(self):
        self.WIDTH = 400
        self.HEIGHT = 600
        self.FPS = 60

        # Colors
        self.WHITE = (255, 255, 255)
        self.BLUE_SKY = (150, 200, 255)
        self.BLUE = (80, 160, 255)
        self.GREEN = (40, 160, 40)
        self.DARK_GREEN = (20, 80, 20)
        self.YELLOW = (255, 255, 0)
        self.BLACK = (0, 0, 0)
        self.BROWN = (139, 69, 19)
        self.DARK_BROWN = (80, 50, 20)

        # Ball setup
        self.ball_size = 40
        self.ball_radius = self.ball_size // 2
        self.ball_x = self.WIDTH // 4
        self.ball_y = self.HEIGHT // 2
        self.ball_vel = 0
        self.gravity = 0.75
        self.jump_velocity = -10

        # Pipes setup
        self.pipe_width = 80
        self.pipe_speed = 3
        self.pipe_gap = 250
        self.pipes = []
        self.next_pipe_time = 0

        # Ground setup
        self.ground_height = 15
        self.ground_speed = self.pipe_speed
        self.ground_x = 0

        # Game state
        self.state = "start"
        self.score = 0
        self.high_score = 0

        # Precompute gradient sky background
        self.gradient_sky = pygame.Surface((self.WIDTH, self.HEIGHT))
        for y in range(self.HEIGHT):
            frac = y / (self.HEIGHT - 1)
            r_val = int(self.BLUE_SKY[0] + (self.BLUE[0] - self.BLUE_SKY[0]) * frac)
            g_val = int(self.BLUE_SKY[1] + (self.BLUE[1] - self.BLUE_SKY[1]) * frac)
            b_val = int(self.BLUE_SKY[2] + (self.BLUE[2] - self.BLUE_SKY[2]) * frac)
            pygame.draw.line(
                self.gradient_sky, (r_val, g_val, b_val), (0, y), (self.WIDTH - 1, y)
            )

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        clock = pygame.time.Clock()
        font_large = pygame.font.SysFont(None, 48)
        font_small = pygame.font.SysFont(None, 24)

        while True:
            clock.tick(self.FPS)
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    if self.state == "start" and event.key == pygame.K_SPACE:
                        self.reset_game()
                    elif self.state == "play" and event.key == pygame.K_SPACE:
                        self.ball_vel = self.jump_velocity
                    elif self.state == "game_over" and event.key == pygame.K_SPACE:
                        self.reset_game()

            # Ball animation in non-play states
            if self.state != "play":
                amplitude = 10.0
                period = 800
                offset = math.sin((current_time % period) * 2 * math.pi / period)
                self.ball_y = (self.HEIGHT // 2) + amplitude * offset

            if self.state == "play":
                # Game Logic
                self.ball_vel += self.gravity

                new_ball_y = self.ball_y + self.ball_vel

                # Ground collision check for bounce
                ground_top = self.HEIGHT - self.ground_height
                if new_ball_y + self.ball_radius > ground_top:
                    # Bounce
                    new_ball_y = ground_top - self.ball_radius
                    self.ball_vel = -(self.ball_vel * 0.85)

                # Update y position
                self.ball_y = new_ball_y

                # Ground movement
                self.ground_x = (self.ground_x - self.pipe_speed) % -self.WIDTH

                # Pipe Processing
                removed_pipes = []
                ball_rect = pygame.Rect(
                    self.ball_x - self.ball_radius,
                    self.ball_y - self.ball_radius,
                    2 * self.ball_radius,
                    2 * self.ball_radius,
                )

                for pipe in self.pipes:
                    pipe["x"] -= self.pipe_speed
                    top_rect = pygame.Rect(
                        pipe["x"], 0, self.pipe_width, pipe["top_height"]
                    )
                    bottom_rect = pygame.Rect(
                        pipe["x"],
                        pipe["bottom_y"],
                        self.pipe_width,
                        self.HEIGHT - pipe["bottom_y"],
                    )

                    # Collision detection
                    if ball_rect.colliderect(top_rect) or ball_rect.colliderect(
                        bottom_rect
                    ):
                        self.hit_object()

                    # Scoring
                    if ball_rect.left > pipe["x"] + self.pipe_width and not pipe.get(
                        "scored", False
                    ):
                        self.score += 1
                        pipe["scored"] = True

                    # Remove off-screen pipes
                    if pipe["x"] + self.pipe_width < 0:
                        removed_pipes.append(pipe)

                # Clean-up old pipes
                for p in removed_pipes:
                    self.pipes.remove(p)

                # Spawn new pipes
                if current_time > self.next_pipe_time:
                    self.spawn_pipes()
                    self.next_pipe_time = current_time + 1500

            # Drawing
            screen.blit(self.gradient_sky, (0, 0))

            if self.state == "play":
                for pipe in self.pipes:
                    top_rect = pygame.Rect(
                        pipe["x"], 0, self.pipe_width, pipe["top_height"]
                    )
                    bottom_rect = pygame.Rect(
                        pipe["x"],
                        pipe["bottom_y"],
                        self.pipe_width,
                        self.HEIGHT - pipe["bottom_y"],
                    )

                    # Draw pipes with vertical stripes
                    for rect in (top_rect, bottom_rect):
                        pygame.draw.rect(screen, self.GREEN, rect)
                        for x in range(rect.x + 10, rect.right - 5, 20):
                            pygame.draw.line(
                                screen,
                                self.DARK_GREEN,
                                (x, rect.y),
                                (x, rect.bottom),
                                3,
                            )

                # Display text
                score_text = font_small.render(f"Score: {self.score}", True, self.WHITE)
                screen.blit(score_text, (20, 16))

                high_score_text = font_small.render(
                    f"High Score: {self.high_score}", True, self.WHITE
                )
                screen.blit(high_score_text, (self.WIDTH - 120, 16))

            # Draw animated ground
            ground_y = self.HEIGHT - self.ground_height
            pygame.draw.rect(
                screen,
                self.BROWN,
                [self.ground_x, ground_y, self.WIDTH * 2, self.ground_height],
            )

            # Ground texture
            for i in range(0, int(self.WIDTH * 2), 15):
                x = self.ground_x + i
                rect_width = randint(3, 6)
                rect_height = randint(self.ground_height // 2, self.ground_height - 1)
                ground_rect = pygame.Rect(
                    x,
                    ground_y + (self.ground_height - rect_height),
                    rect_width,
                    rect_height,
                )
                pygame.draw.rect(screen, self.DARK_BROWN, ground_rect)

            # Draw ball
            ellipse_rect = pygame.Rect(0, 0, self.ball_size, self.ball_size)
            ellipse_rect.center = (int(self.ball_x), int(self.ball_y))

            # Draw circle and ring
            pygame.draw.ellipse(screen, self.YELLOW, ellipse_rect)
            pygame.draw.ellipse(screen, self.BLACK, ellipse_rect, 3)

            if self.state == "game_over":
                gameover_text = font_small.render("GAME OVER...", True, self.WHITE)
                screen.blit(gameover_text, (50, self.HEIGHT // 2 - 105))

                score_line = f"Final Score: {self.score}"
                screen.blit(
                    font_small.render(score_line, True, self.WHITE),
                    (50, self.HEIGHT // 2 + 75),
                )

                high_score_line = f"High Score: {self.high_score}"
                screen.blit(
                    font_small.render(high_score_line, True, self.WHITE),
                    (50, self.HEIGHT // 2 + 105),
                )

                welcome = font_large.render("FLAPPY BALL", True, self.WHITE)
                screen.blit(welcome, (50, self.HEIGHT // 2 - 75))

                instruct_restart = font_small.render(
                    "Press SPACE to Restart", True, self.WHITE
                )
                screen.blit(instruct_restart, (50, self.HEIGHT // 2 + 45))

            elif self.state == "start":
                welcome = font_large.render("FLAPPY BALL", True, self.WHITE)
                screen.blit(welcome, (50, self.HEIGHT // 2 - 75))

                instruct_start = font_small.render(
                    "Press SPACE to Start", True, self.WHITE
                )
                screen.blit(instruct_start, (50, self.HEIGHT // 2 + 45))

            pygame.display.flip()

        pygame.quit()

    def reset_game(self):
        self.ball_y = self.HEIGHT // 2
        self.ball_vel = 0
        self.score = 0
        self.pipes.clear()
        self.next_pipe_time = -1500
        self.state = "play"

    def hit_object(self):
        if self.score > self.high_score:
            self.high_score = self.score
        self.state = "game_over"

    def spawn_pipes(self):
        top_height = randint(50, self.HEIGHT - 250)
        bottom_start_y = top_height + self.pipe_gap
        new_pipe = {
            "x": self.WIDTH,
            "top_height": top_height,
            "bottom_y": bottom_start_y,
        }
        self.pipes.append(new_pipe)


if __name__ == "__main__":
    game = FlappyBall()
    game.run()
