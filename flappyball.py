"""
Flappy Ball Game Implementation using Pygame
This module creates a Flappy Bird-inspired game where the player controls a bouncing ball through obstacles.
"""

import pygame
from random import randint
import math


class FlappyBall:
    def __init__(self):
        """
        Initialize game parameters, colors, and game objects.
        All measurements are in pixels unless otherwise specified.
        """
        # Window configuration
        self.WIDTH = 400  # Game window width
        self.HEIGHT = 600  # Game window height
        self.FPS = 60  # Frames per second for game loop

        # Color definitions using RGB values
        self.WHITE = (255, 255, 255)  # UI text color
        self.BLUE_SKY = (150, 200, 255)  # Top color for sky gradient
        self.BLUE = (80, 160, 255)  # Bottom color for sky gradient
        self.GREEN = (40, 160, 40)  # Main pipe color
        self.DARK_GREEN = (20, 80, 20)  # Pipe stripe color
        self.YELLOW = (255, 255, 0)  # Ball fill color
        self.BLACK = (0, 0, 0)  # Ball outline color
        self.BROWN = (139, 69, 19)  # Ground base color
        self.DARK_BROWN = (80, 50, 20)  # Ground texture color

        # Ball physics parameters
        self.ball_size = 40  # Diameter of the ball
        self.ball_radius = self.ball_size // 2  # Radius for collision detection
        self.ball_x = self.WIDTH // 4  # Fixed horizontal position
        self.ball_y = self.HEIGHT // 2  # Initial vertical position (center)
        self.ball_vel = 0  # Current vertical velocity (pixels/frame)
        self.gravity = 0.75  # Downward acceleration per frame
        self.jump_velocity = -10  # Upward velocity applied on space press

        # Pipe configuration
        self.pipe_width = 80  # Width of each pipe obstacle
        self.pipe_speed = 3  # Horizontal movement speed (pixels/frame)
        self.pipe_gap = 250  # Vertical space between pipe pairs
        self.pipes = []  # List to store active pipe dictionaries
        self.next_pipe_time = 0  # Timestamp for next pipe spawn

        # Ground animation parameters
        self.ground_height = 15  # Height of the ground strip
        self.ground_speed = self.pipe_speed  # Sync with pipe movement
        self.ground_x = 0  # X-offset for scrolling effect

        # Game state management
        self.state = "start"  # Initial state: start -> play -> game_over cycle
        self.score = 0  # Current session score
        self.high_score = 0  # All-time best score

        # Precompute vertical gradient background (optimization)
        self.gradient_sky = pygame.Surface((self.WIDTH, self.HEIGHT))
        for y in range(self.HEIGHT):
            # Linear interpolation between BLUE_SKY (top) and BLUE (bottom)
            frac = y / (self.HEIGHT - 1)  # Normalized position (0-1)
            r_val = int(self.BLUE_SKY[0] + (self.BLUE[0] - self.BLUE_SKY[0]) * frac)
            g_val = int(self.BLUE_SKY[1] + (self.BLUE[1] - self.BLUE_SKY[1]) * frac)
            b_val = int(self.BLUE_SKY[2] + (self.BLUE[2] - self.BLUE_SKY[2]) * frac)
            pygame.draw.line(
                self.gradient_sky, (r_val, g_val, b_val), (0, y), (self.WIDTH - 1, y)
            )

    def run(self):
        """Main game loop handling initialization, input, and rendering."""
        pygame.init()
        screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        clock = pygame.time.Clock()
        font_large = pygame.font.SysFont(None, 48)  # For title text
        font_small = pygame.font.SysFont(None, 24)  # For score and instructions

        while True:  # Main game loop
            clock.tick(self.FPS)  # Maintain consistent frame rate
            current_time = pygame.time.get_ticks()  # Current timestamp in ms

            # Event handling ------------------------------------------------------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return  # Exit game
                elif event.type == pygame.KEYDOWN:
                    # Spacebar state machine
                    if self.state == "start" and event.key == pygame.K_SPACE:
                        self.reset_game()  # Start new game
                    elif self.state == "play" and event.key == pygame.K_SPACE:
                        self.ball_vel = self.jump_velocity  # Apply jump force
                    elif self.state == "game_over" and event.key == pygame.K_SPACE:
                        self.reset_game()  # Restart after game over

            # Game state logic ---------------------------------------------------
            if self.state != "play":
                # Floating animation using sine wave
                amplitude = 10.0  # Vertical movement range
                period = 800  # Wave cycle duration in ms
                # Calculate vertical offset using sine function
                offset = math.sin((current_time % period) * 2 * math.pi / period)
                self.ball_y = (self.HEIGHT // 2) + amplitude * offset

            if self.state == "play":
                # Physics simulation ---------------------------------------------
                self.ball_vel += self.gravity  # Apply gravity
                new_ball_y = self.ball_y + self.ball_vel  # Calculate new position

                # Ground collision and bounce mechanics
                ground_top = self.HEIGHT - self.ground_height  # Y position of ground
                if new_ball_y + self.ball_radius > ground_top:
                    # Keep ball above ground and apply bounce with energy loss
                    new_ball_y = ground_top - self.ball_radius
                    self.ball_vel = -(self.ball_vel * 0.85)  # 15% velocity loss

                self.ball_y = new_ball_y  # Update official position

                # Scrolling ground animation
                self.ground_x = (self.ground_x - self.pipe_speed) % -self.WIDTH

                # Pipe management ------------------------------------------------
                removed_pipes = []  # Pipes to remove this frame
                # Create ball's collision rectangle
                ball_rect = pygame.Rect(
                    self.ball_x - self.ball_radius,
                    self.ball_y - self.ball_radius,
                    2 * self.ball_radius,
                    2 * self.ball_radius,
                )

                for pipe in self.pipes:
                    pipe["x"] -= self.pipe_speed  # Move pipe left

                    # Create collision areas for pipe pair
                    top_rect = pygame.Rect(
                        pipe["x"], 0, self.pipe_width, pipe["top_height"]
                    )
                    bottom_rect = pygame.Rect(
                        pipe["x"],
                        pipe["bottom_y"],
                        self.pipe_width,
                        self.HEIGHT - pipe["bottom_y"],
                    )

                    # Collision detection with ball
                    if ball_rect.colliderect(top_rect) or ball_rect.colliderect(
                        bottom_rect
                    ):
                        self.hit_object()  # Handle collision

                    # Score increment logic
                    if ball_rect.left > pipe["x"] + self.pipe_width and not pipe.get(
                        "scored", False
                    ):
                        self.score += 1
                        pipe["scored"] = True  # Prevent duplicate scoring

                    # Mark pipes for removal when off-screen
                    if pipe["x"] + self.pipe_width < 0:
                        removed_pipes.append(pipe)

                # Remove expired pipes
                for p in removed_pipes:
                    self.pipes.remove(p)

                # Spawn new pipes at fixed intervals
                if current_time > self.next_pipe_time:
                    self.spawn_pipes()
                    self.next_pipe_time = current_time + 1500  # 1.5 second interval

            # Rendering pipeline -------------------------------------------------
            screen.blit(self.gradient_sky, (0, 0))  # Draw background

            if self.state == "play":
                # Draw all pipes with striped pattern
                for pipe in self.pipes:
                    # Create rectangles for pipe visualization
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

                    # Add vertical stripes to pipes
                    for rect in (top_rect, bottom_rect):
                        # Draw stripes at 20px intervals with 5px end padding
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
                screen.blit(score_text, (20, 16))  # Top-left position
                high_score_text = font_small.render(
                    f"High Score: {self.high_score}", True, self.WHITE
                )
                screen.blit(high_score_text, (self.WIDTH - 120, 16))  # Top-right

            # Draw animated ground -----------------------------------------------
            ground_y = self.HEIGHT - self.ground_height  # Base Y position
            # Main ground rectangle (double width for seamless scrolling)
            pygame.draw.rect(
                screen,
                self.BROWN,
                [self.ground_x, ground_y, self.WIDTH * 2, self.ground_height],
            )
            # Add random ground texture elements
            for i in range(0, int(self.WIDTH * 2), 15):  # Every 15px
                x = self.ground_x + i  # Current texture position
                rect_width = randint(3, 6)  # Random element width
                rect_height = randint(self.ground_height // 2, self.ground_height - 1)
                # Create texture rectangle
                ground_rect = pygame.Rect(
                    x,
                    ground_y + (self.ground_height - rect_height),
                    rect_width,
                    rect_height,
                )
                pygame.draw.rect(screen, self.DARK_BROWN, ground_rect)

            # Draw ball with outline ---------------------------------------------
            ellipse_rect = pygame.Rect(0, 0, self.ball_size, self.ball_size)
            ellipse_rect.center = (int(self.ball_x), int(self.ball_y))
            pygame.draw.ellipse(screen, self.YELLOW, ellipse_rect)  # Fill
            pygame.draw.ellipse(screen, self.BLACK, ellipse_rect, 3)  # Outline

            # Game state-specific UI ---------------------------------------------
            if self.state == "game_over":
                # Game over text elements
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
                # Start screen elements
                screen.blit(
                    font_large.render("FLAPPY BALL", True, self.WHITE),
                    (50, self.HEIGHT // 2 - 75),
                )
                screen.blit(
                    font_small.render("Press SPACE to Start", True, self.WHITE),
                    (50, self.HEIGHT // 2 + 45),
                )

            pygame.display.flip()  # Update display with all drawn elements

        pygame.quit()  # Cleanup (though unreachable in current loop structure)

    def reset_game(self):
        """Reset all game parameters to start fresh game session."""
        self.ball_y = self.HEIGHT // 2  # Reset vertical position
        self.ball_vel = 0  # Clear accumulated velocity
        self.score = 0  # Reset current score
        self.pipes.clear()  # Remove all existing pipes
        self.next_pipe_time = -1500  # Force immediate pipe spawn
        self.state = "play"  # Transition to play state

    def hit_object(self):
        """Handle collision events and transition to game over state."""
        # Update high score if current score is better
        if self.score > self.high_score:
            self.high_score = self.score
        self.state = "game_over"  # Change game state

    def spawn_pipes(self):
        """Generate new pipe pair with randomized vertical positioning."""
        # Ensure minimum 50px ceiling space and 200px total gap space
        top_height = randint(50, self.HEIGHT - 250)
        bottom_start_y = top_height + self.pipe_gap  # Calculate lower pipe position
        self.pipes.append(
            {
                "x": self.WIDTH,  # Spawn at right edge
                "top_height": top_height,  # Upper pipe height
                "bottom_y": bottom_start_y,  # Lower pipe starting Y
                "scored": False,  # Initialize scoring flag
            }
        )


if __name__ == "__main__":
    game = FlappyBall()
    game.run()
