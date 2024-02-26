import torch
import random
import numpy as np
from FishGrow import FishGame, Direction, Point, Fish
from collections import deque
from model import Linear_QNet, QTrainer
from helper import plot

MAX_MEMORY = 100_000
BATCH_SIZE = 250
LR = 0.0005
TRAIN = True
MODELPATH = "./model/model.pth"

class Agent:

    def __init__(self):
        self.n_games = 0
        self.epsilon = 0 #control randomness
        self.gamma = 0.99998 # discount rate
        self.memory = deque(maxlen=MAX_MEMORY) #popleft() if it fills
        if TRAIN:
            self.model = Linear_QNet(12, 512,256, 4)
            self.trainer = QTrainer(self.model, lr=LR, gamma = self.gamma)
        else:
            self.model = Linear_QNet(12,512,256,4)
            self.model.load_state_dict(torch.load(MODELPATH))
            self.model.eval()
            #self.model.eval()


    def get_state(self, game):
        head = game.Shifter
        smallestfish = 0
        point_l = Point(head.x - 20, head.y)
        point_r = Point(head.x + 20, head.y)
        point_u = Point(head.x, head.y - 20)
        point_d = Point(head.x, head.y + 20)

        Fishy = Fish(Point(0,0),0)

        fish_l = False
        fish_r = False
        fish_u = False
        fish_d = False

        fish_l_bigger = False
        fish_r_bigger = False
        fish_u_bigger = False
        fish_d_bigger = False


        #gets wheater or not there is a fish up, down, left or right and if its bigger or not
        for F in game.AllFish:
            #gets if there are fish above left right or down
            if F.size < game.size:
                if F.size > smallestfish:
                    smallestfish = F.size
                    Fishy = F

            if Point(head.x-20,head.y) == F.point:               
                if F.size >= game.size:
                    fish_l_bigger = True
                else:
                    fish_l = True
            if Point(head.x+20, head.y) == F.point:      
                if F.size >= game.size:
                    fish_r_bigger = True
                else:
                    fish_r = True
            if Point(head.x,head.y-20) == F.point:               
                if F.size >= game.size:
                    fish_u_bigger = True
                else:
                    fish_u = True
            if Point(head.x,head.y+20) == F.point:                
                if F.size >= game.size:
                    fish_d_bigger = True
                else:
                    fish_d = True

        state = [
            # Danger up down left right
            (game.is_collision(point_l) or fish_l_bigger), 
            (game.is_collision(point_r) or fish_r_bigger), 
            (game.is_collision(point_u) or fish_u_bigger), 
            (game.is_collision(point_d) or fish_d_bigger),

            #edible fish directly up down left or right
            fish_l,
            fish_r,
            fish_u,
            fish_d,

            #if there are fish above or below anywhere
            Fishy.point.x < head.x, #fish left
            Fishy.point.x > head.x, #fish right
            Fishy.point.y < head.y, #fish up
            Fishy.point.y > head.y #fish down
            ]

        return np.array(state, dtype=int)
        

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done)) # popleft if filled

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE) # list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        final_move = [0,0,0,0]
        if TRAIN:
            # random moves: tradeoff exploration / exploitation
            self.epsilon = 90 - (self.n_games/10)
            if self.epsilon < 10:
                self.epsilon = 10
            if random.randint(0, 100) < self.epsilon:
                move = random.randint(0, 3)
                final_move[move] = 1
            else:
                state0 = torch.tensor(state, dtype=torch.float)
                prediction = self.model(state0)
                move = torch.argmax(prediction).item()
                final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move

def train():
    plot_scores=[]
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = FishGame()
    while True:
        # get old state
        state_old = agent.get_state(game)

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward, done, score = game.play_step(final_move)
        state_new = agent.get_state(game)

        if TRAIN:
            # train short memory
            agent.train_short_memory(state_old, final_move, reward, state_new, done)

            # remember
            agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            #train long memory and plot results
            game.reset()
            agent.n_games += 1
            if TRAIN:
                agent.train_long_memory()
                if score > record:
                    record = score
                    agent.model.save()
            else:
                if score > record:
                    record = score

            print('Game', agent.n_games, 'Score',score, 'Record: ',record)

            #plotting
            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)



if __name__ == '__main__':
    train()