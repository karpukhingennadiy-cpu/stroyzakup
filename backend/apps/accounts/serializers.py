from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name")
    def create(self, data):
        data.setdefault('username', data['email'])
        return User.objects.create_user(**data)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "role", "is_staff")
        read_only_fields = ("is_staff",)
