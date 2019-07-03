import json
import random
import re

from django import http
from django.contrib.auth import login, logout

from django.db import DatabaseError
from django.shortcuts import render, redirect

# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from ihome.libs.captcha.captcha import captcha
from ihome.utils.response_code import RET
from ihome.utils.upload_image import client
from user.models import User


class ImageCodeView(View):

    def get(self, request):
        """
        图形验证码的验证
        :param request:
        :return:
        """

        cur = request.GET.get('cur')
        pre = request.GET.get('pre')
        if cur is None:
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '图形验证码不存在'})

        # 生成图片验证码
        text, image = captcha.generate_captcha()
        print(text)
        # 连接redis
        redis_conn = get_redis_connection('verify_code')

        # 判断之前是否存储有图形验证码
        if pre:
            redis_conn.delete('img_%s' % pre)
        # 图形验证码有效期,单位:秒
        redis_conn.setex('img_%s' % cur, 300, text)

        # 响应图形验证码
        return http.HttpResponse(image, content_type='image/jpg')


class SmsCodeView(View):

    def post(self, request):
        """短信验证码"""
        # 1.接受参数
        json_dict = json.loads(request.body.decode())
        mobile = json_dict.get('mobile')
        image_code = json_dict.get('image_code')
        image_code_id = json_dict.get('image_code_id')
        # 2.校验参数
        if not all([mobile, image_code, image_code_id]):
            return http.JsonResponse({
                'errno': RET.USERERR,
                'errmsg': '缺少必传参数'
            })
        # 3.创建连接到redis的对象
        redis_conn = get_redis_connection('verify_code')

        # 4.提取图形验证码
        image_code_server = redis_conn.get('img_%s' % image_code_id)
        if image_code_server is None:
            return http.JsonResponse({
                'errno': RET.USERERR,
                'errmsg': '验证码失效'
            })
        # 5.删除图形验证码
        try:
            redis_conn.delete('img_%s' % image_code_id)
        except Exception as e:
            print(e)
        # 6.对比图形验证码
        image_code_server = image_code_server.decode()
        # 转成小写字母后比较
        if image_code_server.lower() != image_code.lower():
            return http.JsonResponse({
                'code': RET.USERERR,
                'errmsg': '输入图形验证码错误'
            })
        # 7.生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        print(sms_code)
        # 8.保存验证码
        redis_conn.setex('sms_code_%s' % mobile, 300, sms_code)
        # 9.发送短信验证码
        # 10.响应结果
        return http.JsonResponse({
            'code': RET.OK,
            'errmsg': '发送短信成功'
        })


class RegisterView(View):

    def post(self, request):
        """注册功能"""
        # 接受参数
        json_dict = json.loads(request.body.decode())
        mobile = json_dict.get('mobile')
        phonecode = json_dict.get('phonecode')
        password = json_dict.get('password')
        password2 = json_dict.get('password2')
        # 校验参数
        # 判断参数是否齐全
        if not all([mobile, password, password2, phonecode]):
            return http.JsonResponse({
                'errno': RET.USERERR,
                'errmsg': "参数不全"
            })
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({
                'errno': RET.USERERR,
                'errmsg': "手机号格式不对"
            })
        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.JsonResponse({
                'errno': RET.USERERR,
                'errmsg': "密码格式不对"
            })
        # 判断两次密码是否一致
        if password != password2:
            return http.JsonResponse({
                'errno': RET.USERERR,
                'errmsg': "密码两次不一致"
            })

        # 链接redis
        redis_conn = get_redis_connection('verify_code')
        # 获取保存的sms_code
        sms_code_server = redis_conn.get('sms_code_%s' % mobile)
        # 判断sms_code_server是否存在
        if sms_code_server is None:
            return http.JsonResponse({
                'errno': RET.USERERR,
                'errmsg': "短信验证码失效"
            })
        # 对比两者验证码
        if phonecode != sms_code_server.decode():
            return http.JsonResponse({
                'errno': RET.USERERR,
                'errmsg': "短信验证码输入错误"
            })
        # 保存注册数据
        try:
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)
        except DatabaseError as e:
            print(e)
            return http.JsonResponse({
                'errno': RET.DBERR,
                'errmsg': "注册失败"
            })
        # 实现状态保持
        login(request, user)
        response = http.JsonResponse({
            'errno': RET.OK,
            'errmsg': "注册成功"
        })
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)

        # 响应注册结果
        return response


