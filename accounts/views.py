from .models import User
from .permissions import IsVerified
from .serializers import SignUpSerializer, LoginSerializer, UserInfoSerializer
from .utils import send_verification_email, send_password_reset_email
import jwt, os
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from dotenv import load_dotenv
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

load_dotenv()


@api_view(['POST'])
def sign_up_view(request):
    if request.method == 'POST':
        serializer = SignUpSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            user = User.objects.get(email=serializer.validated_data['email'])
            token = RefreshToken.for_user(user)
            current_site = get_current_site(request).domain
            relative_link = reverse('verify_user')
            absolute_url = f'http://{current_site}{relative_link}?token={token}'
            link = str(absolute_url)
            send_verification_email(username=user.username, email=user.email, link=link)

            return Response(
                {
                    'success':True,
                    'user':serializer.data
                }, status=status.HTTP_201_CREATED
            )
        return Response(
            {
                'success':False,
                'user':serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def verify_user_view(request):
    if request.method == 'GET':
        token = request.GET.get('token')

        try:
            payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])

            if not user.is_verified:
                user.is_verified = True
                user.save()
            
            return Response(
                {
                    'success':True,
                    'message':'User has been successfully verified.'
                }, status=status.HTTP_200_OK
            )
        except jwt.ExpiredSignatureError as e:
            return Response(
                {
                    'success':False,
                    'message':'Activation link expired.'
                }, status=status.HTTP_400_BAD_REQUEST
            )
        except jwt.exceptions.DecodeError as e:
            return Response(
                {
                    'success':False,
                    'message':'Invalid token.'
                }, status=status.HTTP_400_BAD_REQUEST
            )
        except jwt.exceptions.InvalidTokenError as e:
            return Response(
                {
                    'success':False,
                    'message':'Invalid token.'
                }, status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist as e:
            return Response(
                {
                    'success':False,
                    'message':'User not found'
                }, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    'success':False,
                    'message':str(e)
                }, status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['POST'])
def login_view(request):
    if request.method == 'POST':
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            tokens = serializer.generate_jwt_tokens(serializer.validated_data)

            return Response(
                {
                    'success':True,
                    'message':'Login successful',
                    'tokens':tokens
                }, status=status.HTTP_200_OK
            )


@api_view(['POST'])
def password_reset_view(request):
    if request.method == 'POST':
        email = request.data.get('email')

        if not email:
            return Response(
                {
                    'success':False,
                    'message':'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            current_site = get_current_site(request).domain
            relative_link = reverse('password_reset_confirm')
            absolute_url = f'http://{current_site}{relative_link}?uid={uid}&token={token}'
            link = str(absolute_url)
            send_password_reset_email(username=user.username, email=user.email, link=link)

            return Response(
                {
                    'success':True,
                    'message':'Password reset email sent'
                }, status=status.HTTP_200_OK
            )
        except User.DoesNotExist as e:
            return Response(
                {
                    'success':False,
                    'message':'User not found.'
                }, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    'success':False,
                    'message':str(e)
                }, status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['PATCH'])
def password_reset_confirm_view(request):
    if request.method == 'PATCH':
        uid = request.data.get('uid')
        token = request.data.get('token')
        password = request.data.get('password')

        if not uid and not token and not password:
            return Response(
                {
                    'success':False,
                    'message':'All fields are required'
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_id = urlsafe_base64_decode(uid)
            user = User.objects.get(id=user_id)

            if not default_token_generator.check_token(user, token):
                return Response(
                    {
                        'success':False,
                        'message':'Invalid token.'
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(password)
            user.save()

            return Response(
                {
                    'success':True,
                    'message':'Password reset successful'
                }, status=status.HTTP_200_OK
            )
        except User.DoesNotExist as e:
            return Response(
                {
                    'success':False,
                    'message':'User not found.'
                }, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    'success':False,
                    'message':str(e)
                }, status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_specific_user_view(request, uid:str):
    if request.method == 'GET':
        try:
            user = User.objects.get(id=uid)
        except User.DoesNotExist:
            return Response(
                {
                    'success':False,
                    'message':'User not found'
                }, status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UserInfoSerializer(user)

        return Response(
            {
                'success':True,
                'user':serializer.data
            }, status=status.HTTP_200_OK
        )

    
@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_all_users_view(request):
    if request.method == 'GET':
        users = User.objects.all()
        serializer = UserInfoSerializer(users, many=True)

        return Response(
            {
                'success':True,
                'users':serializer.data
            }, status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([IsVerified])
def search_users_view(request):
    if request.method == 'GET':
        query = request.query_params.get('query')

        if not query:
            return Response(
                {
                    'success':False,
                    'message':'Please provide a search query'
                }, status=status.HTTP_400_BAD_REQUEST
            )

        users = User.objects.filter(
            Q(name__icontains=query) |
            Q(username__icontains=query) 
        )

        serializer = UserInfoSerializer(users, many=True)

        return Response(
            {
                'success':True,
                'message':'Below are your search results',
                'users':serializer.data
            }, status=status.HTTP_200_OK
        )