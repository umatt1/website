try:
    from chess_neural_network.network import Net
    from chess_neural_network.dataset import ChessDataset
except(ModuleNotFoundError):
    from network import Net
    from dataset import ChessDataset
import torch
from torch.utils.data import Dataset, DataLoader
from copy import deepcopy
from matplotlib.pyplot import plot, ion, show
ion()

def train(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    model.train()
    for batch, (X, y) in enumerate(dataloader):
        # Compute prediction error
        pred = model(X)
        loss = loss_fn(pred, y)

        # Backpropagation
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if batch % 100 == 0:
            loss, current = loss.item(), batch * len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")
    return loss.item()


def test(dataloader, model, loss_fn):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    model.eval()
    test_loss, correct = 0, 0
    with torch.no_grad():
        for X, y in dataloader:
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()
    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")
    return test_loss

def main():
    model = Net()

    criterion = torch.nn.L1Loss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    print("making model")
    train_dataset = ChessDataset(id="blunder_master6969", months=12, split="train")
    test_dataset = ChessDataset(id="blunder_master6969", months=12, split="test")
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=True)


    patience = 10
    epochs_since_last_improved = 0
    t = 0
    best_loss = 500
    model_params = deepcopy(model.state_dict())
    train_losses = []
    test_losses = []
    while epochs_since_last_improved < patience:
        print(f"Epoch {t + 1}\n-------------------------------")
        train_loss = train(train_loader, model, criterion, optimizer)
        test_loss = test(test_loader, model, criterion)
        if test_loss < best_loss:
            epochs_since_last_improved = 0
            model_params = deepcopy(model.state_dict())
            best_loss = test_loss
        else:
            epochs_since_last_improved += 1
        test_losses.append(test_loss)
        train_losses.append(train_loss)
        plot(train_losses)
        plot(test_losses)
        show()

        t+=1

    print("Done!")
    model_path = "saved_models/model.txt"
    torch.save(model_params, model_path)


if __name__ == "__main__":
    main()


