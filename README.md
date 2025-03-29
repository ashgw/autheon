# Autheon

Plug and play OAuth2 3rd party integration library for FastAPI

> **Warning**: This project is still a Work In Progress (WIP). Expect bugs, as it hasn't been officially published yet, nor is it finished.

## Installation

```bash
pip install autheon
```

## Quick Start

Here's a basic example:

```python
from fastapi import FastAPI
from dotenv import load_dotenv
from os import getenv

from autheon.libtypes import UserInfo, FallbackSecrets
from autheon.jwts.helpers import generate_secret
from autheon.oauth2_options import OAuthOptions
from autheon.providers.google.google import Google
from autheon.adapters.fastapi.csrf_middleware import CSRFMitigationMiddleware

load_dotenv()

# Define what happens when a user logs in
async def push_to_db(user_info: UserInfo) -> None:
    with open("my_db", "w") as f:
        f.write(user_info["name"])

# Configure OAuth options
auth = OAuthOptions(
    debug=True,
    provider=Google(
        client_id=getenv("GOOGLE_CLIENT_ID"),
        client_secret=getenv("GOOGLE_CLIENT_SECRET"),
        redirect_uri=getenv("GOOGLE_REDIRECT_URI"),
    ),
    signin_callback=push_to_db,
    fallback_secrets=FallbackSecrets(
        secret_1=getenv("SECRET"),
        secret_2=generate_secret(),
        secret_3=generate_secret(),
        secret_4=generate_secret(),
        secret_5=generate_secret(),
    ),
)

app = FastAPI()
# Plug in the router
app.include_router(auth)

# Optional for OAuth flow, but highly recommended
app.add_middleware(CSRFMitigationMiddleware)
```

## Usage

Define your protected routes:

```python
@app.get("/auth/in")
def logged():
    return "youre in"

@app.get("/auth/out")
def out():
    return "out"
```

## Supported Providers

Autheon currently supports the following OAuth providers:

-   Google
-   GitHub
-   Reddit
-   Discord
-   Spotify

## Documentation

For more detailed documentation, visit [autheon.ashgw.me](https://autheon.ashgw.me)

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/ashgw/autheon/blob/main/LICENSE) file for details.

```

```
