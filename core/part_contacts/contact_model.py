from typing import List, Optional
from pydantic import BaseModel, Field

class Contact(BaseModel):
    id: str = Field(description="Eindeutige ID des Kontakts")
    name: str = Field(description="Name des Kontakts")
    email: Optional[str] = Field(description="E-Mail-Adresse", default=None)
    phone: Optional[str] = Field(description="Telefonnummer", default=None)
    address: Optional[str] = Field(description="Adresse", default=None)

class ContactGroup(BaseModel):
    group_id: str = Field(description="Eindeutige ID der Kontaktgruppe")
    group_name: str = Field(description="Name der Kontaktgruppe")
    contacts: List[Contact] = Field(default=[])  # Liste von Kontakten in der Gruppe

class AccountContactData(BaseModel):
    account_email: str = Field(description="E-Mail-Adresse des Accounts")
    contact_groups: List[ContactGroup] = Field(default=[])  # Gruppen mit Kontakten

