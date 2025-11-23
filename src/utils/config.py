"""Configuration management for Personal Loan Advisor Agent."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class LoanConfig(BaseModel):
    """Loan-specific configuration parameters."""

    # Age constraints
    min_age: int = Field(default=18, description="Minimum age for loan eligibility")
    max_age: int = Field(default=65, description="Maximum age for loan eligibility")

    # Income constraints (in AED or any currency)
    min_income: float = Field(
        default=5000.0, description="Minimum monthly income required"
    )

    # Credit score constraints
    min_credit_score: int = Field(
        default=600, description="Minimum credit score required"
    )

    # Debt-to-Income ratio
    max_dti_ratio: float = Field(
        default=0.5, description="Maximum debt-to-income ratio allowed"
    )

    # Loan amount constraints
    min_loan_amount: float = Field(default=10000.0, description="Minimum loan amount")
    max_loan_amount: float = Field(
        default=1000000.0, description="Maximum loan amount"
    )

    # Interest rate
    interest_rate_base: float = Field(
        default=0.0499, description="Base annual interest rate (4.99%)"
    )

    # Loan term constraints (in months)
    min_loan_term: int = Field(default=12, description="Minimum loan term in months")
    max_loan_term: int = Field(default=60, description="Maximum loan term in months")


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

    loan: LoanConfig = Field(default_factory=LoanConfig)
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


# Global config instance
config = Config()
