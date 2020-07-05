from rest_framework import routers

app_name = 'trainerdex.api:v2'

# Unlike version 1, version 2 will include the User and Trainer object on one API call. Creating a User object will wait until the Trainer object is created too before returning the response.
# All Nickname objects will return along with specification as to which one is active.

router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)

urlpatterns = router.urls
