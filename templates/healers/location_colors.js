location_colors = {};
location_colors_dark = {};
location_address = {};
location_online = {};
//	single_location_colors = {};
//	single_location_colors_dark = {};
{% for loc in locations %}
	location_colors[{{ loc.id }}] = "{{ loc.color }}";
	location_address[{{ loc.id }}] = "{{ loc.full_address_text|linebreaksbr }}";
    location_online[{{ loc.id }}] = {{ loc.book_online }};
{% endfor %}

for(id in location_colors) {
	location_colors_dark[id] = make_dark_color(location_colors[id], 0.16);
//	single_location_colors[id] = make_dark_color(location_colors[id], 0);
//	single_location_colors_dark[id] = make_dark_color(location_colors[id], 0.16);
}
