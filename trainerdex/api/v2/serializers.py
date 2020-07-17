from typing import Iterable

from rest_framework import serializers

from trainerdex.models import Faction, Nickname, Trainer, TrainerCode, Update
from trainerdex.models import UpdateQuerySet


class NicknameSerializer(serializers.ModelSerializer):
    
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
    nicknames = NicknameSerializer(many=True, read_only=True)
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


class LeaderboardSerializer(serializers.ModelSerializer):
    trainer = TrainerSerializerInline(many=False, read_only=True)
    value = serializers.SerializerMethodField()
    datetime = serializers.DateTimeField()
    rank = serializers.IntegerField(max_value=0)
    extra_fields = serializers.SerializerMethodField()
    
    def get_value(self, obj):
        return obj.value
    
    def get_extra_fields(self, obj):
        extra = UpdateSerializerInline(obj, many=False, read_only=True).data
        return {k: v for k, v in extra.items() if v is not None}
    
    class Meta:
        model = Update
        fields = ('trainer', 'value', 'datetime', 'rank', 'extra_fields')


class LeaderboardSerializerLegacy(LeaderboardSerializer):
    trainer = serializers.SerializerMethodField()
    
    def get_trainer(self, obj):
        return TrainerSerializerInline(obj, many=False, read_only=True).data
    
    def get_extra_fields(self, obj):
        extra =  {x.replace('extra_max__', ''): getattr(obj, x) for x in dir(obj) if x.startswith('extra_max__')}
        return {k: v for k, v in extra.items() if v is not None}
        
    class Meta:
        model = Trainer
        fields = ('trainer', 'value', 'datetime', 'rank', 'extra_fields')
