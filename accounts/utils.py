from django.contrib.auth.models import User
from accounts.models import UserData

def create_username(first_name, last_name):
    """create username account
        parameters
        ----------
        first_name: String
            first name of user account
        last_name: String
            last name of user account"""
    first_name = first_name.split(" ")[0].replace(".", "")
    if len(last_name) > 0:
        last_name = last_name.split(" ")[0].replace(".", "")
        username = (first_name + "." + last_name).lower()
    else:
        username= (first_name + ".user").lower()
    usernames = User.objects.filter(username__contains=username).order_by('id')
    if usernames:
        for user_name in usernames:
            repeated_username = user_name.username
            first_part = repeated_username.split('.')[0]
            second_part = repeated_username.split('.')[1]
            if (username.split('.')[0] == first_part and
                    username.split('.')[1] == second_part):
                split_repeated_username = repeated_username.split('.')
                if len(split_repeated_username) == 2:
                    username = username + '.1'
                else:
                    count = int(repeated_username.split('.')[2])
                    count += 1
                    if len(split_repeated_username) == 3:
                        split_repeated_username[2] = str(count)
                        username = '.'.join(split_repeated_username)
                    else:
                        username = username + '.' + str(count)
    return username

def create_user(dict_post):
    """ Create a user """
    exists_user = User.objects.filter(email=dict_post['email']).exists()
    if not exists_user:
        dict_post['firstName'] = (dict_post['firstName']).title()
        if dict_post['lastName'] != 'null':
            dict_post['lastName'] = (dict_post['lastName']).title()
        else:
            dict_post['lastName'] = ''
        username = create_username(dict_post['firstName'],
                                   dict_post['lastName'])
        user = User.objects.create(username=username,
                                   email=dict_post['email'],
                                   password='',
                                   first_name=dict_post['firstName'],
                                   last_name=dict_post['lastName'])
        if 'password' in dict_post:
            if dict_post['password'] == '1234':
                password = 'PassWordBBVABackend'
            else:
                password = dict_post['password']
        else:
            password = User.objects.make_random_password()
        user.set_password(password)
        user.save()
        ###
        # REST addon
        ###
        userdata = UserData.objects.create(user=user,
                                           n_status=1)
        userdata.save()
        ###
        return user
    else:
        return None