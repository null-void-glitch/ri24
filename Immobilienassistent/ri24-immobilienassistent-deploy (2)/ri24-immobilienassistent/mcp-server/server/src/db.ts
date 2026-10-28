import { createReadStream, createWriteStream, existsSync, statSync } from 'node:fs';
import path from 'node:path';
import { Readable } from 'stream';
import sax from 'sax';

export interface Property {
  id: string;
  title: string;
  location: string;
  price: number;
  anzahl_zimmer: number;
  flaeche: number;
  propertyType: string;
  imageUrl: string;
  url?: string;
  vermarktungsart?: string;
  wohnenAufZeit?: boolean;
  softFeatures: string[];
}

let propertiesCache: Property[] | null = null;
let isFetching = false;

const EXPORT_PATH = path.resolve(process.cwd(), '..', 'export.full.xml');

/**
 * Downloads the remote OpenImmo XML and saves it to disk (export.full.xml).
 * Returns true on success, false on failure.
 */
export async function downloadRemoteXML(): Promise<boolean> {
  const url = process.env.OPENIMMO_URL;
  const user = process.env.OPENIMMO_USER;
  const pass = process.env.OPENIMMO_PASS;

  if (!url) return false;

  try {
    const headers: Record<string, string> = {};
    if (user && pass) {
      headers['Authorization'] = `Basic ${Buffer.from(`${user}:${pass}`).toString('base64')}`;
    }

    console.log(`[OpenImmo] Downloading remote XML from ${url}...`);
    const res = await fetch(url, { headers });
    if (!res.ok || !res.body) {
      console.error(`[OpenImmo] Remote fetch failed with status: ${res.status}`);
      return false;
    }

    // Stream directly to disk to handle large files efficiently
    const fileStream = createWriteStream(EXPORT_PATH);
    const readable = Readable.fromWeb(res.body as any) as Readable;

    await new Promise<void>((resolve, reject) => {
      readable.pipe(fileStream);
      fileStream.on('finish', resolve);
      fileStream.on('error', reject);
      readable.on('error', reject);
    });

    const size = statSync(EXPORT_PATH).size;
    console.log(`[OpenImmo] Downloaded ${Math.round(size / 1024 / 1024)} MB to ${EXPORT_PATH}`);
    return true;
  } catch (err) {
    console.error(`[OpenImmo] Remote download error:`, err);
    return false;
  }
}

/**
 * Extracts soft-filter feature keys from OpenImmo ausstattung and freitexte objects.
 * Uses a two-tier strategy:
 *   1. Direct XML field/attribute matching (precise)
 *   2. Keyword fallback in freitext fields (fuzzy)
 */
