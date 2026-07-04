"""
KOVIRX AI Engine — Feature Normalizer.

Handles feature normalization and preprocessing for ML model input.
Supports StandardScaler, MinMaxScaler, and robust scaling.
"""

import logging
import numpy as np
from pathlib import Path

logger = logging.getLogger("kovirx.ai.feature_normalizer")


class FeatureNormalizer:
    """
    Feature normalization pipeline for ML model input.

    Supports:
        - Loading pre-trained sklearn scalers
        - Fallback manual normalization when sklearn is unavailable
        - Feature validation and zero-filling for missing features
    """

    def __init__(self, scaler_path: Path | None = None):
        self.scaler = None
        if scaler_path and scaler_path.exists():
            try:
                import joblib
                self.scaler = joblib.load(scaler_path)
                logger.info("Feature scaler loaded from %s", scaler_path)
            except Exception as e:
                logger.warning("Could not load scaler: %s", e)

    def normalize(self, features: np.ndarray) -> np.ndarray:
        """
        Normalize a feature array.

        Args:
            features: 2D numpy array of shape (n_samples, n_features)

        Returns:
            Normalized feature array
        """
        if self.scaler is not None:
            try:
                return self.scaler.transform(features)
            except Exception as e:
                logger.warning("Scaler transform failed, using manual normalization: %s", e)

        return self._manual_normalize(features)

    @staticmethod
    def _manual_normalize(features: np.ndarray) -> np.ndarray:
        """Manual z-score normalization as fallback."""
        means = np.mean(features, axis=0)
        stds = np.std(features, axis=0)
        stds[stds == 0] = 1.0  # Avoid division by zero
        return (features - means) / stds

    @staticmethod
    def validate_and_fill(
        feature_dict: dict[str, float],
        expected_features: list[str],
    ) -> list[float]:
        """
        Validate feature dict against expected schema and fill missing values.

        Args:
            feature_dict: Dict of feature_name → value
            expected_features: Ordered list of expected feature names

        Returns:
            Ordered list of feature values
        """
        return [float(feature_dict.get(name, 0.0)) for name in expected_features]
