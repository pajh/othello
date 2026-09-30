"""First outcome model: a fixed multilayer perceptron over board planes.

Implements the agreed architecture in docs/first-model-design.md, bounded by
docs/first-model-task.md (stage 1 of the learning pipeline: the model only).

Input encoding version 1: binary own/opponent planes shaped ``(N, 2, 8, 8)``,
flattened in C order from dimension 1 so the own plane comes first, followed
by the opponent plane. Every sample is an **after-action** position seen
from the perspective of the player who made that action, so the same board
appears with the planes swapped depending on who moved.

Output: one score per sample in ``[0, 1]``, the sigmoid of a single logit,
interpreted as the expected outcome of the recorded continuation,
``P(win) + 0.5 * P(draw)``. A score near 0.5 does not imply a likely draw,
and the score is not a proven game value.

This module holds no training logic: no optimizer, loss, loop, target
mapping, dataset loading, checkpointing or bot behaviour. Callers own dtype
conversion (``uint8`` archives become ``float32`` tensors), device
placement, target mapping ``(outcome + 1) / 2`` and resumption state.
``MODEL_VERSION`` exists so a future checkpoint loader can reject files
whose architecture or encoding does not match this one.

Requires PyTorch (installed in the project's venv); the rules engine and
bots remain dependency-free.
"""

import torch
from torch import nn

#: Architecture and encoding identifier for checkpoints written against this
#: module. Bump only when the layer sizes or the input/output encoding change.
MODEL_VERSION = 1

_PLANES = 2
_SIZE = 8
_INPUT_FEATURES = _PLANES * _SIZE * _SIZE
_HIDDEN_1 = 256
_HIDDEN_2 = 64


class OutcomeMLP(nn.Module):
    """Fixed 128 -> 256 -> 64 -> 1 MLP scoring an after-action position.

    The constructor takes no arguments: this architecture is deliberately
    fixed so a checkpoint cannot be loaded into a differently shaped model
    by accident. All linear layers use a bias and PyTorch's default
    initialisation, giving 49,537 trainable parameters.
    """

    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(_INPUT_FEATURES, _HIDDEN_1),
            nn.ReLU(),
            nn.Linear(_HIDDEN_1, _HIDDEN_2),
            nn.ReLU(),
            nn.Linear(_HIDDEN_2, 1),
            nn.Sigmoid(),
        )

    def forward(self, boards):
        """Score a batch of positions.

        Args:
            boards: float32 tensor shaped ``(N, 2, 8, 8)`` in encoding
                version 1, own plane first, from the acting player's
                perspective.

        Returns:
            Tensor shaped ``(N,)`` with expected-outcome scores in
            ``[0, 1]``. A single sample returns shape ``(1,)``.

        Raises:
            ValueError: if *boards* is not a 4-dimensional tensor of shape
                ``(N, 2, 8, 8)``.

        The dtype and device of *boards* are used as given; nothing is cast,
        moved or loaded here.
        """
        if not torch.is_tensor(boards):
            raise ValueError('boards must be a torch.Tensor, got %s'
                             % type(boards).__name__)
        if boards.dim() != 4:
            raise ValueError('boards must have shape (N, 2, 8, 8), got rank %d with shape %s'
                             % (boards.dim(), tuple(boards.shape)))
        if tuple(boards.shape[1:]) != (_PLANES, _SIZE, _SIZE):
            raise ValueError('boards must have shape (N, 2, 8, 8), got shape %s'
                             % (tuple(boards.shape),))
        return self.network(torch.flatten(boards, 1)).squeeze(-1)
