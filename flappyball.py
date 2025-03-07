import pygame
from random import randint
import math


class FlappyBall:
    def __init__(self):
        # Window configuration
        self.WIDTH = 400
        self.HEIGHT = 600
        self.FPS = 60

        # Color definitions (RGB tuples)
        self.WHITE = (255, 255, 255)
        self.BLUE_SKY = (150, 200, 255)  # Sky gradient top color
        self.BLUE = (80, 160, 255)  # Sky gradient bottom color
        self.GREEN = (40, 160, 40)  # Pipe base color
        self.DARK_GREEN = (20, 80, 20)  # Pipe stripe color
        self.YELLOW = (255, 255, 0)  # Ball color
        self.BLACK = (0, 0, 0)  # Ball outline
        self.BROWN = (139, 69, 19)  # Ground base color
        self.DARK_BROWN = (80, 50, 20)  # Ground texture color

        # Ball physics parameters
        self.ball_size = 40
        self.ball_radius = self.ball_size // 2
        self.ball_x = self.WIDTH // 4  # Initial horizontal position
        self.ball_y = self.HEIGHT // 2  # Initial vertical position
        self.ball_vel = 0  # Current vertical velocity
        self.gravity = 0.75  # Acceleration per frame
        self.jump_velocity = -10  # Velocity applied on jump

        # Pipe configuration
        self.pipe_width = 80  # Width of each pipe
        self.pipe_speed = 3  # Horizontal movement speed
        self.pipe_gap = 250  # Vertical space between pipes
        self.pipes = []  # Active pipes storage
        self.next_pipe_time = 0  # Timer for new pipe spawns

        # Ground animation parameters
        self.ground_height = 15  # Visible ground thickness
        self.ground_speed = self.pipe_speed
        self.ground_x = 0  # Scrolling offset

        # Game state management
        self.state = "start"  # Possible: start/play/game_over
        self.score = 0
        self.high_score = 0

        # Precompute vertical gradient for sky background
        self.gradient_sky = pygame.Surface((self.WIDTH, self.HEIGHT))
        for y in range(self.HEIGHT):
            # Calculate color interpolation between BLUE_SKY and BLUE
            frac = y / (self.HEIGHT - 1)
            r_val = int(self.BLUE_SKY[0] + (self.BLUE[0] - self.BLUE_SKY[0]) * frac)
            g_val = int(self.BLUE_SKY[1] + (self.BLUE[1] - self.BLUE_SKY[1]) * frac)
            b_val = int(self.BLUE_SKY[2] + (self.BLUE[2] - self.BLUE_SKY[2]) * frac)
            pygame.draw.line(
                self.gradient_sky, (r_val, g_val, b_val), (0, y), (self.WIDTH - 1, y)
            )

    def run(self):
        """Main game loop handling initialization and continuous updates."""
        pygame.init()
        screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        clock = pygame.time.Clock()
        font_large = pygame.font.SysFont(None, 48)  # For title text
        font_small = pygame.font.SysFont(None, 24)  # For UI elements

        while True:
            clock.tick(self.FPS)
            current_time = pygame.time.get_ticks()

            # Event handling for window close and keyboard input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    # Spacebar handling for different game states
                    if self.state == "start" and event.key == pygame.K_SPACE:
                        self.reset_game()
                    elif self.state == "play" and event.key == pygame.K_SPACE:
                        self.ball_vel = self.jump_velocity  # Apply jump
                    elif self.state == "game_over" and event.key == pygame.K_SPACE:
                        self.reset_game()

            # Animate ball floating in start/game_over states
            if self.state != "play":
                # Sine wave animation parameters
                amplitude = 10.0
                period = 800  # Milliseconds per oscillation
                offset = math.sin((current_time % period) * 2 * math.pi / period)
                self.ball_y = (self.HEIGHT // 2) + amplitude * offset

            if self.state == "play":
                # Physics update: apply gravity to velocity
                self.ball_vel += self.gravity
                new_ball_y = self.ball_y + self.ball_vel

                # Ground collision and bounce physics
                ground_top = self.HEIGHT - self.ground_height
                if new_ball_y + self.ball_radius > ground_top:
                    new_ball_y = ground_top - self.ball_radius
                    self.ball_vel = -(self.ball_vel * 0.85)  # Energy loss on bounce

                self.ball_y = new_ball_y

                # Animate scrolling ground
                self.ground_x = (self.ground_x - self.pipe_speed) % -self.WIDTH

                # Process pipes and collisions
                removed_pipes = []
                ball_rect = pygame.Rect(
                    self.ball_x - self.ball_radius,
                    self.ball_y - self.ball_radius,
                    2 * self.ball_radius,
                    2 * self.ball_radius,
                )

                for pipe in self.pipes:
                    pipe["x"] -= self.pipe_speed  # Move pipe left

                    # Define pipe collision rectangles
                    top_rect = pygame.Rect(
                        pipe["x"], 0, self.pipe_width, pipe["top_height"]
                    )
                    bottom_rect = pygame.Rect(
                        pipe["x"],
                        pipe["bottom_y"],
                        self.pipe_width,
                        self.HEIGHT - pipe["bottom_y"],
                    )

                    # Collision detection with pipes
                    if ball_rect.colliderect(top_rect) or ball_rect.colliderect(
                        bottom_rect
                    ):
                        self.hit_object()

                    # Score when ball passes pipe
                    if ball_rect.left > pipe["x"] + self.pipe_width and not pipe.get(
                        "scored", False
                    ):
                        self.score += 1
                        pipe["scored"] = True

                    # Mark off-screen pipes for removal
                    if pipe["x"] + self.pipe_width < 0:
                        removed_pipes.append(pipe)

                # Remove expired pipes
                for p in removed_pipes:
                    self.pipes.remove(p)

                # Spawn new pipes at timed intervals
                if current_time > self.next_pipe_time:
                    self.spawn_pipes()
                    self.next_pipe_time = (
                        current_time + 1500
                    )  # 1.5 seconds between pipes

            # Render all game elements
            screen.blit(self.gradient_sky, (0, 0))  # Draw background

            if self.state == "play":
                # Draw pipes with striped pattern
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

                    # Base pipe color
                    pygame.draw.rect(screen, self.GREEN, top_rect)
                    pygame.draw.rect(screen, self.GREEN, bottom_rect)

                    # Vertical stripes on pipes
                    for rect in (top_rect, bottom_rect):
                        for x in range(rect.x + 10, rect.right - 5, 20):
                            pygame.draw.line(
                                screen,
                                self.DARK_GREEN,
                                (x, rect.y),
                                (x, rect.bottom),
                                3,
                            )

                # Score displays
                score_text = font_small.render(f"Score: {self.score}", True, self.WHITE)
                screen.blit(score_text, (20, 16))
                high_score_text = font_small.render(
                    f"High Score: {self.high_score}", True, self.WHITE
                )
                screen.blit(high_score_text, (self.WIDTH - 120, 16))

            # Draw animated ground with texture
            ground_y = self.HEIGHT - self.ground_height
            pygame.draw.rect(
                screen,
                self.BROWN,
                [self.ground_x, ground_y, self.WIDTH * 2, self.ground_height],
            )
            # Generate random ground texture
            for i in range(0, int(self.WIDTH * 2), 15):
                x = self.ground_x + i
                rect_width = randint(3, 6)
                rect_height = randint(self.ground_height // 2, self.ground_height - 1)
                pygame.draw.rect(
                    screen,
                    self.DARK_BROWN,
                    pygame.Rect(
                        x,
                        ground_y + (self.ground_height - rect_height),
                        rect_width,
                        rect_height,
                    ),
                )

            # Render ball with outline
            ellipse_rect = pygame.Rect(0, 0, self.ball_size, self.ball_size)
            ellipse_rect.center = (int(self.ball_x), int(self.ball_y))
            pygame.draw.ellipse(screen, self.YELLOW, ellipse_rect)
            pygame.draw.ellipse(screen, self.BLACK, ellipse_rect, 3)

            # Game state-specific UI elements
            if self.state == "game_over":
                screen.blit(
                    font_small.render("GAME OVER...", True, self.WHITE),
                    (50, self.HEIGHT // 2 - 105),
                )
                screen.blit(
                    font_small.render(f"Final Score: {self.score}", True, self.WHITE),
                    (50, self.HEIGHT // 2 + 75),
                )
                screen.blit(
                    font_small.render(
                        f"High Score: {self.high_score}", True, self.WHITE
                    ),
                    (50, self.HEIGHT // 2 + 105),
                )
                screen.blit(
                    font_large.render("FLAPPY BALL", True, self.WHITE),
                    (50, self.HEIGHT // 2 - 75),
                )
                screen.blit(
                    font_small.render("Press SPACE to Restart", True, self.WHITE),
                    (50, self.HEIGHT // 2 + 45),
                )

            elif self.state == "start":
                screen.blit(
                    font_large.render("FLAPPY BALL", True, self.WHITE),
                    (50, self.HEIGHT // 2 - 75),
                )
                screen.blit(
                    font_small.render("Press SPACE to Start", True, self.WHITE),
                    (50, self.HEIGHT // 2 + 45),
                )

            pygame.display.flip()

        pygame.quit()

    def reset_game(self):
        """Reset game state to initial play conditions."""
        self.ball_y = self.HEIGHT // 2
        self.ball_vel = 0
        self.score = 0
        self.pipes.clear()
        self.next_pipe_time = -1500  # Force immediate pipe spawn
        self.state = "play"

    def hit_object(self):
        """Handle collision events and transition to game over state."""
        if self.score > self.high_score:
            self.high_score = self.score
        self.state = "game_over"

    def spawn_pipes(self):
        """Generate new pipe pair with random gap position."""
        top_height = randint(50, self.HEIGHT - 250)  # Ensure minimum gap space
        bottom_start_y = top_height + self.pipe_gap
        self.pipes.append(
            {
                "x": self.WIDTH,  # Spawn at right edge
                "top_height": top_height,  # Upper pipe height
                "bottom_y": bottom_start_y,  # Lower pipe starting Y
            }
        )


if __name__ == "__main__":
    game = FlappyBall()
    game.run()
