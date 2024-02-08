from .models import User
from rest_framework import serializers


class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=50, min_length=8, write_only=True)

    class Meta:
        model = User
        fields = ['name', 'gender', 'email', 'username', 'dob', 'address', 'phone_number', 'license_number', 'password']

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        phone_number = attrs.get('phone_number')
        license_number = attrs.get('license_number')

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError('This username is already in use.')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('This email is already in use.')
        if User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError('This phone number is already in use.')
        if User.objects.filter(license_number=license_number).exists():
            raise serializers.ValidationError('This license number is already in use.')
        
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            name=validated_data['name'],
            gender=validated_data['gender'],
            dob=validated_data['dob'],
            username=validated_data['username'],
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            license_number=validated_data['license_number'],
            address=validated_data['address']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
