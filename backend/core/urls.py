from django.contrib import admin
from django.urls import include, path

from members.urls import admin_urlpatterns, auth_urlpatterns, members_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include(auth_urlpatterns)),
    path("api/members/", include(members_urlpatterns)),
    path("api/admin/", include(admin_urlpatterns)),
    path("api/chats/", include("chats.urls")),
]
