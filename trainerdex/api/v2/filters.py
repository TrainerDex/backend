import django_filters as filters

from trainerdex.models import Trainer, Update


class TrainerFilter(filters.FilterSet):
    nickname = filters.CharFilter(field_name='nicknames__nickname')
    
    class Meta:
        model = Trainer
        fields = [
            'nickname',
            'faction',
            'country',
        ]


class UpdateFiler(filters.FilterSet):
    update_time = filters.IsoDateTimeFromToRangeFilter()
    
    o = filters.OrderingFilter(
        fields=[(x, x) for x, y in Update.field_metadata().items() if y.get('sortable') == True] + [
            ('update_time', 'update_time'),
        ]
    )
    
    class Meta:
        model = Update
        fields = ['trainer', 'update_time']+[x for x, y in Update.field_metadata().items() if y.get('sortable') == True]
