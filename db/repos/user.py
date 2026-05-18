def batch_save_users(
    users: List[UserDto],
    session: Session,
    on_conflict: str = "nothing"
) -> int:
    """
    Batch insert/update users.
    
    Args:
        users: List of UserSchema objects
        session: SQLAlchemy session
        on_conflict: "nothing" (ignore duplicates) or "update" (update on conflict)
    
    Returns:
        Number of rows inserted/updated
    
    Example:
        users = [
            UserSchema(user_id=123, telegram_username="john", resume_text="..."),
            UserSchema(user_id=456, telegram_username="sara", resume_text="...")
        ]
        batch_save_users(users, session)
    """
    if not users:
        return 0
    
    user_dicts = [u.model_dump(exclude={"created_at"}, exclude_none=True) for u in users]
    
    stmt = pg_insert(User).values(user_dicts)
    
    if on_conflict == "update":
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id"],
            set_={
                "telegram_username": stmt.excluded.telegram_username,
                "resume_text": stmt.excluded.resume_text,
                "is_active": stmt.excluded.is_active,
            }
        )
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=["user_id"])
    
    result = session.execute(stmt)
    session.commit()
    return result.rowcount


def get_users(
    session: Session,
    user_id: Optional[int] = None,
    telegram_username: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None
) -> List[UserDto]:
    """
    Get users with optional filters.
    
    Args:
        session: SQLAlchemy session
        user_id: Filter by specific user_id
        telegram_username: Filter by telegram username
        is_active: Filter by active status (True/False/None for all)
        limit: Maximum number of results
    
    Returns:
        List of UserSchema objects
    
    Examples:
        get_users(session)  # all users
        get_users(session, is_active=True)  # only active users
        get_users(session, user_id=123)  # specific user
    """
    query = session.query(User)
    
    if user_id is not None:
        query = query.filter(User.user_id == user_id)
    
    if telegram_username is not None:
        query = query.filter(User.telegram_username == telegram_username)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if limit is not None:
        query = query.limit(limit)
    
    rows = query.all()
    return [UserDto.model_validate(row) for row in rows]