function extractSoftFeatures(ausstattung: any, freitexte: any): string[] {
  const features = new Set<string>();

  if (!ausstattung && !freitexte) return [];

  const attr = (obj: any): Record<string, string> => {
    if (!obj) return {};
    return obj._attributes || {};
  };

  const hasAttr = (obj: any, key: string, value?: string): boolean => {
    const a = attr(obj);
    if (value) return a[key] === value || a[key.toUpperCase()] === value || a[key.toLowerCase()] === value;
    return key in a || key.toUpperCase() in a || key.toLowerCase() in a;
  };

  const isTrue = (obj: any, key: string): boolean => {
    const a = attr(obj);
    const k = Object.keys(a).find(k2 => k2.toUpperCase() === key.toUpperCase());
    if (!k) return false;
    const v = a[k];
    return v === 'true' || v === '1' || v === 'JA' || v === 'ja';
  };

  const getText = (obj: any): string => {
    if (!obj) return '';
    if (typeof obj === 'string') return obj;
    if (obj['#text']) return String(obj['#text']);
    return '';
  };

  if (ausstattung) {
    // ── Balkon ──────────────────────────────────────────────────────────────
    // Check for balkon in ausricht_balkon_terrasse attributes or anzahl_balkone
    const ausricht = ausstattung.ausricht_balkon_terrasse;
    if (ausricht) {
      const a = attr(ausricht);
      const hasDir = Object.values(a).some(v => v === '1' || v === 'true');
      if (hasDir) features.add('balkon');
    }
    const anzBalkone = parseFloat(getText(ausstattung.anzahl_balkone));
    if (!isNaN(anzBalkone) && anzBalkone > 0) features.add('balkon');

    // ── Terrasse ─────────────────────────────────────────────────────────────
    const anzTerrassen = parseFloat(getText(ausstattung.anzahl_terrassen));
    if (!isNaN(anzTerrassen) && anzTerrassen > 0) features.add('terrasse');
    // terrasse as a boolean attribute sometimes
    if (isTrue(ausstattung.terrassen_flaeche, 'JA') || ausstattung.terrasse) {
      features.add('terrasse');
    }

    // ── Garten ───────────────────────────────────────────────────────────────
    if (isTrue(ausstattung.gartennutzung, 'JA') || ausstattung.gartennutzung) {
      const g = ausstattung.gartennutzung;
      const a = attr(g);
      if (Object.keys(a).length > 0) features.add('garten');
      else if (getText(g) === 'JA' || getText(g) === 'true') features.add('garten');
    }

    // ── Aufzug ───────────────────────────────────────────────────────────────
    if (ausstattung.fahrstuhl) {
      const a = attr(ausstattung.fahrstuhl);
      if (Object.values(a).some(v => v === '1' || v === 'true' || v === 'JA')) {
        features.add('aufzug');
      }
    }

    // ── Barrierefrei ─────────────────────────────────────────────────────────
    if (ausstattung.rollstuhlgerecht || isTrue(ausstattung.barrierefrei, 'JA')) {
      const a = attr(ausstattung.rollstuhlgerecht || ausstattung.barrierefrei);
      if (Object.values(a).some(v => v === 'JA' || v === '1' || v === 'true') || getText(ausstattung.rollstuhlgerecht) === 'JA') {
        features.add('barrierefrei');
      }
    }

    // ── Gäste-WC ─────────────────────────────────────────────────────────────
    if (ausstattung.gaestewc) {
      const a = attr(ausstattung.gaestewc);
      if (Object.values(a).some(v => v === 'JA' || v === '1' || v === 'true') || getText(ausstattung.gaestewc) === 'JA') {
        features.add('gaeste_wc');
      }
    }

    // ── Einbauküche ───────────────────────────────────────────────────────────
    if (ausstattung.kueche) {
      const a = attr(ausstattung.kueche);
      if (a['EBK'] === '1' || a['ebk'] === '1' || a['EBK'] === 'true' || getText(ausstattung.kueche).toUpperCase().includes('EBK')) {
        features.add('einbaukueche');
      }
    }

    // ── Bad: Wanne + Dusche ───────────────────────────────────────────────────
    if (ausstattung.bad) {
      const a = attr(ausstattung.bad);
      if (a['WANNE'] === '1' || a['wanne'] === '1' || a['WANNE'] === 'true') features.add('badewanne');
      if (a['DUSCHE'] === '1' || a['dusche'] === '1' || a['DUSCHE'] === 'true') features.add('dusche');
    }

    // ── Fußbodenheizung ───────────────────────────────────────────────────────
    if (ausstattung.heizungsart) {
      const a = attr(ausstattung.heizungsart);
      if (a['FUSSBODEN'] === '1' || a['fussboden'] === '1' || Object.keys(a).some(k => k.toUpperCase() === 'FUSSBODEN')) {
        features.add('fussbodenheizung');
      }
    }

    // ── Kamin ─────────────────────────────────────────────────────────────────
    if (ausstattung.kamin) {
      const a = attr(ausstattung.kamin);
      if (Object.values(a).some(v => v === 'JA' || v === '1' || v === 'true') || getText(ausstattung.kamin).toUpperCase() === 'JA') {
        features.add('kamin');
      }
    }

    // ── Abstellraum ───────────────────────────────────────────────────────────
    if (ausstattung.abstellraum) {
      const a = attr(ausstattung.abstellraum);
      if (Object.values(a).some(v => v === 'JA' || v === '1' || v === 'true') || getText(ausstattung.abstellraum).toUpperCase() === 'JA') {
        features.add('abstellraum');
      }
    }

    // ── Keller ───────────────────────────────────────────────────────────────
    if (ausstattung.unterkellert) {
      const a = attr(ausstattung.unterkellert);
      const v = a['keller'] || a['KELLER'];
      if (v === 'JA' || v === '1' || v === 'true') features.add('keller');
    }

    // ── Dachboden ─────────────────────────────────────────────────────────────
    if (ausstattung.dachboden) {
      const a = attr(ausstattung.dachboden);
      if (Object.values(a).some(v => v === 'JA' || v === '1' || v === 'true') || getText(ausstattung.dachboden).toUpperCase() === 'JA') {
        features.add('dachboden');
      }
    }

    // ── Möbliert ─────────────────────────────────────────────────────────────
    if (ausstattung.moebliert) {
      const a = attr(ausstattung.moebliert);
      const mobVal = a['MOEBLIERT'] || a['moebliert'] || getText(ausstattung.moebliert);
      if (mobVal && mobVal.toUpperCase() !== 'NEIN' && mobVal !== '0' && mobVal !== 'false') {
        features.add('moebliert');
      }
    }

    // ── Klimaanlage ───────────────────────────────────────────────────────────
    if (ausstattung.klimatisiert) {
      const a = attr(ausstattung.klimatisiert);
      if (Object.values(a).some(v => v === 'JA' || v === '1' || v === 'true') || getText(ausstattung.klimatisiert).toUpperCase() === 'JA') {
        features.add('klimaanlage');
      }
    }

    // ── Stellplatz / Garage / Tiefgarage ─────────────────────────────────────
    if (ausstattung.stellplatz_art) {
      const stellList = Array.isArray(ausstattung.stellplatz_art)
        ? ausstattung.stellplatz_art
        : [ausstattung.stellplatz_art];
      for (const st of stellList) {
        const a = attr(st);
        if (a['GARAGE'] === '1' || a['garage'] === '1') features.add('garage');
        if (a['TIEFGARAGE'] === '1' || a['tiefgarage'] === '1') features.add('tiefgarage');
        if (a['STELLPLATZ'] === '1' || a['AUSSEN'] === '1' || Object.keys(a).length > 0) features.add('stellplatz');
      }
    }

    // ── E-Auto Ladestation ───────────────────────────────────────────────────
    if (ausstattung.ladevorrichtung) {
      const a = attr(ausstattung.ladevorrichtung);
      if (Object.values(a).some(v => v === 'JA' || v === '1' || v === 'true') || getText(ausstattung.ladevorrichtung).toUpperCase() === 'JA') {
        features.add('e_ladestation');
      }
    }

    // ── Haustiere erlaubt ─────────────────────────────────────────────────────
    if (ausstattung.haustiere) {
      const a = attr(ausstattung.haustiere);
      const hv = a['HAUSTIERE'] || a['haustiere'] || getText(ausstattung.haustiere);
      if (hv && (hv.toUpperCase() === 'JA' || hv === '1' || hv === 'true')) {
        features.add('haustiere_erlaubt');
      }
    }

    // ── WG-geeignet ───────────────────────────────────────────────────────────
    if (ausstattung.wg_geeignet) {
      const a = attr(ausstattung.wg_geeignet);
      if (Object.values(a).some(v => v === 'JA' || v === '1' || v === 'true') || getText(ausstattung.wg_geeignet).toUpperCase() === 'JA') {
        features.add('wg_geeignet');
      }
    }

    // ── Baujahr / Neubau / Altbau ─────────────────────────────────────────────
    if (ausstattung.zustand_angaben) {
      const a = attr(ausstattung.zustand_angaben);
      const v = Object.keys(a).find(k => a[k] === '1' || a[k] === 'true')?.toUpperCase();
      if (v === 'ERSTBEZUG' || v === 'NEUBAU') features.add('neubau');
      if (v === 'ALTBAU') features.add('altbau');
      if (v === 'MODERNISIERT' || v === 'SANIERT') features.add('modernisiert');
    }

    // ── Energieeffizient (Energiepass endenergiebedarf < 50 kWh/m²a) ─────────
    if (ausstattung.energiepass) {
      const ep = Array.isArray(ausstattung.energiepass) ? ausstattung.energiepass[0] : ausstattung.energiepass;
      const endVal = parseFloat(getText(ep?.endenergiebedarf));
      if (!isNaN(endVal) && endVal <= 50) features.add('energieeffizient');
    }

    // ── Hausmeisterservice ────────────────────────────────────────────────────
    if (ausstattung.sicherheitstechniken || ausstattung.serviceleistungen) {
      // Not a direct standard field; handled via freitext below
    }
  }

  // ── Freitext-Fallback (Stufe 2) ────────────────────────────────────────────
  const titelText = getText(freitexte?.objekttitel).toLowerCase();
  const lageText = (getText(freitexte?.lage) + ' ' + getText(freitexte?.ausstattung_beschreibung)).toLowerCase();
  const objektText = getText(freitexte?.objektbeschreibung).toLowerCase();
  const allText = titelText + ' ' + lageText + ' ' + objektText;

  const keywords: Record<string, string[]> = {
    balkon: ['balkon', 'balkone'],
    terrasse: ['terrasse', 'terrassen', 'dachterrasse'],
    garten: ['garten', 'gartenanteil', 'gartennutzung'],
    aufzug: ['aufzug', 'fahrstuhl', 'lift'],
    barrierefrei: ['barrierefrei', 'rollstuhlgerecht', 'seniorengerecht'],
    gaeste_wc: ['gäste-wc', 'gästewc', 'gäste wc', 'gaeste-wc', 'gaestewc'],
    einbaukueche: ['einbauküche', 'einbaukueche', 'ebk'],
    badewanne: ['badewanne', 'wanne'],
    dusche: ['dusche', 'duschkabine', 'bodengleich'],
    fussbodenheizung: ['fußbodenheizung', 'fussbodenheizung', 'flächenheizung'],
    kamin: ['kamin', 'ofen', 'kachelofen', 'fireplace'],
    abstellraum: ['abstellraum', 'abstellkammer', 'lagerraum'],
    keller: ['keller', 'unterkellerung', 'kellerraum'],
    dachboden: ['dachboden', 'dachspeicher'],
    moebliert: ['möbliert', 'moebliert', 'voll möbliert'],
    klimaanlage: ['klimaanlage', 'klimatisiert', 'klima'],
    stellplatz: ['stellplatz', 'parkplatz', 'außenparkplatz'],
    garage: ['garage', 'einzelgarage'],
    tiefgarage: ['tiefgarage', 'tiefgaragenstellplatz'],
    e_ladestation: ['e-ladestation', 'ladestation', 'wallbox', 'elektroauto'],
    fahrradraum: ['fahrradraum', 'fahrradkeller', 'fahrradstellplatz'],
    haustiere_erlaubt: ['haustiere erlaubt', 'haustiere willkommen', 'tierfreundlich', 'kein haustierverbot'],
    wg_geeignet: ['wg geeignet', 'wg-geeignet', 'wohngemeinschaft'],
    familienfreundlich: ['familienfreundlich', 'familiengeeignet', 'kindergerecht'],
    seniorenfreundlich: ['seniorenfreundlich', 'seniorengerecht', 'altersgerecht', 'senioren', 'für senioren', 'rollstuhlgerecht'],
    neubau: ['neubau', 'erstbezug', 'neubauprojekt'],
    altbau: ['altbau', 'gründerzeit', 'altbauwohnung'],
    modernisiert: ['modernisiert', 'saniert', 'kernsaniert', 'renoviert'],
    energieeffizient: ['energieeffizient', 'niedrigenergie', 'passivhaus', 'kfw'],
    hausmeisterservice: ['hausmeister', 'hausmeisterservice'],
    ruhige_lage: ['ruhige lage', 'ruhig gelegen', 'wenig verkehr', 'ruhiges wohngebiet'],
    zentrale_lage: ['zentrale lage', 'top lage', 'bestlage', 'stadtzentrum', 'zentrumsnah'],
    naturnahe_lage: ['naturnahe', 'grüne umgebung', 'nahe wald', 'nahe see', 'naturlage'],
    innenstadtlage: ['innenstadt', 'city lage', 'innenstadtlage', 'stadtmitte'],
    blick_ins_gruene: ['blick ins grüne', 'grünblick', 'gartenblick', 'naturblick'],
    suedausrichtung: ['südausrichtung', 'südlage', 'südseitig', 'sonnig gelegen'],
    erdgeschoss: ['erdgeschoss', 'eg-wohnung', 'ebenerdig'],
    dachgeschoss: ['dachgeschoss', 'dg-wohnung', 'penthouse'],
    helle_wohnung: ['helle wohnung', 'viel tageslicht', 'lichtdurchflutet', 'hell und freundlich'],
    hohe_decken: ['hohe decken', 'stuckdecken', 'raumhohe fenster'],
    oeffentlicher_nv: ['öpnv', 'öffentliche verkehrsmittel', 's-bahn', 'u-bahn', 'bus anbindung', 'bahnhof'],
    nahe_bahnhof: ['bahnhof', 'hauptbahnhof', 'bahnhofsnähe', 'bahnhof in der nähe'],
    autobahnanbindung: ['autobahn', 'autobahnauffahrt', 'autobahnanbindung'],
    einkauf_nah: ['einkaufen', 'supermarkt', 'einkaufsmöglichkeiten', 'nahversorgung'],
    schule_nah: ['schule', 'gymnasium', 'gesamtschule'],
    kindergarten_nah: ['kindergarten', 'kita', 'kindertagesstätte'],
    arzt_nah: ['arzt', 'apotheke', 'krankenhaus', 'medizinische versorgung'],
    restaurant_nah: ['restaurant', 'café', 'gastronomie in der nähe'],
    park_nah: ['park', 'grünanlage', 'naherholung', 'spielpark'],
    spielplatz_nah: ['spielplatz'],
    provisionsfrei: ['provisionsfrei', 'keine provision', 'ohne maklergebühr', 'ohne provision'],
    kurzzeitmiete: ['kurzzeitmiete', 'zeitlich befristet', 'wohnen auf zeit'],
  };

  for (const [featureKey, words] of Object.entries(keywords)) {
    if (features.has(featureKey)) continue; // already found via direct XML
    if (words.some(w => allText.includes(w))) {
      features.add(featureKey);
    }
  }

  return Array.from(features);
}

