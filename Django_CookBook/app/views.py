from django.shortcuts import render

# Create your views here.
# class ProductForm(forms.ModelForm):
#     # Add some custom validation to our image field
#     def clean_image(self):
#         image = self.cleaned_data.get('image', False)
#         if image:
#             if image._size > 4*1024*1024:
#                 raise ValidationError("Image file too large ( > 4mb )")
#             return image
#         else:
#             raise ValidationError("Couldn't read uploaded image")