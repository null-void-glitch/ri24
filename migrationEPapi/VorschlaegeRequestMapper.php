<?php

/**
 * Maps the legacy Angebote v2 `ErfassteDaten` payload to the request body of the
 * Vorschläge API (`POST /v1/vorschlaege`):  { "metadaten": {...}, "kundenangaben": {...} }
 *
 * Replaces the sunset call:
 *     POST /v2/ergebnisliste/ermittlung   (ErfassteDaten body, no vorgangsNummer)
 *
 * The result is a plain nested array — json_encode() it directly as the POST body.
 * Per the Vorschläge "Tolerant Reader" contract, unknown leaf values are sent as
 * explicit null (meaning "no data known"), NOT omitted.
 *
 * Outstanding items are tagged with @verify / @todo below.
 */

namespace local\php\europace\client\mapper;

use local\php\europace\client\model\angebote\Antragsteller;
use local\php\europace\client\model\angebote\Beschaeftigung;
use local\php\europace\client\model\angebote\ErfassteDaten;
use local\php\europace\client\model\angebote\Finanzbedarf;
use local\php\europace\client\model\angebote\FinanzierungsObjekt;
use local\php\europace\client\model\angebote\Haushalt;
use local\php\europace\client\model\angebote\HaushaltsPositionen;
use local\php\europace\client\model\angebote\Vorhaben;

class VorschlaegeRequestMapper
{
    /**
     * @verify each RHS exists in the Vorschläge YAML `finanzierungszweck` enum.
     */
    private const VERWENDUNGSZWECK_MAP = [
        'KAUF'                       => 'KAUF',
        'NEUBAU'                     => 'NEUBAU',
        'KAUF_NEUBAU_VOM_BAUTRAEGER' => 'KAUF_NEUBAU_VOM_BAUTRAEGER',
        'MODERNISIERUNG_UMBAU_ANBAU' => 'MODERNISIERUNG_UMBAU_ANBAU',
        'ANSCHLUSSFINANZIERUNG'      => 'ANSCHLUSSFINANZIERUNG',
        'KAPITALBESCHAFFUNG'         => 'KAPITALBESCHAFFUNG',
    ];

    /**
     * Source enum (HAUS/EIGENTUMSWOHNUNG/GRUNDSTUECK) differs from the Vorschläge
     * vocabulary (example uses EINFAMILIENHAUS).
     * @verify the target literals against the Vorschläge YAML `objektArt` enum.
     */
    private const OBJEKT_ART_MAP = [
        'HAUS'             => 'EINFAMILIENHAUS',
        'EIGENTUMSWOHNUNG' => 'EIGENTUMSWOHNUNG',
        'GRUNDSTUECK'      => 'GRUNDSTUECK',
    ];

    /**
     * Identity by default. @verify HAUSFRAU / ARBEITSLOSER are accepted by Vorschläge.
     */
    private const BESCHAEFTIGUNGS_ART_MAP = [
        'ANGESTELLTER'   => 'ANGESTELLTER',
        'ARBEITER'       => 'ARBEITER',
        'BEAMTER'        => 'BEAMTER',
        'FREIBERUFLER'   => 'FREIBERUFLER',
        'SELBSTAENDIGER' => 'SELBSTAENDIGER',
        'RENTNER'        => 'RENTNER',
        'HAUSFRAU'       => 'HAUSFRAU',
        'ARBEITSLOSER'   => 'ARBEITSLOSER',
    ];

    /** Equity estimate = 10% of purchase price + incidental purchase costs. */
    private const EIGENKAPITAL_QUOTE = 0.10;

