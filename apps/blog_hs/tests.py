from django.core.urlresolvers import reverse
from django import test
from healers.models import Healer
from mezzanine.generic.models import Keyword, AssignedKeyword
from mezzanine.blog.models import BlogPost as Post
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED, CONTENT_STATUS_DRAFT


class BlogTest(test.TestCase):
	fixtures = ['hs_auth.json', 'client.json', 'healers.json', 'oauth.json',
		'locations.json']

	def setUp(self):
		# get client from fixture, update user password and make login
		self.test_healer = Healer.objects.get(pk=1)
		self.test_healer.user.set_password('test')
		self.test_healer.user.save()
		result_login = self.client.login(email=self.test_healer.user.email, password='test')
		self.assertTrue(result_login)
		self.data = {
			'title': 'title',
			'content': '''<div style="color: red;">test</div><div>test1test1test
			1test1test1test1test1test1test1test1test1test1test1test1test1test1te
			st1test1test1test1test1test1test1test1test1test1test1test1test1test1
			test1test1test1test1test1test1test1test1test1test1test1test1test1tes
			t1test1test1test1test1test1test1test1test1test1test1test1test1test1t
			est1test1test1test1test1test1test1test1test1test1test1test1test1test
			1test1test1test1test1test1test1test1test1test1test1</div>''',
			'status': CONTENT_STATUS_DRAFT,
			'action': 'create'}


class BlogNewTest(BlogTest):

	def test_post_fail(self):
		self.data['content'] = 'test'
		self.data['status'] = CONTENT_STATUS_PUBLISHED
		response = self.client.post(reverse('blog_new'), self.data)
		self.assertIn('Your blog post must be at least 400 characters long to be published.',
			response.content)

	def test_post_success(self):
		self.client.post(reverse('blog_new'), self.data)
		post = Post.objects.get(user=self.test_healer.user)
		self.assertEqual(post.title, self.data['title'])
		self.assertEqual(post.content, '<div style="">\n   test\n  </div>\n  <div>\n   test1test1test\n\t\t\t1test1test1test1test1test1test1test1test1test1test1test1test1test1te\n\t\t\tst1test1test1test1test1test1test1test1test1test1test1test1test1test1\n\t\t\ttest1test1test1test1test1test1test1test1test1test1test1test1test1tes\n\t\t\tt1test1test1test1test1test1test1test1test1test1test1test1test1test1t\n\t\t\test1test1test1test1test1test1test1test1test1test1test1test1test1test\n\t\t\t1test1test1test1test1test1test1test1test1test1test1\n  </div>')
		self.assertEqual(post.description.strip(), 'test\n  \n  \n   test1test1test\n\t\t\t1test1test1test1test1test1test1test1test1test1test1test1test1test1te\n\t\t\tst1test1test1test1test1test1test1test1test1test1test1test1test1test1\n\t\t\ttest1test1test1test1test1test1test1test1test1test1test1test1test1tes\n\t\t\tt1test1test1test1test1test1test1test1test1test1test1test1test1test1t\n\t\t\test1test1test1test1test1test1test1test1test1test1test1test1test1test\n\t\t\t1test1test1test1test1test1test1test1test1test1test1')
		self.assertEqual(post.status, CONTENT_STATUS_DRAFT)


class BlogUpdateTest(BlogTest):

	def test_post(self):
		self.data['action'] = 'update'
		post = Post.objects.create(title='title1', content='body1', user=self.test_healer.user)
		self.client.post(reverse('blog_edit', args=[post.pk]), self.data)
		post = Post.objects.get(pk=post.pk)
		self.assertEqual(post.title, self.data['title'])
		self.assertEqual(post.content, '<div style="">\n   test\n  </div>\n  <div>\n   test1test1test\n\t\t\t1test1test1test1test1test1test1test1test1test1test1test1test1test1te\n\t\t\tst1test1test1test1test1test1test1test1test1test1test1test1test1test1\n\t\t\ttest1test1test1test1test1test1test1test1test1test1test1test1test1tes\n\t\t\tt1test1test1test1test1test1test1test1test1test1test1test1test1test1t\n\t\t\test1test1test1test1test1test1test1test1test1test1test1test1test1test\n\t\t\t1test1test1test1test1test1test1test1test1test1test1\n  </div>')
		self.assertEqual(post.description.strip(), 'test\n  \n  \n   test1test1test\n\t\t\t1test1test1test1test1test1test1test1test1test1test1test1test1test1te\n\t\t\tst1test1test1test1test1test1test1test1test1test1test1test1test1test1\n\t\t\ttest1test1test1test1test1test1test1test1test1test1test1test1test1tes\n\t\t\tt1test1test1test1test1test1test1test1test1test1test1test1test1test1t\n\t\t\test1test1test1test1test1test1test1test1test1test1test1test1test1test\n\t\t\t1test1test1test1test1test1test1test1test1test1test1')
		self.assertEqual(post.status, CONTENT_STATUS_PUBLISHED)
