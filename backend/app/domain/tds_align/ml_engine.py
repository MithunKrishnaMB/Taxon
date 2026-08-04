# pyrefly: ignore [missing-import]
import torch
# pyrefly: ignore [missing-import]
import torch.nn as nn


class TdsAutoencoder(nn.Module):
    """Deep Learning Autoencoder for anomaly detection in tripartite tax ledgers."""

    def __init__(self, input_dim: int = 4):
        super().__init__()
        # Encoder: Compresses 4 ledger features down to 2 latent numbers
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 8),
            nn.ReLU(),
            nn.Linear(8, 2),
        )
        # Decoder: Reconstructs the 4 original features from the 2 latent numbers
        self.decoder = nn.Sequential(
            nn.Linear(2, 8),
            nn.ReLU(),
            nn.Linear(8, input_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

    @staticmethod
    def calculate_reconstruction_loss(
        features: list[float], threshold: float = 0.15
    ) -> tuple[float, bool]:
        """Returns (MSE_loss, is_anomalous). If loss > threshold, it's flagged!"""
        model = TdsAutoencoder()
        model.eval()  # Set model to evaluation mode

        with torch.no_grad():
            x = torch.tensor([features], dtype=torch.float32)
            reconstructed = model(x)
            # Calculate Mean Squared Error (MSE)
            mse_loss = float(torch.mean((x - reconstructed) ** 2).item())
            
        return mse_loss, mse_loss > threshold