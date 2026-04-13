from django.contrib import admin
from django.urls import include, path

from members.urls import auth_urlpatterns, members_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include(auth_urlpatterns)),
    path("api/members/", include(members_urlpatterns)),
]
