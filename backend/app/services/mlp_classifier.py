"""
Configurable Multi-Layer Perceptron (MLP) Classifier for Static Hand Gestures.

Architecture (default):
- Input: 63 normalized coordinates (21 landmarks x 3D)
- Hidden Layer 1: Dense(128), ReLU, Dropout(0.25)
- Hidden Layer 2: Dense(64), ReLU, Dropout(0.20)
- Output: Softmax(num_classes)

Vectorized NumPy implementation for deterministic training and ultra-fast (<0.1ms) inference.
"""

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

logger = logging.getLogger(__name__)


class MLPClassifierModel:
    """
    Lightweight, configurable Multi-Layer Perceptron neural network.
    """

    def __init__(
        self,
        input_dim: int = 63,
        hidden_layers: Optional[List[int]] = None,
        dropout_rates: Optional[List[float]] = None,
        num_classes: int = 2,
        class_mapping: Optional[Dict[str, int]] = None,
        seed: int = 42,
    ):
        """
        Initialize network parameters.

        Args:
            input_dim: Number of input features (default: 63).
            hidden_layers: Hidden layer sizes (default: [128, 64]).
            dropout_rates: Dropout probabilities per hidden layer (default: [0.25, 0.20]).
            num_classes: Number of gesture output classes.
            class_mapping: Mapping of gesture_id -> class index.
            seed: Random seed for reproducible initialization.
        """
        self.input_dim = input_dim
        self.hidden_layers = hidden_layers or [128, 64]
        self.dropout_rates = dropout_rates or [0.25, 0.20]
        self.num_classes = max(2, num_classes)
        self.class_mapping = class_mapping or {}
        self.reverse_class_mapping: Dict[int, str] = {v: k for k, v in self.class_mapping.items()}

        self.rng = np.random.RandomState(seed)

        # Build layer dimensions: [63, 128, 64, num_classes]
        self.layer_dims = [self.input_dim] + self.hidden_layers + [self.num_classes]

        # Weights & Biases
        self.weights: List[np.ndarray] = []
        self.biases: List[np.ndarray] = []

        # Adam optimizer state
        self.m_w: List[np.ndarray] = []
        self.v_w: List[np.ndarray] = []
        self.m_b: List[np.ndarray] = []
        self.v_b: List[np.ndarray] = []
        self.t: int = 0

        self._init_weights()

    def _init_weights(self) -> None:
        """He / Kaiming normal initialization for ReLU activations."""
        self.weights.clear()
        self.biases.clear()
        self.m_w.clear()
        self.v_w.clear()
        self.m_b.clear()
        self.v_b.clear()
        self.t = 0

        for i in range(len(self.layer_dims) - 1):
            fan_in = self.layer_dims[i]
            fan_out = self.layer_dims[i + 1]

            # He normal std = sqrt(2 / fan_in)
            std = math.sqrt(2.0 / fan_in)
            w = self.rng.randn(fan_in, fan_out).astype(np.float32) * std
            b = np.zeros(fan_out, dtype=np.float32)

            self.weights.append(w)
            self.biases.append(b)

            # Adam moments
            self.m_w.append(np.zeros_like(w))
            self.v_w.append(np.zeros_like(w))
            self.m_b.append(np.zeros_like(b))
            self.v_b.append(np.zeros_like(b))

    @staticmethod
    def _relu(z: np.ndarray) -> np.ndarray:
        return np.maximum(0.0, z)

    @staticmethod
    def _relu_derivative(z: np.ndarray) -> np.ndarray:
        return (z > 0.0).astype(np.float32)

    @staticmethod
    def _softmax(z: np.ndarray) -> np.ndarray:
        """Numerically stable softmax."""
        if z.ndim == 1:
            z_shifted = z - np.max(z)
            exp_z = np.exp(z_shifted)
            return exp_z / np.sum(exp_z)
        z_shifted = z - np.max(z, axis=1, keepdims=True)
        exp_z = np.exp(z_shifted)
        return exp_z / np.sum(exp_z, axis=1, keepdims=True)

    def forward(
        self, X: np.ndarray, training: bool = False
    ) -> Tuple[np.ndarray, List[np.ndarray], List[np.ndarray], List[np.ndarray]]:
        """
        Forward propagation.

        Returns:
            (probabilities, activations_list, pre_activations_list, dropout_masks_list)
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        activations = [X]
        pre_activations = []
        dropout_masks = []

        curr = X
        num_layers = len(self.weights)

        for l in range(num_layers):
            z = np.dot(curr, self.weights[l]) + self.biases[l]
            pre_activations.append(z)

            if l == num_layers - 1:
                # Output layer: Softmax
                a = self._softmax(z)
                dropout_masks.append(np.ones_like(a))
            else:
                # Hidden layers: ReLU + Inverted Dropout
                a = self._relu(z)
                drop_rate = self.dropout_rates[l] if l < len(self.dropout_rates) else 0.0

                if training and drop_rate > 0.0:
                    keep_prob = 1.0 - drop_rate
                    mask = (self.rng.rand(*a.shape) < keep_prob).astype(np.float32) / keep_prob
                    a = a * mask
                    dropout_masks.append(mask)
                else:
                    dropout_masks.append(np.ones_like(a))

            activations.append(a)
            curr = a

        return curr, activations, pre_activations, dropout_masks

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Compute class probabilities in evaluation mode."""
        probs, _, _, _ = self.forward(X, training=False)
        return probs

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Compute predicted class indices in evaluation mode."""
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)

    def compute_loss_and_acc(
        self, X: np.ndarray, y: np.ndarray
    ) -> Tuple[float, float]:
        """Compute categorical cross-entropy loss and accuracy."""
        n_samples = len(y)
        if n_samples == 0:
            return 0.0, 0.0

        probs = self.predict_proba(X)
        preds = np.argmax(probs, axis=1)
        acc = float(np.mean(preds == y))

        # Cross entropy loss with epsilon clipping
        eps = 1e-12
        probs_clipped = np.clip(probs, eps, 1.0 - eps)
        loss = -float(np.mean(np.log(probs_clipped[np.arange(n_samples), y])))

        return loss, acc

    def train_epoch(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        batch_size: int = 32,
        lr: float = 0.001,
        weight_decay: float = 1e-4,
    ) -> Tuple[float, float]:
        """
        Train network for one epoch using mini-batch Adam optimization.
        Returns (epoch_loss, epoch_accuracy).
        """
        n_samples = len(X_train)
        indices = np.arange(n_samples)
        self.rng.shuffle(indices)

        running_loss = 0.0
        correct_predictions = 0

        for start_idx in range(0, n_samples, batch_size):
            batch_indices = indices[start_idx : start_idx + batch_size]
            X_b = X_train[batch_indices]
            y_b = y_train[batch_indices]
            b_size = len(y_b)

            # 1. Forward Pass
            probs, acts, pre_acts, masks = self.forward(X_b, training=True)

            # Accumulate loss & acc
            preds = np.argmax(probs, axis=1)
            correct_predictions += int(np.sum(preds == y_b))
            eps = 1e-12
            running_loss += -float(np.sum(np.log(np.clip(probs[np.arange(b_size), y_b], eps, 1.0 - eps))))

            # 2. Backward Pass
            # Derivative of Cross-Entropy w.r.t. Softmax input: (p - y_onehot)
            y_onehot = np.zeros_like(probs)
            y_onehot[np.arange(b_size), y_b] = 1.0
            delta = (probs - y_onehot) / b_size

            num_layers = len(self.weights)
            grads_w = []
            grads_b = []

            for l in reversed(range(num_layers)):
                a_prev = acts[l]
                gw = np.dot(a_prev.T, delta) + weight_decay * self.weights[l]
                gb = np.sum(delta, axis=0)

                grads_w.insert(0, gw)
                grads_b.insert(0, gb)

                if l > 0:
                    delta = np.dot(delta, self.weights[l].T)
                    # Backprop through dropout
                    delta = delta * masks[l - 1]
                    # Backprop through ReLU
                    delta = delta * self._relu_derivative(pre_acts[l - 1])

            # 3. Adam Optimizer Update
            self.t += 1
            beta1 = 0.9
            beta2 = 0.999
            eps_adam = 1e-8

            for l in range(num_layers):
                # Update weights
                self.m_w[l] = beta1 * self.m_w[l] + (1 - beta1) * grads_w[l]
                self.v_w[l] = beta2 * self.v_w[l] + (1 - beta2) * (grads_w[l] ** 2)
                m_hat_w = self.m_w[l] / (1 - beta1 ** self.t)
                v_hat_w = self.v_w[l] / (1 - beta2 ** self.t)
                self.weights[l] -= lr * m_hat_w / (np.sqrt(v_hat_w) + eps_adam)

                # Update biases
                self.m_b[l] = beta1 * self.m_b[l] + (1 - beta1) * grads_b[l]
                self.v_b[l] = beta2 * self.v_b[l] + (1 - beta2) * (grads_b[l] ** 2)
                m_hat_b = self.m_b[l] / (1 - beta1 ** self.t)
                v_hat_b = self.v_b[l] / (1 - beta2 ** self.t)
                self.biases[l] -= lr * m_hat_b / (np.sqrt(v_hat_b) + eps_adam)

        epoch_loss = running_loss / n_samples
        epoch_acc = correct_predictions / n_samples
        return epoch_loss, epoch_acc

    def save(self, filepath: Union[str, Path]) -> None:
        """Save model parameters and architecture to .npz file."""
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)

        arrays_to_save: Dict[str, Any] = {
            f"w_{i}": w for i, w in enumerate(self.weights)
        }
        for i, b in enumerate(self.biases):
            arrays_to_save[f"b_{i}"] = b

        config_dict = {
            "input_dim": self.input_dim,
            "hidden_layers": self.hidden_layers,
            "dropout_rates": self.dropout_rates,
            "num_classes": self.num_classes,
            "class_mapping": self.class_mapping,
        }
        arrays_to_save["config_json"] = np.array([json.dumps(config_dict)], dtype=object)

        np.savez_compressed(p, **arrays_to_save)
        logger.info("Saved MLP model to %s", p)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "MLPClassifierModel":
        """Load model from .npz file."""
        p = Path(filepath)
        if not p.exists():
            raise FileNotFoundError(f"Model file not found: {p}")

        data = np.load(p, allow_pickle=True)
        config_dict = json.loads(str(data["config_json"][0]))

        model = cls(
            input_dim=config_dict["input_dim"],
            hidden_layers=config_dict["hidden_layers"],
            dropout_rates=config_dict["dropout_rates"],
            num_classes=config_dict["num_classes"],
            class_mapping=config_dict["class_mapping"],
        )

        num_layers = len(model.layer_dims) - 1
        model.weights = [data[f"w_{i}"] for i in range(num_layers)]
        model.biases = [data[f"b_{i}"] for i in range(num_layers)]

        return model
