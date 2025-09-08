from pydantic import BaseModel

class AdminPanelUser(BaseModel):
    vorname: str
    name: str
    eMailadresse: str
    uStID: str | None = None
    zrNummer: str
    firma: str
    strasse: str
    postleitzahl: str
    stadt: str
    land: str
    adresstyp: str
    entraID: str


class AdminPanelZrContact(BaseModel):
    uStID: str | None = None
    zrNummer: str
    firma: str
    strasse: str
    postleitzahl: str
    stadt: str
    land: str
    adresstyp: str