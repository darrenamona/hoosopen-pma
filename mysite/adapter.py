from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
# Author: NKSM
# Date: 12/22/2023
# URL: https://stackoverflow.com/questions/77703624/custom-adapter-inheriting-from-defaultsocialaccountadapter-in-django-allauth-thr
# Social Account Adapter hook to edit the default user's username to be their email
class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super(SocialAccountAdapter, self).save_user(request, sociallogin, form=None)
        user.username = user.email
        user.save()
        return user