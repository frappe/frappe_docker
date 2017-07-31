from __future__ import absolute_import
# Copyright (c) 2010-2015 openpyxl

from openpyxl.descriptors.serialisable import Serialisable
from openpyxl.descriptors import (
    Alias,
    Typed,
    String,
    Float,
    Integer,
    Bool,
    NoneSet,
    Set,
)
from openpyxl.descriptors.excel import (
    ExtensionList,
    HexBinary,
    Guid,
    Relation,
    Base64Binary,
)


class WorkbookProtection(Serialisable):

    tagname = "workbookPr"

    workbookPassword = HexBinary(allow_none=True)
    workbook_password = Alias("workbookPassword")
    workbookPasswordCharacterSet = String(allow_none=True)
    revisionsPassword = HexBinary(allow_none=True)
    revision_password = Alias("revisionsPassword")
    revisionsPasswordCharacterSet = String(allow_none=True)
    lockStructure = Bool(allow_none=True)
    lock_structure = Alias("lockStructure")
    lockWindows = Bool(allow_none=True)
    lock_windows = Alias("lockWindows")
    lockRevision = Bool(allow_none=True)
    lock_revision = Alias("lockRevision")
    revisionsAlgorithmName = String(allow_none=True)
    revisionsHashValue = Base64Binary(allow_none=True)
    revisionsSaltValue = Base64Binary(allow_none=True)
    revisionsSpinCount = Integer(allow_none=True)
    workbookAlgorithmName = String(allow_none=True)
    workbookHashValue = Base64Binary(allow_none=True)
    workbookSaltValue = Base64Binary(allow_none=True)
    workbookSpinCount = Integer(allow_none=True)

    def __init__(self,
                 workbookPassword=None,
                 workbookPasswordCharacterSet=None,
                 revisionsPassword=None,
                 revisionsPasswordCharacterSet=None,
                 lockStructure=None,
                 lockWindows=None,
                 lockRevision=None,
                 revisionsAlgorithmName=None,
                 revisionsHashValue=None,
                 revisionsSaltValue=None,
                 revisionsSpinCount=None,
                 workbookAlgorithmName=None,
                 workbookHashValue=None,
                 workbookSaltValue=None,
                 workbookSpinCount=None,
                ):
        self.workbookPassword = workbookPassword
        self.workbookPasswordCharacterSet = workbookPasswordCharacterSet
        self.revisionsPassword = revisionsPassword
        self.revisionsPasswordCharacterSet = revisionsPasswordCharacterSet
        self.lockStructure = lockStructure
        self.lockWindows = lockWindows
        self.lockRevision = lockRevision
        self.revisionsAlgorithmName = revisionsAlgorithmName
        self.revisionsHashValue = revisionsHashValue
        self.revisionsSaltValue = revisionsSaltValue
        self.revisionsSpinCount = revisionsSpinCount
        self.workbookAlgorithmName = workbookAlgorithmName
        self.workbookHashValue = workbookHashValue
        self.workbookSaltValue = workbookSaltValue
        self.workbookSpinCount = workbookSpinCount


# Backwards compatibility
DocumentSecurity = WorkbookProtection


class FileSharing(Serialisable):

    tagname = "fileSharing"

    readOnlyRecommended = Bool(allow_none=True)
    userName = String(allow_none=True)
    reservationPassword = HexBinary(allow_none=True)
    algorithmName = String(allow_none=True)
    hashValue = HexBinary(allow_none=True)
    saltValue = HexBinary(allow_none=True)
    spinCount = Integer(allow_none=True)

    def __init__(self,
                 readOnlyRecommended=None,
                 userName=None,
                 reservationPassword=None,
                 algorithmName=None,
                 hashValue=None,
                 saltValue=None,
                 spinCount=None,
                ):
        self.readOnlyRecommended = readOnlyRecommended
        self.userName = userName
        self.reservationPassword = reservationPassword
        self.algorithmName = algorithmName
        self.hashValue = hashValue
        self.saltValue = saltValue
        self.spinCount = spinCount
