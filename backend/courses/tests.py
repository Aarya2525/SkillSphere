from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from test_utils.base import FAST_HASHERS_OVERRIDE
from .models import Course, Module, Lesson

User = get_user_model()


@FAST_HASHERS_OVERRIDE
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

    # ============================================================
    # I: STAGE 18 SECURITY: CROSS-INSTRUCTOR IDOR PROTECTION
    # ============================================================

    def test_instructor_cannot_move_module_to_another_instructors_course(self):
        self.client.force_authenticate(user=self.instructor1)
        response = self.client.patch(
            f"/api/courses/modules/{self.pub_module_inst1.id}/",
            {"course": self.course_inst2.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.pub_module_inst1.refresh_from_db()
        self.assertEqual(self.pub_module_inst1.course_id, self.pub_course_inst1.id)

    def test_instructor_cannot_move_lesson_to_another_instructors_module(self):
        self.client.force_authenticate(user=self.instructor1)
        response = self.client.patch(
            f"/api/courses/lessons/{self.pub_lesson_inst1.id}/",
            {"module": self.module_inst2.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.pub_lesson_inst1.refresh_from_db()
        self.assertEqual(self.pub_lesson_inst1.module_id, self.pub_module_inst1.id)


@FAST_HASHERS_OVERRIDE
class CourseManagementLifecycleTests(APITestCase):
    """
    Stage 17: Comprehensive testing for Course Management, CRUD,
    publishing lifecycles, and authorization boundaries.
    """

    def setUp(self):
        self.instructor1 = User.objects.create_user(
            username="course_inst1",
            email="course_inst1@example.com",
            password="password123",
            role=User.Role.INSTRUCTOR,
        )
        self.instructor2 = User.objects.create_user(
            username="course_inst2",
            email="course_inst2@example.com",
            password="password123",
            role=User.Role.INSTRUCTOR,
        )
        self.student = User.objects.create_user(
            username="course_student",
            email="course_student@example.com",
            password="password123",
            role=User.Role.STUDENT,
        )
        self.admin = User.objects.create_user(
            username="course_admin",
            email="course_admin@example.com",
            password="password123",
            role=User.Role.ADMIN,
        )

        self.course1 = Course.objects.create(
            instructor=self.instructor1,
            title="Python Fundamentals",
            description="Learn Python from scratch",
            is_published=False,
        )

    # 1. Course creation
    def test_instructor_can_create_course(self):
        self.client.force_authenticate(user=self.instructor1)
        response = self.client.post("/api/courses/", {
            "title": "Django Deep Dive",
            "description": "Advanced Django architecture.",
            "is_published": True,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Django Deep Dive")
        self.assertEqual(response.data["instructor"], self.instructor1.id)

    # 2. Student cannot create course
    def test_student_cannot_create_course(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post("/api/courses/", {
            "title": "Hacked Course",
            "description": "Unauthorized creation attempt.",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 3. Course update
    def test_instructor_can_update_own_course(self):
        self.client.force_authenticate(user=self.instructor1)
        response = self.client.patch(f"/api/courses/{self.course1.id}/", {
            "title": "Python 3.12 Fundamentals Updated",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Python 3.12 Fundamentals Updated")

    # 4. Another instructor cannot update course
    def test_instructor_cannot_update_another_instructors_course(self):
        self.client.force_authenticate(user=self.instructor2)
        response = self.client.patch(f"/api/courses/{self.course1.id}/", {
            "title": "Hijacked Course",
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 5. Course delete
    def test_instructor_can_delete_own_course(self):
        self.client.force_authenticate(user=self.instructor1)
        response = self.client.delete(f"/api/courses/{self.course1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Course.objects.filter(id=self.course1.id).exists())

    # 6. Student cannot delete course
    def test_student_cannot_delete_course(self):
        self.course1.is_published = True
        self.course1.save()
        self.client.force_authenticate(user=self.student)
        response = self.client.delete(f"/api/courses/{self.course1.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 7. Publish and unpublish toggle
    def test_publish_unpublish_course_lifecycle(self):
        self.client.force_authenticate(user=self.instructor1)
        # Publish
        res_pub = self.client.patch(f"/api/courses/{self.course1.id}/", {"is_published": True})
        self.assertEqual(res_pub.status_code, status.HTTP_200_OK)
        self.assertTrue(res_pub.data["is_published"])

        # Unpublish
        res_unpub = self.client.patch(f"/api/courses/{self.course1.id}/", {"is_published": False})
        self.assertEqual(res_unpub.status_code, status.HTTP_200_OK)
        self.assertFalse(res_unpub.data["is_published"])

    # 8. Unpublished course visibility
    def test_unpublished_course_visibility_boundaries(self):
        # Owner can view
        self.client.force_authenticate(user=self.instructor1)
        self.assertEqual(self.client.get(f"/api/courses/{self.course1.id}/").status_code, status.HTTP_200_OK)

        # Admin can view
        self.client.force_authenticate(user=self.admin)
        self.assertEqual(self.client.get(f"/api/courses/{self.course1.id}/").status_code, status.HTTP_200_OK)

        # Another instructor cannot view (404)
        self.client.force_authenticate(user=self.instructor2)
        self.assertEqual(self.client.get(f"/api/courses/{self.course1.id}/").status_code, status.HTTP_404_NOT_FOUND)

        # Student cannot view (404)
        self.client.force_authenticate(user=self.student)
        self.assertEqual(self.client.get(f"/api/courses/{self.course1.id}/").status_code, status.HTTP_404_NOT_FOUND)

    # 9. Module and Lesson creation by owner
    def test_instructor_can_create_module_and_lesson(self):
        self.client.force_authenticate(user=self.instructor1)
        res_mod = self.client.post("/api/courses/modules/", {
            "course": self.course1.id,
            "title": "Module 1",
            "order": 1,
        })
        self.assertEqual(res_mod.status_code, status.HTTP_201_CREATED)
        module_id = res_mod.data["id"]

        res_les = self.client.post("/api/courses/lessons/", {
            "module": module_id,
            "title": "Lesson 1",
            "content": "Lesson content here.",
            "order": 1,
        })
        self.assertEqual(res_les.status_code, status.HTTP_201_CREATED)

    # 10. Instructor cannot add module to another instructor's course
    def test_instructor_cannot_add_module_to_another_instructors_course(self):
        self.client.force_authenticate(user=self.instructor2)
        response = self.client.post("/api/courses/modules/", {
            "course": self.course1.id,
            "title": "Intruder Module",
            "order": 1,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 11. Invalid IDs return 404
    def test_invalid_course_module_lesson_ids_return_404(self):
        self.client.force_authenticate(user=self.instructor1)
        self.assertEqual(self.client.get("/api/courses/999999/").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.get("/api/courses/modules/999999/").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.get("/api/courses/lessons/999999/").status_code, status.HTTP_404_NOT_FOUND)

    # 12. Serializer validation
    def test_course_serializer_validation_empty_title(self):
        self.client.force_authenticate(user=self.instructor1)
        response = self.client.post("/api/courses/", {
            "title": "",
            "description": "Valid description.",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "validation_error")
