import logging

from .common import EWSService
from ..errors import ErrorNameResolutionNoResults, ErrorNameResolutionMultipleResults
from ..items import SHAPE_CHOICES, SEARCH_SCOPE_CHOICES, Contact
from ..properties import Mailbox
from ..util import create_element, set_xml_value, add_xml_child, MNS
from ..version import EXCHANGE_2010_SP2

log = logging.getLogger(__name__)


class ResolveNames(EWSService):
    """MSDN: https://docs.microsoft.com/en-us/exchange/client-developer/web-service-reference/resolvenames-operation"""

    SERVICE_NAME = 'ResolveNames'
    element_container_name = f'{{{MNS}}}ResolutionSet'
    ERRORS_TO_CATCH_IN_RESPONSE = ErrorNameResolutionNoResults
    WARNINGS_TO_IGNORE_IN_RESPONSE = ErrorNameResolutionMultipleResults
    # Note: paging information is returned as attrs on the 'ResolutionSet' element, but this service does not
    # support the 'IndexedPageItemView' element, so it's not really a paging service. According to docs, at most
    # 100 candidates are returned for a lookup.
    supports_paging = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.return_full_contact_data = False  # A hack to communicate parsing args to _elems_to_objs()

    def call(self, unresolved_entries, parent_folders=None, return_full_contact_data=False, search_scope=None,
             contact_data_shape=None):
        if self.chunk_size > 100:
            raise AttributeError(
                'Chunk size %s is too high. %s supports returning at most 100 candidates for a lookup',
                self.chunk_size, self.SERVICE_NAME
            )
        if search_scope and search_scope not in SEARCH_SCOPE_CHOICES:
            raise ValueError(f"'search_scope' {search_scope} must be one if {SEARCH_SCOPE_CHOICES}")
        if contact_data_shape and contact_data_shape not in SHAPE_CHOICES:
            raise ValueError(f"'shape' {contact_data_shape} must be one if {SHAPE_CHOICES}")
        self.return_full_contact_data = return_full_contact_data
        return self._elems_to_objs(self._chunked_get_elements(
            self.get_payload,
            items=unresolved_entries,
            parent_folders=parent_folders,
            return_full_contact_data=return_full_contact_data,
            search_scope=search_scope,
            contact_data_shape=contact_data_shape,
        ))

    def _elem_to_obj(self, elem):
        if self.return_full_contact_data:
            mailbox_elem = elem.find(Mailbox.response_tag())
            contact_elem = elem.find(Contact.response_tag())
            return (
                None if mailbox_elem is None else Mailbox.from_xml(elem=mailbox_elem, account=None),
                None if contact_elem is None else Contact.from_xml(elem=contact_elem, account=None),
            )
        return Mailbox.from_xml(elem=elem.find(Mailbox.response_tag()), account=None)

    def get_payload(self, unresolved_entries, parent_folders, return_full_contact_data, search_scope,
                    contact_data_shape):
        attrs = dict(ReturnFullContactData=return_full_contact_data)
        if search_scope:
            attrs['SearchScope'] = search_scope
        if contact_data_shape:
            if self.protocol.version.build < EXCHANGE_2010_SP2:
                raise NotImplementedError(
                    "'contact_data_shape' is only supported for Exchange 2010 SP2 servers and later")
            attrs['ContactDataShape'] = contact_data_shape
        payload = create_element(f'm:{self.SERVICE_NAME}', attrs=attrs)
        if parent_folders:
            set_xml_value(create_element('m:ParentFolderIds'), parent_folders, version=self.protocol.version)
        for entry in unresolved_entries:
            add_xml_child(payload, 'm:UnresolvedEntry', entry)
        if not len(payload):
            raise ValueError('"unresolved_entries" must not be empty')
        return payload
