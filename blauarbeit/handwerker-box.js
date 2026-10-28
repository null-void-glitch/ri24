(function () {
    function renderCard(craftsman) {
        var card = document.createElement('div');
        card.className = 'blauarbeit-data-craftsman';

        var logo = document.createElement('div');
        logo.className = 'blauarbeit-data-craftsman-logo';
        var img = document.createElement('img');
        img.loading = 'lazy';
        img.alt = '';
        img.src = craftsman.avatar || '/get-file/img/ressource/img/elements/blauarbeit/avatar-placeholder.png';
        logo.appendChild(img);
        card.appendChild(logo);

        var body = document.createElement('div');
        body.className = 'blauarbeit-data-craftsman-body';

        var name = document.createElement('h4');
        name.title = craftsman.companyName;
        name.textContent = craftsman.companyName;
        body.appendChild(name);

        if (craftsman.categories && craftsman.categories.length) {
            var categories = document.createElement('p');
            categories.title = craftsman.categories.join(', ');
            categories.textContent = craftsman.categories.slice(0, 2).join(', ');
            body.appendChild(categories);
        }

        var geo = document.createElement('p');
        geo.textContent = craftsman.geo.name + ' (' + craftsman.geo.zipcode + ') · ' + craftsman.distanceKm.toFixed(1) + ' km';
        body.appendChild(geo);

        if (craftsman.ratings && craftsman.ratings.count > 0) {
            var rating = document.createElement('p');
            rating.textContent = '★ ' + craftsman.ratings.overall.toFixed(1) + ' (' + craftsman.ratings.count + ')';
            body.appendChild(rating);
        }

        var link = document.createElement('a');
        link.className = 'cmd cmd-l';
        link.href = craftsman.profileLink;
        link.target = '_blank';
        link.rel = 'noopener';
        link.textContent = 'ansehen';
        body.appendChild(link);

        card.appendChild(body);

        return card;
    }

    function setupSlider(box) {
        var track = box.querySelector('.blauarbeit-data');
        var prev = box.querySelector('.blauarbeit-nav-prev');
        var next = box.querySelector('.blauarbeit-nav-next');
        if (!track || !prev || !next) {
            return function () {};
        }

        function cardStep() {
            var card = track.querySelector('.blauarbeit-data-craftsman');
            return card ? card.getBoundingClientRect().width + 16 : 260;
        }

        function update() {
            var scrollable = track.scrollWidth > track.clientWidth + 1;
            prev.hidden = !scrollable;
            next.hidden = !scrollable;
            if (scrollable) {
                prev.disabled = track.scrollLeft <= 0;
                next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 1;
            }
        }

        prev.addEventListener('click', function () {
            track.scrollBy({ left: -cardStep(), behavior: 'smooth' });
        });
        next.addEventListener('click', function () {
            track.scrollBy({ left: cardStep(), behavior: 'smooth' });
        });
        track.addEventListener('scroll', update);
        window.addEventListener('resize', update);

        return update;
    }

    function loadCategories(box) {
        var select = box.querySelector('.blauarbeit-form-category');
        if (!select) {
            return;
        }

        var endpoint = (box.dataset.endpoint || '/blauarbeit/craftsmen.php').replace('craftsmen.php', 'categories.php');

        fetch(endpoint, { headers: { Accept: 'application/json' } })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(function (payload) {
                var categories = (payload.data && payload.data.list) || [];
                categories.forEach(function (category) {
                    var option = document.createElement('option');
                    option.value = String(category.id);
                    option.textContent = category.name;
                    select.appendChild(option);
                });
                select.value = box.dataset.category || '';
            })
            .catch(function () {
                // Dropdown just stays at "Alle Handwerkerarten" if categories fail to load.
            });
    }

    function search(box, zipcode, category) {
        var endpoint = box.dataset.endpoint || '/blauarbeit/craftsmen.php';
        var list = box.querySelector('.blauarbeit-data');
        var status = box.querySelector('.blauarbeit-status');
        var updateSlider = box.blauarbeitUpdateSlider;

        status.hidden = true;
        list.textContent = '';

        if (!zipcode || !/^\d{5}$/.test(zipcode)) {
            status.hidden = false;
            status.textContent = 'Bitte eine gültige 5-stellige PLZ eingeben.';
            return;
        }

        var url = endpoint + '?zipcode=' + encodeURIComponent(zipcode);
        if (category) {
            url += '&category=' + encodeURIComponent(category);
        }

        fetch(url, { headers: { Accept: 'application/json' } })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(function (payload) {
                var craftsmen = (payload.data && payload.data.list) || [];
                if (!craftsmen.length) {
                    status.hidden = false;
                    status.textContent = 'Aktuell keine Handwerker in der Nähe gefunden.';
                    return;
                }
                craftsmen.forEach(function (craftsman) {
                    list.appendChild(renderCard(craftsman));
                });
                updateSlider();
            })
            .catch(function () {
                status.hidden = false;
                status.textContent = 'Handwerker konnten aktuell nicht geladen werden.';
            });
    }

    function initBox(box) {
        box.blauarbeitUpdateSlider = setupSlider(box);
        loadCategories(box);

        var form = box.querySelector('.blauarbeit-form');
        var zipcodeInput = box.querySelector('.blauarbeit-form-zipcode');
        var categorySelect = box.querySelector('.blauarbeit-form-category');

        if (zipcodeInput) {
            zipcodeInput.value = box.dataset.zipcode || '';
        }

        if (form) {
            form.addEventListener('submit', function (event) {
                event.preventDefault();
                search(box, zipcodeInput.value.trim(), categorySelect.value);
            });
        }

        search(box, box.dataset.zipcode, box.dataset.category);
    }

    document.querySelectorAll('.blauarbeit-box').forEach(initBox);
})();
