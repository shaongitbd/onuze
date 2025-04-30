from django import forms
from .models import Post, PostImage

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'community', 'post_type']
        
class PostImageForm(forms.ModelForm):
    class Meta:
        model = PostImage
        fields = ['image_url', 'order']
        widgets = {
            'image_url': forms.FileInput(attrs={'accept': 'image/*'}),
        }
        
PostImageFormSet = forms.inlineformset_factory(
    Post, PostImage, form=PostImageForm,
    extra=3, max_num=10, can_delete=True
) 