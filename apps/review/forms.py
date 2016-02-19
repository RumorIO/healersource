from django import forms
from review.models import Review

class ReviewForm(forms.ModelForm):
	title = forms.CharField(max_length=255, min_length=8)
	review = forms.CharField(min_length=20, widget=forms.Textarea())

	def __init__(self, *args, **kwargs):
		super(ReviewForm, self).__init__(*args, **kwargs)
		self.fields['rating'].widget = forms.HiddenInput()
		self.fields['rating'].label = "How do you rate this Provider?"
		self.fields['title'].label = "Please enter a title for your review"
		self.fields['review'].label = "Write your review"

	class Meta:
		model = Review
		fields = ('rating', 'title', 'review')