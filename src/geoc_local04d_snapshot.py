"""Frozen exact Local04D functions from GeoC fe056a759790e5e4cf5d1d62dec323851625b121.
No GeoC runtime dependency. Original bodies retained; provenance in bridge design.
"""
from typing import Sequence
import numpy as np
from sklearn.linear_model import Ridge

def haversine_distance_matrix(
    latitude_deg: Sequence[float],
    longitude_deg: Sequence[float],
) -> np.ndarray:
    """Return the full great-circle distance matrix in kilometres."""

    lat = np.radians(np.asarray(latitude_deg, dtype=float))
    lon = np.radians(np.asarray(longitude_deg, dtype=float))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2
    )
    a = np.clip(a, 0.0, 1.0)
    return 6371.0088 * 2.0 * np.arcsin(np.sqrt(a))

def _nearest_distance(
    matrix: np.ndarray,
    query_position: int,
    reference_positions: Sequence[int],
    *,
    exclude_self: bool,
) -> float:
    refs = [
        int(position)
        for position in reference_positions
        if not (exclude_self and int(position) == int(query_position))
    ]
    if not refs:
        return np.nan
    values = np.asarray(matrix[int(query_position), refs], dtype=float)
    values = values[np.isfinite(values)]
    return float(np.min(values)) if len(values) else np.nan

def normalized_distance_matrix(
    matrix: np.ndarray,
    *,
    reference_positions: Sequence[int],
) -> tuple[np.ndarray, float]:
    """Scale a distance matrix by the median leave-one-out nearest reference distance."""

    reference = list(map(int, reference_positions))
    nearest: list[float] = []
    for position in reference:
        value = _nearest_distance(matrix, position, reference, exclude_self=True)
        if np.isfinite(value) and value > 0:
            nearest.append(float(value))
    if not nearest:
        raise ValueError("Cannot normalize a distance matrix without positive LOO distances.")
    scale = float(np.median(nearest))
    return np.asarray(matrix, dtype=float) / scale, scale

def predict_weighted_local_ridge(
    x: np.ndarray,
    distance_matrix: np.ndarray,
    y: np.ndarray,
    observed_positions: Sequence[int],
    query_positions: Sequence[int],
    *,
    k: int,
    alpha: float,
    distance_power: float,
) -> np.ndarray:
    """Fit one inverse-distance weighted Ridge model per query parcel."""

    observed = np.asarray(list(map(int, observed_positions)), dtype=int)
    query = list(map(int, query_positions))
    if len(observed) < 3:
        raise ValueError("Local Ridge requires at least three observed parcels.")

    result: list[float] = []
    for position in query:
        distances = np.asarray(distance_matrix[position, observed], dtype=float)
        finite = np.isfinite(distances)
        candidates = observed[finite]
        candidate_distances = distances[finite]
        if len(candidates) < 3:
            result.append(float(np.mean(y[observed])))
            continue

        order = np.argsort(candidate_distances)
        take = order[: max(3, min(int(k), len(order)))]
        local_positions = candidates[take]
        local_distances = candidate_distances[take]
        power = max(float(distance_power), 0.0)
        if power == 0:
            weights = np.ones(len(local_positions), dtype=float)
        else:
            weights = 1.0 / np.power(local_distances + 1.0e-6, power)

        model = Ridge(alpha=float(alpha))
        model.fit(
            np.asarray(x, dtype=float)[local_positions],
            np.asarray(y, dtype=float)[local_positions],
            sample_weight=weights,
        )
        result.append(float(model.predict(np.asarray(x, dtype=float)[[position]])[0]))
    return np.asarray(result, dtype=float)

