"""
Stage 17: Comprehensive testing for Notifications.
Covers notification retrieval, read/unread states, single mark read, batch mark read,
scoping isolation between users, and invalid ID handling.
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from test_utils.base import FAST_HASHERS_OVERRIDE
from notifications.models import Notification

User = get_user_model()


@FAST_HASHERS_OVERRIDE
class NotificationLifecycleTests(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="notif_user1",
            email="notif_user1@example.com",
            password="password123",
            role=User.Role.STUDENT,
        )
        self.user2 = User.objects.create_user(
            username="notif_user2",
            email="notif_user2@example.com",
            password="password123",
            role=User.Role.STUDENT,
        )

        self.notif1 = Notification.objects.create(
            recipient=self.user1,
            notification_type="ENROLLMENT",
            title="Enrollment Notice",
            message="You enrolled in Course A.",
            is_read=False,
        )
        self.notif2 = Notification.objects.create(
            recipient=self.user1,
            notification_type="QUIZ",
            title="Quiz Notice",
            message="You took Quiz B.",
            is_read=False,
        )
        self.notif_other = Notification.objects.create(
            recipient=self.user2,
            notification_type="SYSTEM",
            title="System Notice",
            message="Notice for user 2.",
            is_read=False,
        )

    # 1. User retrieves own notifications list
    def test_user_retrieves_own_notifications(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notif_ids = [item["id"] for item in response.data]
        self.assertIn(self.notif1.id, notif_ids)
        self.assertIn(self.notif2.id, notif_ids)
        self.assertNotIn(self.notif_other.id, notif_ids)

    # 2. User retrieves single notification detail
    def test_user_retrieves_single_notification(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"/api/notifications/{self.notif1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.notif1.id)
        self.assertEqual(response.data["title"], "Enrollment Notice")
        self.assertFalse(response.data["is_read"])

    # 3. User isolation: user1 cannot retrieve user2's notification -> 404
    def test_user_cannot_access_another_users_notification(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"/api/notifications/{self.notif_other.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 4. Mark single notification as read
    def test_mark_single_notification_read(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(f"/api/notifications/{self.notif1.id}/read/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_read"])

        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.is_read)

    # 5. User cannot mark another user's notification as read -> 404
    def test_user_cannot_mark_another_users_notification_read(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(f"/api/notifications/{self.notif_other.id}/read/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 6. Mark all notifications as read
    def test_mark_all_notifications_as_read(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch("/api/notifications/read-all/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 2)

        self.notif1.refresh_from_db()
        self.notif2.refresh_from_db()
        self.assertTrue(self.notif1.is_read)
        self.assertTrue(self.notif2.is_read)

        # Confirm user2's notification was untouched
        self.notif_other.refresh_from_db()
        self.assertFalse(self.notif_other.is_read)

    # 7. Invalid notification ID returns 404
    def test_invalid_notification_id_returns_404(self):
        self.client.force_authenticate(user=self.user1)
        self.assertEqual(
            self.client.get("/api/notifications/999999/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
