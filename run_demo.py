import sys, os
# Ensure the project root is on PYTHONPATH
project_root = r'C:/Users/User/projects/customer-support-agent'
if project_root not in sys.path:
    sys.path.append(project_root)

from app.agent import CustomerSupportAgent

# Simulated user query (you can change this string as needed)
user_query = "What are the shipping rates?"

print('Running CustomerSupportAgent with query:', user_query)

# Provide the input directly to the graph agent (bypassing the interactive RequestInput node)
# The RequestInput node uses the key "request_input" by default.
result = CustomerSupportAgent().run({"request_input": user_query})

print('\nAgent response:')
print(result)
