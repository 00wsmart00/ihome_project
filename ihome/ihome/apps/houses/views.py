import json

from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View

from address.models import Area
from houses.models import House, Facility, HouseImage
from ihome.utils.response_code import RET
from ihome.utils.upload_image import client
from order.models import Order


class AreaView(View):
    """地区展示"""

    def get(self, request):
        data = []
        areas = Area.objects.all()
        for area in areas:
            area_list = dict()
            area_list['aid'] = area.id
            area_list['aname'] = area.name
            data.append(area_list)
        return http.JsonResponse({
            "errmsg": "OK",
            "errno": "0",
            "data": data
        })


class HouseView(View):
    """我的房源"""

    def get(self, request):
        """我的房源信息"""
        houses = House.objects.all()
        data = []
        for house in houses:
            house_list = dict()
            house_list['address'] = house.address
            house_list['area_name '] = house.area.name
            house_list['ctime'] = house.create_time
            house_list['house_id'] = house.id
            house_list['img_url'] = house.index_image_url
            house_list['price'] = house.price
            house_list['room_count'] = house.room_count
            house_list['title'] = house.title
            house_list['user_avatar'] = request.user.avatar_url
            data.append(house_list)
        return http.JsonResponse({
            'data': data,
            'errmsg': 'Ok',
            'errno': RET.OK
        })

    def post(self, request):
        """发布新房源"""
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        price = json_dict.get('price')
        area_id = json_dict.get('area_id')
        address = json_dict.get('address')
        room_count = json_dict.get('room_count')
        acreage = json_dict.get('acreage')
        unit = json_dict.get('unit')
        capacity = json_dict.get('capacity')
        beds = json_dict.get('beds')
        deposit = json_dict.get('deposit')
        min_days = json_dict.get('min_days')
        max_days = json_dict.get('max_days')
        facilities = json_dict.get('facility')
        user = request.user
        try:
            house = House.objects.create(
                title=title,
                price=price,
                area_id=area_id,
                address=address,
                room_count=room_count,
                acreage=acreage,
                unit=unit,
                capacity=capacity,
                beds=beds,
                deposit=deposit,
                min_days=min_days,
                max_days=max_days,
                user_id=user.id

            )
            facilities = Facility.objects.filter(id__in=facilities)
            house.facilities.add(*facilities)

        except Exception as e:
            print(e)
            return http.JsonResponse({
                'errno': RET.DBERR,
                'errmsg': '添加房源失败'
            })
        return http.JsonResponse({
            "errno": RET.OK,
            "errmsg": "OK",
            "data": {"house_id": house.id}
        })


class HouseImageView(View):
    """上传房源图片"""

    def post(self, request, house_id):
        house = House.objects.get(id=house_id)
        file_name = request.FILES.get("house_image")

        response = client.put_object(
            Bucket='ihome-1259563135',
            Body=file_name.read(),
            Key=file_name.name,
        )
        url = response.get('url')
        # 保存首页图片
        try:
            house.index_image_url = url
            house.save()
        except Exception as e:
            print(e)
            return http.JsonResponse({
                'errno': RET.DBERR,
                'errmsg': '保存数据失败',
            })
        # 保存图片的地址
        try:
            house_img = HouseImage.objects.filter(house_id=house_id)
            house_img.url = url
            house_img.save()
        except Exception as e:
            print(e)
            return http.JsonResponse({
                'errno': RET.DBERR,
                'errmsg': '保存数据失败',
            })

        return http.JsonResponse({
            'errno': RET.OK,
            'errmsg': 'OK',
            "data": {"url": url}
        })


class HouseDetailView(View):
    """房间详情页"""

    def get(self, request, house_id):
        """展示房间的详情信息"""
        data = dict()
        house = House.objects.get(id=house_id)
        order = Order.objects.get(house_id=house_id)
        house_dict = dict()
        house_dict['acreage'] = house.acreage
        house_dict['address'] = house.address
        house_dict['beds'] = house.beds
        house_dict['capacity'] = house.capacity
        house_dict['deposit'] = house.deposit
        house_dict['img_urls'] = [house.index_image_url]
        house_dict['max_days'] = house.max_days
        house_dict['min_days'] = house.min_days
        house_dict['price'] = house.price
        house_dict['facilities'] = []
        house_dict['room_count'] = house.room_count
        house_dict['title'] = house.title
        house_dict['unit'] = house.unit
        house_dict['user_avatar'] = house.user.avatar_url
        house_dict['user_id'] = house.user_id
        house_dict['user_name'] = house.user.username
        house_dict['comments'] = [{
            "comment":order.comment,
            "ctime":order.create_time,
            "user_name": order.user.username
        }]
        facilities = house.facilities.all()
        for facility in facilities:
            house_dict['facilities'].append(facility.id)

        print(data)
        data['house'] = house_dict
        data['user_id'] = request.user.id if request.user.is_authenticated else -1
        return http.JsonResponse({
            "data": data,
            "errmsg": "OK",
            "errno": '0'

        })


class IndexHouseView(View):
    """首页房源推荐"""

    def get(self, request):
        data = []

        houses = House.objects.all()
        for house in houses:
            house_dict = dict()
            house_dict['house_id'] = house.id
            house_dict['img_url'] = house.index_image_url
            house_dict['title'] = house.title
            data.append(house_dict)

        return http.JsonResponse({
            "data": data,
            'errmsg': 'OK',
            'errno': '0'
        })


class IndexHouseSearchView(View):
    """首页房源搜索"""
    def get(self, request):
        # 1.接受参数
        json_dict = request.GET
        aid = json_dict.get('aid')
        sd = json_dict.get('sd')
        ed = json_dict.get('ed')
        sk = json_dict.get('sk')
        p = json_dict.get('p')
        # 2.根据参数查找房源
        houses = House.objects.filter(area_id=aid)

        # 3.拼接数据,返回
        data = dict()
        for house in houses:
            houses = []
            house_dict = dict()
            house_dict['house_id'] = house.id
            house_dict['order_count'] = house.order_count
            house_dict['title'] = house.title
            house_dict['ctime'] = house.create_time
            house_dict['price'] = house.price
            house_dict['area_name'] = house.area.name
            house_dict['address'] = house.address
            house_dict['room_count'] = house.room_count
            house_dict['img_url'] = house.index_image_url
            house_dict['user_avatar'] = request.user.avatar_url
            houses.append(house_dict)
            data['houses'] = houses
            data['total'] = p
        return http.JsonResponse({
            "data": data,
            'errmsg': '请求成功',
            'errno': '0'
        })

