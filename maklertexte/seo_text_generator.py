"""Generiert den SEO-Text + FAQ für die Makler-Landingpage (immobilienportal-partner-werden)
regional angepasst über OpenAI GPT-4o."""

from __future__ import annotations

from openai import OpenAI

MODEL = "gpt-4o"

SYSTEM_PROMPT = (
    "Du bist ein SEO-Texter für das regionale Immobilienportal Regionalimmobilien24. "
    "Du erhältst einen HTML-Artikel mit SEO-Text und FAQ-Bereich und erstellst "
    "eine regional angepasste Version für eine bestimmte Region in Deutschland. "
    "\n\nRegeln:\n"
    "- Behalte die EXAKTE HTML-Struktur bei: alle Tags, Attribute, CSS-Klassen "
    "(faq-section, faq-item), &nbsp;-Leerzeilen zwischen Absätzen, <ul>-Listen.\n"
    "- Integriere den Regionsnamen mehrfach (mindestens 6×) natürlich in den Text — "
    "in Überschriften, Absätzen und FAQ-Antworten.\n"
    "- Passe Stadtbeispiele, regionale Bezüge und lokale Formulierungen an die "
    "Zielregion an (z. B. 'in der Region [Region]', 'im Raum [Region]', "
    "'Makler in [Region]').\n"
    "- Behalte Inhalt, Struktur und Länge der FAQ-Fragen bei; passe Antworten "
    "nur dort regional an, wo es sinnvoll ist.\n"
    "- Schreibe ausschließlich auf Deutsch.\n"
    "- Gib NUR den HTML-Code aus — keine Markdown-Codeblöcke, keine Erläuterungen.\n"
    "- Beginne direkt mit <article> und ende mit </article>."
)

USER_PROMPT_TEMPLATE = (
    'Erstelle eine regional angepasste Version des folgenden HTML-Textes '
    'für die Region "{region_name}".\n\n'
    'PFLICHT-ANFORDERUNGEN (nicht verhandelbar):\n'
    '1. "{region_name}" MUSS mindestens 8× im Text vorkommen — prüfe das vor der Ausgabe\n'
    '2. Die erste <h2>-Überschrift MUSS "{region_name}" enthalten\n'
    '3. Mindestens 3 weitere <h2>-Überschriften sollen "{region_name}" nennen\n'
    '4. In der FAQ-Sektion: mindestens 4 Antworten sollen "{region_name}" erwähnen\n'
    '5. Formulierungen wie "in der Region", "im Raum", "für {region_name}", '
    '"Makler in {region_name}" müssen natürlich im Text erscheinen\n'
    '6. Behalte die exakte HTML-Struktur (alle Tags, Klassen, &nbsp;-Zeilen) komplett bei\n'
    '7. Gib NUR den HTML-Code aus, beginnend mit <article>, ohne Kommentare\n\n'
    'VORLAGE:\n{template_html}'
)

