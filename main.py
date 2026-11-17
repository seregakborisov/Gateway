from typing import Annotated

import httpx
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response

app = FastAPI()

USERS_URL = "http://127.0.0.1:8000"
LESSONS_URL = "http://127.0.0.1:8001"

bearer_scheme = HTTPBearer()


class UserSchema(BaseModel):
    username: str
    password: str    


class AddUserSchema(BaseModel):
    username: str
    password: str
    is_active: bool = True
    is_admin: bool = False
    balance: float = 0
    role: str


class UserUpdateSchema(BaseModel):
    username: str | None = None


class UserAdminSchema(BaseModel):
    username: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None
    balance: float | None = None

class LessonCreate(BaseModel):
    name: str
    mentor_id: int
    description: str | None = None
    is_active: bool = True



async def get_verified_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            USERS_URL + "/self",
            headers={
                "Authorization": "Bearer " + credentials.credentials
            },
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "Ошибка авторизации"),
        )

    return response.json()


async def teacher_or_admin(current_user: dict):
    if current_user["role"] not in ("Teacher", "Admin"):
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав",
        )


async def admin_only(current_user: dict):
    if current_user["role"] != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав",
        )


async def forward_request(
    url: str,
    request: Request,
    token: str = "",
):
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            params=request.query_params,
            content=await request.body(),
            headers={
                "Content-Type": request.headers.get("Content-Type", ""),
                **(
                    {"Authorization": "Bearer " + token}
                    if token else {}
                ),
            },
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers={
            "Content-Type": response.headers.get(
                "Content-Type", "application/json"
            )
        },
    )

@app.post("/users/get_token")
async def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            USERS_URL + "/token",
            data={
                "username": username,
                "password": password,
            },
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type"),
    )


@app.get("/auth/check")
async def check_auth(
    current_user: Annotated[dict, Depends(get_verified_user)],
):
    return current_user


@app.post("/users/registration")
async def registration(
    user_data: UserSchema,
    request: Request,
):
    return await forward_request(
        USERS_URL + "/registration",
        request,
    )


@app.post("/users/self")
async def users_self(
    request: Request,
    current_user: Annotated[dict, Depends(get_verified_user)],
):
    token = request.headers["Authorization"].replace("Bearer ", "")

    return await forward_request(
        USERS_URL + "/self",
        request,
        token,
    )

@app.get("/users/all_users")
async def users_get(
    request: Request,
    current_user: Annotated[dict, Depends(get_verified_user)],
):
    await teacher_or_admin(current_user)

    token = request.headers["Authorization"].replace("Bearer ", "")

    return await forward_request(
        USERS_URL + "/users",
        request,
        token,
    )


@app.post("/users/user_add")
async def users_add(
    user_data: AddUserSchema,
    request: Request,
    current_user: Annotated[dict, Depends(get_verified_user)],
):
    await admin_only(current_user)

    token = request.headers["Authorization"].replace("Bearer ", "")

    return await forward_request(
        USERS_URL + "/user_add",
        request,
        token,
    )

@app.put("/users/up_self")
async def users_up_self(
    user_data: UserSchema,
    request: Request,
    current_user: Annotated[dict, Depends(get_verified_user)],
):
    token = request.headers["Authorization"].replace("Bearer ", "")

    return await forward_request(
        USERS_URL + "/up_self",
        request,
        token,
    )


@app.put("/users/uppdate_admin")
async def users_update_admin(
    user_id: int,
    user_data: UserAdminSchema,
    request: Request,
    current_user: Annotated[dict, Depends(get_verified_user)],
):
    await admin_only(current_user)

    token = request.headers["Authorization"].replace("Bearer ", "")

    return await forward_request(
        USERS_URL + "/uppdate_admin",
        request,
        token,
    )


@app.delete("/users/deactivate")
async def users_deactivate(
    user_id: int,
    request: Request,
    current_user: Annotated[dict, Depends(get_verified_user)],
):
    await admin_only(current_user)

    token = request.headers["Authorization"].replace("Bearer ", "")

    return await forward_request(
        USERS_URL + "/deactivate",
        request,
        token,
    )



@app.get("/lessons/get_lessons")
async def lessons_get(request: Request,
    current_user: Annotated[dict, Depends(get_verified_user)],
):  
    
    token = request.headers["Authorization"].replace("Bearer ", "")

    return await forward_request(
        LESSONS_URL + "/all_lessons",
        request,
        token,
    )


@app.post("/lessons/create_lesson")
async def create_lesson(request: Request,
    lesson_data: LessonCreate,
    current_user: Annotated[dict, Depends(get_verified_user)],
):  
    await teacher_or_admin(current_user)

    token = request.headers["Authorization"].replace("Bearer ", "")

    return await forward_request(
        LESSONS_URL + "/create_lesson",
        request,
        token,
    )


@app.delete("/lessons/delete")
async def lesson_delete(
    current_user: Annotated[dict, Depends(get_verified_user)],
    request: Request,
    lesson_id: int):
    await teacher_or_admin(current_user)

    token = request.headers["Authorization"].replace("Bearer ", "")

    return await forward_request(
        LESSONS_URL + "/lesson_delete",
        request,
        token,
    )
