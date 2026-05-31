## Possbible Tag-Values to make entries findable in OpenStreetMap
Auf [taginfo](https://taginfo.openstreetmap.org/) kann prüfen, wie beliebt ein Schlüssel, eine Schlüssel-Wert-Kombination ist, damit nicht unnötige neue Tags und Werte einführt, um Sachen auf OpenStreetMap zu verschlagworten, eine einheitliche Begrifflichkeit erleichtert auch die Auffindbarkeit
* [leisure=hackerspace](https://taginfo.openstreetmap.org/tags/leisure=hackerspace)
  * Hackspace als Freizeit
  * Eine Einrichtung, in der sich Leute mit gemeinsamen Interessen (Wissenschaft, Technik, ...) treffen.
* [amenity=workshop](https://taginfo.openstreetmap.org/tags/amenity=workshop)
  * Werkstatt
  * A room or building in which goods are manufactured or repaired.
  * [How to use this tag](https://wiki.openstreetmap.org/wiki/Tag:amenity=workshop)
* [workshop=repaircafe](https://taginfo.openstreetmap.org/tags/workshop=repaircafe)
  * Repair Café Werkstatt
* [club=doityourself](https://taginfo.openstreetmap.org/tags/club=doityourself)
  * Verein (club) für Heimwerken
* [social_facility=workshop](https://taginfo.openstreetmap.org/tags/social_facility=workshop)
  * speziell genutzt für Behinderten-Werkstätten
* [service:3dprinter=yes](https://taginfo.openstreetmap.org/tags/service:3dprinter=yes)
  * angebotene Dienste / verfügbare Geräte: 3D-Drucker
* [service:lasercutter=yes](https://taginfo.openstreetmap.org/tags/service:lasercutter=yes)
  * angebotene Dienste / verfügbare Geräte: Lasercutter
* [shop=woodwork](https://taginfo.openstreetmap.org/tags/shop=woodwork)
  * angebotene Dienste / verfügbare Geräte: Holzwerkstatt
* [fablab=yes](https://taginfo.openstreetmap.org/tags/fablab=yes)
  * Makerspace (Fablab) (macht Sinn das Tag zu nutzen, wenn der Key workshop schon mit einem anderen Wert belegt ist)
* [workshop=fablab](https://taginfo.openstreetmap.org/tags/workshop=fablab)
  * Makerspace (Fablab)
* [amenity=coworking_space](https://taginfo.openstreetmap.org/tags/amenity=coworking_space) and [office=coworking](https://taginfo.openstreetmap.org/tags/office=coworking)
  * usually only used for commercial coworking spaces
  * A place where people can go to work (typically requires a fee); not limited to a single employer.
* [shop=doityourself](https://taginfo.openstreetmap.org/tags/shop=doityourself)
  * Ein Baumarkt ist ein großflächiger Supermarkt, der sich auf Materialien für Heimwerker spezialisiert hat.

## Overpass API
Usable via [Overpass Turbo](https://overpass-turbo.eu)
```
[out:json][timeout:25];
{{geocodeArea:Görlitz}}->.searchArea;
(
  nwr["leisure"="hackerspace"](area.searchArea);
  nwr["amenity"="workshop"](area.searchArea);
  nwr["workshop"="repaircafe"](area.searchArea);
  nwr["club"="doityourself"](area.searchArea);
  nwr["social_facility"="workshop"](area.searchArea);
  nwr["service:3dprinter"="yes"](area.searchArea);
  nwr["service:lasercutter"="yes"](area.searchArea);
  nwr["shop"="woodwork"](area.searchArea);
  nwr["fablab"="yes"](area.searchArea);
  nwr["workshop"="fablab"](area.searchArea);
  nwr["amenity"="coworking_space"](area.searchArea);
  nwr["shop"="doityourself"](area.searchArea);
);
out geom;
```

Additional one may add entries in Wikidata / Wikipedia as well and link it to the OpenStreetMap entries.

```
[out:json][timeout:25];
(
  nwr["leisure"="hackerspace"]({{bbox}});
  nwr["amenity"="workshop"]({{bbox}});
  nwr["workshop"="repaircafe"]({{bbox}});
  nwr["club"="doityourself"]({{bbox}});
  nwr["social_facility"="workshop"]({{bbox}});
  nwr["service:3dprinter"="yes"]({{bbox}});
  nwr["service:lasercutter"="yes"]({{bbox}});
  nwr["shop"="woodwork"]({{bbox}});
  nwr["fablab"="yes"]({{bbox}});
  nwr["workshop"="fablab"]({{bbox}});
  nwr["amenity"="coworking_space"]({{bbox}});
  nwr["shop"="doityourself"]({{bbox}});
);
out geom;
```