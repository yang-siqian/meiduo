import re

from django.contrib.auth.backends import ModelBackend

from .models import User


def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义jwt认证成功返回数据
    """
    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }


def get_user_by_account(account):
    """
    根据账号查询用户对象
    :param account: 账号：username or mobile
    :return: none or User
    """
    try:
        # 账号为手机号
        if re.match('^1[3-9]\d{9}$',account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user





class UsernameMobileAuthBackend(ModelBackend):
    """自定义用户名和密码认证"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 根据账号查询用户对象  账号：用户名或手机号
        user = get_user_by_account(username)
        # 将密码传给check_password验证
        if user is not None and user.check_password(password):
            return user
