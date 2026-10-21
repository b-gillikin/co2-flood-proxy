"""Explain calendar support without guessing which masked pixels were clouds."""

import numpy as np


def slot_reason(planned, local, companion_missing, observed):
    if planned <= 0:
        return "no_catalogued_source"
    if local < planned or companion_missing:
        return "local_files_incomplete"
    if not np.isfinite(observed) or observed <= 0:
        return "no_valid_catchment_pixels"
    return "observed"


def support_reason(reasons, encoded):
    if encoded:
        if any(reason != "observed" for reason in reasons):
            raise ValueError("Encoded representation contradicts raw slot support")
        return "encoded"
    for reason in ["local_files_incomplete", "no_catalogued_source", "no_valid_catchment_pixels"]:
        if reason in reasons:
            return reason
    return "encoder_sequence_support_loss"