export function parseOpenImmoXMLStream(stream: Readable): Promise<Property[]> {
  return new Promise((resolve, reject) => {
    const newProperties: Property[] = [];
    const saxStream = sax.createStream(true, { trim: true });

    let inImmobilie = false;
    let contextStack: any[] = [];
    let currentText = '';

    saxStream.on('error', (e) => reject(e));

    saxStream.on('opentag', (node) => {
      if (node.name === 'immobilie') {
        inImmobilie = true;
        contextStack = [{}];
      } else if (inImmobilie) {
        const newObj: any = { _attributes: node.attributes };
        const parent = contextStack[contextStack.length - 1];

        if (parent[node.name]) {
          if (!Array.isArray(parent[node.name])) {
            parent[node.name] = [parent[node.name]];
          }
          parent[node.name].push(newObj);
        } else {
          parent[node.name] = newObj;
        }
        contextStack.push(newObj);
      }
      currentText = '';
    });

    saxStream.on('text', (t) => {
      if (inImmobilie) currentText += t;
    });

    saxStream.on('cdata', (t) => {
      if (inImmobilie) currentText += t;
    });

    saxStream.on('closetag', (name) => {
      if (name === 'immobilie') {
        inImmobilie = false;
        const immo = contextStack[0];

        const extractText = (val: any, defaultVal: string = ""): string => {
          if (val === undefined || val === null) return defaultVal;
          if (typeof val === "string") return val;
          if (typeof val === "number") return val.toString();
          if (typeof val === "object" && val["#text"]) return String(val["#text"]);
          if (Array.isArray(val)) return extractText(val[0], defaultVal);
          return defaultVal || String(val);
        };

        const id = extractText(immo?.verwaltung_techn?.objektnr_intern, Math.random().toString(36).substring(7));
        const title = extractText(immo?.freitexte?.objekttitel, "Untitled Property");
        const location = extractText(immo?.geo?.ort || immo?.geo?.postf_ort, "Unknown Location");
        const priceStr = extractText(immo?.preise?.kaufpreis || immo?.preise?.kaltmiete || immo?.preise?.warmmiete, "0");
        // Smart number parsing: handle both German (1.234,56) and English (1234.56) formats
        const parseGermanNumber = (s: string): number => {
          const trimmed = s.trim();
          const hasDot = trimmed.includes('.');
          const hasComma = trimmed.includes(',');
          if (hasDot && hasComma) {
            // German format: 1.234,56 → remove dots, comma→dot
            return parseFloat(trimmed.replace(/\./g, '').replace(',', '.'));
          } else if (hasComma && !hasDot) {
            // German decimal only: 295,31 → comma→dot
            return parseFloat(trimmed.replace(',', '.'));
          } else if (hasDot && !hasComma) {
            // Ambiguous dot: check digits after last dot
            const afterDot = trimmed.split('.').pop() || '';
            if (afterDot.length === 3 && trimmed.split('.').length > 2) {
              // Multiple dots like 1.234.567 → thousands separators
              return parseFloat(trimmed.replace(/\./g, ''));
            } else if (afterDot.length <= 2) {
              // 295.31 or 295.5 → English decimal
              return parseFloat(trimmed);
            } else {
              // 1.234 (single dot, 3 digits after) → thousands separator
              // But could also be a decimal 1.234 meaning 1.234 → ambiguous, treat as decimal for small numbers
              const raw = parseFloat(trimmed);
              const asThousands = parseFloat(trimmed.replace(/\./g, ''));
              // If removing dot gives a number > 10000 and original < 10, it's likely a decimal
              return raw < 100 ? raw : asThousands;
            }
          }
          return parseFloat(trimmed) || 0;
        };
        const price = parseGermanNumber(priceStr);
        const anzahlZimmerStr = extractText(immo?.flaechen?.anzahl_zimmer || immo?.flaechen?.anzahl_schlafzimmer, "0");
        const anzahl_zimmer = parseFloat(anzahlZimmerStr);

        const flaecheStr = extractText(immo?.flaechen?.wohnflaeche || immo?.flaechen?.nutzflaeche || immo?.flaechen?.gesamtflaeche || immo?.flaechen?.grundstuecksflaeche, "0");
        const flaeche = parseFloat(flaecheStr);

        const url = extractText(immo?.kontaktperson?.url, "");

        let type: string = "sonstige";
        if (immo?.objektkategorie?.objektart) {
          const keys = Object.keys(immo.objektkategorie.objektart).filter(k => k !== '_attributes' && k !== 'objektart_zusatz');
          if (keys.length > 0) {
            type = keys[0];
          } else if (immo.objektkategorie.objektart._attributes) {
            const mappedAttr = immo.objektkategorie.objektart._attributes;
            const trueKey = Object.keys(mappedAttr).find(k => k !== 'xmlns' && mappedAttr[k] === 'true');
            if (trueKey) {
              type = trueKey;
            } else {
              const attrKeys = Object.keys(mappedAttr).filter(k => k !== 'xmlns');
              if (attrKeys.length > 0) type = attrKeys[0];
            }
          }
        }

        let vermarktungsart: string = "unbekannt";
        if (immo?.objektkategorie?.vermarktungsart) {
          const vKeys = Object.keys(immo.objektkategorie.vermarktungsart).filter(k => k !== '_attributes');
          if (vKeys.length > 0) {
            vermarktungsart = vKeys[0].toLowerCase();
          } else if (immo.objektkategorie.vermarktungsart._attributes) {
            const mappedAttr = immo.objektkategorie.vermarktungsart._attributes;
            const trueKey = Object.keys(mappedAttr).find(k => k !== 'xmlns' && mappedAttr[k] === 'true');
            if (trueKey) {
              vermarktungsart = trueKey.toLowerCase();
            } else {
              const attrKeys = Object.keys(mappedAttr).filter(k => k !== 'xmlns');
              if (attrKeys.length > 0) vermarktungsart = attrKeys[0].toLowerCase();
            }
          }
        }

        let imageUrl = "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400";
        if (immo?.anhaenge?.anhang) {
          const anhangeList = Array.isArray(immo.anhaenge.anhang) ? immo.anhaenge.anhang : [immo.anhaenge.anhang];
          const firstImg = anhangeList.find((a: any) => a.daten?.pfad?.["#text"] || (typeof a.daten?.pfad === 'string' && a.daten?.pfad) || a.daten?.pfad?._attributes);
          if (firstImg) {
            let pfad = firstImg.daten.pfad?.["#text"] || firstImg.daten.pfad;
            if (typeof pfad === 'object' && pfad?._attributes?.['xmlns']) pfad = pfad['#text'];
            if (typeof pfad === 'string' && pfad.startsWith("http")) {
              imageUrl = pfad;
            }
          }
        }

        // Extract WAZ (Wohnen auf Zeit) from nutzungsart
        const nutzungsartAttrs = immo?.objektkategorie?.nutzungsart?._attributes || {};
        const wohnenAufZeit = nutzungsartAttrs['WAZ'] === 'true' || nutzungsartAttrs['waz'] === 'true' || nutzungsartAttrs['WAZ'] === '1';

        // Extract soft features from ausstattung + freitexte
        const softFeatures = extractSoftFeatures(immo?.ausstattung, immo?.freitexte);

        newProperties.push({
          id: id.toString(),
          title: title.toString(),
          location: location.toString(),
          price: isNaN(price) ? 0 : price,
          anzahl_zimmer: isNaN(anzahl_zimmer) ? 0 : anzahl_zimmer,
          flaeche: isNaN(flaeche) ? 0 : flaeche,
          propertyType: type,
          url,
          vermarktungsart,
          wohnenAufZeit,
          imageUrl,
          softFeatures,
        });

        contextStack = [];
      } else if (inImmobilie) {
        const top = contextStack.pop();
        if (top && currentText.trim()) {
          top["#text"] = currentText;
        }
      }
      currentText = '';
    });

    saxStream.on('end', () => {
      resolve(newProperties);
    });

    stream.pipe(saxStream);
  });
}