    /**
     * @param int|null $gewuenschteAnzahlVorschlaege replaces the old `alternativen` query param
     * @return array ready for json_encode() as the POST /v1/vorschlaege body
     */
    public function map(ErfassteDaten $ed, ?int $gewuenschteAnzahlVorschlaege = 3): array
    {
        $vorhaben     = $ed->getVorhaben();
        $finanzbedarf = $vorhaben !== null ? $vorhaben->getFinanzbedarf() : null;
        $eigenkapital = $this->computeEigenkapital($finanzbedarf);

        $haushalte = $ed->getHaushalte() ?? [];
        $mappedHaushalte = [];
        foreach ($haushalte as $idx => $haushalt) {
            // eigenKapital is a household-level field; assign the derived amount to the
            // primary household only so it is not counted once per household.
            $mappedHaushalte[] = $this->mapHaushalt($haushalt, $idx === 0 ? $eigenkapital : null);
        }

        return [
            'metadaten' => [
                // @verify productive literal: ErfassteDaten allows TEST_MODUS | ECHT_GESCHAEFT;
                //         the Vorschläge example only shows TEST_MODUS.
                'datenkontext'                 => $ed->getDatenKontext(),
                'extKundenId'                  => $ed->getExterneVorgangsNummer(), // @verify source
                'extClientId'                  => null,                            // @todo from getLeadTracking() if used
                'gewuenschteAnzahlVorschlaege' => $gewuenschteAnzahlVorschlaege,
            ],
            'kundenangaben' => [
                'haushalte'           => $mappedHaushalte,
                'finanzierungsbedarf' => $this->mapFinanzierungsbedarf($vorhaben),
                'finanzierungsobjekt' => $this->mapFinanzierungsobjekt($ed->getFinanzierungsObjekt()),
            ],
        ];
    }

    private function mapHaushalt(Haushalt $h, ?float $eigenkapital): array
    {
        $kunden = [];
        foreach ($h->getAntragsteller() ?? [] as $antragsteller) {
            $kunden[] = $this->mapKunde($antragsteller);
        }

        return [
            'kunden'               => $kunden,
            'finanzielleSituation' => $this->mapFinanzielleSituation($h->getPositionen(), $eigenkapital),
        ];
    }

    private function mapKunde(Antragsteller $a): array
    {
        $b   = $a->getBeschaeftigung();
        $art = $b !== null ? $b->getArt() : null;
        $befristungsStatus = $b !== null ? $b->getBefristungsStatus() : null;

        return [
            'geburtsdatum'       => self::fmtDate($a->getGeburtsdatum()),
            'einkommenNetto'     => $b !== null ? $b->getEinkommenNettoMonatlich() : null,
            'beschaeftigungsArt' => $art !== null ? (self::BESCHAEFTIGUNGS_ART_MAP[$art] ?? $art) : null,
            'beschaeftigtSeit'   => $b !== null ? self::fmtDate($b->getBeschaeftigtSeit()) : null,
            'arbeitBefristet'    => $befristungsStatus !== null
                ? ($befristungsStatus === Beschaeftigung::BEFRISTUNGS_STATUS_BEFRISTET)
                : null,
        ];
    }

    private function mapFinanzielleSituation(?HaushaltsPositionen $p, ?float $eigenkapital): array
    {
        if ($p === null) {
            return ['eigenKapital' => $eigenkapital];
        }

        $notAbgeloest = static function ($v) {
            return $v->getWirdAbgeloest() !== true;
        };

        return [
            'eigenKapital'                          => $eigenkapital,
            'sonstigeEinnahmen'                     => $this->sumWhere($p->getSonstigeEinnahmen(), 'getEinnahmenMonatlich'),
            'gesamtRatenkrediteRestschuld'          => $this->sumWhere($p->getRatenkredite(), 'getRestschuld'),
            'verbleibendeRatenkrediteRestschuld'    => $this->sumWhere($p->getRatenkredite(), 'getRestschuld', $notAbgeloest),
            'verbleibendeRatenkrediteRateMonatlich' => $this->sumWhere($p->getRatenkredite(), 'getRateMonatlich', $notAbgeloest),
            'gesamtPrivateDarlehenRestschuld'       => $this->sumWhere($p->getPrivateDarlehen(), 'getRestschuld'),
        ];
    }

