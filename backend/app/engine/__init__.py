"""
Security intelligence engines for CloudContextGuard.

Each engine is a pure function: it accepts plain, already-resolved inputs
(no database session, no ORM objects) and returns a structured, explainable
result. Database resolution and orchestration live in ``app.services``.
"""
