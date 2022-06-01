import torch
import torch.nn as nn
import torch.nn.functional as F
from math import sqrt

# https://stackoverflow.com/questions/753954/how-to-program-a-neural-network-for-chess
'''
I would like to use an artificial neural network which should then evaluate a given position. The output should be a 
numerical value. The higher the value is, the better is the position for the white player.

My approach is to build a network of 385 neurons: There are six unique chess pieces and 64 fields on the board. So for 
every field we take 6 neurons (1 for every piece). If there is a white piece, the input value is 1. If there is a black
 piece, the value is -1. And if there is no piece of that sort on that field, the value is 0. In addition to that there 
 should be 1 neuron for the player to move. If it is White's turn, the input value is 1 and if it's Black's turn, the value is -1.
'''
# neural network evaluates the state of the board
# color = 1 if white, -1 if black
# positions that ARE NOT chosen of possible moves are back propped with correct label of -1 * color
# positions that ARE chosen of possible moves are back propped with correct label of +1 * color
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()

        # lets just overfit the fuck out of this and see what it looks like
        self.conv1 = nn.Conv2d(7, 640, (3,3), padding='same')
        self.conv2 = nn.Conv2d(640, 640, (3, 3), padding='same')
        self.fc1 = nn.Linear(40960, 2048)

        self.fc2 = nn.Linear(2048, 1)

        self.init_weights()

    def init_weights(self):
        nn.init.normal_(self.conv1.weight, 0.0, 1/sqrt(5*5*self.conv1.weight.size(1)))
        nn.init.constant_(self.conv1.bias, 0.0)

        nn.init.normal_(self.conv2.weight, 0.0, 1 / sqrt(5 * 5 * self.conv2.weight.size(1)))
        nn.init.constant_(self.conv2.bias, 0.0)

        nn.init.normal_(self.fc1.weight, 0.0, 1/sqrt(385))
        nn.init.constant_(self.fc1.bias, 0.0)

        nn.init.normal_(self.fc2.weight, 0.0, 1/sqrt(1024))
        nn.init.constant_(self.fc2.bias, 0.0)

    def forward(self, x):
        x=self.conv1(x)
        #x=F.relu(x)
        x=self.conv2(x)
        #x=F.relu(x)
        x=torch.flatten(x,1)
        try:
            x = self.fc1(x)
        except(RuntimeError):
            x = torch.flatten(x)
            x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)
        return x