from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Course, Module, Lesson

User = get_user_model()


class CourseModuleLessonSecurityTests(APITestCase):

    def setUp(self):
        # Users
        self.student = User.objects.create_user(
            username="student_user",
            email="student@example.com",
            password="password123",
            role=User.Role.STUDENT
        )
        self.instructor1 = User.objects.create_user(
            username="instructor1_user",
            email="instructor1@example.com",
            password="password123",
            role=User.Role.INSTRUCTOR
        )
        self.instructor2 = User.objects.create_user(
            username="instructor2_user",
            email="instructor2@example.com",
            password="password123",
            role=User.Role.INSTRUCTOR
        )
        self.admin = User.objects.create_user(
            username="admin_user",
            email="admin@example.com",
            password="password123",
            role=User.Role.ADMIN
        )

        # Courses
        # 1. Published course owned by Instructor 1
        self.pub_course_inst1 = Course.objects.create(
            instructor=self.instructor1,
            title="Published Course Inst 1",
            description="Published Course",
            is_published=True
        )
        self.pub_module_inst1 = Module.objects.create(
            course=self.pub_course_inst1,
            title="Published Module Inst 1",
            order=1
        )
        self.pub_lesson_inst1 = Lesson.objects.create(
            module=self.pub_module_inst1,
            title="Published Lesson Inst 1",
            content="Content pub",
            order=1
        )

        # 2. Unpublished course owned by Instructor 1
        self.unpub_course_inst1 = Course.objects.create(
            instructor=self.instructor1,
            title="Unpublished Course Inst 1",
            description="Draft Course",
            is_published=False
        )
        self.unpub_module_inst1 = Module.objects.create(
            course=self.unpub_course_inst1,
            title="Unpublished Module Inst 1",
            order=1
        )
        self.unpub_lesson_inst1 = Lesson.objects.create(
            module=self.unpub_module_inst1,
            title="Unpublished Lesson Inst 1",
            content="Content draft",
            order=1
        )

        # 3. Course owned by Instructor 2
        self.course_inst2 = Course.objects.create(
            instructor=self.instructor2,
            title="Course Inst 2",
            description="Instructor 2 Course",
            is_published=True
        )
        self.module_inst2 = Module.objects.create(
            course=self.course_inst2,
            title="Module Inst 2",
            order=1
        )
        self.lesson_inst2 = Lesson.objects.create(
            module=self.module_inst2,
            title="Lesson Inst 2",
            content="Content inst2",
            order=1
        )

    # ============================================================
    # A & B: MODULE VISIBILITY FOR STUDENTS
    # ============================================================

    def test_student_can_access_modules_of_published_course(self):
        self.client.force_authenticate(user=self.student)

        # Detail view -> 200 OK
        resp = self.client.get(f"/api/courses/modules/{self.pub_module_inst1.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], self.pub_module_inst1.id)

        # List view -> contains published module
        resp_list = self.client.get("/api/courses/modules/")
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        module_ids = [m["id"] for m in resp_list.data]
        self.assertIn(self.pub_module_inst1.id, module_ids)

        # Filter by published course
        resp_filtered = self.client.get(f"/api/courses/modules/?course={self.pub_course_inst1.id}")
        self.assertEqual(resp_filtered.status_code, status.HTTP_200_OK)
        filtered_ids = [m["id"] for m in resp_filtered.data]
        self.assertIn(self.pub_module_inst1.id, filtered_ids)

    def test_student_cannot_access_modules_of_unpublished_course(self):
        self.client.force_authenticate(user=self.student)

        # Detail view -> 404 Not Found
        resp = self.client.get(f"/api/courses/modules/{self.unpub_module_inst1.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # List view -> does NOT contain unpublished module
        resp_list = self.client.get("/api/courses/modules/")
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        module_ids = [m["id"] for m in resp_list.data]
        self.assertNotIn(self.unpub_module_inst1.id, module_ids)

        # Filter by unpublished course -> empty list
        resp_filtered = self.client.get(f"/api/courses/modules/?course={self.unpub_course_inst1.id}")
        self.assertEqual(resp_filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_filtered.data), 0)

    # ============================================================
    # C & D: LESSON VISIBILITY FOR STUDENTS
    # ============================================================

    def test_student_can_access_lessons_of_published_course(self):
        self.client.force_authenticate(user=self.student)

        # Detail view -> 200 OK
        resp = self.client.get(f"/api/courses/lessons/{self.pub_lesson_inst1.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], self.pub_lesson_inst1.id)

        # List view -> contains published lesson
        resp_list = self.client.get("/api/courses/lessons/")
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        lesson_ids = [l["id"] for l in resp_list.data]
        self.assertIn(self.pub_lesson_inst1.id, lesson_ids)

        # Filter by published module
        resp_filtered = self.client.get(f"/api/courses/lessons/?module={self.pub_module_inst1.id}")
        self.assertEqual(resp_filtered.status_code, status.HTTP_200_OK)
        filtered_ids = [l["id"] for l in resp_filtered.data]
        self.assertIn(self.pub_lesson_inst1.id, filtered_ids)

    def test_student_cannot_access_lessons_of_unpublished_course(self):
        self.client.force_authenticate(user=self.student)

        # Detail view -> 404 Not Found
        resp = self.client.get(f"/api/courses/lessons/{self.unpub_lesson_inst1.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # List view -> does NOT contain unpublished lesson
        resp_list = self.client.get("/api/courses/lessons/")
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        lesson_ids = [l["id"] for l in resp_list.data]
        self.assertNotIn(self.unpub_lesson_inst1.id, lesson_ids)

        # Filter by unpublished module -> empty list
        resp_filtered = self.client.get(f"/api/courses/lessons/?module={self.unpub_module_inst1.id}")
        self.assertEqual(resp_filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_filtered.data), 0)

    # ============================================================
    # E & F: INSTRUCTOR OWNERSHIP SCOPING
    # ============================================================

    def test_instructor_can_access_modules_and_lessons_for_own_course(self):
        self.client.force_authenticate(user=self.instructor1)

        # Instructor 1 can access their own unpublished module and lesson
        resp_mod = self.client.get(f"/api/courses/modules/{self.unpub_module_inst1.id}/")
        self.assertEqual(resp_mod.status_code, status.HTTP_200_OK)

        resp_les = self.client.get(f"/api/courses/lessons/{self.unpub_lesson_inst1.id}/")
        self.assertEqual(resp_les.status_code, status.HTTP_200_OK)

        # In list view, Instructor 1 sees both published and unpublished modules for own courses
        resp_mod_list = self.client.get("/api/courses/modules/")
        self.assertEqual(resp_mod_list.status_code, status.HTTP_200_OK)
        mod_ids = [m["id"] for m in resp_mod_list.data]
        self.assertIn(self.pub_module_inst1.id, mod_ids)
        self.assertIn(self.unpub_module_inst1.id, mod_ids)

    def test_instructor_cannot_access_another_instructors_course_content(self):
        self.client.force_authenticate(user=self.instructor1)

        # Instructor 1 cannot access Instructor 2's module or lesson
        resp_mod = self.client.get(f"/api/courses/modules/{self.module_inst2.id}/")
        self.assertEqual(resp_mod.status_code, status.HTTP_404_NOT_FOUND)

        resp_les = self.client.get(f"/api/courses/lessons/{self.lesson_inst2.id}/")
        self.assertEqual(resp_les.status_code, status.HTTP_404_NOT_FOUND)

        # Instructor 2's content does NOT appear in Instructor 1's list view
        resp_mod_list = self.client.get("/api/courses/modules/")
        mod_ids = [m["id"] for m in resp_mod_list.data]
        self.assertNotIn(self.module_inst2.id, mod_ids)

        resp_les_list = self.client.get("/api/courses/lessons/")
        les_ids = [l["id"] for l in resp_les_list.data]
        self.assertNotIn(self.lesson_inst2.id, les_ids)

    # ============================================================
    # G: ADMIN GLOBAL ACCESS
    # ============================================================

    def test_admin_can_access_modules_and_lessons_across_courses(self):
        self.client.force_authenticate(user=self.admin)

        # Admin can access Instructor 1's unpublished module and lesson
        resp_mod1 = self.client.get(f"/api/courses/modules/{self.unpub_module_inst1.id}/")
        self.assertEqual(resp_mod1.status_code, status.HTTP_200_OK)

        resp_les1 = self.client.get(f"/api/courses/lessons/{self.unpub_lesson_inst1.id}/")
        self.assertEqual(resp_les1.status_code, status.HTTP_200_OK)

        # Admin can access Instructor 2's module and lesson
        resp_mod2 = self.client.get(f"/api/courses/modules/{self.module_inst2.id}/")
        self.assertEqual(resp_mod2.status_code, status.HTTP_200_OK)

        resp_les2 = self.client.get(f"/api/courses/lessons/{self.lesson_inst2.id}/")
        self.assertEqual(resp_les2.status_code, status.HTTP_200_OK)

        # Admin list view includes all modules and lessons
        resp_mod_list = self.client.get("/api/courses/modules/")
        mod_ids = [m["id"] for m in resp_mod_list.data]
        self.assertIn(self.pub_module_inst1.id, mod_ids)
        self.assertIn(self.unpub_module_inst1.id, mod_ids)
        self.assertIn(self.module_inst2.id, mod_ids)

        resp_les_list = self.client.get("/api/courses/lessons/")
        les_ids = [l["id"] for l in resp_les_list.data]
        self.assertIn(self.pub_lesson_inst1.id, les_ids)
        self.assertIn(self.unpub_lesson_inst1.id, les_ids)
        self.assertIn(self.lesson_inst2.id, les_ids)

    # ============================================================
    # H: STUDENT CANNOT CREATE MODULES OR LESSONS
    # ============================================================

    def test_student_cannot_create_modules_or_lessons(self):
        self.client.force_authenticate(user=self.student)

        resp_mod = self.client.post("/api/courses/modules/", {
            "course": self.pub_course_inst1.id,
            "title": "Malicious Module",
            "order": 99
        })
        self.assertEqual(resp_mod.status_code, status.HTTP_403_FORBIDDEN)

        resp_les = self.client.post("/api/courses/lessons/", {
            "module": self.pub_module_inst1.id,
            "title": "Malicious Lesson",
            "content": "Malicious content",
            "order": 99
        })
        self.assertEqual(resp_les.status_code, status.HTTP_403_FORBIDDEN)
