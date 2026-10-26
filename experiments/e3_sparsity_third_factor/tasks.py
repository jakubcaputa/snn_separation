"""
E3 — dane: MNIST z plików idx (bez torchvision), Split-MNIST class-incremental.

Domyślny katalog z danymi to kopia MNIST w repo `snn_stdp_vs_surrogate_gradient`
(tylko do odczytu; to repo nie jest modyfikowane). Nadpisanie: zmienna
środowiskowa E3_MNIST_DIR albo argument `mnist_dir`.
"""
from __future__ import annotations

import os

import numpy as np

DEFAULT_MNIST_DIR = os.environ.get(
    'E3_MNIST_DIR',
    '/net/tscratch/people/plgjakubcaputa/snn_stdp_vs_surrogate_gradient/data/MNIST/raw')

TASKS = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]


def _read_idx(path: str) -> np.ndarray:
    with open(path, 'rb') as f:
        data = f.read()
    ndim = data[3]
    dims = [int.from_bytes(data[4 + 4 * i: 8 + 4 * i], 'big') for i in range(ndim)]
    return np.frombuffer(data, np.uint8, offset=4 + 4 * ndim).reshape(dims)


# Średnia suma jasności obrazu MNIST (zbiór treningowy) — cel normalizacji.
MEAN_TOTAL = 103.0


def normalize_images(X: np.ndarray) -> np.ndarray:
    """Normalizacja dzieląca: każdy obraz przeskalowany do tej samej sumy jasności.

    Po co (E3.0, README): przy samym hamowaniu tonicznym (jeden próg dla wszystkich
    obrazów) odsetek aktywnych neuronów zależy od „masy” cyfry — przy średnim f = 5%
    cyfra 1 aktywuje ~0.1% neuronów, a cyfra 0 ~18%, i kod traci większość informacji.
    W dg_core wzorce wejściowe mają z konstrukcji stałą liczbę aktywnych włókien;
    tu odpowiada temu normalizacja wejścia (biologicznie: normalizacja w korze
    śródwęchowej, jak w płatach czułkowych muszki przed komórkami Kenyona)."""
    s = X.sum(1, keepdims=True)
    return (X / np.maximum(s, 1e-6) * MEAN_TOTAL).astype(np.float32)


def load_mnist(mnist_dir: str = DEFAULT_MNIST_DIR, normalize: bool = True):
    """Zwraca (X_train [60000,784] float32, y_train, X_test, y_test).
    normalize=True (domyślnie): normalize_images — patrz wyżej."""
    def rd(name):
        return _read_idx(os.path.join(mnist_dir, name))
    Xtr = rd('train-images-idx3-ubyte').reshape(-1, 784).astype(np.float32) / 255.0
    ytr = rd('train-labels-idx1-ubyte').astype(np.int64)
    Xte = rd('t10k-images-idx3-ubyte').reshape(-1, 784).astype(np.float32) / 255.0
    yte = rd('t10k-labels-idx1-ubyte').astype(np.int64)
    if normalize:
        Xtr, Xte = normalize_images(Xtr), normalize_images(Xte)
    return Xtr, ytr, Xte, yte


def calib_indices(n_train: int, n: int = 1000, seed: int = 0) -> np.ndarray:
    """Obrazy kalibracyjne K(f): losowe obrazy treningowe (nigdy testowe)."""
    return np.random.default_rng(777 + seed).choice(n_train, n, replace=False)


def task_indices(y: np.ndarray, task: tuple) -> np.ndarray:
    return np.where(np.isin(y, task))[0]


def task_stream(y_train: np.ndarray, order_seed: int, epochs_per_task: int = 1):
    """Kolejne zadania Split-MNIST: lista (task_id, indeksy w losowej kolejności)."""
    rng = np.random.default_rng(order_seed)
    out = []
    for k, task in enumerate(TASKS):
        idx = task_indices(y_train, task)
        seq = np.concatenate([rng.permutation(idx) for _ in range(epochs_per_task)])
        out.append((k, seq))
    return out