    private function mapFinanzierungsbedarf(?Vorhaben $v): array
    {
        if ($v === null) {
            return [];
        }
        $fb    = $v->getFinanzbedarf();
        $zweck = $v->getVerwendungszweck();

        return [
            'finanzierungszweck'                       => $zweck !== null ? (self::VERWENDUNGSZWECK_MAP[$zweck] ?? null) : null,
            'kaufpreis'                                => $fb !== null ? $fb->getKaufpreis() : null,
            'grundstueckKaufpreis'                     => $fb !== null ? $fb->getGrundstuecksKaufpreis() : null,
            'modernisierungsKostenInklEigenleistungen' => $fb !== null ? $fb->getModernisierung() : null,
            'modernisierungEigenleistung'              => $v->getEigenleistungWennNeubauOderModernisierungsmassnahmen(),
            // praeferenzen is OPTIONAL. Finanzierungswunsch holds darlehensWuensche[]
            // (DarlehensWunsch[]) — mapping rate/laufzeit/dates needs that model plus a
            // business rule for which wish to use. Sent null until then.
            'praeferenzen'                             => null, // @todo needs DarlehensWunsch
        ];
    }

    private function mapFinanzierungsobjekt(?FinanzierungsObjekt $o): array
    {
        if ($o === null) {
            return [];
        }

        $geb     = $o->getGebaeude();
        $adr     = $o->getAdresse();
        $baujahr = $geb !== null ? $geb->getBaujahr() : null;

        $wohnflaeche = null;
        if ($geb !== null) {
            $wf = $geb->getWohnflaeche();               // GebaeudeFlaeche
            $wohnflaeche = $wf !== null ? $wf->getGesamtGroesse() : null;
        }

        $gewerblicheNutzung = null;
        if ($geb !== null) {
            $gewerblicheNutzung = ($geb->getAnzahlDerGewerbeeinheiten() ?? 0) > 0
                || $geb->getGewerbeflaeche() !== null;
        }

        return [
            'objektArt'          => self::OBJEKT_ART_MAP[$o->getObjektArt()] ?? null,
            'wohnflaeche'        => $wohnflaeche,
            'baujahr'            => $baujahr !== null ? (int) $baujahr : null,
            'gewerblicheNutzung' => $gewerblicheNutzung,
            // No vermietet flag on Gebaeude; the real source is
            // GebaeudeFlaeche::getVermietungsInformationen(). Sent null by decision.
            'vermietet'          => null,
            'anschrift'          => $adr === null ? null : [
                'plz'        => $adr->getPostleitzahl(),
                'ort'        => $adr->getOrt(),
                'strasse'    => $adr->getStrasse(),
                'hausnummer' => $adr->getHausnummer(),
            ],
        ];
    }

    /** Equity = 10% of purchase price + incidental purchase costs (Kaufnebenkosten). */
    private function computeEigenkapital(?Finanzbedarf $fb): ?float
    {
        if ($fb === null) {
            return null;
        }
        $kaufpreis = (float) ($fb->getKaufpreis() ?? 0.0);
        if ($kaufpreis <= 0.0) {
            return null;
        }
        // Classic Kaufnebenkosten: Grunderwerbsteuer + Maklergebühr + Notargebühr.
        // Adjust if your definition includes other Finanzbedarf cost components.
        $kaufnebenkosten = (float) ($fb->getGrunderwerbsteuer() ?? 0.0)
            + (float) ($fb->getMaklergebuehr() ?? 0.0)
            + (float) ($fb->getNotargebuehr() ?? 0.0);

        return round(self::EIGENKAPITAL_QUOTE * $kaufpreis + $kaufnebenkosten, 2);
    }

    /** Sum $valueGetter over items, optionally filtered; null when nothing applies. */
    private function sumWhere(?array $items, string $valueGetter, ?callable $filter = null): ?float
    {
        if (empty($items)) {
            return null;
        }
        $sum  = 0.0;
        $seen = false;
        foreach ($items as $i) {
            if ($filter !== null && !$filter($i)) {
                continue;
            }
            $sum += (float) $i->$valueGetter();
            $seen = true;
        }
        return $seen ? $sum : null;
    }

    private static function fmtDate(?\DateTime $d): ?string
    {
        return $d !== null ? $d->format('Y-m-d') : null;
    }
}
