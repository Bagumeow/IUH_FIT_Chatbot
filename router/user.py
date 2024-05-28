from tools.tools import *
# from tools import *
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone

router = APIRouter()


class UserCreate(BaseModel):
    email: str
    password: str
    user_name: str
    full_name:  str
    phone_number : Union[str, None] = None
    avatar : Union[str, None] = None
    gender : Union[bool, None] = None

class RegisterResponse(BaseModel):
    status: bool

@router.post("/register", response_model=RegisterResponse, status_code = status.HTTP_201_CREATED)
async def register(user : UserCreate):
    conn = create_connection()
    cursor = create_cursor(conn)

    if check_dupliate_username_or_email(conn, user.email, user.user_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tài Khoản hoặc Email đã tồn tại!!!")
    
    table_name = "users"
    columns = "email, hashed_password, user_name, full_name, phone_number, avatar, gender"
    insert_query = f"INSERT INTO {table_name} ({columns}) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    data_insert = (user.email, get_password_hash(user.password), user.user_name, user.full_name, user.phone_number, user.avatar, user.gender)
    cursor.execute(insert_query, data_insert)

    conn.commit()
    _,result = get_user(conn, user.email)
    conn.close()
    return {
        "status": bool(result)
    }

class Login(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login_for_access_token(from_data : Login):
    conn=create_connection()
    user = authenticate_user(conn, from_data.email, from_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    conn.close()
    return {"access_token": access_token, "token_type": "bearer"}


# if __name__ == "__main__":
#     import uvicorn
#     app = FastAPI()
#     app.include_router(router)
#     uvicorn.run(app, host="0.0.0.0", port=5000)