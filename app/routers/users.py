from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user
from app.models import User
from app.schemas import UserOut
from app.utils.file_upload import save_upload

router = APIRouter()


@router.get("/me", response_model=UserOut)
def get_me(user: current_user):
    return user


@router.post("/me/profile-image", response_model=UserOut)
async def upload_profile_image(
    file: UploadFile,
    user: current_user,
    db: Session = Depends(get_db),
):
    url = await save_upload(file, "profile")
    user.profile_image = url
    db.commit()
    db.refresh(user)
    return user
