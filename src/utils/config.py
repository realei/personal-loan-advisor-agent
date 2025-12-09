"""Configuration management for Personal Loan Advisor Agent.

All loan regulations (DTI, LTV, rates) are configurable via environment variables.
See .env.example for all available options.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


def _env_float(key: str, default: float) -> float:
    """Get float from environment variable."""
    return float(os.getenv(key, str(default)))


def _env_int(key: str, default: int) -> int:
    """Get int from environment variable."""
    return int(os.getenv(key, str(default)))


# =============================================================================
# PERSONAL LOAN CONFIG
# =============================================================================
class PersonalLoanConfig(BaseModel):
    """Personal loan configuration - unsecured, shorter term."""

    # DTI
    max_dti_ratio: float = Field(
        default_factory=lambda: _env_float("PERSONAL_MAX_DTI", 0.50)
    )
    recommended_dti: float = Field(
        default_factory=lambda: _env_float("PERSONAL_RECOMMENDED_DTI", 0.36)
    )

    # Interest rate
    base_rate: float = Field(
        default_factory=lambda: _env_float("PERSONAL_BASE_RATE", 0.0699)
    )

    # Term (months)
    min_term: int = Field(
        default_factory=lambda: _env_int("PERSONAL_MIN_TERM", 12)
    )
    max_term: int = Field(
        default_factory=lambda: _env_int("PERSONAL_MAX_TERM", 60)
    )

    # Amount
    min_amount: float = Field(
        default_factory=lambda: _env_float("PERSONAL_MIN_AMOUNT", 5000)
    )
    max_amount: float = Field(
        default_factory=lambda: _env_float("PERSONAL_MAX_AMOUNT", 500000)
    )

    # Income
    min_income: float = Field(
        default_factory=lambda: _env_float("PERSONAL_MIN_INCOME", 5000)
    )

    # Credit
    min_credit_score: int = Field(
        default_factory=lambda: _env_int("PERSONAL_MIN_CREDIT_SCORE", 600)
    )


# =============================================================================
# MORTGAGE / HOME LOAN CONFIG
# =============================================================================
class MortgageConfig(BaseModel):
    """Mortgage configuration - secured by property, long term."""

    # DTI - stricter for mortgage
    max_dti_ratio: float = Field(
        default_factory=lambda: _env_float("MORTGAGE_MAX_DTI", 0.43)
    )
    recommended_dti: float = Field(
        default_factory=lambda: _env_float("MORTGAGE_RECOMMENDED_DTI", 0.36)
    )

    # LTV (Loan-to-Value)
    max_ltv_ratio: float = Field(
        default_factory=lambda: _env_float("MORTGAGE_MAX_LTV", 0.80)
    )
    min_down_payment: float = Field(
        default_factory=lambda: _env_float("MORTGAGE_MIN_DOWN_PAYMENT", 0.20)
    )

    # Interest rate - lower for secured
    base_rate: float = Field(
        default_factory=lambda: _env_float("MORTGAGE_BASE_RATE", 0.0449)
    )

    # Term (months) - long term
    min_term: int = Field(
        default_factory=lambda: _env_int("MORTGAGE_MIN_TERM", 120)  # 10 years
    )
    max_term: int = Field(
        default_factory=lambda: _env_int("MORTGAGE_MAX_TERM", 360)  # 30 years
    )

    # Amount - higher for property
    min_amount: float = Field(
        default_factory=lambda: _env_float("MORTGAGE_MIN_AMOUNT", 50000)
    )
    max_amount: float = Field(
        default_factory=lambda: _env_float("MORTGAGE_MAX_AMOUNT", 10000000)
    )

    # Income - higher requirements
    min_income: float = Field(
        default_factory=lambda: _env_float("MORTGAGE_MIN_INCOME", 8000)
    )

    # Credit - stricter
    min_credit_score: int = Field(
        default_factory=lambda: _env_int("MORTGAGE_MIN_CREDIT_SCORE", 620)
    )

    # Employment - longer history
    min_employment_years: float = Field(
        default_factory=lambda: _env_float("MORTGAGE_MIN_EMPLOYMENT_YEARS", 2.0)
    )

    # Age at maturity - extended for mortgage
    max_age_at_maturity: int = Field(
        default_factory=lambda: _env_int("MORTGAGE_MAX_AGE_AT_MATURITY", 70)
    )


# =============================================================================
# AUTO / CAR LOAN CONFIG
# =============================================================================
class AutoLoanConfig(BaseModel):
    """Auto loan configuration - secured by vehicle, medium term."""

    # DTI
    max_dti_ratio: float = Field(
        default_factory=lambda: _env_float("AUTO_MAX_DTI", 0.45)
    )
    recommended_dti: float = Field(
        default_factory=lambda: _env_float("AUTO_RECOMMENDED_DTI", 0.36)
    )

    # LTV - less strict than mortgage
    max_ltv_ratio: float = Field(
        default_factory=lambda: _env_float("AUTO_MAX_LTV", 0.90)
    )
    min_down_payment: float = Field(
        default_factory=lambda: _env_float("AUTO_MIN_DOWN_PAYMENT", 0.10)
    )

    # Interest rate
    base_rate: float = Field(
        default_factory=lambda: _env_float("AUTO_BASE_RATE", 0.0549)
    )

    # Term (months)
    min_term: int = Field(
        default_factory=lambda: _env_int("AUTO_MIN_TERM", 36)
    )
    max_term: int = Field(
        default_factory=lambda: _env_int("AUTO_MAX_TERM", 84)  # 7 years
    )

    # Amount
    min_amount: float = Field(
        default_factory=lambda: _env_float("AUTO_MIN_AMOUNT", 10000)
    )
    max_amount: float = Field(
        default_factory=lambda: _env_float("AUTO_MAX_AMOUNT", 500000)
    )

    # Income
    min_income: float = Field(
        default_factory=lambda: _env_float("AUTO_MIN_INCOME", 5000)
    )

    # Credit
    min_credit_score: int = Field(
        default_factory=lambda: _env_int("AUTO_MIN_CREDIT_SCORE", 600)
    )


# =============================================================================
# LEGACY LOAN CONFIG (for backward compatibility)
# =============================================================================
class LoanConfig(BaseModel):
    """Legacy loan configuration - maps to PersonalLoanConfig for compatibility."""

    # Age constraints
    min_age: int = Field(default=18, description="Minimum age for loan eligibility")
    max_age: int = Field(default=65, description="Maximum age for loan eligibility")

    # Income constraints (in AED or any currency)
    min_income: float = Field(
        default_factory=lambda: _env_float("PERSONAL_MIN_INCOME", 5000.0),
        description="Minimum monthly income required",
    )

    # Credit score constraints
    min_credit_score: int = Field(
        default_factory=lambda: _env_int("PERSONAL_MIN_CREDIT_SCORE", 600),
        description="Minimum credit score required",
    )

    # Debt-to-Income ratio
    max_dti_ratio: float = Field(
        default_factory=lambda: _env_float("PERSONAL_MAX_DTI", 0.5),
        description="Maximum debt-to-income ratio allowed",
    )

    # Loan amount constraints
    min_loan_amount: float = Field(
        default_factory=lambda: _env_float("PERSONAL_MIN_AMOUNT", 10000.0),
        description="Minimum loan amount",
    )
    max_loan_amount: float = Field(
        default_factory=lambda: _env_float("PERSONAL_MAX_AMOUNT", 1000000.0),
        description="Maximum loan amount",
    )

    # Interest rate
    interest_rate_base: float = Field(
        default_factory=lambda: _env_float("PERSONAL_BASE_RATE", 0.0499),
        description="Base annual interest rate (4.99%)",
    )

    # Loan term constraints (in months)
    min_loan_term: int = Field(
        default_factory=lambda: _env_int("PERSONAL_MIN_TERM", 12),
        description="Minimum loan term in months",
    )
    max_loan_term: int = Field(
        default_factory=lambda: _env_int("PERSONAL_MAX_TERM", 60),
        description="Maximum loan term in months",
    )


class ModelConfig(BaseModel):
    """ML model configuration."""

    model_path: Path = Field(
        default=Path("models/credit_scoring/xgboost_model.pkl"),
        description="Path to trained XGBoost model",
    )
    scaler_path: Path = Field(
        default=Path("models/credit_scoring/scaler.pkl"),
        description="Path to feature scaler",
    )
    feature_names_path: Path = Field(
        default=Path("models/credit_scoring/feature_names.pkl"),
        description="Path to feature names",
    )


class MongoDBConfig(BaseModel):
    """MongoDB configuration."""

    mongodb_uri: str = Field(
        default_factory=lambda: os.getenv(
            "MONGODB_URI", "mongodb://admin:password123@localhost:27017/"
        ),
        description="MongoDB connection URI",
    )
    database_name: str = Field(
        default_factory=lambda: os.getenv("MONGODB_DATABASE", "loan_advisor"),
        description="MongoDB database name",
    )
    session_collection: str = Field(
        default_factory=lambda: os.getenv("MONGODB_SESSION_COLLECTION", "agno_sessions"),
        description="Session collection name",
    )
    memory_collection: str = Field(
        default_factory=lambda: os.getenv("MONGODB_MEMORY_COLLECTION", "agno_memories"),
        description="Memory collection name",
    )
    metrics_collection: str = Field(
        default_factory=lambda: os.getenv("MONGODB_METRICS_COLLECTION", "agno_metrics"),
        description="Metrics collection name",
    )


class APIConfig(BaseModel):
    """API configuration."""

    openai_api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", ""),
        description="OpenAI API key",
    )
    os_security_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("OS_SECURITY_KEY"),
        description="AgentOS security key for API authentication (optional)",
    )
    deepeval_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("DEEPEVAL_API_KEY"),
        description="DeepEval API key (optional)",
    )
    agent_model: str = Field(
        default_factory=lambda: os.getenv("AGENT_MODEL", "gpt-4o-mini"),
        description="Agent model for conversation and tool calls",
    )
    deepeval_model: str = Field(
        default_factory=lambda: os.getenv("DEEPEVAL_MODEL", "gpt-4o-mini"),
        description="DeepEval model for evaluation",
    )
    temperature: float = Field(
        default_factory=lambda: float(os.getenv("TEMPERATURE", "0.7")),
        description="LLM temperature",
    )


class Config(BaseModel):
    """Main configuration class."""

    # Legacy config (backward compatible)
    loan: LoanConfig = Field(default_factory=LoanConfig)

    # Loan type specific configs
    personal_loan: PersonalLoanConfig = Field(default_factory=PersonalLoanConfig)
    mortgage: MortgageConfig = Field(default_factory=MortgageConfig)
    auto_loan: AutoLoanConfig = Field(default_factory=AutoLoanConfig)

    # Other configs
    model: ModelConfig = Field(default_factory=ModelConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    mongodb: MongoDBConfig = Field(default_factory=MongoDBConfig)

    # Project paths
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent
    )
    data_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent / "data"
    )
    models_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent / "models"
    )

    def get_loan_config(self, loan_type: str):
        """Get config for a specific loan type.

        Args:
            loan_type: 'personal', 'mortgage', or 'auto'

        Returns:
            The corresponding loan config object
        """
        configs = {
            "personal": self.personal_loan,
            "mortgage": self.mortgage,
            "auto": self.auto_loan,
        }
        loan_type = loan_type.lower()
        if loan_type not in configs:
            raise ValueError(f"Unknown loan type: {loan_type}")
        return configs[loan_type]


# Global config instance
config = Config()
