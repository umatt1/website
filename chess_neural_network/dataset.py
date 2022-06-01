import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
try:
    from chess_neural_network.utils import create_dataframe, convert_to_array
except(ModuleNotFoundError):
    from utils import create_dataframe, convert_to_array

class ChessDataset(Dataset):
    """Dataset class for chess."""
    id = "blunder_master6969"
    id = "GregorySteven"
    def __init__(self, id=id, months=12, split="train"):
        super().__init__()

        # Load in all the data we need

        df = create_dataframe(id, months)
        self.df = df[df["split"] == split].reset_index()
        self.df = df.reset_index()
        self.X = self.df['X']
        self.y = self.df['y']

    def __len__(self):
        """Return size of dataset."""
        return len(self.X)

    def __getitem__(self, idx):
        """Return (image, label) pair at index `idx` of dataset."""
        # this is where we need to convert to something useable
        board_map = convert_to_array(self.X[idx])
        return torch.tensor(board_map).float(), torch.tensor(self.y[idx])
        #return torch.from_numpy(self.X[idx]), torch.tensor(self.y[idx])

