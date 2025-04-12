import json
import os
import uuid

import gotrue.errors
import jwt
from starlette import status
from supabase import create_client, Client
from fastapi import HTTPException, Security, Depends, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database.postgres import get_postgres_connection, insert_query
from database.redis import get_redis_client
from models.Models import User, RefreshRequest, AuthUser, ResendOTPRequest, ResetPasswordRequest, UpdatePasswordRequest
import logging
from utils.aws_utils import get_secret
from utils.supabase_utils import validate_supabase_credentials

# Set up logging
logger = logging.getLogger(__name__)

# Get Supabase secret name from environment variable
supabase_secret_name = os.getenv("supabase_secret_name")
if not supabase_secret_name:
    raise RuntimeError("Missing environment variable: supabase_secret_name")

# Retrieve credentials from AWS Secrets Manager
try:
    supabase_values = get_secret(supabase_secret_name)
    logger.info(f"Retrieved Supabase credentials from AWS Secrets Manager")
    
    # Validate the structure and format of the credentials
    is_valid, validation_message = validate_supabase_credentials(supabase_values)
    
    if not is_valid:
        logger.error(f"Supabase credential validation failed: {validation_message}")
        raise ValueError(f"Invalid Supabase credentials: {validation_message}")
    
    logger.info(f"Supabase credentials validated: {validation_message}")
    
    # Initialize Supabase client with validated credentials
    SUPABASE_URL = supabase_values["SUPABASE_URL"]
    SUPABASE_KEY = supabase_values["SUPABASE_SERVICE_ROLE_KEY"]
    JWT_SECRET = supabase_values["JWT_SECRET"]
    
    # Log credential details (safely)
    logger.info(f"Using Supabase URL: {SUPABASE_URL}")
    logger.info(f"API Key length: {len(SUPABASE_KEY)} characters")
    logger.info(f"JWT Secret length: {len(JWT_SECRET)} characters")
    
except Exception as e:
    logger.critical(f"Failed to initialize Supabase credentials: {str(e)}", exc_info=True)
    raise

# Confirm requirements are met
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and API key are required")

SUPABASE_JWT_SECRET = JWT_SECRET
if SUPABASE_JWT_SECRET is None:
    raise ValueError("JWT_SECRET is required")

auth_scheme = HTTPBearer()
router = APIRouter()

# Initialize Supabase client with robust error handling
try:
    logger.info(f"Initializing Supabase client with URL: {SUPABASE_URL}")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully")
    
    # Optional: Make a simple query to verify the connection works
    try:
        result = supabase.table("users").select("count").limit(1).execute()
        logger.info(f"Supabase connection test successful")
    except Exception as query_error:
        logger.warning(f"Supabase connection test query failed: {str(query_error)}")
        # Continue anyway as this is just a verification
except Exception as e:
    logger.critical(f"Failed to initialize Supabase client: {str(e)}", exc_info=True)
    raise RuntimeError(f"Supabase initialization failed: {str(e)}")


def validate_token(auth: HTTPAuthorizationCredentials = Security(auth_scheme)) -> User:
    token = auth.credentials
    try:
        logger.info("Validating JWT token...")

        # Decode the JWT and verify claims
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )

        # Verify audience manually (Supabase default is 'authenticated')
        if payload.get("aud") != "authenticated":
            logger.warning("Invalid token: Incorrect audience")
            raise HTTPException(status_code=401, detail="Invalid token: Invalid audience")

        # Extract user details
        user_id = payload.get("sub")
        email = payload.get("email")
        print(f"user id: {user_id} email: {email}")
        if not user_id:
            logger.error("Token validation failed: Missing user_id")
            raise HTTPException(status_code=400, detail="Token payload is missing required fields")

        # Ensure at least one identifier is present (email or phone)
        if not email:
            logger.error("Token validation failed: Missing email")
            raise HTTPException(status_code=400, detail="Token must contain email")

        # Fetch profile data from Supabase
        try:
            user_id = str(user_id).strip()
            response = supabase.table("users").select("*").eq("id", user_id).limit(1).execute()
            profile = response.data
        except Exception as e:
            logger.error(f"Failed to fetch user profile for {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch user profile")

        if not profile:
            logger.warning(f"User {user_id} authenticated but no profile found.")
            raise HTTPException(status_code=404, detail="User profile not found")

        logger.info(f"User {user_id} successfully validated.")
        return User(
            id=user_id,
        )
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.critical(f"Unexpected error during token validation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected server error during token validation")



