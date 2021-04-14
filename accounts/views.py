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

# Create your views here.

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
            dict_post['email'] = request.query_params['email']
        elif 'email' in request.query_params:
            dict_post['email'] = request.query_params['email']
        new_user = create_user(dict_post)
        if new_user is not None:
            save_user_agent(new_user, request.META['HTTP_USER_AGENT'], 0)
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
                    host = request.META['HTTP_HOST']
                    if 'kiwilex' in host:
                        host = 'https://' + host
                    else:
                        host = 'http://' + host
                    activation_key = generate_confirmation_email_key(new_user)
                    try:
                        if 'is_business' in self.request.GET:
                            send_email_confirmation(
                                new_user, host, activation_key, True)
                        else:
                            send_email_confirmation(
                                new_user, host, activation_key)
                    except:
                        error_requests_logger.info(
                            parse_error_requests_log(
                                self.request.META,
                                self.request.data,
                                None,
                                'ERROR SEND EMAIL CONFIRMATION IN REGISTER'
                            )
                        )
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
            application = Application.objects.get(name="KIWIREST")
            app = ApplicationSerializer(application)
            # url = ("http://"+request.META['HTTP_HOST']+"/o/token/?grant_type=password&" +
            #       "client_id=" + app['client_id'].value + "&" +
            #       "client_secret=" + app['client_secret'].value + "&" +
            #       "username=" + new_user.username + "&" +
            #       "password=" + dict_post['password'] + "&" +
            #       "date=" + str(timezone.now()))
            #request_content = requests.post(url)
            #r_json = request_content.json()
            # rest = {'access_token': r_json['access_token'],
            #        'refresh_token': r_json['refresh_token'],
            #        'client_id': app['client_id'].value,
            #        'client_secret': app['client_secret'].value}
            rest = create_token(new_user.username, dict_post['password'], request,
                                is_authenticated)
            user = UserSerializer(new_user, context=context)
            response_dict = {'rest': rest, 'user': user.data,
                             'status': True, 'app': app.data}
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
            if 'code' in request.query_params:
                id_prom_code = request.query_params['code']
                prom_code = PromotionalCode.objects.filter(id=id_prom_code)
                if prom_code.exists():
                    prom_code = prom_code.last()
                    user_promo = UserInvitationCode.objects.filter(
                        user=new_user,
                        promotional_code=prom_code
                    )
                    if not user_promo.exists():
                        UserInvitationCode.objects.create(
                            user=new_user,
                            promotional_code=prom_code
                        )
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
                    if 'business' in request.GET:
                        if not (UserInstitution.objects
                                .filter(user=user, role_by_institution__id=2,
                                        is_active=True)
                                .exists()):
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
                # if user.userdata.user_pass is not None:
                #    password = user.userdata.user_pass
                # else:
                #    password = '1234'
                # user_fb = authenticate(username=user.username,
                #                       password=password)
                # if user_fb:
                #    login(request, user_fb)
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
            if 'business' in request.GET:
                application = Application.objects.get(name="KIWICOURSEREST")
                tokens = AccessToken.objects.filter(
                    user=user, expires__gt=timezone.now(),
                    application=application
                )
                if tokens.count() < settings.LIMIT_LOGIN_USERS:
                    rest = create_token(
                        user.username, password, request, is_authenticated)
                else:
                    first_token = tokens.first()
                    first_token.delete()
                    rest = create_token(
                        user.username, password, request, is_authenticated)
            else:
                application = Application.objects.get(name="KIWIREST")
                if AccessToken.objects.filter(user=user,
                                              expires__gt=timezone.now(),
                                              application=application).exists():
                    token = AccessToken.objects.filter(user=user,
                                                       expires__gt=timezone.now(),
                                                       application=application).last()
                    rest = TokenSerializer(token, context=context).data
                else:
                    if AccessToken.objects.filter(user=user).exists():
                        AccessToken.objects.filter(user=user).last()
                    rest = create_token(user.username, password, request,
                                        is_authenticated)
            person = UserData.objects.filter(user=user)
            id_person = None
            if person.exists():
                id_person = person.last().id_kiwilex
            user = UserSerializer(user, context=context)
            is_tutor = Tutor.objects.filter(user=obj_user).exists()
            is_tutor_kiwilex = Tutor.objects.filter(user=obj_user,
                                                    is_team=True).exists()
            user_data = UserData.objects.filter(user=obj_user).last()
            is_beta = user_data.is_beta
            institution = None
            if 'business' in self.request.GET:
                user_data.times_logged += 1
                user_data.save()
                institution = get_my_institution(user.data['id'], False)
                if institution:
                    institution = {'id': institution.id,
                                   'image': institution.image,
                                   'name': institution.name,
                                   'full_name': institution.full_name}
            country = {'name': '', 'has_exams': None}
            student_inst = StudentInstitution.objects.filter(
                student_id=user.data['id'],
                institution__country__isnull=False
            )
            if student_inst.exists():
                country_obj = student_inst.last().institution.country
                country = {
                    'name': country_obj.name,
                    'has_exams': Exam.objects.filter(
                        institution__country__id=country_obj.id
                    ).exists()
                }
            succesful_response = {
                'rest': rest, 'user': user.data, 'status': True,
                'is_tutor': is_tutor,
                'country': country,
                'is_beta': is_beta, 'institution': institution,
                'is_tutor_kiwilex': is_tutor_kiwilex,
                'id_kiwilex': id_person
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