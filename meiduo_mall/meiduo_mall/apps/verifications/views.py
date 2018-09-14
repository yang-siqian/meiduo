import random
from django.http import HttpResponse
# Create your views here.
from rest_framework import status
from rest_framework.generics import GenericAPIView, CreateAPIView
from rest_framework.response import Response

from users.models import User
from . import serializers
from rest_framework.views import APIView
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from . import constants
from celery_tasks.sms.tasks import send_sms_code


class SMSCodeByTokenView(APIView):
    """根据access_token发送短信"""
    def get(self, request):
        # 获取并校验access_token
        access_token = request.query_params.get('access_token')
        if not access_token:
            return Response({'message': '缺少access token'}, status=status.HTTP_400_BAD_REQUEST)

        # 从acces_token中取出手机号
        mobile = User.check_send_sms_token(access_token)
        if not mobile:
            return Response({'message': 'access token 无效'}, status=status.HTTP_400_BAD_REQUEST)

        # 判断手机号发送的次数
        redis_conn = get_redis_connection('verify_codes')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return Response({'message': '发送次数过于频繁'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()

        # 发送短信验证码
        send_sms_code.delay(mobile, sms_code)
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)



class ImageCodeView(APIView):
    """图片验证码"""

    def get(self, request, image_code_id):

        # 生成图片验证码
        text, image = captcha.generate_captcha()

        # 保存真实值到redis
        redis_conn = get_redis_connection('verify_codes')
        redis_conn.setex('image_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 返回图片
        return HttpResponse(image, content_type='image/jpg')


class SMSCodeView(GenericAPIView):
    """
    短信验证码
    传入参数：
        mobile, image_code_id, text
    """

    serializer_class = serializers.ImageCodeCheckSerializer

    def get(self, request, mobile):
        """创建短信验证码"""
        # 判断图片验证码，是否在60s内
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 生成短信验证码
        sms_code = '%06d' % random.randint(0,999999)

        # 保存短信验证码与发送记录
        redis_conn = get_redis_connection('verify_codes')
        pl = redis_conn.pipeline()   # pipline管道一次性执行多个命令
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()  # 执行

        # # 发送短信验证码
        # ccp = CCP()
        # time = str(constants.SMS_CODE_REDIS_EXPIRES/60)
        # ccp.send_template_sms(mobile,[sms_code, time], constants.SMS_CODE_TEMP_ID)

        send_sms_code.delay(mobile, sms_code)
        print(sms_code)
        return Response({'message': 'OK'})