@router.post("/signup")
async def signup(request: AuthUser):
    """Sign up a new user via Supabase and store them in PostgreSQL"""
    try:
        logger.info(f"User signup attempt for email: {request.email}")
        redis = await get_redis_client()

        # Signup request to Supabase
        try:
            response = supabase.auth.sign_up({"email": request.email, "password": request.password})
            logger.info(f"Supabase response: {response}")
        except Exception as e:
            logger.error(f"Supabase signup failed for {request.email}: {str(e)}")
            raise HTTPException(status_code=400, detail="Signup failed due to Supabase error")

        # Extract user details
        user = response.user
        if not user:
            logger.warning(f"Signup failed for {request.email}: No user returned from Supabase")
            raise HTTPException(status_code=400, detail="Signup failed, user not created")

        user_id = user.id
        email = user.email
        session = response.session
        access_token = session.access_token if session else None
        refresh_token = session.refresh_token if session else None

        # Store user details in PostgreSQL
        query = """
            INSERT INTO users (
                id, email, role, firstname, lastname
            ) VALUES (
                $1, $2, $3, $4, $5
            ) ON CONFLICT (id) DO NOTHING
        """
        try:
            await insert_query(query, user_id, email, request.role, request.firstname, request.lastname)
            logger.info(f"User {user_id} successfully stored in database")
        except Exception as e:
            logger.error(f"Database insert failed for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error during signup")

        # Store session in Redis if session exists
        if access_token:
            try:
                await redis.setex(f"session:{user_id}", 3600, access_token)
                await redis.setex(f"refresh:{user_id}", 86400, refresh_token)
                logger.info(f"Session stored in Redis for user {user_id}")
            except Exception as e:
                logger.error(f"Redis storage failed for user {user_id}: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to store session in Redis")

        return {
            "message": "User registered successfully. Please check your email to confirm your account.",
            "access_token": access_token if access_token else None,
            "requires_confirmation": session is None
        }

    except Exception as e:
        logger.critical(f"Unexpected error during signup: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected server error during signup")


