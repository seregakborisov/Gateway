from typing import Annotated

import httpx
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response

app = FastAPI()

USERS_URL = "http://127.0.0.1:8000"
LESSONS_URL = "http://127.0.0.1:8001"

bearer_scheme = HTTPBearer()


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

    return response.json()

def teacher_or_admin(current_user: dict):
    if current_user["role"] not in ("Teacher", "Admin"):
        raise HTTPException(
            status_code=403,
            detail="Вы не админ",
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
                **({"Authorization": "Bearer " + token} if token else {})})

    return Response(
        content=response.content,
        status_code=response.status_code,
    )

@app.get("/auth/check")
async def check_auth(
    current_user: Annotated[dict, Depends(get_verified_user)]):
    return current_user


@app.post("/users/token")
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

