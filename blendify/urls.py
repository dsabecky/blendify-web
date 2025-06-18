####################################################################
# Module Imports
####################################################################


from django.contrib import admin
from django.urls import path, include


####################################################################
# Define URLs
####################################################################

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include('social_django.urls', namespace='social')),
    path('', include('core.urls')), # load in our user facing urls
]