export async function loadProperties() {
  if (isFetching) return;
  isFetching = true;
  try {
    // Step 1: Try to download fresh data from remote source and save to disk
    const downloaded = await downloadRemoteXML();
    if (downloaded) {
      console.log(`[OpenImmo] Fresh data downloaded, parsing...`);
    }

    // Step 2: Parse from local file (either freshly downloaded or existing)
    const data127Path = path.resolve(process.cwd(), '..', 'openimmo-data_127.xml');
    let targetPath: string | null = null;
    if (existsSync(EXPORT_PATH)) targetPath = EXPORT_PATH;
    else if (existsSync(data127Path)) targetPath = data127Path;

    if (targetPath) {
      const size = statSync(targetPath).size;
      console.log(`[OpenImmo] Parsing ${targetPath} (${Math.round(size / 1024 / 1024)} MB)...`);
      const stream = createReadStream(targetPath) as Readable;
      const parsedProperties = await parseOpenImmoXMLStream(stream);
      propertiesCache = parsedProperties;
      console.log(`[OpenImmo] Successfully cached ${parsedProperties.length} properties at ${new Date().toISOString()}.`);
    } else {
      console.warn('[OpenImmo] No XML file found (neither remote download nor local fallback).');
    }
  } catch (err) {
    console.error(`[OpenImmo] Error loading properties:`, err);
  } finally {
    isFetching = false;
  }
}

