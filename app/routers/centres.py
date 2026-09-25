"""
Diagnostic Centres Router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.centre import DiagnosticCentreResponse, CentreWithTestsResponse, DiagnosticTestResponse
from app.services import centre_service
from app.utils.response import send_response

from fastapi_cache.decorator import cache

router = APIRouter(prefix="/centres", tags=["Centres & Tests"])


@router.get("/", summary="List all diagnostic centres")
@cache(expire=60)
def list_centres(db: Session = Depends(get_db)):
    """Retrieve a list of all available diagnostic centres."""
    centres = centre_service.get_centres(db)
    return send_response(
        success=True,
        message="Centres retrieved successfully.",
        data=[DiagnosticCentreResponse.model_validate(c).model_dump() for c in centres]
    )


@router.get("/{centre_id}", summary="Get centre details with tests")
def get_centre_details(centre_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific diagnostic centre, including all the tests it offers."""
    centre = centre_service.get_centre_with_tests(db, centre_id)
    return send_response(
        success=True,
        message="Centre details retrieved successfully.",
        data=CentreWithTestsResponse.model_validate(centre).model_dump()
    )


@router.get("/tests/{test_id}", summary="Get diagnostic test details")
def get_test_details(test_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific diagnostic test."""
    test = centre_service.get_test(db, test_id)
    return send_response(
        success=True,
        message="Test details retrieved successfully.",
        data=DiagnosticTestResponse.model_validate(test).model_dump()
    )
