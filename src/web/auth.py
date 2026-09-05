"""用户注册 / 登录认证服务。

密码使用 PBKDF2-HMAC-SHA256 加盐哈希存储，不保存明文。
"""
import hashlib
import logging
import re
import secrets
from typing import Optional, Tuple

from sqlalchemy import select

from storage.database.db import get_engine, get_session
from storage.database.models.user import User
from storage.database.shared.model import Base

logger = logging.getLogger(__name__)

# 游客账号（默认展示在登录框的灰色提示中）
GUEST_USERNAME = "youke"
GUEST_PASSWORD = "123456"

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_\u4e00-\u9fa5]{2,32}$")
_PBKDF2_ITERATIONS = 100_000


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """生成带盐的密码哈希，格式为 `salt$digest`。"""
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PBKDF2_ITERATIONS,
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """校验密码是否与已存储的哈希匹配。"""
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return secrets.compare_digest(hash_password(password, salt), stored)


def init_auth() -> None:
    """建表并初始化默认游客账号（幂等）。"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    session = get_session()
    try:
        exists = session.execute(
            select(User).where(User.username == GUEST_USERNAME)
        ).scalar_one_or_none()
        if exists is None:
            session.add(
                User(
                    username=GUEST_USERNAME,
                    password_hash=hash_password(GUEST_PASSWORD),
                )
            )
            session.commit()
            logger.info("guest account '%s' created", GUEST_USERNAME)
    finally:
        session.close()


def register_user(username: str, password: str) -> Tuple[bool, str]:
    """注册新用户。返回 (是否成功, 提示信息)。"""
    username = (username or "").strip()
    if not _USERNAME_RE.match(username):
        return False, "用户名需为 2-32 位，仅支持中英文、数字、下划线"
    if not password or len(password) < 6 or len(password) > 64:
        return False, "密码长度需在 6-64 位之间"

    session = get_session()
    try:
        exists = session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        if exists is not None:
            return False, "该用户名已被注册"
        session.add(User(username=username, password_hash=hash_password(password)))
        session.commit()
        return True, "注册成功"
    except Exception as exc:  # noqa: BLE001
        logger.error("register failed: %s", exc)
        session.rollback()
        return False, "注册失败，请稍后重试"
    finally:
        session.close()


def login_user(username: str, password: str) -> Tuple[bool, str]:
    """登录校验。返回 (是否成功, 提示信息)。"""
    username = (username or "").strip()
    if not username or not password:
        return False, "请输入用户名和密码"

    session = get_session()
    try:
        user = session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        if user is None:
            return False, "用户名或密码错误"
        if not verify_password(password, user.password_hash):
            return False, "用户名或密码错误"
        return True, "登录成功"
    finally:
        session.close()