// Initial boot load
loadProperties();

// Schedule daily refresh (default: every 24h, configurable via REFRESH_INTERVAL_HOURS)
const refreshHours = parseFloat(process.env.REFRESH_INTERVAL_HOURS || '24');
setInterval(loadProperties, refreshHours * 60 * 60 * 1000);
console.log(`[OpenImmo] Scheduled refresh every ${refreshHours}h.`);

export async function getProperties(): Promise<Property[]> {
  if (!propertiesCache) {
    await loadProperties();
  }
  return propertiesCache || [];
}

export async function searchProperties(criteria: {
  location?: string;
  maxPrice?: number;
  minZimmer?: number;
  maxZimmer?: number;
  vermarktungsart?: string;
  objektart?: string;
  softFilters?: string[];
}) {
  const properties = await getProperties();

  return properties
    .filter(p => {
      if (criteria.location) {
        const escaped = criteria.location.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const cityRegex = new RegExp(`(^|[\\s/,;-])${escaped}($|[\\s/,;-])`, 'i');
        if (!cityRegex.test(p.location)) return false;
      }
      if (criteria.maxPrice && p.price > criteria.maxPrice) return false;
      if (criteria.minZimmer && p.anzahl_zimmer < criteria.minZimmer) return false;
      if (criteria.maxZimmer && p.anzahl_zimmer > criteria.maxZimmer) return false;

      if (criteria.vermarktungsart) {
        if (criteria.vermarktungsart.toLowerCase() === 'kauf' && p.vermarktungsart !== 'kauf') return false;
        if (criteria.vermarktungsart.toLowerCase() === 'miete' && !p.vermarktungsart?.includes('miete')) return false;
      }

      if (criteria.objektart) {
        const typesMap: Record<string, string[]> = {
          "wohnung": ["wohnung", "apartment"],
          "haus": ["haus", "villa"],
          "grundstueck": ["grundstueck"],
          "garage_stellplatz": ["parken"],
          "seniorenwohnen": ["seniorenwohnen"],
          "wohnen_auf_zeit": ["wohnen_auf_zeit"],
          "wg_zimmer": ["zimmer"],
          "neubau": ["wohnung", "haus", "neubau"],
          "anlageobjekt": ["zinshaus_renditeobjekt", "anlageobjekt"],
          "zwangsversteigerung": ["zwangsversteigerung"],
          "buero_praxis": ["buero_praxen"],
          "halle_produktion": ["hallen_lager_prod"],
          "einzelhandel": ["einzelhandel"],
          "gastronomie_hotel": ["gastgewerbe"],
          "gewerbegrundstueck": ["gewerbegrundstueck", "grundstueck"],
          "sonstige_wohnen": ["sonstige"],
          "sonstige_gewerbe": ["freizeitimmobilie_gewerblich", "land_und_forstwirtschaft", "sonstige"]
        };

        const requestedType = criteria.objektart.toLowerCase();
        const titleLower = p.title.toLowerCase();
        const pType = p.propertyType.toLowerCase();

        // Title-based matching for garage_stellplatz:
        // Catches listings categorized as "sonstige" whose title indicates parking,
        // but excludes known residential/commercial types that just mention a parking spot.
        if (requestedType === 'garage_stellplatz') {
          const parkingKeywords = ['stellplatz', 'tiefgarage', 'tiefgaragenstellplatz', 'garage', 'carport', 'duplex-stellplatz'];
          const residentialTypes = ['wohnung', 'apartment', 'haus', 'villa', 'buero_praxen', 'einzelhandel',
            'gastgewerbe', 'hallen_lager_prod', 'zinshaus_renditeobjekt', 'zimmer'];
          const hasParkingKeyword = parkingKeywords.some(kw => titleLower.includes(kw));

          if (pType === 'parken') {
            // Direct match — always include
          } else if (hasParkingKeyword && !residentialTypes.includes(pType)) {
            // Title says parking + not a residential/commercial type → include
          } else {
            return false;
          }
        }
        // Title-based matching for seniorenwohnen:
        // Catches flats whose title indicates senior/accessible living.
        else if (requestedType === 'seniorenwohnen') {
          const seniorKeywords = ['altersgerecht', 'seniorengerecht', 'behindertengerecht', 'barrierefrei', 'seniorenwohnen', 'rollstuhl', 'senioren'];
          const flatTypes = ['wohnung', 'apartment', 'seniorenwohnen'];
          const hasSeniorKeyword = seniorKeywords.some(kw => titleLower.includes(kw));

          if (pType === 'seniorenwohnen') {
            // Direct match — always include
          } else if (hasSeniorKeyword && flatTypes.includes(pType)) {
            // Title says senior-accessible + it's a flat → include
          } else {
            return false;
          }
        }
        // WAZ-based matching for wohnen_auf_zeit:
        // Catches wohnungen with nutzungsart WAZ=true (temporary rental).
        else if (requestedType === 'wohnen_auf_zeit') {
          if (pType === 'wohnen_auf_zeit') {
            // Direct match — always include
          } else if (p.wohnenAufZeit && ['wohnung', 'apartment', 'zimmer'].includes(pType)) {
            // WAZ flag set + residential type → include
          } else {
            return false;
          }
        }
        // Title-based matching for wg_zimmer:
        // Catches wohnungen whose title indicates a shared flat (WG).
        else if (requestedType === 'wg_zimmer') {
          const wgKeywords = ['wg', 'wg-zimmer', 'wg zimmer', 'wohngemeinschaft'];
          const wgTypes = ['wohnung', 'apartment', 'zimmer', 'wg_zimmer'];
          const hasWgKeyword = wgKeywords.some(kw => titleLower.includes(kw));

          if (pType === 'zimmer' || pType === 'wg_zimmer') {
            // Direct match — always include
          } else if (hasWgKeyword && wgTypes.includes(pType)) {
            // Title says WG + residential type → include
          } else {
            return false;
          }
        }
        // Title-based matching for neubau:
        // Only matches listings with new-build keywords in the title.
        else if (requestedType === 'neubau') {
          const neubauKeywords = ['neubau', 'rohbau', 'projektiert', 'rohbauhaus', 'erstbezug', 'neubauprojekt'];
          const hasNeubauKeyword = neubauKeywords.some(kw => titleLower.includes(kw));

          if (pType === 'neubau') {
            // Direct match — always include
          } else if (hasNeubauKeyword) {
            // Title indicates new build → include regardless of type
          } else {
            return false;
          }
        }
        // Standard type mapping for everything else
        else {
          const mappedTypes = typesMap[requestedType] || [requestedType];
          if (!mappedTypes.includes(pType)) return false;
        }
      }

      // Soft filter: AND logic – alle genannten Features müssen vorhanden sein
      if (criteria.softFilters && criteria.softFilters.length > 0) {
        const missing = criteria.softFilters.filter(f => !p.softFeatures.includes(f));
        if (missing.length > 0) return false;
      }

      return true;
    })
    .sort((a, b) => {
      // Score-based ranking: properties matching more soft filters rank higher
      if (criteria.softFilters && criteria.softFilters.length > 0) {
        const scoreA = criteria.softFilters.filter(f => a.softFeatures.includes(f)).length;
        const scoreB = criteria.softFilters.filter(f => b.softFeatures.includes(f)).length;
        return scoreB - scoreA;
      }
      return 0;
    });
}

export async function getPropertyById(id: string): Promise<Property | null> {
  const props = await getProperties();
  return props.find(p => p.id === id) || null;
}
