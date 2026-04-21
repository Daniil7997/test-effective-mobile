from fastapi import (Depends,
                     HTTPException,
                     APIRouter,
                     status)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination import Page, Params
from fastapi_cache import JsonCoder
from fastapi_cache.decorator import cache

from app.dependencies.deps import (get_db,
                                   verify_access_token,
                                   check_admin)
from app.schemas.pydantic_schemas import (CreatePostReturn,
                                          DbUser,
                                          PostData,
                                          PostsFromDB,
                                          User,
                                          RegisterUser,
                                          AccessTokensPayload)
from app.repositories.crud import (create_user,
                                   create_post,
                                   read_posts)


router = APIRouter()


@router.post('/users',
             response_model=DbUser,
             status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: RegisterUser,
    db: AsyncSession = Depends(get_db),
    payload: AccessTokensPayload = Depends(verify_access_token)
) -> DbUser:
    data = User(user_uuid=payload.sub, username=user_data.username)
    try:
        db_data: DbUser = await create_user(db=db, data=data)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=[{"loc": "email",
                                     "msg": "Profile already exists",
                                     "type": "conflict"}])
    return db_data


@router.post('/posts',
             response_model=CreatePostReturn,
             status_code=status.HTTP_201_CREATED)
async def send_post(postdata: PostData,
                    db: AsyncSession = Depends(get_db),
                    payload: AccessTokensPayload = Depends(verify_access_token)
                    ) -> DbUser:
    try:
        new_post: CreatePostReturn = await create_post(db=db,
                                                       user_uuid=payload.sub,
                                                       data=postdata)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=[
                {
                    "loc": ["body", "user_uuid"],
                    "msg": "profile not created",
                    "type": "profile-not-created"
                }
            ]
        )
    return new_post


@router.get('/posts',
            response_model=Page[PostsFromDB],
            status_code=status.HTTP_200_OK)
@cache(expire=300, namespace='get-posts', coder=JsonCoder)
async def get_posts(params: Params = Depends(),
                    db: AsyncSession = Depends(get_db)):
    db_data = await read_posts(db=db, params=params)
    return db_data


@router.get('/secrets',
            status_code=status.HTTP_200_OK,
            dependencies=[Depends(check_admin)])
async def secret():
    return 'secret'
