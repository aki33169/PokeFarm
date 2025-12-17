import hashlib
import os

# 生成随机盐
def generate_salt(length=16):
    return os.urandom(length).hex()

# 计算密码哈希
def hash_password(password: str, salt: str):
    return hashlib.sha256((password + salt).encode()).hexdigest()