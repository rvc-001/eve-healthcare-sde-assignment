"""
Seed script for Diagnostic Centres and Tests.
Populates the database with test centres in Raipur, Bhilai, and Durg (CG).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.centre import DiagnosticCentre, DiagnosticTest, TestSlot


def seed_data():
    db: Session = SessionLocal()

    # Centres data (Raipur, Bhilai, Durg - CG)
    centres_data = [
        {
            "name": "Main Diagnostic Hub",
            "location": "GE Road, Raipur, CG",
            "tests": [
                {"name": "Complete Blood Count (CBC)", "description": "Measures different features of your blood.", "price": Decimal("350.00")},
                {"name": "Thyroid Profile", "description": "T3, T4, and TSH levels.", "price": Decimal("600.00")},
                {"name": "Lipid Profile", "description": "Cholesterol and triglyceride levels.", "price": Decimal("750.00")}
            ]
        },
        {
            "name": "Apollo Diagnostics",
            "location": "Supela, Bhilai, CG",
            "tests": [
                {"name": "Complete Blood Count (CBC)", "description": "Basic blood test panel.", "price": Decimal("300.00")},
                {"name": "Diabetes Screening (HbA1c)", "description": "Average blood sugar level over 3 months.", "price": Decimal("500.00")},
                {"name": "Vitamin D Total", "description": "Vitamin D levels in blood.", "price": Decimal("1200.00")}
            ]
        },
        {
            "name": "Pathkind Labs",
            "location": "Station Road, Durg, CG",
            "tests": [
                {"name": "Liver Function Test (LFT)", "description": "Assess liver health.", "price": Decimal("850.00")},
                {"name": "Kidney Function Test (KFT)", "description": "Assess kidney health.", "price": Decimal("900.00")},
                {"name": "Thyroid Profile", "description": "Comprehensive thyroid test.", "price": Decimal("550.00")}
            ]
        }
    ]

    print("🌱 Starting database seed...")

    for centre_info in centres_data:
        # Check if centre already exists
        existing_centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.name == centre_info["name"]).first()
        if not existing_centre:
            centre = DiagnosticCentre(name=centre_info["name"], location=centre_info["location"])
            db.add(centre)
            db.commit()
            db.refresh(centre)
            print(f"Created centre: {centre.name}")

            for test_info in centre_info["tests"]:
                test = DiagnosticTest(
                    centre_id=centre.id,
                    name=test_info["name"],
                    description=test_info["description"],
                    price=test_info["price"]
                )
                db.add(test)
                db.commit()
                db.refresh(test)
                
                # Generate 3 dummy slots for each test
                base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
                for i in range(3):
                    slot = TestSlot(
                        test_id=test.id,
                        start_time=base_time + timedelta(hours=i),
                        end_time=base_time + timedelta(hours=i, minutes=45),
                        is_booked=False
                    )
                    db.add(slot)
            
            db.commit()
            print(f"  └ Added {len(centre_info['tests'])} tests with time slots.")
        else:
            print(f"Centre '{centre_info['name']}' already exists, checking for missing slots.")
            tests = db.query(DiagnosticTest).filter(DiagnosticTest.centre_id == existing_centre.id).all()
            for test in tests:
                slots_count = db.query(TestSlot).filter(TestSlot.test_id == test.id).count()
                if slots_count == 0:
                    base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
                    for i in range(3):
                        slot = TestSlot(
                            test_id=test.id,
                            start_time=base_time + timedelta(hours=i),
                            end_time=base_time + timedelta(hours=i, minutes=45),
                            is_booked=False
                        )
                        db.add(slot)
            db.commit()

    db.close()
    print("✅ Seed complete!")

if __name__ == "__main__":
    seed_data()
