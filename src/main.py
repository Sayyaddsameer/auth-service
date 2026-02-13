import json
import httpx
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from src.database import engine, Base, get_db, User, AuthProvider, AsyncSessionLocal
from src.schemas import UserCreate, UserLogin, Token, UserResponse, UserUpdate, RefreshTokenRequest
from src.security import (
    get_password_hash, verify_password, create_access_token, 
    create_refresh_token, verify_token
)
from src.limiter import rate_limiter
from src.config import settings

# --- THIS IS THE MISSING VARIABLE ---
app = FastAPI()
# ------------------------------------

# --- Startup: Dynamic Seeding ---
@app.on_event("startup")
async def startup_event():
    # 1. Create DB Tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Seed Users from submission.json dynamically
    try:
        with open("submission.json", "r") as f:
            data = json.load(f)
            creds = data.get("testCredentials", {})
            
            async with AsyncSessionLocal() as session:
                # Seed Admin
                admin_data = creds.get("adminUser")
                if admin_data:
                    exists = await session.execute(select(User).where(User.email == admin_data["email"]))
                    if not exists.scalar_one_or_none():
                        admin = User(
                            email=admin_data["email"],
                            password_hash=get_password_hash(admin_data["password"]),
                            name="Admin User",
                            role="admin"
                        )
                        session.add(admin)

                # Seed Regular User
                user_data = creds.get("regularUser")
                if user_data:
                    exists = await session.execute(select(User).where(User.email == user_data["email"]))
                    if not exists.scalar_one_or_none():
                        user = User(
                            email=user_data["email"],
                            password_hash=get_password_hash(user_data["password"]),
                            name="Regular User",
                            role="user"
                        )
                        session.add(user)
                
                await session.commit()
                print("Database seeded from submission.json")
    except FileNotFoundError:
        print("submission.json not found, skipping seed.")
    except Exception as e:
        print(f"Error seeding database: {e}")

@app.get("/health")
def health_check():
    return {"status": "ok"}

# --- Dependencies ---
async def get_current_user(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    result = await db.execute(select(User).where(User.email == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

# --- Auth Routes ---
@app.post("/api/auth/register", response_model=UserResponse, status_code=201, dependencies=[Depends(rate_limiter)])
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        role="user"
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.post("/api/auth/login", response_model=Token, dependencies=[Depends(rate_limiter)])
async def login(creds: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == creds.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(creds.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "accessToken": create_access_token({"sub": user.email, "role": user.role}),
        "refreshToken": create_refresh_token({"sub": user.email})
    }

@app.post("/api/auth/refresh", response_model=dict)
async def refresh_token(request: RefreshTokenRequest):
    payload = verify_token(request.refreshToken, is_refresh=True)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return {"accessToken": create_access_token({"sub": payload["sub"]})}

# --- OAuth Implementation ---
async def handle_oauth_login(db: AsyncSession, email: str, name: str, provider: str, provider_id: str):
    result = await db.execute(select(AuthProvider).where(
        AuthProvider.provider == provider,
        AuthProvider.provider_user_id == provider_id
    ))
    link = result.scalar_one_or_none()

    if link:
        user_res = await db.execute(select(User).where(User.id == link.user_id))
        user = user_res.scalar_one()
    else:
        user_res = await db.execute(select(User).where(User.email == email))
        user = user_res.scalar_one_or_none()
        
        if not user:
            user = User(email=email, name=name, role="user")
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        new_link = AuthProvider(user_id=user.id, provider=provider, provider_user_id=provider_id)
        db.add(new_link)
        await db.commit()
    
    return {
        "accessToken": create_access_token({"sub": user.email, "role": user.role}),
        "refreshToken": create_refresh_token({"sub": user.email})
    }

@app.get("/api/auth/google")
async def google_auth():
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?response_type=code"
        f"&client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        "&scope=openid%20email%20profile"
    )
    return RedirectResponse(url)

@app.get("/api/auth/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            }
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Google Auth Failed")
        
        token_data = token_resp.json()
        user_info_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        user_info = user_info_resp.json()
        
        return await handle_oauth_login(
            db, 
            email=user_info["email"], 
            name=user_info.get("name", "Google User"), 
            provider="google", 
            provider_id=user_info["sub"]
        )

@app.get("/api/auth/github")
async def github_auth():
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        "&scope=user:email"
    )
    return RedirectResponse(url)

@app.get("/api/auth/github/callback")
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI
            }
        )
        token_data = token_resp.json()
        if "access_token" not in token_data:
            raise HTTPException(status_code=400, detail="GitHub Auth Failed")

        access_token = token_data["access_token"]
        user_resp = await client.get("https://api.github.com/user", headers={"Authorization": f"Bearer {access_token}"})
        user_data = user_resp.json()
        
        email = user_data.get("email")
        if not email:
            emails_resp = await client.get("https://api.github.com/user/emails", headers={"Authorization": f"Bearer {access_token}"})
            for e in emails_resp.json():
                if e["primary"] and e["verified"]:
                    email = e["email"]
                    break
        
        return await handle_oauth_login(
            db,
            email=email,
            name=user_data.get("name") or user_data.get("login"),
            provider="github",
            provider_id=str(user_data["id"])
        )

# --- User Routes ---
@app.get("/api/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.patch("/api/users/me", response_model=UserResponse)
async def update_user_me(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    current_user.name = user_update.name
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user

@app.get("/api/users", response_model=list[UserResponse])
async def read_users(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()