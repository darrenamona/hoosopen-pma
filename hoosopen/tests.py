import datetime
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from .models import *
from time import sleep

class MessageModelTests(TestCase):
    @classmethod
    def setUpClass(self):
        self.user = User(username="test@gmail.com")
        self.user.save()
        self.userprofile = self.user.userprofile
        self.project = Project(creator=self.userprofile)
        self.project.save()
    @classmethod
    def tearDownClass(self):
        self.user.delete()
        self.project.delete()
    def test_message_postdate(self):
        datetime_before = timezone.now()
        sleep(1)
        message1 = Message(user_profile=self.userprofile,
                          project=self.project,
                          message="test")
        message1.save()
        self.assertTrue(message1.post_date >= datetime_before)
        sleep(1)
        message2 = Message(user_profile=self.userprofile,
                          project=self.project,
                          message="test2")
        message2.save()
        latest_messages = sorted(Message.objects.all(), key=lambda x: x.post_date, reverse=True)
        self.assertTrue(latest_messages[0].message == "test2")
        self.assertTrue(latest_messages[1].message == "test")


    def test_message_testcorrect(self):
        message = Message(user_profile=self.userprofile,
                          project=self.project,
                          message="test")
        message.save()
        self.assertTrue(message.message == "test")

class ProjectMessagesViewTests(TestCase):
    @classmethod
    def setUpClass(self):
        self.user = User(username="test@gmail.com")
        self.user.save()
        self.c = Client()
        self.c.force_login(user=self.user)
        self.userprofile = self.user.userprofile
        self.project = Project(creator=self.userprofile)
        self.project.save()
        self.messages = [Message(user_profile=self.userprofile,
                          project=self.project,
                          message="this is my test message!")]
        
        self.extrauser = User(username="extrauser@gmail.com")
        self.extrauser.save()
        self.extrauserc = Client()
        self.extrauserc.force_login(user=self.extrauser)
    @classmethod
    def tearDownClass(self):
        User.objects.all().delete()
        Project.objects.all().delete()
        Message.objects.all().delete()
    def test_empty_messages(self):
        url = reverse("messages", args=(self.project.pk,))
        response = self.c.get(url)
        self.assertContains(response, 'No messages!')
        self.assertEqual(response.status_code, 200)
    def test_singlemessages(self):
        self.messages[0].save()
        url = reverse("messages", args=(self.project.pk,))
        response = self.c.get(url)
        self.assertContains(response, 'this is my test message!')
        self.assertEqual(response.status_code, 200)
    def test_post_question(self):
        url = reverse("messages", args=(self.project.pk,))
        response = self.c.post(url, {'text': 'this is a real authentic message!', 'action': 'create'})
        self.assertEqual(response.status_code, 200)
        response = self.c.get(url)
        self.assertContains(response, 'this is a real authentic message!')
    def test_unauthenticated_post(self):
        url = reverse("messages", args=(self.project.pk,))
        response = self.extrauserc.post(url, {'text': 'this shouldn\'t get posted!'})
        self.assertEqual(response.status_code, 403)
        response = self.c.get(url)
        self.assertContains(response, 'No messages!')
    
class CreateUserProfileTest(TestCase):
    @classmethod
    def tearDownClass(self):
        User.objects.all().delete()
    def test_userprofile_created(self):
        user = User(username="test@gmail.com")
        user.save()
        userprofile = user.userprofile
        self.assertIsNotNone(userprofile)
        self.assertEqual(userprofile.user, user)
    def test_userprofile_deletecascade(self):
        user = User(username="test@gmail.com")
        user.save()
        user.delete()
        length = len(UserProfile.objects.all())
        self.assertEqual(length, 0)
