import logging

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from oauth2_provider.models import Application, AccessToken
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication

from accounts.utils import create_user
# Create your views here.
logger = logging.getLogger('login_logger')

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

class RegisterUserAPI(APIView):
    """ API used to register a user """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        response_dict = {}
        dict_post = {}
        context = {'request': request}
        login_type = request.query_params['loginType']
        dict_post['firstName'] = request.query_params['firstName']
        dict_post['lastName'] = request.query_params['lastName']
        dict_post['password'] = request.query_params['password']
        is_authenticated = False
        if login_type == 'facebook':
            user_found = False
            generated_email = (
                dict_post['firstName'].replace(' ', '_').lower() + '_'
                + dict_post['lastName'].replace(' ', '_').lower()
                + '@facebook.com'
            )
            if 'facebookId' in request.query_params:
                id_facebook = request.query_params['facebookId']
                facebook_user = FacebookUser.objects.filter(
                    id_facebook=id_facebook
                )
                if facebook_user.exists():
                    fb_user = facebook_user.first().user
                    if 'email' in request.query_params:
                        fb_user.email = request.query_params['email']
                        fb_user.save()
                    dict_post['email'] = fb_user.email
                    user_found = True
                else:
                    generated_email = id_facebook + '@facebook.com'
            if not user_found:
                if 'email' in request.query_params:
                    if request.query_params['email'] == 'undefined':
                        dict_post['email'] = generated_email
                    else:
                        dict_post['email'] = request.query_params['email']
                else:
                    dict_post['email'] = generated_email
        elif login_type == 'google':
            if 'googleId' in request.query_params:
                id_google = request.query_params['googleId']
                if google_user.exists():
                    user_found = True
            if 'email' in request.data:
                dict_post['email'] = request.data['email']
            dict_post['email'] = request.query_params['email']
        elif 'email' in request.query_params:
            dict_post['email'] = request.query_params['email']
        new_user = create_user(dict_post)
        print(new_user)
        if new_user is not None:
            print("new_user")
            if login_type == 'facebook':
                new_user.userdata.is_fb_user = True
                new_user.userdata.save()
                if new_user.userdata.user_pass is not None:
                    dict_post['password'] = new_user.userdata.user_pass
                if 'facebookId' in request.query_params:
                    id_facebook = request.query_params['facebookId']
                    FacebookUser.objects.create(user=new_user,
                                                id_facebook=id_facebook)
            elif login_type == 'google':
                new_user.userdata.is_google_user = True
                new_user.userdata.save()
                if new_user.userdata.user_pass is not None:
                    dict_post['password'] = new_user.userdata.user_pass
                if 'googleId' in request.query_params:
                    id_google = request.query_params['googleId']
                    GoogleUser.objects.create(user=new_user,
                                              id_google=id_google)
            else:
                print('no social network register')
            if new_user and login_type != 'facebook' and login_type != 'google':
                new_user_auth = authenticate(username=new_user.username,
                                             password=dict_post['password'])
                if new_user_auth:
                    is_authenticated = True
                    login(request, new_user_auth)
                else:
                    response_dict = {'status': False, 'app': {'status': False}}
                    try:
                        logger.info(
                            parse_login_request_log(
                                request.META,
                                request.query_params.items(),
                                response_dict.items(),
                                not new_user_auth,
                                False
                            )
                        )
                    except:
                        print('Error login log')
                    return Response(response_dict)
            response_dict = {'status': True}
            try:
                logger.info(
                    parse_login_request_log(
                        request.META,
                        request.query_params.items(),
                        response_dict.items(),
                        not new_user,
                        True
                    )
                )
            except:
                print('Error login log')
            return Response(response_dict, status=status.HTTP_200_OK)
        response_dict = {'status': False,
                         'app': {'status': False},
                         'email': dict_post['email']}
        try:
            logger.info(
                parse_login_request_log(
                    request.META,
                    request.query_params.items(),
                    response_dict.items(),
                    not new_user,
                    False
                )
            )
        except:
            print('Error login log')
        return Response(response_dict)

class AuthenticateUserAPI(APIView):
    """ API to authenticate a user """
    # Still used but DEPRECATED, change future calls to new authenticate api
    permission_classes = [AllowAny]

    def get(self, request):
        """ Get method for the authentication of a user """
        context = {'request': request}
        if ('email' not in self.request.query_params or
            'password' not in self.request.query_params or
                'loginType' not in self.request.query_params):
            try:
                logger.info(
                    parse_login_request_log(
                        request.META,
                        request.query_params.items(),
                        {'Kiwilex': 'Descarga nuestra aplicación aqui http://kiwilex.com/kiwi-info/'}.items(),
                        True,
                        False
                    )
                )
            except:
                print('Error login log')
            return Response({'Kiwilex', 'Descarga nuestra aplicación aqui https://kiwilex.com/kiwi-info/'})
        email = self.request.query_params['email']
        password = request.query_params['password']
        login_type = request.query_params['loginType']
        obj_user = None
        user = None
        is_authenticated = False
        response_error_dict = {'status': False, 'app': {'status': False}}
        if User.objects.filter(email=email, is_active=True).exists():
            obj_user = User.objects.filter(email=email, is_active=True).last()
            if login_type == 'native':
                user = authenticate(username=obj_user.username,
                                    password=password)
                if user:
                    is_authenticated = True
                    login(request, user)
                else:
                    try:
                        logger.info(
                            parse_login_request_log(
                                request.META,
                                request.query_params.items(),
                                response_error_dict.items(),
                                not user,
                                False
                            )
                        )
                    except:
                        print('Error login log')
                    return Response(response_error_dict)
            else:
                user = obj_user
        if user:
            if login_type == 'facebook':
                user.userdata.is_fb_user = True
                user.userdata.save()
                if 'facebookId' in request.query_params:
                    if not FacebookUser.objects.filter(user=user).exists():
                        id_facebook = request.query_params['facebookId']
                        FacebookUser.objects.create(user=user,
                                                    id_facebook=id_facebook)
                # else:
                #    return Response({'status': False, 'app': {'status': False}})
            elif login_type == 'google':
                user.userdata.is_google_user = True
                user.userdata.save()
                #password = '1234'
                # user_google = authenticate(username=user.username,
                #                           password=password)
                # if user_google:
                #    login(request, user_google)
                if 'googleId' in request.query_params:
                    if not GoogleUser.objects.filter(user=user).exists():
                        id_google = request.query_params['googleId']
                        GoogleUser.objects.create(user=user,
                                                  id_google=id_google)
                # else:
                #    return Response({'status': False, 'app': {'status': False}})
            rest = None
            person = UserData.objects.filter(user=user)
            id_person = None
            if person.exists():
                id_person = person.last().id_kiwilex
            user = UserSerializer(user, context=context)
            user_data = UserData.objects.filter(user=obj_user).last()
            succesful_response = {
                'rest': rest, 'user': user.data, 'status': True,
            }
            try:
                logger.info(
                    parse_login_request_log(
                        request.META,
                        request.query_params.items(),
                        succesful_response.items(),
                        not user,
                        True
                    )
                )
            except:
                print('Error login log')
            return Response(succesful_response, status=status.HTTP_200_OK)
        try:
            logger.info(
                parse_login_request_log(
                    request.META,
                    request.query_params.items(),
                    response_error_dict.items(),
                    not user,
                    False
                )
            )
        except:
            print('Error login log')
        return Response(response_error_dict)