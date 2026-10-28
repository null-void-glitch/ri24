# Lead

**Returns a list of resources identified by the following URL. Returns all financing-/appointment-requests of a given timeframe and a mortgage provider identified by their customer number (ScoutID, The requester must be authorized to receive requests of that ScoutID). If no ScoutID was passed, requests of all ScoutIDs the requester is authorized for are returned. For test purposes the parameter test=true can be passed to receive test leads (any other parameter will be ignored).**

The customer number (scoutId value) can be found either on invoices or when navigating to [Vertragsdaten](https://www.immobilienscout24.de/meinkonto/einstellungen/vertragsdaten) when logged in as the main user of the user account connected to the mortgage advisor account.

> GET /financing/construction/v2/lead

Supported media types:

XML

JSON

### Request

> GET https://rest.immobilienscout24.de/restapi/api/financing/construction/v2/lead?scoutid=123123&from=2021-12-01T00:00:00&to=2022-12-01T00:00:00
> 
> GET https://rest.sandbox-immobilienscout24.de/restapi/api/financing/construction/v2/lead?scoutid=123123&from=2021-12-01T00:00:00&to=2022-12-01T00:00:00

#### Query Parameters

| parameter | value | example |
| --- | --- | --- |
| scoutid | The mortgage providers customer number (Kundennummer) | 12345 |
| from date | string, [time format](https://www.joda.org/joda-time/key_format.html): yyyy-MM-dd'T'HH:mm:ss | 2021-12-01T00:00:00 |
| to date | string, format: yyyy-MM-dd'T'HH:mm:ss | 2021-12-02T00:00:00 |
| test | if set to true, some test leads are returned |     |

### Response

**1 Basic Lead Data:**

| parameter | value | description |
| --- | --- | --- |
| lead.id |     | id of the lead |
| lead.providerId |     | id of the bank or financial advisor that was contacted |
| lead.providerName |     | name of the bank or financial advisor that was contacted |
| lead.shortName |     | short name or the name of the contacted branch |
| lead.offerTracking |     | shows if bank offers tracking |
| lead.processingStatus | NEW, CLIENT\_NOT\_REACHABLE, DECLINED\_BY\_CLIENT, APPOINTMENT\_ARRANGED, APPOINTMENT\_MISSED, OFFER\_SENT, CONSULTING\_NO\_DEAL, CONSULTING\_DEAL\_OTHER, CONSULTING\_DEAL\_MORTGAGE, IN\_PROGRESS, NO\_INTEREST, DECLINED\_BY\_BANK, CLAIMED, FOLLOW\_UP | status set by bank |
| lead.processingStatusChanged |     | date and time when status was changed |
| lead.note |     | notes entered in the BaufiManager, may not be present |
| lead.price |     | lead price |
| lead.shopBudgetReduction |     | price reducted from the budget |
| lead.effectiveInterestRate |     | may not be present |
| lead.nominalInterestRate |     | may not be present |
| lead.requestDate |     | Deprecated. Creation date and time of the lead in format "yyyy-MM-dd'T'HH:mm:ss" in Europe/Berlin timezone. This field is deprecated and might be removed in the future. Use lead.requestDateUTC instead. |
| lead.requestDateUTC |     | creation date and time of the lead in format "yyyy-MM-dd'T'HH:mm:ss" in UTC. |
| lead.requestType | APPOINTMENT\_REQUEST, FINANCING\_REQUEST, LOCAL\_LENDER. [for further information on RequestType](#RequestTypes) |     |
| lead.shopLead |     | shows if the lead type is shop |
| lead.singleLead | true / false | shows if the lead was exclusive lead or multi lead. True = exclusive / single lead. |
| lead.contactRequest.useType | OWNER\_OCCUPATION, PARTIALLY\_RENTING, RENTING, UNKNOWN | use type of the financing object |
| lead.contactRequest.financingTerms.financing.type | BuildingFinancing, PurchaseFinancing, FollowupFinancing. [for further information on FinancingType](#FinTypes). |     |
| lead.contactRequest.bank |     | the main bank of the requester |
| lead.contactRequest.dateOfBirth |     | the date of birth of the requester |
| lead.contactRequest.numberOfBorrowers |     | number of borrowers |
| lead.contactRequest.currentCredits |     | sum of running credits of the requester |
| lead.contactRequest.message |     | message of the requester |
| lead.contactRequest.partnerTracking |     | If the contact request comes from a partner, this field should contain the id of the contact request on the partner's side |
| lead.contactRequest.contactChannel | TELEPHONE, MEETING\_AT\_PROVIDERS\_PLACE, MEETING\_AT\_REQUESTERS\_PLACE, EMAIL, UNKNOWN | preferred way of contact |
| lead.contactRequest.financingTerms.fixedNominalInterestRate | FIVE\_YEARS, TEN\_YEARS, FIFTEEN\_YEARS, TWENTY\_YEARS, THIRTY\_YEARS, FORTY\_YEARS |     |
| lead.contactRequest.financingTerms.amortizationRate |     | Tilgung p.a. in % |
| lead.contactRequest.financingTerms.geoCode |     | geocode of the search region(e.g. 1276003001046= Berlin-Mitte) |
| lead.contactRequest.financingTerms.postalCode |     | postal code of the search region |
| lead.contactRequest.financingTerms.locationName |     | name of the search region |
| lead.contactRequest.financingTerms.employment | CIVIL\_SERVANT, EMPLOYED, FREELANCER, PENSIONER, SELFEMPLOYED, UNEMPLOYED, WORKER, HOUSEWIFE |     |
| lead.contactRequest.financingTerms.employmentSector | MEDICAL |     |
| lead.contactRequest.salutation | MR, MRS, UNKNOWN |     |
| lead.contactRequest.surname |     | family name |
| lead.contactRequest.forename |     | first name of the requester) |
| lead.contactRequest.email |     | email address of the requester |
| lead.contactRequest.phoneNumber |     | Phone number of the requester |
| lead.contactRequest.netIncome |     | net income of the requester |
| lead.contactRequest.netIncomeRange | BELOW\_500, OVER\_500\_UPTO\_1000, OVER\_1000\_UPTO\_1500, OVER\_1500\_UPTO\_2000, OVER\_2000\_UPTO\_3000, OVER\_2000\_UPTO\_2500, OVER\_2500\_UPTO\_3000, OVER\_3000\_UPTO\_4000, OVER\_3000\_UPTO\_3500, OVER\_3500\_UPTO\_4000, OVER\_4000\_UPTO\_5000, OVER\_5000 |     |
| lead.contactRequest.contactAddress.street |     | street of the requester |
| lead.contactRequest.contactAddress.streetNumber |     | street no. of the requester |
| lead.contactRequest.contactAddress.postalCode |     | postal code of the requester |
| lead.contactRequest.contactAddress.location |     | location of the requester |
| lead.contactRequest.exposeId |     | if contact request is related to an expose |
| lead.contactRequest.objectId |     | if contact request is related to an expose; it is the field realEstate.externalId returned by the ExposeAPI |
| lead.contactRequest.dpaAccepted |     | accepted the Data Processing Agreement |
| lead.contactRequest.kfwPromotion |     | requester is interested in KfW consulting |
| lead.contactRequest.arvatoScoringPermitted |     | agree with sending data to Arvato to generate score |
| lead.contactRequest.title | NO\_TITLE, DOCTOR, PROFESSOR, PROFESSOR\_DOCTOR | requester title |
| lead.contactRequest.energeticModernization | AFTER\_PURCHASE, LATER, NOT\_NEEDED, UNCLEAR | type of energetic modernization for the requester |
| lead.contactRequest.segmentClass | For example: A, B, C, D, E, BASIC, BAUSPAR, PREMIUM\_XS, PREMIUM\_S, PREMIUM\_M, PREMIUM\_L, PREMIUM\_XL, P\_APPROVED | class that evaluates the quality of the request. We might add additional values any time, please be flexible on read! |
| lead.contactRequest.experiments |     | experiments in contact request |
| lead.realEstate |     | If a lead is connected to an Expose you will find information about the expose in this area. The information given depends on the expose. There is no minimum set of required fields. |
| lead.realEstate.id |     | Id of the real estate |
| lead.realEstate.title |     | Title of the real estate |
| lead.realEstate.type | APARTMENT\_RENT, APARTMENT\_BUY, HOUSE\_BUY, HOUSE\_RENT, GARAGE\_RENT, GARAGE\_BUY, LIVING\_RENT\_SITE, LIVING\_BUY\_SITE, TRADE\_SITE, HOUSE\_TYPE, FLAT\_SHARE\_ROOM, SENIOR\_CARE, ASSISTED\_LIVING, OFFICE, INDUSTRY, STORE, GASTRONOMY, SPECIAL\_PURPOSE, INVESTMENT, COMPULSORY\_AUCTION, SHORT\_TERM\_ACCOMMODATION | Please note that the field names in the RealEstateAddress differ from the ones in the ContactAddress |
| lead.realEstate.purchasePrice |     | Purchase price of the real estate |
| lead.realEstate.livingArea |     | Living area of the real estate |
| lead.realEstate.siteArea |     | Site area of the real estate |
| lead.realEstate.constructionDate |     | Construction date of the real estate |
| lead.realEstate.modernizationDate |     | Modernization date of the real estate |
| lead.realEstate.address.street |     | Street of the real estate |
| lead.realEstate.address.houseNumber |     | Number of the real estate |
| lead.realEstate.address.postcode |     | Postcode of the real estate |
| lead.realEstate.address.city |     | City of the real estate |
| lead.realEstate.numberOfRooms |     | Number of rooms of the real estate |
| lead.realEstate.picture |     | Picture of the real estate |

  

- - -

**2 EXTENDED LEAD DATA**

User can provide additional (‘’extended”) data.

| parameter | value | description |
| --- | --- | --- |
| lead.contactRequest.borrowerRelationship | MARRIED=verheiratet, LIVING\_TOGETHER=zusammenlebend, OTHER=andere Beziehung | Verhältnis der Darlehensnehmer |
| lead.contactRequest.nationality |     | Staatsangehörigkeit |
| lead.contactRequest.workContractType | LIMITED=befristet, PERMANENT=unbefristet, PROBATION=Probezeit | Vertragsverhältnis |
| lead.contactRequest.workContractEndDate |     | Befristet bis |
| lead.contactRequest.numberOfChildren |     | Anzahl der Kinder |
| lead.contactRequest.maritalStatus | SINGLE=Single, MARRIED=verheiratet, SEPARATED=getrennt lebend, DIVORCED=geschieden, WIDOWED=verwitwet, PARTNERSHIP=Lebenspartnerschaft | Familienstand |
| lead.contactRequest.secondBorrower.firstName |     | Vorname |
| lead.contactRequest.secondBorrower.lastName |     | Nachname |
| lead.contactRequest.secondBorrower.dateOfBirth |     | Geburtsdatum |
| lead.contactRequest.secondBorrower.nationality |     | Staatsangehörigkeit |
| lead.contactRequest.secondBorrower.employment | CIVIL\_SERVANT, EMPLOYED, FREELANCER, PENSIONER, SELFEMPLOYED, UNEMPLOYED, WORKER, HOUSEWIFE | Beschäftigungsverhältnis |
| lead.contactRequest.secondBorrower.workContractType | LIMITED, PERMANENT, PROBATION | Vertragsverhältnis |
| lead.contactRequest.secondBorrower.workContractEndDate |     | Befristet bis |
| lead.contactRequest.secondBorrower.maritalStatus | SINGLE=Single, MARRIED=verheiratet, SEPARATED=getrennt lebend, DIVORCED=geschieden, WIDOWED=verwitwet, PARTNERSHIP=Lebenspartnerschaft | Familienstand |

**Income (1st borrower)**

| parameter | value | description |
| --- | --- | --- |
| lead.contactRequest.income.salary |     | Monatliches Nettoeinkommen |
| lead.contactRequest.income.numberOfSalaries |     | Anzahl der Monatsgehälter |
| lead.contactRequest.income.alimony |     | Unterhalt |
| lead.contactRequest.income.pension |     | Pensionen, Renten o. Ä. |
| lead.contactRequest.income.rental |     | Einkünfte aus Vermietung und Verpac.. |
| lead.contactRequest.income.childBenefits |     | Kindergeld |
| lead.contactRequest.income.other |     | Sonstige regelmäßige Einnahmen |

**Spending (1st borrower)**

| parameter | value | description |
| --- | --- | --- |
| lead.contactRequest.spending.livingCost |     | Lebenshaltungskostenpauschale |
| lead.contactRequest.spending.rent |     | Monatliche Warmmiete |
| lead.contactRequest.spending.buildingSaving |     | Bausparbeitrag |
| lead.contactRequest.spending.saving |     | Sparbeiträge |
| lead.contactRequest.spending.alimony |     | Unterhalt |
| lead.contactRequest.spending.healthInsurance |     | Private Krankenversicherung |
| lead.contactRequest.spending.pensionInsurance |     | Private Lebens-/ Rentenversicherung |
| lead.contactRequest.spending.creditRate |     | Kreditaten |
| lead.contactRequest.spending.numberOfVehicles |     | Anzahl Kfz |
| lead.contactRequest.spending.other |     | Sonstige regelmäßige Ausgaben |

**Income (2nd borrower)**

| parameter | value | description |
| --- | --- | --- |
| lead.contactRequest.secondBorrower.income.salary |     | Monatliches Nettoeinkommen |
| lead.contactRequest.secondBorrower.income.numberOfSalaries |     | Anzahl der Monatsgehälter |
| lead.contactRequest.secondBorrower.income.alimony |     | Unterhalt |
| lead.contactRequest.secondBorrower.income.pension |     | Pensionen, Renten o. Ä. |
| lead.contactRequest.secondBorrower.income.rental |     | Einkünfte aus Vermietung und Verpac.. |
| lead.contactRequest.secondBorrower.income.childBenefits |     | Kindergeld |
| lead.contactRequest.secondBorrower.income.other |     | Sonstige regelmäßige Einnahmen |

**Spending (2nd borrower)**

| parameter | value | description |
| --- | --- | --- |
| lead.contactRequest.secondBorrower.spending.livingCost |     | Lebenshaltungskostenpauschale |
| lead.contactRequest.secondBorrower.spending.rent |     | Monatliche Warmmiete |
| lead.contactRequest.secondBorrower.spending.buildingSaving |     | Bausparbeitrag |
| lead.contactRequest.secondBorrower.spending.saving |     | Sparbeiträge |
| lead.contactRequest.secondBorrower.spending.alimony |     | Unterhalt |
| lead.contactRequest.secondBorrower.spending.healthInsurance |     | Private Krankenversicherung |
| lead.contactRequest.secondBorrower.spending.pensionInsurance |     | Private Lebens-/ Rentenversicherung |
| lead.contactRequest.secondBorrower.spending.creditRate |     | Kreditaten |
| lead.contactRequest.secondBorrower.spending.numberOfVehicles |     | Anzahl Kfz |
| lead.contactRequest.secondBorrower.spending.other |     | Sonstige regelmäßige Ausgaben |

**Purchase object data**

| parameter | value | description |
| --- | --- | --- |
| lead.contactRequest.financingObject.street |     | Straße |
| lead.contactRequest.financingObject.streetNumber |     | Nr. |
| lead.contactRequest.financingObject.postalCode |     | PLZ |
| lead.contactRequest.financingObject.city |     | Ort |
| lead.contactRequest.financingObject.livingArea |     | Wohnfläche |
| lead.contactRequest.financingObject.siteArea |     | Grundstücksfläche |
| lead.contactRequest.financingObject.constructionYear |     | Baujahr der Immobilie |
| lead.contactRequest.financingObject.type | APARTMENT\_BUY=Wohnung, HOUSE\_BUY=Haus, LIVING\_BUY\_SITE=Grundstück | Haustyp |
| lead.contactRequest.financingObject.subType | SINGLE\_FAMILY\_HOUSE=Einfamiliehaus, SEMIDETACHED\_HOUSE=Doppelhaushälfte, TERRACE\_HOUSE=Reihenhaus, MULTI\_FAMILY\_HOUSE=Mehrfamilienhaus, HALF\_BASEMENT=Souterrain, GROUND\_FLOOR=Erdgeschoss, APARTMENT=Etagenwohnung, ROOF\_STOREY=Dachgeschoss, MAISONETTE=Maisonette, LOFT=Loft | Wohnungstyp |
| lead.contactRequest.financingObject.rooms |     | Anzahl der Räume |
| lead.contactRequest.financingObject.hasLift |     | Ob das Finanzierungsobjekt einen Aufzug hat |
| lead.contactRequest.financingObject.hasParking |     | Ob das Finanzierungsobjekt Parkplätze hat |
| lead.contactRequest.financingObject.hasStorage |     | Ob das Finanzierungsobjekt gespeichert ist |
| lead.contactRequest.financingObject.hasOutdoorArea |     | Ob das Finanzierungsobjekt einen Außenbereich hat |
| lead.contactRequest.financingObject.lastModified |     | Das letzte Mal wurde das Finanzierungsobjekt geändert |

- - -

#### Financing types

**lead.contactRequest.financingTerms.financing.type=BuildingFinancing (Neubau):**

| parameter | value |
| --- | --- |
| lead.contactRequest.financingTerms.financing.purchasePrice |     |
| lead.contactRequest.financingTerms.financing.ownFunds |     |
| lead.contactRequest.financingTerms.financing.additionalCosts |     |
| lead.contactRequest.financingTerms.financing.financingStart | NA, IN\_LESS\_THAN\_THREE\_MONTH, IN\_BETWEEN\_THREE\_AND\_SIX\_MONTHS, IN\_MORE\_THAN\_SIX\_MONTH |
| lead.contactRequest.financingTerms.financing.projectState | NA, NOT\_YET\_IN\_PLANNING, LAND\_PROPERTY\_EXISTS, LAND\_PROPERTY\_AND\_COMPANY\_EXIST, PROPERTY\_FOUND, NOTARY\_APPOINTMENT\_PLANNED, ON\_BUILDER\_SEARCH |

**lead.contactRequest.financingTerms.financing.type=PurchaseFinancing (Kauf einer Immobilie):**

| parameter | value |
| --- | --- |
| lead.contactRequest.financingTerms.financing.purchasePrice |     |
| lead.contactRequest.financingTerms.financing.ownFunds |     |
| lead.contactRequest.financingTerms.financing.additionalCosts |     |
| lead.contactRequest.financingTerms.financing.financingStart | NA, IN\_LESS\_THAN\_THREE\_MONTH, IN\_BETWEEN\_THREE\_AND\_SIX\_MONTHS, IN\_MORE\_THAN\_SIX\_MONTH |
| lead.contactRequest.financingTerms.financing.projectState | NA, REAL\_ESTATE\_VISITED, REAL\_ESTATE\_NOT\_YET\_VISITED, PURCHASING\_NEGOTIATIONS, CONCRETE\_OBJECT\_FOUND, NOTARY\_APPOINTMENT\_PLANNED, ON\_OBJECT\_SEARCH |

**lead.contactRequest.financingTerms.financing.type=FollowupFinancing (Anschlussfinanzierung):**

| parameter | value |
| --- | --- |
| lead.financingTerms.financing.propertyValue |     |
| lead.financingTerms.financing.remainingDebt |     |
| lead.financingTerms.financing.financingStart | NA, IN\_LESS\_THAN\_ONE\_YEAR, IN\_ONE\_YEAR, IN\_TWO\_YEARS, IN\_THREE\_YEARS, IN\_FOUR\_YEARS, IN\_FIVE\_YEARS |

- - -

#### Request types

**lead.requestType=APPOINTMENT\_REQUEST:** Leads with lead.requestType=APPOINTMENT\_REQUEST include up to 2 appointments (primary and secondary). An appointment consists of the date field which is a Unix Timestamp and a time field which is an enum described below.

| parameter | value |
| --- | --- |
| lead.contactRequest.primaryAppointmentDate | primary date in miliseconds of prefered appointment |
| lead.contactRequest.secondaryAppointmentDate | secondary date in milliseconds of preferred appointment |
| lead.contactRequest.primaryAppointmentTime / lead.contactRequest.secondaryAppointmentTime | ALL\_DAY, EIGHT\_TO\_TWELVE, TWELVE\_TO\_SIXTEEN, SIXTEEN\_TO\_NINETEEN, UNKNOWN, TEN\_UNTIL\_ELEVEN, ELEVEN\_UNTIL\_TWELVE, TWELVE\_UNTIL\_THIRTEEN, THIRTEEN\_UNTIL\_FOURTEEN, FOURTEEN\_UNTIL\_FIFTEEN, FIFTEEN\_UNTIL\_SIXTEEN, SIXTEEN\_UNTIL\_SEVENTEEN, SEVENTEEN\_UNTIL\_EIGHTEEN, EIGHTEEN\_UNTIL\_NINETEEN, NINETEEN\_UNTIL\_TWENTY, TWENTY\_UNTIL\_TWENTYONE |

**lead.requestType=FINANCING\_REQUEST:**

| parameter | value |
| --- | --- |
| lead.contactRequest.availability | ALL\_DAY, EIGHT\_TO\_TWELVE, TWELVE\_TO\_SIXTEEN, SIXTEEN\_TO\_NINETEEN, UNKNOWN, TEN\_UNTIL\_ELEVEN, ELEVEN\_UNTIL\_TWELVE, TWELVE\_UNTIL\_THIRTEEN, THIRTEEN\_UNTIL\_FOURTEEN, FOURTEEN\_UNTIL\_FIFTEEN, FIFTEEN\_UNTIL\_SIXTEEN, SIXTEEN\_UNTIL\_SEVENTEEN, SEVENTEEN\_UNTIL\_EIGHTEEN, EIGHTEEN\_UNTIL\_NINETEEN, NINETEEN\_UNTIL\_TWENTY, TWENTY\_UNTIL\_TWENTYONE |

#### Overview of mandatory fields

The table below shows which fields are mandatory / optional / not present in ApointmentRequests FinancingRequests.

| Field | APPOINTMENT\_REQUEST | FINANCING\_REQUESTS |
| --- | --- | --- |
| lead.id | mandatory | mandatory |
| lead.providerId | mandatory | mandatory |
| lead.providerName | mandatory | mandatory |
| lead.shortName | optional | optional |
| lead.note | optional | optional |
| lead.effectiveInterestRate | optional | optional |
| lead.nominalInterestRate | optional | optional |
| lead.requestDate | mandatory | mandatory |
| lead.requestType | mandatory | mandatory |
| lead.shopLead | mandatory | mandatory |
| lead.contactRequest.useType | defaults to "UNKNOWN" | mandatory |
| lead.contactRequest.financingTerms | mandatory | mandatory |
| lead.contactRequest.contactChannel | mandatory | mandatory |
| lead.contactRequest.salutation | mandatory | mandatory |
| lead.contactRequest.surname | mandatory | mandatory |
| lead.contactRequest.forename | mandatory | mandatory |
| lead.contactRequest.email | mandatory | mandatory |
| lead.contactRequest.phoneNumber | mandatory | mandatory |
| lead.contactRequest.message | optional | optional |
| lead.contactRequest.exposeId | optional | optional |
| lead.contactRequest.partnerTracking | optional | optional |
| lead.contactRequest.objectId | optional | optional |
| lead.contactRequest.netIncome | optional | mandatory |
| lead.contactRequest.netIncomeRange | optional | optional |
| lead.contactRequest.currentCredits | optional | optional |
| lead.contactRequest.numberOfBorrowers | optional | optional |
| lead.contactRequest.dateOfBirth | optional | optional |
| lead.contactRequest.bank | optional | optional |
| lead.contactRequest.contactAddress | optional | mandatory |
| lead.contactRequest.energeticModernization | optional | optional |
| lead.contactRequest.availability | not present | optional |
| lead.contactRequest.primaryAppointmentDate | optional | not present |
| lead.contactRequest.secondaryAppointmentDate | optional | not present |
| lead.contactRequest.primaryAppointmentTime | optional | not present |
| lead.contactRequest.secondaryAppointmentTime | optional | not present |
| lead.contactRequest.dpaAccepted | defaults to false | defaults to false |
| lead.contactRequest.kfwPromotion | defaults to false | defaults to false |
| lead.contactRequest.arvatoScoringPermitted | defaults to false | defaults to false |
| lead.contactRequest.borrowerRelationship | not present | optional |
| lead.contactRequest.nationality | not present | optional |
| lead.contactRequest.workContractType | not present | optional |
| lead.contactRequest.workContractEndDate | not present | optional |
| lead.contactRequest.numberOfChildren | not present | optional |
| lead.contactRequest.maritalStatus | not present | optional |
| lead.contactRequest.secondBorrower | not present | optional |
| lead.contactRequest.secondBorrower.firstName | not present | optional |
| lead.contactRequest.secondBorrower.lastName | not present | optional |
| lead.contactRequest.secondBorrower.dateOfBirth | not present | optional |
| lead.contactRequest.secondBorrower.nationality | not present | optional |
| lead.contactRequest.secondBorrower.employment | not present | optional |
| lead.contactRequest.secondBorrower.workContractType | not present | optional |
| lead.contactRequest.secondBorrower.workContractEndDate | not present | optional |
| lead.contactRequest.secondBorrower.maritalStatus | not present | optional |
| lead.contactRequest.secondBorrower.income | not present | optional |
| lead.contactRequest.secondBorrower.spending | not present | optional |
| lead.contactRequest.financingObject | not present | optional |
| lead.contactRequest.financingObject.street | not present | optional |
| lead.contactRequest.financingObject.streetNumber | not present | optional |
| lead.contactRequest.financingObject.postalCode | not present | optional |
| lead.contactRequest.financingObject.city | not present | optional |
| lead.contactRequest.financingObject.type | not present | optional |
| lead.contactRequest.financingObject.subType | not present | optional |
| lead.contactRequest.financingObject.livingArea | not present | optional |
| lead.contactRequest.financingObject.siteArea | not present | optional |
| lead.contactRequest.financingObject.constructionYear | not present | optional |
| lead.contactRequest.income | not present | optional |
| lead.contactRequest.income.salary | not present | optional |
| lead.contactRequest.income.numberOfSalaries | not present | optional |
| lead.contactRequest.income.alimony | not present | optional |
| lead.contactRequest.income.pension | not present | optional |
| lead.contactRequest.income.rental | not present | optional |
| lead.contactRequest.income.childBenefits | not present | optional |
| lead.contactRequest.income.other | not present | optional |
| lead.contactRequest.spending | not present | optional |
| lead.contactRequest.spending.livingCost | not present | optional |
| lead.contactRequest.spending.rent | not present | optional |
| lead.contactRequest.spending.buildingSaving | not present | optional |
| lead.contactRequest.spending.saving | not present | optional |
| lead.contactRequest.spending.alimony | not present | optional |
| lead.contactRequest.spending.healthInsurance | not present | optional |
| lead.contactRequest.spending.pensionInsurance | not present | optional |
| lead.contactRequest.spending.creditRate | not present | optional |
| lead.contactRequest.spending.numberOfVehicles | not present | optional |
| lead.contactRequest.spending.other | not present | optional |
| lead.contactRequest.title | defaults to NO\_TITLE | defaults to NO\_TITLE |
| lead.contactRequest.segmentClass | not present | optional |
| lead.contactRequest.experiments | not present | optional |
| lead.realEstate | optional | optional |
| lead.offerTracking | optional | optional |
| lead.processingStatus | mandatory | mandatory |
| lead.processingStatusChanged | mandatory | mandatory |
| lead.price | defaults to 0 | defaults to 0 |

### Response

XML:

|     |     |
| --- | --- |
| 1<br> 2<br> 3<br> 4<br> 5<br> 6<br> 7<br> 8<br> 9<br>10<br>11<br>12<br>13<br>14<br>15<br>16<br>17<br>18<br>19<br>20<br>21<br>22<br>23<br>24<br>25<br>26<br>27<br>28<br>29<br>30<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>63<br>64<br>65<br>66<br>67<br>68<br>69<br>70<br>71<br>72 | `<?xml version="1.0" encoding="UTF-8" standalone="yes"?> <ns3:leads xmlns:ns2="http://rest.immobilienscout24.de/schema/financing/construction/2.0"            xmlns:ns3="http://rest.immobilienscout24.de/schema/financing/construction/1.0">     <lead>         <id>987654</id>         <providerId>111</providerId>         <providerName>Name of the bank or finance broker</providerName>         <shortName>a short name or the name of a branch</shortName>         <requestDate>2014-07-03T20:50:12</requestDate>         <requestType>APPOINTMENT_REQUEST</requestType>         <shopLead>false</shopLead>         <contactRequest>             <useType>OWNER_OCCUPATION</useType>             <financingTerms>                 <amortizationRate>2.00</amortizationRate>                 <postalCode>10243</postalCode>                 <employment>EMPLOYED</employment>                 <fixedNominalInterestRate>TEN_YEARS</fixedNominalInterestRate>                 <financing xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="ns2:PurchaseFinancing">                     <purchasePrice>300000.00</purchasePrice>                     <ownFunds>20000.00</ownFunds>                     <additionalCosts>10000.00</additionalCosts>                     <financingStart>IN_LESS_THAN_THREE_MONTH</financingStart>                     <projectState>REAL_ESTATE_NOT_YET_VISITED</projectState>                 </financing>             </financingTerms>             <contactChannel>UNKNOWN</contactChannel>             <salutation>MRS</salutation>             <surname>Muster</surname>             <forename>Max</forename>             <email>max.muster@gmail.com</email>             <phoneNumber>55555</phoneNumber>             <message>Message of the requester</message>             <contactAddress>                 <street>Andreasstraße</street>                 <streetNumber>10</streetNumber>                 <postalCode>10243</postalCode>                 <location>Berlin</location>             </contactAddress>             <energeticModernization>AFTER_PURCHASE</energeticModernization>             <exposeId>987654321</exposeId>             <numberOfBorrowers>2</numberOfBorrowers>             <currentCredits>20000.00</currentCredits>             <bank>Parkbank</bank>             <primaryAppointmentDate>1621202400000</primaryAppointmentDate>             <secondaryAppointmentDate>1621634400000</secondaryAppointmentDate>             <primaryAppointmentTime>EIGHTEEN_UNTIL_NINETEEN</primaryAppointmentTime>             <secondaryAppointmentTime>ELEVEN_UNTIL_TWELVE</secondaryAppointmentTime>             <dpaAccepted>false</dpaAccepted>             <kfwPromotion>false</kfwPromotion>             <title>NO_TITLE</title>         </contactRequest>         <realEstate>             <id>29648095</id>             <title>Großzügiges Landhaus</title>             <type>HOUSE_BUY</type>             <purchasePrice>250000</purchasePrice>             <livingArea>200.00</livingArea>             <siteArea>1000.00</siteArea>             <constructionDate>1884</constructionDate>             <address>                 <street>Platz der Republik</street>                 <houseNumber>1</houseNumber>                 <postcode>11011</postcode>                 <city>Berlin</city>             </address>         </realEstate>         <processingStatus>APPOINTMENT_ARRANGED</processingStatus>         <processingStatusChanged>2021-05-17T10:54:09</processingStatusChanged>         <price>0</price>     </lead> </ns3:leads>` |

JSON:

|     |     |
| --- | --- |
| 1<br> 2<br> 3<br> 4<br> 5<br> 6<br> 7<br> 8<br> 9<br>10<br>11<br>12<br>13<br>14<br>15<br>16<br>17<br>18<br>19<br>20<br>21<br>22<br>23<br>24<br>25<br>26<br>27<br>28<br>29<br>30<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>63<br>64<br>65<br>66<br>67<br>68<br>69<br>70<br>71<br>72<br>73 | `{    "lead":[       {          "id":987654,          "providerId":111,          "providerName":"Name of the bank or finance broker",          "shortName":"a short name or the name of a branch",          "requestDate":"2014-07-03T20:50:12",          "requestType":"APPOINTMENT_REQUEST",          "shopLead": false,          "contactRequest":{             "financingTerms":{                "amortizationRate":2.00,                "postalCode":"10243",                "employment":"EMPLOYED",                "fixedNominalInterestRate":"TEN_YEARS",                "financing":{                   "type":"PurchaseFinancing",                   "purchasePrice":300000.00,                   "ownFunds":20000.00,                   "additionalCosts":10000.00,                   "financingStart":"IN_LESS_THAN_THREE_MONTH",                   "projectState":"REAL_ESTATE_NOT_YET_VISITED"                }             },             "contactChannel":"UNKNOWN",             "salutation":"MR",             "surname":"Muster",             "forename":"Max",             "email":"max.muster@gmail.com",             "phoneNumber":"55555",             "message":"Message of the requester",             "contactAddress":{                "street":"Andreasstraße",                "streetNumber":"10",                "postalCode":"10243",                "location":"Berlin"             },             "energeticModernization": "AFTER_PURCHASE",             "exposeId":987654321,             "numberOfBorrowers":2,             "currentCredits":20000.00,             "bank":"Parkbank",             "primaryAppointmentDate": 1621202400000,             "secondaryAppointmentDate": 1621634400000,             "primaryAppointmentTime": "EIGHTEEN_UNTIL_NINETEEN",             "secondaryAppointmentTime": "ELEVEN_UNTIL_TWELVE",             "dpaAccepted": false,             "kfwPromotion": false,             "title": "NO_TITLE",             "useType":"OWNER_OCCUPATION"          },          "realEstate":{             "id": 29648095,             "title":"Großzügiges Landhaus",             "type":"HOUSE_BUY",             "purchasePrice":250000,             "livingArea":200.00,             "siteArea":1000.00,             "constructionDate":1884,             "address":{                "street":"Platz der Republik",                "houseNumber":"1",                "postcode":"11011",                "city":"Berlin"             }          },          "processingStatus":"APPOINTMENT_ARRANGED",          "processingStatusChanged":"2021-05-17T10:54:09",          "price": 0       }    ] }` |