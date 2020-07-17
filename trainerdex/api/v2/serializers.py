from typing import Iterable

from rest_framework import serializers

from trainerdex.models import Faction, Nickname, Trainer, TrainerCode, Update
from trainerdex.models import UpdateQuerySet


class NicknameSerializerInline(serializers.ModelSerializer):
    
    class Meta:
        model = Nickname
        fields = (
            'nickname',
            'active',
        )


class UpdateSerializerInlineFilteredListSerializer(serializers.ListSerializer):
    
    def to_representation(self, data: UpdateQuerySet):
        data = data.order_by('-update_time')[:15]
        return super().to_representation(data)


class UpdateSerializerInline(serializers.ModelSerializer):
    data_source = serializers.SlugRelatedField(many=False, read_only=True, slug_field='slug')
    
    class Meta:
        model = Update
        list_serializer_class = UpdateSerializerInlineFilteredListSerializer
        fields = [
            'uuid',
            'update_time',
            'submission_date',
            'comment',
            'data_source',
            'data_source_notes'
        ]+[x for x in Update.field_metadata().keys()]


class FactionInline(serializers.ModelSerializer):
    
    class Meta:
        model = Faction
        fields = (
            'id',
            'name_short',
        )


class TrainerSerializer(serializers.ModelSerializer):
    country = serializers.CharField()
    faction = FactionInline(many=False, read_only=True)
    leaderboard_eligibility = serializers.BooleanField(read_only=True)
    nicknames = NicknameSerializerInline(many=True, read_only=True)
    updates = UpdateSerializerInline(many=True, read_only=True)
    
    def get_fields(self, *args, **kwargs) -> Iterable[str]:
        fields = super().get_fields(*args, **kwargs)
        request = self.context.get('request')
        if request is not None and not request.parser_context.get('kwargs'):
            fields.pop('updates', None)
        return fields
    
    class Meta:
        model = Trainer
        fields = (
            'id',
            'username',
            'first_name',
            'start_date',
            'faction',
            'country',
            'is_active',
            'is_verified',
            'is_banned',
            'date_joined',
            'last_modified',
            'leaderboard_eligibility',
            'nicknames',
            'updates',
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
            'trainer',
            'update_time',
            'submission_date',
            'comment',
            'data_source',
            'data_source_notes'
        ]+[x for x in Update.field_metadata().keys()]


class TrainerSerializerInline(serializers.ModelSerializer):
    country = serializers.CharField()
    faction = FactionInline(many=False, read_only=True)
    
    class Meta:
        model = Trainer
        fields = (
            'id',
            'nickname',
            'faction',
            'country',
        )


class TrainerCodeSerializer(serializers.ModelSerializer):
    trainer = TrainerSerializerInline(many=False, read_only=True)
    
    class Meta:
        model = TrainerCode
        fields = '__all__'
