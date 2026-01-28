from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from user.serializers import UserSerializer


class ManageUserView(generics.RetrieveUpdateAPIView):
    def get_object(self):
        return self.request.user

    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
