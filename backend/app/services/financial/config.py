"""
Financial Services Configuration

Controls whether to use mock data or real data sources.
"""
import os
from enum import Enum


class DataMode(str, Enum):
    """Data source mode"""
    REAL = "real"  # Use real data sources (APIs, databases)
    MOCK = "mock"  # Use mock data for demonstration
    ERROR = "error"  # Raise NotImplementedError


# Global configuration
# In production, this should be set to REAL or ERROR
# In development/demo, can be set to MOCK
FINANCIAL_DATA_MODE = DataMode(os.getenv("FINANCIAL_DATA_MODE", "ERROR"))


class FinancialServiceNotImplementedError(NotImplementedError):
    """Raised when a financial service feature is not yet implemented"""

    def __init__(self, service_name: str, feature_name: str):
        self.service_name = service_name
        self.feature_name = feature_name
        super().__init__(
            f"Financial service '{service_name}' feature '{feature_name}' is not yet implemented. "
            f"This requires integration with real data sources (APIs, databases). "
            f"To use mock data for demonstration, set FINANCIAL_DATA_MODE=mock"
        )


def check_data_mode_or_raise(service_name: str, feature_name: str) -> bool:
    """
    Check if mock data is allowed, otherwise raise error.

    Returns:
        True if mock data should be used

    Raises:
        FinancialServiceNotImplementedError if mode is ERROR
    """
    if FINANCIAL_DATA_MODE == DataMode.ERROR:
        raise FinancialServiceNotImplementedError(service_name, feature_name)

    return FINANCIAL_DATA_MODE == DataMode.MOCK
