<?php

// Dev-only router for `php -S`: maps the production path /blauarbeit/craftsmen.php
// (as referenced in handwerker-box.html) onto the flat local checkout.
$uri = urldecode(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));

if ($uri === '/blauarbeit/craftsmen.php') {
    require __DIR__ . '/craftsmen.php';
    return true;
}

if ($uri === '/blauarbeit/categories.php') {
    require __DIR__ . '/categories.php';
    return true;
}

return false;
