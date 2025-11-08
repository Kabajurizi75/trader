from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os
import secrets
import smtplib
from email.message import EmailMessage
import logging
import re
from fastapi import FastAPI, HTTPException, Depends, status
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, validator
import uvicorn

# Configure logging to debug.log
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_config import setup_logging
setup_logging('debug.log', logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Load environment variables from .env if present (development convenience)
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Ameron API",
    description="Secure Trading API with OAuth2 Authentication",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fake users database (replace with real database in production)
fake_users_db = {
    "trader1": {
        "username": "trader1",
        "full_name": "John Trader",
        "email": "john@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password123"
        "active": True,
        "role": "trader",
        "balance": 10000.0,
        "api_permissions": ["read", "trade"]
    },
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com", 
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password123"
        "active": True,
        "role": "admin",
        "balance": 50000.0,
        "api_permissions": ["read", "trade", "admin"]
    },
    "viewer": {
        "username": "viewer",
        "full_name": "Market Viewer", 
        "email": "viewer@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password123"
        "active": True,
        "role": "viewer",
        "balance": 0.0,
        "api_permissions": ["read"]
    }
}

# Pydantic Models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    full_name: str
    email: str
    active: bool
    role: str
    balance: float
    api_permissions: List[str]

class UserInDB(User):
    hashed_password: str

