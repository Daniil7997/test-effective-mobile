from fastapi import (Depends,
                     HTTPException,
                     APIRouter,
                     status)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.deps import (get_db,
                                   verify_access_token,
                                   verify_refresh_token)
from app.schemas.pydantic_schemas import (AccessTokensPayload,
                                          RefreshTokensPayload,
                                          DbUserData,
                                          User,
                                          CreateUserResponse,
                                          GetTokens,
                                          ChangeUserData,
                                          AccessToken,
                                          ConfirmAction)
from app.repositories.crud import (create_user,
                                   find_user_by_email,
                                   find_user_by_uuid,
                                   change_user_data)
from app.core.security import (verify_password,
                               create_tokens,
                               hash_password)


router = APIRouter()


@router.post('/accounts',
             response_model=CreateUserResponse,
             status_code=status.HTTP_201_CREATED)
async def register_user(
        user: User,
        db: AsyncSession = Depends(get_db)) -> CreateUserResponse:
    try:
        new_user = await create_user(db, user)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=[{"loc": "email",
                                     "msg": "Email already exists",
                                     "type": "conflict"}])
    return CreateUserResponse(email=new_user.email,
                              user_uuid=new_user.user_uuid)


@router.patch('/accounts',
              status_code=status.HTTP_200_OK)
async def change_password(
    user_data: ChangeUserData,
    payload: AccessTokensPayload = Depends(verify_access_token),
    db: AsyncSession = Depends(get_db)
):
    async with change_user_data(db=db, user_uuid=payload.sub) as db_user:
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=[{"loc": ["header", "Authorization"],
                         "msg": "User with this token does not exists",
                         "type": "user-dont-exist"}]
                                )
        check_password: bool = verify_password(
            raw_password=user_data.current_password,
            hash_password=db_user[0].password
            )
        if not check_password:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=[{"loc": ["body", "password"],
                         "msg": "The passwords don't match",
                         "type": "access-denied"}]
                                )
        db_user[0].password = hash_password(user_data.new_data.password)
        return {"detail": "Password updated successfully"}


@router.delete('/accounts',
               status_code=status.HTTP_200_OK)
async def soft_delete_user(
    user_data: ConfirmAction,
    payload: AccessTokensPayload = Depends(verify_access_token),
    db: AsyncSession = Depends(get_db)
):
    async with change_user_data(db=db, user_uuid=payload.sub) as db_user:
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=[{"loc": ["header", "Authorization"],
                         "msg": "User with this token does not exists",
                         "type": "user-dont-exist"}]
                                )
        check_password: bool = verify_password(
            raw_password=user_data.password,
            hash_password=db_user[0].password
            )
        if not check_password:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=[{"loc": ["body", "password"],
                         "msg": "The passwords don't match",
                         "type": "access-denied"}]
                                )
        db_user[0].is_active = False
        return {"detail": "User deleted successfully"}


@router.post('/tokens',
             response_model=GetTokens,
             status_code=status.HTTP_200_OK)
async def get_tokens(user_data: User,
                     db: AsyncSession = Depends(get_db)) -> GetTokens:
    user_db_data = await find_user_by_email(db=db,
                                            user_email=user_data.email)
    exception_detail = [{"loc": ["email", "password"],
                         "msg": "Invalid password or email",
                         "type": "auth-failed"}]
    if not user_db_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=exception_detail,
                            headers={"WWW-Authenticate": "Bearer"})

    check_password: bool = verify_password(
        raw_password=user_data.password,
        hash_password=user_db_data.password
        )
    if not check_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=exception_detail,
                            headers={"WWW-Authenticate": "Bearer"})
    return create_tokens(user_db_data.user_uuid,
                         user_db_data.role)


@router.post('/refresh',
             response_model=AccessToken,
             status_code=200)
async def refresh(
    refresh_payload: RefreshTokensPayload = Depends(verify_refresh_token),
    db: AsyncSession = Depends(get_db)
):
    db_user: DbUserData = await find_user_by_uuid(
        db=db,
        user_uuid=refresh_payload.sub
                                                  )
    new_tokens: GetTokens = create_tokens(user_uuid=refresh_payload.sub,
                                          role=db_user.role)
    access_token = AccessToken(token=new_tokens.access_token)
    return access_token
