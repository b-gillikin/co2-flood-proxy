"""Event-level summaries and complete training batches for applied comparisons."""

import math
import random

import numpy as np


class CompleteBatches:
    """Shuffle once per epoch; merge a final singleton, never discard examples.

    A batch can be one larger than requested. This preserves all examples and
    avoids singleton pooled batch-normalization in the native task heads.
    """

    def __init__(self, size, batch_size, seed):
        if size < 2 or batch_size < 2:
            raise ValueError("Pooled batch-normalization requires at least two examples")
        self.size, self.batch_size, self.seed = size, batch_size, seed

    def __iter__(self):
        indices = list(range(self.size))
        random.Random(self.seed).shuffle(indices)
        batches = [indices[i : i + self.batch_size] for i in range(0, self.size, self.batch_size)]
        if len(batches) > 1 and len(batches[-1]) == 1:
            batches[-2].extend(batches.pop())
        yield from batches

    def __len__(self):
        n = math.ceil(self.size / self.batch_size)
        return n - int(n > 1 and self.size % self.batch_size == 1)


def count_metrics(counts):
    """Compute metrics AFTER summing nonoverlapping confusion counts."""
    tp, fn, fp, tn = (int(counts[k]) for k in ["tp", "fn", "fp", "tn"])

    def ratio(a, b):
        return a / b if b else None

    return dict(
        tp=tp,
        fn=fn,
        fp=fp,
        tn=tn,
        support_pixels=tp + fn + fp + tn,
        iou=ratio(tp, tp + fn + fp),
        precision=ratio(tp, tp + fp),
        recall=ratio(tp, tp + fn),
        f1=ratio(2 * tp, 2 * tp + fn + fp),
    )


def paired_event_summary(left, right, draws=999, seed=42):
    """Equal-event IoU differences; pairs must be identical, undefined stay visible.

    Inputs map event ID -> IoU. Training seeds must be consolidated separately
    before calling this: repeated seeds are not independent flood events.
    """
    if set(left) != set(right):
        raise ValueError("Different event census; use an explicit matched comparison")
    if draws < 1:
        raise ValueError("Positive bootstrap draws required")
    events = sorted(left)
    valid = [
        e
        for e in events
        if left[e] is not None
        and right[e] is not None
        and np.isfinite(left[e])
        and np.isfinite(right[e])
    ]
    values = np.array([left[e] - right[e] for e in valid])
    interval = None
    if len(values) >= 2:
        rng = np.random.default_rng(seed)
        samples = values[rng.integers(0, len(values), size=(draws, len(values)))].mean(1)
        interval = np.quantile(samples, [0.025, 0.975]).tolist()
    return dict(
        events=events,
        defined_events=valid,
        undefined_events=sorted(set(events) - set(valid)),
        event_differences={e: float(v) for e, v in zip(valid, values, strict=True)},
        mean_difference=float(values.mean()) if len(values) else None,
        leave_one_event_out_means={
            e: float(np.delete(values, i).mean()) for i, e in enumerate(valid)
        }
        if len(values) > 1
        else {},
        event_bootstrap_interval=interval,
        draws=draws,
        seed=seed,
        interpretation="Exploratory paired event resampling; not seed/pixel independence or equivalence",
    )


def label_accounting(rows, available_training_chips, training_examples):
    train, valid, test = (len(rows[k]) for k in ["train", "valid", "test"])
    return dict(
        training_chips=train,
        validation_chips=valid,
        test_chips=test,
        available_training_chips=available_training_chips,
        training_label_fraction=train / available_training_chips,
        combined_selection_label_fraction=(train + valid) / (available_training_chips + valid),
        unique_selection_labels=train + valid,
        training_examples_per_epoch=training_examples,
        note="Complete labeled chips; not annotation hours. Test labels are evaluation-only.",
    )
