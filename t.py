import os
from dotenv import load_dotenv

load_dotenv()

print(os.getenv('api_key'), os.getenv('api_secret_key'))
print(os.getenv('access_token'), os.getenv('secret_access_token'))