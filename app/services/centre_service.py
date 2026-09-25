"""
Diagnostic Centre & Test Service
"""

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.models.centre import DiagnosticCentre, DiagnosticTest


def get_centres(db: Session) -> list[DiagnosticCentre]:
    """Get all diagnostic centres."""
    return db.query(DiagnosticCentre).all()


def get_centre_with_tests(db: Session, centre_id: str) -> DiagnosticCentre:
    """Get a centre by ID with its associated tests."""
    centre = (
        db.query(DiagnosticCentre)
        .options(joinedload(DiagnosticCentre.tests))
        .filter(DiagnosticCentre.id == centre_id)
        .first()
    )
    if not centre:
        raise HTTPException(status_code=404, detail="Diagnostic centre not found")
    return centre


def get_test(db: Session, test_id: str) -> DiagnosticTest:
    """Get a specific test by ID."""
    test = db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Diagnostic test not found")
    return test
