"""
Model class for MyTardis API v1's StorageBoxResource.
"""
class StorageBox():
    """
    Model class for MyTardis API v1's StorageBoxResource.
    """
    def __init__(self, storagebox_dict):
        self.storage_box_id = None
        self.django_storage_class = None
        self.max_size = None
        self.status = None
        self.name = None
        self.description = None
        self.master_box = None
        self.options = []
        self.attributes = []
        if storagebox_dict is not None:
            for attr in storagebox_dict:
                if attr == "id":
                    attr = "storage_box_id"
                if hasattr(self, attr):
                    self.__dict__[attr] = storagebox_dict[attr]
            self.options = []
            for option_dict in storagebox_dict['options']:
                self.options.append(StorageBoxOption(option_dict=option_dict))
            self.attributes = []
            for attr_dict in storagebox_dict['attributes']:
                self.attributes.append(StorageBoxAttribute(attr_dict=attr_dict))


class StorageBoxOption():
    """
    Model class for MyTardis API v1's StorageBoxOptionResource.
    """
    def __init__(self, option_dict):
        self.storageboxoption_id = None
        self.key = None
        self.value = None
        if option_dict is not None:
            for attr in option_dict:
                if attr == "id":
                    attr = "storageboxoption_id"
                if hasattr(self, attr):
                    self.__dict__[attr] = option_dict[attr]


class StorageBoxAttribute():
    """
    Model class for MyTardis API v1's StorageBoxAttributeResource.
    """
    def __init__(self, attr_dict):
        self.storageboxattribute_id = None
        self.key = None
        self.value = None
        if attr_dict is not None:
            for attr in attr_dict:
                if attr == "id":
                    attr = "storageboxattribute_id"
                if hasattr(self, attr):
                    self.__dict__[attr] = attr_dict[attr]
