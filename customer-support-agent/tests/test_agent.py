import unittest
import json
from unittest.mock import MagicMock, patch
from app.agent import CustomerSupportAgent

class TestCustomerSupportAgent(unittest.TestCase):
    @patch('google.genai.Client')
    def test_workflow_runs_end_to_end(self, mock_client_class):
        # Set up mock client instance
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.vertexai = False
        
        from google.genai import types

        # Create a real response object using pydantic models to satisfy validation
        mock_response = types.GenerateContentResponse(
            model_version="gemini-2.5-flash",
            candidates=[
                types.Candidate(
                    content=types.Content(
                        role="model",
                        parts=[
                            types.Part.from_text(
                                text=(
                                    "1. Entity: Acme Corp\n"
                                    "2. Problem Type: payment delays\n"
                                    "3. Risk Assessment: high\n"
                                    "4. Revenue Loss Risk: $50,000 overdue invoice\n"
                                    "5. Recommended Action: Send payment reminder."
                                )
                            )
                        ]
                    )
                )
            ]
        )
        
        # Mock both sync and async generate content models
        mock_client.models.generate_content.return_value = mock_response
        
        async def mock_async_stream(*args, **kwargs):
            yield mock_response
            
        mock_client.models.generate_content_stream_async = mock_async_stream
        
        async def mock_async_generate(*args, **kwargs):
            return mock_response
            
        mock_client.models.generate_content_async = mock_async_generate
        
        # Add mock for the async client client.aio.models.generate_content
        mock_client.aio = MagicMock()
        mock_client.aio.models = MagicMock()
        mock_client.aio.models.generate_content = mock_async_generate
        
        # Run agent
        agent = CustomerSupportAgent()
        
        mock_data = {
            "crm": [{"account_name": "Acme Corp", "deal_stage": "Negotiation", "days_in_stage": 120, "last_contact_days_ago": 45}],
            "invoices": [{"invoice_id": "INV-1001", "customer": "Acme Corp", "amount": 50000.00, "status": "Overdue", "due_days_overdue": 90}],
            "customers": [{"name": "Acme Corp", "support_tickets_open": 5, "satisfaction_score": 2.1, "contract_expiry": "2026-08-31"}],
            "transactions": [{"transaction_id": "TXN-501", "customer": "Acme Corp", "type": "Subscription Renewal Payment", "status": "Failed", "amount": 50000.00}]
        }
        
        result = agent.run(mock_data)
        
        # Assertions
        self.assertIn("REVENUE LOSS RISK ANALYSIS REPORT", result)
        self.assertIn("Acme Corp", result)
        self.assertIn("payment delays", result)

 

if __name__ == '__main__':
    unittest.main()
