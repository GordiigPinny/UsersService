from rest_framework.views import APIView, Response, Request
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import LimitOffsetPagination
from ApiRequesters.Auth.permissions import IsAuthenticated
from ApiRequesters.Auth.AuthRequester import AuthRequester
from ApiRequesters.utils import get_token_from_request
from ApiRequesters.exceptions import BaseApiRequestError, UnexpectedResponse
from ApiRequesters.Awards.AwardsRequester import AwardsRequester
from Users.models import Profile
from Users.serializers import ProfileSerializer, ProfilesListSerializer
from Users.permissions import EditableByMeAndAdminPermission


class ProfilesListView(ListCreateAPIView):
    """
    Вьюха для спискового представления профилей
    """
    pagination_class = LimitOffsetPagination
    serializer_class = ProfilesListSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        return Profile.objects.all()

    def create(self, request, *args, **kwargs):
        r = AuthRequester()
        token = get_token_from_request(request)
        try:
            auth_info = r.get_user_info(token)
        except UnexpectedResponse as e:
            return Response(data=e.response, status=e.code)
        except BaseApiRequestError as e:
            return Response(data=str(e), status=500)
        request._full_data['user_id'] = auth_info['id']
        return super().create(request, args, kwargs)


class ProfileDetailView(RetrieveUpdateDestroyAPIView):
    """
    Вьюха для детального представления профиля
    """
    serializer_class = ProfileSerializer
    permission_classes = (EditableByMeAndAdminPermission, )
    lookup_field = 'user_id'
    lookup_url_kwarg = 'user_id'

    def get_queryset(self):
        return Profile.objects.all()

    def update(self, request, *args, **kwargs):
        response = super().update(request, args, kwargs)
        if response.status_code == 200:
            response.status_code = 202
        return response


class AddNewAwardView(APIView):
    """
    Вьюха для добавления нового пина
    """
    permission_classes = (EditableByMeAndAdminPermission, )
    lookup_url_kwarg = 'user_id'

    def _check_awards_ids(self, award_type, awards_ids, token) -> bool:
        r = AwardsRequester()
        try:
            for award_id in awards_ids:
                if award_type == 'achievement':
                    r.get_achievement(award_id, token)
                else:
                    r.get_pin(award_id, token)
        except BaseApiRequestError:
            return False
        return True

    def post(self, request: Request, user_id: int):
        try:
            profile = Profile.objects.get(user_id=user_id)
        except Profile.DoesNotExist:
            return Response(status=404)
        try:
            award_type, award_ids = request.data['award_type'], request.data['award_ids']
        except KeyError:
            return Response({'error': 'Необходимые поля: "award_type", "award_ids"'}, status=400)

        if not isinstance(award_ids, list):
            return Response({'error': '"award_ids" должен быть массивом'}, status=400)

        if len([x for x in award_ids if not isinstance(x, int)]) > 0:
            return Response({'error': '"award_ids" должен быть целочисленным массивом'}, status=400)

        if award_type not in ['upin', 'ppin', 'achievement']:
            return Response({'error': 'Допустимые типы наград: "upin", "ppin", "achievement"'}, status=400)

        if not self._check_awards_ids(award_type, award_ids, get_token_from_request(request)):
            return Response({'error': 'Некоторые id наград не существуют'}, status=404)

        if award_type == 'upin':
            profile.unlocked_geopins += ',' + ','.join([str(x) for x in award_ids])
        elif award_type == 'ppin':
            profile.unlocked_pins += ',' + ','.join([str(x) for x in award_ids])
        else:
            profile.achievements += ',' + ','.join([str(x) for x in award_ids])
        profile.save()
        s = ProfileSerializer(profile)
        return Response(s.data, status=201)
