class AddFieldsetsMixin:
    add_fieldsets = []
    
    def get_fieldsets(self, request, obj=None):
       if not obj:
           return self.add_fieldsets
       return super().get_fieldsets(request, obj)