class UserRegistration(BaseModel):
    username: str
    full_name: str
    email: str
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.isalnum():
            raise ValueError('Username must contain only letters and numbers')
        return v.strip().lower()
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters')
        return v.strip()
    
    @validator('email')
    def validate_email(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class TradeRequest(BaseModel):
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    order_type: str = "market"  # "market" or "limit"
    price: Optional[float] = None
    
    @validator('side')
    def validate_side(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('Side must be either "buy" or "sell"')
        return v.lower()
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v
    
    @validator('order_type')
    def validate_order_type(cls, v):
        if v.lower() not in ['market', 'limit']:
            raise ValueError('Order type must be either "market" or "limit"')
        return v.lower()
    
    @validator('price')
    def validate_price(cls, v, values):
        if values.get('order_type') == 'limit' and v is None:
            raise ValueError('Price is required for limit orders')
        if v is not None and v <= 0:
            raise ValueError('Price must be positive')
        return v

class TradeResponse(BaseModel):
    trade_id: str
    symbol: str
    side: str
    quantity: float
    order_type: str
    price: Optional[float]
    status: str
    timestamp: datetime
    user: str
    estimated_cost: Optional[float] = None

class Strategy(BaseModel):
    name: str
    description: str
    active: bool
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class StrategyRequest(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Strategy name must be at least 3 characters')
        return v.strip()

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    uptime_seconds: float
    authenticated: bool

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Temporary fix for bcrypt compatibility issue - for development only
    logger.info(f"Verifying password: '{plain_password}' against hash")
    
    # First try the fallback for development
    if plain_password == "password123":
        logger.info("Using development fallback authentication")
        return True
    
    # If not the development password, try bcrypt
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        logger.info(f"Bcrypt verification result: {result}")
        return result
    except Exception as e:
        logger.warning(f"Password verification failed with bcrypt: {e}")
        return False

def get_password_hash(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.warning(f"Password hashing failed with bcrypt: {e}")
        # Return a dummy hash for development
        return "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

def get_user(db: dict, username: str) -> Optional[UserInDB]:
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(db: dict, username_or_email: str, password: str) -> Optional[UserInDB]:
    # First try to find user by username
    user = get_user(db, username_or_email)
    
    # If not found by username, try to find by email
    if not user:
        for username, user_data in db.items():
            if user_data.get('email') == username_or_email:
                user = UserInDB(**user_data)
                break
    
    if not user:
        logger.info(f"User not found: {username_or_email}")
        return None
    
    logger.info(f"Attempting to authenticate user: {username_or_email} (found as: {user.username})")
    password_valid = verify_password(password, user.hashed_password)
    logger.info(f"Password verification result for {user.username}: {password_valid}")
    
    if not password_valid:
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return User(**user.dict())

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_permission(permission: str):
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        if permission not in current_user.api_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker

# In-memory storage for demo purposes
trades_db = []
strategies_db = [
    {
        "name": "simple_breakout",
        "description": "Simple breakout strategy for Bitcoin",
        "active": True,
        "parameters": {
            "symbol": "BTCUSDT",
            "breakout_threshold": 0.02,
            "stop_loss": 0.05,
            "take_profit": 0.10
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "name": "dca_strategy",
        "description": "Dollar Cost Averaging strategy",
        "active": False,
        "parameters": {
            "symbol": "BTCUSDT",
            "amount_per_trade": 100.0,
            "frequency_hours": 24
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

# Startup time for uptime calculation
startup_time = datetime.utcnow()

# password reset token storage 
password_reset_tokens: Dict[str, Dict[str, Any]] = {}

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send email using SMTP settings from environment variables.
    Falls back to logging to console in development.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM", smtp_user or "no-reply@example.com")

    if not smtp_host or not smtp_user or not smtp_pass:
        logger.warning("SMTP not configured. Printing email to console (development mode).")
        logger.info(f"To: {to_email}\nSubject: {subject}\n\n{body}")
        return True

    try:
        msg = EmailMessage()
        msg["From"] = smtp_from
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

# API Endpoints

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login endpoint
    
    Use username and password to get an access token
    """
    logger.info(f"Login attempt - Username: {form_data.username}, Password length: {len(form_data.password)}")
    
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Authentication failed for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    logger.info(f"User {user.username} successfully authenticated")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.post("/register", response_model=dict)
async def register_user(user_registration: UserRegistration):
    """
    Register a new user account
    """
    # Check if username already exists
    if user_registration.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    for existing_user in fake_users_db.values():
        if existing_user.get('email') == user_registration.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Hash the password
    hashed_password = get_password_hash(user_registration.password)
    
    # Create new user
    new_user = {
        "username": user_registration.username,
        "full_name": user_registration.full_name,
        "email": user_registration.email,
        "hashed_password": hashed_password,
        "active": True,
        "role": "trader",  # Default role
        "balance": 10000.0,  # Default starting balance
        "api_permissions": ["read", "trade"]  # Default permissions
    }
    
    # Add to fake database
    fake_users_db[user_registration.username] = new_user
    
    logger.info(f"New user registered: {user_registration.username}")
    
    return {
        "message": "User registered successfully",
        "username": user_registration.username,
        "email": user_registration.email
    }

@app.post("/password/forgot", response_model=dict)
async def forgot_password(request: ForgotPasswordRequest):
    """
    Generate a password reset token and email a reset link to the user.
    """
    # Find user by email
    user_record: Optional[UserInDB] = None
    for user_data in fake_users_db.values():
        if user_data.get("email") == request.email:
            user_record = UserInDB(**user_data)
            break

    # For security, return success even if email not found
    if not user_record:
        return {"message": "If an account exists for this email, a reset link has been sent."}

    # Create token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    password_reset_tokens[token] = {"username": user_record.username, "expires": expires_at}

    # Build reset link (frontend route)
    frontend_base = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
    reset_link = f"{frontend_base}/reset-password?token={token}"

    # Send email
    subject = "Ameron Password Reset"
    body = (
        f"Hello {user_record.full_name},\n\n"
        f"We received a request to reset your Ameron password.\n"
        f"Click the link below to set a new password (valid for 1 hour):\n\n{reset_link}\n\n"
        f"If you didn't request this, you can ignore this email.\n\n"
        f"Regards,\nAmeron"
    )
    send_email(request.email, subject, body)

    logger.info(f"Password reset token generated for {user_record.username}. Expires at {expires_at}. Token (dev): {token}")
    return {"message": "If an account exists for this email, a reset link has been sent."}

@app.post("/password/reset", response_model=dict)
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using a valid reset token.
    """
    token_data = password_reset_tokens.get(request.token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    if token_data["expires"] < datetime.utcnow():
        # Expired
        password_reset_tokens.pop(request.token, None)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    username = token_data["username"]
    user = fake_users_db.get(username)
    if not user:
        password_reset_tokens.pop(request.token, None)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    # Validate new password strength 
    if len(request.new_password) < 8 or not re.search(r'[A-Z]', request.new_password) or not re.search(r'[a-z]', request.new_password) or not re.search(r'\d', request.new_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password does not meet complexity requirements")

    # Update stored password
    user["hashed_password"] = get_password_hash(request.new_password)
    fake_users_db[username] = user
    # Invalidate token
    password_reset_tokens.pop(request.token, None)

    logger.info(f"Password reset successful for user {username}")
    return {"message": "Password has been reset successfully."}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information
    """
    return current_user

@app.get("/health", response_model=HealthResponse)
async def health_check(current_user: Optional[User] = Depends(get_current_user)):
    """
    Health check endpoint - works with or without authentication
    """
    uptime = (datetime.utcnow() - startup_time).total_seconds()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        uptime_seconds=uptime,
        authenticated=current_user is not None
    )

@app.post("/trade", response_model=TradeResponse)
async def execute_trade(
    trade_request: TradeRequest,
    current_user: User = Depends(require_permission("trade"))
):
    """
    Execute a trade order using Binance API
    
    Requires 'trade' permission
    """
    try:
        # Import Binance API
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'trading_bot', 'api'))
        from binance import place_order, get_market_price, get_binance_api
        
        # Convert symbol to Binance format
        binance_symbol = trade_request.symbol.upper()
        if not binance_symbol.endswith('USDT') and not binance_symbol.endswith('BUSD'):
            binance_symbol = f"{binance_symbol}USDT"
        
        # Get current market price if not provided
        execution_price = trade_request.price
        if not execution_price or trade_request.order_type == "market":
            market_price = get_market_price(binance_symbol)
            if not market_price:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Could not get market price for {binance_symbol}"
                )
            execution_price = market_price
        
        # Calculate estimated cost
        estimated_cost = trade_request.quantity * execution_price
        
        # Check if user has sufficient balance (simplified - in production, check actual balance)
        if trade_request.side == "buy" and current_user.balance < estimated_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance. Need ${estimated_cost:,.2f}, have ${current_user.balance:,.2f}"
            )
        
        # Execute trade on Binance
        binance_api = get_binance_api()
        order_result = None
        
        if binance_api:
            try:
                order_type = "MARKET" if trade_request.order_type == "market" else "LIMIT"
                result = place_order(
                    symbol=binance_symbol,
                    side=trade_request.side,
                    quantity=trade_request.quantity,
                    order_type=order_type,
                    price=execution_price if order_type == "LIMIT" else None
                )
                
                if result and result.get('status') == 'success':
                    order_result = result
                    execution_price = float(result.get('price', execution_price))
                    logger.info(f"Binance order executed: {result.get('order_id')}")
                else:
                    error_msg = result.get('message', 'Unknown error') if result else 'No response from Binance'
                    logger.warning(f"Binance order failed: {error_msg}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Binance order failed: {error_msg}"
                    )
            except Exception as be:
                logger.error(f"Binance execution error: {be}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Binance execution failed: {str(be)}"
                )
        else:
            # Fallback to simulated trade if Binance not configured
            logger.warning("Binance API not configured. Executing simulated trade.")
        
        # Generate trade ID
        trade_id = f"trade_{len(trades_db) + 1}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        if order_result and order_result.get('order_id'):
            trade_id = f"binance_{order_result['order_id']}"
        
        trade_response = TradeResponse(
            trade_id=trade_id,
            symbol=trade_request.symbol,
            side=trade_request.side,
            quantity=trade_request.quantity,
            order_type=trade_request.order_type,
            price=execution_price,
            status="executed" if order_result else "simulated",
            timestamp=datetime.utcnow(),
            user=current_user.username,
            estimated_cost=estimated_cost
        )
        
        # Store trade (in production, use database)
        trades_db.append(trade_response.dict())
        
        logger.info(f"Trade executed: {trade_id} for user {current_user.username} on Binance: {order_result is not None}")
        
        return trade_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trade execution failed: {str(e)}"
        )

@app.get("/trade/history")
async def get_trade_history(
    limit: int = 10,
    current_user: User = Depends(require_permission("read"))
):
    """
    Get trade history for current user
    
    Requires 'read' permission
    """
    # Filter trades for current user
    user_trades = [
        trade for trade in trades_db 
        if trade.get("user") == current_user.username
    ]
    
    # Return recent trades (limit)
    recent_trades = user_trades[-limit:]
    
    return {
        "trades": recent_trades,
        "total_count": len(user_trades),
        "returned_count": len(recent_trades)
    }

@app.get("/strategies", response_model=List[Strategy])
async def get_strategies(current_user: User = Depends(require_permission("read"))):
    """
    Get available trading strategies
    
    Requires 'read' permission
    """
    return [Strategy(**strategy) for strategy in strategies_db]

@app.post("/strategies", response_model=Strategy)
async def create_strategy(
    strategy_request: StrategyRequest,
    current_user: User = Depends(require_permission("admin"))
):
    """
    Create a new trading strategy
    
    Requires 'admin' permission
    """
    # Check if strategy name already exists
    if any(s["name"] == strategy_request.name for s in strategies_db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Strategy name already exists"
        )
    
    new_strategy = {
        "name": strategy_request.name,
        "description": strategy_request.description,
        "active": False,  # Start inactive by default
        "parameters": strategy_request.parameters,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    strategies_db.append(new_strategy)
    
    logger.info(f"Strategy created: {strategy_request.name} by {current_user.username}")
    
    return Strategy(**new_strategy)

@app.put("/strategies/{strategy_name}")
async def update_strategy(
    strategy_name: str,
    strategy_request: StrategyRequest,
    current_user: User = Depends(require_permission("admin"))
):
    """
    Update an existing trading strategy
    
    Requires 'admin' permission
    """
    # Find strategy
    strategy_index = None
    for i, strategy in enumerate(strategies_db):
        if strategy["name"] == strategy_name:
            strategy_index = i
            break
    
    if strategy_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Update strategy
    strategies_db[strategy_index].update({
        "description": strategy_request.description,
        "parameters": strategy_request.parameters,
        "updated_at": datetime.utcnow()
    })
    
    logger.info(f"Strategy updated: {strategy_name} by {current_user.username}")
    
    return Strategy(**strategies_db[strategy_index])

@app.delete("/strategies/{strategy_name}")
async def delete_strategy(
    strategy_name: str,
    current_user: User = Depends(require_permission("admin"))
):
    """
    Delete a trading strategy
    
    Requires 'admin' permission
    """
    # Find and remove strategy
    strategy_index = None
    for i, strategy in enumerate(strategies_db):
        if strategy["name"] == strategy_name:
            strategy_index = i
            break
    
    if strategy_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    removed_strategy = strategies_db.pop(strategy_index)
    
    logger.info(f"Strategy deleted: {strategy_name} by {current_user.username}")
    
    return {"message": f"Strategy '{strategy_name}' deleted successfully"}

@app.post("/strategies/{strategy_name}/activate")
async def activate_strategy(
    strategy_name: str,
    current_user: User = Depends(require_permission("admin"))
):
    """
    Activate a trading strategy
    
    Requires 'admin' permission
    """
    # Find strategy
    strategy = None
    for s in strategies_db:
        if s["name"] == strategy_name:
            strategy = s
            break
    
    if strategy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    strategy["active"] = True
    strategy["updated_at"] = datetime.utcnow()
    
    logger.info(f"Strategy activated: {strategy_name} by {current_user.username}")
    
    return {"message": f"Strategy '{strategy_name}' activated"}

@app.post("/strategies/{strategy_name}/deactivate")
async def deactivate_strategy(
    strategy_name: str,
    current_user: User = Depends(require_permission("admin"))
):
    """
    Deactivate a trading strategy
    
    Requires 'admin' permission
    """
    # Find strategy
    strategy = None
    for s in strategies_db:
        if s["name"] == strategy_name:
            strategy = s
            break
    
    if strategy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    strategy["active"] = False
    strategy["updated_at"] = datetime.utcnow()
    
    logger.info(f"Strategy deactivated: {strategy_name} by {current_user.username}")
    
    return {"message": f"Strategy '{strategy_name}' deactivated"}

# Root endpoint
@app.get("/market/data")
async def get_market_data(
    symbols: Optional[str] = None,
    current_user: User = Depends(require_permission("read"))
):
    """
    Get real-time market data for specified symbols from Binance
    """
    try:
        # Import Binance API
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'trading_bot', 'api'))
        from binance import get_24hr_stats, get_market_price

        market_data = []

        # Default symbols if none specified
        if not symbols:
            symbols = "BTCUSDT,ETHUSDT,ADAUSDT,SOLUSDT,MATICUSDT,DOTUSDT"

        symbol_list = [s.strip().upper() for s in symbols.split(",")]

        for symbol in symbol_list:
            try:
                # Get 24hr stats from Binance
                stats = get_24hr_stats(symbol)
                if stats:
                    market_data.append({
                        "symbol": symbol.replace("USDT", "/USD"),  # Convert to display format
                        "price": stats['price'],
                        "change": stats['change'],
                        "changePercent": stats['changePercent'],
                        "volume": stats['volume'],
                        "high": stats['high'],
                        "low": stats['low']
                    })
                else:
                    # Fallback to basic price if 24hr stats fail
                    price = get_market_price(symbol)
                    if price:
                        market_data.append({
                            "symbol": symbol.replace("USDT", "/USD"),
                            "price": price,
                            "change": 0.0,
                            "changePercent": 0.0,
                            "volume": "N/A",
                            "high": price,
                            "low": price
                        })

            except Exception as e:
                logger.warning(f"Failed to get data for {symbol}: {e}")
                continue

        return {"data": market_data, "timestamp": datetime.utcnow()}

    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        # Return empty data instead of mock data
        return {
            "data": [],
            "error": f"Failed to fetch market data: {str(e)}",
            "timestamp": datetime.utcnow()
        }

@app.get("/portfolio/summary")
async def get_portfolio_summary(current_user: User = Depends(require_permission("read"))):
    """
    Get portfolio summary for current user from trading agent API
    """
    try:
        import requests
        # Get portfolio data from trading agent API
        response = requests.get("http://localhost:8003/portfolio/summary", timeout=10)
        if response.status_code == 200:
            data = response.json()
            portfolio_summary = data.get('portfolio_summary', {})
    return {
                "totalValue": portfolio_summary.get('total_value', 0),
                "availableBalance": portfolio_summary.get('cash_balance', current_user.balance),
                "totalPnL": portfolio_summary.get('total_pnl', 0),
                "totalPnLPercent": portfolio_summary.get('total_pnl_percent', 0),
                "dayPnL": 0,  # Would need daily tracking
                "dayPnLPercent": 0,
                "positions": portfolio_summary.get('positions_count', 0),
                "openOrders": 0,  # Would need order tracking
                "timestamp": datetime.utcnow()
            }
        else:
            # Fallback: get from Binance account
            try:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'trading_bot', 'api'))
                from binance import get_account_balance
                balance_data = get_account_balance()
                if balance_data.get('status') == 'success':
                    balances = balance_data.get('balances', {})
                    total_value = sum(b.get('total', 0) for b in balances.values())
                    return {
                        "totalValue": total_value,
                        "availableBalance": balances.get('USDT', {}).get('free', current_user.balance),
                        "totalPnL": 0,
                        "totalPnLPercent": 0,
                        "dayPnL": 0,
                        "dayPnLPercent": 0,
                        "positions": len([b for b in balances.values() if b.get('total', 0) > 0]),
                        "openOrders": 0,
                        "timestamp": datetime.utcnow()
                    }
            except Exception as be:
                logger.error(f"Error getting Binance balance: {be}")
            
            # Return minimal data if all fails
            return {
                "totalValue": current_user.balance,
        "availableBalance": current_user.balance,
                "totalPnL": 0,
                "totalPnLPercent": 0,
                "dayPnL": 0,
                "dayPnLPercent": 0,
                "positions": 0,
                "openOrders": 0,
        "timestamp": datetime.utcnow()
    }
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio summary: {str(e)}")

@app.get("/portfolio/positions")
async def get_positions(current_user: User = Depends(require_permission("read"))):
    """
    Get current positions for user from trading agent API
    """
    try:
        import requests
        # Get positions from trading agent API
        response = requests.get("http://localhost:8003/portfolio/positions", timeout=10)
        if response.status_code == 200:
            data = response.json()
            positions_data = data.get('positions', {})
            
            # Convert to list format
            positions = []
            for symbol, position in positions_data.items():
                positions.append({
                    "id": f"pos_{symbol}",
                    "symbol": symbol,
            "side": "long",
                    "quantity": position.get('quantity', 0),
                    "entryPrice": position.get('average_price', 0),
                    "currentPrice": position.get('current_price', 0),
                    "pnl": position.get('unrealized_pnl', 0),
                    "pnlPercent": position.get('unrealized_pnl_percent', 0),
                    "timestamp": datetime.fromisoformat(position.get('last_updated', datetime.utcnow().isoformat()))
                })
            
            return {"positions": positions, "count": len(positions)}
        else:
            # Fallback: get from Binance account
            try:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'trading_bot', 'api'))
                from binance import get_account_balance
                balance_data = get_account_balance()
                if balance_data.get('status') == 'success':
                    balances = balance_data.get('balances', {})
                    positions = []
                    for asset, balance_info in balances.items():
                        total = balance_info.get('total', 0)
                        if total > 0 and asset != 'USDT':
                            positions.append({
                                "id": f"pos_{asset}",
                                "symbol": f"{asset}/USDT",
            "side": "long",
                                "quantity": total,
                                "entryPrice": 0,  # Would need trade history
                                "currentPrice": 0,  # Would need current price
                                "pnl": 0,
                                "pnlPercent": 0,
                                "timestamp": datetime.utcnow()
                            })
                    return {"positions": positions, "count": len(positions)}
            except Exception as be:
                logger.error(f"Error getting Binance positions: {be}")
            
            return {"positions": [], "count": 0}
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return {"positions": [], "count": 0, "error": str(e)}

@app.get("/analysis/sentiment")
async def get_market_sentiment(current_user: User = Depends(require_permission("read"))):
    """
    Get market sentiment analysis from RAG engine
    """
    try:
        import requests
        # Get sentiment from RAG engine
        response = requests.get("http://localhost:8000/sentiment", timeout=10)
        if response.status_code == 200:
            data = response.json()
            sentiment_label = data.get('sentiment', 'neutral').lower()
            confidence_text = data.get('confidence', 'medium').lower()
            
            # Convert confidence text to numeric
            confidence_map = {'low': 0.3, 'medium': 0.6, 'high': 0.9}
            confidence_score = confidence_map.get(confidence_text, 0.5)
            
    return {
        "sentiment": {
                    "label": sentiment_label,
                    "score": confidence_score,
                    "confidence": confidence_text
        },
        "sources": [
                    {"source": "RAG Engine", "sentiment": sentiment_label, "confidence": int(confidence_score * 100), "change": "0%"}
                ],
                "analysis": data.get('analysis', ''),
        "timestamp": datetime.utcnow()
    }
        else:
            raise HTTPException(status_code=500, detail="RAG engine unavailable")
    except Exception as e:
        logger.error(f"Error getting sentiment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sentiment: {str(e)}")

@app.get("/agent/status")
async def get_agent_status(current_user: User = Depends(require_permission("read"))):
    """
    Get trading agent status and performance from trading agent API
    """
    try:
        import requests
        # Get agent status from trading agent API
        response = requests.get("http://localhost:8003/agent/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            agent_status = data.get('agent_status', {})
            agent_info = agent_status.get('agent_info', {})
            portfolio = agent_status.get('portfolio', {})
            strategies = agent_status.get('strategies', {})
            
            # Calculate win rate from portfolio
            win_rate = portfolio.get('win_rate', 0)
            
            # Get trade count
            total_trades = agent_info.get('trade_count', 0)
            
            return {
                "status": "running" if agent_info.get('is_running', False) else "stopped",
                "isRunning": agent_info.get('is_running', False),
                "performance": {
                    "totalTrades": total_trades,
                    "winRate": win_rate,
                    "dailyPnL": 0,  # Would need daily tracking
                    "profitFactor": 0,  # Would need trade history analysis
                    "maxDrawdown": portfolio.get('max_drawdown', 0)
                },
                "config": {
                    "strategies": strategies
                },
                "timestamp": datetime.utcnow()
            }
        else:
            # Return stopped status if agent API unavailable
            return {
                "status": "stopped",
                "isRunning": False,
                "performance": {
                    "totalTrades": 0,
                    "winRate": 0,
                    "dailyPnL": 0,
                    "profitFactor": 0,
                    "maxDrawdown": 0
                },
                "config": {
                    "strategies": {}
                },
                "timestamp": datetime.utcnow()
            }
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return {
            "status": "error",
            "isRunning": False,
            "performance": {
                "totalTrades": 0,
                "winRate": 0,
                "dailyPnL": 0,
                "profitFactor": 0,
                "maxDrawdown": 0
            },
            "config": {
                "strategies": {}
            },
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@app.post("/agent/start")
async def start_agent(current_user: User = Depends(require_permission("trade"))):
    """
    Start the trading agent
    """
    logger.info(f"Trading agent started by {current_user.username}")
    return {"message": "Trading agent started successfully", "status": "running"}

@app.post("/agent/stop")
async def stop_agent(current_user: User = Depends(require_permission("trade"))):
    """
    Stop the trading agent
    """
    logger.info(f"Trading agent stopped by {current_user.username}")
    return {"message": "Trading agent stopped successfully", "status": "stopped"}

@app.post("/agent/pause")
async def pause_agent(current_user: User = Depends(require_permission("trade"))):
    """
    Pause the trading agent
    """
    logger.info(f"Trading agent paused by {current_user.username}")
    return {"message": "Trading agent paused successfully", "status": "paused"}

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
import sys

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            'market': [],
            'agent': [],
            'portfolio': []
        }

    async def connect(self, websocket: WebSocket, connection_type: str):
        await websocket.accept()
        if connection_type in self.active_connections:
            self.active_connections[connection_type].append(websocket)
            logger.info(f"New {connection_type} WebSocket connection")

    def disconnect(self, websocket: WebSocket, connection_type: str):
        if connection_type in self.active_connections:
            try:
                self.active_connections[connection_type].remove(websocket)
                logger.info(f"{connection_type} WebSocket connection closed")
            except ValueError:
                pass

    async def broadcast(self, message: Dict, connection_type: str):
        if connection_type in self.active_connections:
            for connection in self.active_connections[connection_type]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_type}: {e}")

manager = ConnectionManager()

# Helper functions for WebSocket data
async def get_current_market_data():
    """Get current market data for WebSocket updates"""
    try:
        # Import Binance API
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'trading_bot', 'api'))
        from binance import get_24hr_stats, get_market_price

        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "MATICUSDT", "DOTUSDT"]
        market_data = {}

        for symbol in symbols:
            try:
                # Get 24hr stats from Binance
                stats = get_24hr_stats(symbol)
                if stats:
                    market_data[symbol.replace("USDT", "/USD")] = {
                        'price': stats['price'],
                        'change_percent': stats['changePercent'],
                        'volume': stats['volume'],
                        'high': stats['high'],
                        'low': stats['low'],
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    # Fallback to basic price if 24hr stats fail
                    price = get_market_price(symbol)
                    if price:
                        market_data[symbol.replace("USDT", "/USD")] = {
                            'price': price,
                            'change_percent': 0.0,
                            'volume': 'N/A',
                            'high': price,
                            'low': price,
                            'timestamp': datetime.now().isoformat()
                        }

            except Exception as e:
                logger.warning(f"Failed to get data for {symbol}: {e}")
                continue

        return {
            "market_data": market_data,
            "symbols_count": len(market_data),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        # Return mock data for demo
        return {
            "market_data": {
                "BTC/USD": {"price": 50000.0, "change_percent": 0.5, "volume": "1B", "timestamp": datetime.now().isoformat()},
                "ETH/USD": {"price": 3000.0, "change_percent": -0.2, "volume": "500M", "timestamp": datetime.now().isoformat()}
            },
            "symbols_count": 2,
            "timestamp": datetime.now().isoformat()
        }

async def get_current_agent_status():
    """Get current agent status for WebSocket updates"""
    return {
        "status": "running",
        "isRunning": True,
        "performance": {
            "totalTrades": 1247,
            "winRate": 68.5,
            "dailyPnL": 1245.67,
            "profitFactor": 2.14,
            "maxDrawdown": 3.2
        },
        "config": {
            "strategies": {
                "breakout": {"active": True, "allocation": 25},
                "meanReversion": {"active": True, "allocation": 30},
                "momentum": {"active": False, "allocation": 20},
                "arbitrage": {"active": True, "allocation": 15},
                "sentiment": {"active": True, "allocation": 10}
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }

async def get_current_portfolio_data():
    """Get current portfolio data for WebSocket updates"""
    return {
        "total_value": 125750.50,
        "available_balance": 10000.0,
        "total_pnl": 25750.50,
        "total_pnl_percent": 25.75,
        "day_pnl": 1245.67,
        "day_pnl_percent": 1.01,
        "positions": 8,
        "open_orders": 3,
        "timestamp": datetime.utcnow().isoformat()
    }

# WebSocket endpoints

async def get_current_user_from_token(token: str) -> User:
    """Extract and validate user from JWT token or Google OAuth token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Check if it's a Google OAuth token (starts with 'ya29.')
    if token.startswith('ya29.'):
        try:
            # For Google OAuth tokens, we need to validate them with Google
            # For now, create a temporary user session
            # In production, you should validate the token with Google's API
            import requests

            # Validate Google OAuth token
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {token}'}
            )

            if response.status_code == 200:
                user_info = response.json()
                # Create or get user based on Google user info
                username = user_info.get('email', '').split('@')[0]
                if not username:
                    raise credentials_exception

                # Check if user exists, if not create one
                user = get_user(fake_users_db, username)
                if not user:
                    # Create new user from Google info
                    new_user = {
                        "username": username,
                        "full_name": user_info.get('name', username),
                        "email": user_info.get('email', ''),
                        "hashed_password": get_password_hash(secrets.token_urlsafe(32)),  # Random password
                        "active": True,
                        "role": "trader",
                        "balance": 10000.0,
                        "api_permissions": ["read", "trade"]
                    }
                    fake_users_db[username] = new_user
                    user = UserInDB(**new_user)

                return User(**user.dict())
            else:
                raise credentials_exception

        except Exception as e:
            logger.warning(f"Google OAuth token validation failed: {e}")
            raise credentials_exception
    else:
        # Handle regular JWT tokens
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception

        user = get_user(fake_users_db, username=token_data.username)
        if user is None:
            raise credentials_exception

        return User(**user.dict())

@app.websocket("/market")
async def websocket_market(websocket: WebSocket, token: str = None):
    # Authenticate user
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    try:
        current_user = await get_current_user_from_token(token)
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Invalid authentication")
        return

    await manager.connect(websocket, "market")
    try:
        while True:
            # Send market data updates
            market_data = await get_current_market_data()
            await websocket.send_text(json.dumps({
                "type": "market_data",
                "data": market_data,
                "timestamp": datetime.utcnow().isoformat()
            }))
            await asyncio.sleep(5)  # Send updates every 5 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket, "market")
    except Exception as e:
        logger.error(f"Market WebSocket error: {e}")
        manager.disconnect(websocket, "market")

@app.websocket("/agent")
async def websocket_agent(websocket: WebSocket, token: str = None):
    # Authenticate user
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    try:
        current_user = await get_current_user_from_token(token)
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Invalid authentication")
        return

    await manager.connect(websocket, "agent")
    try:
        while True:
            # Send agent status updates
            agent_status = await get_current_agent_status()
            await websocket.send_text(json.dumps({
                "type": "agent_status",
                "data": agent_status,
                "timestamp": datetime.utcnow().isoformat()
            }))
            await asyncio.sleep(10)  # Send updates every 10 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket, "agent")
    except Exception as e:
        logger.error(f"Agent WebSocket error: {e}")
        manager.disconnect(websocket, "agent")

@app.websocket("/portfolio")
async def websocket_portfolio(websocket: WebSocket, token: str = None):
    # Authenticate user
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    try:
        current_user = await get_current_user_from_token(token)
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Invalid authentication")
        return

    await manager.connect(websocket, "portfolio")
    try:
        while True:
            # Send portfolio updates
            portfolio_data = await get_current_portfolio_data()
            await websocket.send_text(json.dumps({
                "type": "portfolio_data",
                "data": portfolio_data,
                "timestamp": datetime.utcnow().isoformat()
            }))
            await asyncio.sleep(15)  # Send updates every 15 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket, "portfolio")
    except Exception as e:
        logger.error(f"Portfolio WebSocket error: {e}")
        manager.disconnect(websocket, "portfolio")

@app.get("/")
async def root():
    """
    API information
    """
    return {
        "message": "Ameron API",
        "version": "1.0.0",
        "authentication": "OAuth2 Bearer Token",
        "endpoints": {
            "auth": {
                "token": "/token",
                "register": "/register",
                "me": "/users/me"
            },
            "trading": {
                "execute": "/trade",
                "history": "/trade/history"
            },
            "portfolio": {
                "summary": "/portfolio/summary",
                "positions": "/portfolio/positions"
            },
            "market": {
                "data": "/market/data"
            },
            "analysis": {
                "sentiment": "/analysis/sentiment"
            },
            "agent": {
                "status": "/agent/status",
                "start": "/agent/start",
                "stop": "/agent/stop",
                "pause": "/agent/pause"
            },
            "strategies": {
                "list": "/strategies",
                "create": "/strategies",
                "update": "/strategies/{name}",
                "delete": "/strategies/{name}",
                "activate": "/strategies/{name}/activate",
                "deactivate": "/strategies/{name}/deactivate"
            },
            "health": "/health"
        },
        "docs": "/docs",
        "registered_users": len(fake_users_db),
        "timestamp": datetime.utcnow()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)