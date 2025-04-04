import pygame

# Create a 32x32 surface
icon = pygame.Surface((32, 32))
icon.fill((0, 0, 0))  # Black background

# Draw a simple fighting game icon
pygame.draw.rect(icon, (255, 0, 0), (8, 8, 16, 16))  # Red square
pygame.draw.line(icon, (255, 255, 255), (12, 12), (20, 20), 2)  # White cross
pygame.draw.line(icon, (255, 255, 255), (20, 12), (12, 20), 2)

# Save the icon
pygame.image.save(icon, "game_icon.png") 