# Vollständige Vorlage aus dem Vatermodell (Element 56gbzo), dient als Strukturreferenz.
TEMPLATE_HTML = """\
<article>
<h2>Immobilienportal für Makler und gewerbliche Immobilienanbieter</h2>

<p>Sie sind <strong>Immobilienmakler, Hausverwalter, Bauträger oder gewerblicher Immobilienanbieter</strong> und möchten Ihre Immobilienangebote online sichtbar machen? Mit Regionalimmobilien24 präsentieren Sie Ihre Objekte auf einem Immobilienportal mit konsequent regionaler Ausrichtung und erreichen Interessenten dort, wo die Immobiliensuche beginnt: in ihrer Stadt und Region.</p>
&nbsp;

<p>Ob <strong>Haus zum Kauf, Eigentumswohnung, Mietwohnung, Grundstück, Anlageimmobilie oder Gewerbeobjekt</strong> &ndash; bei Regionalimmobilien24 können Sie Immobilienangebote professionell veröffentlichen und potenzielle Käufer sowie Mieter gezielt ansprechen.</p>
&nbsp;

<p>Wählen Sie einfach das zu Ihrem Immobilienbestand passende Paket und nutzen Sie Regionalimmobilien24 als zusätzlichen digitalen Vertriebskanal für Ihre Immobilienvermarktung.</p>
&nbsp;

<h2>Immobilien inserieren &ndash; für Kauf und Miete</h2>

<p>Eine erfolgreiche Immobilienvermarktung beginnt mit der richtigen Reichweite. Kaufinteressenten und Mieter suchen heute überwiegend online nach passenden Angeboten und erwarten aktuelle Immobilienanzeigen mit allen relevanten Informationen auf einen Blick.</p>
&nbsp;

<p>Regionalimmobilien24 bietet gewerblichen Anbietern die Möglichkeit, unterschiedlichste Immobilien zu veröffentlichen. Dazu zählen beispielsweise:</p>
&nbsp;

<ul>
	<li>Häuser zum Kauf und zur Miete</li>
	<li>Eigentumswohnungen</li>
	<li>Mietwohnungen</li>
	<li>Grundstücke und Baugrundstücke</li>
	<li>Mehrfamilienhäuser und Anlageimmobilien</li>
	<li>Neubauimmobilien</li>
	<li>Gewerbeimmobilien</li>
	<li>Büro-, Praxis- und Ladenflächen</li>
	<li>Hallen und weitere gewerblich genutzte Objekte</li>
</ul>
&nbsp;

<p>Damit eignet sich Regionalimmobilien24 sowohl für Makler mit einem breit gefächerten Immobilienportfolio als auch für Anbieter, die sich auf bestimmte Objektarten oder regionale Märkte spezialisiert haben.</p>
&nbsp;

<h2>Das Immobilienportal mit regionalem Fokus</h2>

<p>Immobilien sind lokal. Wer ein Haus kaufen, eine Wohnung mieten oder eine Kapitalanlage erwerben möchte, sucht in der Regel sehr gezielt in bestimmten Städten, Gemeinden und Regionen.</p>
&nbsp;

<p>Genau hier setzt <strong>Regionalimmobilien24</strong> an.</p>
&nbsp;

<p>Durch unsere regionale Struktur werden Immobilienangebote passend zu ihrem Standort präsentiert. So treffen Anbieter auf Interessenten, die sich konkret für Immobilien in der jeweiligen Region interessieren.</p>
&nbsp;

<p>Für Immobilienmakler und andere gewerbliche Anbieter bedeutet das: Ihre Objekte werden nicht nur veröffentlicht, sondern in einem thematisch und geografisch passenden Umfeld präsentiert.</p>
&nbsp;

<p>Das macht Regionalimmobilien24 zu einer interessanten Ergänzung Ihrer bestehenden Online-Vermarktung.</p>
&nbsp;

<h2>Passende Veröffentlichungspakete für Immobilienprofis</h2>

<p>Nicht jedes Immobilienunternehmen hat die gleichen Anforderungen. Ein regional tätiger Makler mit wenigen gleichzeitig verfügbaren Objekten benötigt eine andere Lösung als ein Unternehmen mit einem umfangreichen und regelmäßig wechselnden Immobilienbestand.</p>
&nbsp;

<p>Deshalb bietet Regionalimmobilien24 verschiedene <strong>Pakete zur Veröffentlichung von Immobilien</strong>.</p>
&nbsp;

<p>So können Sie die Lösung auswählen, die am besten zu Ihrem Unternehmen und der Anzahl Ihrer Immobilienangebote passt.</p>
&nbsp;

<p>Egal, ob Sie einzelne Objekte vermarkten oder kontinuierlich zahlreiche Immobilien inserieren: Unsere Pakete ermöglichen Ihnen eine flexible Nutzung des Portals.</p>
&nbsp;

<p><strong>Vergleichen Sie jetzt die verfügbaren Möglichkeiten und wählen Sie das für Sie passende Paket.</strong></p>
&nbsp;

<h2>Mietobjekte professionell veröffentlichen</h2>

<p>Gerade bei Mietimmobilien ist Geschwindigkeit wichtig. Wohnungen, Häuser und Gewerbeflächen sollen möglichst schnell passende Interessenten erreichen und Leerstandszeiten reduziert werden.</p>
&nbsp;

<p>Über Regionalimmobilien24 können Sie Ihre <strong>Mietobjekte online inserieren</strong> und übersichtlich präsentieren.</p>
&nbsp;

<p>Interessenten können gezielt nach Immobilien zur Miete in ihrer gewünschten Region suchen und passende Angebote entdecken.</p>
&nbsp;

<p>So eignet sich das Portal beispielsweise für:</p>
&nbsp;

<ul>
	<li>Immobilienmakler</li>
	<li>Hausverwaltungen</li>
	<li>Wohnungsunternehmen</li>
	<li>Bestandshalter</li>
	<li>Projektentwickler</li>
	<li>gewerbliche Vermieter</li>
</ul>
&nbsp;

<p>Von der einzelnen Mietwohnung bis zum größeren Immobilienbestand können aktuelle Angebote für potenzielle Mieter sichtbar gemacht werden.</p>
&nbsp;

<h2>Kaufimmobilien gezielt vermarkten</h2>

<p>Auch Verkäufer und Makler von Kaufimmobilien profitieren von einer zusätzlichen Präsenz im Internet.</p>
&nbsp;

<p>Wer ein Haus, eine Eigentumswohnung, ein Grundstück oder eine Anlageimmobilie verkaufen möchte, benötigt möglichst viele relevante Kontaktpunkte zu potenziellen Käufern.</p>
&nbsp;

<p>Mit einer Veröffentlichung auf Regionalimmobilien24 ergänzen Sie Ihre digitale Immobilienvermarktung um einen weiteren Vertriebskanal.</p>
&nbsp;

<p>Präsentieren Sie beispielsweise:</p>
&nbsp;

<ul>
	<li>Einfamilienhäuser</li>
	<li>Doppel- und Reihenhäuser</li>
	<li>Eigentumswohnungen</li>
	<li>Mehrfamilienhäuser</li>
	<li>Grundstücke</li>
	<li>Neubauprojekte</li>
	<li>Renditeobjekte</li>
	<li>Gewerbeimmobilien</li>
</ul>
&nbsp;

<p>und machen Sie Ihre Immobilienangebote für Kaufinteressenten aus der jeweiligen Region auffindbar.</p>
&nbsp;

<h2>Mehr Sichtbarkeit für Ihr Immobilienunternehmen</h2>

<p>Eine professionelle Immobilienpräsentation dient nicht nur der Vermarktung einzelner Objekte. Sie stärkt gleichzeitig die Sichtbarkeit Ihres Unternehmens.</p>
&nbsp;

<p>Interessenten lernen Ihr Immobilienangebot und Ihr Unternehmen kennen und können direkt Kontakt aufnehmen.</p>
&nbsp;

<p>Gerade für regional tätige Immobilienmakler ist diese Präsenz besonders interessant: Wer regelmäßig Immobilien in einer bestimmten Stadt oder Region anbietet, kann sich dort als Ansprechpartner für den lokalen Immobilienmarkt positionieren.</p>
&nbsp;

<p>Regionalimmobilien24 verbindet somit <strong>Immobilienvermarktung mit regionaler Sichtbarkeit</strong>.</p>
&nbsp;

<h2>Immobilienangebote einfach online präsentieren</h2>

<p>Eine zusätzliche Immobilienplattform sollte vor allem eines sein: unkompliziert.</p>
&nbsp;

<p>Deshalb richtet sich Regionalimmobilien24 an professionelle Immobilienanbieter, die ihre Objekte effizient online präsentieren und ihre bestehende Vermarktung sinnvoll ergänzen möchten.</p>
&nbsp;

<p>Ob Kauf oder Miete, Wohnimmobilie oder Gewerbeobjekt &ndash; Sie entscheiden, welche Immobilien Sie veröffentlichen und welches Paket zu Ihrem Bedarf passt.</p>
&nbsp;

<p>So können Sie Ihre verfügbaren Immobilienangebote einem weiteren Kreis potenzieller Interessenten präsentieren.</p>
&nbsp;

<h2>Für wen eignet sich Regionalimmobilien24?</h2>

<p>Unser Angebot richtet sich insbesondere an gewerbliche Immobilienanbieter wie:</p>
&nbsp;

<ul>
	<li>Immobilienmakler und Maklerbüros</li>
	<li>Haus- und Immobilienverwaltungen</li>
	<li>Wohnungsunternehmen</li>
	<li>Bauträger</li>
	<li>Projektentwickler</li>
	<li>Bestandshalter</li>
	<li>gewerbliche Vermieter</li>
	<li>Anbieter von Anlage- und Gewerbeimmobilien</li>
</ul>
&nbsp;

<p>Ganz gleich, ob Ihr Schwerpunkt auf dem <strong>Verkauf von Immobilien</strong>, der <strong>Vermietung von Wohnungen und Häusern</strong> oder auf einer Kombination aus Kauf- und Mietangeboten liegt: Regionalimmobilien24 bietet Ihnen eine Plattform zur zusätzlichen Online-Vermarktung Ihrer Objekte.</p>
&nbsp;

<h2>Jetzt Partner von Regionalimmobilien24 werden</h2>

<p>Erweitern Sie Ihre Immobilienvermarktung und präsentieren Sie Ihre Miet- und Kaufobjekte auf Regionalimmobilien24.</p>
&nbsp;

<p>Wählen Sie jetzt das passende Veröffentlichungspaket für Ihr Unternehmen und machen Sie Ihre Immobilienangebote für Interessenten in der jeweiligen Region sichtbar.</p>
&nbsp;

<p><strong>Jetzt Paket auswählen und Immobilien auf Regionalimmobilien24 veröffentlichen.</strong></p>
&nbsp;

<section class="faq-section">
<h2>Häufige Fragen für Immobilienmakler und gewerbliche Immobilienanbieter</h2>

<p>Sie möchten Ihre Immobilien auf Regionalimmobilien24 veröffentlichen? Hier finden Sie Antworten auf häufige Fragen zu unseren Immobilienpaketen, der Veröffentlichung von Kauf- und Mietobjekten sowie zu den Leistungen für Makler und gewerbliche Immobilienanbieter.</p>
&nbsp;

<div class="faq-item">
<h3>1. Welche Immobilienpakete bietet Regionalimmobilien24 für Makler und gewerbliche Anbieter an?</h3>

<p>Regionalimmobilien24 bietet mit <strong>Basic, Plus und Premium</strong> verschiedene Pakete für professionelle Immobilienanbieter an. Bereits das Basic-Paket ermöglicht die Veröffentlichung einer unbegrenzten Anzahl von Immobilien. Die Pakete Plus und Premium ergänzen die Immobilienvermarktung um weitere Funktionen für mehr Sichtbarkeit, Reichweite und Unterstützung bei der Akquise.</p>
</div>
&nbsp;

<div class="faq-item">
<h3>2. Wie viele Immobilien kann ich bei Regionalimmobilien24 gleichzeitig veröffentlichen?</h3>

<p>Bei Regionalimmobilien24 können Sie <strong>unbegrenzt viele Immobilien veröffentlichen</strong>. Damit eignet sich das Portal sowohl für kleinere Maklerbüros als auch für Immobilienunternehmen, Hausverwaltungen und andere gewerbliche Anbieter mit einem umfangreichen oder regelmäßig wechselnden Immobilienbestand.</p>
</div>
&nbsp;

<div class="faq-item">
<h3>3. Kann ich sowohl Kaufimmobilien als auch Mietimmobilien inserieren?</h3>

<p>Ja. Sie können auf Regionalimmobilien24 sowohl <strong>Immobilien zum Kauf als auch Immobilien zur Miete</strong> veröffentlichen. Damit können Sie beispielsweise Eigentumswohnungen, Einfamilienhäuser und Grundstücke ebenso vermarkten wie Mietwohnungen, Mietshäuser oder gewerbliche Mietflächen.</p>
</div>
&nbsp;

<div class="faq-item">
<h3>4. Welche Immobilienarten kann ich auf Regionalimmobilien24 anbieten?</h3>

<p>Regionalimmobilien24 ist für die Vermarktung unterschiedlichster Wohn- und Gewerbeimmobilien geeignet. Dazu gehören beispielsweise <strong>Häuser, Wohnungen, Grundstücke, Neubauimmobilien, Anlageobjekte sowie Büro-, Praxis-, Einzelhandels-, Hallen- und Gewerbeimmobilien</strong>. Sowohl Kauf- als auch Mietangebote können über das Portal veröffentlicht werden.</p>
</div>
&nbsp;

<div class="faq-item">
<h3>5. Kann ich meine Maklersoftware mit Regionalimmobilien24 verbinden?</h3>

<p>Ja. Regionalimmobilien24 unterstützt die <strong>Anbindung gängiger Maklersoftware</strong>. Dadurch können Immobilienangebote komfortabel aus Ihrer bestehenden Software heraus an das Portal übertragen werden. Das erleichtert insbesondere Maklern mit mehreren gleichzeitig verfügbaren Objekten die laufende Pflege ihrer Immobilienanzeigen.</p>
</div>
&nbsp;

<div class="faq-item">
<h3>6. Kann ich Immobilien auch ohne Maklersoftware direkt verwalten?</h3>

<p>Ja. Wenn Sie keine Maklersoftware einsetzen, können Sie Ihre Immobilienangebote auch über die <strong>Direktverwaltung von Regionalimmobilien24</strong> verwalten. Damit können auch kleinere Maklerbüros, gewerbliche Vermieter oder andere Immobilienanbieter ihre Kauf- und Mietobjekte auf dem Portal präsentieren.</p>
</div>
&nbsp;

<div class="faq-item">
<h3>7. Wie viele Bilder kann ich pro Immobilienanzeige veröffentlichen?</h3>

<p>Pro Immobilienanzeige können Sie <strong>bis zu 50 Bilder</strong> veröffentlichen. Darüber hinaus unterstützt Regionalimmobilien24 auch 360&deg;-Bilder und virtuelle Touren. So können Interessenten bereits online einen umfassenden Eindruck von der angebotenen Immobilie erhalten.</p>
</div>
&nbsp;

<div class="faq-item">
<h3>8. Ist das Basic-Paket von Regionalimmobilien24 kostenlos?</h3>

<p>Ja. Das <strong>Immobilienpaket Basic ist dauerhaft kostenfrei</strong>. Es ermöglicht unter anderem die unbegrenzte Veröffentlichung von Immobilien, die Nutzung gängiger Maklersoftware beziehungsweise der Direktverwaltung sowie die Darstellung von bis zu 50 Bildern je Anzeige. Damit können Immobilienanbieter Regionalimmobilien24 als zusätzlichen Vermarktungskanal nutzen, ohne monatliche Kosten für das Basic-Paket.</p>
</div>
&nbsp;

<div class="faq-item">
<h3>9. Was ist der Unterschied zwischen Basic, Plus und Premium?</h3>

<p>Das <strong>Basic-Paket</strong> bietet bereits die wesentlichen Funktionen zur Veröffentlichung Ihrer Immobilien. Mit dem <strong>Plus-Paket</strong> kommen zusätzliche Leistungen wie die Darstellung Ihres Firmenlogos, eine eigene Kunden-Webapp mit Empfehlungsmanagement sowie die zusätzliche Veröffentlichung von Inseraten auf Partnerseiten hinzu.</p>
&nbsp;

<p>Das <strong>Premium-Paket</strong> erweitert diese Leistungen unter anderem um eine bevorzugte Darstellung und regelmäßige Hervorhebung von Objekten in der Ergebnisliste, einen Immobilienassistenten zur Einbindung auf der eigenen Webseite, Zugang zu weiteren Netzwerk- und Partnervorteilen sowie zusätzliche Möglichkeiten zur Zuführung von Verkaufs- und Vermietungsobjekten.</p>
</div>
&nbsp;

<div class="faq-item">
<h3>10. Für welche gewerblichen Immobilienanbieter eignet sich Regionalimmobilien24?</h3>

<p>Regionalimmobilien24 eignet sich für <strong>Immobilienmakler, Maklerbüros, Hausverwaltungen, Wohnungsunternehmen, Bauträger, Projektentwickler, Bestandshalter und gewerbliche Vermieter</strong>. Das Portal kann sowohl für die Vermarktung einzelner Immobilien als auch für größere Immobilienbestände genutzt werden und unterstützt gleichermaßen Kauf- und Mietobjekte.</p>
</div>
</section>
</article>"""


def generate_seo_text(openai_key: str, region_name: str) -> str:
    """Erzeugt einen regionalen SEO-Text + FAQ als HTML für die Makler-Landingpage."""
    client = OpenAI(api_key=openai_key)
    prompt = USER_PROMPT_TEMPLATE.format(
        region_name=region_name,
        template_html=TEMPLATE_HTML,
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=8000,
        temperature=0.7,
    )
    text = response.choices[0].message.content.strip()
    # Markdown-Codeblock entfernen, falls das Modell ihn trotzdem hinzufügt.
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0].strip()
    return text
