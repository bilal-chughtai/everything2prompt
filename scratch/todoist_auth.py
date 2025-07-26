# %%
from dotenv import load_dotenv
import uuid
from todoist_api_python.authentication import get_auth_token, get_authentication_url
import os
load_dotenv()

# 1. Generate a random state
state = uuid.uuid4()

# %%
# 2. Get authorization url
url = get_authentication_url(
    client_id=os.getenv("TODOIST_CLIENT_ID"),
    scopes=["data:read"],
    state=state,
)
print(url)

# %%
# 3.Redirect user to url
# 4. Handle OAuth callback and get code
code = "CODE_YOU_OBTAINED"

# %%
# 5. Exchange code for access token
auth_result = get_auth_token(
    client_id=os.getenv("TODOIST_CLIENT_ID"),
    client_secret=os.getenv("TODOIST_CLIENT_SECRET"),
    code=code,
)

# %%
# 6. Ensure state is consistent, and done!
assert auth_result.state == state
access_token = auth_result.access_token
