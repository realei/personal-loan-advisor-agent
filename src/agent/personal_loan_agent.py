"""Personal Loan Advisor Agent - Main agent implementation using Agno.

This agent helps customers with:
1. Loan eligibility assessment
2. Loan payment calculations
3. Personalized loan recommendations
"""

from typing import Optional

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.tools.loan_eligibility import LoanEligibilityTool, ApplicantInfo
from src.tools.loan_calculator import LoanCalculatorTool, LoanRequest
from src.utils.config import config
from src.utils.memory import ConversationMemory
from src.utils.logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class PersonalLoanAgent:
    """Personal Loan Advisor Agent powered by Agno and OpenAI."""

    def __init__(
        self,
        model: str = "gpt-4",
        temperature: float = 0.7,
        debug_mode: bool = False,
        memory: Optional[ConversationMemory] = None,
    ):
        """Initialize the Personal Loan Agent.

        Args:
            model: OpenAI model to use (default: gpt-4)
            temperature: LLM temperature for responses (default: 0.7)
            debug_mode: Enable debug logging (default: False)
            memory: ConversationMemory instance for multi-user support (optional)
        """
        self.memory = memory
        self.eligibility_tool = LoanEligibilityTool(
            min_age=config.loan.min_age,
            max_age=config.loan.max_age,
            min_monthly_income=config.loan.min_income,
            min_credit_score=config.loan.min_credit_score,
            max_dti_ratio=config.loan.max_dti_ratio,
            min_employment_length=1.0,
            max_loan_amount=config.loan.max_loan_amount,
        )

        self.calculator_tool = LoanCalculatorTool(max_dti_ratio=config.loan.max_dti_ratio)

        # Configure Agno agent
        self.agent = Agent(
            name="Personal Loan Advisor",
            model=OpenAIChat(id=model, temperature=temperature),
            tools=[
                self.check_eligibility,
                self.calculate_loan_payment,
                self.generate_payment_schedule,
                self.check_affordability,
                self.compare_loan_terms,
                self.calculate_max_affordable_loan,
            ],
            instructions=self._get_system_instructions(),
            markdown=True,
            debug_mode=debug_mode,
        )

    def _get_system_instructions(self) -> list[str]:
        """Get system instructions for the agent."""
        return [
            "You are a helpful and professional Personal Loan Advisor.",
            "Your goal is to help customers understand their loan options and make informed decisions.",
            "",
            "## Your Capabilities:",
            "1. Check loan eligibility based on customer profile",
            "2. Calculate monthly payments and total costs",
            "3. Generate detailed amortization schedules",
            "4. Assess loan affordability",
            "5. Compare different loan term options",
            "6. Calculate maximum affordable loan amount",
            "",
            "## Guidelines:",
            "- Always be friendly, clear, and professional",
            "- Explain financial terms in simple language",
            "- Provide specific numbers and calculations",
            "- Warn about potential risks (high DTI, unaffordable loans)",
            "- Suggest alternatives when loans are not affordable",
            "- Never make guarantees about loan approval",
            "- Always mention that final approval depends on full application review",
            "",
            "## IMPORTANT: Information Extraction",
            "- ALWAYS extract information from the user's message first",
            "- If user mentions age, income, credit score, etc., USE THAT INFORMATION immediately",
            "- DO NOT ask for information that the user has already provided",
            "- For missing non-critical info, use reasonable defaults:",
            "  * monthly_debt_obligations: assume 0 if not mentioned",
            "  * has_existing_loans: assume False if not mentioned",
            "  * previous_defaults: assume False if not mentioned",
            "- Only ask for missing CRITICAL information (age, income, credit score, loan amount, term)",
            "",
            "## When customers ask about loans:",
            "1. **Extract all information from their message** (age, income, credit score, employment, loan amount, term)",
            "2. **If you have enough information, IMMEDIATELY call the appropriate tool**",
            "3. Only ask follow-up questions if critical information is truly missing",
            "4. Provide clear recommendations based on tool results",
            "",
            "## Examples of Good Behavior:",
            "User: \"I'm 35, earn $10k/month, credit score 720, work full-time 5 years, want $50k for 36 months\"",
            "You: [IMMEDIATELY call check_eligibility tool with extracted data]",
            "",
            "User: \"Calculate payment for $50k at 5% for 36 months\"",
            "You: [IMMEDIATELY call calculate_loan_payment tool]",
            "",
            "## Response Style:",
            "- Use bullet points for clarity",
            "- Include specific dollar amounts",
            "- Highlight important warnings in bold",
            "- End with next steps or recommendations",
        ]

    def check_eligibility(
        self,
        age: int,
        monthly_income: float,
        credit_score: int,
        employment_status: str,
        employment_length_years: float,
        requested_loan_amount: float,
        loan_term_months: int,
        monthly_debt_obligations: float = 0.0,
        has_existing_loans: bool = False,
        previous_defaults: bool = False,
    ) -> str:
        """Check if customer is eligible for a loan.

        Args:
            age: Customer age
            monthly_income: Monthly income in local currency
            credit_score: Credit score (300-850)
            employment_status: One of: full_time, part_time, self_employed, unemployed, retired
            employment_length_years: Years at current employment
            monthly_debt_obligations: Total monthly debt payments
            requested_loan_amount: Desired loan amount
            loan_term_months: Desired loan term in months
            has_existing_loans: Whether customer has other active loans
            previous_defaults: Whether customer has previous loan defaults

        Returns:
            Eligibility assessment result
        """
        try:
            # Map employment status string to enum
            from src.tools.loan_eligibility import EmploymentStatus

            emp_status_map = {
                "full_time": EmploymentStatus.FULL_TIME,
                "part_time": EmploymentStatus.PART_TIME,
                "self_employed": EmploymentStatus.SELF_EMPLOYED,
                "unemployed": EmploymentStatus.UNEMPLOYED,
                "retired": EmploymentStatus.RETIRED,
            }
            emp_status = emp_status_map.get(
                employment_status.lower(), EmploymentStatus.FULL_TIME
            )

            applicant = ApplicantInfo(
                age=age,
                monthly_income=monthly_income,
                credit_score=credit_score,
                employment_status=emp_status,
                employment_length_years=employment_length_years,
                monthly_debt_obligations=monthly_debt_obligations,
                requested_loan_amount=requested_loan_amount,
                loan_term_months=loan_term_months,
                has_existing_loans=has_existing_loans,
                previous_defaults=previous_defaults,
            )

            result = self.eligibility_tool.check_eligibility(applicant)

            # Format response
            response = f"## Loan Eligibility Assessment\n\n"
            response += f"**Status**: {result.status.value.upper()}\n"
            response += f"**Eligible**: {'✅ Yes' if result.eligible else '❌ No'}\n"
            response += f"**Eligibility Score**: {result.score:.1f}/100\n\n"

            if result.reasons:
                response += "### Assessment Details:\n"
                for reason in result.reasons:
                    response += f"- {reason}\n"
                response += "\n"

            if result.recommendations:
                response += "### Recommendations:\n"
                for rec in result.recommendations:
                    response += f"- {rec}\n"

            return response

        except Exception as e:
            return f"Error checking eligibility: {str(e)}"

    def calculate_loan_payment(
        self,
        loan_amount: float,
        annual_interest_rate: float,
        loan_term_months: int,
    ) -> str:
        """Calculate monthly loan payment and total costs.

        Args:
            loan_amount: Principal loan amount
            annual_interest_rate: Annual interest rate (e.g., 0.0499 for 4.99%)
            loan_term_months: Loan term in months

        Returns:
            Payment calculation results
        """
        try:
            loan_request = LoanRequest(
                loan_amount=loan_amount,
                annual_interest_rate=annual_interest_rate,
                loan_term_months=loan_term_months,
            )

            calc = self.calculator_tool.calculate_monthly_payment(loan_request)

            response = f"## Loan Payment Calculation\n\n"
            response += f"**Loan Amount**: ${calc.total_principal:,.2f}\n"
            response += f"**Interest Rate**: {calc.annual_interest_rate*100:.2f}% per year\n"
            response += f"**Loan Term**: {calc.loan_term_months} months ({calc.loan_term_months/12:.1f} years)\n\n"
            response += f"### Monthly Payment: ${calc.monthly_payment:,.2f}\n\n"
            response += f"**Total Payment**: ${calc.total_payment:,.2f}\n"
            response += f"**Total Interest**: ${calc.total_interest:,.2f}\n"
            response += f"**Interest as % of Principal**: {(calc.total_interest/calc.total_principal)*100:.1f}%\n"

            return response

        except Exception as e:
            return f"Error calculating payment: {str(e)}"

    def generate_payment_schedule(
        self,
        loan_amount: float,
        annual_interest_rate: float,
        loan_term_months: int,
        show_first_n_months: int = 12,
    ) -> str:
        """Generate amortization schedule showing payment breakdown.

        Args:
            loan_amount: Principal loan amount
            annual_interest_rate: Annual interest rate
            loan_term_months: Loan term in months
            show_first_n_months: Number of initial months to display (default: 12)

        Returns:
            Formatted amortization schedule
        """
        try:
            loan_request = LoanRequest(
                loan_amount=loan_amount,
                annual_interest_rate=annual_interest_rate,
                loan_term_months=loan_term_months,
            )

            schedule = self.calculator_tool.generate_amortization_schedule(loan_request)

            response = f"## Amortization Schedule\n\n"
            response += f"Showing first {min(show_first_n_months, loan_term_months)} months:\n\n"

            # Format first N months
            df_subset = schedule.schedule.head(show_first_n_months)
            response += "| Month | Payment | Principal | Interest | Remaining Balance |\n"
            response += "|-------|---------|-----------|----------|-------------------|\n"

            for _, row in df_subset.iterrows():
                response += (
                    f"| {int(row['month'])} | "
                    f"${row['payment']:,.2f} | "
                    f"${row['principal']:,.2f} | "
                    f"${row['interest']:,.2f} | "
                    f"${row['balance']:,.2f} |\n"
                )

            if loan_term_months > show_first_n_months:
                response += f"\n... ({loan_term_months - show_first_n_months} more months)\n\n"

                # Show last month
                last_row = schedule.schedule.iloc[-1]
                response += f"**Final Month ({int(last_row['month'])})**: "
                response += f"${last_row['payment']:,.2f} payment, "
                response += f"Balance: ${last_row['balance']:,.2f}\n"

            return response

        except Exception as e:
            return f"Error generating schedule: {str(e)}"

    def check_affordability(
        self,
        loan_amount: float,
        annual_interest_rate: float,
        loan_term_months: int,
        monthly_income: float,
        existing_monthly_debt: float = 0.0,
    ) -> str:
        """Check if loan is affordable based on income and existing debt.

        Args:
            loan_amount: Principal loan amount
            annual_interest_rate: Annual interest rate
            loan_term_months: Loan term in months
            monthly_income: Monthly income
            existing_monthly_debt: Existing monthly debt payments

        Returns:
            Affordability assessment
        """
        try:
            loan_request = LoanRequest(
                loan_amount=loan_amount,
                annual_interest_rate=annual_interest_rate,
                loan_term_months=loan_term_months,
                monthly_income=monthly_income,
            )

            result = self.calculator_tool.check_affordability(loan_request, existing_monthly_debt)

            response = f"## Affordability Assessment\n\n"

            if result["affordable"]:
                response += "✅ **This loan appears AFFORDABLE**\n\n"
            else:
                response += "⚠️ **WARNING: This loan may be UNAFFORDABLE**\n\n"

            response += f"**Monthly Income**: ${result['monthly_income']:,.2f}\n"
            response += f"**Existing Monthly Debt**: ${result['existing_debt']:,.2f}\n"
            response += f"**New Loan Payment**: ${result['monthly_payment']:,.2f}\n"
            response += f"**Total Monthly Debt**: ${result['total_monthly_debt']:,.2f}\n\n"
            response += (
                f"**Debt-to-Income Ratio**: {result['dti_ratio']*100:.1f}% "
                f"(Max Recommended: {result['max_recommended_dti']*100:.0f}%)\n\n"
            )
            response += f"### Analysis:\n{result['message']}\n"

            return response

        except Exception as e:
            return f"Error checking affordability: {str(e)}"

    def compare_loan_terms(
        self,
        loan_amount: float,
        annual_interest_rate: float,
        term_options: Optional[list[int]] = None,
    ) -> str:
        """Compare different loan term options.

        Args:
            loan_amount: Principal loan amount
            annual_interest_rate: Annual interest rate
            term_options: List of terms in months (default: [24, 36, 48, 60])

        Returns:
            Comparison of loan term options
        """
        try:
            if term_options is None:
                term_options = [24, 36, 48, 60]

            comparison = self.calculator_tool.compare_loan_options(
                loan_amount=loan_amount, annual_rate=annual_interest_rate, terms=term_options
            )

            response = f"## Loan Term Comparison\n\n"
            response += f"Comparing different terms for ${loan_amount:,.2f} at {annual_interest_rate*100:.2f}% APR:\n\n"

            response += (
                "| Term | Monthly Payment | Total Payment | Total Interest | "
                "Interest as % |\n"
            )
            response += (
                "|------|----------------|---------------|----------------|---------------|\n"
            )

            for _, row in comparison.iterrows():
                response += (
                    f"| {int(row['term_months'])} months ({row['term_years']:.1f} yrs) | "
                    f"${row['monthly_payment']:,.2f} | "
                    f"${row['total_payment']:,.2f} | "
                    f"${row['total_interest']:,.2f} | "
                    f"{row['interest_percentage']:.1f}% |\n"
                )

            response += "\n### Key Insights:\n"
            response += "- **Shorter terms**: Higher monthly payment, less total interest\n"
            response += "- **Longer terms**: Lower monthly payment, more total interest\n"

            return response

        except Exception as e:
            return f"Error comparing terms: {str(e)}"

    def calculate_max_affordable_loan(
        self,
        monthly_income: float,
        annual_interest_rate: float,
        loan_term_months: int,
        existing_monthly_debt: float = 0.0,
    ) -> str:
        """Calculate maximum affordable loan amount.

        Args:
            monthly_income: Monthly income
            annual_interest_rate: Annual interest rate
            loan_term_months: Desired loan term
            existing_monthly_debt: Existing monthly debt payments

        Returns:
            Maximum affordable loan calculation
        """
        try:
            result = self.calculator_tool.calculate_max_loan_amount(
                monthly_income=monthly_income,
                annual_interest_rate=annual_interest_rate,
                loan_term_months=loan_term_months,
                existing_monthly_debt=existing_monthly_debt,
            )

            response = f"## Maximum Affordable Loan\n\n"

            if result["max_loan_amount"] > 0:
                response += f"✅ **Maximum Loan Amount**: ${result['max_loan_amount']:,.2f}\n\n"
                response += f"**Monthly Income**: ${result['monthly_income']:,.2f}\n"
                response += f"**Existing Debt**: ${result['existing_debt']:,.2f}\n"
                response += f"**Maximum Monthly Payment**: ${result['max_monthly_payment']:,.2f}\n"
                response += f"**Loan Term**: {result['term_months']} months\n"
                response += f"**Interest Rate**: {result['annual_interest_rate']*100:.2f}%\n\n"
                response += f"### Analysis:\n{result['message']}\n"
            else:
                response += f"❌ **Cannot afford additional loan**\n\n"
                response += f"{result['message']}\n"

            return response

        except Exception as e:
            return f"Error calculating max loan: {str(e)}"

    @property
    def user_id(self) -> Optional[str]:
        """Get current user ID from memory.

        Returns:
            User ID if memory is available and session is active, None otherwise
        """
        return self.memory.user_id if self.memory else None

    @property
    def session_id(self) -> Optional[str]:
        """Get current session ID from memory.

        Returns:
            Session ID if memory is available and session is active, None otherwise
        """
        return self.memory.session_id if self.memory else None

    def _extract_context_from_message(self, message: str) -> dict:
        """Extract context information from user message.

        Args:
            message: User's message

        Returns:
            Context dictionary with extracted information
        """
        context = {}

        # Try to extract common loan-related information
        import re

        # Extract income (e.g., "$8000/month", "earn $10k")
        income_patterns = [
            r'\$?(\d+,?\d*)[kK]?\s*(?:per\s*)?(?:month|monthly|/month)',
            r'(?:earn|income|make)\s+\$?(\d+,?\d*)[kK]?',
        ]
        for pattern in income_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                income_str = match.group(1).replace(',', '')
                income = float(income_str)
                if 'k' in match.group(0).lower() or 'K' in match.group(0):
                    income *= 1000
                context['monthly_income'] = income
                break

        # Extract credit score
        credit_match = re.search(r'credit\s*score\s*(?:of|is)?\s*(\d{3})', message, re.IGNORECASE)
        if credit_match:
            context['credit_score'] = int(credit_match.group(1))

        # Extract age
        age_match = re.search(r"(?:I'm|I am|age)\s*(\d{2})", message, re.IGNORECASE)
        if age_match:
            context['age'] = int(age_match.group(1))

        # Extract loan amount
        loan_patterns = [
            r'\$(\d+,?\d*)[kK]?\s*(?:loan|borrow)',
            r'(?:loan|borrow)\s*\$?(\d+,?\d*)[kK]?',
        ]
        for pattern in loan_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                amount = float(amount_str)
                if 'k' in match.group(0).lower() or 'K' in match.group(0):
                    amount *= 1000
                context['loan_amount'] = amount
                break

        # Extract loan term
        term_match = re.search(r'(\d+)\s*months?', message, re.IGNORECASE)
        if term_match:
            context['loan_term_months'] = int(term_match.group(1))

        # Extract employment status
        employment_keywords = {
            'full-time': 'full_time',
            'full time': 'full_time',
            'part-time': 'part_time',
            'part time': 'part_time',
            'self-employed': 'self_employed',
            'self employed': 'self_employed',
            'retired': 'retired',
            'unemployed': 'unemployed',
        }
        for keyword, status in employment_keywords.items():
            if keyword in message.lower():
                context['employment_status'] = status
                break

        return context

    def run(self, message: str, stream: bool = True):
        """Run the agent with a user message and print response.

        Args:
            message: User's question or request
            stream: Whether to stream the response (default: True)
        """
        # Store user message in MongoDB if memory is available
        if self.memory:
            self.memory.add_message("user", message)

        # Build conversation context manually from MongoDB history
        if self.memory:
            history = self.memory.get_conversation_history()
            # Convert to Agno format and build context string
            if len(history) > 1:  # If there's history beyond current message
                context_parts = []
                for msg in history[:-1]:  # Exclude the last message (current user message)
                    if msg['role'] == 'user':
                        context_parts.append(f"User previously said: {msg['content']}")
                    else:
                        context_parts.append(f"Assistant previously responded: {msg['content']}")

                # Prepend context to current message
                if context_parts:
                    context_str = "\n\n".join(context_parts)
                    full_message = f"Previous conversation:\n{context_str}\n\nCurrent message: {message}"
                else:
                    full_message = message
            else:
                full_message = message
        else:
            full_message = message

        # Run the agent with Agno's print_response
        run_result = self.agent.print_response(
            full_message,
            stream=stream
        )

        # After the response, save assistant message to MongoDB if memory is available
        if self.memory and run_result:
            # Extract response text from run result
            if hasattr(run_result, 'content'):
                response_text = run_result.content
            elif hasattr(run_result, 'messages') and run_result.messages:
                # Get last assistant message
                last_msg = run_result.messages[-1]
                response_text = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
            else:
                response_text = str(run_result)

            # Store assistant response in MongoDB
            if response_text:
                self.memory.add_message("assistant", response_text)

                # Trigger async evaluation (100% of interactions)
                if self.memory.enable_evaluation:
                    # Extract context from conversation
                    context = self._extract_context_from_message(message)

                    # Add metadata
                    metadata = {
                        "agent_model": self.agent.model.id if hasattr(self.agent, 'model') else "unknown",
                        "stream_mode": stream,
                    }

                    # Submit evaluation asynchronously (non-blocking)
                    evaluation_id = self.memory.evaluate_interaction(
                        user_input=message,
                        agent_output=response_text,
                        context=context,
                        metadata=metadata,
                    )

                    if evaluation_id:
                        logger.debug(f"Evaluation submitted: {evaluation_id}")
                        if self.agent.debug_mode:
                            logger.info(f"Evaluation {evaluation_id} queued for session {self.session_id}")
