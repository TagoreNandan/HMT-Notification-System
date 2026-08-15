from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from db.models import User

router = APIRouter(tags=["account"])


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    db.delete(current_user)
    db.commit()
