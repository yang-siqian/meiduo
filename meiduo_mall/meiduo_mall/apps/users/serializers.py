import re

from django_redis import get_redis_connection

from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from .models import User
from .utils import get_user_by_account


class CreateUserSerializer(serializers.ModelSerializer):
    """创建用户序列化器"""
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)
    token = serializers.CharField(label='登录状态token', read_only=True)  # 增加token字段

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow', 'token')
        extra_kwargs = {
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password':{
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的用户名',
                    'max_length': '仅允许8-20个字符的用户名',
                }
            }
        }


    def validate(self, attrs):
        """校验手机号、是否同意协议、密码"""
        if not re.match(r'^1[3-9]\d{9}', attrs['mobile']):
            raise serializers.ValidationError('手机号格式错误')

        if attrs['allow'] != 'true':
            raise serializers.ValidationError('请同意用户协议')

        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次密码不一致')

        redis_conn = get_redis_connection('verify_codes')
        mobile = attrs['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)

        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')

        if attrs['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return attrs

    def create(self, validated_data):
        """创建用户"""
        # 移除数据库模型中不存在的属性
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        user = super().create(validated_data)

        # 调用Django的认证系统加密密码
        user.set_password(validated_data['password'])
        user.save()

        # 补充生成记录登录状态的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token


        return user


class CheckSMSCodeSerializer(serializers.Serializer):
    """检查短信验证码sms_code"""
    sms_code = serializers.CharField(min_length=6, max_length=6)

    def validate_sms_code(self, value):
        account = self.context['view'].kwargs['account']
        user = get_user_by_account(account)
        if user is None:
            raise serializers.ValidationError('用户不存在')

        # 将user对象保存到序列化器对象中
        self.user = user

        # 校验短信验证码
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % user.mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if value != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')
        return value




