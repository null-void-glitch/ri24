<?php
/**
 * Dummy-Datenbasis der Finanzierungsberater für den eigenständigen
 * Baufinanzierungs-Assistenten.
 *
 * Alle Werte sind klar erkennbare Platzhalter (Muster wie "(Dummy)" im
 * Exposé-Prototyp, Optikanpassungen/Expose/Expose-Prototyp-P2-Chat.html).
 * Vor Go-Live durch echte Berater ersetzen — Struktur (Keys) beibehalten,
 * da `advisor-resolver.php`, `resolve-advisor.php` und `chat.php` sich
 * darauf verlassen.
 *
 * @return array<string, array{name:string,title:string,phone:string,mobile?:string,email:string,calendly:string,rating:string,avatarInitials:string,photo?:string}>
 */
return [
    'philipp-steppohn' => [
        'name'           => 'Philipp Steppohn',
        'title'          => 'Finanzierungsspezialist',
        'phone'          => '03741 384 49 69',
        'mobile'         => '0176 476 653 21',
        'email'          => 'philipp.steppohn@regionalimmobilien24.de',
        'calendly'       => 'https://calendly.com/dummy-philipp-steppohn/baufinanzierung',
        'rating'         => '4,92 / 5',
        'avatarInitials' => 'PS',
        'photo'          => 'assets/philipp-steppohn.png',
    ],
    'sandra-berger' => [
        'name'           => 'Sandra Berger',
        'title'          => 'Finanzierungsspezialistin',
        'phone'          => '+49 000 0000002 (Dummy)',
        'email'          => 's.berger@beispiel-dummy.de',
        'calendly'       => 'https://calendly.com/dummy-sandra-berger/baufinanzierung',
        'rating'         => '4,88 / 5',
        'avatarInitials' => 'SB',
    ],
    'markus-weiss' => [
        'name'           => 'Markus Weiß',
        'title'          => 'Finanzierungsspezialist',
        'phone'          => '+49 000 0000003 (Dummy)',
        'email'          => 'm.weiss@beispiel-dummy.de',
        'calendly'       => 'https://calendly.com/dummy-markus-weiss/baufinanzierung',
        'rating'         => '4,95 / 5',
        'avatarInitials' => 'MW',
    ],
];
