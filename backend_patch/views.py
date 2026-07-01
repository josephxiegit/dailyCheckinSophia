import json
from app01.models import *
from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from rest_framework.views import APIView
import os
import datetime
import numpy as np
import time
from django.utils import timezone
from django.db import connections
from django.db.models import F
from homeworkonline.get_questions import main_get_question
from homeworkonline.return_question import main_return_question


class DailyCheckinAPIView(APIView):

    def post(self, request, *args, **kwargs):
        try:
            method = request.data['method']
        except:
            method = None

        print("收到请求数据:", request.data)

        def format_dt(dt):
            if not dt:
                return ''
            local_dt = timezone.localtime(dt) if timezone.is_aware(dt) else dt
            return local_dt.strftime("%Y-%m-%d %H:%M")

        def is_frontend_editable_date(target_date):
            if isinstance(target_date, str):
                target_date = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()
            today = timezone.localdate()
            return target_date in [
                today - datetime.timedelta(days=2),
                today - datetime.timedelta(days=1),
                today,
                today + datetime.timedelta(days=1),
            ]

        def section_is_coupon_exempt(record, section):
            if not record:
                return False
            if section == 'reading':
                return str(record.reading_start) == '-1'
            if section == 'math':
                return record.math_title == '媛媛免除'
            if section == 'class':
                return record.class_title == '媛媛免除'
            return False

        def ensure_couponbatch_table():
            # checkindb 上没有走 Django 迁移，这里幂等建表（首个券请求时创建）
            conn = connections['checkindb']
            if 'app01_couponbatch' not in conn.introspection.table_names():
                with conn.schema_editor() as se:
                    se.create_model(CouponBatch)

        def covering_batches(coupon_type, date_str):
            # 返回所有「区间覆盖该日期」的批次，按最早到期排序（最早到期优先消费/退还）
            return (
                CouponBatch.objects.using('checkindb')
                .filter(coupon_type=coupon_type, start_date__lte=date_str, end_date__gte=date_str)
                .order_by('end_date')
            )

        def coupon_summary(coupon_type):
            # 聚合某类型所有批次，返回 {total, used, remaining, batches:[...]}
            ensure_couponbatch_table()
            batches = (
                CouponBatch.objects.using('checkindb')
                .filter(coupon_type=coupon_type)
                .order_by('end_date')
            )
            total = used = 0
            items = []
            for b in batches:
                remaining = b.total_coupons - b.used_coupons
                total += b.total_coupons
                used += b.used_coupons
                items.append({
                    'startDate': str(b.start_date).split(' ')[0],
                    'endDate': str(b.end_date).split(' ')[0],
                    'total': b.total_coupons,
                    'used': b.used_coupons,
                    'remaining': remaining,
                })
            return {'total': total, 'used': used, 'remaining': total - used, 'batches': items}

        def merge_remedy_log_fallback(remedy_dict, logs):
            section_name_map = {
                '英语阅读': 'reading',
                '数学练习': 'math',
                '英语网课': 'class',
            }
            for log in logs:
                detail = log.get('detail') or ''
                if not detail.startswith('使用补救: '):
                    continue
                parts = detail.replace('使用补救: ', '', 1).split()
                if len(parts) < 2:
                    continue
                date_str = parts[0]
                section = section_name_map.get(parts[1])
                if not section:
                    continue
                if date_str not in remedy_dict:
                    remedy_dict[date_str] = {}
                existing = remedy_dict[date_str].get(section, {})
                remedy_dict[date_str][section] = {
                    'used_at': existing.get('used_at') or format_dt(log.get('create_time')),
                    'saved_at': existing.get('saved_at') or format_dt(log.get('create_time')),
                }
            
        if method == 'saveStudyRecord':
            try:
                target_date = request.data.get('date')
                section = request.data.get('section') # 获取前端传来的模块标识
                now = timezone.now()
                if not target_date:
                    return JsonResponse({'code': 1, 'msg': '日期不能为空'})
                if section not in ['reading', 'math', 'class']:
                    return JsonResponse({'code': 1, 'msg': '未知的保存模块'})

                if not is_frontend_editable_date(target_date):
                    remedy_usage = RemedyCouponUsage.objects.using('checkindb').filter(
                        date=target_date,
                        section=section,
                        saved_at__isnull=True
                    ).first()
                    if not remedy_usage:
                        return JsonResponse({'code': 1, 'msg': '该日期已锁定，请先使用补救券'})
                
                # 动态构建需要更新的字段，避免覆盖其他模块的已有数据
                update_defaults = {}
                
                if section == 'reading':
                    update_defaults['reading_start'] = request.data.get('readingStart')
                    update_defaults['reading_end'] = request.data.get('readingEnd')
                    update_defaults['reading_saved_at'] = now
                elif section == 'math':
                    update_defaults['math_title'] = request.data.get('mathTitle')
                    update_defaults['math_min'] = request.data.get('mathMin') or 0
                    update_defaults['math_sec'] = request.data.get('mathSec') or 0
                    update_defaults['math_saved_at'] = now
                elif section == 'class':
                    update_defaults['class_title'] = request.data.get('classTitle')
                    update_defaults['class_type'] = request.data.get('classType')
                    update_defaults['class_saved_at'] = now
                else:
                    return JsonResponse({'code': 1, 'msg': '未知的保存模块'})

                # 使用 update_or_create，只更新前端传来的特定模块的字段
                obj, created = dailyCheckinRecords.objects.using('checkindb').update_or_create(
                    date=target_date, 
                    defaults=update_defaults
                )
                remedy_time = ''
                if not is_frontend_editable_date(target_date):
                    remedy_saved_count = RemedyCouponUsage.objects.using('checkindb').filter(
                        date=target_date,
                        section=section,
                        saved_at__isnull=True
                    ).update(saved_at=now)
                    if remedy_saved_count:
                        remedy_time = format_dt(now)
                print(f"数据保存成功！日期：{obj.date}, 模块：{section}, 是否新创建：{created}")
                return JsonResponse({
                    'code': 0,
                    'msg': '保存成功',
                    'actionTime': format_dt(getattr(obj, f'{section}_saved_at', None)),
                    'remedyTime': remedy_time
                })
            except Exception as e:
                print(f"数据库写入失败: {e}")
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'getMonthRecords':
            try:
                year  = request.data.get('year')
                month = request.data.get('month')
                records = (
                    dailyCheckinRecords.objects
                    .using('checkindb')
                    .filter(date__year=year, date__month=month)
                    .values(
                        'date', 'reading_start', 'reading_end',
                        'math_title', 'math_min', 'math_sec',
                        'class_title', 'class_type',
                        'reading_saved_at', 'math_saved_at', 'class_saved_at',
                        'reading_coupon_used_at', 'math_coupon_used_at', 'class_coupon_used_at'
                    )
                )
                # 获取该月的补救券使用记录
                remedy_usages = RemedyCouponUsage.objects.using('checkindb').filter(
                    date__year=year,
                    date__month=month
                ).values('date', 'section', 'used_at', 'saved_at')
                
                # 构建补救记录字典
                remedy_dict = {}
                for usage in remedy_usages:
                    date_str = str(usage['date'])
                    if date_str not in remedy_dict:
                        remedy_dict[date_str] = {}
                    remedy_dict[date_str][usage['section']] = {
                            'used_at': format_dt(usage['used_at']),
                            'saved_at': format_dt(usage['saved_at'])
                        }

                remedy_logs = RemedyCouponLog.objects.using('checkindb').filter(
                    action='use',
                    detail__contains=f"{year}-{str(month).zfill(2)}"
                ).values('detail', 'create_time')
                merge_remedy_log_fallback(remedy_dict, remedy_logs)
                
                data = {}
                for r in records:
                    row = dict(r)
                    row['reading_saved_at'] = format_dt(row.get('reading_saved_at'))
                    row['math_saved_at'] = format_dt(row.get('math_saved_at'))
                    row['class_saved_at'] = format_dt(row.get('class_saved_at'))
                    row['reading_coupon_used_at'] = format_dt(row.get('reading_coupon_used_at'))
                    row['math_coupon_used_at'] = format_dt(row.get('math_coupon_used_at'))
                    row['class_coupon_used_at'] = format_dt(row.get('class_coupon_used_at'))
                    
                    # 添加补救券信息
                    date_str = str(r['date'])
                    if date_str in remedy_dict:
                        row['remedy'] = remedy_dict[date_str]
                    else:
                        row['remedy'] = {}
                        
                    data[date_str] = row
                # 以 "YYYY-MM-DD" 字符串为 key，方便前端直接查找
                return JsonResponse({'code': 0, 'data': data})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})
        
        elif method == 'deleteStudyRecord':
            try:
                target_date = request.data.get('date')
                record = dailyCheckinRecords.objects.using('checkindb').filter(date=target_date).first()
                
                if record:
                    # 检查是否包含“媛媛免除”，有的话自动退款
                    refund_count = 0
                    if str(record.reading_start) == '-1': refund_count += 1
                    if record.math_title == '媛媛免除': refund_count += 1
                    if record.class_title == '媛媛免除': refund_count += 1
                    
                    if refund_count > 0:
                        ensure_couponbatch_table()
                        # 逐张退还到「覆盖该日期、且已用>0、最早到期」的免除券批次
                        for _ in range(refund_count):
                            rb = covering_batches('exempt', target_date).filter(
                                used_coupons__gt=0).first()
                            if not rb:
                                break
                            rb.used_coupons -= 1
                            if rb.used_coupons < 0: rb.used_coupons = 0
                            rb.save()

                    record.delete()
                    return JsonResponse({'code': 0, 'msg': '删除成功，已返还免除券'})
                else:
                    return JsonResponse({'code': 1, 'msg': '未找到该日期的记录'})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)}) 
                    
        elif method == 'getDateRangeRecords':
            try:
                start_date = request.data.get('startDate')
                end_date   = request.data.get('endDate')
                records = (
                    dailyCheckinRecords.objects
                    .using('checkindb')
                    .filter(date__gte=start_date, date__lte=end_date)
                    .order_by('date')
                    .values('date', 'reading_start', 'reading_end',
                        'math_title', 'math_min', 'math_sec',
                        'class_title', 'class_type',
                        'reading_saved_at', 'math_saved_at', 'class_saved_at',
                        'reading_coupon_used_at', 'math_coupon_used_at', 'class_coupon_used_at')
                )
                
                # 获取该日期范围的补救券使用记录
                remedy_usages = RemedyCouponUsage.objects.using('checkindb').filter(
                    date__gte=start_date,
                    date__lte=end_date
                ).values('date', 'section', 'used_at', 'saved_at')
                
                # 构建补救记录字典
                remedy_dict = {}
                for usage in remedy_usages:
                    date_str = str(usage['date'])
                    if date_str not in remedy_dict:
                        remedy_dict[date_str] = {}
                    remedy_dict[date_str][usage['section']] = {
                            'used_at': format_dt(usage['used_at']),
                            'saved_at': format_dt(usage['saved_at'])
                        }

                remedy_logs = RemedyCouponLog.objects.using('checkindb').filter(
                    action='use'
                ).values('detail', 'create_time')
                merge_remedy_log_fallback(remedy_dict, remedy_logs)
                
                data = []
                for r in records:
                    row = dict(r)
                    row['date'] = str(r['date']).split(' ')[0]
                    row['reading_saved_at'] = format_dt(row.get('reading_saved_at'))
                    row['math_saved_at'] = format_dt(row.get('math_saved_at'))
                    row['class_saved_at'] = format_dt(row.get('class_saved_at'))
                    row['reading_coupon_used_at'] = format_dt(row.get('reading_coupon_used_at'))
                    row['math_coupon_used_at'] = format_dt(row.get('math_coupon_used_at'))
                    row['class_coupon_used_at'] = format_dt(row.get('class_coupon_used_at'))
                    
                    # 添加补救券信息
                    date_str = str(r['date'])
                    if date_str in remedy_dict:
                        row['remedy'] = remedy_dict[date_str]
                    else:
                        row['remedy'] = {}
                        
                    data.append(row)
                return JsonResponse({'code': 0, 'data': data})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'getSavedDateRange':
            try:
                ranges = (
                    savedDateRange.objects
                    .using('checkindb')
                    .all()
                    .order_by('start_date', 'end_date')
                    .values('start_date', 'end_date', 'amount', 'status')
                )
                result = []
                for r in ranges:
                    result.append({
                        'startDate': str(r['start_date']).split(' ')[0],
                        'endDate':   str(r['end_date']).split(' ')[0],
                        'amount':    str(r['amount']) if r['amount'] is not None else '',
                        'status':    r['status'] or '',
                    })
                return JsonResponse({'code': 0, 'ranges': result})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'addDateRange':
            try:
                start_date = request.data.get('startDate')
                end_date   = request.data.get('endDate')
                if not start_date or not end_date:
                    return JsonResponse({'code': 1, 'msg': '日期不能为空'})
                # 同一区间已存在则跳过，避免重复
                exists = savedDateRange.objects.using('checkindb').filter(
                    start_date=start_date, end_date=end_date
                ).exists()
                if not exists:
                    savedDateRange.objects.using('checkindb').create(
                        start_date=start_date,
                        end_date=end_date,
                        amount=None,
                        status=None,
                    )
                return JsonResponse({'code': 0})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'saveDateRange':
            try:
                start_date = request.data.get('startDate')
                end_date   = request.data.get('endDate')
                old_obj = savedDateRange.objects.using('checkindb').first()
                old_amount = old_obj.amount if old_obj else None
                old_status = old_obj.status if old_obj else None
                # 只保存一条记录，有就更新，没有就创建
                savedDateRange.objects.using('checkindb').all().delete()
                savedDateRange.objects.using('checkindb').create(
                    start_date=start_date,
                    end_date=end_date,
                    amount=old_amount,
                    status=old_status,
                )
                return JsonResponse({'code': 0})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'saveSavedDateRangeMeta':
            try:
                start_date = request.data.get('startDate')
                end_date   = request.data.get('endDate')
                amount     = request.data.get('amount')
                status     = request.data.get('status')

                if not start_date or not end_date:
                    return JsonResponse({'code': 1, 'msg': '请传入 startDate 和 endDate'})
                if status not in ['pending', 'received']:
                    return JsonResponse({'code': 1, 'msg': '状态不合法'})
                if amount in [None, '']:
                    return JsonResponse({'code': 1, 'msg': '金额不能为空'})

                updated = (
                    savedDateRange.objects
                    .using('checkindb')
                    .filter(start_date=start_date, end_date=end_date)
                    .update(amount=amount, status=status)
                )
                if updated == 0:
                    # 不存在则新建
                    savedDateRange.objects.using('checkindb').create(
                        start_date=start_date,
                        end_date=end_date,
                        amount=amount,
                        status=status,
                    )
                return JsonResponse({'code': 0, 'msg': '保存成功'})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'deleteSavedDateRangeMeta':
            try:
                start_date = request.data.get('startDate')
                end_date   = request.data.get('endDate')

                if not start_date or not end_date:
                    return JsonResponse({'code': 1, 'msg': '请传入 startDate 和 endDate'})

                (
                    savedDateRange.objects
                    .using('checkindb')
                    .filter(start_date=start_date, end_date=end_date)
                    .update(amount=None, status=None)
                )
                return JsonResponse({'code': 0, 'msg': '删除成功'})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'deleteEntireDateRange':
            try:
                start_date = request.data.get('startDate')
                end_date   = request.data.get('endDate')
                if not start_date or not end_date:
                    return JsonResponse({'code': 1, 'msg': '请传入 startDate 和 endDate'})
                savedDateRange.objects.using('checkindb').filter(
                    start_date=start_date, end_date=end_date
                ).delete()
                return JsonResponse({'code': 0, 'msg': '删除成功'})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'saveExclusions':
            try:
                from django.conf import settings
                print("💡 Django当前使用的数据库路径是:", settings.DATABASES['checkindb']['NAME'])
                import json
                # 兼容不同解析方式，防止由于 content-type 不同导致 request.data 获取不到
                exclusions_data = request.data.get('exclusions')
                if not exclusions_data:
                    exclusions_data = request.POST.get('exclusions', '[]')
                    
                if isinstance(exclusions_data, str):
                    exclusions_list = json.loads(exclusions_data)
                else:
                    exclusions_list = exclusions_data

                # 清空旧数据，保存新数据
                savedExclusions.objects.using('checkindb').all().delete()
                savedExclusions.objects.using('checkindb').create(
                    exclusions=json.dumps(exclusions_list, ensure_ascii=False)
                )
                return JsonResponse({'code': 0, 'msg': '保存成功'})
            except Exception as e:
                # 抛出具体的报错信息给前端，方便查错
                return JsonResponse({'code': 1, 'msg': f"存库失败: {str(e)}"})

        elif method == 'getExclusions':
            try:
                import json
                obj = savedExclusions.objects.using('checkindb').first()
                if obj and obj.exclusions:
                    exclusions_list = json.loads(obj.exclusions)
                else:
                    exclusions_list = []
                return JsonResponse({'code': 0, 'exclusions': exclusions_list})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})  

        elif method == 'clearAllConfigs':
            try:
                # 清空保存的日期范围
                savedDateRange.objects.using('checkindb').all().delete()
                # 清空保存的免除项
                savedExclusions.objects.using('checkindb').all().delete()
                
                return JsonResponse({'code': 0, 'msg': '已清除配置'})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': f"清除失败: {str(e)}"})
            
        elif method == 'getCoupon':
            try:
                s = coupon_summary('exempt')
                return JsonResponse({'code': 0, 'total': s['total'], 'used': s['used'],
                                     'remaining': s['remaining'], 'batches': s['batches']})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'getRemedyCoupon':
            try:
                s = coupon_summary('remedy')
                return JsonResponse({'code': 0, 'total': s['total'], 'used': s['used'],
                                     'remaining': s['remaining'], 'batches': s['batches']})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'addCoupon':
            try:
                raw_count = request.data.get('count')
                if not raw_count:
                    raw_count = request.POST.get('count', 0)
                count = int(raw_count)
                if count <= 0:
                    return JsonResponse({'code': 1, 'msg': '数量必须大于 0'})

                start_date = request.data.get('startDate')
                end_date = request.data.get('endDate')
                if not start_date or not end_date:
                    return JsonResponse({'code': 1, 'msg': '请选择要绑定的常用时间区间'})
                if not savedDateRange.objects.using('checkindb').filter(
                        start_date=start_date, end_date=end_date).exists():
                    return JsonResponse({'code': 1, 'msg': '请先在区间记录中保存该常用时间段'})

                ensure_couponbatch_table()
                batch, _ = CouponBatch.objects.using('checkindb').get_or_create(
                    coupon_type='exempt', start_date=start_date, end_date=end_date,
                    defaults={'total_coupons': 0, 'used_coupons': 0})
                batch.total_coupons += count
                batch.save()

                CouponLog.objects.using('checkindb').create(
                    action='add', amount=count,
                    detail=f"增加免除券 {count} 张（{start_date} 至 {end_date}）")

                return JsonResponse({'code': 0, 'msg': '添加成功'})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': f"添加失败: {str(e)}"})

        elif method == 'addRemedyCoupon':
            try:
                raw_count = request.data.get('count')
                if not raw_count:
                    raw_count = request.POST.get('count', 0)
                count = int(raw_count)
                if count <= 0:
                    return JsonResponse({'code': 1, 'msg': '数量必须大于 0'})

                start_date = request.data.get('startDate')
                end_date = request.data.get('endDate')
                if not start_date or not end_date:
                    return JsonResponse({'code': 1, 'msg': '请选择要绑定的常用时间区间'})
                if not savedDateRange.objects.using('checkindb').filter(
                        start_date=start_date, end_date=end_date).exists():
                    return JsonResponse({'code': 1, 'msg': '请先在区间记录中保存该常用时间段'})

                ensure_couponbatch_table()
                batch, _ = CouponBatch.objects.using('checkindb').get_or_create(
                    coupon_type='remedy', start_date=start_date, end_date=end_date,
                    defaults={'total_coupons': 0, 'used_coupons': 0})
                batch.total_coupons += count
                batch.save()

                RemedyCouponLog.objects.using('checkindb').create(
                    action='add', amount=count,
                    detail=f"增加补救券 {count} 张（{start_date} 至 {end_date}）")

                return JsonResponse({'code': 0, 'msg': '添加成功'})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': f"添加失败: {str(e)}"})

        elif method == 'reduceCoupon':
            try:
                raw_count = request.data.get('count')
                if not raw_count:
                    raw_count = request.POST.get('count', 0)
                count = int(raw_count)
                if count <= 0:
                    return JsonResponse({'code': 1, 'msg': '数量必须大于 0'})

                start_date = request.data.get('startDate')
                end_date = request.data.get('endDate')
                if not start_date or not end_date:
                    return JsonResponse({'code': 1, 'msg': '请选择要删除的区间'})

                ensure_couponbatch_table()
                batch = CouponBatch.objects.using('checkindb').filter(
                    coupon_type='exempt', start_date=start_date, end_date=end_date).first()
                if not batch:
                    return JsonResponse({'code': 1, 'msg': '该区间没有免除券'})

                remaining = batch.total_coupons - batch.used_coupons
                if count > remaining:
                    return JsonResponse({'code': 1, 'msg': f'最多只能删除未使用的 {remaining} 张'})

                batch.total_coupons -= count
                if batch.total_coupons <= 0:
                    batch.delete()
                else:
                    batch.save()

                CouponLog.objects.using('checkindb').create(
                    action='reduce', amount=-count,
                    detail=f"删除免除券 {count} 张（{start_date} 至 {end_date}）")

                return JsonResponse({'code': 0, 'msg': '删除成功'})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': f"删除失败: {str(e)}"})

        elif method == 'reduceRemedyCoupon':
            try:
                raw_count = request.data.get('count')
                if not raw_count:
                    raw_count = request.POST.get('count', 0)
                count = int(raw_count)
                if count <= 0:
                    return JsonResponse({'code': 1, 'msg': '数量必须大于 0'})

                start_date = request.data.get('startDate')
                end_date = request.data.get('endDate')
                if not start_date or not end_date:
                    return JsonResponse({'code': 1, 'msg': '请选择要删除的区间'})

                ensure_couponbatch_table()
                batch = CouponBatch.objects.using('checkindb').filter(
                    coupon_type='remedy', start_date=start_date, end_date=end_date).first()
                if not batch:
                    return JsonResponse({'code': 1, 'msg': '该区间没有补救券'})

                remaining = batch.total_coupons - batch.used_coupons
                if count > remaining:
                    return JsonResponse({'code': 1, 'msg': f'最多只能删除未使用的 {remaining} 张'})

                batch.total_coupons -= count
                if batch.total_coupons <= 0:
                    batch.delete()
                else:
                    batch.save()

                RemedyCouponLog.objects.using('checkindb').create(
                    action='reduce', amount=-count,
                    detail=f"删除补救券 {count} 张（{start_date} 至 {end_date}）")

                return JsonResponse({'code': 0, 'msg': '删除成功'})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': f"删除失败: {str(e)}"})

        elif method == 'useCoupon':
            try:
                target_date = request.data.get('date')
                section = request.data.get('section')
                section_map = {'reading': '英语阅读', 'math': '数学练习', 'class': '英语网课'}
                now = timezone.now()

                ensure_couponbatch_table()
                batch = covering_batches('exempt', target_date).filter(
                    used_coupons__lt=F('total_coupons')).first()
                if not batch:
                    return JsonResponse({'code': 1, 'msg': '该日期没有可用免除券（不在已绑定区间内或已用完）'})

                update_defaults = {}
                if section == 'reading':
                    update_defaults['reading_start'] = -1
                    update_defaults['reading_end'] = -1
                    update_defaults['reading_coupon_used_at'] = now
                elif section == 'math':
                    update_defaults['math_title'] = '媛媛免除'
                    update_defaults['math_min'] = 0
                    update_defaults['math_sec'] = 0
                    update_defaults['math_coupon_used_at'] = now
                elif section == 'class':
                    update_defaults['class_title'] = '媛媛免除'
                    update_defaults['class_type'] = '全部'
                    update_defaults['class_coupon_used_at'] = now
                else:
                    return JsonResponse({'code': 1, 'msg': '未知模块'})
                
                record, _ = dailyCheckinRecords.objects.using('checkindb').update_or_create(date=target_date, defaults=update_defaults)

                batch.used_coupons += 1
                batch.save()

                # 写入日志
                CouponLog.objects.using('checkindb').create(action='use', amount=-1, detail=f"使用抵消: {target_date} {section_map.get(section, '')}")
                
                return JsonResponse({
                    'code': 0,
                    'msg': '免除成功',
                    'actionTime': format_dt(getattr(record, f'{section}_coupon_used_at', None))
                })
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'useRemedyCoupon':
            try:
                target_date = request.data.get('date')
                section = request.data.get('section')
                section_map = {'reading': '英语阅读', 'math': '数学练习', 'class': '英语网课'}
                
                if not target_date:
                    return JsonResponse({'code': 1, 'msg': '日期不能为空'})
                if section not in section_map:
                    return JsonResponse({'code': 1, 'msg': '未知模块'})
                if is_frontend_editable_date(target_date):
                    return JsonResponse({'code': 1, 'msg': '该日期仍可编辑，不需要使用补救券'})
                
                record = dailyCheckinRecords.objects.using('checkindb').filter(date=target_date).first()
                if section_is_coupon_exempt(record, section):
                    return JsonResponse({'code': 1, 'msg': '免除状态不能使用补救券'})
                
                existing = RemedyCouponUsage.objects.using('checkindb').filter(
                    date=target_date,
                    section=section,
                    saved_at__isnull=True
                ).first()
                if existing:
                    return JsonResponse({'code': 0, 'msg': '已开启补救编辑'})
                
                ensure_couponbatch_table()
                batch = covering_batches('remedy', target_date).filter(
                    used_coupons__lt=F('total_coupons')).first()
                if not batch:
                    return JsonResponse({'code': 1, 'msg': '该日期没有可用补救券（不在已绑定区间内或已用完）'})

                RemedyCouponUsage.objects.using('checkindb').create(date=target_date, section=section)
                batch.used_coupons += 1
                batch.save()

                RemedyCouponLog.objects.using('checkindb').create(
                    action='use',
                    amount=-1,
                    detail=f"使用补救: {target_date} {section_map.get(section, '')}"
                )
                
                return JsonResponse({'code': 0, 'msg': '已开启补救编辑'})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'revokeCoupon':
            try:
                target_date = request.data.get('date')
                section = request.data.get('section')
                section_map = {'reading': '英语阅读', 'math': '数学练习', 'class': '英语网课'}
                
                record = dailyCheckinRecords.objects.using('checkindb').filter(date=target_date).first()
                if not record:
                    return JsonResponse({'code': 1, 'msg': '找不到记录'})
                
                # 清除免除数据
                if section == 'reading' and str(record.reading_start) == '-1':
                    record.reading_start = None
                    record.reading_end = None
                elif section == 'math' and record.math_title == '媛媛免除':
                    record.math_title = None
                    record.math_min = 0
                    record.math_sec = 0
                elif section == 'class' and record.class_title == '媛媛免除':
                    record.class_title = None
                    record.class_type = None
                else:
                    return JsonResponse({'code': 1, 'msg': '该项不是免除状态'})
                record.save()

                # 退还免除券到对应区间批次
                ensure_couponbatch_table()
                refund_batch = covering_batches('exempt', target_date).filter(
                    used_coupons__gt=0).first()
                if refund_batch:
                    refund_batch.used_coupons -= 1
                    if refund_batch.used_coupons < 0: refund_batch.used_coupons = 0
                    refund_batch.save()

                # 写入日志
                CouponLog.objects.using('checkindb').create(action='revoke', amount=1, detail=f"撤销使用: {target_date} {section_map.get(section, '')}")
                
                return JsonResponse({'code': 0, 'msg': '撤销成功'})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})
                        
        elif method == 'getCouponLogs':
            try:
                page = int(request.data.get('page', 1))
                size = int(request.data.get('size', 15))
                offset = (page - 1) * size
                
                # 获取分页数据
                logs_qs = CouponLog.objects.using('checkindb').all()
                total = logs_qs.count()
                logs = logs_qs[offset:offset+size]
                
                data = []
                for log in logs:
                    ct = log.create_time
                    if ct and timezone.is_aware(ct):
                        ct = timezone.localtime(ct)
                    data.append({
                        'id': log.nid,
                        'amount': log.amount,
                        'detail': log.detail,
                        'time': ct.strftime("%Y-%m-%d %H:%M:%S") if ct else '' # 转本地时区后格式化
                    })
                return JsonResponse({'code': 0, 'data': data, 'total': total})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'getRemedyCouponLogs':
            try:
                page = int(request.data.get('page', 1))
                size = int(request.data.get('size', 15))
                offset = (page - 1) * size
                
                logs_qs = RemedyCouponLog.objects.using('checkindb').all()
                total = logs_qs.count()
                logs = logs_qs[offset:offset+size]
                
                data = []
                for log in logs:
                    ct = log.create_time
                    if ct and timezone.is_aware(ct):
                        ct = timezone.localtime(ct)
                    data.append({
                        'id': log.nid,
                        'amount': log.amount,
                        'detail': log.detail,
                        'time': ct.strftime("%Y-%m-%d %H:%M:%S") if ct else '' # 转本地时区后格式化
                    })
                return JsonResponse({'code': 0, 'data': data, 'total': total})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})

        elif method == 'deleteStudyRecord':
            try:
                target_date = request.data.get('date')
                record = dailyCheckinRecords.objects.using('checkindb').filter(date=target_date).first()
                
                if record:
                    refund_count = 0
                    if str(record.reading_start) == '-1': refund_count += 1
                    if record.math_title == '媛媛免除': refund_count += 1
                    if record.class_title == '媛媛免除': refund_count += 1
                    
                    if refund_count > 0:
                        ensure_couponbatch_table()
                        # 逐张退还到「覆盖该日期、且已用>0、最早到期」的免除券批次
                        for _ in range(refund_count):
                            rb = covering_batches('exempt', target_date).filter(
                                used_coupons__gt=0).first()
                            if not rb:
                                break
                            rb.used_coupons -= 1
                            if rb.used_coupons < 0: rb.used_coupons = 0
                            rb.save()
                        # 写入日志
                        CouponLog.objects.using('checkindb').create(action='refund', amount=refund_count, detail=f"删除记录: {target_date} 退还免除券")
                    
                    record.delete()
                    return JsonResponse({'code': 0, 'msg': '删除成功'})
                else:
                    return JsonResponse({'code': 1, 'msg': '未找到该日期的记录'})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': str(e)})