class LoginView(View):

    def post(self, request):
        # 1.获取参数
        json_dict = json.loads(request.body.decode())
        mobile = json_dict.get('mobile')
        password = json_dict.get('password')
        # 2.校验参数
        # 整体
        if not all([mobile, password]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 单个
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的用户名或手机号')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码最少8位,最长20位')
        # 3.获取登陆用户,并查看是否存在
        try:
            user = User.objects.get(mobile=mobile)
        except Exception as e:
            return http.JsonResponse({
                'errno': RET.USERERR,
                'errmsg': "用户名或是密码错误"
            })

        if not user.check_password(password):
            return http.JsonResponse({
                'errno': RET.USERERR,
                'errmsg': "用户名或密码错误"
            })

        # if user is None:
        #     return http.JsonResponse({
        #         'errno': RET.USERERR,
        #         'errmsg': "用户名或是密码错误"
        #     })
        # 4.实现状态保持
        login(request, user)
        # 5.返回响应
        return http.JsonResponse({
            'errno': RET.OK,
            'errmsg': "登录成功"
        })


class SessionView(View):

    def get(self, request):
        """获取session"""
        # 判断是否是登录状态
        if not request.user.is_authenticated:
            return http.JsonResponse({
                'errno': RET.USERERR,
                'errmsg': "用户未登录"
            })

        # 登录的话,拼接数据返回
        user_id = request.user.id
        name = request.user.username
        user_data = {"user_id": user_id, "name": name}
        return http.JsonResponse({
            'errno': RET.OK,
            'errmsg': "OK",
            'data': user_data
        })


class LogoutView(View):

    def delete(self, request):
        """退出登录"""
        # 清除session
        logout(request)

        # 返回响应
        return http.JsonResponse({
            'errno': RET.OK,
            'errmsg': '用户已退出'
        })


class UserProfile(View):
    """用户中心"""

    def get(self, request):
        """获取用户信息"""
        user = request.user
        name = user.username
        mobile = user.mobile
        avatar_url = user.avatar_url
        user_data = {
            "name": name,
            "avatar_url": avatar_url,
            "mobile": mobile
        }
        return http.JsonResponse({
            'errno': RET.OK,
            'errmsg': 'OK',
            "data": user_data
        })

    def post(self, request):
        """修改用户名"""
        json_dict = json.loads(request.body.decode())
        name = json_dict.get('name')
        user = request.user
        try:
            user = User.objects.get(id=user.id)
            user.username = name
            user.save()
        except Exception as e:
            print(e)
        return http.JsonResponse({
            'errno': RET.OK,
            'errmsg': 'OK'
        })


class ImageUpload(View):
    """上传用户图像"""

    def post(self, request):
        file_name = request.FILES.get("avatar")

        response = client.put_object(
            Bucket='ihome-1259563135',
            Body=file_name.read(),
            Key=file_name.name,
        )
        url = response.get('url')
        request.user.avatar_url = url
        request.user.save()
        return http.JsonResponse({
            'errno': RET.OK,
            'errmsg': 'OK',
            "data": {"avatar_url": url}
        })


class RealNameAuth(View):
    """实名认证"""
    def get(self, request):
        real_name = request.user.real_name
        id_card = request.user.id_card
        user_data = {}
        user_data['real_name'] = real_name
        user_data['id_card'] = id_card

        return http.JsonResponse({
            "errno": 0,
            "errmsg": "success",
            "data": user_data
        })

    def post(self,request):

        json_dict = json.loads(request.body.decode())
        real_name = json_dict.get('real_name')
        id_card = json_dict.get('id_card')
        user = request.user
        try:
            user.real_name = real_name
            user.id_card = id_card
            user.save()
        except Exception as e:
            print(e)
            return http.JsonResponse({
                'errno': RET.DBERR,
                'errmsg': '实名认证失败',
            })
        return http.JsonResponse({
            'errno': RET.OK,
            'errmsg': "OK"
        })