@router.post("/resend-otp")
async def resend_otp(request: ResendOTPRequest):
    """Resends OTP for email verification in Supabase"""
    try:
        logger.info(f"Resending OTP for email: {request.email}")

        # Resend OTP request to Supabase
        try:
            response = supabase.auth.resend({
                "type": "signup",
                "email": request.email,
                # TODO: Add email redirect option if needed
                # "options": {"email_redirect_to": EMAIL_REDIRECT_URL},
            })
            logger.info(f"Supabase OTP resend response: {response}")
        except Exception as e:
            logger.error(f"Failed to resend OTP for {request.email}: {str(e)}")
            raise HTTPException(status_code=500, detail="Supabase OTP resend failed")

        return {"message": "Verification email has been resent. Please check your inbox."}

    except gotrue.errors.AuthApiError as e:
        logger.warning(f"Auth API error while resending OTP: {str(e)}")

        if "User not found" in str(e):
            raise HTTPException(status_code=404, detail="User not found. Please sign up first.")
        elif "Email already confirmed" in str(e):
            raise HTTPException(status_code=400, detail="Email is already verified.")
        elif "Too many requests" in str(e):
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

        raise HTTPException(status_code=500, detail="Failed to resend verification email.")

    except Exception as e:
        logger.critical(f"Unexpected error during OTP resend: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error during OTP resend")


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Sends a password reset email via Supabase with custom redirect URL"""
    try:
        # The redirect_to parameter should be your backend endpoint that will handle the token
        # This endpoint should extract the token from the URL and present a form for the new password
        response = supabase.auth.reset_password_for_email(
            request.email,
            options={
                "redirect_to": f"{os.environ.get('BACKEND_URL', 'http://localhost:8000')}/auth/password-reset-form"
            }
        )
        # Note: For security, we don't confirm if the email exists or not
        return {"success": True,
                "message": "If your email exists in our system, you will receive a password reset link."}

    except gotrue.errors.AuthApiError as e:
        # Log the error but don't expose specifics to the client
        print(f"Auth error during password reset: {str(e)}")

        if "Too many requests" in str(e):
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

        # Generic message for other auth errors to prevent email enumeration
        return {"success": True,
                "message": "If your email exists in our system, you will receive a password reset link."}

    except Exception as e:
        print(f"Unexpected error during password reset: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/confirm-reset", status_code=status.HTTP_200_OK)
async def confirm_reset(request: UpdatePasswordRequest):
    """
    Handles password reset using Supabase session tokens.

    This endpoint expects the access_token and refresh_token obtained from the reset link,
    along with the new password to set for the user account.
    """
    try:
        # Set the Supabase session with the provided tokens
        supabase.auth.set_session(request.access_token, request.refresh_token)

        # Update the user's password
        response = supabase.auth.update_user(
            {"password": request.new_password}
        )

        # Check if the response contains a user object to confirm success
        if not response or not getattr(response, 'user', None):
            logger.warning(f"Password reset failed for {request.email}: No user in response")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password update failed. Please try again or request a new reset link."
            )

        logger.info(f"Password reset successful for user {request.email}")
        return {
            "success": True,
            "message": "Password has been successfully updated. You can now log in with your new password."
        }

    except gotrue.errors.AuthApiError as auth_error:
        # Handle Supabase auth-specific errors
        error_message = str(auth_error)
        logger.error(f"Auth API error during password reset: {error_message}")

        if "token is invalid" in error_message.lower() or "token expired" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your reset link has expired or is invalid. Please request a new password reset link."
            )
        elif "password" in error_message.lower():
            # Handle password policy errors
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet security requirements. Please choose a stronger password."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reset password. Please try again."
            )
    except Exception as e:
        # Handle any unexpected errors
        logger.error(f"Unexpected error during password reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request. Please try again later."
        )


@router.post("/login")
async def login(request: AuthUser, connection=Depends(get_postgres_connection)):
    """Authenticate user via Supabase, fetch user details from PostgreSQL, and store session in Redis."""
    try:
        logger.info(f"Login attempt for email: {request.email}")
        redis = await get_redis_client()

        # Authenticate with Supabase
        try:
            response = supabase.auth.sign_in_with_password({"email": request.email, "password": request.password})
            logger.info(f"Supabase response: {response}")
        except gotrue.errors.AuthApiError as e:
            logger.error(f"Supabase authentication failed for {request.email}: {str(e)}")
            if "Email not confirmed" in str(e):
                raise HTTPException(status_code=403, detail="Email not confirmed. Please verify your email.")
            raise HTTPException(status_code=401, detail="Authentication failed. Check email and password.")

        user = response.user
        if not user:
            logger.warning(f"Authentication failed: No user found for email {request.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id = user.id
        email = user.email
        role = user.app_metadata.get("role", "authenticated")

        access_token = response.session.access_token
        refresh_token = response.session.refresh_token

        # Fetch full user details from PostgreSQL
        query = """
            SELECT id, email, role, firstname, lastname
            FROM users WHERE id = $1
        """
        try:
            user_record = await connection.fetchrow(query, user_id)
            if not user_record:
                logger.warning(f"User {user_id} authenticated but not found in database.")
                raise HTTPException(status_code=404, detail="User not found")
        except Exception as e:
            logger.error(f"Database query failed for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error occurred")

        user_data = {
            "user_id": user_id,
            "firstname": user_record["firstname"],
            "lastname": user_record["lastname"],
            "email": user_record["email"],
            "role": user_record["role"],
        }

        # Store user details in Redis
        try:
            await redis.setex(f"user:{user_id}", 86400, json.dumps(user_data))
            await redis.setex(f"session:{user_id}", 3600, access_token)
            await redis.setex(f"refresh:{user_id}", 86400, refresh_token)
            logger.info(f"User {user_id} session stored in Redis")
        except Exception as e:
            logger.error(f"Redis storage failed for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Session storage failed")

        logger.info(f"User {user_id} successfully logged in")
        return {
            "user": user_data,
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token
        }

    except HTTPException as e:
        logger.error(f"Login error for {request.email}: {e.detail}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during login: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected server error occurred")


@router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    """Refresh JWT session and keep user data in Redis"""
    redis = await get_redis_client()
    refresh_token = request.refresh_token

    try:
        logger.info("Refreshing token...")

        # Attempt to refresh session via Supabase
        try:
            response = supabase.auth.refresh_session(refresh_token)
            logger.info(f"Supabase response: {response}")
        except Exception as e:
            logger.error(f"Failed to refresh session with Supabase: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if not response or not response.session:
            logger.warning("Refresh token is invalid or session data missing")
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = response.session.access_token
        new_refresh_token = response.session.refresh_token
        user_id = response.user.id

        # Update Redis with new tokens
        try:
            await redis.setex(f"session:{user_id}", 3600, new_access_token)
            await redis.setex(f"refresh:{user_id}", 86400, new_refresh_token)
            logger.info(f"Refreshed tokens stored for user {user_id}")
        except Exception as e:
            logger.error(f"Redis storage failed for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update session in Redis")

        # Retrieve user data from Redis
        try:
            user_data_raw = await redis.get(f"user:{user_id}")
            if not user_data_raw:
                logger.warning(f"User data missing in Redis for user {user_id}")
                raise HTTPException(status_code=404, detail="User data not found")
        except Exception as e:
            logger.error(f"Redis retrieval failed for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve user data from Redis")

        logger.info(f"Token refresh successful for user {user_id}")
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "user": json.loads(user_data_raw)
        }

    except HTTPException as e:
        logger.error(f"Refresh token error: {e.detail}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during token refresh: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected server error occurred")


@router.get("/logout")
async def logout(user: User = Depends(validate_token)):
    """Logs out the user by deleting their session from Redis"""
    redis = await get_redis_client()
    user_id = user.id  # Extract user ID from the authenticated user

    try:
        logger.info(f"Logging out user {user_id}...")

        # Remove user data and tokens from Redis
        deleted_keys = await redis.delete(f"user:{user_id}", f"session:{user_id}", f"refresh:{user_id}")

        if deleted_keys > 0:
            logger.info(f"User {user_id} successfully logged out.")
        else:
            logger.warning(f"No session data found for user {user_id} during logout.")

        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Logout failed for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Logout failed due to server error")


@router.get("/user")
async def get_user_info(user: User = Depends(validate_token), connection = Depends(get_postgres_connection)):
    """
        Get user profile information
    """
    try:
        logger.info(f"Executing get user profile query for user {user.id}")

        sql = """
                Select * from users where id = $1;
              """
        get_user = await connection.fetchrow(sql, user.id)

        if not get_user:
            logger.error(f"User {user.id} updated successfully but no record found afterward.")
            raise HTTPException(status_code=404, detail="User not found after update")

        user_data = dict(get_user)
        if isinstance(user_data.get("id"), uuid.UUID):
            user_data["id"] = str(user_data["id"])
        return user_data
    except Exception as e:
        logger.critical(f"Unexpected error updating user {user.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error updating user profile")