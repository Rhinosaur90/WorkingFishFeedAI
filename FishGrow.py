import pygame
import random
import numpy as np
from enum import Enum
from collections import namedtuple


class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4
pygame.init()
font = pygame.font.Font('arial.ttf', 25)
    
Fish = namedtuple('Fish', ['point','size'])
Point = namedtuple('Point', 'x, y')
# rgb colors
WHITE = (255, 255, 255)
RED = (200,0,0)
GREEN = (0,255,0)
BLACK = (0,0,0)

BLOCK_SIZE = 20
SPEED = 90

class FishGame:

    def __init__(self, w=1280, h=960):
        self.w = w
        self.h = h
        # init display
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Maze')
        self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        self.direction = Direction.RIGHT
        self.Shifter = Point(self.w/2, self.h/2)
        self.score = 0
        self.size = 4
        self.AllFish = []
        self.frame_iteration = 0
        self.spawn_first()
        for i in range(10):
            self.spawn_fish()

    def spawn_fish(self):
        tempblock = BLOCK_SIZE/20
        newPoint = Point(random.randint(tempblock,(self.w/20)-tempblock)*20,random.randint(tempblock,(self.h/20)-tempblock)*20)
        F = Fish(newPoint,random.randint(self.size-3,self.size+2))
        self.AllFish.append(F)

    #this is so there is always a smaller fish
    def spawn_first(self):
        tempblock = BLOCK_SIZE/20
        newPoint = Point(random.randint(tempblock,(self.w/20)-tempblock)*20,random.randint(tempblock,(self.h/20)-tempblock)*20)
        F = Fish(newPoint,2)
        self.AllFish.append(F)

    def play_step(self, action):           
            self.frame_iteration += 1
            #print(self.frame_iteration)
            # 1. collect user input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

            # 2. move
            self._move(action)

            # 2. check if on fish and score
            fishVar = self.touchingFish()

            # 3. check if game over
            reward = 0
            game_over = False
            if self.is_collision() or fishVar == 1:
                game_over = True
                reward = -10
                return reward, game_over, self.score

            # 4. spawn fish if eaten
            if fishVar == 0:
                reward = 20
                self.spawn_fish()

            if self.size > 20:
                reward = 50
                self.score += 50
                game_over = True
                return reward, game_over, self.score
            
                


            # 5. update ui and clock
            self._update_ui()
            self.clock.tick(SPEED)
            # 6. return game over and score
            return reward, game_over, self.score

    def is_collision(self,pt = None):
        if pt is None:
            pt = self.Shifter
        # hits boundary
        if pt.x > self.w - BLOCK_SIZE or pt.x < 0 or pt.y > self.h - BLOCK_SIZE or pt.y < 0 or self.touchingFish() == 1:
            return True
        return False

    def _update_ui(self):
        self.display.fill(BLACK)

        pygame.draw.rect(self.display, GREEN, pygame.Rect(self.Shifter.x, self.Shifter.y, BLOCK_SIZE, BLOCK_SIZE))
        sizescore = font.render(str(self.size),True, WHITE)
        self.display.blit(sizescore,[self.Shifter.x +15, self.Shifter.y + 15])
        
        #moves the fish every so often
        if random.randint(0,100) < 25:
            self.move_fish()
        
        self.draw_fish()

        text = font.render("Score: " + str(self.score), True, WHITE)
        self.display.blit(text, [0, 0])
        pygame.display.flip()

    def _move(self, action):
                # [straign, right, left]
        clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]

        if np.array_equal(action,[1,0,0,0]):
            new_dir = clock_wise[0] #Right
        elif np.array_equal(action,[0,1,0,0]):
            new_dir = clock_wise[1] # Down
        elif np.array_equal(action,[0,0,1,0]):
            new_dir = clock_wise[2] #Left
        elif np.array_equal(action,[0,0,0,1]):
            new_dir = clock_wise[3] # Up

        self.direction = new_dir

        x = self.Shifter.x
        y = self.Shifter.y

        if self.direction == Direction.RIGHT:
            x += BLOCK_SIZE
        elif self.direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif self.direction == Direction.DOWN:
            y += BLOCK_SIZE
        elif self.direction == Direction.UP:
            y -= BLOCK_SIZE
            
        self.Shifter = Point(x, y)

    #0 if touching fish and bigger so gets score and size
    #1 if touching fish and smaller so restart game
    #2 if not touching fish
    def touchingFish(self):
        for F in self.AllFish:
            if F.point == self.Shifter:
                if self.size > F.size:
                    self.score += F.size
                    self.size += 1
                    self.AllFish.remove(F)
                    return 0
                else:
                    return 1
        return 2

    #all fish functions for movement and drawing
    def move_fish(self):
        rand = random.randrange(0,4)
        for F in self.AllFish:
            x = F.point.x
            y = F.point.y
            if(rand == 0):
                x += BLOCK_SIZE
            elif (rand == 1):
                y += BLOCK_SIZE
            elif (rand == 2):
                x -= BLOCK_SIZE
            else:
                y -= BLOCK_SIZE
            
            #custom if in case the fish is at a wall
            if x > self.w - BLOCK_SIZE or x < 0 or y > self.h - BLOCK_SIZE or y < 0:
                newPoint = self.hitWall(x,y)
                self.AllFish.remove(F)
                F = Fish(newPoint, F.size)
                self.AllFish.append(F)
            else:
                self.AllFish.remove(F)
                F = Fish(Point(x,y), F.size)
                self.AllFish.append(F)
            
            #This is to let the other fish eat eachother
            for F2 in self.AllFish:
                size1 = F.size
                size2 = F2.size
                if F.point == F2.point and F != F2:
                    if size1 > size2:
                        size1 += 1

                        if(F2 in self.AllFish):
                            self.AllFish.remove(F2)
                            self.spawn_fish()
                        if(F in self.AllFish):
                            self.AllFish.remove(F)
                            self.AllFish.append(Fish(F.point,size1))
                    elif size1 < size2:
                        size2 += 1

                        if(F in self.AllFish):
                            self.AllFish.remove(F)
                            self.spawn_fish()
                        if(F2 in self.AllFish):
                            self.AllFish.remove(F2)
                            self.AllFish.append(Fish(F2.point,size2))
        
    def hitWall(self, xPos, yPos):#spits out a new movement if on edge
        if xPos > self.w - (BLOCK_SIZE):
            xPos -= BLOCK_SIZE
        if xPos < 0:
            xPos += BLOCK_SIZE
        if yPos > self.h - (BLOCK_SIZE):
            yPos -= BLOCK_SIZE
        if yPos < 0:
            yPos += BLOCK_SIZE
        return Point(xPos,yPos)

    def draw_fish(self):
        for F in self.AllFish:
            pygame.draw.rect(self.display, RED, pygame.Rect(F.point.x, F.point.y, BLOCK_SIZE, BLOCK_SIZE))
            sizescore = font.render(str(F.size),True, WHITE)
            self.display.blit(sizescore,[F.point.x +15, F.point.y + 15])
        
            
if __name__ == '__main__':
    game = FishGame()
    
    while True:
        game_over, score = game.play_step()
        
        if game_over == True:
            break

    

