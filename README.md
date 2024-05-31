This setup currently works, but this project is still under development
```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response

from dotenv import load_dotenv
from os import getenv

from starlette.requests import Request
from fastauth._types import UserInfo, FallbackSecrets
from fastauth.jwts.helpers import generate_secret
from fastauth.frameworks import FastAPI as FastAPIFramework
from fastauth.oauth2_options import OAuthOptions
from fastauth.providers.google.google import Google


from fastauth.adapters.fastapi.csrf_middleware import CSRFMitigationMiddleware
load_dotenv()


# What happens when someone logs in
async def push_to_db(user_info: UserInfo) -> None:
    with open('my_db','w') as f:
        f.write(user_info['name'])

# One router takes care of everything
auth = OAuthOptions(
    framework=FastAPIFramework(),
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
app.include_router(auth)

# Optional for OAuth flow, but highly recommended
app.add_middleware(CSRFMitigationMiddleware)
```
OAuth routes should use POST methods, but as I mentioned, I'm still devving. So this will work, play around with it
```python
@app.get("/auth/in")
def logged():
    return  'youre in'
@app.get("/auth/out")
def out():
    return 'out'
```
