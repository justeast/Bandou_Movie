from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    """ 为用户生成 JWT tokens """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
