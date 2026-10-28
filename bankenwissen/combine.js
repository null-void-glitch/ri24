const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(__dirname, 'output');
const COMBINED_DIR = path.join(__dirname, 'combined');

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function cleanCategory(cat) {
  return cat
    .replace(/^v/, '')
    .replace(/^Kriterian?\s+/i, '')
    .trim();
}

// Identify Förderbanken by name
const FOERDER_KEYS = ['kfw', 'förder', 'l-bank', 'lfa', 'sächsische aufbaubank', 'nrw.bank'];
function isForederbank(name) {
  const n = name.toLowerCase();
  return FOERDER_KEYS.some(k => n.includes(k));
}

// Identify VR banks by name (for banks without company pages)
const VR_KEYS = ['volksbank', 'raiffeisenbank', 'raiffeisen ', 'genossenschaftsbank', 'voba ', 'vrbank'];
function isVRBank(name) {
  const n = name.toLowerCase();
  return VR_KEYS.some(k => n.includes(k));
}

function main() {
  ensureDir(COMBINED_DIR);

  // ── Load company metadata ─────────────────────────────────────────────────
  const companyDir = path.join(OUTPUT_DIR, 'companies');
  const companyByName = {};     // bankName → company data
  const companyByCategory = {}; // category → [company data]

  for (const file of fs.readdirSync(companyDir)) {
    const d = JSON.parse(fs.readFileSync(path.join(companyDir, file)));
    if (!d.bank_name) continue;
    companyByName[d.bank_name] = d;
    const cat = d.category || 'unknown';
    if (!companyByCategory[cat]) companyByCategory[cat] = [];
    companyByCategory[cat].push(d);
  }

  // ── Load all bank pivot files ─────────────────────────────────────────────
  const banksDir = path.join(OUTPUT_DIR, 'banks');
  const allBankData = {}; // bankName → bank pivot data

  for (const file of fs.readdirSync(banksDir)) {
    const d = JSON.parse(fs.readFileSync(path.join(banksDir, file)));
    if (d.bank) allBankData[d.bank] = d;
  }

  // ── Helper: build bank entry from pivot + company data ────────────────────
  function buildBankEntry(bankName) {
    const pivot = allBankData[bankName] || {};
    const company = companyByName[bankName] || {};

    const cleanCriteria = {};
    for (const [id, crit] of Object.entries(pivot.criteria || {})) {
      if (crit.value && crit.value.trim()) {
        cleanCriteria[id] = {
          name: crit.name,
          category: cleanCategory(crit.category || ''),
          value: crit.value,
        };
      }
    }

    return {
      company_id: pivot.company_id || company.company_id || null,
      last_modified: pivot.last_modified || company.last_modified || null,
      recent_news: pivot.recent_news || company.recent_news || [],
      criteria: cleanCriteria,
    };
  }

  // ── Helper: build company-only entry (no Baufinanzierung criteria) ────────
  function buildCompanyEntry(companyData) {
    return {
      company_id: companyData.company_id || null,
      last_modified: companyData.last_modified || null,
      recent_news: companyData.recent_news || [],
      note: 'Produktspezifische Kriterien sind im Partnerportal abrufbar.',
    };
  }

  // ── 1. KRITERIEN ─────────────────────────────────────────────────────────
  const criteriaDir = path.join(OUTPUT_DIR, 'criteria');
  const kriterien = {};

  for (const file of fs.readdirSync(criteriaDir).sort()) {
    const data = JSON.parse(fs.readFileSync(path.join(criteriaDir, file)));
    const cat = cleanCategory(data.category);
    if (!kriterien[cat]) kriterien[cat] = {};

    const banksMap = {};
    for (const { bank, value } of data.banks) {
      if (value && value.trim()) banksMap[bank] = value;
    }

    kriterien[cat][data.criterion_id] = {
      name: data.criterion_name,
      banks: banksMap,
    };
  }

  fs.writeFileSync(
    path.join(COMBINED_DIR, 'kriterien.json'),
    JSON.stringify({ generated_at: new Date().toISOString(), kriterien }, null, 2)
  );
  console.log('Written: kriterien.json');

  // ── 2. BAUFINANZIERUNG BANK GROUPS ────────────────────────────────────────
  const groups = {
    'baufinanzierung-ueberregionale-banken': {},
    'baufinanzierung-psd-banken': {},
    'baufinanzierung-sparkassen': {},
    'baufinanzierung-volks-und-raiffeisenbanken': {},
    'baufinanzierung-sparda-banken': {},
    'baufinanzierung-foerderbanken': {},
  };

  // Banks WITH company pages → use company category to group
  for (const [bankName, pivot] of Object.entries(allBankData)) {
    const company = companyByName[bankName];
    const cat = pivot.bank_category || company?.category || '';

    // Förderbanken override (regardless of listed category)
    if (isForederbank(bankName)) {
      groups['baufinanzierung-foerderbanken'][bankName] = buildBankEntry(bankName);
      continue;
    }

    if (cat === 'Überregionale Anbieter') {
      groups['baufinanzierung-ueberregionale-banken'][bankName] = buildBankEntry(bankName);
    } else if (cat === 'PSD - Banken') {
      groups['baufinanzierung-psd-banken'][bankName] = buildBankEntry(bankName);
    } else if (cat === 'Sparkassen') {
      groups['baufinanzierung-sparkassen'][bankName] = buildBankEntry(bankName);
    } else if (cat === 'Volks- und Raiffeisenbanken') {
      // Only non-Förderbanken land here (Förderbanken already captured above)
      groups['baufinanzierung-volks-und-raiffeisenbanken'][bankName] = buildBankEntry(bankName);
    } else if (cat === 'Sparda - Banken') {
      groups['baufinanzierung-sparda-banken'][bankName] = buildBankEntry(bankName);
    } else if (!cat || cat === 'unknown') {
      // Banks from criterion pages WITHOUT company pages → classify by name
      if (isVRBank(bankName)) {
        groups['baufinanzierung-volks-und-raiffeisenbanken'][bankName] = buildBankEntry(bankName);
      }
      // Sparkassen without company pages should already have company pages in our data,
      // so we don't need to name-match them here.
    }
  }

  // Add Förderbank company entries that didn't appear on criterion pages (from any category)
  for (const comp of Object.values(companyByName)) {
    if (isForederbank(comp.bank_name) && !groups['baufinanzierung-foerderbanken'][comp.bank_name]) {
      // Merge with any partial pivot data if available
      const pivot = allBankData[comp.bank_name];
      groups['baufinanzierung-foerderbanken'][comp.bank_name] = pivot
        ? buildBankEntry(comp.bank_name)
        : buildCompanyEntry(comp);
    }
  }

  // ── 3. BAUSPAREN ─────────────────────────────────────────────────────────
  const bausparenBanks = {};
  for (const comp of (companyByCategory['Kriterien Bausparen und Bausparkassen'] || [])) {
    bausparenBanks[comp.bank_name] = buildCompanyEntry(comp);
  }

  // ── 4. RATENKREDITE ───────────────────────────────────────────────────────
  const ratenkrediteBanks = {};
  for (const comp of (companyByCategory['Kriterien Ratenkredite'] || [])) {
    ratenkrediteBanks[comp.bank_name] = buildCompanyEntry(comp);
  }

  // ── Write all bank group files ─────────────────────────────────────────────
  const allGroupData = [
    ...Object.entries(groups).map(([name, data]) => ({ name, data })),
    { name: 'bausparen', data: bausparenBanks },
    { name: 'ratenkredite', data: ratenkrediteBanks },
  ];

  const fileMeta = [];
  let totalBanks = 0;

  for (const { name, data } of allGroupData) {
    const count = Object.keys(data).length;
    const output = {
      generated_at: new Date().toISOString(),
      bank_count: count,
      banks: data,
    };
    const filename = name + '.json';
    fs.writeFileSync(path.join(COMBINED_DIR, filename), JSON.stringify(output, null, 2));
    console.log(`Written: ${filename} (${count} banks)`);
    totalBanks += count;

    fileMeta.push({ name, filename, count });
  }

  // ── 5. INDEX ──────────────────────────────────────────────────────────────
  const criteriaCount = Object.values(kriterien)
    .reduce((s, cat) => s + Object.keys(cat).length, 0);

  const labelMap = {
    'baufinanzierung-ueberregionale-banken': 'Baufinanzierung – Überregionale Anbieter',
    'baufinanzierung-psd-banken': 'Baufinanzierung – PSD-Banken',
    'baufinanzierung-sparkassen': 'Baufinanzierung – Sparkassen',
    'baufinanzierung-volks-und-raiffeisenbanken': 'Baufinanzierung – Volks- und Raiffeisenbanken',
    'baufinanzierung-sparda-banken': 'Baufinanzierung – Sparda-Banken',
    'baufinanzierung-foerderbanken': 'Baufinanzierung – Förderbanken',
    'bausparen': 'Bausparen und Bausparkassen',
    'ratenkredite': 'Ratenkredite',
  };

  const descMap = {
    'baufinanzierung-ueberregionale-banken': 'Überregionale Baufinanzierungsanbieter mit allen Kriterien',
    'baufinanzierung-psd-banken': 'PSD-Banken mit Baufinanzierungskriterien',
    'baufinanzierung-sparkassen': 'Sparkassen mit Baufinanzierungskriterien',
    'baufinanzierung-volks-und-raiffeisenbanken': 'Volksbanken und Raiffeisenbanken mit Baufinanzierungskriterien',
    'baufinanzierung-sparda-banken': 'Sparda-Banken mit Baufinanzierungskriterien',
    'baufinanzierung-foerderbanken': 'Förderbanken (KfW, L-Bank, NRW.Bank, Sächsische Aufbaubank)',
    'bausparen': 'Bausparkassen – Metadaten und aktuelle Neuigkeiten',
    'ratenkredite': 'Ratenkreditanbieter – Metadaten und aktuelle Neuigkeiten',
  };

  const indexFiles = [
    {
      file: 'kriterien.json',
      label: 'Kriterien',
      description: 'Alle 132 Baufinanzierungskriterien mit Werten aller Bankpartner, gruppiert nach Kategorie',
      criterion_count: criteriaCount,
      categories: Object.keys(kriterien),
    },
    ...fileMeta.map(({ name, filename, count }) => {
      // Get bank names for the index
      const filePath = path.join(COMBINED_DIR, filename);
      const fileData = JSON.parse(fs.readFileSync(filePath));
      return {
        file: filename,
        label: labelMap[name] || name,
        description: descMap[name] || '',
        bank_count: count,
        banks: Object.keys(fileData.banks).sort(),
      };
    }),
  ];

  const index = {
    generated_at: new Date().toISOString(),
    description: 'Baufinanzierungs- und Bankkriterien – Qualitypool Partnerportal',
    data_source: 'https://partnerportal.qualitypool.de',
    total_files: indexFiles.length,
    total_criteria: criteriaCount,
    total_banks: totalBanks,
    usage_note: 'kriterien.json enthält alle Kriterien im Quervergleich. Die Bankgruppen-Dateien enthalten alle Kriterien je Bank im Einzelprofil.',
    files: indexFiles,
  };

  fs.writeFileSync(path.join(COMBINED_DIR, 'index.json'), JSON.stringify(index, null, 2));
  console.log('\nWritten: index.json');
  console.log(`\nTotal: 10 files (1 Kriterien + 8 Bankgruppen + 1 Index)`);
  console.log(`Total banks: ${totalBanks}`);
}

main();
