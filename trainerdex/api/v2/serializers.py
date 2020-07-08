from rest_framework import serializers

from core.models import Nickname
from trainerdex.models import Faction, Trainer, Update


class NicknameSerializerInline(serializers.ModelSerializer):
    
    class Meta:
        model = Nickname
        fields = (
            'nickname',
            'active',
        )


class FactionInline(serializers.ModelSerializer):
    
    class Meta:
        model = Faction
        fields = (
            'id',
            'name_short',
        )


class TrainerSerializer(serializers.ModelSerializer):
    nickname_set = NicknameSerializerInline(many=True, read_only=True)
    faction = FactionInline(many=False, read_only=True)
    leaderboard_eligibility = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Trainer
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'start_date',
            'faction',
            'country',
            'is_active',
            'is_verified',
            'is_banned',
            'last_modified',
            'leaderboard_eligibility',
            'nickname_set',
        )


class NicknameSerializerInline(serializers.ModelSerializer):
    
    class Meta:
        model = Nickname
        fields = (
            'user',
            'nickname',
            'active',
        )


class UpdateSerializer(serializers.ModelSerializer):
    data_source = serializers.SlugRelatedField(many=False, read_only=True, slug_field='slug')
    
    class Meta:
        model = Update
        fields = [
            'uuid',
            'update_time',
            'submission_date',
            'comment',
            'data_source',
            'data_source_notes'
        ]+[x for x in Update.field_metadata().keys()]
