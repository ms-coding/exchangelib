from ..util import create_element, set_xml_value, MNS
from .common import EWSAccountService, EWSPooledMixIn, to_item_id


class CreateAttachment(EWSAccountService, EWSPooledMixIn):
    """MSDN: https://docs.microsoft.com/en-us/exchange/client-developer/web-service-reference/createattachment-operation
    """
    SERVICE_NAME = 'CreateAttachment'
    element_container_name = '{%s}Attachments' % MNS

    def call(self, parent_item, items):
        return self._pool_requests(payload_func=self.get_payload, **dict(
            items=items, parent_item=parent_item,
        ))

    def get_payload(self, items, parent_item):
        from ..properties import ParentItemId
        from ..items import BaseItem
        payload = create_element('m:%s' % self.SERVICE_NAME)
        version = self.account.version
        if isinstance(parent_item, BaseItem):
            # to_item_id() would convert this to a normal ItemId, but the service wants a ParentItemId
            parent_item = ParentItemId(parent_item.id, parent_item.changekey)
        set_xml_value(payload, to_item_id(parent_item, ParentItemId, version=version), version=version)
        attachments = create_element('m:Attachments')
        for item in items:
            set_xml_value(attachments, item, version=self.account.version)
        if not len(attachments):
            raise ValueError('"items" must not be empty')
        payload.append(attachments)
        return payload
