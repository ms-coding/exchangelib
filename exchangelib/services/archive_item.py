from .common import EWSAccountService, create_folder_ids_element, create_item_ids_element
from ..items import Item
from ..util import create_element, MNS
from ..version import EXCHANGE_2013


class ArchiveItem(EWSAccountService):
    """MSDN: https://docs.microsoft.com/en-us/exchange/client-developer/web-service-reference/archiveitem-operation"""

    SERVICE_NAME = 'ArchiveItem'
    element_container_name = f'{{{MNS}}}Items'
    supported_from = EXCHANGE_2013

    def call(self, items, to_folder):
        """Move a list of items to a specific folder in the archive mailbox.

        :param items: a list of (id, changekey) tuples or Item objects
        :param to_folder:

        :return: None
        """
        return self._elems_to_objs(self._chunked_get_elements(self.get_payload, items=items, to_folder=to_folder))

    def _elem_to_obj(self, elem):
        return Item.id_from_xml(elem)

    def get_payload(self, items, to_folder):
        payload = create_element(f'm:{self.SERVICE_NAME}')
        payload.append(
            create_folder_ids_element(tag='m:ArchiveSourceFolderId', folders=[to_folder], version=self.account.version)
        )
        payload.append(create_item_ids_element(items=items, version=self.account.version))
        return payload
