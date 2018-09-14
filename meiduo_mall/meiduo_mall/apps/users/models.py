from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSerializer, BadData
from . import constants

# Create your models here.
class User(AbstractUser):
    """用户模型类"""
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def generate_send_sms_token(self):
        """
        生成短信验证access_token
        :return: token
        """
        serializer = TJWSerializer(settings.SECRET_KEY, constants.SEND_SMS_CODE_TOKEN_EXPIRES)
        data = {
            'mobile': self.mobile
        }
        token = serializer.dumps(data)
        token = token.decode()    # 加密
        return token

    @staticmethod
    def check_send_sms_token(token):
        """
        校验短信验证access_token
        :return: None/mobile
        """
        serializer = TJWSerializer(settings.SECRET_KEY, constants.SEND_SMS_CODE_TOKEN_EXPIRES)
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            mobile = data.get('mobile')
            return mobile