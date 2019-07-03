import datetime
import json

from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View

from houses.models import House
from ihome.utils.response_code import RET
from order.models import Order


class OrderView(View):
    """订单"""

    def post(self, request):
        """添加订单"""
        json_dict = json.loads(request.body.decode())
        house_id = json_dict.get('house_id')
        start_date = json_dict.get('start_date')
        end_date = json_dict.get('end_date')
        date1 = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        date2 = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        days = (date2 - date1).days
        house_price = House.objects.get(id=house_id).price
        amount = days * house_price

        # 保存订单数据
        try:
            order_house = Order.objects.create(
                house_id=house_id,
                begin_date=start_date,
                end_date=end_date,
                user_id=request.user.id,
                days=days,
                house_price=house_price,
                amount=amount
            )

        except Exception as e:
            print(e)
            return http.JsonResponse({
                "errno": RET.DBERR,
                "errmsg": "保存订单失败"
            })
        order_id = order_house.id
        return http.JsonResponse({
            "errno": RET.OK,
            "errmsg": "保存订单成功",
            "data": {"order_id": order_id}
        })

    def get(self, request):
        """获取订单"""
        json_dict = request.GET
        role = json_dict.get('role')
        user = request.user
        data = dict()
        orders_list = []
        if role == 'custom':
            try:
                orders = Order.objects.filter(user_id=user.id)
            except Order.DoesNotExist:
                return http.JsonResponse({
                    "errno": RET.DBERR,
                    "errmsg": "数据不存在"
                })

        else:
            try:
                orders = Order.objects.filter(house_id__in=user.house_set.all())
            except Order.DoesNotExist:
                return http.JsonResponse({
                    "errno": RET.DBERR,
                    "errmsg": "数据不存在"
                })
        for order in orders:
            order_dict = dict()
            try:
                order_dict['amount'] = order.amount
                order_dict['comment'] = order.comment
                order_dict['ctime'] = order.create_time
                order_dict['days'] = order.days
                order_dict['end_date'] = order.end_date
                order_dict['img_url'] = order.house.index_image_url
                order_dict['order_id'] = order.id
                order_dict['start_date'] = order.begin_date
                order_dict['status'] = order.status
                order_dict['title'] = order.house.title
                orders_list.append(order_dict)
                data["orders"] = orders_list
            except Exception as e:
                print(e)
                return http.JsonResponse({
                    "errmsg": "数据查询错误",
                    "errno": RET.DBERR
                })

        return http.JsonResponse({
                "data": data,
                "errmsg": "OK",
                "errno": RET.OK
            })

    # 订单处理

    def put(self, request):
        json_dict = json.loads(request.body.decode())
        action = json_dict.get("action")
        order_id = json_dict.get('order_id')
        reason = json_dict.get('reason')

        if action == 'reject':
            try:
                order = Order.objects.get(id=order_id)
                order.status = Order.ORDER_STATUS_CHOICES[6][0]
                order.comment = reason
                order.save()
            except Exception as e:
                print(e)
                return http.JsonResponse({
                    "errmsg": "更新数据失败",
                    "errno": RET.DBERR
                })
        else:
            try:
                order = Order.objects.get(id=order_id)
                order.status = Order.ORDER_STATUS_CHOICES[3][0]
                order.save()
            except Exception as e:
                print(e)
                return http.JsonResponse({
                    "errmsg": "更新数据失败",
                    "errno": RET.DBERR
                })
        return http.JsonResponse({
            "errno": RET.OK,
            "errmsg": "OK"
        })


class CommentView(View):
    """客户评论"""

    def put(self, request):

        json_dict = json.loads(request.body.decode())
        comment = json_dict.get('comment')
        order_id = json_dict.get('order_id')
        try:
            order = Order.objects.get(id=order_id)
            order.status = Order.ORDER_STATUS_CHOICES[4][0]
            order.comment = comment
            order.save()
        except Exception as e:
            print(e)
            return http.JsonResponse({
                "errmsg": "更新数据失败",
                "errno": RET.DBERR
            })
        return http.JsonResponse({
            "errno": RET.OK,
            "errmsg": "OK"
        })
