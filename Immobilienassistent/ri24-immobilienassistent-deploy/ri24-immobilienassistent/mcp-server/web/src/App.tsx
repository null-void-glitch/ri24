import { useState } from 'react';
import { MapPin, Search, ChevronRight, Home, Sparkles } from 'lucide-react';
import { useApp } from '@modelcontextprotocol/ext-apps/react';

interface Property {
  id: string;
  title: string;
  location: string;
  price: number;
  anzahl_zimmer: number;
  flaeche: number;
  propertyType: string;
  imageUrl: string;
  url?: string;
  softFeatures?: string[];
}

function App() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);

  // Use the official MCP Apps SDK hook for reliable communication with ChatGPT.
  // This handles the initialization handshake, notification buffering, and
  // reconnection — fixing the issue where a second search in the same chat
  // would get stuck on the loading screen.
  const { isConnected, error } = useApp({
    appInfo: { name: 'real-estate-widget', version: '1.0.0' },
    capabilities: {},
    onAppCreated: (app) => {
      // Recursively search for the properties array in any payload shape
      const findProperties = (obj: any): any[] | null => {
        if (!obj || typeof obj !== 'object') return null;

        if (Array.isArray(obj.properties) && obj.properties.length > 0 && 'price' in obj.properties[0]) {
          return obj.properties;
        }
        if (Array.isArray(obj.properties) && obj.properties.length === 0) {
          return obj.properties;
        }
        if (Array.isArray(obj) && obj.length > 0 && 'price' in obj[0]) {
          return obj;
        }

        for (const key of Object.keys(obj)) {
          const found = findProperties(obj[key]);
          if (found) return found;
        }
        return null;
      };

      // Register tool result handler BEFORE connect (SDK buffers missed notifications)
      app.ontoolresult = (result) => {
        console.log('[Widget] ontoolresult received:', result);

        // structuredContent is the primary source (from _meta.structuredContent)
        const structured = (result as any).structuredContent || (result as any)._meta?.structuredContent;
        if (structured) {
          const found = findProperties(structured);
          if (found) {
            console.log('[Widget] Setting properties from structuredContent:', found.length);
            setProperties(found);
            setLoading(false);
            return;
          }
        }

        // Fallback: search the entire result object (handles content[] payloads etc.)
        const found = findProperties(result);
        if (found) {
          console.log('[Widget] Setting properties from result:', found.length);
          setProperties(found);
          setLoading(false);
          return;
        }

        // Fallback: parse text content for zero-results indicator
        if (result.content) {
          const textItems = (result.content as any[]).filter((c: any) => c.type === 'text');
          const anyZero = textItems.some((c: any) => c.text?.includes('0 Immobilien') || c.text?.includes('Found 0'));
          if (anyZero) {
            setProperties([]);
            setLoading(false);
            return;
          }
        }

        console.warn('[Widget] Could not extract properties from tool result:', result);
      };

      app.ontoolcancelled = (params) => {
        console.log('[Widget] Tool cancelled:', params.reason);
        setLoading(false);
      };

      app.onerror = (err) => {
        console.error('[Widget] App error:', err);
      };
    },
  });

  // Dev-mode fallbacks (standalone or MCP Inspector without the ChatGPT IPC bridge)
  useState(() => {
    const timer = setTimeout(() => {
      if (properties.length > 0) return;

      // Mock data when running standalone (not in an iframe)
      if (window.self === window.top) {
        setProperties([
          {
            id: '1', title: 'Luxury Penthouse with Skyline View', location: 'Manhattan, NY', price: 4500000, anzahl_zimmer: 3, flaeche: 250, propertyType: 'apartment', imageUrl: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&q=80', url: 'https://www.regionalimmobilien24.de/immobilien/expose/?id=1'
          },
          {
            id: '2', title: 'Modern Lakeside Villa', location: 'Lake Tahoe, NV', price: 2850000, anzahl_zimmer: 5, flaeche: 400, propertyType: 'villa', imageUrl: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&q=80', url: 'https://www.regionalimmobilien24.de/immobilien/expose/?id=2'
          },
          {
            id: '3', title: 'Minimalist Smart Home', location: 'Austin, TX', price: 1250000, anzahl_zimmer: 4, flaeche: 180, propertyType: 'house', imageUrl: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800&q=80', url: 'https://www.regionalimmobilien24.de/immobilien/expose/?id=3'
          }
        ]);
        setLoading(false);
        return;
      }

      // Legacy openai bridge injection
      if ((window as any).openai?.toolOutput) {
        const findProperties = (obj: any): any[] | null => {
          if (!obj || typeof obj !== 'object') return null;
          if (Array.isArray(obj.properties) && obj.properties.length > 0 && 'price' in obj.properties[0]) return obj.properties;
          if (Array.isArray(obj) && obj.length > 0 && 'price' in obj[0]) return obj;
          for (const key of Object.keys(obj)) {
            const found = findProperties(obj[key]);
            if (found) return found;
          }
          return null;
        };
        const found = findProperties((window as any).openai.toolOutput);
        if (found) {
          setProperties(found);
          setLoading(false);
          return;
        }
      }

      // MCP Inspector fallback via REST
      fetch('http://localhost:3000/dev/properties')
        .then(res => res.json())
        .then(data => {
          if (data && Array.isArray(data) && data.length > 0) {
            setProperties(data);
            setLoading(false);
          }
        })
        .catch(err => {
          console.log('[Widget] Could not fetch dev properties:', err);
        });
    }, 2500);

    return () => clearTimeout(timer);
  });

  if (error) {
    console.error('[Widget] Connection error:', error);
    // Don't block rendering — fallbacks may still provide data
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-transparent text-slate-800">
        <div className="relative">
          <div className="absolute inset-0 bg-[#BDE04F]/20 blur-xl rounded-full animate-pulse px-8 py-8"></div>
          <div className="glass-panel p-5 rounded-3xl animate-float relative z-10">
            <Search className="w-8 h-8 text-[#98b835] animate-pulse" />
          </div>
        </div>
        <p className="mt-6 text-sm font-semibold text-slate-500 tracking-widest uppercase items-center flex gap-2">
          <Sparkles className="w-4 h-4 text-[#BDE04F]" />
          Lade Immobilien...
        </p>
      </div>
    );
  }

  if (properties.length === 0) {
    return (
      <div className="flex items-center justify-center p-6 bg-transparent">
        <div className="glass-panel rounded-3xl p-10 text-center max-w-sm mx-auto animate-fade-in flex flex-col items-center">
          <div className="w-16 h-16 bg-slate-50 text-slate-300 rounded-2xl flex items-center justify-center mb-5 rotate-3 shadow-inner">
            <Home className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2">Keine Treffer gefunden</h3>
          <p className="text-slate-500 text-sm leading-relaxed">Wir konnten leider keine Immobilien finden, die Ihren genauen Kriterien entsprechen. Bitte passen Sie Ihre Filter an.</p>
        </div>
      </div>
    );
  }

  const propertyTypeMap: Record<string, string> = {
    wohnung: "Wohnung",
    haus: "Haus",
    grundstueck: "Grundstück",
    buero_praxen: "Büro / Praxis",
    einzelhandel: "Einzelhandel",
    gastgewerbe: "Gastronomie",
    hallen_lager_prod: "Halle / Lager",
    land_und_forstwirtschaft: "Land-/Forstwirtschaft",
    parken: "Stellplatz / Garage",
    sonstige: "Sonstige",
    freizeitimmobilie_gewerblich: "Freizeitimmobilie",
    zinshaus_renditeobjekt: "Renditeobjekt",
    zimmer: "Zimmer",
    apartment: "Wohnung",
    villa: "Villa"
  };

  // Feature badge config: key → { label, emoji }
  const featureConfig: Record<string, { label: string; emoji: string }> = {
    balkon: { label: 'Balkon', emoji: '🏡' },
    terrasse: { label: 'Terrasse', emoji: '☀️' },
    garten: { label: 'Garten', emoji: '🌿' },
    aufzug: { label: 'Aufzug', emoji: '⬆️' },
    barrierefrei: { label: 'Barrierefrei', emoji: '♿' },
    gaeste_wc: { label: 'Gäste-WC', emoji: '🚹' },
    einbaukueche: { label: 'Einbauküche', emoji: '🍳' },
    badewanne: { label: 'Badewanne', emoji: '🛀' },
    dusche: { label: 'Dusche', emoji: '🚿' },
    fussbodenheizung: { label: 'Fußbodenheiz.', emoji: '🔥' },
    kamin: { label: 'Kamin', emoji: '🧱' },
    abstellraum: { label: 'Abstellraum', emoji: '🛠️' },
    keller: { label: 'Keller', emoji: '📦' },
    dachboden: { label: 'Dachboden', emoji: '🏠' },
    moebliert: { label: 'Möbliert', emoji: '🛋️' },
    klimaanlage: { label: 'Klimaanlage', emoji: '❄️' },
    stellplatz: { label: 'Stellplatz', emoji: '🚗' },
    garage: { label: 'Garage', emoji: '🏭' },
    tiefgarage: { label: 'Tiefgarage', emoji: '⏬' },
    e_ladestation: { label: 'E-Ladestation', emoji: '⚡' },
    fahrradraum: { label: 'Fahrradraum', emoji: '🚲' },
    haustiere_erlaubt: { label: 'Haustiere', emoji: '🐾' },
    wg_geeignet: { label: 'WG-geeignet', emoji: '👥' },
    familienfreundlich: { label: 'Familienfreundl.', emoji: '👨‍👩‍👧' },
    seniorenfreundlich: { label: 'Seniorenfreundl.', emoji: '👴' },
    ruhige_lage: { label: 'Ruhige Lage', emoji: '🧘' },
    zentrale_lage: { label: 'Zentrale Lage', emoji: '🏙️' },
    naturnahe_lage: { label: 'Naturnahe Lage', emoji: '🌲' },
    suedausrichtung: { label: 'Südausrichtung', emoji: '☀️' },
    erdgeschoss: { label: 'Erdgeschoss', emoji: '📍' },
    dachgeschoss: { label: 'Dachgeschoss', emoji: '🏠' },
    neubau: { label: 'Neubau', emoji: '🏗️' },
    altbau: { label: 'Altbau', emoji: '🏛️' },
    modernisiert: { label: 'Modernisiert', emoji: '✨' },
    energieeffizient: { label: 'Energieeffizient', emoji: '🌿' },
    provisionsfrei: { label: 'Provisionsfrei', emoji: '✅' },
    oeffentlicher_nv: { label: 'ÖPNV-Anbindung', emoji: '🚌' },
    nahe_bahnhof: { label: 'Nahe Bahnhof', emoji: '🚂' },
    einkauf_nah: { label: 'Einkauf', emoji: '🛍️' },
    schule_nah: { label: 'Schule', emoji: '🏫' },
    kindergarten_nah: { label: 'Kindergarten', emoji: '👶' },
    park_nah: { label: 'Park', emoji: '🌳' },
    spielplatz_nah: { label: 'Spielplatz', emoji: '🏗️' },
  };

  return (
    <div className="w-full p-2 py-4 bg-transparent font-sans overflow-visible">
      <div className="flex overflow-x-auto snap-x snap-mandatory custom-scrollbar gap-5 pb-6 px-2 pt-2 items-stretch">
        {properties.map((property, idx) => (
          <div
            key={property.id}
            className="flex-none w-[320px] snap-start glass-panel rounded-[2rem] overflow-hidden group hover:-translate-y-2 transition-all duration-500 ease-out animate-fade-in relative"
            style={{ animationDelay: `${idx * 100}ms` }}
          >
            {/* Image Section */}
            <div className="relative h-56 m-2 mb-0 rounded-t-[1.5rem] rounded-b-xl overflow-hidden mask-image">
              <div className="absolute inset-0 bg-slate-900/10 group-hover:bg-transparent z-10 transition-colors duration-500"></div>
              <img
                src={property.imageUrl}
                alt={property.title}
                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 ease-out"
                loading="lazy"
              />

              {/* Floating Badges */}
              <div className="absolute top-3 left-3 z-20 flex gap-2">
                <span className="px-3 py-1.5 glass-panel text-slate-800 text-xs font-bold rounded-full capitalize tracking-wider shadow-md backdrop-blur-md">
                  {propertyTypeMap[property.propertyType] || property.propertyType}
                </span>
              </div>
              <div className="absolute bottom-3 right-3 z-20">
                <span className="px-3 py-1.5 bg-slate-900/80 backdrop-blur-md text-white/90 text-xs font-semibold rounded-full shadow-lg flex items-center gap-1.5 border border-white/10">
                  {['grundstueck', 'parken', 'gewerbegrundstueck'].includes(property.propertyType.toLowerCase()) || property.anzahl_zimmer === 0
                    ? (property.flaeche > 0 ? `${property.flaeche.toLocaleString("de-DE")} m²` : "Fläche a.A.")
                    : `${property.anzahl_zimmer} Zimmer`}
                </span>
              </div>
            </div>

            {/* Content Section */}
            <div className="p-6 pt-5 flex flex-col">
              <div className="flex items-center gap-1.5 text-slate-500 text-xs font-bold mb-3 uppercase tracking-widest pl-0.5">
                <MapPin className="w-3.5 h-3.5 text-[#BDE04F]" />
                <span className="truncate">{property.location}</span>
              </div>

              <h3 className="text-[20px] font-extrabold text-slate-800 leading-[1.2] mb-3 line-clamp-2 h-[48px] group-hover:text-[#98b835] transition-colors">
                {property.title}
              </h3>

              {/* Soft Feature Badges — fixed height for uniform cards */}
              <div className="flex flex-wrap gap-1.5 mb-4 h-[52px] overflow-hidden content-start items-start">
                {(property.softFeatures || []).slice(0, 5).map(f => {
                  const cfg = featureConfig[f];
                  if (!cfg) return null;
                  return (
                    <span
                      key={f}
                      title={cfg.label}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600 border border-slate-200"
                    >
                      <span>{cfg.emoji}</span>
                      <span>{cfg.label}</span>
                    </span>
                  );
                })}
                {(property.softFeatures || []).length > 5 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#BDE04F]/20 text-[#6e8f20] border border-[#BDE04F]/40">
                    +{property.softFeatures!.length - 5}
                  </span>
                )}
              </div>

              <div className="flex items-end justify-between mt-auto pt-2">
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-0.5 ml-0.5">Preis</p>
                  <p className={property.price === 0 ? "text-[16px] font-black text-slate-700 tracking-tight mt-1" : "text-2xl font-black text-slate-900 tracking-tight"}>
                    {property.price === 0 ? "Preis auf Anfrage" : `${property.price.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`}
                  </p>
                </div>

                <button
                  onClick={() => property.url && window.open(property.url, "_blank", "noopener,noreferrer")}
                  className="w-12 h-12 bg-[#BDE04F] hover:bg-[#a8cf38] text-slate-900 rounded-2xl flex items-center justify-center shadow-xl shadow-[#BDE04F]/20 group-hover:shadow-[#BDE04F]/40 group-hover:-rotate-6 transition-all duration-300"
                >
                  <ChevronRight className="w-6 h-6" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
