from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from MemberApp.models import DriverNotification, VehicleInfo
from AuthApp.models import Driver

from django.utils import timezone
from django.db.models import Sum, Count

from datetime import timedelta, datetime, time
from dateutil.parser import parse

import logging

logger = logging.getLogger(__name__)

# Create your views here.



class DashboardAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        response = {"status": 400}
        try:
            from_date = request.query_params.get("from")
            to_date = request.query_params.get("to")

            # Default date range (last 30 days)
            default_to = timezone.now()
            default_from = default_to - timedelta(days=30)

            # Parse dates with validation (lambda cond)
            start_date = parse(from_date).date() if from_date else default_from
            end_date = parse(to_date).date() if to_date else default_to

            # Calculate period length and previous period
            period_length = (end_date - start_date).days + 1
            last_period_start = start_date - timedelta(days=period_length)
            last_period_end = end_date - timedelta(days=period_length)

            # 1. Calculate current period income (using accepted notifications only)
            current_income = DriverNotification.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
                is_read=True,
                is_accepted=True,
            ).aggregate(
                total=Sum("rate", default=0)
            )["total"] or 0

            last_income = DriverNotification.objects.filter(
                date__gte=last_period_start,
                date__lte=last_period_end,
                is_read=True,
                is_accepted=True,
            ).aggregate(
                total=Sum("rate", default=0)
            )["total"] or 0

            income_change = self._calculate_percentage_change(current_income, last_income)

            # 2. Build categories (vehicle types + drivers + notifications)
            categories = []

            # Vehicle type categories
            vehicle_types = VehicleInfo.objects.values("vehicle_type").annotate(
                count=Count("id"),
            )
            categories.extend({
                "name": f"{vt["vehicle_type"]} Vehicles",
                "value": vt["count"]
            } for vt in vehicle_types)

            # Driver status categories
            driver_statuses = Driver.objects.values("is_deleted").annotate(
                count=Count("id")
            )
            categories.extend({
                "name": "Active Drivers" if not status["is_deleted"] else "Inactive Drivers",
                "value": status["count"]
            } for status in driver_statuses)

            # Notification status categories
            notification_statuses = DriverNotification.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
            ).values("is_read", "is_accepted").annotate(
                count=Count("id"),
            )
            categories.extend({
                "name": "Read Notifications" if ns["is_read"] and ns["is_accepted"] else 
                "Unread Notifications" if not ns["is_read"] and not ns["is_accepted"] else "Reject Notifications",
                "value": ns["count"]
            } for ns in notification_statuses)

            # 3. Get successfully read notifications data
            read_notifications = DriverNotification.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
                is_read=True,
                is_accepted=True,
            ).order_by("-created_at")

            notifications_data = [{
                "id": str(notification.id),
                "vehicle_id": str(notification.vehicle.id),
                "vehicle_model": str(notification.vehicle.model),
                "driver_number": str(notification.vehicle.alternate_number),
                "driver_name": str(notification.vehicle.name),
                "vehicle_number": str(notification.vehicle.vehicle_number),
                "created_by": notification.created_by.name if notification.created_by else "Unknown",
                "source": notification.source,
                "destination": notification.destination,
                "rate": float(notification.rate),
                "weight": notification.weight,
                "message": notification.message,
                "contact": notification.contact,
                "is_read": notification.is_read,
                "is_accepted": notification.is_accepted,
                "date": notification.date.strftime("%Y-%m-%d"),
                "created_at": notification.created_at.strftime("%Y-%m-%d"),
                "updated_at": notification.updated_at.strftime("%Y-%m-%d"),
            } for notification in read_notifications]

            # 4. Daily income breakdown (only accepted notifications)
            days_data = DriverNotification.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
                is_read=True,
                is_accepted=True,
            ).values("created_at").annotate(
                income=Sum("rate", default=0),
            ).order_by("created_at")
            days = [{
                "date": day["created_at"].strftime('%Y-%m-%d'),
                "income": float(day["income"])
            } for day in days_data]

            # Fill missing days with zero income
            existing_dates = {day["created_at"] for day in days_data}
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                if date_str not in existing_dates:
                    days.append({
                        "date": date_str,
                        "income": 0,
                    })
                current_date += timedelta(days=1)
            
            days = sorted(days, key=lambda x: x["date"])

            # 5. Active Users 
            current_active_users = Driver.objects.filter(
                is_deleted=False,
                created_at__lte=timezone.make_aware(
                    datetime.combine(end_date, time.max)
                )
            ).count()

            last_active_users = Driver.objects.filter(
                is_deleted=False,
                 created_at__lte=timezone.make_aware(
                    datetime.combine(last_period_end, time.max)
                )
            ).count()

            user_change = self._calculate_percentage_change(current_active_users, last_active_users)

            # Final response 
            data = {
                "incomeAmount": current_income,
                "incomeChange": income_change,
                "ActiveUsers": current_active_users,
                "ActiveUsersChange": user_change,
                "categories": categories,
                "days": days,
                "notifications": notifications_data,
            }
            response["status"] = 200
            response["data"] = data

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)
    
    # calculte income change percentage
    def _calculate_percentage_change(self, current, previous):
        if previous == 0:
                return 0
        return round(((current - previous) / previous) * 100, 2)