import re

from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User
from . import serializers
from verifications.serializers import ImageCodeCheckSerializer
from .utils import get_user_by_account





class UserView(CreateAPIView):
    """用户注册"""

    serializer_class = serializers.CreateUserSerializer


class UsernameCountView(APIView):
    """用户名数量"""

    def get(self, request, username):
        """获取指定用户名的数量"""
        count = User.objects.filter(username=username).count()
        data = {
            'username': username,
            'count': count
        }
        return Response(data)


class MobileCountView(APIView):
    """手机号数量"""

    def get(self, request, mobile):
        """获取手机号数量"""
        count = User.objects.filter(mobile=mobile)
        data = {
            'mobile': mobile,
            'count': count
        }
        return Response(data)

class SMSCodeTokenView(GenericAPIView):
    """根据账号和图片验证码获取发送短信的token"""
    # 校验图片验证码
    serializer_class = ImageCodeCheckSerializer
    def get(self, request, account):
        # 根据账号获取User对象
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        user = get_user_by_account(account)

        if user is None:
            return Response({'message':'用户不存在'},status=status.HTTP_404_NOT_FOUND)
        # 生成acess_token
        access_token = user.generate_send_sms_token()
        # 处理手机号
        mobile = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', user.mobile)
        return Response({'mobile': mobile, 'access_token': access_token})



class PasswordTokenView(GenericAPIView):
    """用户账号设置密码的token"""

    serializer_class = serializers.CheckSMSCodeSerializer
    def get(self, request, account):
        """
        根据用户帐号获取修改密码的token
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = serializer.user

        # 生成修改用户密码的access token
        access_token = user.generate_set_password_token()

        return Response({'user_id': user.id, 'access_token': access_token})














