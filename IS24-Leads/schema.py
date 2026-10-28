"""Pydantic models for the IS24 lead API.

Two layers:

- ``RawLeadsResponse`` / ``RawLead`` etc. mirror the IS24 JSON response.
  All sub-models use ``extra="allow"`` so future IS24 additions (we already
  see undocumented fields like ``source``, ``ssoId``, ``leadType``) don't
  break parsing.

- ``LeadEnvelope`` wraps each ``RawLead`` with routing metadata the CRM will
  need: which scoutId received the lead, which advisor pool it belongs to,
  when we fetched it, and appointment timestamps converted from epoch-ms to
  proper datetimes. This is the shape the CRM ingestion will consume.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class _Permissive(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


# --- Addresses -------------------------------------------------------------

class ContactAddress(_Permissive):
    street: Optional[str] = None
    streetNumber: Optional[str] = None
    postalCode: Optional[str] = None
    location: Optional[str] = None


class RealEstateAddress(_Permissive):
    street: Optional[str] = None
    houseNumber: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None


# --- Real estate (expose) --------------------------------------------------

class RealEstate(_Permissive):
    id: Optional[int] = None
    title: Optional[str] = None
    type: Optional[str] = None
    purchasePrice: Optional[float] = None
    livingArea: Optional[float] = None
    siteArea: Optional[float] = None
    constructionDate: Optional[int] = None
    modernizationDate: Optional[int] = None
    numberOfRooms: Optional[float] = None
    picture: Optional[str] = None
    address: Optional[RealEstateAddress] = None


# --- Financing (discriminated union on .type) ------------------------------

class PurchaseFinancing(_Permissive):
    type: Literal["PurchaseFinancing"]
    purchasePrice: Optional[float] = None
    ownFunds: Optional[float] = None
    additionalCosts: Optional[float] = None
    financingStart: Optional[str] = None
    projectState: Optional[str] = None


class BuildingFinancing(_Permissive):
    type: Literal["BuildingFinancing"]
    purchasePrice: Optional[float] = None
    ownFunds: Optional[float] = None
    additionalCosts: Optional[float] = None
    financingStart: Optional[str] = None
    projectState: Optional[str] = None


class FollowupFinancing(_Permissive):
    type: Literal["FollowupFinancing"]
    propertyValue: Optional[float] = None
    remainingDebt: Optional[float] = None
    financingStart: Optional[str] = None


Financing = Annotated[
    Union[PurchaseFinancing, BuildingFinancing, FollowupFinancing],
    Field(discriminator="type"),
]


class FinancingTerms(_Permissive):
    amortizationRate: Optional[float] = None
    postalCode: Optional[str] = None
    geoCode: Optional[str] = None
    locationName: Optional[str] = None
    employment: Optional[str] = None
    employmentSector: Optional[str] = None
    fixedNominalInterestRate: Optional[str] = None
    financing: Optional[Financing] = None


# --- Income, spending, second borrower, financing object -------------------

class Income(_Permissive):
    salary: Optional[float] = None
    numberOfSalaries: Optional[int] = None
    alimony: Optional[float] = None
    pension: Optional[float] = None
    rental: Optional[float] = None
    childBenefits: Optional[float] = None
    other: Optional[float] = None


class Spending(_Permissive):
    livingCost: Optional[float] = None
    rent: Optional[float] = None
    buildingSaving: Optional[float] = None
    saving: Optional[float] = None
    alimony: Optional[float] = None
    healthInsurance: Optional[float] = None
    pensionInsurance: Optional[float] = None
    creditRate: Optional[float] = None
    numberOfVehicles: Optional[int] = None
    other: Optional[float] = None


class SecondBorrower(_Permissive):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    dateOfBirth: Optional[str] = None
    nationality: Optional[str] = None
    employment: Optional[str] = None
    workContractType: Optional[str] = None
    workContractEndDate: Optional[str] = None
    maritalStatus: Optional[str] = None
    income: Optional[Income] = None
    spending: Optional[Spending] = None


class FinancingObject(_Permissive):
    street: Optional[str] = None
    streetNumber: Optional[str] = None
    postalCode: Optional[str] = None
    city: Optional[str] = None
    livingArea: Optional[float] = None
    siteArea: Optional[float] = None
    constructionYear: Optional[int] = None
    type: Optional[str] = None
    subType: Optional[str] = None
    rooms: Optional[float] = None
    hasLift: Optional[bool] = None
    hasParking: Optional[bool] = None
    hasStorage: Optional[bool] = None
    hasOutdoorArea: Optional[bool] = None
    lastModified: Optional[str] = None


# --- Contact request -------------------------------------------------------

class ContactRequest(_Permissive):
    useType: Optional[str] = None
    financingTerms: Optional[FinancingTerms] = None
    contactChannel: Optional[str] = None
    bank: Optional[str] = None
    dateOfBirth: Optional[str] = None
    numberOfBorrowers: Optional[int] = None
    currentCredits: Optional[float] = None
    message: Optional[str] = None
    partnerTracking: Optional[str] = None
    salutation: Optional[str] = None
    title: Optional[str] = None
    surname: Optional[str] = None
    forename: Optional[str] = None
    email: Optional[str] = None
    phoneNumber: Optional[str] = None
    netIncome: Optional[float] = None
    netIncomeRange: Optional[str] = None
    contactAddress: Optional[ContactAddress] = None
    exposeId: Optional[int] = None
    objectId: Optional[str] = None
    dpaAccepted: Optional[bool] = None
    kfwPromotion: Optional[bool] = None
    arvatoScoringPermitted: Optional[bool] = None
    energeticModernization: Optional[str] = None
    segmentClass: Optional[str] = None
    availability: Optional[str] = None
    primaryAppointmentDate: Optional[int] = None
    secondaryAppointmentDate: Optional[int] = None
    primaryAppointmentTime: Optional[str] = None
    secondaryAppointmentTime: Optional[str] = None
    borrowerRelationship: Optional[str] = None
    nationality: Optional[str] = None
    workContractType: Optional[str] = None
    workContractEndDate: Optional[str] = None
    numberOfChildren: Optional[int] = None
    maritalStatus: Optional[str] = None
    secondBorrower: Optional[SecondBorrower] = None
    income: Optional[Income] = None
    spending: Optional[Spending] = None
    financingObject: Optional[FinancingObject] = None


# --- Lead + response wrapper ----------------------------------------------

class RawLead(_Permissive):
    id: int
    providerId: int
    providerName: str
    shortName: Optional[str] = None
    requestDate: Optional[datetime] = None
    requestDateUTC: Optional[datetime] = None
    requestType: str
    shopLead: bool
    singleLead: Optional[bool] = None
    offerTracking: Optional[bool] = None
    note: Optional[str] = None
    effectiveInterestRate: Optional[float] = None
    nominalInterestRate: Optional[float] = None
    price: float = 0
    shopBudgetReduction: Optional[float] = None
    processingStatus: str
    processingStatusChanged: datetime
    contactRequest: Optional[ContactRequest] = None
    realEstate: Optional[RealEstate] = None
    scoutId: Optional[str] = None


class RawLeadsResponse(_Permissive):
    lead: list[RawLead] = Field(default_factory=list)


# --- Envelope: CRM-facing shape -------------------------------------------

class LeadEnvelope(BaseModel):
    """A single IS24 lead with routing metadata the CRM uses to assign it.

    Fields:
      - is24_lead_id: stable upsert key (== lead.id)
      - scout_id: which scoutId the lead came in on (advisor or org)
      - pool: which configured pool this scoutId belongs to ("organization"
              or "advisor:<name>"); set by the sync layer.
      - fetched_at: when we pulled it from IS24
      - primary_appointment / secondary_appointment: appointment-request
        timestamps converted from epoch-ms to ISO datetimes
      - lead: full RawLead payload preserved as-is
    """
    model_config = ConfigDict(extra="forbid")

    is24_lead_id: int
    scout_id: Optional[str]
    pool: str
    fetched_at: datetime
    primary_appointment: Optional[datetime] = None
    secondary_appointment: Optional[datetime] = None
    lead: RawLead


def _ms_to_dt(ms: Optional[int]) -> Optional[datetime]:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def envelope(lead: RawLead, *, pool: str, fetched_at: datetime) -> LeadEnvelope:
    cr = lead.contactRequest
    return LeadEnvelope(
        is24_lead_id=lead.id,
        scout_id=lead.scoutId,
        pool=pool,
        fetched_at=fetched_at,
        primary_appointment=_ms_to_dt(cr.primaryAppointmentDate) if cr else None,
        secondary_appointment=_ms_to_dt(cr.secondaryAppointmentDate) if cr else None,
        lead=lead,
    )
